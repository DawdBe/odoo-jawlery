import logging
from datetime import timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class DailyCashRegister(models.Model):
    _name = 'daily.cash.register'
    _description = 'Daily Cash Register'
    _order = 'date desc'
    _sql_constraints = [
        ('unique_date', 'UNIQUE(date)',
         "Un registre existe déjà pour cette date. Impossible d'en créer un deuxième."),
    ]

    name = fields.Char(required=True, default='New')
    opening_balance = fields.Monetary(string='Opening Balance')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('daily.cash.register') or 'New'
        registers = super().create(vals_list)
        registers._init_from_existing_data()
        for reg in registers:
            _logger.info("=== POST _init_from_existing_data register=%s line_ids.ids=%s tickets.ids=%s",
                         reg.id, reg.line_ids.ids, reg.ticket_ids.ids)
            reg._create_safe_float_movement()
        return registers

    def _init_from_existing_data(self):
        for register in self:
            date = register.date
            date_end = date + timedelta(days=1)
            dt_start = fields.Datetime.to_datetime(date)
            dt_end = fields.Datetime.to_datetime(date_end)

            _logger.info("=== _init_from_existing_data START register=%s date=%s range=[%s, %s)",
                         register.id, date, dt_start, dt_end)

            # ---- TICKETS ----
            ticket_domain = [
                ('date', '>=', dt_start),
                ('date', '<', dt_end),
                ('related_register_id', '=', False),
            ]
            orphan_tickets = self.env['jewelry.ticket'].search(ticket_domain)
            _logger.info("  TICKETS: domain=%s found=%s ids=%s",
                         ticket_domain, len(orphan_tickets), orphan_tickets.ids)
            if orphan_tickets:
                orphan_tickets.related_register_id = register.id
                _logger.info("  TICKETS: reassigned to register=%s", register.id)

            # ---- ALL CASH LINES FOR DATE ----
            all_lines = self.env['cash.register.line'].search([
                ('date', '>=', dt_start),
                ('date', '<', dt_end),
            ])
            _logger.info("  ALL LINES for date: count=%s", len(all_lines))
            for l in all_lines:
                _logger.info("    line id=%s date=%s amount=%s type=%s register_id=%s",
                             l.id, l.date, l.amount, l.type,
                             l.register_id.id if l.register_id else None)

            # ---- ORPHAN CASH LINES (not linked to this register) ----
            orphan_domain = [
                ('date', '>=', dt_start),
                ('date', '<', dt_end),
                '|',
                ('register_id', '=', False),
                ('register_id', '!=', register.id),
            ]
            orphan_lines = self.env['cash.register.line'].search(orphan_domain)
            _logger.info("  ORPHAN LINES: domain=%s found=%s ids=%s",
                         orphan_domain, len(orphan_lines), orphan_lines.ids)
            if orphan_lines:
                _logger.info("  ORPHAN LINES: reassigning to register=%s", register.id)
                orphan_lines.register_id = register.id

            self.env.flush_all()

            # ---- VERIFY AFTER REASSIGNMENT ----
            _logger.info("  AFTER REASSIGNMENT: register.line_ids.ids=%s",
                         register.line_ids.ids)
            for l in register.line_ids:
                _logger.info("    line_ids: id=%s date=%s amount=%s type=%s register_id=%s",
                             l.id, l.date, l.amount, l.type,
                             l.register_id.id if l.register_id else None)

            _logger.info("  calling _compute_balances")
            register._compute_balances()

    closing_balance = fields.Monetary(string='Closing Balance (Physical Count)')
    expected_balance = fields.Monetary(
        string='Expected Balance', compute='_compute_balances', store=True)
    difference = fields.Monetary(
        string='Difference', compute='_compute_balances', store=True)
    cashier_id = fields.Many2one('res.users', string='Cashier', default=lambda self: self.env.user)
    date = fields.Date(default=fields.Date.today, required=True)
    state = fields.Selection([
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('verified', 'Verified'),
    ], default='open', required=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    breakdown_2000 = fields.Integer(string='2000 DZD')
    breakdown_1000 = fields.Integer(string='1000 DZD')
    breakdown_500 = fields.Integer(string='500 DZD')
    breakdown_200 = fields.Integer(string='200 DZD')
    breakdown_100 = fields.Integer(string='100 DZD')
    breakdown_50 = fields.Integer(string='50 DZD')
    breakdown_20 = fields.Integer(string='20 DZD')
    breakdown_10 = fields.Integer(string='10 DZD')

    line_ids = fields.One2many('cash.register.line', 'register_id', string='Cash Movements')
    ticket_ids = fields.One2many('jewelry.ticket', 'related_register_id', string="Today's Tickets")

    @api.model
    def _get_register_for_date(self, dt):
        """Return the register for the given date, or None if none exists.
        This method ONLY searches — it never creates a register.
        Registers should only be created manually by the cashier."""
        register = self.search([('date', '=', dt)], limit=1)
        return register if register else self.browse()

    @api.model
    def init(self):
        pass

    @api.depends('opening_balance', 'line_ids.amount', 'line_ids.type', 'closing_balance')
    def _compute_balances(self):
        for register in self:
            old_expected = register.expected_balance
            old_difference = register.difference
            expected = register.opening_balance or 0.0
            for line in register.line_ids:
                if line.type == 'entree':
                    expected += line.amount or 0.0
                else:
                    expected -= line.amount or 0.0
            _logger.info("=== _compute_balances register=%s opening=%s lines=%s expected=%s old_expected=%s",
                         register.id, register.opening_balance,
                         [(l.id, l.amount, l.type) for l in register.line_ids],
                         expected, old_expected)
            register.expected_balance = expected
            if register.closing_balance is not None:
                register.difference = (register.closing_balance or 0.0) - expected
            else:
                register.difference = 0.0

            changed = register.expected_balance != old_expected or register.difference != old_difference
            _logger.info("  sending bus notification? changed=%s expected=%s->%s diff=%s->%s",
                         changed, old_expected, register.expected_balance,
                         old_difference, register.difference)
            if changed:
                self.env['bus.bus']._sendone(
                    'daily.cash.register.balance',
                    'register_balance_updated',
                    {
                        'register_id': register.id,
                        'expected_balance': register.expected_balance,
                        'difference': register.difference,
                    }
                )
                self.env['bus.bus']._sendone(
                    'daily.cash.register.balance',
                    'register_data_changed',
                    {'register_id': register.id}
                )

    def write(self, vals):
        return super().write(vals)

    @api.constrains('date')
    def _check_unique_date(self):
        for register in self:
            duplicate = self.search([
                ('date', '=', register.date),
                ('id', '!=', register.id),
            ], limit=1)
            if duplicate:
                raise ValidationError(_(
                    "Un registre existe déjà pour le %s. "
                    "Impossible d'en avoir deux pour la même date."
                ) % register.date)

    def close_register(self):
        self.closing_balance = self.closing_balance or self.expected_balance
        self.state = 'closed'
        self._create_safe_return_movement()

    def _create_safe_float_movement(self):
        if not self.opening_balance:
            return
        safe = self.env['cash.safe']._get_main_safe()
        self.env['cash.safe.movement'].create({
            'safe_id': safe.id,
            'type': 'out',
            'amount': self.opening_balance,
            'reason': 'register_float',
            'register_id': self.id,
            'date': fields.Datetime.now(),
            'notes': _('Float for %s') % self.name,
        })

    def _create_safe_return_movement(self):
        if not self.closing_balance:
            return
        safe = self.env['cash.safe']._get_main_safe()
        self.env['cash.safe.movement'].create({
            'safe_id': safe.id,
            'type': 'in',
            'amount': self.closing_balance,
            'reason': 'register_return',
            'register_id': self.id,
            'date': fields.Datetime.now(),
            'notes': _('Return from %s') % self.name,
        })

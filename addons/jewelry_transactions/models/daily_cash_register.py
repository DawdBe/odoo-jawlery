import logging

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
        return super().create(vals_list)

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
    def _get_or_create_for_date(self, dt):
        register = self.search([('date', '=', dt)], limit=1)
        if register:
            return register
        register = self.create({
            'opening_balance': 0.0,
            'date': dt,
        })
        return register

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
            register.expected_balance = expected
            if register.closing_balance is not None:
                register.difference = (register.closing_balance or 0.0) - expected
            else:
                register.difference = 0.0

            if register.expected_balance != old_expected or register.difference != old_difference:
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

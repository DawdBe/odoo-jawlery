from datetime import datetime

from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError


class CashRegisterLine(models.Model):
    _name = 'cash.register.line'
    _description = 'Cash Register Line'
    _order = 'date desc, id desc'

    register_id = fields.Many2one('daily.cash.register', string='Register', ondelete='set null')
    ticket_id = fields.Many2one('jewelry.ticket', string='Linked Ticket')
    amount = fields.Monetary(string='Amount', required=True)
    type = fields.Selection([
        ('entree', 'Entrée'),
        ('sortie', 'Sortie'),
    ], string='Type', required=True)
    category_id = fields.Many2one(
        'cash.movement.category', string='Category',
        help='Business category. Selecting a category auto-fills the direction.')
    origin = fields.Selection([
        ('ticket', 'Ticket Payment'),
        ('manual', 'Manual Entry'),
        ('system', 'System Generated'),
    ], string='Origin', required=True, default='manual',
        help='How this movement was created. Set automatically by the system.')
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('transfer', 'Bank Transfer'),
        ('check', 'Check'),
        ('other', 'Other'),
    ], string='Payment Method', default='cash')
    date = fields.Datetime(string='Date', default=fields.Datetime.now)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    is_travel_cash = fields.Boolean(string='Travel Cash')
    journal_id = fields.Many2one('account.journal', string='Journal')
    partner_id = fields.Many2one('res.partner', string='Partner')
    weight = fields.Float(string='Weight (g)')
    description = fields.Char(string='Description', required=False)
    reference = fields.Char(string='Reference')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    reversed = fields.Boolean(string='Reversed', default=False, help="This payment has been reversed")
    reversal_id = fields.Many2one('cash.register.line', string='Reversal', ondelete='set null', help="The reversal entry for this payment")

    @api.onchange('category_id')
    def _onchange_category_id(self):
        if self.category_id:
            self.type = self.category_id.direction

    @api.constrains('amount')
    def _check_positive_amount(self):
        for line in self:
            if line.amount < 0:
                raise ValidationError(_("Amount must be positive. Use 'type' to indicate direction."))

    @api.constrains('category_id', 'ticket_id')
    def _check_category_or_ticket(self):
        for line in self:
            if line.origin == 'manual' and not line.category_id:
                raise ValidationError(_("Manual cash movements require a category."))

    @api.model
    def _find_or_create_register(self, date_val):
        Register = self.env['daily.cash.register']
        register = Register.search([('date', '=', date_val)], limit=1)
        if not register:
            register = Register.create({
                'date': date_val,
                'cashier_id': self.env.user.id,
            })
        return register

    @api.model_create_multi
    def create(self, vals_list):
        Register = self.env['daily.cash.register']
        register_ids = set()
        for vals in vals_list:
            if vals.get('amount', 0) < 0:
                raise UserError(_("Amount must be positive. Use 'type' to indicate direction."))
            if not vals.get('register_id'):
                date_val = vals.get('date', fields.Datetime.now())
                if isinstance(date_val, datetime):
                    date_val = date_val.date()
                register = self._find_or_create_register(date_val)
                vals['register_id'] = register.id
                register_ids.add(register.id)
            else:
                register_ids.add(vals['register_id'])
            if vals.get('ticket_id') and not vals.get('origin'):
                vals['origin'] = 'ticket'
        lines = super().create(vals_list)
        if register_ids:
            register_ids.discard(False)
            if register_ids:
                Register.browse(list(register_ids))._compute_balances()
        return lines

    def write(self, vals):
        Register = self.env['daily.cash.register']
        old_registers = self.mapped('register_id')
        if vals.get('amount', 0) < 0:
            raise UserError(_("Amount must be positive. Use 'type' to indicate direction."))
        if any(f in vals for f in ('amount', 'type')):
            for record in self:
                if record.register_id and record.register_id.state == 'closed':
                    raise UserError(_(
                        "Impossible de modifier une ligne dans un registre clôturé. "
                        "Rouvrez d'abord le registre."
                    ))
        if 'date' in vals and 'register_id' not in vals:
            for record in self:
                date_val = vals.get('date', record.date)
                if isinstance(date_val, datetime):
                    date_val = date_val.date()
                new_reg = Register.search([('date', '=', date_val)], limit=1)
                if not new_reg:
                    continue
                if record.register_id and record.register_id.state == 'closed' and record.register_id.id != new_reg.id:
                    raise UserError(_(
                        "Impossible de déplacer une ligne de caisse vers une autre date "
                        "car le registre d'origine est clôturé."
                    ))
            result = super().write(vals)
            for record in self:
                date_val = vals.get('date', record.date)
                if isinstance(date_val, datetime):
                    date_val = date_val.date()
                new_reg = Register.search([('date', '=', date_val)], limit=1)
                if new_reg and record.register_id and record.register_id.id != new_reg.id:
                    record.register_id = new_reg.id
            new_registers = self.mapped('register_id')
            (old_registers | new_registers)._compute_balances()
            return result
        result = super().write(vals)
        if 'register_id' in vals:
            new_registers = self.mapped('register_id')
            (old_registers | new_registers)._compute_balances()
        return result

    def unlink(self):
        registers = self.mapped('register_id')
        for record in self:
            if record.register_id and record.register_id.state == 'closed':
                raise UserError(_(
                    "Impossible de supprimer une ligne dans un registre clôturé. "
                    "Rouvrez d'abord le registre."
                ))
        result = super().unlink()
        if registers:
            self.env.flush_all()
            registers._compute_balances()
        return result

    def action_quick_save(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Saved'),
                'message': _('Cash movement recorded successfully.'),
                'sticky': False,
                'type': 'success',
                'next': {'type': 'ir.actions.client', 'tag': 'reload'},
            },
        }

    def action_reverse_payment(self):
        self.ensure_one()
        if self.reversed:
            return
        if self.register_id and self.register_id.state == 'closed':
            raise UserError(_(
                "Impossible d'inverser un paiement dans un registre clôturé. "
                "Rouvrez d'abord le registre."
            ))
        today = fields.Date.today()
        today_reg = self.env['daily.cash.register'].search([('date', '=', today)], limit=1)
        if today_reg and today_reg.state == 'closed':
            raise UserError(_(
                "Impossible d'inverser un paiement aujourd'hui car le registre du %s "
                "est déjà clôturé. Rouvrez-le d'abord."
            ) % today)
        description = _('Reversal: %s') % (
            self.description or (self.ticket_id.name if self.ticket_id else ''))
        reversal = self.create({
            'ticket_id': self.ticket_id.id if self.ticket_id else False,
            'partner_id': self.partner_id.id,
            'category_id': self.category_id.id,
            'amount': self.amount,
            'type': 'sortie' if self.type == 'entree' else 'entree',
            'payment_method': self.payment_method,
            'date': fields.Datetime.now(),
            'user_id': self.env.user.id,
            'description': description,
            'reference': self.reference,
            'origin': self.origin,
        })
        self.reversed = True
        self.reversal_id = reversal.id
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Payment Reversed'),
                'message': _('The payment has been reversed. A new reversal line has been created.'),
                'sticky': False,
                'type': 'success',
                'next': {'type': 'ir.actions.client', 'tag': 'reload'},
            },
        }

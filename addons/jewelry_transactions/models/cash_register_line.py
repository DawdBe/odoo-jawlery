from datetime import datetime

from odoo import api, models, fields, _
from odoo.exceptions import UserError


class CashRegisterLine(models.Model):
    _name = 'cash.register.line'
    _description = 'Cash Register Line'
    _order = 'date desc, id desc'

    register_id = fields.Many2one('daily.cash.register', string='Register', ondelete='cascade')
    ticket_id = fields.Many2one('jewelry.ticket', string='Linked Ticket')
    amount = fields.Monetary(string='Amount', required=True)
    type = fields.Selection([
        ('entree', 'Entrée'),
        ('sortie', 'Sortie'),
    ], string='Type', required=True)
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

    @api.model_create_multi
    def create(self, vals_list):
        Register = self.env['daily.cash.register']
        for vals in vals_list:
            if not vals.get('register_id'):
                date_val = vals.get('date', fields.Datetime.now())
                if isinstance(date_val, datetime):
                    date_val = date_val.date()
                register = Register._get_or_create_for_date(date_val)
                vals['register_id'] = register.id
        return super().create(vals_list)

    def write(self, vals):
        Register = self.env['daily.cash.register']
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
                new_reg = Register._get_or_create_for_date(date_val)
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
                new_reg = Register._get_or_create_for_date(date_val)
                if record.register_id and record.register_id.id != new_reg.id:
                    record.register_id = new_reg.id
            return result
        return super().write(vals)

    def unlink(self):
        for record in self:
            if record.register_id and record.register_id.state == 'closed':
                raise UserError(_(
                    "Impossible de supprimer une ligne dans un registre clôturé. "
                    "Rouvrez d'abord le registre."
                ))
        return super().unlink()

    def action_reverse_payment(self):
        self.ensure_one()
        if self.reversed:
            return
        if not self.ticket_id:
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
        ticket = self.ticket_id
        reversal = self.create({
            'ticket_id': ticket.id,
            'partner_id': self.partner_id.id,
            'amount': -self.amount,
            'type': self.type,
            'payment_method': self.payment_method,
            'date': fields.Datetime.now(),
            'user_id': self.env.user.id,
            'description': _('Reversal: %s') % (self.description or self.ticket_id.name),
            'reference': self.reference,
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

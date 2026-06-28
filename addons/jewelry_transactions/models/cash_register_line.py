from odoo import models, fields


class CashRegisterLine(models.Model):
    _name = 'cash.register.line'
    _description = 'Cash Register Line'
    _order = 'id'

    register_id = fields.Many2one('daily.cash.register', string='Register', ondelete='cascade')
    ticket_id = fields.Many2one('jewelry.ticket', string='Linked Ticket')
    amount = fields.Monetary(string='Amount', required=True)
    type = fields.Selection([
        ('entree', 'Entrée'),
        ('sortie', 'Sortie'),
    ], string='Type', required=True)
    is_travel_cash = fields.Boolean(string='Travel Cash')
    journal_id = fields.Many2one('account.journal', string='Journal')
    supplier_account_id = fields.Many2one('supplier.account', string='Supplier Account')
    partner_id = fields.Many2one('res.partner', string='Partner')
    weight = fields.Float(string='Weight (g)')
    description = fields.Char(string='Description')
    reference = fields.Char(string='Reference')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

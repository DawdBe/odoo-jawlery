from odoo import models, fields


class AssociateTransaction(models.Model):
    _name = 'associate.transaction'
    _description = 'Associate Transaction'
    _order = 'date desc'

    account_id = fields.Many2one('associate.account', string='Account')
    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    transaction_type = fields.Selection([
        ('capital_deposit', 'Capital Deposit'),
        ('capital_withdrawal', 'Capital Withdrawal'),
        ('advance_profit', 'Advance on Profit'),
        ('profit_distribution', 'Profit Distribution'),
        ('profit_effort', 'Profit Effort'),
        ('zakat', 'Zakat'),
    ], string='Type', required=True)
    amount = fields.Monetary(string='Amount', required=True)
    date = fields.Datetime(default=fields.Datetime.now)
    fiscal_year = fields.Char(string='Fiscal Year')
    ticket_id = fields.Many2one('jewelry.ticket', string='Linked Ticket')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    notes = fields.Text()

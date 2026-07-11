from odoo import models, fields, api


class AssociateAccount(models.Model):
    _name = 'associate.account'
    _description = 'Associate Account'
    # Tracks capital and advance balances for business associates (partners).
    # Associates invest capital, receive profit distributions, and can take
    # advances against future profits. This is a simplified partnership ledger.

    partner_id = fields.Many2one('res.partner', string='Associate', required=True)
    capital_balance = fields.Monetary(string='Capital Balance', compute='_compute_balances', store=True)
    advance_balance = fields.Monetary(string='Advance Balance', compute='_compute_balances', store=True)
    last_transaction_date = fields.Datetime(string='Last Transaction Date')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    transaction_ids = fields.One2many('associate.transaction', 'account_id', string='Transactions')

    @api.depends('transaction_ids.amount', 'transaction_ids.transaction_type')
    def _compute_balances(self):
        for account in self:
            capital = 0.0
            advance = 0.0
            for t in account.transaction_ids:
                if t.transaction_type in ('capital_deposit', 'profit_distribution'):
                    capital += t.amount
                elif t.transaction_type == 'capital_withdrawal':
                    capital -= t.amount
                elif t.transaction_type == 'advance_profit':
                    advance += t.amount
            account.capital_balance = capital
            account.advance_balance = advance

    def record_transaction(self, ttype, amount, notes=''):
        self.ensure_one()
        self.env['associate.transaction'].create({
            'account_id': self.id,
            'partner_id': self.partner_id.id,
            'transaction_type': ttype,
            'amount': amount,
            'notes': notes,
        })

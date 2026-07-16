from odoo import models, fields, api


class AssociateAccount(models.Model):
    _name = 'associate.account'
    _description = 'Associate Account'

    partner_id = fields.Many2one('res.partner', string='Associate', required=True, index=True)
    capital_balance = fields.Monetary(string='Capital Balance', compute='_compute_balances', store=True)
    advance_balance = fields.Monetary(string='Advance Balance', compute='_compute_balances', store=True)

    last_transaction_date = fields.Datetime(
        string='Last Transaction Date',
        compute='_compute_last_transaction_date', store=True)

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

    @api.depends('transaction_ids.date')
    def _compute_last_transaction_date(self):
        for account in self:
            dates = account.transaction_ids.mapped('date')
            account.last_transaction_date = max(dates) if dates else False

    def record_transaction(self, ttype, amount, origin='manual', notes='',
                           source_model='', source_id=0, ticket_id=False):
        self.ensure_one()
        self.env['associate.transaction'].create({
            'account_id': self.id,
            'partner_id': self.partner_id.id,
            'transaction_type': ttype,
            'amount': amount,
            'origin': origin,
            'source_model': source_model or '',
            'source_id': source_id or 0,
            'ticket_id': ticket_id or False,
            'notes': notes,
            'state': 'posted',
        })

    def action_view_transactions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Transactions',
            'res_model': 'associate.transaction',
            'view_mode': 'tree,form',
            'domain': [('account_id', '=', self.id)],
            'context': {
                'default_account_id': self.id,
                'default_partner_id': self.partner_id.id,
            },
        }

    def action_view_tickets(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'jewelry_transactions.action_jewelry_ticket')
        partner = self.partner_id
        action['domain'] = [('partner_id', '=', partner.id)]
        action['context'] = {
            'default_partner_id': partner.id,
            'search_default_partner_id': partner.id,
        }
        return action

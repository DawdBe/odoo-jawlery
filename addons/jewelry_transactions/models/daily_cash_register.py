from odoo import models, fields, api


class DailyCashRegister(models.Model):
    _name = 'daily.cash.register'
    _description = 'Daily Cash Register'
    _order = 'date desc'

    name = fields.Char(required=True, default='New')
    opening_balance = fields.Monetary(string='Opening Balance')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('daily.cash.register') or 'New'
        return super().create(vals)
    closing_balance = fields.Monetary(string='Closing Balance (Physical Count)')
    expected_balance = fields.Monetary(string='Expected Balance', compute='_compute_balances', store=True)
    difference = fields.Monetary(string='Difference', compute='_compute_balances', store=True)
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

    line_ids = fields.One2many('cash.register.line', 'register_id', string='Cash Lines')

    @api.depends('opening_balance', 'line_ids.amount', 'line_ids.type', 'state', 'closing_balance')
    def _compute_balances(self):
        for register in self:
            expected = register.opening_balance or 0.0
            for line in register.line_ids:
                if line.type == 'entree':
                    expected += line.amount or 0.0
                else:
                    expected -= line.amount or 0.0
            register.expected_balance = expected
            if register.state == 'closed':
                register.difference = (register.closing_balance or 0.0) - expected
            else:
                register.difference = 0.0

    def compute_difference(self):
        self._compute_balances()

    def close_register(self):
        self.closing_balance = self.closing_balance or self.expected_balance
        self.state = 'closed'
        self._compute_balances()

from odoo import models, fields, api


class SupplierAccount(models.Model):
    _name = 'supplier.account'
    _description = 'Supplier / Atelier Account'

    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    partner_type = fields.Selection([
        ('fournisseur', 'Fournisseur'),
        ('atelier', 'Atelier'),
    ], string='Partner Type')
    weight_balance = fields.Float(string='Weight Balance (g)', compute='_compute_balances', store=True)
    cash_balance = fields.Monetary(string='Cash Balance', compute='_compute_balances', store=True)
    last_rate_used = fields.Monetary(string='Last Rate Used')
    last_transaction_date = fields.Datetime(string='Last Transaction')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    purchase_order_ids = fields.One2many('purchase.order', 'supplier_account_id', string='Purchase Orders')
    cash_line_ids = fields.One2many('cash.register.line', 'supplier_account_id', string='Cash Lines')

    @api.depends('purchase_order_ids.gold_weight_in', 'purchase_order_ids.gold_weight_out',
                 'cash_line_ids.amount', 'cash_line_ids.type', 'cash_line_ids.weight')
    def _compute_balances(self):
        for account in self:
            weight = 0.0
            cash = 0.0
            for po in account.purchase_order_ids:
                weight += (po.gold_weight_in or 0.0) - (po.gold_weight_out or 0.0)
            for cl in account.cash_line_ids:
                if cl.type == 'entree':
                    cash += cl.amount or 0.0
                    weight += cl.weight or 0.0
                else:
                    cash -= cl.amount or 0.0
                    weight -= cl.weight or 0.0
            account.weight_balance = weight
            account.cash_balance = cash

    def compute_weight_value(self, current_rate):
        self.ensure_one()
        return self.weight_balance * current_rate

    def record_sale(self, weight, cash, description=''):
        self.ensure_one()
        self.env['cash.register.line'].create({
            'supplier_account_id': self.id,
            'partner_id': self.partner_id.id,
            'amount': cash,
            'type': 'entree',
            'weight': weight,
            'description': description,
        })

    def record_return(self, weight, description=''):
        self.ensure_one()
        self.env['cash.register.line'].create({
            'supplier_account_id': self.id,
            'partner_id': self.partner_id.id,
            'amount': 0.0,
            'type': 'sortie',
            'weight': weight,
            'description': description,
        })

    def record_cash_payment(self, amount, description=''):
        self.ensure_one()
        self.env['cash.register.line'].create({
            'supplier_account_id': self.id,
            'partner_id': self.partner_id.id,
            'amount': amount,
            'type': 'sortie',
            'description': description,
        })

from odoo import models, fields


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    is_consignment = fields.Boolean(string='Consignment')
    gold_weight_in = fields.Float(string='Gold Weight In (g)')
    gold_weight_out = fields.Float(string='Gold Weight Out (g)')
    gold_metal_type = fields.Many2one('metal.type', string='Gold Metal Type')
    supplier_account_id = fields.Many2one('supplier.account', string='Supplier Account')
    partner_type = fields.Selection([
        ('fournisseur', 'Fournisseur'),
        ('atelier', 'Atelier'),
    ], string='Partner Type')

    def settle_gold_trade(self):
        self.ensure_one()
        if self.partner_type == 'fournisseur':
            account = self.env['supplier.account'].search([('partner_id', '=', self.partner_id.id)], limit=1)
            if account:
                account._compute_balances()

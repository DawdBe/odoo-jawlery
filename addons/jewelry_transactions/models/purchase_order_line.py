from odoo import models, fields


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    weight = fields.Float(string='Weight (g)')
    metal_type_id = fields.Many2one('metal.type', string='Metal Type')
    is_raw_gold = fields.Boolean(string='Is Raw Gold')
    unit_price_per_gram = fields.Monetary(string='Unit Price / Gram')
    line_type = fields.Selection([
        ('achat', 'Achat'),
        ('transfert', 'Transfert'),
        ('consignation', 'Consignation'),
    ], string='Line Type')

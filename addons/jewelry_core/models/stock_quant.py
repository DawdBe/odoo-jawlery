from odoo import models, fields, api


class StockQuant(models.Model):
    _inherit = 'stock.quant'
    # Extends inventory quants to track weight and estimated value per metal type.
    # This is crucial for jewelry stores where inventory value = weight × gold rate,
    # not just a fixed purchase price.

    weight_total = fields.Float(string='Total Weight (g)')
    metal_type_id = fields.Many2one('metal.type', related='product_id.product_tmpl_id.metal_type_id', store=True)
    # Related field: metal type flows from product template → product → quant.
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    estimated_value = fields.Monetary(string='Estimated Value', compute='_compute_estimated_value')

    @api.depends('weight_total', 'metal_type_id')
    def _compute_estimated_value(self):
        # Inventory value = weight × current gold market rate.
        # Junior Developer Note: This computes live valuation rather than
        # using historical cost. That means the balance sheet reflects current
        # market conditions, which is standard practice in gold trading.
        for record in self:
            if record.metal_type_id and record.weight_total:
                rate = record.metal_type_id.get_current_rate('market')
                record.estimated_value = record.weight_total * rate
            else:
                record.estimated_value = 0.0

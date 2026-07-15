from odoo import models, fields, api


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    weight_total = fields.Float(string='Total Weight (g)')
    metal_type_id = fields.Many2one('metal.type', related='product_id.product_tmpl_id.metal_type_id', store=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    estimated_value = fields.Monetary(string='Estimated Value', compute='_compute_estimated_value', store=True)

    @api.depends('weight_total', 'metal_type_id')
    def _compute_estimated_value(self):
        for record in self:
            if record.metal_type_id and record.weight_total:
                rate = record.metal_type_id.get_current_rate('market')
                record.estimated_value = record.weight_total * rate
            else:
                record.estimated_value = 0.0




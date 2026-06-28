from odoo import models, fields


class StockMove(models.Model):
    _inherit = 'stock.move'

    weight_total = fields.Float(string='Total Weight (g)')
    metal_type_id = fields.Many2one('metal.type', related='product_id.product_tmpl_id.metal_type_id', store=True)
    move_type = fields.Selection([
        ('achat', 'Achat'),
        ('vente', 'Vente'),
        ('transfert', 'Transfert'),
        ('fasonage', 'Fasonage'),
        ('fonte', 'Fonte'),
    ], string='Move Type')

from odoo import models, fields


class ProductPromotion(models.Model):
    _name = 'product.promotion'
    _description = 'Product Promotion'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    promotion_type = fields.Selection([
        ('percentage', 'Percentage'),
        ('fixed_price', 'Fixed Price'),
    ], required=True)
    value = fields.Float(string='Value (% or Fixed)')
    applicable_on = fields.Selection([
        ('all', 'All'),
        ('category', 'Category'),
        ('style', 'Style'),
        ('metal_type', 'Metal Type'),
        ('product', 'Product'),
    ], required=True, default='all')
    metal_type_id = fields.Many2one('metal.type', string='Metal Type')
    product_category_id = fields.Many2one('product.category', string='Category')
    style = fields.Selection([
        ('massif', 'Massif'),
        ('massif_lux', 'Massif Lux'),
        ('bataille', 'Bataille'),
        ('massif_controle', 'Massif Controlé'),
        ('mesaise', 'Mesaise'),
        ('or_750', 'Or 750'),
    ], string='Style')
    product_id = fields.Many2one('product.product', string='Product')
    date_start = fields.Date(string='Start Date')
    date_end = fields.Date(string='End Date')
    notes = fields.Text()

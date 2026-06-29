from odoo import models, fields, api
from dateutil.parser import parse


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

    def get_applicable_price(self, product, metal_type, style):
        today = fields.Date.today()
        promotions = self.search([
            ('active', '=', True),
            '|', ('date_start', '<=', today), ('date_start', '=', False),
            '|', ('date_end', '>=', today), ('date_end', '=', False),
        ])
        base_price = product.lst_price if hasattr(product, 'lst_price') else 0.0
        best_price = base_price
        for promo in promotions:
            if not promo._applies_to(product, metal_type, style):
                continue
            if promo.promotion_type == 'percentage':
                discounted = base_price * (1 - promo.value / 100)
            else:
                discounted = promo.value
            if discounted < best_price:
                best_price = discounted
        return best_price

    def _applies_to(self, product, metal_type, style):
        self.ensure_one()
        if self.applicable_on == 'all':
            return True
        if self.applicable_on == 'product' and self.product_id == product:
            return True
        if self.applicable_on == 'metal_type' and metal_type and self.metal_type_id == metal_type:
            return True
        if self.applicable_on == 'style' and style and self.style == style:
            return True
        if self.applicable_on == 'category' and self.product_category_id:
            cat = product.product_tmpl_id.categ_id if hasattr(product, 'product_tmpl_id') else None
            if cat and (cat.id == self.product_category_id.id or cat.parent_path.startswith(str(self.product_category_id.id))):
                return True
        return False

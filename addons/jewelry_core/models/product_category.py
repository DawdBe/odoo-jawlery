from odoo import models, fields


class ProductCategory(models.Model):
    _inherit = 'product.category'

    has_weight = fields.Boolean(string='Sold by Weight', help='True = sold by weight, False = fixed price')
    is_jewelry = fields.Boolean(string='Is Jewelry')

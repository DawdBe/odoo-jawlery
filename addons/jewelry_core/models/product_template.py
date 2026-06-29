from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    metal_type_id = fields.Many2one('metal.type', string='Metal Type')
    jewelry_category = fields.Selection([
        ('fini', 'Fini (Finished)'),
        ('brut', 'Brut (Raw)'),
        ('pierre', 'Pierre (Stone)'),
        ('fourniture', 'Fourniture (Supply)'),
    ], string='Jewelry Category')
    gross_weight = fields.Float(string='Gross Weight (g)')
    stone_weight = fields.Float(string='Stone Weight (g)')
    net_weight = fields.Float(string='Net Weight (g)', compute='_compute_net_weight')
    style = fields.Selection([
        ('massif', 'Massif'),
        ('massif_lux', 'Massif Lux'),
        ('bataille', 'Bataille'),
        ('massif_controle', 'Massif Controlé'),
        ('mesaise', 'Mesaise'),
        ('or_750', 'Or 750'),
    ], string='Style')
    barcode = fields.Char(string='Barcode', help='Encodes product attributes (casse, karat, weight, style)')

    @api.depends('gross_weight', 'stone_weight')
    def _compute_net_weight(self):
        for record in self:
            record.net_weight = (record.gross_weight or 0.0) - (record.stone_weight or 0.0)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    serial_number = fields.Char(string='Serial Number')
    certificate_number = fields.Char(string='Certificate Number')
    weight = fields.Float(string='Weight (g)')
    location_id = fields.Many2one('stock.location', string='Location')

    @api.model
    def create(self, vals):
        if not vals.get('barcode'):
            seq = self.env['ir.sequence'].next_by_code('product.barcode') or ''
            if seq:
                vals['barcode'] = seq
        return super().create(vals)

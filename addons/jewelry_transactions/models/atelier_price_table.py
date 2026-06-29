from odoo import models, fields


class AtelierPriceTable(models.Model):
    _name = 'atelier.price.table'
    _description = 'Atelier Price Table'
    _rec_name = 'atelier_id'

    atelier_id = fields.Many2one('res.partner', string='Atelier', required=True, domain="[('partner_type','=','atelier')]")
    style = fields.Selection([
        ('massif', 'Massif'),
        ('massif_lux', 'Massif Lux'),
        ('bataille', 'Bataille'),
        ('massif_controle', 'Massif Controlé'),
        ('mesaise', 'Mesaise'),
        ('or_750', 'Or 750'),
    ], string='Style', required=True)
    metal_type_id = fields.Many2one('metal.type', string='Metal Type', required=True)
    cost_per_gram = fields.Monetary(string='Cost per Gram', required=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    notes = fields.Text()

    _sql_constraints = [
        ('unique_atelier_style_metal', 'UNIQUE(atelier_id, style, metal_type_id)',
         'This atelier already has a price for this style and metal type!'),
    ]

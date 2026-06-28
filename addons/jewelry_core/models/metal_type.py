from odoo import models, fields, api


class MetalType(models.Model):
    _name = 'metal.type'
    _description = 'Metal Type / Casse'
    _order = 'sequence, name'

    name = fields.Char(required=True, translate=True)
    code = fields.Char(string='Code', help='AU, AG, PT, etc.')
    purity_percentage = fields.Float(string='Purity (%)')
    karat_value = fields.Float(string='Karat')
    category = fields.Selection([
        ('or', 'Or'),
        ('argent', 'Argent'),
        ('casse', 'Casse'),
        ('plaque', 'Plaqué'),
        ('perle', 'Perle / Djouhar'),
        ('devise', 'Devise'),
    ], required=True, default='casse')
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    gold_rate_ids = fields.One2many('gold.rate.history', 'metal_type_id', string='Gold Rates')

    @api.model
    def _get_casse_types(self):
        return self.search([('category', '=', 'casse')])

    def get_current_rate(self, rate_type='market'):
        self.ensure_one()
        rate = self.env['gold.rate.history'].search([
            ('metal_type_id', '=', self.id),
            ('is_active', '=', True),
        ], order='effective_date desc', limit=1)
        if rate:
            return rate.market_rate if rate_type == 'market' else rate.bursa_rate
        return 0.0

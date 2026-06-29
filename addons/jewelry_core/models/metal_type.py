from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class MetalType(models.Model):
    _name = 'metal.type'
    _description = 'Metal Type / Casse'
    _order = 'sequence, name'
    _sql_constraints = [
        ('name_unique', 'UNIQUE(name)', _('A metal type with this name already exists.')),
    ]

    name = fields.Char(required=True, translate=True)
    purity_percentage = fields.Float(string='Purity (%)')
    karat_value = fields.Float(string='Karat')
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    gold_rate_ids = fields.One2many('gold.rate.history', 'metal_type_id', string='Gold Rates')

    @api.constrains('karat_value')
    def _check_karat(self):
        for rec in self:
            if rec.karat_value == 0.0:
                raise ValidationError(_('Karat value cannot be 0.'))

    def get_current_rate(self, rate_type='market'):
        self.ensure_one()
        rate = self.env['gold.rate.history'].search([
            ('metal_type_id', '=', self.id),
            ('is_active', '=', True),
        ], order='effective_date desc', limit=1)
        if rate:
            if rate_type == 'market':
                return rate.market_rate or 0.0
            return rate.bursa_rate or 0.0
        return 0.0

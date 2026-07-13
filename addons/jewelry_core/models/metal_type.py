from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class MetalType(models.Model):
    _name = 'metal.type'
    _description = 'Metal Type / Casse'
    _order = 'sequence, name'
    _sql_constraints = [
        ('name_unique', 'UNIQUE(name)', _('A metal type with this name already exists.')),
    ]
    # Defines metal purity types used throughout the jewelry system.
    # Examples: Or 18K (75.0%), Or 21K (87.5%), Argent 925 (92.5%).
    # The term "Casse" refers to scrap/recycled gold classified by purity.
    # Each metal type has its own gold rate history and pricing.

    name = fields.Char(required=True, translate=True)
    purity_percentage = fields.Float(string='Purity (%)')
    # E.g., 75.0 for 18k gold (75% pure gold, 25% alloy)
    karat_value = fields.Float(string='Karat')
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    gold_rate_ids = fields.One2many('gold.rate.history', 'metal_type_id', string='Gold Rates')
    silver_rate_ids = fields.One2many('silver.rate.history', 'metal_type_id', string='Silver Rates')

    @api.constrains('karat_value')
    def _check_karat(self):
        for rec in self:
            if rec.karat_value == 0.0:
                raise ValidationError(_('Karat value cannot be 0.'))

    def get_current_rate(self, rate_type='market'):
        # Returns the latest active rate for this metal type.
        # Used extensively throughout the system whenever a price
        # needs to be computed from current gold prices.
        # rate_type can be 'market' (selling price) or 'bursa' (reference).
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

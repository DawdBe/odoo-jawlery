from odoo import models, fields, api


class GoldRateHistory(models.Model):
    _name = 'gold.rate.history'
    _description = 'Gold Rate History'
    _order = 'effective_date desc'

    metal_type_id = fields.Many2one('metal.type', string='Metal Type', required=True)
    bursa_rate = fields.Monetary(string='Bursa Rate (Reference)', currency_field='currency_id')
    market_rate = fields.Monetary(string='Market Rate (Used)', currency_field='currency_id')
    market_spread = fields.Monetary(string='Spread (Bursa→Market)', compute='_compute_spread', store=True,
                                    currency_field='currency_id')
    is_active = fields.Boolean(default=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    effective_date = fields.Date(string='Effective Date', default=fields.Date.today)
    created_by = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user)
    notes = fields.Text()

    @api.depends('bursa_rate', 'market_rate')
    def _compute_spread(self):
        for rec in self:
            rec.market_spread = (rec.market_rate or 0.0) - (rec.bursa_rate or 0.0)

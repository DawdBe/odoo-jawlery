from odoo import models, fields, api


class SilverRateHistory(models.Model):
    _name = 'silver.rate.history'
    _description = 'Silver Rate History'
    _order = 'effective_date desc'

    metal_type_id = fields.Many2one('metal.type', string='Metal Type', required=True)

    base_silver_usd = fields.Monetary(
        string='Silver Base (USD/oz)',
        currency_field='currency_id',
        help='Live pure silver price in USD per Troy ounce from API')
    base_silver_dzd = fields.Monetary(
        string='Silver Base (DZD/g)',
        compute='_compute_base_silver_dzd', store=True,
        currency_field='currency_id',
        help='Pure silver price in DZD per gram (USD/oz × DZD rate ÷ 31.1035)')
    dzd_parallel_rate = fields.Float(
        string='DZD Parallel Rate',
        help='Parallel market USD/DZD rate (ChangeDA)')

    bursa_rate = fields.Monetary(
        string='Bursa Rate (Reference)',
        compute='_compute_bursa_rate', store=True,
        currency_field='currency_id',
        help='Theoretical rate = base × (metal purity ÷ 100)')

    market_rate = fields.Monetary(
        string='Market Rate (Used)',
        currency_field='currency_id',
        help='Your selling price per gram — used in ticket transactions')
    market_spread = fields.Monetary(
        string='Spread (Bursa→Market)',
        compute='_compute_market_spread', store=True,
        currency_field='currency_id',
        help='Auto-computed: Market Rate − Bursa Rate')

    is_active = fields.Boolean(default=True)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.company.currency_id)
    effective_date = fields.Date(string='Effective Date', default=fields.Date.today)
    created_by = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user)
    notes = fields.Text()

    @api.depends('base_silver_usd', 'dzd_parallel_rate')
    def _compute_base_silver_dzd(self):
        helper = self.env['metal.rate.helper']
        for rec in self:
            if rec.base_silver_usd and rec.dzd_parallel_rate:
                rec.base_silver_dzd = helper.compute_base_dzd(rec.base_silver_usd, rec.dzd_parallel_rate)
            elif rec.base_silver_usd:
                rec.base_silver_dzd = helper.compute_base_dzd(rec.base_silver_usd, 1.0)
            else:
                rec.base_silver_dzd = 0

    @api.depends('base_silver_dzd', 'metal_type_id')
    def _compute_bursa_rate(self):
        helper = self.env['metal.rate.helper']
        for rec in self:
            if rec.base_silver_dzd and rec.metal_type_id:
                purity = rec.metal_type_id.purity_percentage or 0.0
                rec.bursa_rate = helper.compute_bursa(rec.base_silver_dzd, purity, base_purity=100.0)
            else:
                rec.bursa_rate = 0

    @api.depends('bursa_rate', 'market_rate')
    def _compute_market_spread(self):
        helper = self.env['metal.rate.helper']
        for rec in self:
            rec.market_spread = helper.compute_spread(rec.market_rate, rec.bursa_rate)

    def _get_market_for(self, purity_label):
        purity_map = {'1000': 100.0, '925': 92.5, '500': 50.0}
        target_purity = purity_map.get(purity_label)
        if not target_purity:
            return 0.0
        rec = self.search([
            ('metal_type_id.purity_percentage', '=', target_purity),
            ('is_active', '=', True),
        ], order='effective_date desc, id desc', limit=1)
        return rec.market_rate or 0.0 if rec else 0.0

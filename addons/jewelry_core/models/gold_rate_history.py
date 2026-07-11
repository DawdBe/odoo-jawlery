from odoo import models, fields, api


class GoldRateHistory(models.Model):
    _name = 'gold.rate.history'
    _description = 'Gold Rate History'
    _order = 'effective_date desc'
    # Daily snapshot of gold prices per metal type.
    # Each record captures the 24k reference in USD/oz, the DZD parallel rate,
    # and derived values (bursa, market, spread) for one metal purity.
    # The is_active flag marks the "current" rate used in ticket transactions.

    metal_type_id = fields.Many2one('metal.type', string='Metal Type', required=True)

    base_24k_usd = fields.Monetary(
        string='24k Base (USD/oz)',
        currency_field='currency_id',
        help='Live 24k 99.99% gold price in USD per Troy ounce from API')
    base_24k_dzd = fields.Monetary(
        string='24k Base (DZD/g)',
        compute='_compute_base_24k_dzd', store=True,
        currency_field='currency_id',
        help='24k 99.99% gold price in DZD per gram (USD/oz × DZD rate ÷ 31.1035)')
    dzd_parallel_rate = fields.Float(
        string='DZD Parallel Rate',
        help='Parallel market USD/DZD rate (ChangeDA)')
    # The parallel rate is crucial: Algerian jewelry stores operate on the
    # parallel (black) market rate, not the official bank rate.

    bursa_rate = fields.Monetary(
        string='Bursa Rate (Reference)',
        compute='_compute_bursa_rate', store=True,
        currency_field='currency_id',
        help='Theoretical rate = 24k base × (metal purity ÷ 99.99)')
    # "Bursa" = reference rate based purely on gold content.
    # For 18k (75% purity): bursa = 24k_DZD/g × (75.0 / 99.99)

    market_rate = fields.Monetary(
        string='Market Rate (Used)',
        currency_field='currency_id',
        help='Your selling price per gram — used in ticket transactions')
    # Market rate is the actual selling price the store uses.
    # The spread (market - bursa) represents profit per gram.
    # This is the key field used in ticket line price_unit calculations.
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

    @staticmethod
    def _r10(val):
        return round(val / 10.0) * 10

    @api.depends('base_24k_usd', 'dzd_parallel_rate')
    def _compute_base_24k_dzd(self):
        for rec in self:
            if rec.base_24k_usd and rec.dzd_parallel_rate:
                rec.base_24k_dzd = self._r10(rec.base_24k_usd * rec.dzd_parallel_rate / 31.1035)
            elif rec.base_24k_usd:
                rec.base_24k_dzd = self._r10(rec.base_24k_usd / 31.1035)
            else:
                rec.base_24k_dzd = 0

    @api.depends('base_24k_dzd', 'metal_type_id')
    def _compute_bursa_rate(self):
        for rec in self:
            if rec.base_24k_dzd and rec.metal_type_id:
                purity = rec.metal_type_id.purity_percentage or 0.0
                rec.bursa_rate = self._r10(rec.base_24k_dzd * (purity / 99.99)) if purity else 0
            else:
                rec.bursa_rate = 0

    @api.depends('bursa_rate', 'market_rate')
    def _compute_market_spread(self):
        for rec in self:
            rec.market_spread = self._r10((rec.market_rate or 0.0) - (rec.bursa_rate or 0.0))

    def _get_market_for(self, karat_label):
        # Look up the latest active market rate for a given karat label.
        # Used by the gold price overview and ticket line auto-pricing.
        purity_map = {'24k': 99.99, '21k': 87.5, '18k': 75.0,
                       '18k_720': 72.0, '18k_710': 71.0, '18k_705': 70.5}
        target_purity = purity_map.get(karat_label)
        if not target_purity:
            return 0.0
        rec = self.search([
            ('metal_type_id.purity_percentage', '=', target_purity),
            ('is_active', '=', True),
        ], order='effective_date desc, id desc', limit=1)
        return rec.market_rate or 0.0 if rec else 0.0

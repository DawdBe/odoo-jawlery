from odoo import models, fields, api, _
from odoo.exceptions import UserError


class GoldPriceOverview(models.TransientModel):
    _name = 'gold.price.overview'
    _description = 'Gold Price Overview'

    # ── API / Reference ──
    base_24k_usd_oz = fields.Monetary(
        string='24k USD/oz',
        currency_field='currency_id',
        help='Live 24k gold price in USD per Troy ounce (from API)')
    base_24k_usd_g = fields.Monetary(
        string='24k USD/g',
        compute='_compute_all', currency_field='currency_id',
        help='24k gold price in USD per gram = USD/oz ÷ 31.1035')
    dzd_parallel_rate = fields.Float(
        string='DZD Parallel',
        help='Type the ChangeDA parallel rate (e.g. 237.00)')
    base_24k_dzd = fields.Monetary(
        string='24k DZD/g',
        compute='_compute_all', currency_field='currency_id',
        help='24k gold price in DZD per gram = USD/g × DZD parallel')

    # ── Bursa / Market / Spread per purity ──
    bursa_24k_dzd = fields.Monetary(compute='_compute_all', currency_field='currency_id')
    bursa_21k_dzd = fields.Monetary(compute='_compute_all', currency_field='currency_id')
    bursa_18k_dzd = fields.Monetary(compute='_compute_all', currency_field='currency_id')
    bursa_18k_720_dzd = fields.Monetary(compute='_compute_all', currency_field='currency_id')
    bursa_18k_710_dzd = fields.Monetary(compute='_compute_all', currency_field='currency_id')
    bursa_18k_705_dzd = fields.Monetary(compute='_compute_all', currency_field='currency_id')

    market_24k_dzd = fields.Monetary(
        string='Market 24k/g',
        currency_field='currency_id',
        help='Your 24k selling price per gram — type directly')
    market_21k_dzd = fields.Monetary(
        compute='_compute_all', currency_field='currency_id')
    market_18k_dzd = fields.Monetary(
        compute='_compute_all', currency_field='currency_id')
    market_18k_720_dzd = fields.Monetary(
        compute='_compute_all', currency_field='currency_id')
    market_18k_710_dzd = fields.Monetary(
        compute='_compute_all', currency_field='currency_id')
    market_18k_705_dzd = fields.Monetary(
        compute='_compute_all', currency_field='currency_id')

    spread_24k = fields.Monetary(compute='_compute_all', currency_field='currency_id')
    spread_21k = fields.Monetary(compute='_compute_all', currency_field='currency_id')
    spread_18k = fields.Monetary(compute='_compute_all', currency_field='currency_id')
    spread_18k_720 = fields.Monetary(compute='_compute_all', currency_field='currency_id')
    spread_18k_710 = fields.Monetary(compute='_compute_all', currency_field='currency_id')
    spread_18k_705 = fields.Monetary(compute='_compute_all', currency_field='currency_id')

    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    last_update = fields.Datetime(string='Last Update')

    PURITY = {
        '24k': 999, '21k': 875, '18k': 750,
        '18k_720': 720, '18k_710': 710, '18k_705': 705,
    }

    @staticmethod
    def _r10(val):
        return round(val / 10.0) * 10

    @api.depends('base_24k_usd_oz', 'dzd_parallel_rate', 'market_24k_dzd')
    def _compute_all(self):
        for rec in self:
            usd_per_g = (rec.base_24k_usd_oz or 0.0) / 31.1035
            rec.base_24k_usd_g = usd_per_g
            rec.base_24k_dzd = self._r10(usd_per_g * (rec.dzd_parallel_rate or 0.0))

            m24 = rec.market_24k_dzd or 0.0
            for k, per_mille in self.PURITY.items():
                ratio = per_mille / 999.0
                bursa = self._r10(rec.base_24k_dzd * ratio)
                setattr(rec, f'bursa_{k}_dzd', bursa)
                if k == '24k':
                    setattr(rec, f'market_{k}_dzd', m24)
                else:
                    setattr(rec, f'market_{k}_dzd', self._r10(m24 * per_mille / 999))
                setattr(rec, f'spread_{k}',
                        getattr(rec, f'market_{k}_dzd') - bursa)

    def load_from_db(self):
        latest = self.env['gold.rate.history'].search([
            ('is_active', '=', True),
        ], order='effective_date desc, id desc', limit=1)
        if latest:
            self.base_24k_usd_oz = latest.base_24k_usd or 0.0
            self.dzd_parallel_rate = latest.dzd_parallel_rate or 0.0
            m24 = self._r10(latest._get_market_for('24k') or 0.0)
            self.market_24k_dzd = m24
        self.last_update = fields.Datetime.now()
        self._compute_all()

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        latest = self.env['gold.rate.history'].search([
            ('is_active', '=', True),
        ], order='effective_date desc, id desc', limit=1)
        if latest:
            res['base_24k_usd_oz'] = latest.base_24k_usd or 0.0
            res['dzd_parallel_rate'] = latest.dzd_parallel_rate or 0.0
            m24 = self._r10(latest._get_market_for('24k') or 0.0)
            res['market_24k_dzd'] = m24
            for k, per_mille in self.PURITY.items():
                if k != '24k':
                    res[f'market_{k}_dzd'] = self._r10(m24 * per_mille / 999)
        res['last_update'] = fields.Datetime.now()
        return res

    @api.onchange('market_24k_dzd')
    def _onchange_market_24k(self):
        if self.market_24k_dzd:
            self.market_24k_dzd = self._r10(self.market_24k_dzd)

    def action_refresh(self):
        config = self.env['gold.price.api.config']._get_config()
        if config:
            config.fetch_all_rates()
        self.load_from_db()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'gold.price.overview',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'inline',
        }

    def action_save_rates(self):
        purity_to_pct = {
            999: 99.99, 875: 87.5, 750: 75.0,
            720: 72.0, 710: 71.0, 705: 70.5,
        }
        for rec in self:
            for k, per_mille in self.PURITY.items():
                pct = purity_to_pct.get(per_mille)
                if not pct:
                    continue
                metal = self.env['metal.type'].search([
                    ('purity_percentage', '=', pct),
                ], limit=1)
                if not metal:
                    continue
                existing = self.env['gold.rate.history'].search([
                    ('metal_type_id', '=', metal.id),
                    ('effective_date', '=', fields.Date.today()),
                ], limit=1)
                market = self._r10(getattr(rec, f'market_{k}_dzd') or 0.0)
                vals = {
                    'metal_type_id': metal.id,
                    'base_24k_usd': rec.base_24k_usd_oz or 0.0,
                    'dzd_parallel_rate': rec.dzd_parallel_rate or 0.0,
                    'market_rate': market,
                    'effective_date': fields.Date.today(),
                    'is_active': True,
                }
                if existing:
                    existing.write(vals)
                else:
                    self.env['gold.rate.history'].create(vals)
        return {'type': 'ir.actions.client', 'tag': 'reload'}

from datetime import timedelta
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class GoldPriceOverview(models.TransientModel):
    _name = 'gold.price.overview'
    _description = 'Gold & Silver Price Overview'

    # ── Gold Reference ──
    base_24k_usd_oz = fields.Monetary(
        string='24k USD/oz',
        currency_field='currency_id',
        help='Live 24k gold price in USD per Troy ounce (from API)')
    base_24k_usd_g = fields.Monetary(
        string='24k USD/g',
        compute='_compute_all', currency_field='currency_id')
    dzd_parallel_rate = fields.Float(
        string='DZD Parallel',
        help='Type the ChangeDA parallel rate (e.g. 237.00)')
    base_24k_dzd = fields.Monetary(
        string='24k DZD/g',
        compute='_compute_all', currency_field='currency_id')

    # ── Gold Bursa / Market / Spread per purity ──
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
    market_21k_dzd = fields.Monetary(compute='_compute_all', currency_field='currency_id')
    market_18k_dzd = fields.Monetary(compute='_compute_all', currency_field='currency_id')
    market_18k_720_dzd = fields.Monetary(compute='_compute_all', currency_field='currency_id')
    market_18k_710_dzd = fields.Monetary(compute='_compute_all', currency_field='currency_id')
    market_18k_705_dzd = fields.Monetary(compute='_compute_all', currency_field='currency_id')

    spread_24k = fields.Monetary(compute='_compute_all', currency_field='currency_id')
    spread_21k = fields.Monetary(compute='_compute_all', currency_field='currency_id')
    spread_18k = fields.Monetary(compute='_compute_all', currency_field='currency_id')
    spread_18k_720 = fields.Monetary(compute='_compute_all', currency_field='currency_id')
    spread_18k_710 = fields.Monetary(compute='_compute_all', currency_field='currency_id')
    spread_18k_705 = fields.Monetary(compute='_compute_all', currency_field='currency_id')

    # ── Silver Reference ──
    base_silver_usd_oz = fields.Monetary(
        string='Silver USD/oz',
        currency_field='currency_id',
        help='Live silver price in USD per Troy ounce (from API)')
    base_silver_usd_g = fields.Monetary(
        string='Silver USD/g',
        compute='_compute_all', currency_field='currency_id')
    base_silver_dzd = fields.Monetary(
        string='Silver DZD/g',
        compute='_compute_all', currency_field='currency_id')

    # ── Silver Bursa / Market / Spread per purity ──
    silver_bursa_1000_dzd = fields.Monetary(compute='_compute_all', currency_field='currency_id')
    silver_bursa_925_dzd = fields.Monetary(compute='_compute_all', currency_field='currency_id')
    silver_bursa_500_dzd = fields.Monetary(compute='_compute_all', currency_field='currency_id')

    silver_market_1000_dzd = fields.Monetary(
        string='Market 1000/g',
        currency_field='currency_id',
        help='Your pure silver selling price per gram — type directly')
    silver_market_925_dzd = fields.Monetary(compute='_compute_all', currency_field='currency_id')
    silver_market_500_dzd = fields.Monetary(compute='_compute_all', currency_field='currency_id')

    silver_spread_1000 = fields.Monetary(compute='_compute_all', currency_field='currency_id')
    silver_spread_925 = fields.Monetary(compute='_compute_all', currency_field='currency_id')
    silver_spread_500 = fields.Monetary(compute='_compute_all', currency_field='currency_id')

    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    last_update = fields.Datetime(string='Last Update')
    chart_data_text = fields.Text(string='Chart Data (internal)')
    auto_refresh_msg = fields.Char(string='Auto-Refresh Status (internal)')

    GOLD_PURITY = {
        '24k': 999, '21k': 875, '18k': 750,
        '18k_720': 720, '18k_710': 710, '18k_705': 705,
    }
    SILVER_PURITY = {
        '1000': 1000, '925': 925, '500': 500,
    }

    @api.depends(
        'base_24k_usd_oz', 'dzd_parallel_rate', 'market_24k_dzd',
        'base_silver_usd_oz', 'silver_market_1000_dzd')
    def _compute_all(self):
        helper = self.env['metal.rate.helper']
        for rec in self:
            # ── Gold ──
            usd_per_g = (rec.base_24k_usd_oz or 0.0) / 31.1035
            rec.base_24k_usd_g = usd_per_g
            rec.base_24k_dzd = helper._r10(usd_per_g * (rec.dzd_parallel_rate or 0.0))

            m24 = rec.market_24k_dzd or 0.0
            for k, per_mille in self.GOLD_PURITY.items():
                ratio = per_mille / 999.0
                bursa = helper._r10(rec.base_24k_dzd * ratio)
                setattr(rec, f'bursa_{k}_dzd', bursa)
                if k == '24k':
                    setattr(rec, f'market_{k}_dzd', m24)
                else:
                    setattr(rec, f'market_{k}_dzd', helper._r10(m24 * per_mille / 999))
                setattr(rec, f'spread_{k}',
                        getattr(rec, f'market_{k}_dzd') - bursa)

            # ── Silver ──
            silver_usd_per_g = (rec.base_silver_usd_oz or 0.0) / 31.1035
            rec.base_silver_usd_g = silver_usd_per_g
            rec.base_silver_dzd = helper._r10(silver_usd_per_g * (rec.dzd_parallel_rate or 0.0))

            m1000 = rec.silver_market_1000_dzd or 0.0
            for k, per_mille in self.SILVER_PURITY.items():
                ratio = per_mille / 1000.0
                bursa = helper._r10(rec.base_silver_dzd * ratio)
                setattr(rec, f'silver_bursa_{k}_dzd', bursa)
                if k == '1000':
                    setattr(rec, f'silver_market_{k}_dzd', m1000)
                else:
                    setattr(rec, f'silver_market_{k}_dzd', helper._r10(m1000 * per_mille / 1000))
                setattr(rec, f'silver_spread_{k}',
                        getattr(rec, f'silver_market_{k}_dzd') - bursa)

    def load_from_db(self):
        helper = self.env['metal.rate.helper']
        latest_gold = self.env['gold.rate.history'].search([
            ('is_active', '=', True),
        ], order='effective_date desc, id desc', limit=1)
        if latest_gold:
            self.base_24k_usd_oz = latest_gold.base_24k_usd or 0.0
            self.dzd_parallel_rate = latest_gold.dzd_parallel_rate or 0.0
            self.market_24k_dzd = helper._r10(latest_gold._get_market_for('24k') or 0.0)

        latest_silver = self.env['silver.rate.history'].search([
            ('is_active', '=', True),
        ], order='effective_date desc, id desc', limit=1)
        if latest_silver:
            self.base_silver_usd_oz = latest_silver.base_silver_usd or 0.0
            if not latest_gold:
                self.dzd_parallel_rate = latest_silver.dzd_parallel_rate or 0.0
            self.silver_market_1000_dzd = helper._r10(latest_silver._get_market_for('1000') or 0.0)

        self.last_update = fields.Datetime.now()
        self._compute_all()

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        helper = self.env['metal.rate.helper']

        latest_gold = self.env['gold.rate.history'].search([
            ('is_active', '=', True),
        ], order='effective_date desc, id desc', limit=1)
        if latest_gold:
            res['base_24k_usd_oz'] = latest_gold.base_24k_usd or 0.0
            res['dzd_parallel_rate'] = latest_gold.dzd_parallel_rate or 0.0
            m24 = helper._r10(latest_gold._get_market_for('24k') or 0.0)
            res['market_24k_dzd'] = m24
            for k, per_mille in self.GOLD_PURITY.items():
                if k != '24k':
                    res[f'market_{k}_dzd'] = helper._r10(m24 * per_mille / 999)

        latest_silver = self.env['silver.rate.history'].search([
            ('is_active', '=', True),
        ], order='effective_date desc, id desc', limit=1)
        if latest_silver:
            res['base_silver_usd_oz'] = latest_silver.base_silver_usd or 0.0
            if not latest_gold:
                res['dzd_parallel_rate'] = latest_silver.dzd_parallel_rate or 0.0
            m1000 = helper._r10(latest_silver._get_market_for('1000') or 0.0)
            res['silver_market_1000_dzd'] = m1000
            for k, per_mille in self.SILVER_PURITY.items():
                if k != '1000':
                    res[f'silver_market_{k}_dzd'] = helper._r10(m1000 * per_mille / 1000)

        res['last_update'] = fields.Datetime.now()
        return res

    @api.onchange('market_24k_dzd')
    def _onchange_market_24k(self):
        helper = self.env['metal.rate.helper']
        if self.market_24k_dzd:
            self.market_24k_dzd = helper._r10(self.market_24k_dzd)

    @api.onchange('silver_market_1000_dzd')
    def _onchange_silver_market_1000(self):
        helper = self.env['metal.rate.helper']
        if self.silver_market_1000_dzd:
            self.silver_market_1000_dzd = helper._r10(self.silver_market_1000_dzd)

    @api.model
    def get_chart_data(self, date_range='all'):
        today = fields.Date.today()
        ranges = {
            'today': (today, today),
            '7d': (today - timedelta(days=7), today),
            '30d': (today - timedelta(days=30), today),
            '90d': (today - timedelta(days=90), today),
            '1y': (today - timedelta(days=365), today),
            'all': (None, None),
        }
        date_from, date_to = ranges.get(date_range, (None, None))

        metal_24k = self.env['metal.type'].search([('purity_percentage', '=', 99.99)], limit=1)
        if not metal_24k:
            return {'data': []}

        domain = [('metal_type_id', '=', metal_24k.id)]
        if date_from:
            domain.append(('effective_date', '>=', date_from))
        if date_to:
            domain.append(('effective_date', '<=', date_to))

        records = self.env['gold.rate.history'].search(
            domain, order='effective_date asc, id desc'
        )

        data = []
        seen = set()
        for rec in records:
            date_key = str(rec.effective_date)
            if date_key in seen:
                continue
            seen.add(date_key)
            data.append({
                'x': date_key,
                'bourse_dzd': rec.bursa_rate or 0.0,
                'market_dzd': rec.market_rate or 0.0,
            })

        return {'data': data}

    @api.model
    def get_silver_chart_data(self, date_range='all'):
        today = fields.Date.today()
        ranges = {
            'today': (today, today),
            '7d': (today - timedelta(days=7), today),
            '30d': (today - timedelta(days=30), today),
            '90d': (today - timedelta(days=90), today),
            '1y': (today - timedelta(days=365), today),
            'all': (None, None),
        }
        date_from, date_to = ranges.get(date_range, (None, None))

        metal_1000 = self.env['metal.type'].search([('purity_percentage', '=', 100.0)], limit=1)
        if not metal_1000:
            return {'data': []}

        domain = [('metal_type_id', '=', metal_1000.id)]
        if date_from:
            domain.append(('effective_date', '>=', date_from))
        if date_to:
            domain.append(('effective_date', '<=', date_to))

        records = self.env['silver.rate.history'].search(
            domain, order='effective_date asc, id desc'
        )

        data = []
        seen = set()
        for rec in records:
            date_key = str(rec.effective_date)
            if date_key in seen:
                continue
            seen.add(date_key)
            data.append({
                'x': date_key,
                'bourse_dzd': rec.bursa_rate or 0.0,
                'market_dzd': rec.market_rate or 0.0,
            })

        return {'data': data}

    def read(self, fnames=None, load='_classic_read'):
        if not self:
            defaults = self.default_get(list(self.env['gold.price.overview'].fields_get().keys()))
            new = self.create(defaults)
            return new.read(fnames=fnames, load=load)
        return super().read(fields=fnames, load=load)

    def action_refresh(self):
        gold_config = self.env['gold.price.api.config']._get_config()
        if gold_config:
            gold_config.fetch_all_rates()
        silver_config = self.env['silver.price.api.config']._get_config()
        if silver_config:
            silver_config.fetch_all_rates()
        self.load_from_db()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'gold.price.overview',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'inline',
        }

    def action_save_rates(self):
        helper = self.env['metal.rate.helper']
        gold_purity_to_pct = {
            999: 99.99, 875: 87.5, 750: 75.0,
            720: 72.0, 710: 71.0, 705: 70.5,
        }
        silver_purity_to_pct = {
            1000: 100.0, 925: 92.5, 500: 50.0,
        }
        for rec in self:
            # ── Save gold rates ──
            for k, per_mille in self.GOLD_PURITY.items():
                pct = gold_purity_to_pct.get(per_mille)
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
                market = helper._r10(getattr(rec, f'market_{k}_dzd') or 0.0)
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

            # ── Save silver rates ──
            for k, per_mille in self.SILVER_PURITY.items():
                pct = silver_purity_to_pct.get(per_mille)
                if not pct:
                    continue
                metal = self.env['metal.type'].search([
                    ('purity_percentage', '=', pct),
                ], limit=1)
                if not metal:
                    continue
                existing = self.env['silver.rate.history'].search([
                    ('metal_type_id', '=', metal.id),
                    ('effective_date', '=', fields.Date.today()),
                ], limit=1)
                market = helper._r10(getattr(rec, f'silver_market_{k}_dzd') or 0.0)
                vals = {
                    'metal_type_id': metal.id,
                    'base_silver_usd': rec.base_silver_usd_oz or 0.0,
                    'dzd_parallel_rate': rec.dzd_parallel_rate or 0.0,
                    'market_rate': market,
                    'effective_date': fields.Date.today(),
                    'is_active': True,
                }
                if existing:
                    existing.write(vals)
                else:
                    self.env['silver.rate.history'].create(vals)
        return {'type': 'ir.actions.client', 'tag': 'reload'}

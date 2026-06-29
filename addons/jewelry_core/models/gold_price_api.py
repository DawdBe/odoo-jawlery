import json
import logging
import re
from datetime import datetime, timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    import requests
except ImportError:
    _logger.warning("requests not installed — gold API fetch will fail")
    requests = None


class GoldPriceApiConfig(models.Model):
    _name = 'gold.price.api.config'
    _description = 'Gold Price API Configuration'
    _rec_name = 'name'

    name = fields.Char(default='Gold API Config', required=True)
    api_url_usd = fields.Char(
        string='Gold API URL',
        default='https://api.gold-api.com/price/XAU',
        help='Returns 24k gold price in USD (per Troy ounce = 31.1035g)')
    api_url_dzd = fields.Char(
        string='DZD Rate URL (scraper)',
        default='https://www.exchangedz.com/rates/usd-to-dzd',
        help='ChangeDA parallel rate source — scraped from this URL')
    dzd_rate_scrape_pattern = fields.Char(
        string='DZD Scrape Pattern',
        default=r'"value":\s*([\d.]+).*?sell.*?"value":\s*([\d.]+)',
        help='Regex with two capture groups: buy rate, sell rate. Uses the SELL rate.')
    usd_price_json_path = fields.Char(
        string='USD JSON Path',
        default='price',
        help='JSON path to extract gold USD price')
    active = fields.Boolean(default=True)
    last_fetch_time = fields.Datetime(string='Last Fetch')
    last_fetch_status = fields.Char(string='Last Fetch Status')
    auto_fetch = fields.Boolean(string='Auto Fetch', default=True,
                                help='Automatically fetch rates on cron')
    interval_hours = fields.Integer(string='Fetch Interval (hours)', default=6)
    parallel_premium_percent = fields.Float(
        string='Parallel Premium %', default=70.0,
        help='Fallback: premium over official rate if scraping fails')
    log_ids = fields.One2many('gold.price.api.log', 'config_id', string='Fetch Logs')

    @api.model
    def _get_config(self):
        return self.search([('active', '=', True)], limit=1)

    def _extract_json_path(self, data, path):
        parts = path.split('.')
        for part in parts:
            if isinstance(data, dict) and part in data:
                data = data[part]
            else:
                return None
        return data

    def fetch_gold_price_usd(self):
        self.ensure_one()
        if not requests:
            raise UserError(_("Python 'requests' library is required for API fetch"))
        try:
            resp = requests.get(self.api_url_usd, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            price_usd = self._extract_json_path(data, self.usd_price_json_path)
            if price_usd is None:
                _logger.warning("Could not extract USD price from: %s", data)
                return None
            return float(price_usd)
        except Exception as e:
            _logger.error("Gold USD API fetch failed: %s", e)
            return None

    def fetch_dzd_parallel_rate(self):
        self.ensure_one()
        if not requests:
            raise UserError(_("Python 'requests' library is required for API fetch"))

        # 1) Try scraping ChangeDA (exchangedz.com)
        rate = self._scrape_changeda(self.api_url_dzd)
        if rate:
            return rate

        # 2) Fallback: official rate + premium
        _logger.info("ChangeDA scrape failed, falling back to official rate + premium")
        fallback_url = 'https://api.exchangerate-api.com/v4/latest/USD'
        try:
            resp = requests.get(fallback_url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            official = self._extract_json_path(data, 'rates.DZD')
            if official:
                premium = 1.0 + (self.parallel_premium_percent / 100.0)
                return float(official) * premium
        except Exception as e:
            _logger.warning("Fallback DZD rate also failed: %s", e)
        return None

    def _scrape_changeda(self, url):
        try:
            resp = requests.get(url, timeout=15, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml',
            })
            resp.raise_for_status()
            html = resp.text

            # Strategy 1: extract JSON-LD ItemList with MonetaryAmount entries
            # Look for the sell rate from the structured data
            patterns = [
                # "value": 236.67 ... sell ... "value": 239.0  (buy then sell)
                r'"value":\s*([\d.]+).*?sell.*?"value":\s*([\d.]+)',
                # Sell: 239.00 (from ticker HTML)
                r'Sell\s*:\s*([\d.]+)',
            ]
            for pat in patterns:
                match = re.search(pat, html, re.DOTALL)
                if match:
                    groups = match.groups()
                    val = float(groups[-1])  # last group = sell rate
                    if 100 < val < 500:
                        _logger.info("ChangeDA scraped rate: 1 USD = %s DZD", val)
                        return val
            _logger.warning("Could not find parallel rate in ChangeDA HTML")
            return None
        except Exception as e:
            _logger.warning("ChangeDA scrape exception: %s", e)
            return None

    def fetch_all_rates(self):
        self.ensure_one()
        usd_price_oz = self.fetch_gold_price_usd()
        dzd_rate = self.fetch_dzd_parallel_rate()
        if usd_price_oz:
            MetalType = self.env['metal.type']
            gold_metals = MetalType.search([('category', 'in', ('or', 'casse'))])
            for metal in gold_metals:
                existing = self.env['gold.rate.history'].search([
                    ('metal_type_id', '=', metal.id),
                    ('effective_date', '=', fields.Date.today()),
                ], limit=1)
                vals = {
                    'metal_type_id': metal.id,
                    'base_24k_usd': usd_price_oz,
                    'dzd_parallel_rate': dzd_rate or 0.0,
                    'effective_date': fields.Date.today(),
                    'is_active': True,
                }
                if existing:
                    existing.write(vals)
                else:
                    self.env['gold.rate.history'].create(vals)
            self.write({
                'last_fetch_time': fields.Datetime.now(),
                'last_fetch_status': 'OK' if usd_price_oz else 'PARTIAL',
            })
            return True
        self.write({
            'last_fetch_time': fields.Datetime.now(),
            'last_fetch_status': 'FAILED',
        })
        return False

    def action_fetch_now(self):
        self.ensure_one()
        ok = self.fetch_all_rates()
        if not ok:
            raise UserError(_("Gold price fetch failed. Check API configuration."))
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }


class GoldPriceApiLog(models.Model):
    _name = 'gold.price.api.log'
    _description = 'Gold API Fetch Log'
    _order = 'fetch_date desc'

    config_id = fields.Many2one('gold.price.api.config', string='Config')
    fetch_date = fields.Datetime(default=fields.Datetime.now)
    status = fields.Selection([
        ('ok', 'Success'),
        ('partial', 'Partial'),
        ('failed', 'Failed'),
    ], string='Status')
    usd_price = fields.Monetary(string='USD Price (per g)')
    dzd_rate = fields.Float(string='DZD Rate')
    market_rate = fields.Monetary(string='DZD Market Rate (per g)')
    error_message = fields.Text(string='Error')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    @api.model
    def log_fetch(self, config, status, usd_price=None, dzd_rate=None, market_rate=None, error=None):
        return self.create({
            'config_id': config.id if config else None,
            'status': status,
            'usd_price': usd_price,
            'dzd_rate': dzd_rate,
            'market_rate': market_rate,
            'error_message': error,
        })


class GoldPriceApiCron(models.Model):
    _inherit = 'ir.cron'

    @api.model
    def _gold_price_auto_fetch(self):
        config = self.env['gold.price.api.config']._get_config()
        if config and config.auto_fetch:
            config.fetch_all_rates()

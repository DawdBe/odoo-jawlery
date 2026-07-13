import json
import logging
from datetime import datetime, timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    import requests
except ImportError:
    _logger.warning("requests not installed — silver API fetch will fail")
    requests = None


class SilverPriceApiConfig(models.Model):
    _name = 'silver.price.api.config'
    _description = 'Silver Price API Configuration'
    _rec_name = 'name'

    name = fields.Char(default='Silver API Config', required=True)
    api_url_usd = fields.Char(
        string='Silver API URL',
        default='https://api.gold-api.com/price/XAG',
        help='Returns silver price in USD (per Troy ounce = 31.1035g)')
    api_url_dzd = fields.Char(
        string='DZD Rate URL (scraper)',
        default='https://www.exchangedz.com/rates/usd-to-dzd',
        help='ChangeDA parallel rate source — scraped from this URL')
    usd_price_json_path = fields.Char(
        string='USD JSON Path',
        default='price',
        help='JSON path to extract silver USD price')
    dzd_rate_scrape_pattern = fields.Char(
        string='DZD Scrape Pattern',
        default=r'"value":\s*([\d.]+).*?sell.*?"value":\s*([\d.]+)',
        help='Regex with two capture groups: buy rate, sell rate. Uses the SELL rate.')
    active = fields.Boolean(default=True)
    last_fetch_time = fields.Datetime(string='Last Fetch')
    last_fetch_status = fields.Char(string='Last Fetch Status')
    auto_fetch = fields.Boolean(string='Auto Fetch', default=True)
    interval_hours = fields.Integer(string='Fetch Interval (hours)', default=6)
    parallel_premium_percent = fields.Float(
        string='Parallel Premium %', default=70.0)
    log_ids = fields.One2many('silver.price.api.log', 'config_id', string='Fetch Logs')

    @api.model
    def _get_config(self):
        return self.search([('active', '=', True)], limit=1)

    def _fetch_silver_price_usd(self):
        self.ensure_one()
        if not requests:
            raise UserError(_("Python 'requests' library is required for API fetch"))
        try:
            resp = requests.get(self.api_url_usd, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            price_usd = self.env['metal.rate.helper']._extract_json_path(data, self.usd_price_json_path)
            if price_usd is None:
                _logger.warning("Could not extract silver USD price from: %s", data)
                return None
            return float(price_usd)
        except Exception as e:
            _logger.error("Silver USD API fetch failed: %s", e)
            return None

    def fetch_all_rates(self):
        self.ensure_one()
        usd_price_oz = self._fetch_silver_price_usd()
        dzd_rate = self.env['metal.rate.helper'].fetch_dzd_rate(self.api_url_dzd, self.parallel_premium_percent)
        if usd_price_oz:
            MetalType = self.env['metal.type']
            silver_purities = [100.0, 92.5, 50.0]
            for purity in silver_purities:
                metal = MetalType.search([('purity_percentage', '=', purity)], limit=1)
                if not metal:
                    continue
                existing = self.env['silver.rate.history'].search([
                    ('metal_type_id', '=', metal.id),
                    ('effective_date', '=', fields.Date.today()),
                ], limit=1)
                prev = self.env['silver.rate.history'].search([
                    ('metal_type_id', '=', metal.id),
                    ('is_active', '=', True),
                ], order='effective_date desc, id desc', limit=1)
                prev_market = prev.market_rate if prev else 0.0
                vals = {
                    'metal_type_id': metal.id,
                    'base_silver_usd': usd_price_oz,
                    'dzd_parallel_rate': dzd_rate or 0.0,
                    'effective_date': fields.Date.today(),
                    'is_active': True,
                }
                if existing:
                    vals['market_rate'] = existing.market_rate or prev_market
                    existing.write(vals)
                else:
                    vals['market_rate'] = prev_market
                    self.env['silver.rate.history'].create(vals)
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
            raise UserError(_("Silver price fetch failed. Check API configuration."))
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }


class SilverPriceApiLog(models.Model):
    _name = 'silver.price.api.log'
    _description = 'Silver API Fetch Log'
    _order = 'fetch_date desc'

    config_id = fields.Many2one('silver.price.api.config', string='Config')
    fetch_date = fields.Datetime(default=fields.Datetime.now)
    status = fields.Selection([
        ('ok', 'Success'),
        ('partial', 'Partial'),
        ('failed', 'Failed'),
    ], string='Status')
    usd_price = fields.Monetary(string='USD Price (per oz)')
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


class SilverPriceApiCron(models.Model):
    _inherit = 'ir.cron'

    @api.model
    def _silver_price_auto_fetch(self):
        config = self.env['silver.price.api.config']._get_config()
        if config and config.auto_fetch:
            config.fetch_all_rates()

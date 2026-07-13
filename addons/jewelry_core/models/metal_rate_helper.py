import logging
import re

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    import requests
except ImportError:
    _logger.warning("requests not installed — API fetch will fail")
    requests = None


class MetalRateHelper(models.AbstractModel):
    _name = 'metal.rate.helper'
    _description = 'Shared computation and fetching logic for gold/silver rate models'

    @staticmethod
    def _r10(val):
        return round(val / 10.0) * 10

    @staticmethod
    def compute_base_dzd(usd_per_oz, dzd_rate, divisor=31.1035):
        return MetalRateHelper._r10(usd_per_oz * dzd_rate / divisor)

    @staticmethod
    def compute_bursa(base_dzd, purity_pct, base_purity=99.99):
        return MetalRateHelper._r10(base_dzd * (purity_pct / base_purity)) if purity_pct else 0

    @staticmethod
    def compute_spread(market, bursa):
        return MetalRateHelper._r10((market or 0.0) - (bursa or 0.0))

    @staticmethod
    def _extract_json_path(data, path):
        parts = path.split('.')
        for part in parts:
            if isinstance(data, dict) and part in data:
                data = data[part]
            else:
                return None
        return data

    @api.model
    def fetch_dzd_rate(self, scrape_url, premium_percent=70.0):
        rate = self._scrape_changeda(scrape_url)
        if rate:
            return rate
        _logger.info("ChangeDA scrape failed, falling back to official rate + premium")
        fallback_url = 'https://api.exchangerate-api.com/v4/latest/USD'
        try:
            resp = requests.get(fallback_url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            official = self._extract_json_path(data, 'rates.DZD')
            if official:
                premium = 1.0 + (premium_percent / 100.0)
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
            patterns = [
                r'"value":\s*([\d.]+).*?sell.*?"value":\s*([\d.]+)',
                r'Sell\s*:\s*<[^>]+>([\d.]+)',
            ]
            for pat in patterns:
                match = re.search(pat, html, re.DOTALL | re.IGNORECASE)
                if match:
                    groups = match.groups()
                    val = float(groups[-1])
                    if 100 < val < 500:
                        _logger.info("ChangeDA scraped rate (sell): 1 USD = %s DZD", val)
                        return val
            _logger.warning("Could not find parallel rate in ChangeDA HTML")
            return None
        except Exception as e:
            _logger.warning("ChangeDA scrape exception: %s", e)
            return None

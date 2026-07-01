from odoo import api, SUPERUSER_ID


def apply_translations(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    lang = env['res.lang']
    lang._activate_lang('fr_FR')
    lang._activate_lang('ar_MA')

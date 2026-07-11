from odoo.addons.jewelry_core.translations import apply_module_translations


def apply_translations(env):
    apply_module_translations(env, 'jewelry_core')
    lang = env['res.lang']
    lang._activate_lang('fr_FR')
    lang._activate_lang('ar_MA')

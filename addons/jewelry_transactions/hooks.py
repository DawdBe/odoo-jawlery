from odoo.addons.jewelry_core.translations import apply_module_translations


def _deactivate_menus(env):
    menus = [
        'stock.int_picking',
        'stock.product_uom_menu',
        'purchase.menu_purchase_rfq',
        'purchase.menu_product_in_config_purchase',
        'purchase.menu_unit_of_measure_in_config_purchase',
        'purchase.menu_procurement_management_supplier_name',
    ]
    for xml_id in menus:
        try:
            menu = env.ref(xml_id, raise_if_not_found=False)
            if menu and menu.active:
                menu.active = False
        except Exception:
            pass


def apply_translations(env):
    apply_module_translations(env, 'jewelry_transactions')
    _deactivate_menus(env)

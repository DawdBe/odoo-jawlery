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


def _migrate_associate_transactions(env):
    Transaction = env['associate.transaction']
    Account = env['associate.account']
    existing = Transaction.search([])
    if not existing:
        return

    for t in existing:
        vals = {}
        if not t.account_id and t.partner_id:
            account = Account.search([('partner_id', '=', t.partner_id.id)], limit=1)
            if not account:
                account = Account.create({'partner_id': t.partner_id.id})
            vals['account_id'] = account.id
        if not t.state:
            vals['state'] = 'posted'
        if not t.origin:
            vals['origin'] = 'manual'
        if not t.user_id:
            vals['user_id'] = env.ref('base.user_admin').id
        if vals:
            t.write(vals)


def apply_translations(env):
    apply_module_translations(env, 'jewelry_transactions')
    _deactivate_menus(env)
    _migrate_associate_transactions(env)

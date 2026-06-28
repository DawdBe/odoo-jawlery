from odoo.addons.jewelry_core.translations import apply_module_translations


def apply_translations(env):
    apply_module_translations(env, 'jewelry_core')

    # Hide Discuss app from navbar
    for xml_id in ['mail.menu_root_discuss', 'mail.mail_menu_technical']:
        try:
            menu = env.ref(xml_id, raise_if_not_found=False)
            if menu and menu.active:
                menu.active = False
        except Exception:
            pass

    # Create inherited view to hide tax fields on product form
    _hide_fields(env, 'product.template', 'product.product_template_form_view', [
        "//field[@name='taxes_id']",
        "//field[@name='supplier_taxes_id']",
    ])


def _hide_fields(env, model, base_xml_id, xpaths):
    View = env['ir.ui.view']
    base = env.ref(base_xml_id, raise_if_not_found=False)
    if not base:
        return
    name = f'{model}.hide.fields'
    if View.search([('name', '=', name)], limit=1):
        return
    arch = '<data>' + ''.join(
        f'<xpath expr="{xp}" position="attributes">'
        f'<attribute name="invisible">1</attribute>'
        f'</xpath>'
        for xp in xpaths
    ) + '</data>'
    View.create({'name': name, 'model': model, 'inherit_id': base.id, 'arch_db': arch})

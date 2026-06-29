{
    'name': 'Jewelry Dashboard',
    'version': '17.0.1.0.0',
    'category': 'Inventory',
    'summary': 'Dashboard 360° — interface temps réel',
    'depends': ['jewelry_accounting', 'jewelry_core'],
    'data': [
        'security/ir.model.access.csv',
        'views/actions.xml',
        'views/dashboard_views.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
    'post_init_hook': 'apply_translations',
}

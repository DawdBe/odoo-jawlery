{
    'name': 'Jewelry Accounting',
    'version': '17.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Rapports et comptabilité — écritures, bilans',
    'depends': ['jewelry_transactions', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_move_views.xml',
        'views/menus.xml',
        'reports/bilan_global_report.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
    'post_init_hook': 'apply_translations',
}

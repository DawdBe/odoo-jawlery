{
    'name': 'Jewelry Core',
    'version': '17.0.1.0.0',
    'category': 'Inventory',
    'summary': 'Socle fondation — métaux, cours, produits, inventaire',
    'depends': ['product', 'stock', 'stock_account', 'uom', 'mail', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'data/metal_type_data.xml',
        'data/sequence_data.xml',
        'data/cron_data.xml',
        'views/metal_type_views.xml',
        'views/gold_rate_views.xml',
        'views/gold_price_api_views.xml',
        'views/gold_price_overview_views.xml',
        'views/product_views.xml',
        'views/partner_views.xml',
        'views/stock_inventory_views.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'jewelry_core/static/src/js/clipboard_fix.js',
            'jewelry_core/static/src/css/metal_type.css',
        ],
    },
    'installable': True,
    'license': 'LGPL-3',
    'post_init_hook': 'apply_translations',
    'demo': [
        'demo/demo_data.xml',
    ],
}

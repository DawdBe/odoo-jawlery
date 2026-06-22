{
    'name': 'My Custom Module',
    'version': '1.0.0',
    'category': 'Custom',
    'summary': 'Custom module example',
    'description': """
        My Custom Module - Custom Odoo Module
        =====================================
        A scaffold module demonstrating Odoo project structure.
    """,
    'author': 'Your Company',
    'website': 'https://yourcompany.com',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/example_model_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}

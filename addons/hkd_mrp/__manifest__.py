{
    'name': 'HKD MRP Production',
    'version': '16.0.1.1.0',
    'summary': 'HKD MRP Production',
    'author': 'Hoa Mai',
    'category': 'Manufacturing',
    'depends': [
        'mrp',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
        'views/mrp_production_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
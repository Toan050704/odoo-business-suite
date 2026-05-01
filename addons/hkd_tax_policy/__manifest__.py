# -*- coding: utf-8 -*-
{
    'name': 'Chính sách thuế HKD',
    'version': '16.0.1.0.3',
    'summary': 'Danh mục cha–con (chính sách thuế HKD); dữ liệu nhóm ngành giống tax_config/tb.tax.category',
    'author': 'Hoa Mai',
    'category': 'Accounting',
    'depends': [ 
        'account',
        'sale_management', 
        'point_of_sale',
        'product',
        'purchase',
        'l10n_vn',
        ],
    'data': [
        'security/ir.model.access.csv',
        'data/hkd_tax_policy_data.xml',
        'data/account_tax_data.xml',
        'views/hkd_tax_policy_views.xml',
        'views/account_tax_views.xml',
        'views/product_template_views.xml',
        'views/purchase_order_views.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}

{
    'name': 'HKD Sales',
    'version': '16.0.1.19.0',
    'summary': 'Tạo invoice ngay khi thanh toán POS',
    'author': 'Hoa Mai',
    'category': 'Point of Sale',
    'depends': [
        'point_of_sale',
        'account',
        'sale_management',
        'sale_stock',
        'stock',
        'hkd_tax_policy',
    ],
    'data': [
        'data/ir_sequence_data.xml',
        'data/hkd_branding_server_action.xml',
        'data/hkd_branding_on_module_update.xml',
        'views/pos_config_views.xml',
        'views/res_partner_so_views.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'assets': {
        'point_of_sale.assets': [
            'hkd_sales/static/src/scss/hkd_pos_flat.scss',
            'hkd_sales/static/src/xml/hkd_pos_chrome.xml',
            'hkd_sales/static/src/js/hkd_pos_payment.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
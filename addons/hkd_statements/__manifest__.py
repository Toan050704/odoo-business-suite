{
    'name': 'HKD Statements',
    'version': '16.0.1.0.0',
    'summary': 'Quản lý sổ S2B, S2C, S2D, S2E',
    'author': 'Hoa Mai',
    'category': '',
    'depends': [
        'base',
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/s2b_statement_views.xml',
        'views/s2c_statement_views.xml',
        'views/s2d_statement_views.xml',
        'views/s2e_statement_views.xml',
        'views/statements_wizard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hkd_statements/static/src/js/statements_filter_button.js',
            'hkd_statements/static/src/xml/statements_filter_button.xml',
            'hkd_statements/static/src/css/s2e_statement.css',
            'hkd_statements/static/src/css/s2d_statement.css',
            'hkd_statements/static/src/css/s2c_statement.css',
            'hkd_statements/static/src/css/s2b_statement.css',
        ],
    },
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
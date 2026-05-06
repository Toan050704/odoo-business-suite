# -*- coding: utf-8 -*-
{
    'name': 'HKD Access Control',
    'version': '16.0.1.0.0',
    'summary': 'Phân quyền và ẩn menu theo vai trò HKD',
    'author': 'Hoa Mai',
    'category': 'Hidden',
    'depends': [
        'hkd_core',
        'contacts',
    ],
    'data': [
        'security/security.xml',
        'views/menu_groups.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}

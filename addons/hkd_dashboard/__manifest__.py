# -*- coding: utf-8 -*-
{
    'name': 'Dashboard',
    'version': '16.0.1.4.0',
    'summary': 'Trung tâm báo cáo HKD: doanh thu, chi phí, so sánh thuế theo chính sách HKD',
    'author': 'Hoa Mai',
    'category': 'Accounting',
    'depends': [
            'account',
            'stock',
            'purchase',
            # 'invoice_account',
            'hkd_tax_policy'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/dashboard_launcher_views.xml',
        'views/vendor_debt_views.xml',
         
    ],
    'assets': {
    'web.assets_backend': [
        'hkd_dashboard/static/lib/chart/chart.umd.js',
        'hkd_dashboard/static/src/css/dashboard.css',
        'hkd_dashboard/static/src/js/dashboard_chart.js',
       
    ],
    },
    'installable': True,
    'license': 'LGPL-3',
}

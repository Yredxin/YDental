{
    'name': 'YDental Settlement and Offline Finance',
    'version': '20.0.1.0.0',
    'license': 'GPL-3',
    'author': 'YDental',
    'depends': ['ydental_exam', 'ydental_print', 'account', 'sale_stock', 'purchase_stock'],
    'data': [
        'data/ydental_settlement_mutex.xml',
        'security/ir.access.csv',
        'report/ydental_settlement_reports.xml',
        'report/ydental_settlement_templates.xml',
        'views/ydental_settlement_templates.xml',
        'views/ydental_settlement_frontdesk.xml',
    ],
    'installable': True,
}

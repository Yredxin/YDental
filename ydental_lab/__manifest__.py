{
    'name': 'YDental Internal Dental Laboratory',
    'summary': 'Qualified vendor work orders, physical receipt and prosthesis stock lifecycle',
    'version': '20.0.1.0.0',
    'category': 'Services',
    'author': 'YDental',
    'license': 'LGPL-3',
    'depends': ['ydental_base', 'ydental_access', 'ydental_followup', 'ydental_treatment',
                'ydental_inventory', 'purchase_stock'],
    'data': [
        'security/ir.access.csv',
        'views/ydental_lab_views.xml',
    ],
    'application': False,
    'installable': True,
}

{
    'name': 'YDental Settlement and Offline Finance',
    'version': '20.0.1.0.0',
    'license': 'GPL-3',
    'author': 'YDental',
    'depends': ['ydental_exam', 'ydental_print', 'ydental_intake', 'account', 'sale_stock', 'purchase_stock'],
    'data': [
        'data/ydental_settlement_mutex.xml',
        'security/ir.access.csv',
        'report/ydental_settlement_reports.xml',
        'report/ydental_settlement_templates.xml',
        'views/ydental_settlement_templates.xml',
        'views/ydental_settlement_frontdesk.xml',
        'views/ydental_synthetic_setup.xml',
        'views/ydental_external_original_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'ydental_settlement/static/src/scss/settlement_lookup.scss',
            'ydental_settlement/static/src/scss/settlement_readonly_actions.scss',
            'ydental_settlement/static/src/scss/settlement_bill_panel.scss',
            'ydental_settlement/static/src/scss/settlement_unpaid.scss',
            'ydental_settlement/static/src/fee_focus/fee_focus.js',
        ],
    },
    'installable': True,
}

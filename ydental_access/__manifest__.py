{
    'name': 'YDental Store Access',
    'summary': 'Store membership, employee lifecycle, authorization and audit',
    'version': '20.0.1.0.0',
    'category': 'Services',
    'author': 'YDental',
    'website': 'https://github.com/Yredxin/YDental',
    'license': 'LGPL-3',
    'depends': ['ydental_base', 'hr', 'auth_signup', 'auth_timeout', 'auth_password_policy', 'auth_totp_mail'],
    'data': [
        'security/ydental_access_security.xml',
        'security/ir.access.csv',
        'data/ydental_access_data.xml',
        'views/ydental_access_templates.xml',
        'views/ydental_access_menus.xml',
    ],
    'assets': {
        'web.assets_backend': ['ydental_access/static/src/store_status/*'],
        'web.assets_frontend': [
            'ydental_access/static/src/scss/_actions.scss',
            'ydental_access/static/src/workspace/workspace.scss',
        ],
    },
    'installable': True,
    'application': False,
}

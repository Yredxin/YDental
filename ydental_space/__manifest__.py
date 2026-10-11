{
    'name': 'YDental Clinic Space',
    'summary': 'Floors, reporting areas, stable workstations and safe resource artwork',
    'version': '20.0.1.0.0',
    'category': 'Services',
    'author': 'YDental',
    'website': 'https://github.com/Yredxin/YDental',
    'license': 'LGPL-3',
    'depends': ['ydental_access', 'web'],
    'external_dependencies': {'python': ['lxml']},
    'data': [
        'security/ir.access.csv',
        'data/ydental_space_data.xml',
        'views/ydental_space_views.xml',
    ],
    'assets': {'web.assets_backend': ['ydental_space/static/src/plan/*', 'ydental_space/static/src/config_form/*']},
    'installable': True,
}

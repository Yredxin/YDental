{
    'name': 'Dental',
    'summary': 'YDental application entry and synthetic PDF samples',
    'version': '20.0.1.0.1',
    'category': 'Services',
    'author': 'YDental',
    'website': 'https://github.com/Yredxin/YDental',
    'license': 'LGPL-3',
    'depends': ['web', 'base_report_wkhtmltox'],
    'data': [
        'security/ydental_base_security.xml',
        'views/ydental_base_templates.xml',
        'views/ydental_base_menus.xml',
        'report/ydental_base_sample_reports.xml',
    ],
    'demo': ['demo/ydental_base_demo.xml'],
    'application': True,
    'installable': True,
}

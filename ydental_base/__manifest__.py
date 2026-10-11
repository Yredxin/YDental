{
    'name': '牙科',
    'summary': 'YDental application entry and project baseline',
    'version': '20.0.1.0.0',
    'category': 'Services',
    'author': 'YDental',
    'website': 'https://github.com/Yredxin/YDental',
    'license': 'LGPL-3',
    'depends': ['web'],
    'data': [
        'security/ydental_base_security.xml',
        'views/ydental_base_templates.xml',
        'views/ydental_base_menus.xml',
    ],
    'demo': ['demo/ydental_base_demo.xml'],
    'application': True,
    'installable': True,
}

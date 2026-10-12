{
    'name': 'YDental Workstation Queue',
    'author': 'YDental',
    'version': '20.0.1.2.0',
    'license': 'LGPL-3',
    'depends': ['ydental_intake', 'ydental_patient', 'ydental_supply', 'ydental_space', 'ydental_access', 'bus'],
    'data': ['security/ydental_queue_security.xml', 'security/ir.access.csv', 'data/ydental_queue_data.xml', 'views/ydental_queue_templates.xml'],
    'assets': {'web.assets_backend': ['ydental_queue/static/src/workstation_status/*']},
    'installable': True,
}

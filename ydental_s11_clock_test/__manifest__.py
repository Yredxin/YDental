{
    'name': 'YDental S11 Synthetic Application Clock',
    'summary': 'Session scoped test clock for the authorized S11 scratch database',
    'version': '20.0.1.0.0',
    'license': 'LGPL-3',
    'depends': ['web', 'ydental_access', 'ydental_queue', 'ydental_intake', 'ydental_supply', 'ydental_patient', 'ydental_inventory',
                'ydental_exam', 'ydental_treatment', 'ydental_lab', 'ydental_settlement', 'ydental_followup'],
    'pre_init_hook': 'pre_init_hook',
    'data': ['security/clock_security.xml', 'views/clock_templates.xml'],
    'installable': True,
    'application': False,
}

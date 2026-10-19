{
    'name': 'YDental Follow-up and Notification Reliability',
    'author': 'YDental',
    'version': '20.0.1.0.0',
    'license': 'LGPL-3',
    'depends': ['ydental_clinical', 'ydental_treatment', 'ydental_access', 'mail', 'web'],
    'data': [
        'security/ir.access.csv',
        'data/ydental_followup_data.xml',
        'views/ydental_followup_templates.xml',
        'views/ydental_followup_views.xml',
    ],
    'installable': True,
}

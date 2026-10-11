{
    'name': 'YDental Patient Identity',
    'version': '20.0.1.0.0',
    'license': 'LGPL-3',
    'depends': ['ydental_access', 'mail', 'phone_validation', 'web'],
    'external_dependencies': {'python': ['phonenumbers']},
    'data': ['security/ir.access.csv', 'data/ydental_patient_data.xml',
             'views/ydental_patient_templates.xml', 'views/ydental_patient_views.xml'],
    'installable': True,
}

{
    'name': 'YDental Clinical Documents',
    'author': 'YDental',
    'version': '20.0.1.0.0',
    'license': 'LGPL-3',
    'depends': ['ydental_queue', 'ydental_patient', 'ydental_intake', 'ydental_access'],
    'data': ['security/ir.access.csv', 'views/ydental_clinical_templates.xml'],
    'installable': True,
}

{
    'name': 'YDental Service Intake',
    'version': '20.0.1.0.0',
    'category': 'Services',
    'summary': 'Versioned service prices and capacity-backed patient intake',
    'license': 'LGPL-3',
    'depends': ['ydental_patient', 'ydental_supply', 'product'],
    'data': ['security/ir.access.csv', 'data/intake.xml', 'views/intake.xml'],
    'installable': True,
    'application': False,
}

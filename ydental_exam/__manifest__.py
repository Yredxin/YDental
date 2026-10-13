{
    'name': 'YDental Examination Workbench',
    'version': '20.0.1.0.0',
    'license': 'GPL-3',
    'author': 'YDental',
    'depends': ['ydental_print'],
    'data': ['security/ir.access.csv', 'report/ydental_exam_reports.xml',
             'report/ydental_exam_templates.xml', 'views/ydental_exam_templates.xml'],
    'assets': {'web.assets_frontend': ['ydental_exam/static/src/workbench/workbench.js']},
    'installable': True,
}

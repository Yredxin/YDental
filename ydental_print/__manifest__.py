{
    'name': 'YDental Controlled Demonstration PDFs',
    'version': '20.0.1.0.0',
    'license': 'GPL-3',
    'author': 'YDental',
    'depends': ['ydental_treatment', 'base_report_wkhtmltox'],
    'data': ['report/ydental_print_reports.xml', 'report/ydental_print_templates.xml', 'views/ydental_print_templates.xml', 'views/ydental_document_templates.xml', 'views/ydental_consent_templates.xml'],
    'assets': {'web.assets_frontend': ['ydental_print/static/src/print/print.js', 'ydental_print/static/src/print/print.scss', 'ydental_print/static/src/documents_query/documents_query.js', 'ydental_print/static/src/documents_query/documents_query.scss']},
    'installable': True,
}

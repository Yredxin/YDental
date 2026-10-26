{
    'name': 'YDental Controlled Demonstration PDFs',
    'version': '20.0.1.0.0',
    'license': 'GPL-3',
    'author': 'YDental',
    'depends': ['ydental_treatment', 'base_report_wkhtmltox', 'ydental_access', 'ydental_inventory'],
    'data': ['report/ydental_print_reports.xml', 'report/ydental_print_templates.xml', 'views/ydental_print_templates.xml', 'views/ydental_document_templates.xml', 'views/ydental_consent_templates.xml'],
    'assets': {'web.assets_frontend': ['ydental_print/static/src/print/print.js', 'ydental_print/static/src/print/print.scss', 'ydental_print/static/src/documents_query/documents_query.js', 'ydental_print/static/src/documents_query/documents_query.scss', 'ydental_print/static/src/documents_header/documents_header.scss', 'ydental_print/static/src/documents_originals/documents_originals.scss', 'ydental_print/static/src/documents_actions/documents_actions.scss', 'ydental_print/static/src/documents_spacing/documents_spacing.scss']},
    'installable': True,
}

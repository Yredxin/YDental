{
    'name': 'YDental Source-backed Operating Reports',
    'version': '20.0.1.1.0',
    'license': 'GPL-3',
    'author': 'YDental',
    'depends': ['ydental_lab', 'ydental_followup'],
    'data': ['views/ydental_reporting_templates.xml'],
    'assets': {'web.assets_frontend': [
        'ydental_reporting/static/src/reporting/reporting.scss',
        'ydental_reporting/static/src/reporting/reporting.js',
        'ydental_reporting/static/src/report_filters/report_filters.scss',
        'ydental_reporting/static/src/report_filters/report_filters.js',
    ]},
    'installable': True,
}

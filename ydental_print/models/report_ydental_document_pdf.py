from odoo import models
from odoo.exceptions import AccessError


class YDentalDocumentPdf(models.AbstractModel):
    _name = 'report.ydental_print.ydental_document_pdf'
    _description = 'Controlled static QWeb demonstration PDF values'

    def _get_report_values(self, docids, data=None):
        payload = self.env['ydental.print.service']._validate_render_scope()
        if docids != [payload['source_id']] or data and set(data) - {'report_type', 'debug'} or data and data.get('debug', False) is not False:
            raise AccessError(self.env._('access_denied: Arbitrary report arguments are unavailable.'))
        return {'doc_ids': docids, 'doc_model': 'ydental.print.job', 'docs': [], 'p': payload}

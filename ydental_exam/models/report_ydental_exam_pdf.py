from odoo import models
from odoo.exceptions import AccessError


class YDentalExamPdf(models.AbstractModel):
    _name = 'report.ydental_exam.ydental_exam_pdf'
    _description = 'Controlled unsigned examination result PDF'

    def _get_report_values(self, docids, data=None):
        payload = self.env['ydental.exam.service']._validate_pdf_scope()
        if docids != [payload['result_id']] or data and set(data) - {'report_type', 'debug'} or data and data.get('debug', False) is not False:
            raise AccessError(self.env._('access_denied: Arbitrary report arguments are unavailable.'))
        return {'doc_ids': docids, 'doc_model': 'ydental.exam.result', 'docs': [], 'p': payload}

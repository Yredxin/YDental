from odoo import models
from odoo.exceptions import AccessError


class YDentalSettlementPdf(models.AbstractModel):
    _name = 'report.ydental_settlement.ydental_settlement_pdf'
    _description = 'Bound synthetic settlement, receipt and refund PDF'

    def _get_report_values(self, docids, data=None):
        payload = self.env['ydental.settlement.service']._validate_pdf_scope()
        if docids != [payload['source_id']] or data and set(data) - {'report_type', 'debug'} or data and data.get('debug', False) is not False:
            raise AccessError(self.env._('access_denied: Arbitrary settlement report arguments are unavailable.'))
        return {'doc_ids': docids, 'doc_model': 'ydental.settlement.receipt', 'docs': [], 'p': payload}

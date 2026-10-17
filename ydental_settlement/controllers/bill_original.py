from odoo import http
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request

from .settlement import HEADERS, YDentalSettlement


class YDentalBillOriginal(YDentalSettlement):
    @http.route('/ydental/settlement/bill-original/create/<int:invoice_id>', type='http', auth='user', methods=['POST'])
    def create_bill_original(self, invoice_id, revision, key, previous_id=None, **kwargs):
        try:
            service = self._service(int(revision))
            service._store_bill_original(invoice_id, key, int(previous_id) if previous_id else None)
            return self._html_feedback('accepted')
        except (AccessError, UserError, ValidationError, ValueError) as error:
            return request.make_json_response({'error': str(error)}, status=403 if isinstance(error, AccessError) else 409, headers=HEADERS)

    @http.route('/ydental/settlement/bill-original/<int:original_id>', type='http', auth='user', methods=['GET'])
    def bill_original(self, original_id, **kwargs):
        try:
            raw, digest = self._service()._bill_original_bytes(original_id)
            return request.make_response(raw, headers=HEADERS + [('Content-Type', 'application/pdf'),
                ('Content-Disposition', 'attachment; filename="internal-bill-original.pdf"'),
                ('X-YDental-PDF-SHA256', digest)])
        except (AccessError, UserError, ValidationError) as error:
            return request.make_json_response({'error': str(error)}, status=403 if isinstance(error, AccessError) else 409, headers=HEADERS)

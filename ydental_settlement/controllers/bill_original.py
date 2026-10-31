from odoo import http
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request
from odoo.addons.ydental_access.controllers.diagnostics import observed_http
from odoo.addons.ydental_access.diagnostics import record_exception, update_context

from .settlement import HEADERS, YDentalSettlement


class YDentalBillOriginal(YDentalSettlement):
    @http.route('/ydental/settlement/bill-original/create/<int:invoice_id>', type='http', auth='user', methods=['POST'])
    @observed_http('settlement.original.create')
    def create_bill_original(self, invoice_id, revision, key, previous_id=None, **kwargs):
        try:
            update_context(stage='request.parse')
            parsed_revision = int(revision)
            update_context(stage='authorization')
            service = self._service(parsed_revision)
            return_patient_id = self._return_patient(service, kwargs.get('return_patient_id'))
            update_context(stage='request.parse')
            parsed_previous = int(previous_id) if previous_id else None
            update_context(stage='business.call')
            service._store_bill_original(invoice_id, key, parsed_previous)
        except (AccessError, UserError, ValidationError, ValueError) as error:
            record_exception(error, 'settlement.original.create')
            return request.make_json_response({'error': str(error)}, status=403 if isinstance(error, AccessError) else 409, headers=HEADERS)
        return self._html_feedback('accepted', return_patient_id)

    @http.route('/ydental/settlement/bill-original/<int:original_id>', type='http', auth='user', methods=['GET'])
    @observed_http('settlement.original.download')
    def bill_original(self, original_id, **kwargs):
        try:
            raw, digest = self._service()._bill_original_bytes(original_id)
            return request.make_response(raw, headers=HEADERS + [('Content-Type', 'application/pdf'),
                ('Content-Disposition', 'attachment; filename="internal-bill-original.pdf"'),
                ('X-YDental-PDF-SHA256', digest)])
        except (AccessError, UserError, ValidationError) as error:
            record_exception(error, 'settlement.original.download')
            return request.make_json_response({'error': str(error)}, status=403 if isinstance(error, AccessError) else 409, headers=HEADERS)

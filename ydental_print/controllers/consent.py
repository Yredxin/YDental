import base64

from odoo import http
from odoo.exceptions import AccessError, UserError
from odoo.http import request

from .documents import YDentalDocuments
from .printing import HEADERS


class YDentalConsentDocuments(YDentalDocuments):
    @http.route('/ydental/documents/consent', type='http', auth='user', methods=['POST'], max_content_length=8000000)
    def consent(self, operation, revision, **kwargs):
        try:
            service = self._service(int(revision))
            if operation == 'consent_upload':
                uploaded = kwargs['file']
                raw = uploaded.read(5000001)
                arguments = {'original_id': int(kwargs['original_id']), 'filename': uploaded.filename,
                    'content': base64.b64encode(raw).decode('ascii')}
            elif operation == 'consent_verify':
                arguments = {'evidence_id': int(kwargs['evidence_id']), 'conclusion': kwargs['conclusion'], 'reason': kwargs['reason']}
            elif operation == 'consent_status':
                arguments = {'patient_id': int(kwargs['patient_id'])}
            elif operation == 'consent_download':
                arguments = {'evidence_id': int(kwargs['evidence_id'])}
            else:
                raise ValueError('invalid_action')
            result = service._original_operate(operation, arguments)
            if operation == 'consent_download':
                raw, checksum = result
                return request.make_response(raw, headers=HEADERS + [('Content-Type', 'application/pdf'),
                    ('Content-Disposition', 'attachment; filename="ydental-consent-upload.pdf"'), ('X-YDental-PDF-SHA256', checksum)])
            return self._page(service, result=result)
        except (AccessError, UserError, ValueError, TypeError, KeyError) as error:
            access = request.env['ydental.access.service']
            access._denial('document.consent')
            access._audit('document.consent', 'medical', request.env.user, result='denied', source='document_original',
                after={'failure_kind': 'permission' if isinstance(error, AccessError) else 'request'})
            return request.make_json_response({'error': 'access_denied' if isinstance(error, AccessError) else 'request_failed',
                'message': str(error)}, status=403 if isinstance(error, AccessError) else 409, headers=HEADERS)

    @http.route('/ydental/documents/selection', type='http', auth='user', methods=['POST'], max_content_length=12000)
    def source_selection(self, revision, document_ids, mode, template_id=None, **kwargs):
        try:
            service = self._service(int(revision))
            selected_ids = [int(value.strip()) for value in document_ids.split(',')]
            result = service._original_operate('select_clinical_sources', {'document_ids': selected_ids, 'mode': mode,
                'template_id': int(template_id) if template_id else None})
            return self._page(service, result=result)
        except (AccessError, UserError, ValueError, TypeError, KeyError) as error:
            access = request.env['ydental.access.service']
            access._denial('document.source_selection')
            access._audit('document.source_selection', 'medical', request.env.user, result='denied', source='document_original')
            return request.make_json_response({'error': 'access_denied' if isinstance(error, AccessError) else 'request_failed',
                'message': str(error)}, status=403 if isinstance(error, AccessError) else 409, headers=HEADERS)

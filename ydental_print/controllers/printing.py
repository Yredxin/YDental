import json

from odoo import http
from odoo.exceptions import AccessError, UserError
from odoo.http import request


HEADERS = [('Cache-Control', 'no-store, private, max-age=0'), ('Pragma', 'no-cache'),
           ('X-Content-Type-Options', 'nosniff'), ('Referrer-Policy', 'no-referrer')]


class YDentalPrinting(http.Controller):
    def _service(self, revision=None):
        access = request.env['ydental.access.service']
        session = access._session_for_key(request.session.sid[:42])
        return access._bind(session, revision).with_context(lang='zh_CN').env['ydental.print.service']

    @http.route('/ydental/print', type='http', auth='user', methods=['GET'])
    def workbench(self, **kwargs):
        service = self._service()
        revision = service.env['ydental.access.service']._scope().ydental_revision
        try:
            choices = service._choices()
        except (AccessError, UserError):
            choices = []
        return request.render('ydental_print.ydental_print_page', {'revision': revision, 'choices': choices}, headers=HEADERS)

    @http.route('/ydental/print/action', type='http', auth='user', methods=['POST'], max_content_length=12000)
    def action(self, operation, revision, payload):
        try:
            service = self._service(int(revision))
            result = service._operate(operation, json.loads(payload))
            if operation in ('pdf_view', 'download', 'print_request'):
                pdf, pdf_digest = result
                return request.make_response(pdf, headers=HEADERS + [('Content-Type', 'application/pdf'),
                    ('Content-Disposition', ('attachment' if operation == 'download' else 'inline') + '; filename="ydental-demonstration.pdf"'),
                    ('X-YDental-PDF-SHA256', pdf_digest)])
            return request.make_json_response(result, headers=HEADERS)
        except (AccessError, UserError, ValueError, TypeError, KeyError) as error:
            access = request.env['ydental.access.service']
            action = operation if operation in ('preview', 'generate', 'pdf_view', 'download', 'print_request') else 'invalid_action'
            access._denial('print.' + action)
            # Failed actions leave nonsensitive metadata, never source IDs or text.
            access._audit('print.' + action, 'export', request.env.user,
                result='denied' if isinstance(error, AccessError) else 'failed', source='controlled_demo_pdf',
                after={'paper_output': 'unknown'})
            code = 'access_denied' if isinstance(error, AccessError) else 'version_conflict' if isinstance(error, UserError) and str(error).startswith('version_conflict:') else 'request_failed'
            return request.make_json_response({'error': code, 'message': request.env._('PDF request failed. Refresh the source and check current permissions. No paper output is verified.')},
                status=403 if isinstance(error, AccessError) else 409, headers=HEADERS)

import json
import secrets

from odoo import http
from odoo.exceptions import AccessError, UserError
from odoo.http import request

from .printing import HEADERS


class YDentalDocuments(http.Controller):
    def _service(self, revision=None):
        access = request.env['ydental.access.service']
        session = access._session_for_key(request.session.sid[:42])
        return access._bind(session, revision).with_context(lang='zh_CN').env['ydental.print.service']

    def _page(self, service, **values):
        result = service._original_workbench()
        result.update({'revision': service.env['ydental.access.service']._scope().ydental_revision,
            'preview': None, 'result': None, 'selection': None, 'key': secrets.token_hex(16), 'error': None})
        result.update(values)
        return request.render('ydental_print.ydental_document_page', result, headers=HEADERS)

    @http.route('/ydental/documents', type='http', auth='user', methods=['GET'])
    def workbench(self, **kwargs):
        request.update_context(lang='zh_CN')
        return self._page(self._service())

    @http.route('/ydental/documents/action', type='http', auth='user', methods=['POST'], max_content_length=60000)
    def action(self, operation, revision, payload=None, **kwargs):
        request.update_context(lang='zh_CN')
        try:
            service = self._service(int(revision))
            if payload is not None:
                arguments = json.loads(payload)
            elif operation == 'preview':
                kind, source_id, version = kwargs['selection'].split(':')
                arguments = {'kind': kind, 'source_id': int(source_id), 'version': int(version),
                    'purpose': kwargs.get('purpose') or None, 'template_id': int(kwargs['template_id']) if kwargs.get('template_id') else None}
            elif operation == 'generate':
                arguments = json.loads(kwargs['selection'])
                arguments.update({'expected_digest': kwargs['expected_digest'], 'key': kwargs['key'],
                    'previous_id': int(kwargs['previous_id']) if kwargs.get('previous_id') else None})
            elif operation in ('download', 'pdf_view', 'print_request'):
                arguments = {'original_id': int(kwargs['original_id'])}
            elif operation == 'template_create':
                arguments = {name: kwargs[name] for name in ('name', 'kind', 'version', 'body', 'applicability')}
                arguments.update({'synthetic': kwargs.get('synthetic') == 'on', 'paper': kwargs.get('paper', 'a4'),
                    'allow_excerpt': kwargs.get('allow_excerpt') == 'on', 'approval_reference': kwargs.get('approval_reference') or None})
            elif operation == 'template_review':
                arguments = {'template_id': int(kwargs['template_id']), 'action': kwargs['action']}
            else:
                arguments = kwargs
            result = service._original_operate(operation, arguments)
            if operation in ('pdf_view', 'download', 'print_request'):
                raw, checksum = result
                return request.make_response(raw, headers=HEADERS + [('Content-Type', 'application/pdf'),
                    ('Content-Disposition', ('attachment' if operation == 'download' else 'inline') + '; filename="ydental-document-original.pdf"'),
                    ('X-YDental-PDF-SHA256', checksum)])
            if operation == 'export':
                return request.make_response(result, headers=HEADERS + [('Content-Type', 'application/zip'),
                    ('Content-Disposition', 'attachment; filename="ydental-document-originals.zip"')])
            if payload is not None:
                return request.make_json_response(result, headers=HEADERS)
            if operation == 'preview':
                return self._page(service, preview=result, selection=json.dumps(arguments))
            return self._page(service, result=result)
        except (AccessError, UserError, ValueError, TypeError, KeyError) as error:
            access = request.env['ydental.access.service']
            access._denial('document.action')
            access._audit('document.action', 'export', request.env.user, result='denied', source='document_original',
                after={'paper_output': 'unknown', 'failure_kind': 'permission' if isinstance(error, AccessError) else 'request_or_engine'})
            code = 'access_denied' if isinstance(error, AccessError) else 'request_failed'
            return request.make_json_response({'error': code, 'message': str(error)}, status=403 if isinstance(error, AccessError) else 409, headers=HEADERS)

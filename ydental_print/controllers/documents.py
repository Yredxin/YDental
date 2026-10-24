import json
import secrets
from urllib.parse import urlencode

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
        term = values.pop('term', '')
        page = values.pop('page', 1)
        result = service._original_workbench(term=term, page=page)
        result.update({'revision': service.env['ydental.access.service']._scope().ydental_revision,
            'preview': None, 'result': None, 'selection': None, 'key': secrets.token_hex(16), 'error': None})
        result.update(values)
        result['previous_originals'] = []
        if values.get('preview') and values.get('selection'):
            selected = json.loads(values['selection'])
            authorized, source, _selected, _category = service._original_authorize(
                selected['kind'], selected['source_id'], selected['version'], selected.get('purpose'))
            store = authorized.env['ydental.access.service']._scope().ydental_store_id
            source_ids = source.ids
            if selected['kind'] == 'clinical_summary':
                source_ids = authorized.env['ydental.document.selection'].sudo().search([
                    ('ydental_store_id', '=', store.id), ('scope_sha256', '=', source.scope_sha256)]).ids
            latest = authorized.env['ydental.document.original'].sudo().search([
                ('store_id', '=', store.id), ('kind', '=', selected['kind']),
                ('source_model', '=', source._name), ('source_id', 'in', source_ids)],
                order='version desc', limit=1)
            if latest:
                authorized._original_reauthorize(latest)
                result['previous_originals'] = [{'id': latest.id, 'title': latest.source_facts['title'],
                    'patient_number': latest.patient_id.ydental_number, 'version': latest.version}]
        result['search_url'] = lambda number: '/ydental/documents?' + urlencode({'q': term, 'page': number})
        return request.render('ydental_print.ydental_document_page', result, headers=HEADERS)

    @http.route('/ydental/documents', type='http', auth='user', methods=['GET'])
    def workbench(self, **kwargs):
        request.update_context(lang='zh_CN')
        try:
            return self._page(self._service(), term=kwargs.get('q', ''), page=int(kwargs.get('page', '1')))
        except (AccessError, UserError, ValueError, TypeError) as error:
            return request.make_json_response({'error': str(error)}, status=403 if isinstance(error, AccessError) else 409, headers=HEADERS)

    @http.route('/ydental/documents/action', type='http', auth='user', methods=['POST'], max_content_length=8000000)
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
            elif operation == 'export':
                arguments = {'original_ids': [int(value.strip()) for value in kwargs['original_ids'].split(',')]}
            elif operation == 'print_failure':
                arguments = {'request_audit_id': int(kwargs['request_audit_id']), 'reason': kwargs['reason'], 'simulated': True}
            elif operation == 'template_create':
                arguments = {name: kwargs[name] for name in ('name', 'kind', 'version', 'body', 'applicability')}
                arguments.update({'synthetic': kwargs.get('synthetic') == 'on', 'paper': kwargs.get('paper', 'a4'),
                    'allow_excerpt': kwargs.get('allow_excerpt') == 'on', 'approval_reference': kwargs.get('approval_reference') or None,
                    'accepted_previous_template_ids': [int(value.strip()) for value in kwargs.get('accepted_previous_template_ids', '').split(',') if value.strip()]})
            elif operation == 'template_review':
                arguments = {'template_id': int(kwargs['template_id']), 'action': kwargs['action']}
            else:
                arguments = kwargs
            result = service._original_operate(operation, arguments)
            if operation in ('pdf_view', 'download', 'print_request', 'consent_download'):
                raw, checksum = result
                return request.make_response(raw, headers=HEADERS + [('Content-Type', 'application/pdf'),
                    ('Content-Disposition', ('attachment' if operation in ('download', 'consent_download') else 'inline') + '; filename="ydental-document-original.pdf"'),
                    ('X-YDental-PDF-SHA256', checksum)])
            if operation == 'export':
                return request.make_response(result, headers=HEADERS + [('Content-Type', 'application/zip'),
                    ('Content-Disposition', 'attachment; filename="ydental-document-originals.zip"')])
            if payload is not None:
                return request.make_json_response(result, headers=HEADERS)
            if operation == 'preview':
                return self._page(service, preview=result, selection=json.dumps(arguments),
                    term=kwargs.get('q', ''), page=int(kwargs.get('page', '1')))
            return self._page(service, result=result, term=kwargs.get('q', ''), page=int(kwargs.get('page', '1')))
        except (AccessError, UserError, ValueError, TypeError, KeyError) as error:
            access = request.env['ydental.access.service']
            access._denial('document.action')
            access._audit('document.action', 'export', request.env.user, result='denied', source='document_original',
                after={'paper_output': 'unknown', 'failure_kind': 'permission' if isinstance(error, AccessError) else 'request_or_engine'})
            code = 'access_denied' if isinstance(error, AccessError) else 'request_failed'
            return request.make_json_response({'error': code, 'message': str(error)}, status=403 if isinstance(error, AccessError) else 409, headers=HEADERS)

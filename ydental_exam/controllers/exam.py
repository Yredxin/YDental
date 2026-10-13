import json

from odoo import http
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request


HEADERS = [('Cache-Control', 'no-store, private, max-age=0'),
           ('X-Content-Type-Options', 'nosniff'), ('Referrer-Policy', 'no-referrer')]


class YDentalExam(http.Controller):
    def _service(self, revision=None, connection=None):
        access = request.env['ydental.access.service']
        session = access._session_for_key(request.session.sid[:42])
        access = access._bind(session, revision)
        if connection:
            access = access.env['ydental.queue.service']._bind_connection(connection)
        return access.env['ydental.exam.service']

    @http.route('/ydental/exam', type='http', auth='user', methods=['GET'])
    def workbench(self, **kwargs):
        service = self._service()
        store = service._store()
        queue = service.env['ydental.queue.service']
        execution = queue._actor_execution()
        if execution and execution.ydental_store_id != store:
            execution = False
        candidates = service.env['ydental.treatment.line'].sudo().search([
            ('ydental_store_id', '=', store.id), ('ydental_order_id.ydental_kind', '=', 'exam'),
            ('ydental_order_id.state', '=', 'issued')], order='id desc', limit=100)
        lines = service.env['ydental.treatment.line'].sudo()
        for candidate in candidates:
            try:
                service._line(candidate.id)
            except (AccessError, UserError):
                continue
            lines |= candidate
        results = service._model('result').search([('ydental_line_id', 'in', lines.ids)])
        events = service.env['ydental.treatment.event'].sudo().browse(results.ydental_event_id.ids)
        for result in results:
            service._audit('view', result, {'version': result.ydental_version})
        access = service.env['ydental.access.service']
        member = access._membership(service.env.uid, store.id)
        medical_document = service.env['ydental.clinical.document'].sudo().search([
            ('ydental_current_execution_id', '=', execution.id)], limit=1) if (
                execution and execution.ydental_category == 'medical' and execution.state == 'serving') else False
        mappings = service.env['ydental.intake.mapping'].sudo().search([
            ('ydental_store_id', '=', store.id), ('ydental_catalog_id.ydental_kind', '=', 'exam')])
        bound_catalogs = service._model('template').search([
            ('ydental_store_id', '=', store.id)]).ydental_catalog_id.ids
        return request.render('ydental_exam.ydental_exam_page', {
            'store': store, 'revision': access._scope().ydental_revision,
            'execution': execution if execution and execution.state == 'serving' else False,
            'lines': lines, 'results': results, 'events': events,
            'can_write': access._levels(member)['exam'] == 'write',
            'can_medical_write': access._levels(member)['medical'] == 'write',
            'actor_id': service.env.uid,
            'medical_document': medical_document,
            'business_date': service.env['ydental.supply.service']._date(store),
            'unbound_mappings': mappings.filtered(lambda mapping: mapping.ydental_catalog_id.id not in bound_catalogs),
            'line_labels': dict(lines._fields['state']._description_selection(service.env)),
            'result_labels': dict(results._fields['state']._description_selection(service.env)),
        }, headers=HEADERS)

    @http.route('/ydental/exam/action', type='http', auth='user', methods=['POST'], max_content_length=7500000)
    def action(self, operation, revision, connection, payload, key):
        try:
            service = self._service(int(revision), connection)
            args = json.loads(payload)
            response = service._operate(operation, args, key)
            return request.make_json_response(response, headers=HEADERS)
        except (AccessError, UserError, ValidationError, ValueError, TypeError, KeyError) as error:
            request.env['ydental.access.service']._denial('exam.action')
            return request.make_json_response({'error': str(error)},
                status=403 if isinstance(error, AccessError) else 409, headers=HEADERS)

    @http.route('/ydental/exam/result/<int:line_id>', type='http', auth='user', methods=['GET'])
    def result(self, line_id, **kwargs):
        try:
            return request.make_json_response(self._service()._view(line_id), headers=HEADERS)
        except (AccessError, UserError, ValidationError) as error:
            request.env['ydental.access.service']._denial('exam.view')
            return request.make_json_response({'error': str(error)}, status=403, headers=HEADERS)

    @http.route('/ydental/exam/report/<int:line_id>/<int:version>', type='http', auth='user', methods=['GET'])
    def report(self, line_id, version, **kwargs):
        try:
            service = self._service().with_context(lang='zh_CN')
            pdf, digest = service._pdf(line_id, version)
            return request.make_response(pdf, headers=HEADERS + [('Content-Type', 'application/pdf'),
                ('Content-Disposition', 'attachment; filename="ydental-examination-demo.pdf"'),
                ('X-YDental-PDF-SHA256', digest)])
        except (AccessError, UserError, ValidationError) as error:
            request.env['ydental.access.service']._denial('exam.report')
            return request.make_json_response({'error': str(error)}, status=403 if isinstance(error, AccessError) else 409,
                headers=HEADERS)

    @http.route('/ydental/exam/attachment/<int:line_id>/<int:attachment_id>', type='http', auth='user', methods=['GET'])
    def attachment(self, line_id, attachment_id, **kwargs):
        try:
            raw, mimetype, name = self._service()._attachment_download(line_id, attachment_id)
            return request.make_response(raw, headers=HEADERS + [('Content-Type', mimetype),
                ('Content-Disposition', 'attachment; filename="examination-evidence"')])
        except (AccessError, UserError, ValidationError) as error:
            request.env['ydental.access.service']._denial('exam.attachment')
            return request.make_json_response({'error': str(error)}, status=403 if isinstance(error, AccessError) else 409,
                headers=HEADERS)

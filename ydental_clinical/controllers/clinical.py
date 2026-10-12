import json

from odoo import http
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request

from ..models.ydental_clinical_service import TEXT_FIELDS, TEETH


class YDentalClinical(http.Controller):

    def _service(self, revision=None, connection=None):
        access = request.env['ydental.access.service']
        session = access._session_for_key(request.session.sid[:42])
        service = access._bind(session, revision).env['ydental.clinical.service']
        if connection:
            service = service._queue()._bind_connection(connection).env['ydental.clinical.service']
        return service

    @http.route('/ydental/clinical', type='http', auth='user', methods=['GET'])
    def workbench(self, document_id=None, purpose=None, **kwargs):
        service = self._service()
        store = service._access()
        queue = service._queue()
        execution = queue._actor_execution()
        if execution and execution.ydental_category != 'medical':
            execution = False
        doc = None
        snapshot = None
        if document_id:
            snapshot = service._read(int(document_id), purpose)
            doc = service._model().browse(snapshot['document_id'])
        elif execution:
            doc = service._model().search([('ydental_execution_id', '=', execution.id)], limit=1)
            if doc:
                snapshot = service._read(doc.id)
        pending = service.env['ydental.clinical.document'].search([
            ('ydental_store_id', '=', store.id), ('state', '=', 'pending')], order='id desc', limit=100)
        fields = [('chief_complaint', request.env._('Chief complaint')), ('history', request.env._('History')),
            ('findings', request.env._('Findings')), ('diagnosis', request.env._('Diagnosis')),
            ('treatment_plan', request.env._('Treatment plan')), ('suggested_materials', request.env._('Suggested materials')),
            ('follow_up', request.env._('Follow-up'))]
        members = service.env['ydental.access.membership'].sudo().search([
            ('ydental_store_id', '=', store.id), ('active', '=', True)])
        candidates = members.ydental_user_id.filtered(lambda user: doc and service._eligible_responsible(doc, user))
        return request.render('ydental_clinical.ydental_clinical_page', {
            'store': store, 'execution': execution, 'doc': doc, 'snapshot': snapshot, 'pending': pending,
            'state_labels': dict(service._model()._fields['state']._description_selection(service.env)),
            'kind_labels': dict(service._model('version')._fields['ydental_kind']._description_selection(service.env)),
            'can_handover': bool(execution and execution.state == 'serving' and (not doc or doc.ydental_execution_id == execution)),
            'revision': service.env['ydental.access.service']._scope().ydental_revision,
            'fields': fields, 'teeth_rows': [[q * 10 + n for n in (range(8, 0, -1) if q in (1, 4) else range(1, 9))] for q in range(1, 5)] +
                [[q * 10 + n for n in (range(5, 0, -1) if q in (5, 8) else range(1, 6))] for q in range(5, 9)],
            'versions': service._model('version').search([('ydental_document_id', '=', doc.id)], limit=50) if doc else [],
            'content': snapshot['content'] if snapshot else service._empty(), 'candidates': candidates,
            'status': queue._status(), 'heartbeat': queue._settings()[0],
        }, headers=[('Cache-Control', 'no-store')])

    @http.route('/ydental/clinical/action', type='http', auth='user', methods=['POST'], max_content_length=100000)
    def action(self, operation, revision, connection, payload):
        try:
            service = self._service(int(revision), connection)
            args = json.loads(payload)
            result = service._operate(operation, args)
            return request.make_json_response(result, headers=[('Cache-Control', 'no-store')])
        except (AccessError, UserError, ValueError, TypeError, KeyError) as error:
            request.env['ydental.access.service']._denial('clinical.action')
            return request.make_json_response({'error': str(error)}, status=403 if isinstance(error, AccessError) else 409,
                headers=[('Cache-Control', 'no-store')])

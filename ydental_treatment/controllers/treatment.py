import json

from odoo import http
from odoo.exceptions import AccessError, UserError
from odoo.http import request


class YDentalTreatment(http.Controller):
    def _service(self, revision=None, connection=None):
        access = request.env['ydental.access.service']
        session = access._session_for_key(request.session.sid[:42])
        access = access._bind(session, revision)
        if connection:
            access = access.env['ydental.queue.service']._bind_connection(connection)
        return access.env['ydental.treatment.service']

    @http.route('/ydental/treatment', type='http', auth='user', methods=['GET'])
    def workbench(self, prices=None, **kwargs):
        service = self._service()
        role = 'price' if prices == '1' else 'medical'
        try:
            store = service._access(role, write=False)
        except AccessError:
            role = 'pharmacy'
            store = service._access(role, write=False)
        queue = service.env['ydental.queue.service']
        execution = queue._actor_execution()
        if execution and execution.ydental_category != role:
            execution = False
        patient = execution.ydental_patient_id if execution else False
        doc = service.env['ydental.clinical.service']._model().search([
            ('ydental_current_execution_id', '=', execution.id)], limit=1) if execution and role == 'medical' else False
        domain = [('ydental_store_id', '=', store.id)]
        orders = service._model('order').search(domain + ([('ydental_kind', '=', 'prescription'), ('state', 'in', ('issued', 'done'))]
            if role == 'pharmacy' else []), order='id desc', limit=100)
        if role == 'price':
            orders = service._model('order')
        if patient:
            orders = orders.filtered(lambda o: o.ydental_patient_id == patient)
        lines = service._model('line').search([('ydental_order_id', 'in', orders.ids)], order='id')
        segments = service._model('segment').search([('ydental_order_id', 'in', orders.ids)], order='id')
        events = service._model('event').search(domain + ([('ydental_pending_reason', '=', 'missing_price')] if role == 'price' else [('ydental_category', '=', role)]) +
            ([('ydental_patient_id', '=', patient.id)] if patient else []), order='id desc', limit=100)
        consumptions = service._model('consumption').search([('ydental_event_id', 'in', events.ids)])
        mappings = service.env['ydental.intake.service']._model('mapping').search([('ydental_store_id', '=', store.id), ('active', '=', True)])
        target_mappings = service.env['ydental.intake.service']._model('mapping').search([
            ('ydental_store_id', '!=', store.id), ('ydental_store_id.company_id', 'in', service.env.user.sudo().company_ids.ids), ('active', '=', True)]) if role == 'medical' else []
        batches = service.env['ydental.inventory.service']._model('batch').search(domain)
        lots = batches.ydental_lot_id
        products = service.env['product.product'].sudo().search([('ydental_inventory_kind', '=', 'medicine'),
            ('company_id', 'in', [False, store.company_id.id]), ('active', '=', True)]) if role == 'medical' else []
        for order in orders:
            service._audit('order_view', order)
        for event in events:
            service._audit('execution_view', event)
        return request.render('ydental_treatment.ydental_treatment_page', {
            'can_write': service.env['ydental.access.service']._levels(service.env['ydental.access.service']._membership(service.env.uid, store.id))[role] == 'write',
            'store': store, 'role': role, 'execution': execution, 'doc': doc, 'patient': patient,
            'labels': {entity: dict(service._model(entity)._fields['state']._description_selection(service.env)) for entity in ('order', 'line', 'segment', 'event')},
            'referral_receipts': service._model('receipt').search([('ydental_store_id', '=', store.id), ('ydental_actor_id', '=', service.env.uid), ('name', '=', 'refer')], order='id desc', limit=20) if role == 'medical' else service._model('receipt'),
            'consumptions': consumptions, 'currency_id': store.company_id.currency_id.id,
            'orders': orders, 'lines': lines, 'segments': segments, 'events': events,
            'mappings': mappings, 'target_mappings': target_mappings, 'lots': lots, 'products': products,
            'remaining': service._remaining, 'event_result': service._event_result,
            'revision': service.env['ydental.access.service']._scope().ydental_revision,
            'heartbeat': queue._settings()[0], 'status': queue._status(),
        }, headers=[('Cache-Control', 'no-store')])

    @http.route('/ydental/treatment/action', type='http', auth='user', methods=['POST'], max_content_length=100000)
    def action(self, operation, revision, connection, payload, key):
        try:
            service = self._service(int(revision), connection)
            result = service._operate(operation, json.loads(payload), key)
            return request.make_json_response(result, headers=[('Cache-Control', 'no-store')])
        except (AccessError, UserError, ValueError, TypeError, KeyError) as error:
            request.env['ydental.access.service']._denial('treatment.action')
            return request.make_json_response({'error': str(error)}, status=403 if isinstance(error, AccessError) else 409,
                headers=[('Cache-Control', 'no-store')])

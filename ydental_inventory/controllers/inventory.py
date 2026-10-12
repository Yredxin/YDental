import json
import secrets

from odoo import http
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request
from odoo.addons.ydental_intake.controllers.intake import YDentalIntakeDataSet


class YDentalInventory(http.Controller):
    def _service(self, revision=None):
        access = request.env['ydental.access.service']
        session = access._session_for_key(request.session.sid[:42])
        return access._bind(session, revision).env['ydental.inventory.service']

    @http.route('/ydental/inventory', type='http', auth='user', methods=['GET'])
    def dashboard(self, **kwargs):
        service = self._service()
        values = service._dashboard()
        access = service.env['ydental.access.service']
        values.update(revision=access._scope().ydental_revision, key=lambda: secrets.token_hex(16),
            can_write=access._levels(access._membership(service.env.uid, values['store'].id))['warehouse'] == 'write',
            can_catalog=access._is_group_manager(),
            units=service.env['uom.uom'].sudo().search([('active', '=', True)], limit=200),
            stores=service.env['ydental.access.store'].sudo().search([('company_id', '=', values['store'].company_id.id), ('active', '=', True)]))
        return request.render('ydental_inventory.ydental_inventory_page', values, headers=[('Cache-Control', 'no-store')])

    @http.route('/ydental/inventory/catalog', type='http', auth='user', methods=['GET'])
    def catalog(self, **kwargs):
        service = self._service()
        values = service._dashboard(catalog=True)
        access = service.env['ydental.access.service']
        values.update(revision=access._scope().ydental_revision, key=lambda: secrets.token_hex(16), can_write=False,
            can_catalog=True, units=service.env['uom.uom'].sudo().search([('active', '=', True)], limit=200), stores=[])
        return request.render('ydental_inventory.ydental_inventory_page', values, headers=[('Cache-Control', 'no-store')])

    @http.route('/ydental/inventory/action', type='http', auth='user', methods=['POST'], max_content_length=32768)
    def action(self, operation, revision, key, payload=None, output=None, **form):
        try:
            service = self._service(int(revision))
            args = json.loads(payload) if payload is not None else self._form(operation, form)
            result = service._operate(operation, args, key)
        except (AccessError, UserError, ValueError, TypeError, KeyError) as error:
            return request.make_json_response({'error': str(error)}, status=403 if isinstance(error, AccessError) else 409,
                headers=[('Cache-Control', 'no-store')])
        if output == 'json':
            return request.make_json_response(result, headers=[('Cache-Control', 'no-store')])
        return request.redirect('/ydental/inventory/catalog' if operation in ('product', 'product_edit') and not service.env['ydental.access.service']._levels(
            service.env['ydental.access.service']._membership(service.env.uid, service._access(catalog=True).id))['warehouse'] in ('read', 'write') else '/ydental/inventory')

    def _form(self, operation, form):
        schema = {
            'setup': ('code', '', ''), 'policy': ('near_days wait_days low_quantity reason', 'near_days wait_days', 'low_quantity'),
            'product': ('code name kind stock_uom_id issue_uom_id step specification suggested', 'stock_uom_id issue_uom_id', 'step suggested'),
            'product_edit': ('product_id name active', 'product_id', ''),
            'lot': ('product_id name expiration', 'product_id', ''), 'lot_edit': ('lot_id enabled reason', 'lot_id', ''),
            'receive': ('lot_id quantity uom_id source_key reason', 'lot_id uom_id', 'quantity'),
            'issue': ('lot_id quantity uom_id source_key reason', 'lot_id uom_id', 'quantity'),
            'inventory': ('lot_id counted uom_id source_key reason', 'lot_id uom_id', 'counted'),
            'transfer': ('lot_id quantity uom_id target_store_id source_key reason', 'lot_id uom_id target_store_id', 'quantity'),
            'return': ('event_id quantity uom_id source_key reason', 'event_id uom_id', 'quantity'),
            'verify': ('event_id quantity uom_id disposition source_key reason', 'event_id uom_id', 'quantity'),
            'recover': ('event_id reason', 'event_id', ''),
        }
        if operation not in schema:
            raise AccessError(request.env._('access_denied: Unknown inventory action.'))
        names, integers, numbers = schema[operation]
        result = {n: form[n] for n in names.split() if n in form and form[n] != ''}
        for name in integers.split():
            if name in result: result[name] = int(result[name])
        for name in numbers.split():
            if name in result: result[name] = float(result[name])
        for name in ('active', 'enabled'):
            if name in result: result[name] = result[name] == 'yes'
        return result

    @http.route('/ydental/inventory/scan', type='http', auth='user', methods=['POST'])
    def scan(self, code, revision):
        result = self._service(int(revision))._scan(code)
        return request.make_json_response(result, headers=[('Cache-Control', 'no-store')])


class YDentalInventoryDataSet(YDentalIntakeDataSet):
    @http.route()
    def call_kw(self, model, method, args, kwargs, path=None):
        if model.startswith('ydental.inventory.') or model in ('stock.lot', 'stock.quant', 'stock.move', 'stock.move.line', 'stock.location', 'stock.warehouse'):
            context = dict(kwargs.get('context') or {})
            context.pop('ydental_binding', None)
            access = request.env['ydental.access.service']
            session = access._existing_session_for_key(request.session.sid[:42]) if request.env.user.has_group('ydental_base.ydental_base_group_user') else False
            if session:
                bound = access._bind(session)
                context['ydental_binding'] = bound.env.context['ydental_binding']
            kwargs = dict(kwargs, context=context)
        return super().call_kw(model, method, args, kwargs, path=path)

import hashlib
import inspect
import json
import math
from datetime import timedelta, timezone
from zoneinfo import ZoneInfo

from odoo import fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.float_utils import float_round

from .ydental_inventory_record import MUTATION


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


class YDentalInventoryService(models.AbstractModel):
    _name = 'ydental.inventory.service'
    _description = 'Atomic native inventory and trusted execution source service'

    def _now(self):
        return fields.Datetime.now()

    def _access(self, write=False, catalog=False):
        access = self.env['ydental.access.service']
        session = access._scope(write=write)
        store = session.ydental_store_id
        if catalog:
            if not access._is_group_manager() or not store or not store.active or store.company_id.id not in self.env.user.company_ids.ids:
                raise AccessError(self.env._('access_denied: Group inventory master data authority is required.'))
        else:
            access._check('warehouse', 'write' if write else 'read', write=write)
        return store

    def _native(self, model):
        # All model names are server literals; inputs are validated before this
        # narrow native mutation scope. Caller uid stays available for audit.
        return self.env[model].sudo().with_context(ydental_inventory_mutation=MUTATION, tracking_disable=True,
            mail_create_nosubscribe=True, mail_notrack=True)

    def _model(self, entity):
        return self.env['ydental.inventory.' + entity].sudo()

    def _lock(self):
        # Single inventory fence closes absent-quant/source races. The UPDATE
        # also forces repeatable-read contenders to retry from a fresh snapshot.
        self.env.cr.execute('SELECT pg_advisory_xact_lock(%s)', [31007])
        self.env.cr.execute('UPDATE ydental_inventory_mutex SET ydental_revision=ydental_revision+1 WHERE id=%s',
            [self.env.ref('ydental_inventory.ydental_inventory_mutex').id])
        self.env.invalidate_all()

    def _id(self, value):
        if type(value) is not int or value <= 0:
            raise ValidationError(self.env._('Select a valid inventory record.'))
        return value

    def _text(self, value):
        if not isinstance(value, str) or not value.strip() or len(value) > 240:
            raise ValidationError(self.env._('A short source, reason or evidence reference is required.'))
        return value.strip()

    def _number(self, value, zero=False):
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0 or not zero and value == 0:
            raise ValidationError(self.env._('Use a finite positive quantity.'))
        return float(value)

    def _get(self, entity, record_id, store):
        record = self._model(entity).browse(self._id(record_id)).exists()
        if not record or record.ydental_store_id != store:
            raise AccessError(self.env._('access_denied: Select an inventory source in the current store.'))
        return record

    def _config(self, store):
        config = self._model('config').search([('ydental_store_id', '=', store.id)], limit=1)
        if not config or config.ydental_warehouse_id.company_id != store.company_id:
            raise UserError(self.env._('configuration_required: Configure the store inventory warehouse first.'))
        return config

    def _lot(self, lot_id, store):
        lot = self._native('stock.lot').browse(self._id(lot_id)).exists()
        if not lot or not self._batch(lot, store) or lot.company_id != store.company_id or not lot.product_id.ydental_inventory_kind:
            raise AccessError(self.env._('access_denied: Select a lot in the current store.'))
        return lot

    def _batch(self, lot, store):
        return self._model('batch').search([('ydental_store_id', '=', store.id), ('ydental_lot_id', '=', lot.id)], limit=1)

    def _product(self, product_id):
        product = self._native('product.product').with_context(active_test=False).browse(self._id(product_id)).exists()
        if not product or not product.ydental_inventory_kind:
            raise ValidationError(self.env._('Select an inventory product.'))
        return product

    def _location(self, config, product):
        return config['ydental_' + product.ydental_inventory_kind + '_id']

    def _unit(self, product, quantity, uom_id, zero=False):
        quantity = self._number(quantity, zero)
        unit = self._native('uom.uom').browse(self._id(uom_id)).exists()
        if not unit or not unit.active or unit not in (product.uom_id | product.ydental_issue_uom_id):
            raise ValidationError(self.env._('Select the configured stock or issue unit.'))
        raw = unit._compute_quantity(quantity, product.uom_id, round=False)
        digits = self.env['decimal.precision'].sudo().precision_get('Product Unit')
        rounded = float_round(raw, precision_digits=digits)
        step = product.ydental_stock_step
        if not step or abs(raw - rounded) > 1e-9 or abs(raw / step - round(raw / step)) > 1e-7:
            raise ValidationError(self.env._('precision_error: Quantity is not representable at the configured stock precision.'))
        return rounded, unit, {'input_uom': unit.id, 'stock_uom': product.uom_id.id, 'input_factor': unit.factor,
            'stock_factor': product.uom_id.factor, 'digits': digits, 'stock_step': step}

    def _usable(self, lot, store):
        if not self._batch(lot, store).ydental_enabled or not lot.product_id.active:
            raise UserError(self.env._('lot_disabled: New execution requires an active product and lot.'))
        if not lot.expiration_date or lot.expiration_date <= self._now():
            raise UserError(self.env._('lot_expired: New execution requires a nonexpired lot.'))

    def _quantity(self, lot, location):
        quants = self._native('stock.quant').search([('lot_id', '=', lot.id), ('product_id', '=', lot.product_id.id),
            ('location_id', '=', location.id), ('owner_id', '=', False), ('package_id', '=', False)])
        return sum(q.quantity - q.reserved_quantity for q in quants)

    def _audit(self, operation, record, before=None, after=None):
        return self.env['ydental.access.service']._audit('inventory.' + operation, 'warehouse', record,
            record.ydental_store_id.id, before=before, after=after, source='inventory_service')

    def _operate(self, operation, payload, key):
        handlers = {'setup': self._setup, 'policy': self._policy, 'product': self._create_product,
            'product_edit': self._edit_product, 'lot': self._create_lot, 'lot_edit': self._edit_lot,
            'receive': self._receive, 'issue': self._issue, 'inventory': self._inventory,
            'transfer': self._transfer, 'return': self._return, 'verify': self._verify, 'recover': self._recover}
        if operation not in handlers or not isinstance(payload, dict):
            raise AccessError(self.env._('access_denied: Unknown inventory action.'))
        key = self._text(key)
        catalog = operation in ('product', 'product_edit')
        store = self._access(write=True, catalog=catalog)
        digest = fingerprint([operation, store.id, payload])
        with self.env.cr.savepoint():
            self._lock()
            store = self._access(write=True, catalog=catalog)
            receipt = self._model('operation').search([('ydental_store_id', '=', store.id), ('ydental_key', '=', key)], limit=1)
            if receipt:
                if receipt.ydental_fingerprint != digest:
                    raise UserError(self.env._('version_conflict: The request key has different inventory arguments.'))
                return dict(receipt.ydental_result, result='already_accepted')
            try:
                inspect.signature(handlers[operation]).bind(store, **payload)
            except TypeError as error:
                raise ValidationError(self.env._('Unknown or missing inventory arguments.')) from error
            result = dict(handlers[operation](store, **payload), result='accepted')
            receipt = self._model('operation')._new({'name': operation, 'ydental_store_id': store.id,
                'ydental_key': key, 'ydental_fingerprint': digest, 'ydental_result': result, 'ydental_actor_id': self.env.uid})
            self._audit(operation, receipt, after=result)
            return result

    def _setup(self, store, code):
        existing = self._model('config').search([('ydental_store_id', '=', store.id)], limit=1)
        if existing:
            return {'id': existing.id}
        code = self._text(code)
        if len(code) > 5:
            raise ValidationError(self.env._('Warehouse code must have at most five characters.'))
        # Native warehouse creation can change global groups and execute all
        # settings set_values(), including pricelist archival. Serialize the
        # count check with native warehouse writes, then require the Settings
        # administrator to have configured both global stock groups in advance.
        self.env.cr.execute('LOCK TABLE stock_warehouse IN SHARE ROW EXCLUSIVE MODE')
        group_user = self.env.ref('base.group_user')
        self.env.cr.execute('SELECT id FROM res_groups WHERE id = %s FOR UPDATE', [group_user.id])
        multi_warehouse = self.env.ref('stock.group_stock_multi_warehouses')
        multi_location = self.env.ref('stock.group_stock_multi_locations')
        implied_before = set(group_user.implied_ids.ids)
        counts = self._native('stock.warehouse')._read_group(
            [('active', '=', True)], ['company_id'], aggregates=['__count'])
        current = {company.id: count for company, count in counts}
        next_max = max([current.get(store.company_id.id, 0) + 1, *current.values()])
        if next_max > 1 and not {multi_warehouse.id, multi_location.id} <= implied_before:
            raise UserError(self.env._(
                'configuration_required: A Settings administrator must explicitly enable '
                'Multiple Warehouses and Storage Locations for internal users before adding this warehouse.'))
        if next_max <= 1 and multi_warehouse.id in implied_before:
            raise UserError(self.env._(
                'configuration_required: The global Multiple Warehouses setting conflicts with the current warehouse count.'))
        warehouse = self._native('stock.warehouse').with_company(store.company_id).create({
            'name': store.name, 'code': code, 'company_id': store.company_id.id, 'ydental_store_id': store.id})
        if set(group_user.implied_ids.ids) != implied_before:
            raise UserError(self.env._('configuration_required: Native warehouse creation changed global user groups.'))
        warehouse.lot_stock_id.write({'ydental_store_id': store.id})
        warehouse.view_location_id.write({'ydental_store_id': store.id})
        values = {'name': store.name, 'ydental_store_id': store.id, 'ydental_warehouse_id': warehouse.id}
        for kind, name, usage in [('medicine', self.env._('Pharmacy'), 'internal'), ('material', self.env._('Materials'), 'internal'),
                ('prosthesis', self.env._('Prosthesis awaiting collection'), 'internal'), ('quarantine', self.env._('Return verification'), 'internal'),
                ('supplier', self.env._('Supplier'), 'supplier'), ('customer', self.env._('Actual issue'), 'customer'), ('loss', self.env._('Inventory loss'), 'inventory')]:
            location = self._native('stock.location').with_company(store.company_id).create({'name': name,
                'location_id': warehouse.view_location_id.id, 'usage': usage, 'company_id': store.company_id.id,
                'ydental_store_id': store.id})
            values['ydental_' + kind + '_id'] = location.id
        config = self._model('config')._new(values)
        return {'id': config.id, 'warehouse_id': warehouse.id,
            'multi_warehouse_group_enabled': False,
            'multi_location_group_enabled': False}

    def _policy(self, store, near_days, wait_days, low_quantity, reason):
        if type(near_days) is not int or type(wait_days) is not int or not 0 <= near_days <= 3650 or not 0 <= wait_days <= 3650:
            raise ValidationError(self.env._('Use explicit nonnegative alert day thresholds.'))
        config = self._config(store)
        config._save({'ydental_policy_configured': True, 'ydental_near_days': near_days, 'ydental_wait_days': wait_days,
            'ydental_low_quantity': self._number(low_quantity, True), 'ydental_policy_reason': self._text(reason)})
        return {'id': config.id, 'version': config.ydental_version}

    def _create_product(self, store, code, name, kind, stock_uom_id, issue_uom_id, step, specification, suggested=0):
        if kind not in ('medicine', 'material', 'prosthesis'):
            raise ValidationError(self.env._('Select medicine, material or prosthesis.'))
        stock = self._native('uom.uom').browse(self._id(stock_uom_id)).exists()
        issue = self._native('uom.uom').browse(self._id(issue_uom_id)).exists()
        step = self._number(step)
        digits = self.env['decimal.precision'].sudo().precision_get('Product Unit')
        if not stock or not issue or not stock.active or not issue.active or stock.parent_path.split('/')[0] != issue.parent_path.split('/')[0] or abs(step - float_round(step, precision_digits=digits)) > 1e-9:
            raise ValidationError(self.env._('Use active units and a representable stock step.'))
        code = self._text(code)
        if self._native('product.product').with_context(active_test=False).search_count([('default_code', '=', code)]):
            raise UserError(self.env._('version_conflict: Product code already exists.'))
        p = self._native('product.template').create({'name': self._text(name), 'default_code': code, 'type': 'consu',
            'is_storable': True, 'tracking': 'lot', 'use_expiration_date': True, 'uom_id': stock.id,
            'ydental_issue_uom_id': issue.id, 'ydental_inventory_kind': kind, 'ydental_specification': self._text(specification),
            'ydental_stock_step': step, 'ydental_suggested_quantity': self._number(suggested, True)})
        return {'id': p.product_variant_id.id}

    def _edit_product(self, store, product_id, active, name, specification=None, suggested=None):
        if type(active) is not bool:
            raise ValidationError(self.env._('Use an explicit active choice.'))
        product = self._product(product_id)
        values = {'name': self._text(name), 'active': active}
        if specification is not None: values['ydental_specification'] = self._text(specification)
        if suggested is not None: values['ydental_suggested_quantity'] = self._number(suggested, True)
        product.product_tmpl_id.write(values)
        return {'id': product.id}

    def _create_lot(self, store, product_id, name, expiration):
        product = self._product(product_id)
        self._config(store)
        try:
            expiration = fields.Datetime.to_datetime(expiration)
        except (ValueError, TypeError) as error:
            raise ValidationError(self.env._('Use a valid UTC expiry time.')) from error
        if not expiration or expiration.tzinfo:
            raise ValidationError(self.env._('Use a valid UTC expiry time.'))
        lot = self._native('stock.lot').with_company(store.company_id).create({'name': self._text(name),
            'product_id': product.id, 'company_id': store.company_id.id, 'ydental_store_id': store.id,
            'expiration_date': expiration})
        self._model('batch')._new({'name': lot.name, 'ydental_store_id': store.id, 'ydental_lot_id': lot.id})
        return {'id': lot.id}

    def _edit_lot(self, store, lot_id, enabled, reason):
        if type(enabled) is not bool:
            raise ValidationError(self.env._('Use an explicit enabled choice.'))
        self._text(reason)
        lot = self._lot(lot_id, store)
        self._batch(lot, store)._save({'ydental_enabled': enabled})
        return {'id': lot.id, 'enabled': enabled}

    def _event(self, store, namespace, source_key, kind, lot, quantity, uom_id, source, target, reason,
               parent=None, target_store=None, summary='', snapshot=None, actual_at=None, synthetic=False,
               responsible=None, fee_reference='', actual=False):
        source_key = self._text(source_key)
        namespace = self._text(namespace)
        quantity_stock, unit, unit_snapshot = self._unit(lot.product_id, quantity, uom_id)
        reason = self._text(reason)
        digest = fingerprint([kind, lot.id, quantity, unit.id, source.id, target.id, reason,
            parent.id if parent else False, summary, snapshot, fee_reference, synthetic])
        prior = self._model('event').search([('ydental_store_id', '=', store.id), ('ydental_source_namespace', '=', namespace),
            ('ydental_source_key', '=', self._text(source_key))], limit=1)
        if prior:
            if prior.ydental_fingerprint != digest:
                raise UserError(self.env._('version_conflict: The source event is immutable.'))
            return prior
        unusable = False
        if kind in ('replenishment', 'treatment', 'chairside', 'prescription', 'transfer'):
            try:
                self._usable(lot, store)
            except UserError:
                if not actual: raise
                unusable = True
        event = self._model('event')._new({'name': kind, 'ydental_store_id': store.id,
            'ydental_source_namespace': namespace, 'ydental_source_key': source_key, 'ydental_kind': kind,
            'ydental_fingerprint': digest, 'ydental_product_id': lot.product_id.id, 'ydental_lot_id': lot.id,
            'ydental_quantity': quantity_stock, 'ydental_input_quantity': quantity, 'ydental_uom_id': unit.id,
            'ydental_unit_snapshot': unit_snapshot, 'ydental_from_id': source.id, 'ydental_to_id': target.id,
            'ydental_parent_id': parent.id if parent else False, 'ydental_target_store_id': target_store.id if target_store else False,
            'ydental_responsible_id': responsible.id if responsible else self.env.uid, 'ydental_actor_id': self.env.uid,
            'ydental_reason': reason, 'ydental_summary': summary, 'ydental_price_snapshot': snapshot,
            'ydental_actual_at': actual_at or self._now(), 'ydental_synthetic': synthetic, 'ydental_fee_reference': fee_reference,
            'state': 'pending' if actual else 'done'})
        # An already-performed trusted source can persist as pending, with no
        # half move. All other shortages fail the enclosing savepoint.
        if unusable or source.usage == 'internal' and lot.product_id.uom_id.compare(self._quantity(lot, source), quantity_stock) < 0:
            if not actual:
                raise UserError(self.env._('insufficient_balance: There is insufficient available stock.'))
            self._audit('pending', event, after={'event_id': event.id, 'responsible_id': event.ydental_responsible_id.id})
            return event
        self._move(event)
        return event

    def _move(self, event):
        if event.ydental_move_id:
            return
        lot = event.ydental_lot_id
        source, target = event.ydental_from_id, event.ydental_to_id
        if source.usage == 'internal' and lot.product_id.uom_id.compare(self._quantity(lot, source), event.ydental_quantity) < 0:
            raise UserError(self.env._('insufficient_balance: There is insufficient available stock.'))
        move = self._native('stock.move').with_company(event.ydental_store_id.company_id).create({
            'product_id': lot.product_id.id, 'product_uom_qty': event.ydental_quantity, 'uom_id': lot.product_id.uom_id.id,
            'location_id': source.id, 'location_dest_id': target.id, 'company_id': event.ydental_store_id.company_id.id,
            'ydental_store_id': event.ydental_store_id.id, 'origin': 'YDental inventory event %s' % event.id,
            'is_inventory': event.ydental_kind == 'inventory'})
        move._action_confirm(merge=False, create_proc=False)
        move._do_unreserve()
        self._native('stock.move.line').with_company(event.ydental_store_id.company_id).create({'move_id': move.id,
            'product_id': lot.product_id.id, 'uom_id': lot.product_id.uom_id.id, 'quantity': event.ydental_quantity,
            'lot_id': lot.id, 'location_id': source.id, 'location_dest_id': target.id,
            'company_id': event.ydental_store_id.company_id.id, 'ydental_store_id': event.ydental_store_id.id, 'picked': True})
        move.write({'picked': True})
        move._action_done()
        if move.state != 'done':
            raise UserError(self.env._('inventory_error: Native movement did not finish.'))
        if event.ydental_target_store_id:
            self._target_lot(lot, event.ydental_target_store_id)
        event._save({'ydental_move_id': move.id, 'state': 'done'})
        if event.ydental_kind == 'receipt':
            batch = self._batch(lot, event.ydental_store_id)
            if not batch.ydental_received_at:
                batch._save({'ydental_received_at': self._now()})
        self._audit('movement', event, after={'event_id': event.id, 'move_id': move.id, 'quantity': event.ydental_quantity})

    def _target_lot(self, lot, store):
        # Same-company transfers preserve the native manufacturer lot identity.
        # Per-store lifecycle metadata contains no independently writable balance.
        batch = self._batch(lot, store)
        if not batch:
            batch = self._model('batch')._new({'name': lot.name, 'ydental_lot_id': lot.id,
                'ydental_store_id': store.id, 'ydental_received_at': self._now()})
        elif not batch.ydental_received_at:
            batch._save({'ydental_received_at': self._now()})
        return lot

    def _receive(self, store, lot_id, quantity, uom_id, source_key, reason):
        lot = self._lot(lot_id, store); config = self._config(store)
        event = self._event(store, 'warehouse', source_key, 'receipt', lot, quantity, uom_id,
            config.ydental_supplier_id, self._location(config, lot.product_id), reason)
        return {'id': event.id, 'move_id': event.ydental_move_id.id, 'state': event.state}

    def _issue(self, store, lot_id, quantity, uom_id, source_key, reason):
        lot = self._lot(lot_id, store); config = self._config(store)
        event = self._event(store, 'warehouse', source_key, 'replenishment', lot, quantity, uom_id,
            self._location(config, lot.product_id), config.ydental_customer_id, reason)
        return {'id': event.id, 'move_id': event.ydental_move_id.id, 'state': event.state}

    def _inventory(self, store, lot_id, counted, uom_id, source_key, reason):
        lot = self._lot(lot_id, store); config = self._config(store); location = self._location(config, lot.product_id)
        count, unit, precision = self._unit(lot.product_id, counted, uom_id, zero=True)
        original = self._model('event').search([('ydental_store_id', '=', store.id), ('ydental_source_namespace', '=', 'warehouse'), ('ydental_source_key', '=', source_key)], limit=1)
        count_digest = fingerprint([lot_id, counted, uom_id, reason])
        if original:
            if original.ydental_kind != 'inventory' or original.ydental_count_fingerprint != count_digest:
                raise UserError(self.env._('version_conflict: The inventory count source is immutable.'))
            return {'id': original.id, 'move_id': original.ydental_move_id.id, 'counted': count}
        quants = self._native('stock.quant').search([('lot_id', '=', lot.id), ('location_id', '=', location.id)])
        if any(q.reserved_quantity or q.owner_id or q.package_id for q in quants):
            raise UserError(self.env._('inventory_conflict: Resolve reservations and owned stock before counting.'))
        delta = count - sum(quants.mapped('quantity'))
        if lot.product_id.uom_id.is_zero(delta):
            event = self._model('event')._new({'name': 'inventory', 'ydental_store_id': store.id,
                'ydental_source_namespace': 'warehouse', 'ydental_source_key': self._text(source_key), 'ydental_kind': 'inventory',
                'ydental_fingerprint': count_digest, 'ydental_count_fingerprint': count_digest,
                'ydental_product_id': lot.product_id.id, 'ydental_lot_id': lot.id, 'ydental_quantity': 0,
                'ydental_input_quantity': counted, 'ydental_uom_id': unit.id, 'ydental_unit_snapshot': precision,
                'ydental_from_id': location.id, 'ydental_to_id': location.id, 'ydental_reason': self._text(reason),
                'ydental_responsible_id': self.env.uid, 'ydental_actor_id': self.env.uid,
                'ydental_actual_at': self._now(), 'state': 'observed'})
            return {'id': event.id, 'state': 'observed', 'counted': count}
        event = self._event(store, 'warehouse', source_key, 'inventory', lot, abs(delta), lot.product_id.uom_id.id,
            config.ydental_loss_id if delta > 0 else location, location if delta > 0 else config.ydental_loss_id, reason)
        event._save({'ydental_count_fingerprint': count_digest})
        return {'id': event.id, 'move_id': event.ydental_move_id.id, 'counted': count}

    def _transfer(self, store, lot_id, quantity, uom_id, target_store_id, source_key, reason):
        target_store = self.env['ydental.access.store'].sudo().browse(self._id(target_store_id)).exists()
        if not target_store or target_store == store or target_store.company_id != store.company_id:
            raise AccessError(self.env._('access_denied: Transfer requires another store in the same company.'))
        # Both stores require real live warehouse-write grants, even same company.
        self.env['ydental.access.service']._check('warehouse', 'write', store_id=target_store.id, write=True)
        target_config = self._config(target_store)
        lot = self._lot(lot_id, store); config = self._config(store)
        event = self._event(store, 'warehouse', source_key, 'transfer', lot, quantity, uom_id,
            self._location(config, lot.product_id), self._location(target_config, lot.product_id), reason, target_store=target_store)
        return {'id': event.id, 'move_id': event.ydental_move_id.id, 'target_store_id': target_store.id}

    def _return(self, store, event_id, quantity, uom_id, source_key, reason):
        parent = self._get('event', event_id, store)
        if parent.state != 'done' or parent.ydental_kind not in ('replenishment', 'prescription'):
            raise UserError(self.env._('return_invalid: Select an actual completed issue.'))
        lot = parent.ydental_lot_id; config = self._config(store)
        qty, unit, snap = self._unit(lot.product_id, quantity, uom_id)
        prior = self._model('event').search([('ydental_parent_id', '=', parent.id), ('ydental_kind', '=', 'return'), ('ydental_source_key', '!=', source_key)])
        if lot.product_id.uom_id.compare(sum(prior.mapped('ydental_quantity')) + qty, parent.ydental_quantity) > 0:
            raise UserError(self.env._('return_limit: Physical returns cannot exceed the actual issue.'))
        event = self._event(store, 'warehouse', source_key, 'return', lot, quantity, uom_id,
            config.ydental_customer_id, config.ydental_quarantine_id, reason, parent=parent)
        return {'id': event.id, 'move_id': event.ydental_move_id.id, 'state': 'quarantine'}

    def _verify(self, store, event_id, quantity, uom_id, disposition, source_key, reason):
        parent = self._get('event', event_id, store)
        if parent.ydental_kind != 'return' or parent.state != 'done' or disposition not in ('release', 'discard'):
            raise ValidationError(self.env._('Select a physical return and its verified destination.'))
        lot = parent.ydental_lot_id; config = self._config(store)
        if disposition == 'release':
            self._usable(lot, store)
        qty, unit, snap = self._unit(lot.product_id, quantity, uom_id)
        done = self._model('event').search([('ydental_parent_id', '=', parent.id), ('ydental_kind', '=', 'verification'), ('ydental_source_key', '!=', source_key)])
        if lot.product_id.uom_id.compare(sum(done.mapped('ydental_quantity')) + qty, parent.ydental_quantity) > 0:
            raise UserError(self.env._('return_limit: Verification exceeds the remaining physical return.'))
        event = self._event(store, 'warehouse', source_key, 'verification', lot, quantity, uom_id,
            config.ydental_quarantine_id, self._location(config, lot.product_id) if disposition == 'release' else config.ydental_loss_id,
            reason, parent=parent)
        return {'id': event.id, 'move_id': event.ydental_move_id.id, 'disposition': disposition}

    def _authorize_source(self, source):
        # S08 must override with an immutable real source object and verify its
        # actual actor/store/order/batch/price. HTTP/context dictionaries fail.
        raise AccessError(self.env._('access_denied: Clinical inventory source integration is not connected.'))

    def _check_source_product(self, kind, lot):
        expected = {'treatment': 'material', 'chairside': 'medicine', 'prescription': 'medicine'}
        if lot.product_id.ydental_inventory_kind != expected.get(kind):
            raise ValidationError(self.env._('source_category_mismatch: The execution source does not match the inventory product category.'))

    def _source_action(self, source):
        payload = self._authorize_source(source)
        with self.env.cr.savepoint():
            self._lock()
            payload = self._authorize_source(source)
            access = self.env['ydental.access.service']
            store = access._scope(write=True).ydental_store_id
            kind = payload['kind']
            if kind not in ('treatment', 'chairside', 'prescription'):
                raise ValidationError(self.env._('Select a supported execution source kind.'))
            access._check('pharmacy' if kind == 'prescription' else 'medical', 'write', write=True)
            lot = self._lot(payload['lot_id'], store); config = self._config(store)
            self._check_source_product(kind, lot)
            snapshot = payload['price_snapshot']
            if not isinstance(snapshot, dict) or not snapshot.get('version') or not snapshot.get('currency') or 'unit_price' not in snapshot:
                raise ValidationError(self.env._('A frozen original source price snapshot is required.'))
            event = self._event(store, payload['namespace'], payload['source_key'], kind, lot,
                payload['quantity'], payload['uom_id'], self._location(config, lot.product_id), config.ydental_customer_id,
                payload['reason'], summary=payload['summary'], snapshot=snapshot, synthetic=payload['synthetic'],
                responsible=self.env.user, fee_reference=payload['fee_reference'], actual=payload['already_performed'])
            return {'id': event.id, 'state': event.state, 'move_id': event.ydental_move_id.id}

    def _recover(self, store, event_id, reason):
        event = self._get('event', event_id, store); self._text(reason)
        if event.state == 'done':
            return {'id': event.id, 'move_id': event.ydental_move_id.id, 'state': 'done'}
        if event.state != 'pending' or event.ydental_kind not in ('treatment', 'chairside', 'prescription'):
            raise UserError(self.env._('Recovery requires an original pending execution event.'))
        # Pending is created only for an already-performed, trusted private
        # source. Ordinary actions cannot create or alter this historical fact.
        snapshot = event.ydental_price_snapshot
        if (event.ydental_source_namespace == 'warehouse' or not event.ydental_summary
                or not isinstance(snapshot, dict) or not snapshot.get('version')
                or not snapshot.get('currency') or 'unit_price' not in snapshot
                or event.ydental_actual_at > self._now()):
            raise UserError(self.env._('recovery_unconfirmed: Keep the original event pending for manual source and quantity verification.'))
        self._check_source_product(event.ydental_kind, event.ydental_lot_id)
        if event.ydental_lot_id.product_id.uom_id.compare(
                self._quantity(event.ydental_lot_id, event.ydental_from_id), event.ydental_quantity) < 0:
            raise UserError(self.env._('insufficient_balance: There is insufficient available stock.'))
        # Require a real, completed incoming correction after the pending fact,
        # for this store, lot and physical source location. A free-text reason
        # alone never creates stock or authorizes historical bookkeeping.
        corrections = self._model('event').search([
            ('ydental_store_id', '=', store.id), ('ydental_lot_id', '=', event.ydental_lot_id.id),
            ('ydental_kind', 'in', ('receipt', 'inventory')), ('state', '=', 'done'),
            ('ydental_to_id', '=', event.ydental_from_id.id), ('id', '>', event.id),
            ('create_date', '>=', event.create_date),
        ], order='id desc')
        correction = corrections.filtered(lambda c: c.ydental_quantity > 0
            and c.ydental_move_id.state == 'done' and c.ydental_from_id.usage != 'internal')[:1]
        if not correction:
            raise UserError(self.env._('recovery_evidence_required: Keep pending until an evidenced receipt or physical count corrects this lot.'))
        # Only this original pending reconciliation bypasses current usability.
        # New issue, clinical execution and return release still use _usable.
        self._move(event)
        event._save({'ydental_correction_id': correction.id, 'ydental_reconciled_at': self._now()})
        self._audit('recovery', event, before={'state': 'pending'}, after={
            'state': event.state, 'move_id': event.ydental_move_id.id, 'correction_id': correction.id,
            'actual_at': fields.Datetime.to_string(event.ydental_actual_at),
            'reconciled_at': fields.Datetime.to_string(event.ydental_reconciled_at)})
        return {'id': event.id, 'move_id': event.ydental_move_id.id, 'state': event.state}

    def _scan(self, code):
        self._access()
        self._text(code)
        return {'result': 'unsupported_source', 'received': False}

    def _dashboard(self, catalog=False, term='', page=1, event_id=None):
        store = self._access(catalog=catalog)
        if not isinstance(term, str) or len(term) > 100 or type(page) is not int or not 1 <= page <= 10000:
            raise ValidationError(self.env._('Enter a product or lot name and a valid page.'))
        config = self._model('config').search([('ydental_store_id', '=', store.id)], limit=1) if not catalog else self._model('config')
        products = self._native('product.product').with_context(active_test=False).search([('ydental_inventory_kind', '!=', False)])
        batches = self._model('batch').search([('ydental_store_id', '=', store.id)])
        rows = []
        if config:
            today = self._now().replace(tzinfo=timezone.utc).astimezone(ZoneInfo(store.ydental_timezone)).date()
            quantities = {}
            available_by_product = {}
            for batch in batches:
                lot = batch.ydental_lot_id
                raw = self._quantity(lot, self._location(config, lot.product_id))
                usable = bool(batch.ydental_enabled and lot.product_id.active and lot.expiration_date and lot.expiration_date > self._now())
                quantities[lot.id] = (raw, raw if usable else 0)
                available_by_product[lot.product_id.id] = available_by_product.get(lot.product_id.id, 0) + (raw if usable else 0)
            for batch in batches:
                lot = batch.ydental_lot_id
                product = lot.product_id; location = self._location(config, product)
                flags = []
                on_hand, qty = quantities[lot.id]
                if lot.expiration_date and lot.expiration_date <= self._now():
                    flags.append('expired')
                if not batch.ydental_enabled or not product.active:
                    flags.append('disabled')
                if config.ydental_policy_configured:
                    if available_by_product[product.id] <= config.ydental_low_quantity: flags.append('low')
                    if lot.expiration_date and self._now() < lot.expiration_date <= self._now() + timedelta(days=config.ydental_near_days): flags.append('near')
                    if product.ydental_inventory_kind == 'prosthesis' and qty > 0 and batch.ydental_received_at:
                        received_day = batch.ydental_received_at.replace(tzinfo=timezone.utc).astimezone(ZoneInfo(store.ydental_timezone)).date()
                        if (today - received_day).days >= config.ydental_wait_days: flags.append('collection')
                rows.append({'id': lot.id, 'product_id': product.id, 'name': lot.name, 'product': product.name,
                    'kind': product.ydental_inventory_kind, 'unit': product.uom_id.name, 'uom_id': product.uom_id.id,
                    'quantity': qty, 'on_hand': on_hand, 'quarantine': self._quantity(lot, config.ydental_quarantine_id),
                    'expiration': lot.expiration_date, 'received_at': batch.ydental_received_at,
                    'enabled': batch.ydental_enabled, 'flags': flags})
        event_domain = fields.Domain('ydental_store_id', '=', store.id) | (
            fields.Domain('ydental_target_store_id', '=', store.id) & fields.Domain('ydental_kind', '=', 'transfer'))
        if term.strip():
            event_domain &= fields.Domain.OR([
                fields.Domain('ydental_product_id.name', 'ilike', term.strip()),
                fields.Domain('ydental_product_id.default_code', 'ilike', term.strip()),
                fields.Domain('ydental_lot_id.name', 'ilike', term.strip()),
            ])
        if event_id is not None:
            event_domain &= fields.Domain('id', '=', event_id)
        events = self._model('event').search(event_domain, order='id desc',
            offset=(page - 1) * 30, limit=31) if not catalog else self._model('event')
        has_more = len(events) > 30
        events = events[:30]
        # Project only necessary execution summary, never patient IDs/attachments.
        projected = [{'id': e.id, 'kind': e.ydental_kind, 'state': e.state, 'quantity': e.ydental_quantity,
            'product': e.ydental_product_id.name, 'lot': e.ydental_lot_id.name, 'uom_id': e.ydental_uom_id.id,
            'lot_id': e.ydental_lot_id.id, 'move_id': e.ydental_move_id.id, 'version': e.ydental_version,
            'summary': e.ydental_summary, 'responsible': e.ydental_responsible_id.name,
            'synthetic': e.ydental_synthetic} for e in events]
        self.env['ydental.access.service']._audit('inventory.view', 'warehouse', config or self._model('config'),
            store.id, source='inventory_workbench')
        return {'store': store, 'config': config, 'lots': rows, 'events': projected,
            'visible_lots': [row for row in rows if not term.strip() or term.strip().casefold() in (row['product'] + ' ' + row['name']).casefold()],
            'search_term': term, 'search_page': page, 'has_more_events': has_more,
            'products': [{'id': p.id, 'name': p.name, 'kind': p.ydental_inventory_kind, 'code': p.default_code,
                'specification': p.ydental_specification, 'uom_id': p.uom_id.id, 'issue_uom_id': p.ydental_issue_uom_id.id,
                'suggested': p.ydental_suggested_quantity, 'active': p.active} for p in products]}

    def _purchase_receipt_type(self):
        """Resolve this bound store's incoming type for a native purchase handoff."""
        store = self._access()
        config = self._config(store)
        warehouse = config.ydental_warehouse_id
        picking_type = warehouse.in_type_id
        if (warehouse.ydental_store_id != store or warehouse.company_id != store.company_id or not picking_type
                or not picking_type.active or picking_type.code != 'incoming'
                or picking_type.company_id != store.company_id or picking_type.warehouse_id != warehouse):
            raise UserError(self.env._('configuration_required: The current store has no valid incoming operation type.'))
        return {'store_id': store.id, 'company_id': store.company_id.id, 'picking_type_id': picking_type.id}

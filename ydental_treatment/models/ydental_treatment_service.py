import hashlib
import inspect
import json
import math
from dataclasses import dataclass

from odoo import fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


@dataclass(frozen=True)
class InventorySource:
    actor_id: int
    store_id: int
    consumption_id: int


@dataclass(frozen=True)
class ReferralSource:
    actor_id: int
    store_id: int
    execution_id: int
    lease_id: int
    lease_token: str
    document_id: int
    document_version: int
    fingerprint: str


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


class YDentalTreatmentService(models.AbstractModel):
    _name = 'ydental.treatment.service'
    _description = 'Actual treatment, frozen orders and pharmacy transactions'

    def _model(self, entity):
        # All entities are fixed literals selected by this service. No public
        # endpoint accepts a model, domain, arbitrary values or mutation token.
        return self.env['ydental.treatment.' + entity].sudo()

    def _access(self, category, write=True):
        store = self.env['ydental.access.service']._check(category, 'write' if write else 'read', write=write).ydental_store_id
        if store.company_id not in self.env.user.sudo().company_ids:
            raise AccessError(self.env._('access_denied: The source company is outside the account scope.'))
        return store

    def _audit(self, operation, record, after=None, reason=False):
        self.env['ydental.access.service']._audit('treatment.' + operation, record.ydental_category,
            record, record.ydental_store_id.id, after=after, reason=reason, source='actual_clinical_execution')

    def _new(self, entity, source, values):
        return self._model(entity)._new(dict(values, ydental_store_id=source.ydental_store_id.id,
            ydental_category=source.ydental_category, ydental_patient_id=source.ydental_patient_id.id,
            ydental_actor_id=self.env.uid))

    def _get(self, entity, record_id, category):
        record = self._model(entity).browse(self.env['ydental.intake.service']._id(record_id)).exists()
        if not record or record.ydental_store_id != self._access(category):
            raise AccessError(self.env._('access_denied: Select a source in the current store.'))
        return record

    def _operate(self, operation, payload, key):
        handlers = {'execute': self._execute, 'order': self._draft_order, 'edit_order': self._edit_order,
            'issue': self._issue, 'cancel_exam': self._cancel_exam, 'dispense': self._dispense,
            'finish': self._finish, 'reconcile': self._reconcile, 'review_price': self._review_price,
            'correct': self._correct, 'return_material': self._return_material, 'refer': self._refer}
        if operation not in handlers or not isinstance(payload, dict) or not isinstance(key, str) or not 1 <= len(key) <= 120:
            raise ValidationError(self.env._('invalid_action: Supply a documented action and stable request key.'))
        try:
            inspect.signature(handlers[operation]).bind(**payload)
        except TypeError as error:
            raise ValidationError(self.env._('invalid_action: Unknown or missing execution arguments.')) from error
        category = 'pharmacy' if operation in ('dispense', 'finish') else 'price' if operation == 'review_price' else 'medical'
        if operation in ('reconcile', 'return_material'):
            event = self._model('event').browse(self.env['ydental.intake.service']._id(payload.get('event_id'))).exists()
            if event and event.ydental_kind == 'prescription':
                category = 'pharmacy'
        store = self._access(category)
        queue = self.env['ydental.queue.service']
        queue._connection()
        digest = fingerprint([operation, store.id, payload])
        with self.env.cr.savepoint():
            # S01 user/session -> S04 patient -> S03 supply -> S05 intake ->
            # S06 queue -> S07 inventory. All B paths acquire this before native
            # stock or B sources; source adapters never acquire upstream fences.
            queue._locks()
            self.env['ydental.inventory.service']._lock()
            self.env.cr.execute('SELECT pg_advisory_xact_lock(%s)', [32008])
            self._access(category)
            queue._connection()
            prior = self._model('receipt').search([('ydental_actor_id', '=', self.env.uid), ('ydental_key', '=', key)], limit=1)
            if prior:
                if prior.ydental_fingerprint != digest:
                    raise UserError(self.env._('version_conflict: This key belongs to another action.'))
                return dict(prior.ydental_result, result='already_accepted')
            result = handlers[operation](**payload)
            self._model('receipt')._new({'name': operation, 'ydental_store_id': store.id, 'ydental_category': category,
                'ydental_actor_id': self.env.uid, 'ydental_key': key, 'ydental_fingerprint': digest, 'ydental_result': result})
            return dict(result, result='accepted')

    def _serving(self, execution_id, lease_id, lease_token, category):
        queue = self.env['ydental.queue.service']
        lease = queue._held(lease_id, lease_token)
        execution = queue._source_execution(execution_id, lease)
        if execution.state != 'serving' or lease.ydental_category != category or lease.ydental_expires_at <= queue._now():
            raise AccessError(self.env._('execution_required: The current holder must start the actual service.'))
        store = self._access(category)
        if execution.ydental_store_id != store or execution.ydental_service_snapshot != queue._service_snapshot(execution.ydental_task_id):
            raise UserError(self.env._('version_conflict: The actual service source changed.'))
        failure = queue._service_eligibility(queue._execution_entry(execution), lease.ydental_station_id)
        if failure:
            raise AccessError(failure)
        self.env['ydental.patient.service']._current_relation(execution.ydental_patient_id, store)
        return execution

    def _medical(self, execution_id, lease_id, lease_token, document_id, document_version):
        execution = self._serving(execution_id, lease_id, lease_token, 'medical')
        doc = self.env['ydental.clinical.service']._document(document_id, write=True)
        if doc.ydental_current_execution_id != execution or type(document_version) is not int or doc.ydental_version != document_version or document_version < 1:
            raise UserError(self.env._('save_required: Save and verify the current document version before the clinical action.'))
        return execution, doc

    def _quantity(self, quantity, unit, signed=False):
        if type(quantity) not in (float, int) or not math.isfinite(quantity) or (
                unit.compare(abs(quantity) if signed else quantity, 0) <= 0) or abs(unit.round(quantity) - quantity) > 1e-8:
            raise ValidationError(self.env._('invalid_quantity: Use a finite quantity aligned to the native unit.'))
        return quantity

    def _project(self, execution, catalog_id):
        intake = self.env['ydental.intake.service']
        catalog = intake._get('catalog', catalog_id)
        task = execution.ydental_task_id
        mapping = intake._model('mapping').search([('ydental_store_id', '=', execution.ydental_store_id.id),
            ('ydental_catalog_id', '=', catalog.id), ('active', '=', True)], limit=1)
        station = execution.ydental_lease_id.ydental_station_id
        if not mapping or not catalog.active or catalog.ydental_kind not in ('care', 'procedure', 'medicine') or (
                catalog.ydental_capability_id not in station.ydental_capability_ids.filtered('active') or
                catalog.ydental_capability_id not in self.env.user.ydental_capability_ids.filtered('active') or
                catalog.ydental_qualification != task.ydental_mapping_id.ydental_catalog_id.ydental_qualification):
            raise AccessError(self.env._('qualification_required: The project needs an approved store mapping, workstation capability and actual practitioner qualification.'))
        return catalog

    def _quote(self, event):
        intake = self.env['ydental.intake.service']
        # Freeze at the actual event time. A future replacement is never used
        # to silently reconstruct an unknown historical price.
        version, values = intake._quote(event.ydental_store_id, event.ydental_catalog_id.id,
            event.ydental_store_id.company_id.currency_id.id, abs(event.ydental_quantity), instant=event.ydental_actual_at)
        snapshot = intake._new('snapshot', event.ydental_store_id, dict(values, name=event.ydental_source,
            ydental_source='s08b-event-' + str(event.id), ydental_policy='demo_confirmation', ydental_actor_id=self.env.uid))
        event._save({'ydental_price_snapshot_id': snapshot.id})

    def _price_values(self, event):
        if event.ydental_price_snapshot_id:
            snap = event.ydental_price_snapshot_id
            return {'version': snap.ydental_price_id.id, 'currency': snap.ydental_currency_id.id,
                'unit_price': snap.ydental_unit_price, 'policy': 'demo_confirmation'}
        if event.ydental_price_review_id:
            review = event.ydental_price_review_id
            return {'version': 'review-' + str(review.id), 'currency': review.ydental_currency_id.id,
                'unit_price': review.ydental_unit_price, 'policy': 'demo_confirmation'}
        return None

    def _material_rows(self, rows, category, store):
        if not isinstance(rows, list) or len(rows) > 16:
            raise ValidationError(self.env._('invalid_material: Supply at most sixteen explicitly verified batches.'))
        inventory = self.env['ydental.inventory.service']
        result, seen = [], set()
        for row in rows:
            if not isinstance(row, dict) or set(row) != {'lot_id', 'quantity', 'uom_id', 'kind'} or row['kind'] not in ('treatment', 'chairside', 'prescription'):
                raise ValidationError(self.env._('invalid_material: Supply batch, real quantity, native unit and source kind.'))
            if (row['kind'] == 'prescription') != (category == 'pharmacy'):
                raise AccessError(self.env._('source_category_mismatch: Select material or chairside use for treatment.'))
            lot = inventory._lot(row['lot_id'], store)
            inventory._check_source_product(row['kind'], lot)
            inventory._unit(lot.product_id, row['quantity'], row['uom_id'])
            if lot.id in seen:
                raise ValidationError(self.env._('invalid_material: Record each physical batch once.'))
            seen.add(lot.id)
            result.append(row)
        return result

    def _event(self, execution, catalog, quantity, source, reason, rows, *, doc=None, teeth=None,
               already_performed=False, kind='treatment', line=None, parent=None, actual_at=None):
        if not isinstance(source, str) or not 1 <= len(source) <= 120 or type(already_performed) is not bool:
            raise ValidationError(self.env._('invalid_source: Supply a stable source identifier and explicit fact status.'))
        if not (kind == 'correction' and type(quantity) in (int, float) and quantity == 0 and rows):
            quantity = self._quantity(quantity, catalog.ydental_product_id.uom_id, signed=kind == 'correction')
        reason = self.env['ydental.intake.service']._text(reason)
        rows = self._material_rows(rows, execution.ydental_category, execution.ydental_store_id)
        if actual_at is not None and (not isinstance(actual_at, str) or len(actual_at) != 19):
            raise ValidationError(self.env._('invalid_time: Supply an explicit UTC date and time with seconds.'))
        moment = fields.Datetime.to_datetime(actual_at) if actual_at else fields.Datetime.now()
        if moment < execution.ydental_started_at or moment > fields.Datetime.now():
            raise ValidationError(self.env._('invalid_time: Actual time must fall within this started service and cannot be in the future.'))
        digest = fingerprint([actual_at, execution.id, catalog.id, quantity, reason, rows, doc.id if doc else False,
            doc.ydental_version if doc else 0, teeth, already_performed, kind, line.id if line else False, parent.id if parent else False])
        prior = self._model('event').search([('ydental_store_id', '=', execution.ydental_store_id.id), ('ydental_source', '=', source)], limit=1)
        if prior:
            if prior.ydental_fingerprint != digest or prior.ydental_actor_id.id != self.env.uid:
                raise UserError(self.env._('version_conflict: This clinical source already has immutable execution parameters.'))
            return self._event_result(prior)
        event = self._new('event', execution, {'name': catalog.name, 'ydental_execution_id': execution.id,
            'ydental_document_id': doc.id if doc else False, 'ydental_document_version': doc.ydental_version if doc else 0,
            'ydental_order_line_id': line.id if line else False, 'ydental_source': source, 'ydental_fingerprint': digest,
            'ydental_kind': kind, 'ydental_catalog_id': catalog.id, 'ydental_quantity': quantity,
            'ydental_uom_id': catalog.ydental_product_id.uom_id.id, 'ydental_teeth': teeth,
            'ydental_actual_at': moment, 'ydental_business_date': self.env['ydental.supply.service']._date(execution.ydental_store_id, moment),
            'ydental_station_id': execution.ydental_lease_id.ydental_station_id.id, 'ydental_reason': reason,
            'ydental_already_performed': already_performed, 'ydental_parent_id': parent.id if parent else False})
        if parent:
            event._save({'ydental_price_snapshot_id': parent.ydental_price_snapshot_id.id,
                'ydental_price_review_id': parent.ydental_price_review_id.id})
        else:
            try:
                self._quote(event)
            except UserError as error:
                if not already_performed or not str(error).startswith('missing_price:'):
                    raise
                event._save({'ydental_pending_reason': 'missing_price'})
        for row in rows:
            self._new('consumption', event, {'name': source, 'ydental_event_id': event.id,
                'ydental_lot_id': row['lot_id'], 'ydental_quantity': row['quantity'],
                'ydental_uom_id': row['uom_id'], 'ydental_kind': row['kind']})
        self._settle(event)
        self._audit('actual_execution', event, self._event_result(event), reason)
        return self._event_result(event)

    def _settle(self, event):
        price = self._price_values(event)
        if not price:
            event._save({'ydental_pending_reason': 'missing_price'})
            return
        pending = []
        rows = self._model('consumption').search([('ydental_event_id', '=', event.id)])
        inventory = self.env['ydental.inventory.service']
        # If a real historical project is short in any batch, persist its S07
        # pending fact first and defer every other issue. No partial native
        # consumption is posted merely because another material was available.
        unavailable = rows.filtered(lambda row: row.ydental_inventory_event_id and row.ydental_inventory_event_id.state != 'done')
        for row in rows.filtered(lambda row: not row.ydental_inventory_event_id):
            lot = row.ydental_lot_id
            config = inventory._config(event.ydental_store_id)
            stock_quantity, unit, unit_snapshot = inventory._unit(lot.product_id, row.ydental_quantity, row.ydental_uom_id.id)
            batch = inventory._batch(lot, event.ydental_store_id)
            unusable = not batch.ydental_enabled or not lot.product_id.active or not lot.expiration_date or lot.expiration_date <= fields.Datetime.now()
            short = lot.product_id.uom_id.compare(inventory._quantity(lot, inventory._location(config, lot.product_id)), stock_quantity) < 0
            if unusable or short:
                unavailable |= row
        if unavailable:
            for row in unavailable.filtered(lambda row: not row.ydental_inventory_event_id):
                result = inventory._source_action(InventorySource(self.env.uid, event.ydental_store_id.id, row.id))
                row._save({'ydental_inventory_event_id': result['id']})
            event._save({'ydental_pending_reason': 'inventory_pending'})
            return
        for row in rows:
            if not row.ydental_inventory_event_id:
                result = self.env['ydental.inventory.service']._source_action(InventorySource(self.env.uid, event.ydental_store_id.id, row.id))
                row._save({'ydental_inventory_event_id': result['id']})
            if row.ydental_inventory_event_id.state != 'done':
                pending.append(row.id)
        if pending:
            event._save({'ydental_pending_reason': 'inventory_pending'})
            return
        if not self._model('fee').search_count([('ydental_event_id', '=', event.id)]):
            currency = self.env['res.currency'].browse(price['currency'])
            parent_fee = self._model('fee').search([('ydental_event_id', '=', event.ydental_parent_id.id)], limit=1) if event.ydental_parent_id else False
            self._new('fee', event, {'name': event.name, 'ydental_event_id': event.id,
                'ydental_parent_id': parent_fee.id if parent_fee else False,
                'ydental_price_snapshot_id': event.ydental_price_snapshot_id.id,
                'ydental_price_review_id': event.ydental_price_review_id.id,
                'ydental_quantity': event.ydental_quantity, 'ydental_unit_price': price['unit_price'],
                'ydental_currency_id': currency.id, 'ydental_amount': currency.round(event.ydental_quantity * price['unit_price']),
                'ydental_policy': 'demo_confirmation'})
        event._save({'state': 'confirmed', 'ydental_pending_reason': False})

    def _event_result(self, event):
        fee = self._model('fee').search([('ydental_event_id', '=', event.id)], limit=1)
        rows = self._model('consumption').search([('ydental_event_id', '=', event.id)])
        return {'event_id': event.id, 'state': event.state, 'pending_reason': event.ydental_pending_reason or '',
            'fee_id': fee.id, 'amount': fee.ydental_amount if fee else None,
            'inventory_event_ids': rows.ydental_inventory_event_id.ids,
            'move_ids': rows.ydental_inventory_event_id.ydental_move_id.ids,
            'policy': 'demo_confirmation'}

    def _execute(self, execution_id, lease_id, lease_token, document_id, document_version, catalog_id,
                 quantity, source, reason, materials, teeth, already_performed, policy, actual_at=None):
        if policy != 'demo_confirmation':
            raise UserError(self.env._('policy_unpublished: Production price policy awaits approval.'))
        execution, doc = self._medical(execution_id, lease_id, lease_token, document_id, document_version)
        catalog = self._project(execution, catalog_id)
        content = dict(self.env['ydental.clinical.service']._empty(), teeth=teeth)
        teeth = self.env['ydental.clinical.service']._content(content)['teeth']
        kind = 'chairside' if catalog.ydental_kind == 'medicine' else 'treatment'
        return self._event(execution, catalog, quantity, source, reason, materials, doc=doc,
            teeth=teeth, already_performed=already_performed, kind=kind, actual_at=actual_at)

    def _reconcile(self, event_id, reason):
        event = self._model('event').browse(self.env['ydental.intake.service']._id(event_id)).exists()
        if not event:
            raise AccessError(self.env._('access_denied: This clinical event is unavailable.'))
        self._get('event', event.id, 'pharmacy' if event.ydental_kind == 'prescription' else 'medical')
        reason = self.env['ydental.intake.service']._text(reason)
        if event.ydental_actor_id.id != self.env.uid:
            raise AccessError(self.env._('access_denied: Only the original responsible operator can reconcile this clinical fact.'))
        if event.state != 'confirmed':
            # Warehouse staff reconcile the original S07 pending record using
            # S07's evidence-only recovery. This action only reads that outcome.
            self._settle(event)
        self._audit('reconcile', event, self._event_result(event), reason)
        return self._event_result(event)

    def _review_price(self, event_id, unit_price, currency_id, evidence):
        event = self._get('event', event_id, 'price')
        if self._price_values(event) or not event.ydental_already_performed or event.ydental_pending_reason != 'missing_price':
            raise UserError(self.env._('version_conflict: Only an unpriced historical fact can receive an evidenced manual review.'))
        currency = event.ydental_store_id.company_id.currency_id
        if currency.id != currency_id or type(unit_price) not in (int, float) or not math.isfinite(unit_price) or unit_price <= 0:
            raise ValidationError(self.env._('missing_price: An evidenced positive historical price and source currency are required.'))
        review = self._new('price.review', event, {'name': event.name, 'ydental_event_id': event.id,
            'ydental_currency_id': currency.id, 'ydental_unit_price': unit_price,
            'ydental_evidence': self.env['ydental.intake.service']._text(evidence), 'ydental_reviewed_at': fields.Datetime.now()})
        event._save({'ydental_price_review_id': review.id})
        self._audit('historical_price_review', event, {'review_id': review.id}, evidence)
        return {'review_id': review.id, 'event_id': event.id, 'state': 'pending'}

    def _correct(self, event_id, execution_id, lease_id, lease_token, document_id, document_version,
                 delta, source, reason, materials):
        execution, doc = self._medical(execution_id, lease_id, lease_token, document_id, document_version)
        parent = self._get('event', event_id, 'medical')
        if parent.ydental_patient_id != execution.ydental_patient_id or parent.ydental_kind not in ('treatment', 'chairside') or parent.state != 'confirmed':
            raise UserError(self.env._('correction_required: Select a confirmed treatment source for this patient.'))
        self._project(execution, parent.ydental_catalog_id.id)
        if not (type(delta) in (int, float) and delta == 0 and materials):
            self._quantity(delta, parent.ydental_uom_id, signed=True)
        corrections = self._model('event').search([('ydental_parent_id', '=', parent.id)])
        prior = corrections.filtered(lambda e: e.ydental_source == source)
        net = parent.ydental_quantity + sum((corrections - prior).mapped('ydental_quantity')) + delta
        if net < 0 or delta < 0 and materials:
            raise ValidationError(self.env._('invalid_quantity: A correction cannot exceed the original quantity; physical returns require a separate verified return.'))
        return self._event(execution, parent.ydental_catalog_id, delta, source, reason, materials,
            doc=doc, teeth=parent.ydental_teeth, kind='correction', parent=parent)

    def _return_material(self, event_id, inventory_event_id, quantity, uom_id, source, reason):
        event = self._model('event').browse(self.env['ydental.intake.service']._id(event_id)).exists()
        category = 'pharmacy' if event and event.ydental_kind == 'prescription' else 'medical'
        event = self._get('event', event_id, category)
        row = self._model('consumption').search([('ydental_event_id', '=', event.id),
            ('ydental_inventory_event_id', '=', inventory_event_id)], limit=1)
        if not row or row.ydental_inventory_event_id.state != 'done':
            raise AccessError(self.env._('source_required: Select a completed physical issue from this clinical event.'))
        result = self.env['ydental.inventory.service']._return(event.ydental_store_id, inventory_event_id,
            quantity, uom_id, source, reason)
        self._audit('physical_return_quarantine', event, result, reason)
        return result

    def _order_lines(self, order, lines):
        if not isinstance(lines, list) or not 1 <= len(lines) <= 16:
            raise ValidationError(self.env._('invalid_order: Supply one to sixteen explicit order lines.'))
        intake = self.env['ydental.intake.service']
        results = []
        for row in lines:
            keys = {'mapping_id', 'quantity', 'uom_id', 'product_id', 'specification', 'usage', 'frequency', 'course'}
            if not isinstance(row, dict) or set(row) != keys:
                raise ValidationError(self.env._('invalid_order: Supply the complete reviewed order field set.'))
            mapping = intake._target(row['mapping_id'], order.ydental_store_id)
            kind = mapping.ydental_catalog_id.ydental_kind
            if kind != ('exam' if order.ydental_kind == 'exam' else 'medicine'):
                raise ValidationError(self.env._('source_category_mismatch: Examination and pharmacy order mappings are separate.'))
            unit = self.env['uom.uom'].sudo().browse(intake._id(row['uom_id'])).exists()
            if not unit:
                raise ValidationError(self.env._('invalid_quantity: Select an existing native unit.'))
            self._quantity(row['quantity'], unit)
            values = {'name': mapping.name, 'ydental_order_id': order.id, 'ydental_mapping_id': mapping.id,
                'ydental_quantity': row['quantity'], 'ydental_uom_id': unit.id}
            if order.ydental_kind == 'prescription':
                product = self.env['product.product'].sudo().browse(intake._id(row['product_id'])).exists()
                if not product or not product.active or product.ydental_inventory_kind != 'medicine' or unit != product.uom_id or unit != mapping.ydental_catalog_id.ydental_product_id.uom_id:
                    raise ValidationError(self.env._('invalid_order: Select a real active S07 medicine and matching native stock and service units.'))
                values['ydental_product_id'] = product.id
                for field in ('specification', 'usage', 'frequency', 'course'):
                    values['ydental_' + field] = intake._text(row[field])
                # One pharmacy task has one exact service mapping. Multiple
                # medicines may share it; different service directions require
                # independent prescriptions and explicit reporting.
                if results and results[0]['ydental_mapping_id'] != mapping.id:
                    raise ValidationError(self.env._('invalid_order: One prescription must have one exact pharmacy service direction.'))
            elif unit != mapping.ydental_catalog_id.ydental_product_id.uom_id or row['product_id'] or any(row[f] for f in ('specification', 'usage', 'frequency', 'course')):
                raise ValidationError(self.env._('invalid_order: Examination lines use their exact service unit and no medication fields.'))
            results.append(values)
        return results

    def _draft_order(self, execution_id, lease_id, lease_token, document_id, document_version, kind, purpose, lines):
        execution, doc = self._medical(execution_id, lease_id, lease_token, document_id, document_version)
        if kind not in ('exam', 'prescription'):
            raise ValidationError(self.env._('invalid_order: Select an examination or take-away prescription.'))
        order = self._new('order', execution, {'name': self.env['ydental.intake.service']._text(purpose),
            'ydental_purpose': purpose, 'ydental_kind': kind, 'ydental_execution_id': execution.id,
            'ydental_document_id': doc.id, 'ydental_document_version': doc.ydental_version})
        for values in self._order_lines(order, lines):
            self._new('line', order, values)
        self._audit('order_draft', order)
        return {'order_id': order.id, 'version': order.ydental_version, 'state': order.state}

    def _edit_order(self, order_id, version, execution_id, lease_id, lease_token, document_id, document_version, purpose, lines):
        execution, doc = self._medical(execution_id, lease_id, lease_token, document_id, document_version)
        order = self._get('order', order_id, 'medical')
        if order.ydental_execution_id != execution or order.state != 'draft' or order.ydental_version != version:
            raise UserError(self.env._('order_frozen: Only the original draft can be edited at its current version.'))
        # Retain superseded draft rows as cancelled history, never delete them.
        self._model('line').search([('ydental_order_id', '=', order.id), ('state', '=', 'draft')])._save({
            'state': 'cancelled', 'ydental_reason': 'Superseded before issue'})
        for values in self._order_lines(order, lines):
            self._new('line', order, values)
        order._save({'name': self.env['ydental.intake.service']._text(purpose), 'ydental_purpose': purpose,
            'ydental_version': version + 1, 'ydental_document_version': doc.ydental_version})
        self._audit('order_draft_edit', order)
        return {'order_id': order.id, 'version': order.ydental_version, 'state': order.state}

    def _task(self, order, mapping):
        intake = self.env['ydental.intake.service']
        intake._target(mapping.id, order.ydental_store_id)
        return intake._new('task', order.ydental_store_id, dict(intake._identity(order.ydental_patient_id),
            name=mapping.name, ydental_mapping_id=mapping.id,
            ydental_parent_task_id=order.ydental_execution_id.ydental_task_id.id, ydental_source_kind='derived'))

    def _next_segment(self, order):
        prior = self._model('segment').search([('ydental_order_id', '=', order.id), ('state', 'in', ('pending', 'active'))], limit=1)
        if prior:
            return prior
        lines = self._model('line').search([('ydental_order_id', '=', order.id), ('state', '!=', 'cancelled')])
        if not any(self._remaining(line) > 0 for line in lines):
            return self._model('segment')
        sequence = self._model('segment').search_count([('ydental_order_id', '=', order.id)]) + 1
        task = self._task(order, lines[0].ydental_mapping_id)
        return self._new('segment', order, {'name': order.name, 'ydental_order_id': order.id,
            'ydental_task_id': task.id, 'ydental_sequence': sequence})

    def _issue(self, order_id, version, execution_id, lease_id, lease_token, document_id, document_version):
        execution, doc = self._medical(execution_id, lease_id, lease_token, document_id, document_version)
        order = self._get('order', order_id, 'medical')
        if order.ydental_execution_id != execution or order.state != 'draft' or version != order.ydental_version:
            raise UserError(self.env._('order_frozen: Issue only this encounter draft at its current version.'))
        lines = self._model('line').search([('ydental_order_id', '=', order.id), ('state', '=', 'draft')])
        if not lines:
            raise ValidationError(self.env._('invalid_order: An order needs at least one explicit line.'))
        order._save({'state': 'issued', 'ydental_version': version + 1})
        lines._save({'state': 'issued'})
        if order.ydental_kind == 'prescription':
            segment = self._next_segment(order)
            tasks = segment.ydental_task_id.ids
        else:
            tasks = []
            for line in lines:
                task = self._task(order, line.ydental_mapping_id)
                line._save({'ydental_task_id': task.id})
                tasks.append(task.id)
        self._audit('order_issued', order, {'task_ids': tasks, 'state': 'pending_reporting'})
        return {'order_id': order.id, 'version': order.ydental_version, 'state': order.state,
            'task_ids': tasks, 'line_ids': lines.ids}

    def _cancel_exam(self, line_id, order_version, execution_id, lease_id, lease_token, document_id, document_version, reason):
        execution, doc = self._medical(execution_id, lease_id, lease_token, document_id, document_version)
        line = self._get('line', line_id, 'medical')
        order = line.ydental_order_id
        if order.ydental_kind != 'exam' or order.ydental_patient_id != execution.ydental_patient_id or order.ydental_version != order_version:
            raise UserError(self.env._('order_frozen: Select a current examination source for this patient.'))
        task = line.ydental_task_id
        if line.state != 'issued' or task.state not in ('pending', 'accepted') or self.env['ydental.queue.service']._model('execution').search_count([('ydental_task_id', '=', task.id)]):
            raise UserError(self.env._('already_started: An examination that has started cannot be cancelled as unperformed.'))
        reason = self.env['ydental.intake.service']._text(reason)
        intake = self.env['ydental.intake.service']
        if intake._model('position').search_count([('ydental_task_id', '=', task.id), ('ydental_active', '=', True)]):
            intake._withdraw(task, reason)
        task._save({'state': 'cancelled', 'ydental_reason': reason})
        line._save({'state': 'cancelled', 'ydental_reason': reason})
        order._save({'ydental_version': order.ydental_version + 1})
        self._audit('exam_unperformed_cancel', line, {'task_id': task.id}, reason)
        return {'line_id': line.id, 'state': 'cancelled', 'order_version': order.ydental_version}

    def _remaining(self, line):
        # Actual issue facts, including pending bookkeeping, consume the
        # approved allowance. Physical returns never reopen the prescription.
        events = self._model('event').search([('ydental_order_line_id', '=', line.id), ('ydental_kind', '=', 'prescription')])
        return line.ydental_quantity - sum(events.mapped('ydental_quantity'))

    def _pharmacy(self, execution_id, lease_id, lease_token, order_id, order_version):
        execution = self._serving(execution_id, lease_id, lease_token, 'pharmacy')
        order = self._get('order', order_id, 'pharmacy')
        segment = self._model('segment').search([('ydental_task_id', '=', execution.ydental_task_id.id),
            ('ydental_order_id', '=', order.id), ('state', 'in', ('pending', 'active'))], limit=1)
        if not segment or order.state != 'issued' or order.ydental_version != order_version or order.ydental_patient_id != execution.ydental_patient_id:
            raise UserError(self.env._('order_frozen: Select the issued prescription version bound to this actual pharmacy segment.'))
        if segment.ydental_execution_id and segment.ydental_execution_id != execution:
            raise UserError(self.env._('version_conflict: This prescription segment is bound to another execution.'))
        segment._save({'state': 'active', 'ydental_execution_id': execution.id})
        return execution, order, segment

    def _dispense(self, execution_id, lease_id, lease_token, order_id, order_version, line_id,
                  lot_id, quantity, source, reason, policy):
        if policy != 'demo_confirmation':
            raise UserError(self.env._('policy_unpublished: Production price policy awaits approval.'))
        execution, order, segment = self._pharmacy(execution_id, lease_id, lease_token, order_id, order_version)
        line = self._get('line', line_id, 'pharmacy')
        if line.ydental_order_id != order or line.state != 'issued':
            raise AccessError(self.env._('source_required: Select an issued line of the called prescription.'))
        self._quantity(quantity, line.ydental_uom_id)
        prior = self._model('event').search([('ydental_store_id', '=', order.ydental_store_id.id), ('ydental_source', '=', source)], limit=1)
        remaining = self._remaining(line) + (prior.ydental_quantity if prior and prior.ydental_order_line_id == line else 0)
        if line.ydental_uom_id.compare(quantity, remaining) > 0:
            raise UserError(self.env._('overdispense: The actual issue would exceed the remaining approved quantity.'))
        lot = self.env['ydental.inventory.service']._lot(lot_id, order.ydental_store_id)
        if lot.product_id != line.ydental_product_id:
            raise ValidationError(self.env._('source_category_mismatch: The batch must contain the exact prescribed medicine.'))
        result = self._event(execution, line.ydental_mapping_id.ydental_catalog_id, quantity, source, reason,
            [{'lot_id': lot.id, 'quantity': quantity, 'uom_id': line.ydental_uom_id.id, 'kind': 'prescription'}], kind='prescription', line=line)
        self._audit('actual_dispense', order, dict(result, line_id=line.id, remaining=self._remaining(line)))
        return dict(result, line_id=line.id, remaining=self._remaining(line))

    def _finish(self, execution_id, lease_id, lease_token, order_id, order_version, reason):
        execution, order, segment = self._pharmacy(execution_id, lease_id, lease_token, order_id, order_version)
        reason = self.env['ydental.intake.service']._text(reason)
        events = self._model('event').search([('ydental_execution_id', '=', execution.id)])
        if events.filtered(lambda e: e.state != 'confirmed'):
            raise UserError(self.env._('reconcile_required: Reconcile this actual dispensing segment before finishing.'))
        queue = self.env['ydental.queue.service']
        queue._finish_pharmacy_segment(execution)
        segment._save({'state': 'done', 'ydental_finished_at': fields.Datetime.now()})
        segment.flush_recordset(['state'])
        following = self._next_segment(order)
        if not following:
            order._save({'state': 'done'})
            self._model('line').search([('ydental_order_id', '=', order.id), ('state', '=', 'issued')])._save({'state': 'done'})
        queue._exit(lease_id, lease_token)
        self._audit('pharmacy_segment_finished', segment, {'execution_id': execution.id,
            'next_task_id': following.ydental_task_id.id, 'lease_released': True}, reason)
        return {'execution_id': execution.id, 'state': 'completed', 'order_state': order.state,
            'next_task_id': following.ydental_task_id.id, 'next_segment_id': following.id}

    def _refer(self, execution_id, lease_id, lease_token, document_id, document_version,
               mode, mapping_id, reason, start=None, end=None, valid_until=None, source=None):
        execution, doc = self._medical(execution_id, lease_id, lease_token, document_id, document_version)
        intake = self.env['ydental.intake.service']
        mapping = intake._target(mapping_id)
        if mapping.ydental_store_id == execution.ydental_store_id or mode not in ('timed', 'untimed'):
            raise ValidationError(self.env._('invalid_referral: Select an exact target service in another store.'))
        if mapping.ydental_store_id.company_id not in self.env.user.sudo().company_ids:
            raise AccessError(self.env._('access_denied: Cross-legal-entity referral requires explicit account company authorization.'))
        args = {'source_task_id': execution.ydental_task_id.id, 'version': execution.ydental_task_id.ydental_version,
            'mapping_id': mapping.id, 'reason': intake._text(reason)}
        if mode == 'timed':
            if valid_until is not None or not start or not end:
                raise ValidationError(self.env._('invalid_referral: A timed referral requires one explicit slot.'))
            args.update(start=start, end=end)
        else:
            if start is not None or end is not None or not valid_until:
                raise ValidationError(self.env._('invalid_referral: An untimed referral requires only its explicit UTC expiry.'))
            args['valid_until'] = valid_until
        if not isinstance(source, str) or not 1 <= len(source) <= 100:
            raise ValidationError(self.env._('invalid_source: Supply a stable referral source identifier.'))
        operation = 'refer_timed' if mode == 'timed' else 'refer_untimed'
        permit = ReferralSource(self.env.uid, execution.ydental_store_id.id, execution.id, lease_id,
            lease_token, doc.id, doc.ydental_version, fingerprint([operation, args]))
        result = intake._referral_action(operation, args, 's08b-referral-' + source, permit=permit)
        self._audit('referral_initiated', doc, result, reason)
        return result

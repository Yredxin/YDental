import hashlib
import json
import inspect
import math
from dataclasses import dataclass

from odoo import fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.float_utils import float_compare, float_round

from .ydental_intake_record import MUTATION


@dataclass(frozen=True)
class CapacityPermit:
    actor_id: int
    store_id: int
    operation: str
    fingerprint: str


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


class YDentalIntakeService(models.AbstractModel):
    _name = 'ydental.intake.service'
    _description = 'Atomic service pricing and capacity-backed intake'

    def _now(self):
        return fields.Datetime.now()

    def _read_access(self):
        access = self.env['ydental.access.service']
        session = access._scope()
        member = access._membership(self.env.uid, session.ydental_store_id.id)
        if member:
            for category in ('frontdesk', 'price', 'medical', 'exam'):
                if access._levels(member)[category] in ('read', 'write'):
                    return access._check(category, 'read').ydental_store_id
        raise AccessError(self.env._('access_denied: Service intake read permission is required.'))

    def _business_read_access(self):
        access = self.env['ydental.access.service']
        session = access._scope()
        member = access._membership(self.env.uid, session.ydental_store_id.id)
        if member:
            for category in ('frontdesk', 'medical', 'exam'):
                if access._levels(member)[category] in ('read', 'write'):
                    return access._check(category, 'read').ydental_store_id
        raise AccessError(self.env._('access_denied: Patient intake read permission is required.'))

    def _access(self, operation):
        access = self.env['ydental.access.service']
        if operation in ('catalog', 'catalog_edit'):
            member = access._check('price', 'write', write=True)
            if not access._is_group_manager():
                raise AccessError(self.env._('access_denied: Group master data authority is required.'))
            return member.ydental_store_id
        if operation in ('mapping', 'mapping_edit', 'price', 'review', 'publish'):
            return access._check('price', 'write', write=True).ydental_store_id
        if operation in ('snapshot',):
            return access._check('price', 'read', write=True).ydental_store_id
        if operation in ('refer_timed', 'refer_untimed'):
            for category in ('medical', 'exam'):
                member = access._membership(self.env.uid, access._scope(write=True).ydental_store_id.id)
                if member and access._levels(member)[category] == 'write':
                    return access._check(category, 'write', write=True).ydental_store_id
            raise AccessError(self.env._('access_denied: A source store clinician must authorize a referral.'))
        return access._check('frontdesk', 'write', write=True).ydental_store_id

    def _lock(self):
        self.env.cr.execute('SELECT pg_advisory_xact_lock(%s)', [29005])
        mutex = self.env.ref('ydental_intake.ydental_intake_mutex')
        self.env.cr.execute('UPDATE ydental_intake_mutex SET ydental_revision=ydental_revision+1 WHERE id=%s', [mutex.id])
        self.env.invalidate_all()

    def _all_locks(self):
        self.env['ydental.patient.service']._lock()
        self.env['ydental.supply.service']._lock()
        self._lock()

    def _model(self, entity):
        # The entity is always a server literal from this module.
        return self.env['ydental.intake.' + entity].sudo()

    def _id(self, value):
        return self.env['ydental.patient.service']._id(value)

    def _get(self, entity, record_id, store=None):
        record = self._model(entity).with_context(active_test=False).browse(self._id(record_id)).exists()
        if not record or store and record.ydental_store_id != store:
            raise AccessError(self.env._('access_denied: Select a source in the authorized store.'))
        return record

    def _version(self, record, version):
        if type(version) is not int or version != record.ydental_version:
            raise UserError(self.env._('version_conflict: Refresh the service source before retrying.'))

    def _text(self, value):
        return self.env['ydental.patient.service']._text(value, required=True)

    def _instant(self, value):
        try:
            value = fields.Datetime.to_datetime(value)
        except (TypeError, ValueError) as error:
            raise ValidationError(self.env._('Use a valid UTC time without an offset.')) from error
        if not value or value.tzinfo:
            raise ValidationError(self.env._('Use a valid UTC time without an offset.'))
        return value

    def _new(self, entity, store, values):
        return self._model(entity)._new(dict(values, ydental_store_id=store.id))

    def _identity(self, patient):
        return {'ydental_patient_id': patient.id, 'ydental_origin_patient_id': patient.id,
                'ydental_identity_snapshot': self.env['ydental.patient.service']._identity_snapshot(patient)}

    def _patient(self, patient_id, store):
        service = self.env['ydental.patient.service']
        patient = service._business_patient(patient_id)
        # Establish the relationship without manufacturing first arrival.
        relation = service._ensure_relation(patient, store)
        service._audit('relation.intake', relation, after={'patient_id': patient.id, 'store_id': store.id})
        return patient

    def _operate(self, operation, payload, key):
        return self._run(operation, payload, key)

    def _run(self, operation, payload, key, downstream=False):
        handlers = {'catalog': self._catalog, 'catalog_edit': self._catalog_edit,
            'mapping': self._mapping, 'mapping_edit': self._mapping_edit,
            'price': self._price, 'review': self._review, 'publish': self._publish,
            'snapshot': self._snapshot, 'reserve': self._reserve, 'register': self._register,
            'arrive': self._arrive, 'report': self._report, 'walkin_report': self._walkin_report,
            'void': self._void, 'cancel': self._cancel, 'reschedule': self._reschedule,
            'refer_timed': self._refer_timed, 'refer_untimed': self._refer_untimed,
            'accept_referral': self._accept_referral, 'start': self._start, 'derived': self._derived}
        if operation not in handlers or not isinstance(payload, dict) or not isinstance(key, str) or not 1 <= len(key) <= 160:
            raise ValidationError(self.env._('A documented action, arguments and idempotency key are required.'))
        if (operation in ('start', 'derived')) != downstream:
            raise AccessError(self.env._('access_denied: This action requires the fixed downstream server hook.'))
        store = self._authorize_downstream(operation, payload) if downstream else self._access(operation)
        digest = fingerprint([operation, store.id, payload])
        with self.env.cr.savepoint():
            self._all_locks()
            # Revalidate live grants after locks, including transaction retries.
            if not downstream:
                self._access(operation)
            prior = self._model('operation').search([('ydental_actor_id', '=', self.env.uid), ('ydental_key', '=', key)], limit=1)
            if prior:
                if prior.ydental_fingerprint != digest:
                    raise UserError(self.env._('version_conflict: This key belongs to another action.'))
                return dict(prior.ydental_result, result='already_accepted')
            try:
                inspect.signature(handlers[operation]).bind(store, **payload)
            except TypeError as error:
                raise ValidationError(self.env._('Unknown or missing action arguments.')) from error
            result = dict(handlers[operation](store, **payload), result='accepted')
            self._new('operation', store, {'name': operation, 'ydental_actor_id': self.env.uid,
                'ydental_category': 'price' if operation in ('catalog', 'catalog_edit', 'mapping', 'mapping_edit', 'price', 'review', 'publish', 'snapshot') else 'frontdesk',
                'ydental_key': key, 'ydental_fingerprint': digest, 'ydental_result': result})
            self.env['ydental.access.service']._audit('intake.' + operation,
                'price' if operation in ('catalog', 'catalog_edit', 'mapping', 'mapping_edit', 'price', 'review', 'publish', 'snapshot') else 'frontdesk',
                self._model('operation').search([('ydental_actor_id', '=', self.env.uid), ('ydental_key', '=', key)]),
                store.id, after=result, source='intake_service')
            return result

    def _authorize_downstream(self, operation, payload):
        raise AccessError(self.env._('access_denied: Clinical source integration is not connected.'))

    def _downstream_action(self, operation, payload, key):
        return self._run(operation, payload, key, downstream=True)

    def _native(self, model):
        # Only catalog/pricing handlers use the unforgeable native mutation token.
        return self.env[model].sudo().with_context(ydental_intake_mutation=MUTATION)

    def _catalog(self, store, code, name, kind, capability_id, uom_id, qualification=''):
        if kind not in ('care', 'exam', 'medicine', 'procedure', 'prosthesis'):
            raise ValidationError(self.env._('Select a supported service category.'))
        capability = self.env['ydental.access.capability'].sudo().browse(self._id(capability_id)).exists()
        uom = self.env['uom.uom'].sudo().browse(self._id(uom_id)).exists()
        if not capability or not capability.active or not uom:
            raise ValidationError(self.env._('Select an active capability and native unit.'))
        product = self._native('product.template').create({'name': self._text(name), 'default_code': self._text(code),
            'type': 'service', 'uom_id': uom.id, 'ydental_intake_owned': True})
        record = self._model('catalog')._new({'name': name, 'ydental_code': code, 'ydental_kind': kind,
            'ydental_product_id': product.product_variant_id.id, 'ydental_capability_id': capability.id,
            'ydental_qualification': self.env['ydental.patient.service']._text(qualification)})
        return {'id': record.id, 'version': record.ydental_version}

    def _catalog_edit(self, store, record_id, version, name, active):
        record = self._get('catalog', record_id)
        self._version(record, version)
        if type(active) is not bool:
            raise ValidationError(self.env._('Use an explicit enabled value.'))
        record._save({'name': self._text(name), 'active': active})
        self._native('product.template').browse(record.ydental_product_id.product_tmpl_id.id).write({'name': name, 'active': active})
        return {'id': record.id, 'version': record.ydental_version}

    def _mapping(self, store, catalog_id, area_id, execution_area_id, capacity_required=True):
        catalog = self._get('catalog', catalog_id)
        supply = self.env['ydental.supply.service']
        area = supply._space('area', area_id, store)
        execution = supply._space('area', execution_area_id, store)
        if not catalog.active or not area.ydental_reporting or catalog.ydental_capability_id not in area.ydental_capability_ids or catalog.ydental_capability_id not in execution.ydental_capability_ids or type(capacity_required) is not bool:
            raise ValidationError(self.env._('Map the exact service capability to active reporting and execution areas.'))
        record = self._new('mapping', store, {'name': catalog.name + ' / ' + area.name,
            'ydental_catalog_id': catalog.id, 'ydental_area_id': area.id, 'ydental_execution_area_id': execution.id,
            'ydental_capacity_required': capacity_required})
        return {'id': record.id, 'version': record.ydental_version}

    def _mapping_edit(self, store, record_id, version, active):
        record = self._get('mapping', record_id, store)
        self._version(record, version)
        if type(active) is not bool:
            raise ValidationError(self.env._('Use an explicit enabled value.'))
        record._save({'active': active})
        return {'id': record.id, 'version': record.ydental_version}

    def _price(self, store, catalog_id, currency_id, unit_price, start, end, reason):
        catalog = self._get('catalog', catalog_id)
        currency = self.env['res.currency'].sudo().browse(self._id(currency_id)).exists()
        start, end = self._instant(start), self._instant(end)
        if not catalog.active or not currency or not currency.active or type(unit_price) not in (int, float) or not math.isfinite(unit_price) or unit_price <= 0 or start >= end:
            raise ValidationError(self.env._('Enter a positive base price, active currency and nonempty validity interval.'))
        uom = catalog.ydental_product_id.uom_id
        record = self._new('price', store, {'name': catalog.name, 'ydental_catalog_id': catalog.id,
            'ydental_currency_id': currency.id, 'ydental_uom_id': uom.id,
            'ydental_unit_price': currency.round(unit_price), 'ydental_start': start, 'ydental_end': end,
            'ydental_reason': self._text(reason)})
        header = self._native('product.pricelist').create({'name': 'S05 ' + str(record.id), 'currency_id': currency.id,
            'company_id': store.company_id.id, 'ydental_intake_owned': True, 'ydental_intake_store_id': store.id})
        rule = self._native('product.pricelist.item').create({'pricelist_id': header.id,
            'applied_on': '0_product_variant', 'product_id': catalog.ydental_product_id.id, 'uom_id': uom.id,
            'compute_price': 'fixed', 'fixed_price': record.ydental_unit_price, 'date_start': start, 'date_end': end})
        record._save({'ydental_pricelist_id': header.id, 'ydental_rule_id': rule.id})
        return {'id': record.id, 'version': record.ydental_version}

    def _review(self, store, record_id, version, reason):
        record = self._get('price', record_id, store)
        self._version(record, version)
        if record.state != 'draft':
            raise UserError(self.env._('Only a draft price can be reviewed.'))
        record._save({'state': 'reviewed', 'ydental_reviewed_by_id': self.env.uid, 'ydental_reason': self._text(reason)})
        return {'id': record.id, 'version': record.ydental_version}

    def _publish(self, store, record_id, version, reason, replace_id=None, replace_version=None):
        record = self._get('price', record_id, store)
        self._version(record, version)
        if record.state != 'reviewed':
            raise UserError(self.env._('Review a price before publication.'))
        condition = [('ydental_store_id', '=', store.id), ('ydental_catalog_id', '=', record.ydental_catalog_id.id),
            ('ydental_uom_id', '=', record.ydental_uom_id.id), ('ydental_currency_id', '=', record.ydental_currency_id.id), ('state', '=', 'published')]
        if replace_id:
            old = self._get('price', replace_id, store)
            self._version(old, replace_version)
            if old.id not in self._model('price').search(condition).ids or not old.ydental_start < record.ydental_start < old.ydental_end or record.ydental_start < self._now():
                raise ValidationError(self.env._('Replacement must close an overlapping matching price from now or later.'))
            old._save({'ydental_end': record.ydental_start})
            self._native('product.pricelist.item').browse(old.ydental_rule_id.id).write({'date_end': record.ydental_start})
        if self._model('price').search_count(condition + [('ydental_start', '<', record.ydental_end), ('ydental_end', '>', record.ydental_start)]):
            raise UserError(self.env._('version_conflict: Published price intervals must not overlap.'))
        record._save({'state': 'published', 'ydental_published_by_id': self.env.uid,
            'ydental_published_at': self._now(), 'ydental_reason': self._text(reason)})
        return {'id': record.id, 'version': record.ydental_version}

    def _quote(self, store, catalog_id, currency_id, quantity, instant=None):
        catalog = self._get('catalog', catalog_id)
        uom = catalog.ydental_product_id.uom_id
        if not catalog.active or type(quantity) not in (int, float) or not math.isfinite(quantity) or float_compare(quantity, 0, precision_rounding=uom.rounding) <= 0 or float_compare(quantity, float_round(quantity, precision_rounding=uom.rounding), precision_digits=8):
            raise ValidationError(self.env._('Use a positive quantity aligned to the service unit rounding.'))
        instant = instant or self._now()
        versions = self._model('price').search([('ydental_store_id', '=', store.id), ('ydental_catalog_id', '=', catalog.id),
            ('ydental_uom_id', '=', uom.id), ('ydental_currency_id', '=', self._id(currency_id)), ('state', '=', 'published'),
            ('ydental_start', '<=', instant), ('ydental_end', '>', instant)])
        if len(versions) != 1:
            raise UserError(self.env._('missing_price: Exactly one effective published price is required. Configure the store price.'))
        version = versions
        price, rule_id = version.ydental_pricelist_id._get_product_price_rule(catalog.ydental_product_id, quantity, uom=uom, date=instant)
        if rule_id != version.ydental_rule_id.id or version.ydental_currency_id.compare_amounts(price, version.ydental_unit_price):
            raise UserError(self.env._('version_conflict: Native price rule differs from the reviewed version.'))
        return version, {'ydental_catalog_id': catalog.id, 'ydental_price_id': version.id, 'ydental_product_name': catalog.name,
            'ydental_quantity': quantity, 'ydental_uom_id': uom.id, 'ydental_uom_name': uom.name,
            'ydental_currency_id': version.ydental_currency_id.id, 'ydental_unit_price': price,
            'ydental_amount': version.ydental_currency_id.round(price * quantity), 'ydental_quoted_at': instant}

    def _snapshot(self, store, catalog_id, currency_id, quantity, source, policy):
        if policy != 'demo_confirmation':
            raise UserError(self.env._('Production price policy is unpublished. Choose the explicit demonstration policy.'))
        source = self._text(source)
        previous = self._model('snapshot').search([('ydental_store_id', '=', store.id), ('ydental_source', '=', source)], limit=1)
        if previous:
            if (previous.ydental_catalog_id.id, previous.ydental_currency_id.id, previous.ydental_quantity, previous.ydental_policy) != (catalog_id, currency_id, quantity, policy):
                raise UserError(self.env._('version_conflict: Snapshot recovery requires the original source arguments.'))
            return {'id': previous.id, 'price_id': previous.ydental_price_id.id, 'amount': previous.ydental_amount, 'policy': previous.ydental_policy}
        version, values = self._quote(store, catalog_id, currency_id, quantity)
        record = self._new('snapshot', store, dict(values, name=source, ydental_source=source,
            ydental_policy=policy, ydental_actor_id=self.env.uid))
        return {'id': record.id, 'price_id': version.id, 'amount': record.ydental_amount, 'policy': policy}

    def _target(self, mapping_id, store=None):
        mapping = self._get('mapping', mapping_id, store)
        catalog = mapping.ydental_catalog_id
        if not mapping.active or not catalog.active or not catalog.ydental_capability_id.active or not mapping.ydental_store_id.active:
            raise UserError(self.env._('The selected store service is disabled.'))
        for area in (mapping.ydental_area_id, mapping.ydental_execution_area_id):
            if not area.active or catalog.ydental_capability_id not in area.ydental_capability_ids:
                raise UserError(self.env._('The exact selected service capability is unavailable in this area.'))
        if not mapping.ydental_area_id.ydental_reporting:
            raise UserError(self.env._('The selected area cannot accept reporting.'))
        return mapping

    def _open(self, mapping):
        business = self.env['ydental.supply.service']._business_record(mapping.ydental_store_id, mapping.ydental_area_id.id)
        if not business or business.state != 'open':
            raise UserError(self.env._('reporting_closed: The target area is not accepting ordinary reporting.'))

    def _capacity(self, store, operation, payload, key):
        permit = CapacityPermit(self.env.uid, store.id, operation, fingerprint(payload))
        return self.env['ydental.supply.service'].with_context(ydental_intake_capacity=permit)._capacity_action(operation, payload, key)

    def _capacity_args(self, mapping, channel, start, end, source_key):
        return {'area_id': mapping.ydental_area_id.id, 'capability_id': mapping.ydental_catalog_id.ydental_capability_id.id,
            'start': fields.Datetime.to_string(self._instant(start)), 'end': fields.Datetime.to_string(self._instant(end)),
            'channel': channel, 'source': 'ydental.intake.entitlement', 'source_key': source_key}

    def _qualify(self, store, patient_id, mapping_id, start, end, channel, source_task=None):
        mapping = self._target(mapping_id, store)
        patient = self._patient(patient_id, store)
        if channel == 'walkin':
            self._open(mapping)
            if self.env['ydental.supply.service']._date(store, self._instant(start)) != self.env['ydental.supply.service']._date(store):
                raise ValidationError(self.env._('Walk-in qualification is restricted to the current store business date.'))
        identity = self._identity(patient)
        # The task ID is a stable source for the S03 claim; all new rows roll back
        # with acquisition failure, including a newly established relationship.
        task = self._new('task', store, dict(identity, name=mapping.name, ydental_mapping_id=mapping.id))
        result = self._capacity(store, 'acquire', self._capacity_args(mapping, channel, start, end, str(task.id)), 'intake-acquire-' + str(task.id))
        entitlement = self._new('entitlement', store, dict(identity, name=mapping.name,
            ydental_mapping_id=mapping.id, ydental_claim_id=result['id'], ydental_channel=channel,
            ydental_source_task_id=source_task.id if source_task else False))
        task._save({'ydental_entitlement_id': entitlement.id})
        return {'id': entitlement.id, 'task_id': task.id, 'claim_id': result['id'], 'version': entitlement.ydental_version,
                'task_version': task.ydental_version, 'patient_id': patient.id}

    def _reserve(self, store, patient_id, mapping_id, start, end, channel='reservation'):
        if channel not in ('reservation', 'phone'):
            raise ValidationError(self.env._('Use the reservation or published telephone channel.'))
        return self._qualify(store, patient_id, mapping_id, start, end, channel)

    def _register(self, store, patient_id, mapping_id, start, end):
        return self._qualify(store, patient_id, mapping_id, start, end, 'walkin')

    def _arrive(self, store, patient_id):
        patient = self._patient(patient_id, store)
        date = self.env['ydental.supply.service']._date(store)
        arrival = self._model('arrival').search([('ydental_store_id', '=', store.id),
            ('ydental_patient_id', 'in', self.env['ydental.patient.service']._identity_ids(patient)), ('ydental_date', '=', date)], limit=1)
        if not arrival:
            self.env['ydental.patient.service']._arrival(store, patient.id)
            arrival = self._new('arrival', store, dict(self._identity(patient), name=patient.ydental_number,
                ydental_date=date, ydental_timezone=store.ydental_timezone, ydental_occurred_at=self._now(), ydental_actor_id=self.env.uid))
        return {'id': arrival.id, 'patient_id': patient.id}

    def _queue_accept(self, task, previous):
        """S06 extends under all three locks, failing atomically on refusal.

        This base implements only the S05 position contract. No queue number,
        waiting/calling state, sorting or workstation lease exists here.
        """
        return {'queue_status': 'NOT_RUN', 'queue_contract': 's05_position_only'}

    def _queue_void(self, position, reason):
        """S06 revokes its waiting/calling object here, never clinical orders."""
        return None

    def _queue_assert_idle(self, task):
        """S06 must also reject actual execution, even after queue departure."""
        if task.state in ('started', 'done'):
            raise UserError(self.env._('handover_required: A started task requires downstream clinical handling.'))

    def _position(self, patient):
        return self._model('position').search([('ydental_patient_id', '=', patient.id), ('ydental_active', '=', True)], limit=1)

    def _valid_task(self, task, store):
        patient = self.env['ydental.patient.service']._business_patient(task.ydental_patient_id.id)
        if task.ydental_patient_id != patient:
            raise UserError(self.env._('version_conflict: Refresh the canonical task identity.'))
        self.env['ydental.patient.service']._current_relation(patient, store)
        self._queue_assert_idle(task)
        if self._model('task').search_count([('ydental_patient_id', '=', patient.id), ('state', '=', 'started')]):
            raise UserError(self.env._('handover_required: This patient has an active execution segment.'))
        if task.state == 'cancelled':
            raise UserError(self.env._('This qualification was cancelled. Acquire a new qualification.'))
        mapping = self._target(task.ydental_mapping_id.id, store)
        self._open(mapping)
        entitlement = task.ydental_entitlement_id
        if entitlement:
            claim = entitlement.ydental_claim_id
            slot = claim.ydental_slot_id
            if entitlement.state != 'held' or claim.state != 'held' or self._now() >= slot.ydental_end:
                raise UserError(self.env._('This qualification is cancelled, expired or already started. Acquire or review it explicitly.'))
            if slot.state != 'published' or not self.env['ydental.supply.service']._coverage_valid(slot):
                raise UserError(self.env._('The original qualification requires supply review.'))
            # No saleability/free-balance test here: existing valid qualifications
            # retain their original slot and never acquire capacity again.
        elif task.ydental_source_kind == 'independent' or not task.ydental_parent_task_id:
            raise UserError(self.env._('An independent service requires its own qualification.'))
        return patient

    def _report(self, store, task_id, version):
        task = self._get('task', task_id, store)
        self._version(task, version)
        patient = self._valid_task(task, store)
        if not self._model('arrival').search_count([('ydental_store_id', '=', store.id), ('ydental_patient_id', 'in', self.env['ydental.patient.service']._identity_ids(patient)),
                ('ydental_date', '=', self.env['ydental.supply.service']._date(store))]):
            raise UserError(self.env._('Record actual arrival before service reporting.'))
        previous = self._position(patient)
        if previous and previous.ydental_task_id == task:
            return {'id': previous.id, 'task_id': task.id, 'version': task.ydental_version,
                    'queue_status': 'already_at_position'}
        if previous:
            if previous.ydental_store_id != store:
                raise UserError(self.env._('handover_required: Resolve the existing position in its own store first.'))
            self._queue_assert_idle(previous.ydental_task_id)
        contract = self._queue_accept(task, previous)
        # The target adapter accepts before the old position is withdrawn. Any
        # failure, including downstream revoke, rolls back the entire action.
        if previous:
            self._queue_void(previous, 'Successful explicit task switch')
            previous._save({'ydental_active': False, 'ydental_reason': 'Successful explicit task switch'})
            previous.ydental_task_id._save({'state': 'pending'})
        position = self._new('position', store, dict(self._identity(patient), name=task.name,
            ydental_task_id=task.id, ydental_accepted_at=self._now()))
        task._save({'state': 'accepted'})
        return dict(contract, id=position.id, task_id=task.id, version=task.ydental_version)

    def _walkin_report(self, store, patient_id, mapping_id, start, end):
        result = self._register(store, patient_id, mapping_id, start, end)
        self._arrive(store, patient_id)
        position = self._report(store, result['task_id'], result['task_version'])
        return dict(result, position_id=position['id'], task_version=position['version'], queue_status=position['queue_status'])

    def _withdraw(self, task, reason):
        self._queue_assert_idle(task)
        positions = self._model('position').search([('ydental_task_id', '=', task.id), ('ydental_active', '=', True)])
        for position in positions:
            self._queue_void(position, reason)
            position._save({'ydental_active': False, 'ydental_reason': reason})
        task._save({'state': 'pending', 'ydental_reason': reason})

    def _void(self, store, task_id, version, reason, cancel_qualification=False):
        task = self._get('task', task_id, store)
        self._version(task, version)
        if type(cancel_qualification) is not bool:
            raise ValidationError(self.env._('Explicitly choose whether to cancel qualification.'))
        reason = self._text(reason)
        self._withdraw(task, reason)
        if cancel_qualification:
            if not task.ydental_entitlement_id:
                raise UserError(self.env._('This derived task has no independent qualification to cancel.'))
            entitlement = task.ydental_entitlement_id
            self._cancel(store, entitlement.id, entitlement.ydental_version, reason)
        return {'id': task.id, 'version': task.ydental_version, 'qualification_cancelled': cancel_qualification}

    def _cancel(self, store, record_id, version, reason):
        entitlement = self._get('entitlement', record_id, store)
        reason = self._text(reason)
        # Same source can be safely cancelled again with a fresh key/version.
        self._version(entitlement, version)
        if entitlement.state == 'cancelled':
            return {'id': entitlement.id, 'version': entitlement.ydental_version, 'state': entitlement.state}
        if entitlement.state != 'held':
            raise UserError(self.env._('Started qualification cannot return capacity.'))
        tasks = self._model('task').search([('ydental_entitlement_id', '=', entitlement.id)])
        for task in tasks:
            self._withdraw(task, reason)
        self._capacity(store, 'cancel', {'id': entitlement.ydental_claim_id.id, 'reason': reason}, 'intake-cancel-' + str(entitlement.id))
        entitlement._save({'state': 'cancelled', 'ydental_reason': reason})
        tasks._save({'state': 'cancelled', 'ydental_reason': reason})
        return {'id': entitlement.id, 'version': entitlement.ydental_version, 'state': entitlement.state}

    def _reschedule(self, store, record_id, version, mapping_id, start, end, reason):
        entitlement = self._get('entitlement', record_id, store)
        self._version(entitlement, version)
        reason = self._text(reason)
        if entitlement.state != 'held':
            raise UserError(self.env._('Only an unused qualification can be rescheduled.'))
        mapping = self._target(mapping_id, store)
        if mapping.ydental_catalog_id != entitlement.ydental_mapping_id.ydental_catalog_id:
            raise ValidationError(self.env._('Rescheduling must preserve the selected service. New services require independent qualification.'))
        tasks = self._model('task').search([('ydental_entitlement_id', '=', entitlement.id)])
        for task in tasks:
            self._queue_assert_idle(task)
        if entitlement.ydental_channel == 'walkin' and self.env['ydental.supply.service']._date(store, self._instant(start)) != self.env['ydental.supply.service']._date(store):
            raise ValidationError(self.env._('Walk-in rescheduling must remain on the current store business date.'))
        revision = str(entitlement.id) + '-v' + str(version)
        result = self._capacity(store, 'reschedule', {'id': entitlement.ydental_claim_id.id,
            'target': self._capacity_args(mapping, entitlement.ydental_channel, start, end, revision), 'reason': reason}, 'intake-reschedule-' + revision)
        for task in tasks:
            self._withdraw(task, reason)
        entitlement._save({'ydental_claim_id': result['id'], 'ydental_mapping_id': mapping.id, 'ydental_reason': reason})
        tasks._save({'ydental_mapping_id': mapping.id})
        return {'id': entitlement.id, 'version': entitlement.ydental_version, 'claim_id': result['id']}

    def _referral_source(self, store, source_task_id, version, mapping_id):
        source = self._get('task', source_task_id, store)
        self._version(source, version)
        if source.state == 'cancelled':
            raise UserError(self.env._('A cancelled task cannot originate a referral.'))
        patient = self.env['ydental.patient.service']._business_patient(source.ydental_patient_id.id)
        self.env['ydental.patient.service']._current_relation(patient, store)
        mapping = self._target(mapping_id)
        if mapping.ydental_store_id.company_id.id not in self.env.user.company_ids.ids:
            raise AccessError(self.env._('access_denied: Referral target company is outside the authorized group.'))
        return source, patient, mapping

    def _refer_timed(self, store, source_task_id, version, mapping_id, start, end, reason):
        source, patient, mapping = self._referral_source(store, source_task_id, version, mapping_id)
        self._text(reason)
        return self._qualify(mapping.ydental_store_id, patient.id, mapping.id, start, end, 'reservation', source_task=source)

    def _refer_untimed(self, store, source_task_id, version, mapping_id, valid_until, reason):
        source, patient, mapping = self._referral_source(store, source_task_id, version, mapping_id)
        valid_until = self._instant(valid_until)
        if valid_until <= self._now():
            raise ValidationError(self.env._('An untimed referral requires an explicit future expiry.'))
        record = self._new('referral', mapping.ydental_store_id, dict(self._identity(patient), name=mapping.name,
            ydental_mapping_id=mapping.id, ydental_source_task_id=source.id,
            ydental_valid_until=valid_until, ydental_reason=self._text(reason)))
        return {'id': record.id, 'version': record.ydental_version, 'target_qualification': 'not_acquired'}

    def _accept_referral(self, store, record_id, version, start, end):
        record = self._get('referral', record_id, store)
        self._version(record, version)
        if record.state == 'accepted':
            return {'id': record.id, 'task_id': record.ydental_task_id.id, 'version': record.ydental_version}
        if record.ydental_valid_until <= self._now():
            raise UserError(self.env._('referral_expired: Reconfirm the referral explicitly; expiry cannot be extended silently.'))
        result = self._qualify(store, record.ydental_patient_id.id, record.ydental_mapping_id.id,
            start, end, 'walkin', source_task=record.ydental_source_task_id)
        self._arrive(store, record.ydental_patient_id.id)
        record._save({'state': 'accepted', 'ydental_task_id': result['task_id']})
        return dict(result, referral_id=record.id, referral_version=record.ydental_version)

    def _derived(self, store, source_task_id, version, mapping_id, kind):
        source = self._get('task', source_task_id, store)
        self._version(source, version)
        mapping = self._target(mapping_id, store)
        patient = self.env['ydental.patient.service']._business_patient(source.ydental_patient_id.id)
        self.env['ydental.patient.service']._current_relation(patient, store)
        if kind not in ('continuation', 'derived') or source.state not in ('started', 'done'):
            raise UserError(self.env._('A fixed actual encounter source is required for a derived task.'))
        if kind == 'continuation' and mapping.ydental_catalog_id != source.ydental_mapping_id.ydental_catalog_id:
            raise ValidationError(self.env._('A continuation must preserve its outpatient service direction and capability.'))
        existing = self._model('task').search([('ydental_parent_task_id', '=', source.id),
            ('ydental_mapping_id', '=', mapping.id), ('ydental_source_kind', '=', kind), ('state', 'in', ['pending', 'accepted'])], limit=1)
        if not existing:
            existing = self._new('task', store, dict(self._identity(patient), name=mapping.name,
                ydental_mapping_id=mapping.id, ydental_parent_task_id=source.id, ydental_source_kind=kind))
        return {'id': existing.id, 'version': existing.ydental_version}

    def _start(self, store, task_id, version):
        task = self._get('task', task_id, store)
        self._version(task, version)
        if task.state != 'accepted':
            raise UserError(self.env._('Only the accepted source task can start.'))
        patient = self._valid_task(task, store)
        position = self._position(patient)
        if not position or position.ydental_task_id != task:
            raise UserError(self.env._('The task no longer owns the accepted position.'))
        if task.ydental_entitlement_id:
            entitlement = task.ydental_entitlement_id
            self._capacity(store, 'consume', {'id': entitlement.ydental_claim_id.id}, 'intake-start-' + str(task.id))
            entitlement._save({'state': 'started'})
        self._queue_void(position, 'Downstream execution started')
        position._save({'ydental_active': False, 'ydental_reason': 'Downstream execution started'})
        task._save({'state': 'started'})
        return {'id': task.id, 'version': task.ydental_version}

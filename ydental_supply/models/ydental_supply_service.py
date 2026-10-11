import hashlib
import json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class YDentalSupplyService(models.AbstractModel):
    _name = 'ydental.supply.service'
    _description = 'Validated schedule and shared capacity transactions'

    def _now(self):
        return fields.Datetime.now()

    def _access(self, write=False):
        access = self.env['ydental.access.service']
        member = access._check('capacity', 'write' if write else 'read', write=write)
        return member.ydental_store_id

    def _lock(self):
        # Same space lock as S02. The UPDATE is essential under PostgreSQL
        # repeatable read: a stale snapshot must serialize/retry, not sell twice.
        self.env.cr.execute('SELECT pg_advisory_xact_lock(%s)', [26002])
        mutex = self.env.ref('ydental_supply.ydental_supply_mutex', raise_if_not_found=False)
        if not mutex and self.env.context.get('install_mode'):
            return
        if not mutex:
            raise UserError(self.env._('Supply serialization configuration is missing.'))
        self.env.cr.execute('UPDATE ydental_supply_mutex SET ydental_revision=ydental_revision+1 WHERE id=%s', [mutex.id])
        self.env.invalidate_all()

    def _model(self, entity):
        # entity is always a literal in this module, never a request model name.
        return self.env['ydental.supply.' + entity].sudo()

    def _get(self, entity, record_id, store):
        if type(record_id) is not int:
            raise ValidationError(self.env._('An integer record identifier is required.'))
        record = self._model(entity).browse(record_id).exists()
        if not record or record.ydental_store_id != store:
            raise AccessError(self.env._('access_denied: Select a record in the current store.'))
        return record

    def _space(self, entity, record_id, store):
        if type(record_id) is not int:
            raise ValidationError(self.env._('An integer record identifier is required.'))
        record = self.env['ydental.space.' + entity].sudo().browse(record_id).exists()
        if not record or not record.active or record.ydental_store_id != store:
            raise ValidationError(self.env._('Select an active location in this store.'))
        if entity == 'station' and (not record.ydental_enabled or not record.ydental_area_id.active):
            raise ValidationError(self.env._('Select an enabled workstation.'))
        record._space_lock()
        return record

    def _new(self, entity, store, values):
        return self._model(entity)._new(dict(values, ydental_store_id=store.id, ydental_category='capacity'))

    def _reason(self, value):
        if not isinstance(value, str) or not value.strip() or len(value) > 300:
            raise ValidationError(self.env._('A reason of 1 to 300 characters is required.'))
        return value.strip()

    def _integer(self, value, minimum=0, maximum=10000):
        if type(value) is not int or not minimum <= value <= maximum:
            raise ValidationError(self.env._('Enter an integer within the allowed range.'))
        return value

    def _interval(self, start, end):
        try:
            start, end = fields.Datetime.to_datetime(start), fields.Datetime.to_datetime(end)
        except (TypeError, ValueError) as error:
            raise ValidationError(self.env._('Use valid UTC start and end times.')) from error
        if not start or not end or start.tzinfo or end.tzinfo or end <= start or end - start > timedelta(days=7):
            raise ValidationError(self.env._('The end must follow the UTC start within seven days.'))
        return start, end

    def _date(self, store, instant=None):
        return (instant or self._now()).replace(tzinfo=timezone.utc).astimezone(ZoneInfo(store.ydental_timezone)).date()

    def _snapshot(self, slot):
        return {'total': slot.ydental_total, 'reservation': slot.ydental_reservation_free,
                'walkin': slot.ydental_walkin_free, 'unavailable': slot.ydental_unavailable,
                'version': slot.ydental_version, 'state': slot.state, 'converted': slot.ydental_converted}

    def _event(self, store, operation, reason, slot=None, claim=None, before=None, after=None):
        event = self._new('event', store, {'name': operation, 'ydental_operation': operation,
            'ydental_reason': reason, 'ydental_slot_id': slot.id if slot else False,
            'ydental_claim_id': claim.id if claim else False, 'ydental_actor_id': self.env.uid,
            'ydental_before': before or {}, 'ydental_after': after or (self._snapshot(slot) if slot else {}),
            'ydental_policy_id': slot.ydental_policy_id.id if slot else False})
        if not self.env.su:
            self.env['ydental.access.service']._audit('supply.' + operation, 'capacity', event, store.id,
                before=event.ydental_before, after=event.ydental_after, reason=reason)
        return event

    def _run(self, operation, payload, key, downstream=False):
        if not isinstance(payload, dict) or not isinstance(key, str) or not 1 <= len(key) <= 160:
            raise ValidationError(self.env._('Action arguments and an idempotency key are required.'))
        if downstream:
            store = self._check_capacity_source(operation, payload)
        else:
            store = self._access(write=True)
        fingerprint = hashlib.sha256(json.dumps([self.env.uid, operation, payload], sort_keys=True).encode()).hexdigest()
        with self.env.cr.savepoint():
            self._lock()
            receipt = self._model('operation').search([('ydental_store_id', '=', store.id), ('ydental_key', '=', key)], limit=1)
            if receipt:
                if receipt.ydental_fingerprint != fingerprint:
                    raise UserError(self.env._('version_conflict: This key belongs to another request.'))
                return dict(receipt.ydental_result, result='already_accepted')
            handlers = {'policy': self._policy, 'assign': self._assign, 'adjust': self._adjust_assignment,
                'cancel_assignment': self._cancel_assignment, 'copy': self._copy_week, 'batch': self._batch,
                'slot': self._slot, 'publish': self._publish, 'resize': self._resize, 'extend': self._extend,
                'convert': self._convert, 'business': self._business, 'resolve': self._resolve,
                'acquire': self._acquire, 'cancel': self._cancel, 'consume': self._consume,
                'reschedule': self._reschedule, 'reassign': self._reassign}
            if operation not in handlers or (operation in ('acquire', 'cancel', 'consume', 'reschedule', 'reassign')) != downstream:
                raise AccessError(self.env._('access_denied: Unknown supply action.'))
            result = dict(handlers[operation](store, payload), result='accepted')
            self._new('operation', store, {'name': operation, 'ydental_key': key,
                'ydental_fingerprint': fingerprint, 'ydental_result': result})
            return result

    def _operate(self, operation, payload, key):
        return self._run(operation, payload, key)

    def _capacity_action(self, operation, payload, key):
        """S05/S06 server adapter must authorize an actual fixed source first."""
        return self._run(operation, payload, key, downstream=True)

    def _check_capacity_source(self, operation, payload):
        raise AccessError(self.env._('access_denied: Capacity source integration is not connected.'))

    def _keys(self, payload, required, optional=()):
        if set(payload) - set(required) - set(optional) or not set(required) <= set(payload):
            raise ValidationError(self.env._('Unknown or missing action arguments.'))

    def _policy(self, store, p):
        self._keys(p, ('name', 'rounding', 'phone_pool', 'cutoff_minutes', 'reason', 'mode'),
                   ('station_id', 'area_id', 'reservation_weight', 'walkin_weight', 'approved'))
        if p['mode'] not in ('demo', 'published') or p['mode'] == 'published' and p.get('approved') is not True:
            raise ValidationError(self.env._('Formal publication requires explicit approval.'))
        if p['rounding'] not in ('floor', 'nearest') or p['phone_pool'] not in ('reservation', 'walkin'):
            raise ValidationError(self.env._('Select a supported rounding and telephone pool strategy.'))
        station = self._space('station', p['station_id'], store) if p.get('station_id') else False
        area = self._space('area', p['area_id'], store) if p.get('area_id') else False
        if station and area:
            raise ValidationError(self.env._('Choose a store, area or workstation policy scope.'))
        record = self._new('policy', store, {'name': self._reason(p['name']), 'ydental_mode': p['mode'],
            'ydental_rounding': p['rounding'], 'ydental_phone_pool': p['phone_pool'],
            'ydental_cutoff_minutes': self._integer(p['cutoff_minutes'], maximum=1440),
            'ydental_reservation_weight': self._integer(p.get('reservation_weight', 1), 1, 100),
            'ydental_walkin_weight': self._integer(p.get('walkin_weight', 2), 1, 100),
            'ydental_station_id': station.id if station else False, 'ydental_area_id': area.id if area else False,
            'ydental_reason': self._reason(p['reason'])})
        self._event(store, 'policy', p['reason'], after={'policy_id': record.id, 'mode': record.ydental_mode})
        return {'id': record.id, 'preview': [{'quantity': q, 'reservation': record._split(q)[0],
            'walkin': record._split(q)[1], 'zero_reservation_warning': record._split(q)[0] == 0} for q in (1, 2, 3, 6)]}

    def _select_policy(self, store, station):
        policies = self._model('policy').search([('ydental_store_id', '=', store.id)])
        ancestors = station.ydental_area_id
        parent = ancestors.parent_id
        while parent:
            ancestors |= parent
            parent = parent.parent_id
        for policy in policies.filtered(lambda r: r.ydental_station_id == station):
            return policy
        nearest_areas = []
        current_area = station.ydental_area_id
        while current_area:
            nearest_areas.append(current_area)
            current_area = current_area.parent_id
        for area in nearest_areas:
            match = policies.filtered(lambda r: not r.ydental_station_id and r.ydental_area_id == area)
            if match:
                return match[:1]
        match = policies.filtered(lambda r: not r.ydental_station_id and not r.ydental_area_id)
        if not match:
            raise UserError(self.env._('Configure an explicit demonstration or approved supply policy first.'))
        return match[:1]

    def _leaves(self, user, start, end):
        resources = self.env['hr.employee'].sudo().with_context(active_test=False).search([('user_id', '=', user.id)]).resource_id
        return self.env['resource.calendar.leaves'].sudo().search([
            ('count_as', '=', 'absence'), ('date_from', '<', end), ('date_to', '>', start),
        ]).filtered(lambda r: r.resource_id in resources or not r.resource_id and (
            r.calendar_id in resources.calendar_id or not r.calendar_id and r.company_id in resources.company_id))

    def _assignment_warning(self, record):
        if record.state != 'active':
            return ''
        if record.ydental_station_id and (not record.ydental_station_id.active or not record.ydental_station_id.ydental_enabled):
            return self.env._('Workstation unavailable. Review the arrangement.')
        if self._leaves(record.ydental_user_id, record.ydental_start, record.ydental_end):
            return self.env._('Time off conflicts with this assignment. Replacement is required.')
        if record.ydental_station_id and not set(record.ydental_station_id.ydental_capability_ids.ids) <= set(record.ydental_user_id.ydental_capability_ids.ids):
            return self.env._('Staff capabilities do not cover the workstation. Draft may be saved; verify supply separately.')
        return ''

    def _assignment_values(self, store, p, excluding=None):
        self._keys(p, ('user_id', 'start', 'end'), ('station_id', 'area_id', 'reason'))
        self._integer(p['user_id'], 1, 2147483647)
        member = self.env['ydental.access.service']._membership(p['user_id'], store.id)
        if not member or not member.ydental_employee_id.active or not member.ydental_user_id.active:
            raise ValidationError(self.env._('Select an active employee qualified for this store.'))
        start, end = self._interval(p['start'], p['end'])
        station = self._space('station', p['station_id'], store) if p.get('station_id') else False
        area = self._space('area', p['area_id'], store) if p.get('area_id') else False
        if bool(station) == bool(area):
            raise ValidationError(self.env._('Select either a workstation or an area.'))
        conflicts = self._model('assignment').search([('state', '=', 'active'), ('ydental_start', '<', end), ('ydental_end', '>', start)])
        if excluding:
            conflicts -= excluding
        if conflicts.filtered(lambda r: r.ydental_user_id == member.ydental_user_id or station and r.ydental_station_id == station):
            raise UserError(self.env._('version_conflict: The account or workstation already has an overlapping assignment.'))
        if self._leaves(member.ydental_user_id, start, end):
            raise UserError(self.env._('Time off prevents a new effective assignment.'))
        return {'name': member.ydental_user_id.name, 'ydental_user_id': member.ydental_user_id.id,
            'ydental_employee_id': member.ydental_employee_id.id, 'ydental_start': start, 'ydental_end': end,
            'ydental_station_id': station.id if station else False, 'ydental_area_id': area.id if area else False,
            'ydental_reason': self._reason(p.get('reason', 'Default assignment'))}

    def _assign(self, store, p):
        record = self._new('assignment', store, self._assignment_values(store, p))
        self._event(store, 'assign', record.ydental_reason, after={'assignment_id': record.id})
        return {'id': record.id, 'warning': self._assignment_warning(record)}

    def _version(self, record, version):
        if type(version) is not int or record.ydental_version != version:
            raise UserError(self.env._('version_conflict: Reload the changed record.'))

    def _adjust_assignment(self, store, p):
        self._keys(p, ('id', 'version', 'values', 'reason'))
        record = self._get('assignment', p['id'], store)
        self._version(record, p['version'])
        if record.state != 'active' or record.ydental_start <= self._now():
            raise UserError(self.env._('Only future effective assignments can be adjusted.'))
        old_slots = self._affected_slots(record)
        record._save(self._assignment_values(store, p['values'], excluding=record))
        self._suspend_affected(store, old_slots | self._affected_slots(record), self._reason(p['reason']), assignment=record)
        self._event(store, 'adjust', p['reason'], after={'assignment_id': record.id})
        return {'id': record.id}

    def _cancel_assignment(self, store, p):
        self._keys(p, ('id', 'version', 'reason'))
        record = self._get('assignment', p['id'], store)
        self._version(record, p['version'])
        reason = self._reason(p['reason'])
        record._save({'state': 'cancelled', 'ydental_reason': reason})
        self._suspend_affected(store, self._affected_slots(record), reason, assignment=record)
        self._event(store, 'cancel_assignment', reason, after={'assignment_id': record.id})
        return {'id': record.id}

    def _batch(self, store, p):
        self._keys(p, ('rows',))
        if not isinstance(p['rows'], list) or not 1 <= len(p['rows']) <= 50:
            raise ValidationError(self.env._('A batch needs 1 to 50 assignment rows.'))
        return {'ids': [self._assign(store, row)['id'] for row in p['rows']]}

    def _copy_week(self, store, p):
        self._keys(p, ('week_start',))
        start = fields.Date.to_date(p['week_start'])
        local = datetime.combine(start, datetime.min.time(), tzinfo=ZoneInfo(store.ydental_timezone))
        utc = local.astimezone(timezone.utc).replace(tzinfo=None)
        previous = self._model('assignment').search([('ydental_store_id', '=', store.id), ('state', '=', 'active'),
            ('ydental_start', '>=', utc - timedelta(days=7)), ('ydental_start', '<', utc)], limit=51)
        if not previous or len(previous) > 50:
            raise ValidationError(self.env._('Copy requires 1 to 50 source assignments.'))
        rows = [{'user_id': r.ydental_user_id.id, 'station_id': r.ydental_station_id.id,
                 'area_id': r.ydental_area_id.id, 'start': fields.Datetime.to_string((r.ydental_start.replace(tzinfo=timezone.utc).astimezone(ZoneInfo(store.ydental_timezone)) + timedelta(days=7)).astimezone(timezone.utc).replace(tzinfo=None)),
                 'end': fields.Datetime.to_string((r.ydental_end.replace(tzinfo=timezone.utc).astimezone(ZoneInfo(store.ydental_timezone)) + timedelta(days=7)).astimezone(timezone.utc).replace(tzinfo=None)), 'reason': 'Copy previous week'} for r in previous]
        return self._batch(store, {'rows': rows})

    def _slot(self, store, p):
        self._keys(p, ('station_id', 'start', 'end', 'total', 'capability_ids', 'reason'))
        station = self._space('station', p['station_id'], store)
        area = station.ydental_queue_area_id
        if not area or not station.ydental_callable:
            raise ValidationError(self.env._('A reporting area is required for supply.'))
        start, end = self._interval(p['start'], p['end'])
        if self._date(store, start) != self._date(store, end - timedelta(microseconds=1)):
            raise ValidationError(self.env._('A capacity slot must stay within one local business day.'))
        if self._model('slot').search_count([('ydental_station_id', '=', station.id), ('ydental_start', '<', end), ('ydental_end', '>', start)]):
            raise UserError(self.env._('version_conflict: Workstation capacity slots cannot overlap.'))
        ids = p['capability_ids']
        if not isinstance(ids, list) or not ids or any(type(i) is not int for i in ids):
            raise ValidationError(self.env._('Choose active workstation capabilities.'))
        capabilities = self.env['ydental.access.capability'].sudo().browse(ids).exists()
        if len(capabilities) != len(set(ids)) or not all(capabilities.mapped('active')) or not set(ids) <= set(station.ydental_capability_ids.ids):
            raise ValidationError(self.env._('Choose active workstation capabilities.'))
        policy = self._select_policy(store, station)
        total = self._integer(p['total'], 1)
        reservation, walkin = policy._split(total)
        record = self._new('slot', store, {'name': station.name, 'ydental_station_id': station.id,
            'ydental_area_id': area.id, 'ydental_start': start, 'ydental_end': end,
            'ydental_total': total, 'ydental_reservation_free': reservation, 'ydental_walkin_free': walkin,
            'ydental_capability_ids': [fields.Command.set(ids)], 'ydental_policy_id': policy.id,
            'ydental_reason': self._reason(p['reason'])})
        self._event(store, 'slot', p['reason'], slot=record)
        return {'id': record.id, 'zero_reservation_warning': reservation == 0, 'policy_id': policy.id}

    def _coverage(self, slot, user_ids):
        if not isinstance(user_ids, list) or not user_ids or len(user_ids) > 50 or any(type(i) is not int for i in user_ids):
            raise ValidationError(self.env._('Record actual capability coverage before publication.'))
        users = self.env['res.users'].sudo().browse(user_ids).exists()
        if len(users) != len(set(user_ids)):
            raise ValidationError(self.env._('Record actual capability coverage before publication.'))
        covered = set()
        for user in users:
            member = self.env['ydental.access.service']._membership(user.id, slot.ydental_store_id.id)
            if not user.active or not member or not member.ydental_employee_id.active or self._leaves(user, slot.ydental_start, slot.ydental_end):
                raise UserError(self.env._('Coverage requires active store staff without time off.'))
            covered.update(user.ydental_capability_ids.filtered('active').ids)
        if not set(slot.ydental_capability_ids.ids) <= covered:
            raise UserError(self.env._('Unverified capabilities cannot be published as guaranteed supply.'))
        return {'user_ids': user_ids, 'capability_ids': sorted(covered), 'checked_by': self.env.uid,
                'checked_at': fields.Datetime.to_string(self._now())}

    def _publish(self, store, p):
        self._keys(p, ('id', 'version', 'user_ids', 'reason'))
        slot = self._get('slot', p['id'], store)
        self._version(slot, p['version'])
        self._space('station', slot.ydental_station_id.id, store)
        if not set(slot.ydental_capability_ids.ids) <= set(slot.ydental_station_id.ydental_capability_ids.filtered('active').ids):
            raise UserError(self.env._('Workstation capabilities no longer cover this slot.'))
        coverage = self._coverage(slot, p['user_ids'])
        before = self._snapshot(slot)
        slot._save({'state': 'published', 'ydental_coverage': coverage, 'ydental_reason': self._reason(p['reason'])})
        self._event(store, 'publish', p['reason'], slot=slot, before=before)
        return {'id': slot.id}

    def _coverage_valid(self, slot):
        if not slot.ydental_station_id.active or not slot.ydental_station_id.ydental_enabled or not slot.ydental_station_id.ydental_callable or not all(slot.with_context(active_test=False).ydental_capability_ids.mapped('active')):
            return False
        if not set(slot.ydental_capability_ids.ids) <= set(slot.ydental_station_id.ydental_capability_ids.filtered('active').ids):
            return False
        try:
            self._coverage(slot, (slot.ydental_coverage or {}).get('user_ids', []))
        except (UserError, ValidationError):
            return False
        return slot.ydental_station_id.ydental_queue_area_id == slot.ydental_area_id

    def _resize(self, store, p):
        self._keys(p, ('id', 'version', 'total', 'reason'))
        slot = self._get('slot', p['id'], store)
        self._version(slot, p['version'])
        total = self._integer(p['total'])
        before = self._snapshot(slot)
        delta = total - slot.ydental_total
        reservation, walkin, unavailable = slot.ydental_reservation_free, slot.ydental_walkin_free, slot.ydental_unavailable
        if delta < 0:
            if -delta > reservation + walkin + unavailable:
                raise UserError(self.env._('insufficient_balance: Reduction would remove used capacity.'))
            take = min(walkin, -delta)
            walkin -= take
            take_reservation = min(reservation, -delta - take)
            reservation -= take_reservation
            unavailable -= -delta - take - take_reservation
        else:
            add_r, add_w = slot.ydental_policy_id._split(delta)
            if slot.ydental_converted or self._now() >= slot.ydental_start:
                add_w += add_r
                add_r = 0
            reservation += add_r
            walkin += add_w
        slot._save({'ydental_total': total, 'ydental_reservation_free': reservation,
                    'ydental_walkin_free': walkin, 'ydental_unavailable': unavailable, 'ydental_reason': self._reason(p['reason'])})
        self._event(store, 'resize', p['reason'], slot=slot, before=before)
        return {'id': slot.id}

    def _extend(self, store, p):
        self._keys(p, ('id', 'version', 'end', 'reason'))
        slot = self._get('slot', p['id'], store)
        self._version(slot, p['version'])
        _, end = self._interval(slot.ydental_start, p['end'])
        if end <= slot.ydental_end or self._date(store, end - timedelta(microseconds=1)) != self._date(store, slot.ydental_start):
            raise ValidationError(self.env._('Extend within the original local business day.'))
        if self._model('slot').search_count([('id', '!=', slot.id), ('ydental_station_id', '=', slot.ydental_station_id.id),
            ('ydental_start', '<', end), ('ydental_end', '>', slot.ydental_start)]):
            raise UserError(self.env._('version_conflict: Extension overlaps another slot.'))
        before = self._snapshot(slot)
        slot._save({'ydental_end': end, 'state': 'suspended', 'ydental_reason': self._reason(p['reason'])})
        self._event(store, 'extend', p['reason'], slot=slot, before=before, after=dict(self._snapshot(slot), end=fields.Datetime.to_string(end)))
        return {'id': slot.id}

    def _convert_slot(self, store, slot):
        if slot.ydental_converted:
            return
        if not slot.ydental_start <= self._now() < slot.ydental_end:
            raise UserError(self.env._('Conversion requires a current, unexpired slot.'))
        before = self._snapshot(slot)
        slot._save({'ydental_converted': True, 'ydental_reservation_free': 0,
                    'ydental_walkin_free': slot.ydental_walkin_free + slot.ydental_reservation_free})
        self._event(store, 'convert', 'Unused reservation balance converted once', slot=slot, before=before)

    def _convert(self, store, p):
        self._keys(p, ('id',))
        slot = self._get('slot', p['id'], store)
        self._convert_slot(store, slot)
        return {'id': slot.id}

    def _business_record(self, store, area_id, instant=None):
        return self._model('business').search([('ydental_store_id', '=', store.id), ('ydental_area_id', '=', area_id),
            ('ydental_date', '=', self._date(store, instant))], limit=1)

    def _check_queue_empty(self, business):
        # S06 must override and check waiting/calling under this same mutex.
        raise UserError(self.env._('Queue integration is not connected. Ordinary calling cannot be stopped.'))

    def _business(self, store, p):
        self._keys(p, ('area_id', 'state', 'reason'), ('version',))
        area = self._space('area', p['area_id'], store)
        if not area.ydental_reporting or p['state'] not in ('open', 'draining', 'closed'):
            raise ValidationError(self.env._('Select a reporting area and a valid business state.'))
        reason = self._reason(p['reason'])
        record = self._business_record(store, area.id)
        if not record:
            if p['state'] != 'open':
                raise UserError(self.env._('Explicitly open the local business day first.'))
            record = self._new('business', store, {'name': area.name, 'ydental_area_id': area.id,
                'ydental_date': self._date(store), 'ydental_timezone': store.ydental_timezone, 'state': 'open', 'ydental_reason': reason})
        else:
            self._version(record, p.get('version'))
            if p['state'] == 'closed':
                if record.state != 'draining':
                    raise UserError(self.env._('Stop ordinary reporting before ordinary calling.'))
                self._check_queue_empty(record)
            record._save({'state': p['state'], 'ydental_reason': reason})
        self._event(store, 'business', reason, after={'id': record.id, 'state': record.state,
            'date': fields.Date.to_string(record.ydental_date), 'version': record.ydental_version})
        return {'id': record.id, 'version': record.ydental_version}

    def _saleable(self, store, slot, pool):
        now = self._now()
        business = self._business_record(store, slot.ydental_area_id.id, slot.ydental_start)
        if slot.state != 'published' or not self._coverage_valid(slot) or now >= slot.ydental_end:
            return False
        if business and business.state != 'open':
            return False
        # Today's supply requires an explicit local-day opening. Future published
        # reservation supply can be offered before that business day opens.
        if self._date(store, slot.ydental_start) <= self._date(store) and not business:
            return False
        if pool == 'reservation' and (slot.ydental_converted or now >= slot.ydental_start - timedelta(minutes=slot.ydental_policy_id.ydental_cutoff_minutes)):
            return False
        return True

    def _acquire(self, store, p):
        self._keys(p, ('area_id', 'capability_id', 'start', 'end', 'channel', 'source', 'source_key'), ('slot_id',))
        if p['channel'] not in ('reservation', 'walkin', 'phone'):
            raise ValidationError(self.env._('Unknown capacity channel.'))
        source, source_key = self._reason(p['source']), self._reason(p['source_key'])
        previous = self._model('claim').search([('ydental_store_id', '=', store.id), ('ydental_source', '=', source), ('ydental_source_key', '=', source_key)], limit=1)
        if previous:
            raise UserError(self.env._('version_conflict: This source already has a capacity entitlement.'))
        start, end = self._interval(p['start'], p['end'])
        candidates = self._model('slot').search([('ydental_store_id', '=', store.id), ('ydental_area_id', '=', p['area_id']),
            ('ydental_start', '=', start), ('ydental_end', '=', end), ('state', '=', 'published')])
        if p.get('slot_id'):
            candidates = candidates.filtered(lambda r: r.id == p['slot_id'])
        candidates = candidates.sorted(lambda r: (len(r.ydental_capability_ids), r.ydental_station_id.id, r.id))
        for slot in candidates:
            pool = slot.ydental_policy_id.ydental_phone_pool if p['channel'] == 'phone' else p['channel']
            if slot.ydental_start <= self._now() < slot.ydental_end and not slot.ydental_converted:
                self._convert_slot(store, slot)
            field = 'ydental_reservation_free' if pool == 'reservation' else 'ydental_walkin_free'
            if p['capability_id'] not in slot.ydental_capability_ids.ids or not self._saleable(store, slot, pool) or slot[field] <= 0:
                continue
            before = self._snapshot(slot)
            slot._save({field: slot[field] - 1})
            claim = self._new('claim', store, {'name': source_key, 'ydental_slot_id': slot.id,
                'ydental_capability_id': p['capability_id'], 'ydental_pool': pool,
                'ydental_source': source, 'ydental_source_key': source_key})
            self._event(store, 'acquire', 'Source capacity entitlement', slot=slot, claim=claim, before=before)
            return {'id': claim.id, 'slot_id': slot.id}
        raise UserError(self.env._('insufficient_balance: No eligible shared capacity remains.'))

    def _cancel_claim(self, store, claim, reason):
        if claim.state == 'cancelled':
            return
        if claim.state != 'held':
            raise UserError(self.env._('Consumed capacity cannot be returned.'))
        slot = claim.ydental_slot_id
        before = self._snapshot(slot)
        now = self._now()
        business = self._business_record(store, slot.ydental_area_id.id, slot.ydental_start)
        if now >= slot.ydental_end or slot.state != 'published' or business and business.state != 'open':
            field = 'ydental_unavailable'
        elif now >= slot.ydental_start:
            field = 'ydental_walkin_free'
        else:
            field = 'ydental_reservation_free' if claim.ydental_pool == 'reservation' else 'ydental_walkin_free'
        slot._save({field: slot[field] + 1})
        claim._save({'state': 'cancelled'})
        self._event(store, 'cancel', reason, slot=slot, claim=claim, before=before)

    def _cancel(self, store, p):
        self._keys(p, ('id', 'reason'))
        claim = self._get('claim', p['id'], store)
        self._cancel_claim(store, claim, self._reason(p['reason']))
        return {'id': claim.id, 'state': claim.state}

    def _consume(self, store, p):
        self._keys(p, ('id',))
        claim = self._get('claim', p['id'], store)
        if claim.state == 'cancelled':
            raise UserError(self.env._('Cancelled capacity cannot start execution.'))
        if claim.state == 'held':
            claim._save({'state': 'consumed'})
            self._event(store, 'consume', 'Authorized source execution started', slot=claim.ydental_slot_id, claim=claim)
        return {'id': claim.id, 'state': claim.state}

    def _reschedule(self, store, p):
        self._keys(p, ('id', 'target', 'reason'))
        old = self._get('claim', p['id'], store)
        if old.state != 'held':
            raise UserError(self.env._('Only an unused entitlement can be rescheduled.'))
        target = dict(p['target'])
        if target.get('source') != old.ydental_source or target.get('source_key') == old.ydental_source_key:
            raise ValidationError(self.env._('Rescheduling requires a new revision key on the same source.'))
        new = self._acquire(store, target)
        self._cancel_claim(store, old, self._reason(p['reason']))
        self._event(store, 'reschedule', p['reason'], claim=old, after={'old_id': old.id, 'new_id': new['id']})
        return new

    def _reassign(self, store, p):
        self._keys(p, ('id', 'slot_id', 'reason'))
        claim = self._get('claim', p['id'], store)
        target = self._get('slot', p['slot_id'], store)
        old = claim.ydental_slot_id
        if claim.state != 'held' or (old.ydental_area_id, old.ydental_start, old.ydental_end) != (target.ydental_area_id, target.ydental_start, target.ydental_end):
            raise UserError(self.env._('Reassignment requires an unused entitlement in the same area and time.'))
        if old == target:
            return {'id': claim.id, 'slot_id': target.id}
        field = 'ydental_reservation_free' if claim.ydental_pool == 'reservation' else 'ydental_walkin_free'
        if not self._saleable(store, target, claim.ydental_pool) or claim.ydental_capability_id not in target.ydental_capability_ids or target[field] <= 0:
            raise UserError(self.env._('insufficient_balance: Target capacity is unavailable.'))
        old_before, target_before = self._snapshot(old), self._snapshot(target)
        target._save({field: target[field] - 1})
        # A move preserves the original pool only before cutoff. After slot start
        # reservation sources cannot be moved into an already converted pool.
        old_field = field if old.state == 'published' else 'ydental_unavailable'
        old._save({old_field: old[old_field] + 1})
        claim._save({'ydental_slot_id': target.id})
        reason = self._reason(p['reason'])
        self._event(store, 'reassign_out', reason, slot=old, claim=claim, before=old_before)
        self._event(store, 'reassign_in', reason, slot=target, claim=claim, before=target_before)
        return {'id': claim.id, 'slot_id': target.id}

    def _affected_slots(self, assignment):
        slots = self._model('slot').search([('ydental_store_id', '=', assignment.ydental_store_id.id),
            ('ydental_start', '<', assignment.ydental_end), ('ydental_end', '>', assignment.ydental_start),
            ('ydental_end', '>', self._now())])
        return slots.filtered(lambda r: r.ydental_station_id == assignment.ydental_station_id or
            assignment.ydental_user_id.id in (r.ydental_coverage or {}).get('user_ids', []))

    def _suspend_affected(self, store, slots, reason, assignment=None):
        for slot in slots:
            if not self._coverage_valid(slot) and slot.state == 'published':
                slot._save({'state': 'suspended', 'ydental_reason': reason})
                self._new('disposition', store, {'name': slot.name, 'ydental_slot_id': slot.id,
                    'ydental_assignment_id': assignment.id if assignment else False, 'ydental_reason': reason})
                self._event(store, 'suspend', reason, slot=slot)

    def _membership_removed(self, membership):
        # S01 has authorized and serialized the lifecycle operation already.
        self._lock()
        store = membership.ydental_store_id
        assignments = self._model('assignment').search([('ydental_store_id', '=', store.id),
            ('ydental_user_id', '=', membership.ydental_user_id.id), ('state', '=', 'active'),
            ('ydental_start', '>', self._now())])
        for assignment in assignments:
            assignment._save({'state': 'cancelled', 'ydental_reason': 'Store membership removed'})
            self._new('disposition', store, {'name': assignment.name, 'ydental_assignment_id': assignment.id,
                'ydental_reason': 'Store membership removed; review replacement, migration and contact'})
            self._event(store, 'employment_cancel', 'Store membership removed', after={'assignment_id': assignment.id})
        slots = self._model('slot').search([('ydental_store_id', '=', store.id), ('ydental_end', '>', self._now())])
        self._suspend_affected(store, slots, 'Store membership removed')

    def _resolve(self, store, p):
        self._keys(p, ('entity', 'id', 'version', 'reason'))
        if p['entity'] not in ('feedback', 'disposition'):
            raise ValidationError(self.env._('Select a feedback or future handling work item.'))
        record = self._get(p['entity'], p['id'], store)
        self._version(record, p['version'])
        record._save({'state': 'resolved', 'ydental_resolution': self._reason(p['reason'])})
        self._event(store, 'resolve', p['reason'], after={'entity': p['entity'], 'id': record.id})
        return {'id': record.id}

    def _feedback(self, assignment_id, reason, key):
        access = self.env['ydental.access.service']
        access._require_internal()
        session = access._scope(write=True)
        member = access._membership(self.env.uid, session.ydental_store_id.id)
        if not member or not member.ydental_employee_id.active:
            raise AccessError(self.env._('access_denied: Active membership is required.'))
        with self.env.cr.savepoint():
            self._lock()
            assignment = self._get('assignment', assignment_id, session.ydental_store_id)
            if assignment.ydental_user_id.id != self.env.uid:
                raise AccessError(self.env._('access_denied: Report only your own arrangement.'))
            reason = self._reason(reason)
            if not isinstance(key, str) or not 1 <= len(key) <= 160:
                raise ValidationError(self.env._('An idempotency key is required.'))
            old = self._model('feedback').search([('ydental_assignment_id', '=', assignment.id),
                ('ydental_user_id', '=', self.env.uid), ('state', '=', 'pending')], limit=1)
            if old:
                return {'id': old.id, 'result': 'already_accepted'}
            recipients = self._recipients(session.ydental_store_id)
            record = self._new('feedback', session.ydental_store_id, {'name': assignment.name,
                'ydental_assignment_id': assignment.id, 'ydental_user_id': self.env.uid,
                'ydental_recipient_ids': [fields.Command.set(recipients.ids)], 'ydental_reason': reason})
            self._event(session.ydental_store_id, 'feedback', reason, after={'id': record.id, 'recipient_ids': recipients.ids})
            return {'id': record.id, 'result': 'accepted', 'manager_required': not bool(recipients)}

    def _recipients(self, store):
        access = self.env['ydental.access.service']
        members = self.env['ydental.access.membership'].sudo().search([('ydental_store_id', '=', store.id), ('active', '=', True)])
        return members.filtered(lambda m: m.ydental_user_id.active and m.ydental_employee_id.active and
            access._levels(m)['capacity'] == 'write').ydental_user_id

    def _own_assignments(self):
        self.env['ydental.access.service']._require_internal()
        records = self._model('assignment').search([('ydental_user_id', '=', self.env.uid), ('state', '=', 'active'),
            ('ydental_start', '<', self._now() + timedelta(days=2)), ('ydental_end', '>', self._now() - timedelta(days=2))])
        return records.filtered(lambda r: r.ydental_store_id.active and
            self.env['ydental.access.service']._membership(self.env.uid, r.ydental_store_id.id) and
            self.env['ydental.access.service']._membership(self.env.uid, r.ydental_store_id.id).ydental_employee_id.active and
            self._date(r.ydental_store_id, r.ydental_start) <= self._date(r.ydental_store_id) <= self._date(r.ydental_store_id, r.ydental_end - timedelta(microseconds=1)))

    def _default_candidates(self):
        now = self._now()
        assignments = self._own_assignments().filtered(lambda r: r.ydental_end > now)
        current = assignments.filtered(lambda r: r.ydental_start <= now)
        if current:
            return current.ydental_store_id.ids
        if assignments:
            earliest = min(assignments.mapped('ydental_start'))
            return assignments.filtered(lambda r: r.ydental_start == earliest).ydental_store_id.ids
        return []

    def _workbench_suggestion(self, assignment_id):
        assignment = self._own_assignments().filtered(lambda r: r.id == assignment_id)
        if not assignment:
            raise AccessError(self.env._('access_denied: Select your effective arrangement today.'))
        stations = assignment.ydental_station_id or self.env['ydental.space.station'].sudo().search([
            ('ydental_store_id', '=', assignment.ydental_store_id.id), ('ydental_area_id', 'child_of', assignment.ydental_area_id.id),
            ('ydental_enabled', '=', True)])
        capabilities = set(self.env.user.sudo().ydental_capability_ids.filtered('active').ids)
        stations = stations.filtered(lambda r: r.active and r.ydental_enabled and
            bool(set(r.ydental_capability_ids.filtered('active').ids) & capabilities))
        return {'result': 'hint_only', 'station_ids': stations.ids, 'execution': 'not_connected',
                'message': self.env._('Workstation suggestion only. Execution entry awaits the S06 connection.')}

    def _dashboard(self, week_start=None, group_by='station'):
        store = self._access()
        access = self.env['ydental.access.service']
        week = fields.Date.to_date(week_start) if week_start else self._date(store)
        week -= timedelta(days=week.weekday())
        start = datetime.combine(week, datetime.min.time(), tzinfo=ZoneInfo(store.ydental_timezone)).astimezone(timezone.utc).replace(tzinfo=None)
        assignments = self._model('assignment').search([('ydental_store_id', '=', store.id),
            ('ydental_start', '>=', start), ('ydental_start', '<', start + timedelta(days=7))])
        members = self.env['ydental.access.membership'].sudo().search([('ydental_store_id', '=', store.id), ('active', '=', True)])
        areas = self.env['ydental.space.area'].sudo().search([('ydental_store_id', '=', store.id)])
        stations = self.env['ydental.space.station'].sudo().search([('ydental_store_id', '=', store.id), ('ydental_enabled', '=', True)])
        slots = self._model('slot').search([('ydental_store_id', '=', store.id)], limit=100, order='ydental_start desc, id desc')
        return {'store': store, 'revision': access._scope().ydental_revision,
            'can_write': access._levels(access._membership(self.env.uid, store.id))['capacity'] == 'write',
            'week': week, 'previous_week': week - timedelta(days=7), 'next_week': week + timedelta(days=7),
            'group_by': group_by if group_by in ('station', 'person') else 'station',
            'assignments': assignments, 'members': members, 'stations': stations, 'areas': areas,
            'capabilities': stations.ydental_capability_ids.filtered('active'), 'slots': slots,
            'area_summaries': [{'area': rows[0].ydental_area_id.name, 'start': rows[0].ydental_start,
                'end': rows[0].ydental_end, 'total': sum(rows.mapped('ydental_total')),
                'reservation': sum(rows.mapped('ydental_reservation_free')), 'walkin': sum(rows.mapped('ydental_walkin_free'))}
                for rows in slots.grouped(lambda r: (r.ydental_area_id.id, r.ydental_start, r.ydental_end)).values()],
            'policies': self._model('policy').search([('ydental_store_id', '=', store.id)]),
            'feedback': self._model('feedback').search([('ydental_store_id', '=', store.id)], limit=100),
            'dispositions': self._model('disposition').search([('ydental_store_id', '=', store.id)], limit=100),
            'businesses': self._model('business').search([('ydental_store_id', '=', store.id), ('ydental_date', '=', self._date(store))]),
            'events': self._model('event').search([('ydental_store_id', '=', store.id)], limit=100, order='id desc'),
            'format_time': lambda value: value.replace(tzinfo=timezone.utc).astimezone(ZoneInfo(store.ydental_timezone)).strftime('%Y-%m-%d %H:%M'),
            'replacement_candidates': lambda record: self._replacement_candidates(record),
            'groups': assignments.grouped('ydental_user_id' if group_by == 'person' else 'ydental_station_id'),
            'totals': {'shared': sum(slots.mapped('ydental_total')), 'reservation': sum(slots.mapped('ydental_reservation_free')),
                       'walkin': sum(slots.mapped('ydental_walkin_free'))}}

    def _today(self):
        access = self.env['ydental.access.service']
        access._require_internal()
        session = access._scope()
        records = self._own_assignments()
        members = self.env['ydental.access.membership'].sudo().search([('ydental_user_id', '=', self.env.uid), ('active', '=', True)])
        return {'assignments': records, 'revision': session.ydental_revision, 'selected_store_id': session.ydental_store_id.id,
            'candidate_ids': self._default_candidates(), 'stores': members.filtered(lambda m: m.ydental_employee_id.active and m.ydental_store_id.active).ydental_store_id,
            'execution_store_id': access._get_execution_store_id(),
            'format_time': lambda record, value: value.replace(tzinfo=timezone.utc).astimezone(ZoneInfo(record.ydental_store_id.ydental_timezone)).strftime('%Y-%m-%d %H:%M')}


    def _availability(self, area_id, capability_id, start, end, channel):
        store = self._access()
        start, end = self._interval(start, end)
        if channel not in ('reservation', 'walkin', 'phone'):
            raise ValidationError(self.env._('Unknown capacity channel.'))
        slots = self._model('slot').search([('ydental_store_id', '=', store.id), ('ydental_area_id', '=', area_id),
            ('ydental_start', '=', start), ('ydental_end', '=', end)])
        eligible = slots.filtered(lambda r: capability_id in r.ydental_capability_ids.ids)
        def free(slot):
            pool = slot.ydental_policy_id.ydental_phone_pool if channel == 'phone' else channel
            if not self._saleable(store, slot, pool):
                return 0
            value = slot.ydental_reservation_free if pool == 'reservation' else slot.ydental_walkin_free
            if pool == 'walkin' and self._now() >= slot.ydental_start and not slot.ydental_converted:
                value += slot.ydental_reservation_free
            return value
        return {'result': 'hint_only', 'shared_total': sum(slots.mapped('ydental_total')),
                'shared_free': sum(free(slot) for slot in slots), 'capability_free': sum(free(slot) for slot in eligible),
                'additive_capabilities': False}

    def _replacement_candidates(self, assignment):
        store = assignment.ydental_store_id
        members = self.env['ydental.access.membership'].sudo().search([('ydental_store_id', '=', store.id), ('active', '=', True)])
        conflicts = self._model('assignment').search([('state', '=', 'active'), ('id', '!=', assignment.id),
            ('ydental_start', '<', assignment.ydental_end), ('ydental_end', '>', assignment.ydental_start)])
        required = set(assignment.ydental_station_id.ydental_capability_ids.filtered('active').ids)
        return members.filtered(lambda m: m.ydental_user_id.active and m.ydental_employee_id.active and
            m.ydental_user_id.id != assignment.ydental_user_id.id and m.ydental_user_id not in conflicts.ydental_user_id and
            required <= set(m.ydental_user_id.ydental_capability_ids.filtered('active').ids) and
            not self._leaves(m.ydental_user_id, assignment.ydental_start, assignment.ydental_end)).ydental_user_id

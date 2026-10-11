from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase

from .common import acquire, acquire_args, bind, setup_supply, slot


NOW = 'odoo.addons.ydental_supply.models.ydental_supply_service.fields.Datetime.now'


class TestSupply(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup_supply(cls)

    def assert_balance(self, record):
        claims = self.root['ydental.supply.claim'].search([('ydental_slot_id', '=', record.id), ('state', 'in', ['held', 'consumed'])])
        self.assertEqual(record.ydental_total, record.ydental_reservation_free + record.ydental_walkin_free + record.ydental_unavailable + len(claims))

    def test_t01_integer_preview_and_policy_versions(self):
        self.assertEqual([(r['reservation'], r['walkin']) for r in self.policy['preview']], [(0, 1), (0, 2), (1, 2), (2, 4)])
        self.assertTrue(self.policy['preview'][0]['zero_reservation_warning'])
        record = slot(self)
        old_policy = record.ydental_policy_id
        new = self.service._operate('policy', {'name': 'Nearest demo', 'mode': 'demo', 'rounding': 'nearest',
            'phone_pool': 'walkin', 'cutoff_minutes': 15, 'station_id': self.stations[0].id,
            'reason': 'New synthetic policy'}, 'policy2')
        self.assertEqual(new['preview'][1]['reservation'], 1)
        self.assertEqual(record.ydental_policy_id, old_policy)
        with self.assertRaises(ValidationError):
            self.service._operate('policy', {'name': 'Unapproved', 'mode': 'published', 'rounding': 'floor',
                'phone_pool': 'reservation', 'cutoff_minutes': 0, 'reason': 'No approval'}, 'not-approved')
        self.assert_balance(record)

    def test_t02_shared_capability_total_and_source_selection(self):
        one = slot(self, self.stations[0], key='one')
        two = slot(self, self.stations[1], key='two')
        clean = acquire(self, one, key='clean')
        fill = acquire(self, two, key='fill', capability=self.capabilities[1])
        self.assertEqual(clean.ydental_slot_id, one)
        self.assertEqual(fill.ydental_slot_id, two)
        summary = self.service._availability(self.area.id, self.capabilities[0].id, self.start, self.end, 'reservation')
        self.assertEqual(summary['shared_total'], 12)
        self.assertEqual(summary['shared_free'], 2)
        self.assertFalse(summary['additive_capabilities'])
        self.assert_balance(one)
        self.assert_balance(two)

    def test_t03_idempotency_and_failed_reschedule_reassign(self):
        record = slot(self, total=3)
        claim = acquire(self, record)
        retry = self.service._capacity_action('acquire', acquire_args(self, record), 'acquire-source')
        self.assertEqual((retry['result'], retry['id']), ('already_accepted', claim.id))
        before = self.service._snapshot(record)
        with self.assertRaises(UserError):
            self.service._capacity_action('reschedule', {'id': claim.id, 'target': acquire_args(self, record, 'revision2'), 'reason': 'Full target'}, 'failed-move')
        self.assertEqual(self.service._snapshot(record), before)
        self.assertEqual(claim.state, 'held')
        target = slot(self, self.stations[0], total=1, key='target')
        with self.assertRaises(UserError):
            self.service._capacity_action('reassign', {'id': claim.id, 'slot_id': target.id, 'reason': 'No reservation'}, 'bad-reassign')
        self.assertEqual(claim.ydental_slot_id, record)
        self.service._capacity_action('cancel', {'id': claim.id, 'reason': 'Cancelled'}, 'cancel')
        self.service._capacity_action('cancel', {'id': claim.id, 'reason': 'Retry'}, 'cancel-again')
        self.assertEqual(record.ydental_reservation_free, 1)
        self.assertEqual(self.root['ydental.supply.event'].search_count([('ydental_claim_id', '=', claim.id), ('ydental_operation', '=', 'cancel')]), 1)
        self.assert_balance(record)

    def test_t04_conversion_cutoff_and_repeat(self):
        record = slot(self)
        claim = acquire(self, record)
        with patch(NOW, return_value=self.start):
            self.service._operate('business', {'area_id': self.area.id, 'state': 'open', 'reason': 'Synthetic opening'}, 'open')
            self.service._operate('convert', {'id': record.id}, 'convert')
            self.service._operate('convert', {'id': record.id}, 'convert2')
            self.assertEqual((record.ydental_reservation_free, record.ydental_walkin_free), (0, 5))
            with self.assertRaises(UserError):
                acquire(self, record, key='late')
        self.assertEqual(claim.state, 'held')
        self.assert_balance(record)

    def test_t05_account_station_and_leave_conflicts(self):
        p = {'user_id': self.staff.id, 'station_id': self.stations[0].id, 'start': fields.Datetime.to_string(self.start), 'end': fields.Datetime.to_string(self.end)}
        first = self.service._operate('assign', p, 'assignment')
        for values in (dict(p, station_id=self.stations[1].id), dict(p, user_id=self.writer.id)):
            with self.assertRaises(UserError):
                self.service._operate('assign', values, 'conflict')
        foreign_service = bind(self, self.writer, 'foreign', self.stores[1])
        floor = self.root['ydental.space.floor'].create({'name': 'B floor', 'ydental_store_id': self.stores[1].id})
        area = self.root['ydental.space.area'].create({'name': 'B area', 'ydental_store_id': self.stores[1].id, 'ydental_floor_id': floor.id})
        with self.assertRaises(UserError):
            foreign_service._operate('assign', dict(p, station_id=False, area_id=area.id), 'cross-store')
        employee = self.admin._membership(self.staff.id, self.stores[0].id).ydental_employee_id
        self.root['resource.calendar.leaves'].create({'name': 'Synthetic absence', 'resource_id': employee.resource_id.id,
            'date_from': self.start, 'date_to': self.end})
        record = self.root['ydental.supply.assignment'].browse(first['id'])
        self.assertIn('Time off', self.service._assignment_warning(record))
        self.assertIn(self.replacement, self.service._replacement_candidates(record))
        with self.assertRaises(UserError):
            self.service._operate('assign', dict(p, station_id=self.stations[1].id), 'leave')
        self.assertFalse(self.root['ydental.supply.slot'].search([('ydental_store_id', 'in', self.stores.ids)]))

    def test_t06_supply_loss_preserves_entitlement_and_s02_topology(self):
        record = slot(self)
        claim = acquire(self, record)
        station = self.stations[1].with_env(self.service.env)
        station.write({'ydental_enabled': False, 'ydental_version': station.ydental_version})
        self.assertEqual(record.state, 'suspended')
        self.assertEqual(claim.state, 'held')
        with self.assertRaises(UserError):
            acquire(self, record, key='after-disable')
        self.assertTrue(self.root['ydental.supply.disposition'].search([('ydental_slot_id', '=', record.id)]))
        with self.assertRaises(UserError):
            station.write({'ydental_area_id': self.area.id, 'ydental_version': station.ydental_version})
        self.assert_balance(record)

    def test_t07_authorization_extra_capacity_and_reduction(self):
        record = slot(self, total=3)
        claim = acquire(self, record)
        reader = bind(self, self.reader, 'read-only')
        with self.assertRaises(AccessError):
            reader._operate('resize', {'id': record.id, 'version': record.ydental_version, 'total': 8, 'reason': 'Denied'}, 'denied')
        with self.assertRaises(UserError):
            self.service._operate('resize', {'id': record.id, 'version': record.ydental_version, 'total': 0, 'reason': 'Below used'}, 'below-used')
        self.service._operate('resize', {'id': record.id, 'version': record.ydental_version, 'total': 6, 'reason': 'Temporary extra capacity'}, 'extra')
        self.assertEqual(record.ydental_total, 6)
        self.assertEqual(claim.state, 'held')
        with self.assertRaises(AccessError):
            record.with_env(self.service.env).write({'ydental_total': 100})
        self.assert_balance(record)

    def test_t08_business_reopen_next_day_and_queue_contract(self):
        record = slot(self)
        with patch(NOW, return_value=self.start):
            result = self.service._operate('business', {'area_id': self.area.id, 'state': 'open', 'reason': 'Open'}, 'open')
            business = self.root['ydental.supply.business'].browse(result['id'])
            self.service._operate('business', {'area_id': self.area.id, 'state': 'draining', 'version': business.ydental_version, 'reason': 'Stop reporting'}, 'drain')
            with self.assertRaises(UserError):
                self.service._operate('business', {'area_id': self.area.id, 'state': 'closed', 'version': business.ydental_version, 'reason': 'Queue unverified'}, 'close-bad')
            self.root['ir.config_parameter'].set_str('ydental_supply_test.queue', 'synthetic_empty')
            self.service._operate('business', {'area_id': self.area.id, 'state': 'closed', 'version': business.ydental_version, 'reason': 'Synthetic queue empty'}, 'close')
            self.service._operate('business', {'area_id': self.area.id, 'state': 'open', 'version': business.ydental_version, 'reason': 'Reopen'}, 'reopen')
        with patch(NOW, return_value=self.start + timedelta(days=1)):
            self.service._operate('business', {'area_id': self.area.id, 'state': 'open', 'reason': 'Next local day'}, 'nextday')
        self.assertEqual(self.root['ydental.supply.business'].search_count([('ydental_area_id', '=', self.area.id)]), 2)
        self.assertEqual(record.ydental_total, 6)
        self.assertFalse(self.root['ydental.supply.claim'].search([('ydental_store_id', 'in', self.stores.ids)]))

    def test_t09_install_configuration_history_and_no_future_models(self):
        self.assertTrue(self.root.ref('ydental_supply.ydental_supply_mutex'))
        self.assertNotIn('ydental.patient', self.env)
        self.assertNotIn('ydental.appointment', self.env)
        self.assertNotIn('ydental.queue', self.env)
        policy = self.root['ydental.supply.policy'].browse(self.policy['id'])
        with self.assertRaises(AccessError):
            policy.unlink()
        with self.assertRaises(AccessError):
            policy.with_env(self.service.env).write({'ydental_phone_pool': 'walkin'})

    def test_t10_cancellation_before_after_expiry_consumed(self):
        record = slot(self)
        before = acquire(self, record, 'before')
        self.service._capacity_action('cancel', {'id': before.id, 'reason': 'Before start'}, 'before-cancel')
        self.assertEqual(record.ydental_reservation_free, 2)
        after = acquire(self, record, 'after')
        expired = acquire(self, record, 'expired')
        with patch(NOW, return_value=self.start + timedelta(minutes=20)):
            self.service._operate('business', {'area_id': self.area.id, 'state': 'open', 'reason': 'Open synthetic day'}, 'open')
            self.service._capacity_action('cancel', {'id': after.id, 'reason': 'After start'}, 'after-cancel')
            self.assertEqual((record.ydental_reservation_free, record.ydental_walkin_free), (0, 5))
            consumed = acquire(self, record, 'consumed', 'walkin')
            self.service._capacity_action('consume', {'id': consumed.id}, 'consume')
            with self.assertRaises(UserError):
                self.service._capacity_action('cancel', {'id': consumed.id, 'reason': 'Started'}, 'consumed-cancel')
        with patch(NOW, return_value=self.end + timedelta(minutes=5)):
            self.service._capacity_action('cancel', {'id': expired.id, 'reason': 'Expired'}, 'expired-cancel')
            self.assertEqual(record.ydental_unavailable, 1)
            with self.assertRaises(UserError):
                self.service._capacity_action('consume', {'id': expired.id}, 'late-consume')
        self.assertEqual(consumed.state, 'consumed')
        self.assert_balance(record)

    def test_t11_week_batch_copy_and_atomic_conflict(self):
        start = self.start - timedelta(days=self.start.weekday())
        p = {'user_id': self.staff.id, 'area_id': self.area.id, 'start': fields.Datetime.to_string(start), 'end': fields.Datetime.to_string(start + timedelta(hours=1))}
        self.service._operate('batch', {'rows': [p]}, 'batch')
        nextweek = fields.Date.to_string((start + timedelta(days=7)).date())
        result = self.service._operate('copy', {'week_start': nextweek}, 'copy')
        self.assertEqual(len(result['ids']), 1)
        before = self.root['ydental.supply.assignment'].search_count([])
        with self.assertRaises(UserError):
            self.service._operate('batch', {'rows': [dict(p, user_id=self.writer.id), p]}, 'bad-batch')
        self.assertEqual(self.root['ydental.supply.assignment'].search_count([]), before)
        self.assertFalse(self.root['ydental.supply.slot'].search([('ydental_store_id', 'in', self.stores.ids)]))
        dashboard = self.service._dashboard(nextweek, 'person')
        self.assertEqual(dashboard['group_by'], 'person')
        self.assertEqual(len(dashboard['assignments']), 1)

    def test_t12_today_default_feedback_and_session_stability(self):
        now = fields.Datetime.now()
        self.service._operate('assign', {'user_id': self.staff.id, 'station_id': self.stations[0].id,
            'start': fields.Datetime.to_string(now - timedelta(minutes=10)), 'end': fields.Datetime.to_string(now + timedelta(minutes=10))}, 'today')
        staff_access = self.root['ydental.access.service'].with_user(self.staff)
        login = staff_access._session_for_key('new-login-today')
        self.assertEqual(login.ydental_store_id, self.stores[0])
        staff_service = staff_access._bind(login).env['ydental.supply.service']
        record = staff_service._today()['assignments']
        hint = staff_service._workbench_suggestion(record.id)
        self.assertEqual((hint['result'], hint['execution']), ('hint_only', 'not_connected'))
        feedback = staff_service._feedback(record.id, 'Wrong suggested chair', 'feedback')
        item = self.root['ydental.supply.feedback'].browse(feedback['id'])
        self.assertIn(self.writer, item.ydental_recipient_ids)
        self.assertNotIn(self.reader, item.ydental_recipient_ids)
        self.assertEqual(staff_service._feedback(record.id, 'Retry', 'feedback2')['id'], item.id)
        with patch(NOW, return_value=now + timedelta(hours=2)):
            staff_service._today()
            self.assertEqual(login.ydental_store_id, self.stores[0])
        other = bind(self, self.staff, 'other-login', self.stores[1])
        self.assertEqual(other.env['ydental.access.service']._scope().ydental_store_id, self.stores[1])
        self.assertEqual(login.ydental_store_id, self.stores[0])

    def test_t13_membership_removal_preserves_history_other_store_and_claims(self):
        p = {'user_id': self.staff.id, 'station_id': self.stations[1].id, 'start': fields.Datetime.to_string(self.start), 'end': fields.Datetime.to_string(self.end)}
        assignment_id = self.service._operate('assign', p, 'future')['id']
        record = slot(self)
        claim = acquire(self, record)
        self.admin._remove(self.staff.id, self.stores[0].id)
        assignment = self.root['ydental.supply.assignment'].browse(assignment_id)
        self.assertEqual(assignment.state, 'cancelled')
        self.assertEqual(claim.state, 'held')
        self.assertEqual(record.state, 'suspended')
        self.assertTrue(self.admin._membership(self.staff.id, self.stores[1].id))
        self.assertTrue(self.root['ydental.supply.disposition'].search([('ydental_assignment_id', '=', assignment.id)]))
        self.assert_balance(record)

    def test_t14_draft_mismatch_and_separate_coverage_verification(self):
        p = {'user_id': self.reader.id, 'station_id': self.stations[1].id, 'start': fields.Datetime.to_string(self.start), 'end': fields.Datetime.to_string(self.end)}
        result = self.service._operate('assign', p, 'mismatch')
        self.assertIn('Draft may be saved', result['warning'])
        record = slot(self)
        with self.assertRaises(UserError):
            self.service._operate('publish', {'id': record.id, 'version': record.ydental_version,
                'user_ids': [self.reader.id], 'reason': 'Unqualified'}, 'bad-coverage')
        self.assertEqual(record.ydental_coverage['user_ids'], [self.staff.id])
        self.assertNotIn('ydental_user_id', self.root['ydental.supply.claim']._fields)

    def test_successful_move_and_reschedule_do_not_bind_execution_station(self):
        first = slot(self, self.stations[0], key='first')
        second = slot(self, self.stations[1], key='second')
        claim = acquire(self, first)
        self.service._capacity_action('reassign', {'id': claim.id, 'slot_id': second.id, 'reason': 'Same channel move'}, 'move')
        self.assertEqual(claim.ydental_slot_id, second)
        future = slot(self, start=self.start + timedelta(days=1), end=self.end + timedelta(days=1), key='future')
        result = self.service._capacity_action('reschedule', {'id': claim.id, 'target': acquire_args(self, future, 'revision2'), 'reason': 'New time'}, 'reschedule')
        self.assertEqual(claim.state, 'cancelled')
        self.assertEqual(self.root['ydental.supply.claim'].browse(result['id']).ydental_slot_id, future)
        for record in (first, second, future):
            self.assert_balance(record)

    def test_explicit_cutoff_phone_pool_and_local_business_date(self):
        self.stores[0].write({'ydental_timezone': 'Asia/Shanghai'})
        self.service._operate('policy', {'name': 'Phone walk-in and cutoff demo', 'mode': 'demo', 'rounding': 'floor',
            'phone_pool': 'walkin', 'cutoff_minutes': 15, 'reason': 'Explicit demo'}, 'phone-policy')
        record = slot(self)
        phone = acquire(self, record, 'phone', 'phone')
        self.assertEqual(phone.ydental_pool, 'walkin')
        with patch(NOW, return_value=self.start - timedelta(minutes=10)):
            with self.assertRaises(UserError):
                acquire(self, record, 'past-cutoff')
        boundary = self.start.replace(hour=18)
        self.assertEqual(self.service._date(self.stores[0], boundary), boundary.date() + timedelta(days=1))

    def test_cross_company_conflict_departure_and_retained_history(self):
        company = self.root['res.company'].create({'name': 'S03 Second legal company'})
        self.manager.write({'company_ids': [fields.Command.link(company.id)]})
        store = self.root['ydental.access.store'].create({'name': 'S03 Cross-company store', 'company_id': company.id, 'ydental_timezone': 'UTC'})
        self.admin._join(self.staff.id, store.id)
        self.admin._join(self.manager.id, store.id)
        self.admin._grant(self.manager.id, store.id, {'capacity': 'write', 'personnel': 'write'})
        floor = self.root['ydental.space.floor'].create({'name': 'Cross-company floor', 'ydental_store_id': store.id})
        area = self.root['ydental.space.area'].create({'name': 'Cross-company area', 'ydental_store_id': store.id, 'ydental_floor_id': floor.id})
        other = bind(self, self.manager, 'cross-company-manager', store)
        p = {'user_id': self.staff.id, 'area_id': self.area.id, 'start': fields.Datetime.to_string(self.start), 'end': fields.Datetime.to_string(self.end)}
        first = self.service._operate('assign', p, 'first')['id']
        with self.assertRaises(UserError):
            other._operate('assign', dict(p, area_id=area.id), 'cross-company-conflict')
        later = dict(p, area_id=area.id, start=fields.Datetime.to_string(self.start + timedelta(hours=3)), end=fields.Datetime.to_string(self.end + timedelta(hours=3)))
        second = other._operate('assign', later, 'later')['id']
        self.admin._remove(self.staff.id, self.stores[0].id)
        self.assertEqual(self.root['ydental.supply.assignment'].browse(first).state, 'cancelled')
        self.assertEqual(self.root['ydental.supply.assignment'].browse(second).state, 'active')
        self.admin._depart(self.staff.id)
        self.assertEqual(self.root['ydental.supply.assignment'].browse(second).state, 'cancelled')
        self.assertFalse(self.staff.active)
        self.assertTrue(self.root['ydental.supply.assignment'].browse([first, second]).exists())

    def test_adjust_extend_policy_precedence_and_handling_resolution(self):
        result = self.service._operate('assign', {'user_id': self.staff.id, 'station_id': self.stations[0].id,
            'start': fields.Datetime.to_string(self.start), 'end': fields.Datetime.to_string(self.end)}, 'adjustable')
        record = self.root['ydental.supply.assignment'].browse(result['id'])
        self.service._operate('adjust', {'id': record.id, 'version': record.ydental_version, 'reason': 'Replacement',
            'values': {'user_id': self.replacement.id, 'station_id': self.stations[0].id,
                       'start': fields.Datetime.to_string(self.start), 'end': fields.Datetime.to_string(self.end)}}, 'adjust')
        self.assertEqual(record.ydental_user_id, self.replacement)
        p = {'name': 'Area override', 'mode': 'demo', 'rounding': 'nearest', 'phone_pool': 'walkin', 'cutoff_minutes': 20, 'area_id': self.area.id, 'reason': 'Area demo'}
        area_policy = self.service._operate('policy', p, 'area-policy')['id']
        capacity = slot(self, self.stations[0], total=2)
        self.assertEqual(capacity.ydental_policy_id.id, area_policy)
        self.assertEqual(capacity.ydental_reservation_free, 1)
        self.service._operate('extend', {'id': capacity.id, 'version': capacity.ydental_version,
            'end': fields.Datetime.to_string(self.end + timedelta(hours=1)), 'reason': 'Temporary longer opening'}, 'extend')
        self.assertEqual(capacity.state, 'suspended')
        self.assertEqual(capacity.ydental_total, 2)
        self.service._operate('publish', {'id': capacity.id, 'version': capacity.ydental_version, 'user_ids': [self.staff.id], 'reason': 'Reverified extension'}, 'republish')
        self.assertEqual(capacity.state, 'published')

    def test_suspended_or_stopped_release_stays_unsaleable(self):
        capacity = slot(self)
        claim = acquire(self, capacity)
        with patch(NOW, return_value=self.start - timedelta(minutes=5)):
            opened = self.service._operate('business', {'area_id': self.area.id, 'state': 'open', 'reason': 'Open'}, 'open')
            self.service._operate('business', {'area_id': self.area.id, 'state': 'draining', 'version': opened['version'], 'reason': 'Stop'}, 'stop')
            self.service._capacity_action('cancel', {'id': claim.id, 'reason': 'Stopped area cancellation'}, 'cancel-stopped')
        self.assertEqual(capacity.ydental_unavailable, 1)
        self.service._operate('resize', {'id': capacity.id, 'version': capacity.ydental_version, 'total': 0, 'reason': 'Remove unused supply'}, 'reduce-unused')
        self.assertEqual(capacity.ydental_total, 0)
        self.assert_balance(capacity)

    def test_capability_and_absence_changes_suspend_without_revoking_claim(self):
        capacity = slot(self)
        claim = acquire(self, capacity)
        employee = self.admin._membership(self.staff.id, self.stores[0].id).ydental_employee_id
        self.root['resource.calendar.leaves'].create({'name': 'New absence', 'resource_id': employee.resource_id.id,
            'date_from': self.start, 'date_to': self.end})
        self.assertEqual(capacity.state, 'suspended')
        self.assertEqual(claim.state, 'held')
        work = self.root['ydental.supply.disposition'].search([('ydental_slot_id', '=', capacity.id)], limit=1)
        self.service._operate('resolve', {'entity': 'disposition', 'id': work.id, 'version': work.ydental_version, 'reason': 'Contact handled; replacement pending verification'}, 'resolve')
        self.assertEqual(work.state, 'resolved')
        self.assertEqual(capacity.state, 'suspended')
        self.assert_balance(capacity)

    def test_feedback_without_editor_falls_back_to_manager(self):
        now = fields.Datetime.now()
        record = self.service._operate('assign', {'user_id': self.staff.id, 'area_id': self.area.id,
            'start': fields.Datetime.to_string(now), 'end': fields.Datetime.to_string(now + timedelta(minutes=30))}, 'today')
        self.admin._grant(self.writer.id, self.stores[0].id, {'capacity': 'none'})
        self.admin._grant(self.manager.id, self.stores[0].id, {'capacity': 'none'})
        staff_service = bind(self, self.staff, 'staff-feedback')
        response = staff_service._feedback(record['id'], 'No editor available', 'fallback')
        self.assertTrue(response['manager_required'])
        self.assertFalse(self.root['ydental.supply.feedback'].browse(response['id']).ydental_recipient_ids)

    def test_week_copy_preserves_local_time_across_dst(self):
        from datetime import datetime
        from zoneinfo import ZoneInfo
        self.stores[0].write({'ydental_timezone': 'America/New_York'})
        start = datetime(2026, 10, 26, 13, 0)
        self.service._operate('assign', {'user_id': self.staff.id, 'area_id': self.area.id,
            'start': fields.Datetime.to_string(start), 'end': fields.Datetime.to_string(start + timedelta(hours=1))}, 'dst-original')
        copied = self.service._operate('copy', {'week_start': '2026-11-02'}, 'dst-copy')
        record = self.root['ydental.supply.assignment'].browse(copied['ids'][0])
        self.assertEqual(record.ydental_start.hour, 14)
        self.assertEqual(record.ydental_start.replace(tzinfo=ZoneInfo('UTC')).astimezone(ZoneInfo('America/New_York')).hour, 9)

    def test_next_request_revocation_and_unforgeable_write_token(self):
        capacity = slot(self)
        self.admin._grant(self.writer.id, self.stores[0].id, {'capacity': 'none'})
        with self.assertRaises(AccessError):
            self.service._dashboard()
        with self.assertRaises(AccessError):
            self.service._operate('resize', {'id': capacity.id, 'version': capacity.ydental_version, 'total': 100, 'reason': 'Revoked'}, 'revoked')
        with self.assertRaises(AccessError):
            capacity.with_env(self.service.env).with_context(ydental_supply_mutation=True).write({'ydental_total': 100})
        self.assertEqual(capacity.ydental_total, 6)

    def test_published_capability_loss_has_pending_handling(self):
        capacity = slot(self)
        claim = acquire(self, capacity)
        self.capabilities[1].write({'active': False})
        self.assertEqual(capacity.state, 'suspended')
        self.assertTrue(self.root['ydental.supply.disposition'].search([('ydental_slot_id', '=', capacity.id)]))
        self.assertEqual(claim.state, 'held')
        self.assert_balance(capacity)

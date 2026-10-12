from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase

from .common import arrive_report, bind, clinical_source, key, make_slot, patient, price, qualify, setup


class TestIntake(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup(cls)

    def task(self, q):
        return self.root['ydental.intake.task'].browse(q['task_id'])

    def entitlement(self, q):
        return self.root['ydental.intake.entitlement'].browse(q['id'])

    def report(self, q):
        return self.front._operate('report', {'task_id': q['task_id'], 'version': self.task(q).ydental_version}, key())

    def test_t01_two_independent_area_services_no_doctor_or_station(self):
        person = patient(self)
        a = qualify(self, person)
        b = qualify(self, person, self.mappings[0][1])
        self.assertNotEqual(a['task_id'], b['task_id'])
        self.assertNotEqual(a['claim_id'], b['claim_id'])
        for entity in ('entitlement', 'task'):
            model = self.root['ydental.intake.' + entity]
            self.assertNotIn('ydental_doctor_id', model._fields)
            self.assertNotIn('ydental_station_id', model._fields)
        self.assertFalse(self.root['ydental.patient.relation'].search([('ydental_patient_id', '=', person)]).ydental_first_arrival)
        self.assertFalse(self.root['ydental.intake.arrival'].search([('ydental_patient_id', '=', person)]))

    def test_t02_early_reporting_zero_sale_balance_and_idempotency(self):
        q = qualify(self)
        qualify(self)
        self.assertEqual(self.slots[0][0].ydental_reservation_free, 0)
        args = {'task_id': q['task_id'], 'version': self.task(q).ydental_version}
        self.front._operate('arrive', {'patient_id': q['patient_id']}, 'arrival-once')
        self.front._operate('arrive', {'patient_id': q['patient_id']}, 'arrival-once')
        first = self.front._operate('report', args, 'report-once')
        self.assertEqual(self.front._operate('report', args, 'report-once')['id'], first['id'])
        self.assertEqual(self.report(q)['id'], first['id'])
        self.assertEqual(self.slots[0][0].ydental_reservation_free, 0)
        self.assertEqual(self.entitlement(q).ydental_claim_id.ydental_slot_id.ydental_start, self.start)
        self.assertEqual(self.root['ydental.intake.arrival'].search_count([('ydental_patient_id', '=', q['patient_id'])]), 1)
        self.assertEqual(self.root['ydental.intake.test.queue'].search_count([('ydental_patient_id', '=', q['patient_id']), ('ydental_active', '=', True)]), 1)

    def test_t03_switch_success_and_refusal_preserve_old_position(self):
        person = patient(self)
        a, b = qualify(self, person), qualify(self, person, self.mappings[0][1])
        old = arrive_report(self, a)
        business = self.group.env['ydental.supply.service']._business_record(self.stores[0], self.areas[0][1].id)
        self.group.env['ydental.supply.service']._operate('business', {'area_id': self.areas[0][1].id,
            'state': 'draining', 'version': business.ydental_version, 'reason': 'Synthetic stop'}, key())
        with self.assertRaises(UserError):
            self.report(b)
        self.assertTrue(self.root['ydental.intake.position'].browse(old['id']).ydental_active)
        self.group.env['ydental.supply.service']._operate('business', {'area_id': self.areas[0][1].id,
            'state': 'open', 'version': business.ydental_version, 'reason': 'Synthetic reopen'}, key())
        new = self.report(b)
        self.assertFalse(self.root['ydental.intake.position'].browse(old['id']).ydental_active)
        self.assertTrue(self.root['ydental.intake.position'].browse(new['id']).ydental_active)
        self.assertEqual(self.task(a).state, 'pending')
        self.assertEqual(self.entitlement(a).state, 'held')
        self.assertEqual(self.slots[0][0].ydental_reservation_free, 1)

    def test_t05_failed_registration_and_queue_adapter_roll_back_everything(self):
        self.root['ir.config_parameter'].set_str('ydental_intake_test.refuse_task', 'unused')
        counts = {e: self.root['ydental.intake.' + e].search_count([]) for e in ('task', 'entitlement', 'position', 'arrival')}
        before = self.slots[0][0].ydental_walkin_free
        with patch.object(type(self.front), '_queue_accept', side_effect=UserError('Synthetic queue acceptance failure')):
            with self.assertRaises(UserError):
                self.front._operate('walkin_report', {'patient_id': patient(self), 'mapping_id': self.mappings[0][0].id,
                    'start': fields.Datetime.to_string(self.start), 'end': fields.Datetime.to_string(self.end)}, key())
        for entity, count in counts.items():
            self.assertEqual(self.root['ydental.intake.' + entity].search_count([]), count)
        self.assertEqual(self.slots[0][0].ydental_walkin_free, before)

    def test_t06_cancel_once_and_full_target_reschedule_preserves_original(self):
        q = qualify(self)
        target = make_slot(self, self.group, self.stations[0][0], self.start + timedelta(hours=3), self.end + timedelta(hours=3), total=3)
        qualify(self, start=target.ydental_start, end=target.ydental_end)
        old_claim = self.entitlement(q).ydental_claim_id.id
        old_version = self.entitlement(q).ydental_version
        with self.assertRaises(UserError):
            self.front._operate('reschedule', {'record_id': q['id'], 'version': old_version, 'mapping_id': self.mappings[0][0].id,
                'start': fields.Datetime.to_string(target.ydental_start), 'end': fields.Datetime.to_string(target.ydental_end), 'reason': 'Target full'}, key())
        self.assertEqual(self.entitlement(q).ydental_claim_id.id, old_claim)
        self.assertEqual(self.entitlement(q).ydental_version, old_version)
        args = {'record_id': q['id'], 'version': old_version, 'reason': 'Synthetic cancellation'}
        result = self.front._operate('cancel', args, 'cancel-once')
        self.front._operate('cancel', args, 'cancel-once')
        self.front._operate('cancel', dict(args, version=result['version']), key())
        self.assertEqual(self.slots[0][0].ydental_reservation_free, 2)
        self.assertEqual(self.entitlement(q).ydental_claim_id.state, 'cancelled')

    def test_t06_return_after_start_time_and_expiry_use_s03_pools(self):
        q = qualify(self)
        with patch.object(type(self.front.env['ydental.supply.service']), '_now', return_value=self.start + timedelta(minutes=5)):
            self.front._operate('cancel', {'record_id': q['id'], 'version': q['version'], 'reason': 'After slot start'}, key())
        self.assertEqual(self.slots[0][0].ydental_walkin_free, 5)
        q = qualify(self)
        with patch.object(type(self.front.env['ydental.supply.service']), '_now', return_value=self.end + timedelta(minutes=5)):
            self.front._operate('cancel', {'record_id': q['id'], 'version': q['version'], 'reason': 'After expiry'}, key())
        self.assertEqual(self.slots[0][0].ydental_unavailable, 1)
        self.assertEqual(self.slots[0][0].ydental_walkin_free, 5)

    def test_t07_bulk_write_create_forged_context_and_cross_store(self):
        q = qualify(self)
        other = qualify(self)
        for service in (self.front, self.reader, self.doctor):
            with self.assertRaises(AccessError):
                service.env['ydental.intake.task'].with_context(ydental_intake_mutation=True).browse([q['task_id'], other['task_id']]).write({'state': 'started'})
            with self.assertRaises(AccessError):
                service.env['ydental.intake.task'].create({'name': 'Forged', 'ydental_store_id': self.stores[0].id})
        b = bind(self, self.users['frontdesk'], self.stores[1])
        with self.assertRaises(AccessError):
            b._operate('cancel', {'record_id': q['id'], 'version': q['version'], 'reason': 'Cross-store bypass'}, key())
        with self.assertRaises(AccessError):
            self.reader._operate('arrive', {'patient_id': q['patient_id']}, key())
        with self.assertRaises(AccessError):
            self.front.env['ydental.supply.service'].with_context(ydental_intake_capacity={'store_id': self.stores[0].id})._capacity_action('consume', {'id': q['claim_id']}, key())

    def test_t08_panorama_never_falls_back_to_cbct(self):
        slot = self.slots[0][2]
        self.group.env['ydental.supply.service']._operate('resize', {'id': slot.id, 'version': slot.ydental_version,
            'total': 0, 'reason': 'Synthetic no panorama'}, key())
        with self.assertRaises(UserError):
            qualify(self, mapping=self.mappings[0][2])
        self.assertEqual(self.slots[0][3].ydental_reservation_free, 2)
        self.assertFalse(self.root['ydental.intake.task'].search([('ydental_mapping_id', '=', self.mappings[0][3].id)]))

    def test_t09_real_merge_migrates_live_sources_keeps_identity_snapshots(self):
        source, target = patient(self), patient(self)
        q = qualify(self, source)
        position = arrive_report(self, q)
        task = self.task(q)
        snapshot = task.ydental_identity_snapshot
        patients = self.front.env['ydental.patient.service']
        req = patients._operate('request_merge', {'source_id': source, 'target_id': target, 'reason': 'S05 real activity merge'}, key())
        result = self.group.env['ydental.patient.service']._operate('confirm', {'request_id': req['id'], 'version': req['version'], 'reason': 'Verified synthetic identity'}, key())
        self.assertEqual(result['result'], 'accepted')
        for record in (task, self.entitlement(q), self.root['ydental.intake.position'].browse(position['id'])):
            self.assertEqual(record.ydental_patient_id.id, target)
            self.assertEqual(record.ydental_origin_patient_id.id, source)
            self.assertEqual(record.ydental_identity_snapshot, snapshot)
        count = self.root['ydental.intake.arrival'].search_count([])
        self.front._operate('arrive', {'patient_id': source}, key())
        self.assertEqual(self.root['ydental.intake.arrival'].search_count([]), count)
        self.assertEqual(self.report(q)['id'], position['id'])

    def test_t09_real_merge_conflict_and_execution_block(self):
        source, target = patient(self), patient(self)
        qualify(self, source)
        qualify(self, target)
        req = self.front.env['ydental.patient.service']._operate('request_merge', {'source_id': source, 'target_id': target, 'reason': 'Both real reservations'}, key())
        result = self.group.env['ydental.patient.service']._operate('confirm', {'request_id': req['id'], 'version': req['version'], 'reason': 'Conflict must remain'}, key())
        self.assertEqual(result['result'], 'conflict_requires_resolution')
        self.assertTrue(any(c['kind'] == 'intake_entitlement' for c in result['conflicts']))
        self.assertFalse(self.root['ydental.patient'].browse(source).ydental_merged_into_id)

    def test_t10_prices_native_guard_store_permissions_and_missing_price(self):
        a = price(self)
        bservice = bind(self, self.users['manager'], self.stores[1])
        price(self, 650, bservice)
        payload = {'catalog_id': self.catalogs[0].id, 'currency_id': self.currency.id, 'quantity': 1,
            'source': 'demo-A-600', 'policy': 'demo_confirmation'}
        self.assertEqual(self.group._operate('snapshot', payload, key())['amount'], 600)
        self.assertEqual(bservice._operate('snapshot', dict(payload, source='demo-B-650'), key())['amount'], 650)
        with self.assertRaises(UserError):
            self.group._operate('snapshot', dict(payload, catalog_id=self.catalogs[1].id, source='missing'), key())
        with self.assertRaises(AccessError):
            self.front._operate('price', {}, key())
        with self.assertRaises(AccessError):
            self.pricer._operate('catalog', {}, key())
        for record, values in [(self.catalogs[0].ydental_product_id, {'name': 'Bypass'}),
                (self.catalogs[0].ydental_product_id.product_tmpl_id, {'list_price': 0}),
                (self.root['ydental.intake.price'].browse(a['id']).ydental_rule_id, {'fixed_price': 0})]:
            with self.assertRaises(AccessError):
                record.write(values)
        with self.assertRaises(AccessError):
            self.root['product.pricelist.item'].create({'pricelist_id': self.root['ydental.intake.price'].browse(a['id']).ydental_pricelist_id.id, 'fixed_price': 0})
        with self.assertRaises(UserError):
            price(self, 620)

    def test_t11_timed_untimed_referral_target_scope_and_expiry(self):
        q = clinical_source(self, qualify(self))
        target = self.mappings[1][0]
        args = {'source_task_id': q['task_id'], 'version': self.task(q).ydental_version, 'mapping_id': target.id, 'reason': 'S05 synthetic referral'}
        timed = self.doctor._synthetic_referral_action('refer_timed', dict(args, start=fields.Datetime.to_string(self.start), end=fields.Datetime.to_string(self.end)), key())
        self.assertEqual(self.slots[1][0].ydental_reservation_free, 1)
        b = bind(self, self.users['frontdesk'], self.stores[1])
        arrive_report(self, timed, b)
        self.assertEqual(self.slots[1][0].ydental_reservation_free, 1)
        untimed = self.doctor._synthetic_referral_action('refer_untimed', dict(args, valid_until=fields.Datetime.to_string(fields.Datetime.now() + timedelta(days=7))), key())
        self.assertEqual(self.slots[1][0].ydental_walkin_free, 4)
        b._operate('accept_referral', {'record_id': untimed['id'], 'version': untimed['version'],
            'start': fields.Datetime.to_string(self.start), 'end': fields.Datetime.to_string(self.end)}, key())
        self.assertEqual(self.slots[1][0].ydental_walkin_free, 3)
        expired = self.doctor._synthetic_referral_action('refer_untimed', dict(args, valid_until=fields.Datetime.to_string(fields.Datetime.now() + timedelta(seconds=1))), key())
        with patch.object(type(b), '_now', return_value=fields.Datetime.now() + timedelta(days=8)):
            with self.assertRaises(UserError):
                b._operate('accept_referral', {'record_id': expired['id'], 'version': 1,
                    'start': fields.Datetime.to_string(self.start), 'end': fields.Datetime.to_string(self.end)}, key())
        with self.assertRaises(AccessError):
            self.doctor._operate('reserve', {'patient_id': q['patient_id'], 'mapping_id': target.id,
                'start': fields.Datetime.to_string(self.start), 'end': fields.Datetime.to_string(self.end)}, key())
        with self.assertRaises(AccessError):
            self.doctor.env['ydental.intake.task'].browse(timed['task_id']).write({'state': 'started'})

    def test_t12_void_only_reuse_and_explicit_cancel_do_not_reset_missed(self):
        q = qualify(self)
        arrive_report(self, q)
        task = self.task(q)
        task._save({'ydental_missed_count': 2})  # Synthetic true missed-call fact.
        self.front._operate('void', {'task_id': task.id, 'version': task.ydental_version,
            'reason': 'Synthetic void only', 'cancel_qualification': False}, key())
        self.assertEqual(self.entitlement(q).state, 'held')
        self.assertEqual(self.slots[0][0].ydental_reservation_free, 1)
        self.report(q)
        self.assertEqual(task.ydental_missed_count, 2)
        self.front._operate('void', {'task_id': task.id, 'version': task.ydental_version,
            'reason': 'Explicit qualification cancellation', 'cancel_qualification': True}, key())
        self.assertEqual(self.entitlement(q).state, 'cancelled')
        self.assertEqual(self.slots[0][0].ydental_reservation_free, 2)
        with self.assertRaises(UserError):
            self.report(q)

    def test_t12_started_qualification_cannot_return_or_switch(self):
        person = patient(self)
        q = qualify(self, person)
        other = qualify(self, person, self.mappings[0][1])
        arrive_report(self, q)
        task = self.task(q)
        self.doctor._downstream_action('start', {'task_id': task.id, 'version': task.ydental_version}, key())
        with self.assertRaises(UserError):
            self.front._operate('cancel', {'record_id': q['id'], 'version': self.entitlement(q).ydental_version, 'reason': 'Started'}, key())
        with self.assertRaises(UserError):
            self.report(other)
        self.assertEqual(self.entitlement(q).ydental_claim_id.state, 'consumed')
        self.assertEqual(self.slots[0][0].ydental_reservation_free, 1)
        with self.assertRaises(AccessError):
            self.doctor._operate('start', {'task_id': task.id, 'version': task.ydental_version}, key())

    def test_t13_snapshot_recovery_after_price_replacement(self):
        old = price(self)
        payload = {'catalog_id': self.catalogs[0].id, 'currency_id': self.currency.id, 'quantity': 1,
            'source': 'S05 immutable source', 'policy': 'demo_confirmation'}
        frozen = self.group._operate('snapshot', payload, 'frozen')
        moment = fields.Datetime.now() + timedelta(seconds=1)
        new = price(self, 620, start=moment, replace=self.root['ydental.intake.price'].browse(old['id']))
        with patch.object(type(self.group), '_now', return_value=moment + timedelta(seconds=1)):
            self.assertEqual(self.group._operate('snapshot', payload, key())['amount'], 600)
            current = self.group._operate('snapshot', dict(payload, source='S05 new source'), key())
        self.assertEqual(current['amount'], 620)
        self.assertEqual(current['price_id'], new['id'])
        self.assertEqual(self.group._operate('snapshot', payload, 'frozen')['id'], frozen['id'])
        with self.assertRaises(AccessError):
            self.root['ydental.intake.snapshot'].browse(frozen['id']).write({'ydental_unit_price': 0})
        with self.assertRaises(UserError):
            self.group._operate('snapshot', dict(payload, policy='production'), key())

    def test_derived_continuation_no_original_capacity_and_stop_still_applies(self):
        q = qualify(self)
        arrive_report(self, q)
        task = self.task(q)
        self.doctor._downstream_action('start', {'task_id': task.id, 'version': task.ydental_version}, key())
        task._save({'state': 'done'})  # Test-only downstream completion fact.
        derived = self.doctor._downstream_action('derived', {'source_task_id': task.id, 'version': task.ydental_version,
            'mapping_id': self.mappings[0][2].id, 'kind': 'derived'}, 'derived-once')
        self.assertEqual(self.doctor._downstream_action('derived', {'source_task_id': task.id, 'version': task.ydental_version,
            'mapping_id': self.mappings[0][2].id, 'kind': 'derived'}, 'derived-once')['id'], derived['id'])
        self.assertEqual(self.slots[0][0].ydental_reservation_free, 1)
        self.assertEqual(self.slots[0][2].ydental_reservation_free, 2)
        self.assertFalse(self.root['ydental.intake.task'].browse(derived['id']).ydental_entitlement_id)
        business = self.group.env['ydental.supply.service']._business_record(self.stores[0], self.areas[0][2].id)
        self.group.env['ydental.supply.service']._operate('business', {'area_id': self.areas[0][2].id,
            'version': business.ydental_version, 'state': 'draining', 'reason': 'Stop external reporting'}, key())
        with self.assertRaises(UserError):
            self.front._operate('report', {'task_id': derived['id'], 'version': derived['version']}, key())

    def test_native_ordinary_products_and_pricelists_can_still_copy(self):
        ordinary = self.root['product.template'].create({'name': 'S05 ordinary native service', 'type': 'service'})
        copied = ordinary.copy({'name': 'S05 ordinary native copy'})
        self.assertFalse(copied.ydental_intake_owned)
        ordinary_list = self.root['product.pricelist'].create({'name': 'S05 ordinary native pricelist', 'currency_id': self.currency.id})
        self.assertFalse(ordinary_list.copy().ydental_intake_owned)
        with self.assertRaises(AccessError):
            self.catalogs[0].ydental_product_id.product_tmpl_id.copy({'name': 'Protected clone'})

    def test_rework_group_catalog_independent_of_store_price(self):
        old_price = price(self)
        self.admin._grant(self.users['manager'].id, self.stores[0].id, {'price': 'none'})
        args = {'code': 's05_rework_' + key(), 'name': 'S05 Group Only', 'kind': 'care',
            'capability_id': self.capabilities[0].id, 'uom_id': self.uom.id}
        created = self.group._operate('catalog', args, key())
        edited = self.group._operate('catalog_edit', {'record_id': created['id'], 'version': created['version'],
            'name': 'S05 Group Shared Disabled', 'active': False}, key())
        item = self.root['ydental.intake.catalog'].browse(created['id'])
        self.assertEqual(item.ydental_product_id.with_context(active_test=False).name, item.name)
        self.assertFalse(item.ydental_product_id.active)
        for store in self.stores:
            desk = bind(self, self.users['frontdesk'], store)
            self.assertEqual(desk.env['ydental.intake.catalog'].with_context(active_test=False).browse(item.id).name, item.name)
        self.assertEqual(self.root['ydental.intake.price'].browse(old_price['id']).ydental_unit_price, 600)
        for operation in ('mapping', 'mapping_edit', 'price', 'review', 'publish', 'snapshot'):
            with self.assertRaises(AccessError):
                self.group._operate(operation, {}, key())
        for role in ('price', 'frontdesk', 'doctor', 'reader'):
            service = bind(self, self.users[role])
            for operation, payload in [('catalog', args), ('catalog_edit', {'record_id': item.id,
                    'version': edited['version'], 'name': 'Forbidden', 'active': True})]:
                with self.assertRaises(AccessError):
                    service._operate(operation, payload, key())
        # A price writer can maintain its price/mapping, without catalog authority.
        price(self, 700, service=self.pricer, catalog=self.catalogs[1])
        self.pricer._operate('mapping_edit', {'record_id': self.mappings[0][1].id,
            'version': self.mappings[0][1].ydental_version, 'active': True}, key())
        self.users['manager'].write({'group_ids': [fields.Command.unlink(self.root.ref('ydental_access.ydental_group_manager').id)]})
        with self.assertRaises(AccessError):
            self.group._operate('catalog', args, key())

    def test_rework_reservation_phone_local_day_and_zero_balance(self):
        from contextlib import ExitStack
        from datetime import datetime
        store = self.stores[0]
        store.ydental_timezone = 'Pacific/Honolulu'
        before = datetime(2032, 1, 1, 23)
        start, end = datetime(2032, 1, 2, 20), datetime(2032, 1, 2, 21)
        def clock(stack, moment):
            for name in ('ydental.intake.service', 'ydental.supply.service', 'ydental.patient.service'):
                stack.enter_context(patch.object(type(self.front.env[name]), '_now', return_value=moment))
        with ExitStack() as stack:
            clock(stack, before)
            slot = make_slot(self, self.group, self.stations[0][0], start, end)
            qs = [qualify(self, channel=c, start=start, end=end) for c in ('reservation', 'phone')]
            self.assertEqual(slot.ydental_reservation_free, 0)
            for q in qs:
                self.front._operate('arrive', {'patient_id': q['patient_id']}, key())
                with self.assertRaisesRegex(UserError, 'reporting_date_mismatch'):
                    self.report(q)
                self.assertEqual(self.task(q).state, 'pending')
                self.assertEqual(self.entitlement(q).state, 'held')
                self.assertEqual(self.entitlement(q).ydental_claim_id.state, 'held')
                self.assertFalse(self.root['ydental.intake.position'].search([('ydental_task_id', '=', q['task_id'])]))
                self.assertFalse(self.root['ydental.intake.test.queue'].search([('ydental_task_id', '=', q['task_id'])]))
            self.assertEqual(slot.ydental_reservation_free, 0)
        with ExitStack() as stack:
            clock(stack, datetime(2032, 1, 2, 11))  # Local 01:00, nine hours before the slot.
            self.group.env['ydental.supply.service']._operate('business', {'area_id': self.areas[0][0].id,
                'state': 'open', 'reason': 'Synthetic next local day'}, key())
            for q in qs:
                arrive_report(self, q)
                self.assertEqual(self.entitlement(q).ydental_claim_id.id, q['claim_id'])
                self.assertEqual(self.entitlement(q).ydental_claim_id.ydental_slot_id, slot)
            self.assertEqual(slot.ydental_reservation_free, 0)

    def test_rework_cross_legal_trusted_referral_scope_audit_and_failures(self):
        from .common import cross_legal_target
        from odoo.addons.ydental_intake.models.ydental_intake_service import YDentalIntakeService
        store, desk, mapping, slot, manager, user = cross_legal_target(self)
        self.assertNotIn(store.company_id, self.users['doctor'].company_ids)
        # Source doctor's only target-independent work membership is A.
        self.admin._remove(self.users['doctor'].id, self.stores[1].id)
        self.assertFalse(self.doctor.env['ydental.access.service']._membership(self.users['doctor'].id, store.id))
        q = clinical_source(self, qualify(self))
        args = {'source_task_id': q['task_id'], 'version': q['task_version'], 'mapping_id': mapping.id,
            'reason': 'Trusted cross-legal synthetic source'}
        timed_args = dict(args, start=fields.Datetime.to_string(self.start), end=fields.Datetime.to_string(self.end))
        for operation in ('refer_timed', 'refer_untimed'):
            with self.assertRaises(AccessError):
                self.doctor._operate(operation, timed_args, key())
            with self.assertRaises(AccessError):
                self.doctor.with_context(ydental_referral_permit=True)._referral_action(operation, timed_args, key(), permit={'actor_id': self.users['doctor'].id})
        with self.assertRaises(AccessError):
            YDentalIntakeService._authorize_referral(self.doctor, 'refer_timed', timed_args, object())
        timed = self.doctor._synthetic_referral_action('refer_timed', timed_args, key())
        untimed = self.doctor._synthetic_referral_action('refer_untimed', dict(args,
            valid_until=fields.Datetime.to_string(fields.Datetime.now() + timedelta(days=7))), key())
        self.assertEqual((slot.ydental_reservation_free, slot.ydental_walkin_free), (1, 4))
        desk._operate('accept_referral', {'record_id': untimed['id'], 'version': untimed['version'],
            'start': timed_args['start'], 'end': timed_args['end']}, key())
        self.assertEqual((slot.ydental_reservation_free, slot.ydental_walkin_free), (1, 3))
        receipt = self.root['ydental.intake.operation'].search([('name', '=', 'refer_timed'), ('ydental_actor_id', '=', self.users['doctor'].id)])
        self.assertEqual(receipt.ydental_category, 'medical')
        audit = self.root['ydental.access.audit'].search([('ydental_event', '=', 'intake.refer_timed'), ('ydental_target_id', '=', receipt.id)])
        self.assertEqual((audit.ydental_category, audit.ydental_user_id.id), ('medical', self.users['doctor'].id))
        self.assertEqual(audit.ydental_after['target_store_id'], store.id)
        self.assertEqual(audit.ydental_after['source_task_id'], q['task_id'])
        self.assertEqual(audit.ydental_after['target_mapping_id'], mapping.id)
        self.assertEqual(audit.ydental_after['source_store_id'], self.stores[0].id)
        for action, payload in [('reserve', {'patient_id': q['patient_id'], 'mapping_id': mapping.id, 'start': timed_args['start'], 'end': timed_args['end']}),
                ('cancel', {'record_id': timed['id'], 'version': timed['version'], 'reason': 'Forbidden target cancel'}),
                ('mapping_edit', {'record_id': mapping.id, 'version': mapping.ydental_version, 'active': False}), ('price', {})]:
            with self.assertRaises(AccessError):
                self.doctor._operate(action, payload, key())
        with self.assertRaises(AccessError):
            self.doctor.env['ydental.intake.task'].browse(timed['task_id']).write({'state': 'cancelled'})
        with self.assertRaises(AccessError):
            bind(self, self.users['doctor'], store)
        for disabled in ('store', 'mapping', 'stop', 'full'):
            counts = {m: self.root[m].search_count([]) for m in ('ydental.patient.relation', 'ydental.supply.claim', 'ydental.intake.task')}
            source_version = self.task(q).ydental_version
            with self.root.cr.savepoint():
                if disabled == 'store': store.active = False
                if disabled == 'mapping': mapping._save({'active': False})
                if disabled == 'stop': manager.env['ydental.supply.service']._operate('business', {'area_id': mapping.ydental_area_id.id, 'state': 'draining', 'reason': 'Test stop'}, key())
                if disabled == 'full':
                    self.doctor._synthetic_referral_action('refer_timed', timed_args, key())
                    counts = {m: self.root[m].search_count([]) for m in counts}
                with self.assertRaises((AccessError, UserError)):
                    self.doctor._synthetic_referral_action('refer_timed', timed_args, key())
                self.assertEqual(self.task(q).ydental_version, source_version)
                self.assertEqual({m: self.root[m].search_count([]) for m in counts}, counts)
                # Restore the synthetic fixture for the next negative branch.
                if disabled == 'store': store.active = True
                if disabled == 'mapping': mapping._save({'active': True})
                if disabled == 'stop': manager.env['ydental.supply.service']._operate('business', {'area_id': mapping.ydental_area_id.id, 'state': 'open', 'reason': 'Test reopen'}, key())

    def test_rework_timed_referral_uses_target_reservation_day(self):
        from contextlib import ExitStack
        q = clinical_source(self, qualify(self))
        start, end = self.start + timedelta(days=1), self.end + timedelta(days=1)
        bmanager = bind(self, self.users['manager'], self.stores[1])
        slot = make_slot(self, bmanager, self.stations[1][0], start, end, total=3)
        args = {'source_task_id': q['task_id'], 'version': q['task_version'], 'mapping_id': self.mappings[1][0].id,
            'start': fields.Datetime.to_string(start), 'end': fields.Datetime.to_string(end), 'reason': 'Synthetic timed tomorrow'}
        timed = self.doctor._synthetic_referral_action('refer_timed', args, key())
        b = bind(self, self.users['frontdesk'], self.stores[1])
        b._operate('arrive', {'patient_id': timed['patient_id']}, key())
        with self.assertRaisesRegex(UserError, 'reporting_date_mismatch'):
            b._operate('report', {'task_id': timed['task_id'], 'version': timed['task_version']}, key())
        self.assertFalse(self.root['ydental.intake.position'].search([('ydental_task_id', '=', timed['task_id'])]))
        self.assertFalse(self.root['ydental.intake.test.queue'].search([('ydental_task_id', '=', timed['task_id'])]))
        self.assertEqual((self.task(timed).state, self.entitlement(timed).state, slot.ydental_reservation_free), ('pending', 'held', 0))
        with ExitStack() as stack:
            moment = start.replace(hour=0, minute=1, second=0)
            for name in ('ydental.intake.service', 'ydental.supply.service', 'ydental.patient.service'):
                stack.enter_context(patch.object(type(b.env[name]), '_now', return_value=moment))
            bmanager.env['ydental.supply.service']._operate('business', {'area_id': self.areas[1][0].id,
                'state': 'open', 'reason': 'Synthetic target next local day'}, key())
            arrive_report(self, timed, b)
            self.assertEqual(slot.ydental_reservation_free, 0)
            self.assertEqual(self.entitlement(timed).ydental_claim_id.id, timed['claim_id'])

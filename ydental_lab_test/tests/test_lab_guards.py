import base64
import secrets
from datetime import UTC, date, timedelta
from types import SimpleNamespace
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestLaboratoryGuards(TransactionCase):
    def test_dataset_source_registry_and_patient_care_paths_are_installed(self):
        access = self.env['ydental.access.service']
        sources = access._get_sources()
        self.assertEqual(sources['lab_order'], 'ydental.lab.order')
        self.assertEqual(sources['lab_code_scan'], 'ydental.lab.code.scan')
        self.assertEqual(sources['lab_charge'], 'ydental.lab.charge')
        care = access._get_patient_care_sources()
        self.assertEqual(care['ydental.lab.order'], 'ydental_patient_id')
        self.assertEqual(care['ydental.lab.event'], 'ydental_order_id.ydental_patient_id')
        self.assertEqual(care['ydental.lab.charge'], 'ydental_patient_id')

    def test_unknown_action_rejected_before_scope_or_side_effect(self):
        service = self.env['ydental.lab.service']
        with self.assertRaises(ValidationError):
            service._operate('patient_lookup', {'patient_id': 1}, 's' * 24)

    def test_short_idempotency_key_rejected_before_scope_or_side_effect(self):
        service = self.env['ydental.lab.service']
        with self.assertRaises(ValidationError):
            service._operate('send', {'order_id': 1}, 'short')

    def test_order_and_event_direct_create_are_not_public_mutation_paths(self):
        for model in ('ydental.lab.order', 'ydental.lab.event', 'ydental.lab.operation'):
            with self.subTest(model=model), self.assertRaises(AccessError):
                self.env[model].create({})

    def test_client_cannot_force_order_state_through_orm_write(self):
        with self.assertRaises(AccessError):
            self.env['ydental.lab.order'].browse(999999).write({'state': 'done'})

    def test_untrusted_inventory_source_payload_is_rejected(self):
        with self.assertRaises(AccessError):
            self.env['ydental.inventory.service']._lab_workflow_move(
                {'store_id': 1, 'order_id': 1, 'operation': 'discard'}, 'Untrusted payload')

    def test_unknown_package_code_is_non_disclosing_and_repeat_lookup_is_read_only(self):
        store = self.env['ydental.access.store'].sudo().create({
            'name': 'Synthetic laboratory scan scope',
            'company_id': self.env.company.id,
            'ydental_timezone': 'UTC',
        })
        service = self.env['ydental.lab.service']
        before = self.env['ydental.lab.operation'].sudo().search_count([])
        for _attempt in range(2):
            with self.assertRaises(UserError) as error:
                service._resolve_package_code(store, 'synthetic-unknown-package-code')
            self.assertIn('code_unavailable', str(error.exception))
            self.assertNotIn('synthetic-unknown-package-code', str(error.exception))
            self.assertNotIn('patient', str(error.exception).lower())
        self.assertEqual(before, self.env['ydental.lab.operation'].sudo().search_count([]))

    def test_validation_helpers_reject_non_positive_quantity_and_url_credentials(self):
        service = self.env['ydental.lab.service']
        with self.assertRaises(ValidationError):
            service._validate_positive_quantity(0)
        with self.assertRaises(ValidationError):
            service._external_link('https://vendor.example/order?token=secret')

    def test_sent_order_receipt_uses_dispatch_snapshot_after_qualification_expiry(self):
        service = self.env['ydental.lab.service']
        store = SimpleNamespace(id=47)
        order = SimpleNamespace(
            id=12,
            state='processing',
            ydental_vendor_id=SimpleNamespace(state='draft', valid_until=False),
            ydental_cooperation_id=SimpleNamespace(id=93, active=False),
            ydental_vendor_qualification_version=4,
            ydental_vendor_qualification_valid_until='2020-01-01',
            ydental_cooperation_active_at_dispatch=True,
        )
        with (
            patch.object(type(service), '_warehouse_write', return_value=store),
            patch.object(type(service), '_get_order', return_value=order),
            patch.object(type(service), '_record_action', return_value={'state': 'received'}) as record_action,
            patch.object(type(service), '_check_vendor', side_effect=AssertionError('must not recheck current qualification')),
            patch.object(type(service), '_purchase_cost_snapshot', return_value=None) as purchase_snapshot,
        ):
            result = service._receive(store, 12)
        self.assertEqual(result['state'], 'received')
        purchase_snapshot.assert_called_once_with(order)
        record_action.assert_called_once()
        self.assertEqual(record_action.call_args.args[:2], (order, 'received'))
        self.assertEqual(record_action.call_args.kwargs['values']['state'], 'received')

    def test_confirmed_purchase_line_cannot_be_reused_by_another_cycle(self):
        service = self.env['ydental.lab.service']
        line = SimpleNamespace(id=73)
        existing_order = SimpleNamespace(id=19)
        order = SimpleNamespace(id=20)

        class OrderModel:
            def search(self, domain, limit=1):
                self.domain, self.limit = domain, limit
                return existing_order

        with patch.object(type(service), '_model', return_value=OrderModel()) as model:
            with self.assertRaises(ValidationError):
                service._assert_purchase_line_exclusive(order, line)

        self.assertEqual(model.call_args.args[0], 'order')

    def test_vendor_approval_expiry_task_uses_governance_hook_for_each_active_cooperation(self):
        service = self.env['ydental.lab.service']
        store = SimpleNamespace(id=31, company_id=SimpleNamespace(id=8))
        responsible = SimpleNamespace(id=44)
        cooperation = SimpleNamespace(ydental_store_id=store, responsible_id=responsible)

        class Vendor(SimpleNamespace):
            def __len__(self):
                return 1

        vendor = Vendor(
            id=19, state='approved', valid_until=date(2026, 11, 30),
            company_ids=[store.company_id],
        )

        class CooperationModel:
            def search(self, _domain):
                self.domain = _domain
                return [cooperation]

        cooperation_model = CooperationModel()
        followup_service = self.env['ydental.followup.service']
        with (
            patch.object(type(service), '_model', autospec=True, return_value=cooperation_model),
            patch.object(type(self.env['ydental.access.service']), '_is_group_manager', return_value=True),
            patch.object(type(followup_service), '_queue_supplier_expiry', autospec=True) as queue_expiry,
        ):
            service._queue_vendor_expiry(vendor)

        queue_expiry.assert_called_once()
        args = queue_expiry.call_args.args
        self.assertEqual(args[1:], (vendor, store, '2026-11-30T00:00:00', responsible.id))
        self.assertNotIn('ydental_store_id', [term[0] for term in cooperation_model.domain])

    def test_vendor_cooperation_is_store_scoped_within_shared_company(self):
        service = self.env['ydental.lab.service']
        company = SimpleNamespace(id=8)
        store1 = SimpleNamespace(id=31, company_id=company)
        store2 = SimpleNamespace(id=32, company_id=company)
        vendor = SimpleNamespace(
            id=19, state='approved',
            valid_until=fields.Date.context_today(service) + timedelta(days=1),
            company_ids=[company],
        )

        class VendorModel:
            def browse(self, vendor_id):
                return SimpleNamespace(exists=lambda: vendor if vendor_id == vendor.id else False)

        class CooperationModel:
            def __init__(self):
                self.store_ids = []

            def search(self, domain, limit=1):
                self.store_ids.append(next(term[2] for term in domain if term[0] == 'ydental_store_id'))
                active = next(term[2] for term in domain if term[0] == 'active')
                vendor_id = next(term[2] for term in domain if term[0] == 'ydental_vendor_id')
                if self.store_ids[-1] == store1.id and active and vendor_id == vendor.id:
                    return SimpleNamespace(id=93)
                return None

        cooperation_model = CooperationModel()
        models = {'vendor': VendorModel(), 'cooperation': cooperation_model}
        with patch.object(type(service), '_model', side_effect=lambda entity: models[entity]):
            self.assertIs(service._check_vendor_id(vendor.id, store1, None), vendor)
            with self.assertRaises(AccessError):
                service._check_vendor_id(vendor.id, store2, None)

        self.assertEqual(cooperation_model.store_ids, [store1.id, store2.id])

    def test_vendor_qualification_and_cooperation_use_real_store_scoped_records(self):
        root = self.env['base'].sudo().env
        company = root.company
        key = secrets.token_hex(8)
        stores = root['ydental.access.store'].create([
            {'name': 'S11 actual cooperation A ' + key, 'company_id': company.id,
             'ydental_timezone': 'UTC'},
            {'name': 'S11 actual cooperation B ' + key, 'company_id': company.id,
             'ydental_timezone': 'UTC'},
        ])
        users = [new_test_user(
            root,
            name='S11 actual cooperation warehouse ' + str(index),
            login='s11_actual_cooperation_' + str(index) + '_' + key,
            groups='ydental_base.ydental_base_group_user',
            company_id=company.id,
            company_ids=[fields.Command.set([company.id])],
        ) for index in (1, 2)]
        manager = new_test_user(
            root,
            name='S11 actual cooperation manager ' + key,
            login='s11_actual_cooperation_manager_' + key,
            groups='ydental_base.ydental_base_group_user,ydental_access.ydental_group_manager',
            company_id=company.id,
            company_ids=[fields.Command.set([company.id])],
        )
        manager_access = root['ydental.access.service'].with_user(manager)
        manager_access = manager_access._bind(manager_access._session_for_key('s11-actual-cooperation-' + key))
        for store, user in zip(stores, users):
            manager_access._join(user.id, store.id)
            manager_access._grant(user.id, store.id, {'medical': 'write', 'warehouse': 'write'})

        partner = root['res.partner'].create({'name': 'S11 synthetic laboratory ' + key})
        vendor = root['ydental.lab.vendor'].with_user(manager).create({
            'partner_id': partner.id,
            'company_ids': [fields.Command.set([company.id])],
            'category': 'denture',
            'qualification_reference': 'S11 synthetic qualification ' + key,
            'qualification_evidence': base64.b64encode(b'S11 synthetic evidence').decode(),
            'qualification_evidence_name': 'synthetic-evidence.txt',
            'valid_until': fields.Date.to_string(fields.Date.context_today(root['ydental.lab.service']) + timedelta(days=90)),
        })
        vendor.action_approve()
        self.assertEqual(vendor.state, 'approved')
        self.assertEqual(vendor.reviewed_by_id, manager)

        store_accesses = []
        for store, user in zip(stores, users):
            access = root['ydental.access.service'].with_user(user)
            session = access._session_for_key('s11-actual-cooperation-' + key + '-' + str(store.id))
            access = access._bind(session)
            access._switch(store.id)
            store_accesses.append(access._bind(session))

        cooperation1 = store_accesses[0].env['ydental.lab.cooperation'].create({
            'ydental_vendor_id': vendor.id,
        })
        self.assertEqual(cooperation1.ydental_store_id, stores[0])
        self.assertEqual(cooperation1.responsible_id, users[0])
        store1_service = store_accesses[0].env['ydental.lab.service']
        store2_service = store_accesses[1].env['ydental.lab.service']
        self.assertEqual(store1_service._access(write=True), stores[0])
        self.assertEqual(store2_service._access(write=True), stores[1])
        self.assertEqual(store_accesses[0].env['ydental.lab.service']._check_vendor_id(
            vendor.id, stores[0], None), vendor)
        with self.assertRaises(AccessError):
            store_accesses[0].env['ydental.lab.service']._check_vendor_id(vendor.id, stores[1], None)

        cooperation2 = store_accesses[1].env['ydental.lab.cooperation'].create({
            'ydental_vendor_id': vendor.id,
        })
        self.assertEqual(cooperation2.ydental_store_id, stores[1])
        self.assertEqual(cooperation2.responsible_id, users[1])
        self.assertEqual(
            store_accesses[0].env['ydental.lab.cooperation'].search([
                ('ydental_vendor_id', '=', vendor.id),
            ]), cooperation1,
        )
        self.assertEqual(
            store_accesses[1].env['ydental.lab.cooperation'].search([
                ('ydental_vendor_id', '=', vendor.id),
            ]), cooperation2,
        )
        self.assertEqual(store2_service._check_vendor_id(vendor.id, stores[1], None), vendor)

    def test_vendor_expiry_for_store_writer_only_queues_current_store(self):
        service = self.env['ydental.lab.service']
        store1 = SimpleNamespace(id=31, company_id=SimpleNamespace(id=8))
        store2 = SimpleNamespace(id=32, company_id=SimpleNamespace(id=8))
        responsible1 = SimpleNamespace(id=44)
        responsible2 = SimpleNamespace(id=45)
        cooperations = [
            SimpleNamespace(ydental_store_id=store1, responsible_id=responsible1),
            SimpleNamespace(ydental_store_id=store2, responsible_id=responsible2),
        ]

        class Vendor(SimpleNamespace):
            def __len__(self):
                return 1

        vendor = Vendor(
            id=19, state='approved', valid_until=date(2026, 11, 30),
            company_ids=[store1.company_id],
        )

        class CooperationModel:
            def search(self, domain):
                store_id = next((value for field, operator, value in domain if field == 'ydental_store_id'), None)
                return [cooperation for cooperation in cooperations
                        if store_id is None or cooperation.ydental_store_id.id == store_id]

        access = self.env['ydental.access.service']
        followup_service = self.env['ydental.followup.service']
        with (
            patch.object(type(service), '_model', autospec=True, return_value=CooperationModel()),
            patch.object(type(access), '_is_group_manager', return_value=False),
            patch.object(type(access), '_scope', return_value=SimpleNamespace(ydental_store_id=store2)),
            patch.object(type(followup_service), '_queue_supplier_expiry', autospec=True) as queue_expiry,
        ):
            service._queue_vendor_expiry(vendor)

        queue_expiry.assert_called_once()
        args = queue_expiry.call_args.args
        self.assertEqual(args[1:], (vendor, store2, '2026-11-30T00:00:00', responsible2.id))

    def test_additional_rework_cannot_dispatch_before_terms_are_frozen(self):
        service = self.env['ydental.lab.service']
        store = SimpleNamespace(id=31)
        order = SimpleNamespace(
            id=999999,
            state='draft', ydental_parent_order_id=SimpleNamespace(id=12),
            ydental_rework_kind='additional', ydental_additional_terms_frozen=False,
            ydental_no_patient_fee_confirmed=False,
            invalidate_recordset=lambda _fields: None,
        )
        with (
            patch.object(type(service), '_get_order', return_value=order),
            patch.object(type(service), '_check_vendor', side_effect=AssertionError('dispatch must stop before vendor action')),
            self.assertRaises(UserError),
        ):
            service._send(store, 19)

    def test_rework_opens_additional_child_cycle_without_confirming_or_billing_it(self):
        service = self.env['ydental.lab.service']
        store = SimpleNamespace(id=31)
        vendor = SimpleNamespace(id=41, partner_id=SimpleNamespace(id=51))
        product = SimpleNamespace(id=61)
        patient = SimpleNamespace(id=71)
        source_event = SimpleNamespace(id=81)
        source_document = SimpleNamespace(id=91)
        source_fee = SimpleNamespace(id=101)
        responsible = SimpleNamespace(id=111)
        order = SimpleNamespace(
            id=999999, name='Synthetic first cycle', state='available', ydental_rework_kind='additional',
            ydental_exception_reason='Synthetic patient-requested repair', ydental_vendor_id=vendor,
            ydental_product_id=product, ydental_patient_id=patient, ydental_source_event_id=source_event,
            ydental_source_document_id=source_document, ydental_source_fee_id=source_fee,
            ydental_lot_id=SimpleNamespace(id=121), ydental_quantity=1,
            ydental_teeth=[24], ydental_material='synthetic ceramic', ydental_shade='A2',
            ydental_instructions='synthetic repair', ydental_responsible_id=responsible,
            ydental_planned_at='2026-10-19 12:00:00', ydental_external_mode='physical',
            ydental_internal_code='SYNTH-LAB-19',
        )
        child = SimpleNamespace(id=20, ydental_rework_no=1, ydental_rework_kind='additional')
        captured = {}

        class OrderModel:
            def _new(self, values):
                captured.update(values)
                return child

        class InventoryService:
            def _lab_workflow_move(self, source, reason):
                captured['inventory_source'] = source
                captured['inventory_reason'] = reason
                return {'id': 131}

        inventory_event_model = self.env['ydental.inventory.event']

        class InventoryEvent(SimpleNamespace):
            def exists(self):
                return self

        inventory_event = InventoryEvent(id=131)
        followup_service = self.env['ydental.followup.service']
        with (
            patch.object(type(service), '_warehouse_write', return_value=store),
            patch.object(type(service), '_get_order', return_value=order),
            patch.object(type(service), '_check_vendor'),
            patch.object(type(service), '_model', return_value=OrderModel()),
            patch.object(type(service), '_record_action', return_value={'state': 'rework_returned'}),
            patch.object(type(service), '_event'),
            patch.object(type(service), '_audit'),
            patch.object(type(self.env['ydental.inventory.service']), '_lab_workflow_move', new=InventoryService._lab_workflow_move),
            patch.object(type(inventory_event_model), 'sudo', return_value=inventory_event_model),
            patch.object(type(inventory_event_model), 'browse', return_value=inventory_event),
            patch.object(type(followup_service), '_supersede_lab_followup'),
        ):
            result = service._rework(store, order.id)

        self.assertEqual(captured['ydental_rework_kind'], 'additional')
        self.assertEqual(captured['ydental_parent_order_id'], order.id)
        self.assertEqual(result['repair_order_id'], child.id)
        self.assertNotIn('ydental_additional_terms_frozen', captured)
        self.assertNotIn('ydental_additional_performance_recorded', captured)

    def test_initial_order_cannot_smuggle_additional_charge_terms(self):
        service = self.env['ydental.lab.service']
        with self.assertRaises(AccessError):
            service._order_identity(1, {'ydental_additional_service_id': 77}, SimpleNamespace(id=31))

    def test_additional_service_performance_requires_frozen_terms_and_active_child_cycle(self):
        service = self.env['ydental.lab.service']
        store = SimpleNamespace(id=31)
        order = SimpleNamespace(
            ydental_parent_order_id=SimpleNamespace(id=12), ydental_rework_kind='additional',
            ydental_additional_terms_frozen=False, ydental_additional_performance_recorded=False,
            state='processing',
        )
        with (
            patch.object(type(service), '_get_order', return_value=order),
            self.assertRaises(UserError),
        ):
            service._confirm_charge_performed(store, 19)

    def test_terms_approval_freezes_only_the_matching_native_cycle_source(self):
        service = self.env['ydental.lab.service']
        bridge = self.env['ydental.lab.charge.service']
        store = SimpleNamespace(id=31)
        patient = SimpleNamespace(id=52)
        catalog = SimpleNamespace(id=77, active=True)

        class MutableRecord(SimpleNamespace):
            def _save(self, values):
                self.__dict__.update(values)

        class Charge(SimpleNamespace):
            def __len__(self):
                return 1

        order = MutableRecord(
            id=999999, state='draft', ydental_parent_order_id=SimpleNamespace(id=12),
            ydental_rework_kind='additional', ydental_additional_terms_frozen=False,
            ydental_additional_service_id=catalog, ydental_additional_service_quantity=1,
            ydental_additional_consent_reference='consent-ref-synthetic-001',
            ydental_additional_terms_reason='Synthetic additional repair service',
            ydental_no_patient_fee_declaration=False,
            ydental_no_patient_fee_confirmed=False,
            ydental_patient_id=patient,
            invalidate_recordset=lambda _fields: None,
        )
        charge = Charge(
            _name='ydental.lab.charge', id=91, state='terms_confirmed',
            ydental_order_id=order, ydental_store_id=store, ydental_patient_id=patient,
            ydental_catalog_id=catalog, ydental_quantity=1,
            ydental_currency_id=SimpleNamespace(id=1),
        )
        with (
            patch.object(type(service), '_get_order', return_value=order),
            patch.object(type(service), '_event'),
            patch.object(type(service), '_audit'),
            patch.object(type(bridge), '_prepare_terms', autospec=True, return_value=charge) as prepare,
        ):
            result = service._approve_charge_terms(store, order.id)

        self.assertTrue(order.ydental_additional_terms_frozen)
        self.assertEqual(result['charge_source_id'], charge.id)
        self.assertEqual(prepare.call_args.args[1:], (
            order, catalog.id, 1, 'consent-ref-synthetic-001', 'Synthetic additional repair service'))

    def test_performance_confirmation_records_explicit_utc_and_evidence_once(self):
        service = self.env['ydental.lab.service']
        bridge = self.env['ydental.lab.charge.service']
        store = SimpleNamespace(id=31)
        patient = SimpleNamespace(id=52)
        catalog = SimpleNamespace(id=77)

        class MutableRecord(SimpleNamespace):
            def _save(self, values):
                self.__dict__.update(values)

        class Charge(SimpleNamespace):
            def __len__(self):
                return 1

        class Charges(list):
            @property
            def state(self):
                return self[0].state

        performed_at = fields.Datetime.now() - timedelta(minutes=2)
        charge = Charge(
            _name='ydental.lab.charge', id=91, state='terms_confirmed',
            ydental_order_id=None, ydental_store_id=store, ydental_patient_id=patient,
            ydental_catalog_id=catalog, ydental_quantity=1,
        )
        order = MutableRecord(
            id=19, state='processing', ydental_parent_order_id=SimpleNamespace(id=12),
            ydental_rework_kind='additional', ydental_additional_terms_frozen=True,
            ydental_additional_performance_recorded=False,
            ydental_additional_performed_at=performed_at,
            ydental_additional_performance_evidence_reference='vendor-work-proof-synthetic-01',
            ydental_additional_service_id=catalog, ydental_additional_service_quantity=1,
            ydental_patient_id=patient, ydental_charge_ids=Charges([charge]),
        )
        charge.ydental_order_id = order
        performed_charge = Charge(**{**charge.__dict__, 'state': 'performed'})
        with (
            patch.object(type(service), '_get_order', return_value=order),
            patch.object(type(service), '_event'),
            patch.object(type(service), '_audit'),
            patch.object(type(bridge), '_confirm_performed', autospec=True, return_value=performed_charge) as confirm,
        ):
            result = service._confirm_charge_performed(store, order.id)

        self.assertTrue(order.ydental_additional_performance_recorded)
        self.assertEqual(result['state'], 'performed')
        self.assertEqual(confirm.call_args.args[1], order.ydental_charge_ids)
        self.assertEqual(confirm.call_args.args[2], performed_at.replace(tzinfo=UTC).isoformat())
        self.assertEqual(confirm.call_args.args[3], 'vendor-work-proof-synthetic-01')

from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestLaboratoryGuards(TransactionCase):
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
        ):
            result = service._receive(store, 12)
        self.assertEqual(result['state'], 'received')
        record_action.assert_called_once()
        self.assertEqual(record_action.call_args.args[:2], (order, 'received'))
        self.assertEqual(record_action.call_args.kwargs['values']['state'], 'received')

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
                return [cooperation]

        followup_service = self.env['ydental.followup.service']
        with (
            patch.object(type(service), '_model', autospec=True, return_value=CooperationModel()),
            patch.object(type(followup_service), '_queue_supplier_expiry', autospec=True) as queue_expiry,
        ):
            service._queue_vendor_expiry(vendor)

        queue_expiry.assert_called_once()
        args = queue_expiry.call_args.args
        self.assertEqual(args[1:], (vendor, store, '2026-11-30T00:00:00', responsible.id))

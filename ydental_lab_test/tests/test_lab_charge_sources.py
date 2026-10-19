from types import SimpleNamespace
from unittest.mock import patch

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestLabChargeSources(TransactionCase):
    def test_charge_facts_cannot_be_created_or_changed_by_orm(self):
        with self.assertRaises(AccessError):
            self.env['ydental.lab.charge'].create({})
        with self.assertRaises(AccessError):
            self.env['ydental.lab.charge'].browse(1).write({'state': 'performed'})
        with self.assertRaises(AccessError):
            self.env['ydental.lab.charge'].browse(1).unlink()

    def test_charge_operation_is_registered_only_inside_settlement_service(self):
        service = self.env['ydental.settlement.service']
        self.assertIn('bill_lab_charge', service._extension_operation_handlers())
        self.assertIn('credit_lab_charge', service._extension_operation_handlers())
        with self.assertRaises(ValidationError):
            service._operate('bill_lab_charge', {'unexpected': True}, 'invalid-charge-op-key')
        with self.assertRaises(ValidationError):
            service._operate('credit_lab_charge', {'unexpected': True}, 'invalid-charge-credit-key')

    def test_medical_writer_without_price_authority_cannot_freeze_terms(self):
        service = self.env['ydental.lab.charge.service']
        store = SimpleNamespace(id=987654)
        order = SimpleNamespace(
            _name='ydental.lab.order', id=987654321, ydental_additional_terms_frozen=False,
            invalidate_recordset=lambda: None,
        )
        access = self.env['ydental.access.service']

        def reject_price(category, operation, write=False):
            if category == 'price' and operation == 'write' and write:
                raise AccessError('access_denied: Price authority is required.')
            raise AssertionError('unexpected access check')

        with (patch.object(type(service), '_authorized_order', return_value=store),
              patch.object(type(access), '_check', side_effect=reject_price),
              self.assertRaises(AccessError)):
            service._prepare_terms(order, 123, 1.0, 'SYNTHETIC-CONSENT', 'Synthetic additional service')

    def test_missing_charge_is_rejected_before_native_invoice_creation(self):
        service = self.env['ydental.settlement.service']
        store = SimpleNamespace(id=987654)
        invoice_count = self.env['account.move'].sudo().search_count([])
        missing_id = max(self.env['ydental.lab.charge'].sudo().search([]).ids or [0]) + 1000000
        with (patch.object(type(service), '_access', return_value=store),
              patch.object(type(service), '_config', return_value=object()),
              self.assertRaises(AccessError)):
            service._bill_lab_charge([missing_id], 'Synthetic source rejection test')
        self.assertEqual(self.env['account.move'].sudo().search_count([]), invoice_count)

    def test_native_settlement_source_constraint_keeps_source_type_exclusive(self):
        self.env.cr.execute("""
            SELECT count(*) FROM ydental_settlement_source
            WHERE (ydental_fee_id IS NOT NULL)::integer +
                  (ydental_lab_charge_id IS NOT NULL)::integer +
                  (ydental_lab_charge_adjustment_id IS NOT NULL)::integer != 1
        """)
        self.assertEqual(self.env.cr.fetchone()[0], 0)

    def test_credit_limit_allows_multiple_linked_revisions_but_never_overcredits(self):
        service = self.env['ydental.settlement.service']

        class Currency:
            @staticmethod
            def round(value):
                return round(value, 2)

            @staticmethod
            def compare_amounts(left, right):
                return (round(left, 2) > round(right, 2)) - (round(left, 2) < round(right, 2))

        currency = Currency()
        self.assertEqual(service._validate_lab_charge_credit_total(currency, 13.75, [2.25, 3.00], 1.50), 6.75)
        with self.assertRaises(UserError):
            service._validate_lab_charge_credit_total(currency, 13.75, [8.00, 4.25], 1.51)

    def test_charge_bridge_schema_links_frozen_s05_charge_and_each_credit_revision(self):
        charge = self.env['ydental.lab.charge']
        adjustment = self.env['ydental.lab.charge.adjustment']
        source = self.env['ydental.settlement.source']
        for field_name in ('ydental_catalog_id', 'ydental_price_id', 'ydental_price_snapshot_id',
                           'ydental_quantity', 'ydental_unit_price', 'ydental_amount',
                           'ydental_performed_by_id', 'ydental_performed_at', 'ydental_settlement_source_id'):
            self.assertIn(field_name, charge._fields)
        for field_name in ('ydental_charge_id', 'ydental_revision', 'ydental_amount',
                           'ydental_credit_move_id', 'ydental_settlement_source_id'):
            self.assertIn(field_name, adjustment._fields)
        self.assertIn('ydental_lab_charge_id', source._fields)
        self.assertIn('ydental_lab_charge_adjustment_id', source._fields)
        # Separate source types are persisted on their own immutable native links;
        # credit records retain their parent charge and revision identity.
        self.assertEqual(source._fields['ydental_lab_charge_id'].comodel_name, 'ydental.lab.charge')
        self.assertEqual(source._fields['ydental_lab_charge_adjustment_id'].comodel_name,
                         'ydental.lab.charge.adjustment')

    def test_native_settlement_summary_keeps_credit_revision_visible(self):
        service = self.env['ydental.settlement.service']
        adjustment = SimpleNamespace(id=57, name='Synthetic cycle credit revision 2')
        source = SimpleNamespace(
            ydental_lab_charge_id=False,
            ydental_lab_charge_adjustment_id=adjustment,
            ydental_original_amount=-4.25,
            ydental_price_version='S05:12/credit:v2',
        )
        line = service._bill_summary_line(source)
        self.assertEqual(line, {
            'name': adjustment.name,
            'lab_charge_adjustment_id': adjustment.id,
            'amount': -4.25,
            'price_version': 'S05:12/credit:v2',
        })

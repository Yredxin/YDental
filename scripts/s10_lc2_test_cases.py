"""Offline tests of financial observation gates and read-only preservation.

Synthetic files only: no Odoo import, database, network or browser.
"""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from s10_lc2_cases import Actor, assert_main_preserved, reader_levels, verify_d, verify_upgrade


class Cases(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='lc2-case-offline-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = {'payment_id': 1, 'invoice_id': 1, 'refund_id': 1, 'execute_key': 'synthetic-key',
                       'company_id': 1, 'currency_id': 2, 'store_id': 3}
        self.rows = {
            'ydental_settlement_payment': [{'id': 1, 'ydental_payment_id': 1, 'ydental_amount': 6,
                                            'ydental_store_id': 3, 'ydental_currency_id': 2}],
            'ydental_settlement_refund': [{'id': 1, 'ydental_state': 'done', 'ydental_amount': 2,
                'ydental_currency_id': 2, 'ydental_payment_id': 1, 'ydental_native_payment_id': 2,
                'ydental_credit_note_id': 2, 'ydental_requester_id': 5, 'ydental_approver_id': 6}],
            'account_payment': [dict(id=1, amount=6, payment_type='inbound', company_id=1, currency_id=2,
                                     is_reconciled=True, state='reconciled'),
                                dict(id=2, amount=2, payment_type='outbound', company_id=1, currency_id=2,
                                     is_reconciled=True, state='reconciled')],
            'account_move': [dict(id=1, state='posted', amount_total=6, amount_residual=0, company_id=1,
                                  currency_id=2, move_type='out_invoice'),
                             dict(id=2, state='posted', amount_total=2, amount_residual=0, company_id=1,
                                  currency_id=2, move_type='out_refund')],
            'ydental_treatment_fee': [{'id': 1}],
            'account_partial_reconcile': [dict(id=1, amount=6, company_id=1, debit_currency_id=2, credit_currency_id=2),
                                          dict(id=2, amount=2, company_id=1, debit_currency_id=2, credit_currency_id=2)],
            'ydental_settlement_receipt': [{'id': 1, 'ydental_operation': 'refund_execute', 'ydental_key': 'synthetic-key'}],
            'ydental_access_audit': [{'id': 1, 'ydental_event': 'settlement.refund.execute', 'ydental_target_id': 1}],
        }

    def observation(self, rows):
        directory = self.root / ('observation-' + str(len(list(self.root.iterdir()))))
        directory.mkdir(mode=0o700)
        for table, records in rows.items():
            (directory / (table + '.rows.jsonl')).write_text(''.join(
                json.dumps({'server_json_text': json.dumps(row)}) + '\n' for row in records))
        return directory

    def test_independent_complete_refund_observation_is_same_currency_net_four(self):
        result = verify_d(self.observation(self.rows), self.source, state='done', actual_refund=2)
        self.assertEqual((result['received'], result['actually_refunded'], result['net_received']), (6, 2, 4))
        self.assertEqual(result['currency_id'], 2)
        self.assertFalse(result['real_gateway_claimed'])

    def test_unknown_state_never_authorizes_retry_from_amount_alone(self):
        self.rows['ydental_settlement_refund'][0]['ydental_state'] = 'approved'
        with self.assertRaisesRegex(RuntimeError, 'STATE_NOT_VERIFIED'):
            verify_d(self.observation(self.rows), self.source, state='done', actual_refund=2)

    def test_duplicate_outbound_or_receipt_cannot_be_idempotency_success(self):
        for table in ['account_payment', 'ydental_settlement_receipt']:
            rows = copy.deepcopy(self.rows)
            rows[table].append(dict(rows[table][-1], id=99))
            with patch('s10_lc2_cases.stop'), self.assertRaisesRegex(RuntimeError, 'NO_RETRY_ALLOWED'):
                verify_d(self.observation(rows), self.source, state='done', actual_refund=2)

    def test_same_numbers_different_currency_and_missing_reconcile_are_rejected(self):
        for field, value in [('currency_id', 99), ('is_reconciled', False)]:
            rows = copy.deepcopy(self.rows)
            rows['account_payment'][0][field] = value
            with patch('s10_lc2_cases.stop'), self.assertRaises(RuntimeError):
                verify_d(self.observation(rows), self.source, state='done', actual_refund=2)

    def test_failed_recovery_has_zero_outbound_credit_and_native_pointer(self):
        self.rows['ydental_settlement_refund'][0].update(ydental_state='failed', ydental_native_payment_id=None, ydental_credit_note_id=None)
        self.rows['account_payment'] = self.rows['account_payment'][:1]
        self.rows['account_move'] = self.rows['account_move'][:1]
        self.rows['account_partial_reconcile'] = self.rows['account_partial_reconcile'][:1]
        result = verify_d(self.observation(self.rows), self.source, state='failed', actual_refund=0)
        self.assertEqual(result['native_outbound_count'], 0)

    def test_old_queue_drift_is_detected_even_if_money_and_v4_unchanged(self):
        doc = {'id': 1, 'ydental_version': 4, 'state': 'confirmed', 'write_uid': 7, 'ydental_editor_uid': 7}
        rows = {'ydental_queue_lease': [{'id': 8, 'ydental_active': True}], 'ydental_clinical_document': [doc]}
        before = self.observation(rows)
        changed = copy.deepcopy(rows)
        changed['ydental_queue_lease'][0]['ydental_active'] = False
        after = self.observation(changed)
        (before / 'sealed-index.json').write_text(json.dumps({'files': [{'path': name + '.rows.jsonl'} for name in rows]}))
        with patch('s10_lc2_cases.stop'), self.assertRaisesRegex(RuntimeError, 'PRESERVATION_FAILURE'):
            assert_main_preserved(before, after)

    def test_reader_restore_uses_store_baseline_not_nested_store_as_category(self):
        fixture = {'initial_levels': [[1, [['settlement', 'read'], ['export', 'write'], ['medical', 'none']]]]}
        self.assertEqual(reader_levels(fixture), {'settlement': 'read', 'export': 'write', 'medical': 'none'})

    def test_real_settlement_action_keeps_multivalue_invoice_list_and_unknown_not_success(self):
        actor = object.__new__(Actor)
        actor.revision, actor.csrf, actor.connection = 3, 'synthetic-csrf', 'synthetic-connection'
        class Observation:
            commit_observation = 'UNKNOWN'
        class Client:
            def request(self, *args, **kwargs):
                self.seen = kwargs
                return Observation()
        actor.client = Client()
        result = actor.action('settlement', 'refund_execute', {'refund_id': 1, 'proof': 'synthetic', 'actual_utc': '2026-10-17T00:00:00Z'},
                              case='D-LOST-REFUND-2', key='synthetic-key', discard=True, retry=True)
        self.assertEqual(result.commit_observation, 'UNKNOWN')
        self.assertEqual(actor.client.seen['form']['refund_id'], 1)
        self.assertNotIn('payload', actor.client.seen['form'])
        self.assertTrue(actor.client.seen['retry_manifest'])


if __name__ == '__main__':
    unittest.main()

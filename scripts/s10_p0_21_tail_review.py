"""Offline explanation of already captured final rows, not a runtime gate repair.

No database/Odoo/HTTP imports. Keeps Web BLOCKED and the missing response body
UNKNOWN even when the positive payment/original facts can be proved separately.
"""
from collections import Counter
from decimal import Decimal
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / '.local/s10-p0-21'
OUT = ROOT / 'docs/evidence/s10-p0-21'
RUN = ROOT / '.local/ydental_s10_test_20261017050000_21b0cafe'


def read(path):
    return json.loads(path.read_text())


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, sort_keys=True)
        stream.write('\n')


def main():
    before = read(PRIVATE / 'original-security-independent-RO-rows.json')
    final = read(PRIVATE / 'final-RO-rows.json')
    diff = read(PRIVATE / 'Web-to-readonly-tail-full-diff.json')
    b, a = before['tables'], final['tables']
    chain, multi = read(RUN / 'b-chain.json'), read(RUN / 'b-multi.json')
    checks = []

    def check(label, ok):
        checks.append({'label': label, 'PASS': bool(ok)})

    def byid(table, ident):
        return next(row for row in a[table] if row['id'] == ident)

    def money(value):
        return Decimal(str(value))

    additions = [row for row in a['ydental_settlement_payment'] if row['id'] not in
                 {old['id'] for old in b['ydental_settlement_payment']}]
    check('exactly_one_Web_payment', len(additions) == 1)
    payment = additions[0]
    check('ordinary_frontdesk_3_alipay_same_patient_store',
          payment['create_uid'] == payment['ydental_cashier_id'] == multi['frontdesk_id']
          and payment['ydental_patient_id'] == multi['patient_id']
          and payment['ydental_store_id'] == multi['store_id']
          and money(payment['ydental_amount']) == 3 and payment['ydental_channel'] == 'alipay')
    native = byid('account_payment', payment['ydental_payment_id'])
    move = byid('account_move', native['move_id'])
    check('Web_native_payment_posted_3', move['state'] == 'posted' and money(native['amount']) == 3
          and native['create_uid'] == multi['frontdesk_id'])
    lines = [row for row in a['account_move_line'] if row['move_id'] == move['id']]
    check('Web_native_double_entry_balanced', len(lines) == 2
          and sum(money(row['balance']) for row in lines) == 0
          and sum(money(row['debit']) for row in lines) == 3)
    target = multi['new_invoice_ids'][3]
    old = next(row for row in b['account_move'] if row['id'] == target)
    new = byid('account_move', target)
    check('only_selected_invoice_200_to_197', money(old['amount_residual']) == 200
          and money(new['amount_residual']) == 197 and new['payment_state'] == 'partial')
    partials = [r for r in a['account_partial_reconcile'] if r['id'] not in
                {old['id'] for old in b['account_partial_reconcile']}]
    check('exact_Web_partial_3_for_selected_invoice', len(partials) == 1
          and money(partials[0]['amount']) == 3
          and byid('account_move_line', partials[0]['debit_move_id'])['move_id'] == target
          and byid('account_move_line', partials[0]['credit_move_id'])['move_id'] == move['id'])
    changed_existing_invoices = [r for r in diff if r['table'] == 'account_move' and r['before_count']]
    check('all_other_existing_invoices_exact', len(changed_existing_invoices) == 1
          and changed_existing_invoices[0]['physical_key'][2] == target
          and set(changed_existing_invoices[0]['columns']) ==
          {'amount_residual', 'amount_residual_signed', 'payment_state', 'write_date', 'write_uid'})
    protected = ('ydental_treatment_', 'ydental_inventory_', 'stock_', 'ydental_intake_',
                 'ydental_patient', 'ydental_clinical_', 'ydental_settlement_source',
                 'ydental_settlement_refund', 'ydental_settlement_close', 'ydental_settlement_correction')
    check('all_stored_clinical_source_price_stock_refund_close_rows_exact_across_Web',
          not any(row['table'].startswith(protected) for row in diff))
    check('existing_groups_memberships_companies_and_permissions_exact_across_Web',
          not any(row['table'].startswith(('res_groups', 'res_company', 'res_users_res_groups',
              'ydental_access_membership', 'ydental_access_permission')) for row in diff))
    originals = a['ydental_settlement_bill_original']
    check('two_linked_originals_for_same_invoice_patient_store', len(originals) == 2
          and all(r['invoice_id'] == chain['invoice_id'] and r['patient_id'] == chain['patient_id']
                  and r['store_id'] == chain['store_id'] for r in originals)
          and originals[0]['version'] == 1 and originals[1]['version'] == 2
          and originals[1]['previous_id'] == originals[0]['id'])
    check('old_original_record_exact', originals[0] == b['ydental_settlement_bill_original'][0])
    original_files = []
    for row in originals:
        attachment = byid('ir_attachment', row['attachment_id'])
        raw = (RUN / 'data/filestore' / final['database'] / attachment['store_fname']).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        check('original_%s_private_attachment_checksum' % row['id'],
              digest == row['pdf_sha256'] and not attachment['public'] and not attachment['access_token']
              and attachment['res_model'] == 'ydental.settlement.bill.original'
              and attachment['res_id'] == row['id'] and attachment['company_id'] == row['company_id'])
        original_files.append({'original_id': row['id'], 'version': row['version'], 'bytes': len(raw),
                               'sha256': digest, 'attachment_id': attachment['id']})
    old_attachment = next(row for row in b['ir_attachment'] if row['id'] == originals[0]['attachment_id'])
    check('old_attachment_record_exact', old_attachment == byid('ir_attachment', old_attachment['id']))
    downloaded = (PRIVATE / 'UI-retained-original.pdf').read_bytes()
    check('actual_UI_download_same_saved_original_SHA', hashlib.sha256(downloaded).hexdigest() == originals[0]['pdf_sha256'])
    for move in a['account_move']:
        if move['state'] == 'posted':
            check('final_posted_move_%s_balanced' % move['id'],
                  sum(money(row['balance']) for row in a['account_move_line'] if row['move_id'] == move['id']) == 0)
    audits = [r['after'][0] for r in diff if r['table'] == 'ydental_access_audit']
    result = {'offline_only': True, 'checks': checks, 'original_files': original_files,
              'Web_delta_tables': dict(Counter(row['table'] for row in diff)),
              'Web_audits': [{key: row[key] for key in ('id', 'ydental_event', 'ydental_user_id', 'ydental_target_model', 'ydental_target_id')} for row in audits],
              'Web_overall': 'BLOCKED', 'thumbnail_response_body': 'UNKNOWN_NOT_CAPTURED',
              'no_runtime_contract_repair_or_retry': True, 'upgrade': 'NOT_RUN_AFTER_WEB_FAIL',
              'document_completion': 'NOT_RUN_AFTER_ACQUIRE_GATE_FAIL',
              'post_document_change_original_retake': 'NOT_RUN',
              'positive_UI_scope': 'actual pay3, explicit v2 original generation, saved v1 link click/SHA only',
              'S10_stage': 'BLOCKED'}
    save(OUT / 'offline-tail-review.json', result)
    assert all(row['PASS'] for row in checks), [row['label'] for row in checks if not row['PASS']]
    print(json.dumps({'offline_checks': len(checks), 'exit_code': 0, 'Web_and_stage_remain': 'BLOCKED'}))


if __name__ == '__main__':
    main()

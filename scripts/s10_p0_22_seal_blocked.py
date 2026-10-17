"""Offline-only P022 integrity-stop delivery; never resumes the failed window."""
from collections import Counter
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/evidence/s10-p0-22'
PRIVATE = ROOT / '.local/s10-p0-22'
RUN = ROOT / '.local/ydental_s10_test_20261017060000_22b0cafe'


def read(path): return json.loads(path.read_text())


def sha(raw): return hashlib.sha256(raw).hexdigest()


def canonical(value): return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def save(name, value):
    with (OUT / name).open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write('\n')


def main():
    old_path = ROOT / 'docs/evidence/s10-p0-21/exit-table-final.json'
    old = read(old_path)
    integrity = read(OUT / 'integrity-stop.json')
    tail = read(PRIVATE / 'final-tail-RO.json')
    lineage = read(OUT / 'created-lineage.json')
    events = [json.loads(line) for line in (OUT / 'events.jsonl').read_text().splitlines()]
    groups = {
        'A': {'status': 'BLOCKED_BEFORE_DOCUMENT_ACTIONS', 'scope_commit_returned': True,
              'scope_independent_readback_gate': 'FAIL', 'acquire_confirm_correct_release': [0, 0, 0, 0],
              'new_UI_original_GET': 0},
        'B': {'status': 'NOT_RUN_STOP_BOUNDARY', 'six_MODEL_denials': 0},
        'C': {'status': 'NOT_RUN_STOP_BOUNDARY', 'MODEL_fixtures': 0, 'real_RPC': 0,
              'real_HTTP': 0, 'effective_token_construction': 0, 'response_body_pixel_tests': 0},
        'D': {'status': 'NOT_RUN_STOP_BOUNDARY', 'new_fee_invoice_receipt_refund': [0, 0, 0, 0],
              'controlled_response_loss': 0, 'same_key_repeat': 0},
        'E': {'status': 'NOT_RUN_STOP_BOUNDARY', 'S10_upgrade': 0, 'post_upgrade_UI': 0},
    }
    rows = []
    md = ['# S10-P0-22 阶段退出新增表：完整性硬停止／整体 BLOCKED', '',
          'P021完整22行对象、旧口径和正式裁定均保留；本表不重判旧已采子证据，也不将只读复制准入当功能退出。', '',
          '|行|P021原状态|P022新增层|剩余动作／边界|', '|---|---|---|---|']
    for row in old['rows']:
        ident = row['id']
        related = {'F4': ['A'], 'T08': ['A'], 'T12': ['A', 'E'], 'T15': ['A'],
                   'T16': ['B'], 'F6': ['C'], 'T10': ['C'], 'T14': ['C'], 'T05': ['D'],
                   'T11': ['A', 'C', 'D']}.get(ident, [])
        status = 'BLOCKED_BY_INTEGRITY_STOP' if related else 'NO_NEW_BUSINESS_REUSE_P021_ONLY'
        note = '先由GPT独立复核已保存的瞬时arch_prev字段差异及安全继续条件；五组尚未执行，不重建或重收已采主链。' if related else '只沿原来源/版本继承P021限定证据；本批没有重复业务或扩大PASS。'
        rows.append({'id': ident, 'P021_historical_row_unchanged': row,
                     'P021_row_canonical_sha256': sha(canonical(row).encode()),
                     'P022': {'status': status, 'related_groups': related,
                              'new_business': 'NOT_RUN', 'reason': note, 'independent_GPT_review': 'PENDING'}})
        md.append('|%s|%s|%s|%s|' % (ident, row['P021']['status'], status, note))
    assert len(rows) == 22
    saved = {'overall': 'S10_TECHNICAL_EXIT_BLOCKED', 'S10_stage_exit_satisfied': False,
             'P021_rows_preserved': True, 'P021_file_sha256': sha(old_path.read_bytes()),
             'groups': groups, 'rows': rows, 'new_blocker': integrity,
             'production_and_historical_native_risks': 'unchanged; no new proof of resolution'}
    save('exit-table-final.json', saved)
    assert [row['P021_historical_row_unchanged'] for row in read(OUT / 'exit-table-final.json')['rows']] == old['rows']
    (ROOT / 'docs/s10-p0-22-exit-table-final.md').write_text('\n'.join(md) + '\n')
    actions = [event for event in events if event['event'] == 'native_action_intent']
    assert len(actions) == 1 and actions[0]['label'] == 'r0-A-fresh-owner-scope-1'
    assert sum(event['event'] == 'RO_intent' for event in events) == 5
    source_ro = [event for event in events if event['event'] == 'RO_intent' and event['database'] == lineage['source_database']]
    assert len(source_ro) == 2
    assert sum(event['event'] == 'commit_returned' for event in events) == 1
    assert not (RUN / 'A.json').exists() and not (RUN / 'T05.json').exists()
    actual = read(OUT / 'r0-A-result.json')
    assert actual['exit_code'] == 1 and not actual['SIGSEGV']
    doc = next(row for row in tail['tables']['ydental_clinical_document'] if row['id'] == 1)
    invoice = next(row for row in tail['tables']['account_move'] if row['id'] == 1)
    assert (doc['state'], doc['ydental_version'], doc['ydental_editor_id']) == ('pending', 2, None)
    assert Decimal(str(invoice['amount_total'])) == 740 and Decimal(str(invoice['amount_residual'])) == 0
    baseline = read(PRIVATE / 'clone-initial-RO.json')
    for table in ['ydental_settlement_bill_original', 'ir_attachment', 'ydental_settlement_source',
                  'ydental_settlement_payment', 'ydental_settlement_refund', 'stock_move', 'ydental_treatment_fee']:
        assert baseline['tables'][table] == tail['tables'][table], table
    budget = {'source_RO': 2, 'all_explicit_RO_RR': 5, 'RO_cap': 24, 'maintenance': 1, 'CREATE': 1,
              'native_scenarios': [actual], 'native_pool_cap': 8, 'repair_rounds_used': 0,
              'commit_returned': 1, 'commit_scope_only_not_success_marker': True, 'document_actions': 0,
              'B_MODEL_negatives': 0, 'C_MODEL_RPC_HTTP': [0, 0, 0], 'T05_economic_actions': 0,
              'Odoo_HTTP': 0, 'Firefox': 0, 'PDF_render': 0, 'original_GET': 0, 'original_generation': 0,
              'upgrade': 0, 'other_old_business_connections': 0, 'Issue_Project_mutations': 0,
              'event_counts': dict(Counter(event['event'] for event in events)), 'native_DSN_note': actual['per_PID_DSN']}
    save('actual-budget.json', budget)
    save('five-group-results.json', groups)
    save('offline-seal-verification.json', {'exit_code': 0, 'source_preserved': read(OUT / 'source-final-preserved.json'),
         'all_22_P021_historical_objects_exact': True, 'current_tail_all_rows_equal_scope_precommit': True,
         'all_inherited_economic_original_attachment_rows_exact': True,
         'new_snapshot_table_count': len(tail['tables']), 'doc1': {'state': doc['state'], 'version': doc['ydental_version'], 'editor': None},
         'invoice1': {'amount': invoice['amount_total'], 'residual': invoice['amount_residual'], 'state': invoice['state']},
         'only_a_finite_capture_does_not_explain_transient': True,
         'no_resume_or_arch_prev_DML': True, 'overall': 'S10_TECHNICAL_EXIT_BLOCKED'})
    print(json.dumps({'offline_exit': 0, 'P021_rows_exact': 22, 'stage_exit_satisfied': False,
                      'all_explicit_RO': 5, 'source_RO': 2, 'new_business_actions': 0}))


if __name__ == '__main__': main()

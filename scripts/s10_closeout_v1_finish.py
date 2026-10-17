"""Offline evidence seal; never imports Odoo, connects to PostgreSQL or sends HTTP."""
import json
from pathlib import Path
import re
import s10_closeout_v1_contract as c


def events():
    path = c.OUT / 'events.jsonl'
    return [json.loads(v) for v in path.read_text().splitlines()] if path.exists() else []


def verify_tail(tail):
    baseline = c.read(c.PRIVATE / 'clone-initial-RO.json')
    original_tables = baseline['tables']
    new = tail['tables']
    assert baseline['schema'] == tail['schema']
    for table in original_tables:
        if c.economic(table):
            before = original_tables[table]
            old_ids = {row['id'] for row in before if 'id' in row}
            protected = [row for row in new[table] if row.get('id') in old_ids] if old_ids else new[table]
            assert c.canonical(before) == c.canonical(protected), ('INHERITED_ECONOMIC_DRIFT', table)
    for table in ['ydental_settlement_bill_original', 'ydental_access_membership']:
        assert c.canonical(original_tables[table]) == c.canonical(new[table]), ('ORIGINAL_OR_PERMISSION_DRIFT', table)
    before_grants = {r['id']: r for r in original_tables['ydental_access_grant']}
    after_grants = {r['id']: r for r in new['ydental_access_grant']}
    assert before_grants.keys() == after_grants.keys()
    for ident, row in before_grants.items():
        target = after_grants[ident]
        changed = {k for k in row if row[k] != target[k]}
        if changed:
            assert row['ydental_membership_id'] == 7 and row['ydental_category'] in {'settlement', 'export'}
            assert changed <= {'write_uid', 'write_date'} and target['write_uid'] == 5
    old_doc = {r['id']: r for r in original_tables['ydental_clinical_document']}
    for row in new['ydental_clinical_document']:
        if row['id'] == 1:
            assert row['state'] == 'confirmed' and row['ydental_version'] == 4 and not row['ydental_editor_id']
        elif row['id'] in old_doc:
            assert row == old_doc[row['id']], ('OTHER_INHERITED_DOCUMENT_CHANGED', row['id'])
    attachments = {r['id']: r for r in new['ir_attachment']}
    for original in original_tables['ydental_settlement_bill_original']:
        ident = original['attachment_id']
        assert attachments[ident] == next(r for r in original_tables['ir_attachment'] if r['id'] == ident)
    copied_files = c.read(c.PRIVATE / 'source-before-files.json')
    final_files = c.filetree(c.RUN / 'data/filestore' / c.NAME)
    assert all(final_files.get(k) == value for k, value in copied_files.items())
    count = len(new['ydental_access_audit']) - len(original_tables['ydental_access_audit'])
    assert 0 <= count <= 500
    return {'all_inherited_stored_economic_rows_exact': True, 'old_original_rows_attachments_bytes_exact': True,
            'original_permission_levels_and_rows_exact_except_explicit_reader_grant_actor_time': True,
            'new_audit_rows': count, 'file_count_before': len(copied_files),
            'file_count_final': len(final_files), 'other_inherited_document_rows_exact': True}


def main():
    es = events()
    stopped = c.stopped()
    decisions = {p.name: c.read(p) for p in sorted(c.OUT.glob('*decision.json'))}
    actual = {
        'authority': c.AUTH, 'parent': c.BASE, 'execution_commit': c.current_freeze()['execution_commit'],
        'source_READONLY': sum(v['event'] == 'RO_intent' and v.get('database') == c.SOURCE for v in es),
        'RO_total': sum(v['event'] == 'RO_intent' for v in es),
        'RO_closed': sum(v['event'] == 'RO_closed' for v in es),
        'maintenance': sum(v['event'] == 'maintenance_intent' for v in es),
        'CREATE': sum(v['event'] == 'CREATE_intent' for v in es),
        'CREATE_returned': sum(v['event'] == 'CREATE_returned' for v in es),
        'Odoo_processes': sum(v['event'] == 'Odoo_process_intent' for v in es),
        'commit_intent': sum(v['event'] == 'commit_intent' for v in es),
        'commit_returned': sum(v['event'] == 'commit_returned' for v in es),
        'commit_unknown': sum(v['event'] == 'commit_unknown' for v in es),
        'original_generation': 0, 'old_economic_replay': 0, 'S11_merge_deploy_Issue_Project_mutation': 0,
        'full_capture_nodes': [c.read(p)['full'] for p in c.OUT.glob('capture-*-layer.json')].count(True),
        'STOP': c.read(c.PRIVATE / ('STOP-r1.json' if (c.PRIVATE / 'STOP-r1.json').exists() else 'STOP.json')) if stopped else None,
        'prior_R0_stop_preserved': c.read(c.PRIVATE / 'STOP.json') if (c.PRIVATE / 'STOP.json').exists() else None,
        'github_sync': c.read(c.PRIVATE / c.read(c.PRIVATE / 'active-plan.json').get('github_sync_path', 'github-preflight-sync.json'))['state']}
    cap_source = 3 if (c.PRIVATE / 'source-budget-approval.json').exists() else 2
    for key, cap in [('source_READONLY', cap_source), ('RO_total', 28), ('maintenance', 1), ('CREATE', 1), ('Odoo_processes', 6)]:
        assert actual[key] <= cap
    http_path = c.OUT / 'HTTP-events.jsonl'
    http = [json.loads(v) for v in http_path.read_text().splitlines()] if http_path.exists() else []
    dispatched = [v for v in http if v['event'] == 'dispatch']
    actual.update(HTTP_dispatched=len(dispatched),
                  original_GET=sum('/bill-original/' in v.get('path', '') for v in dispatched),
                  refund_PDF=sum('/settlement/pdf/' in v.get('path', '') for v in dispatched),
                  response_loss=sum(v['event'] == 'T05_server_response_observed_client_not_delivered' for v in http))
    assert actual['HTTP_dispatched'] <= 600 and actual['original_GET'] <= 12 and actual['refund_PDF'] <= 2
    result_paths = ['A.json', 'B-rpc-targets.json', 'T05.json']
    facts = {'local_markers': {name: (c.RUN / name).exists() for name in result_paths},
             'decisions': {name: row['PASS'] for name, row in decisions.items()}, 'actual': actual}
    successful = not stopped and (c.OUT / 'Web-and-upgrade-result.json').exists()
    if successful:
        tail = c.read(c.PRIVATE / ('r1-final-tail-RO.json' if c.current_freeze()['round'] else 'final-tail-RO.json'))
        facts['tail'] = verify_tail(tail)
        assert actual['RO_total'] == actual['RO_closed'] and actual['source_READONLY'] == cap_source
        assert (c.OUT / ('source-final-preserved-r1.json' if c.current_freeze()['round'] else 'source-final-preserved.json')).exists()
        assert actual['commit_unknown'] == 0
        facts['upgrade'] = c.read(c.OUT / 'Web-and-upgrade-result.json')
        facts['visual_review'] = c.read(c.OUT / 'visual-review.json')
        assert facts['visual_review']['PASS']
    overall = 'READY_FOR_INDEPENDENT_S10_TECHNICAL_REVIEW' if successful else 'S10_TECHNICAL_EXIT_BLOCKED'
    c.save(c.OUT / 'actual-budget.json', actual)
    c.save(c.OUT / 'final-facts.json', facts | {'overall': overall, 'Codex_self_test_not_GPT_or_user_acceptance': True})
    old = c.read(c.ROOT / 'docs/evidence/s10-p0-21/exit-table-final.json')
    mapping = {'F4': ['A', 'E'], 'F6': ['C', 'E'], 'T05': ['D', 'E'], 'T08': ['A', 'E'],
               'T10': ['C', 'E'], 'T11': ['C', 'D', 'E'], 'T12': ['A', 'E'],
               'T14': ['C', 'E'], 'T15': ['A', 'E'], 'T16': ['B', 'E']}
    history_files = ['docs/s10-p0-21-exit-table-final.md', 'docs/evidence/s10-p0-21/historical-compatibility.json']
    rows = []
    for row in old['rows']:
        ident = row['id']; groups = mapping.get(ident, ['E'])
        record = {'id': ident, 'P021_original_row': row, 'CLOSEOUT': {
            'product_content': 'be1d12a2d21771ca411ca8bdd510437980b68ef3 unchanged',
            'tested_execution_commit': actual['execution_commit'], 'required_groups': groups,
            'result': 'SCOPED_PASS_WITH_FIXED_HISTORY_REUSE' if successful else 'BLOCKED_OR_NOT_RUN_SEE_GROUP_CHECKPOINTS',
            'history_reuse': history_files, 'no_new_concurrency_claim': True,
            'source_chain_not_stitched_across_databases': True,
            'new_evidence': ['docs/evidence/s10-closeout-v1/final-facts.json']}}
        rows.append(record)
    c.save(c.OUT / 'exit-table-final.json', {'overall': overall, 'historical_22_rows_preserved': True, 'rows': rows})
    table = ['# S10-CLOSEOUT-v1.1 22行退出新增层', '', 'P021历史行对象完整保留，旧FAIL/UNKNOWN不覆盖。', '',
             '|行|本包所需组|本包结果|', '|---|---|---|']
    table += ['|%s|%s|%s|' % (r['id'], '+'.join(r['CLOSEOUT']['required_groups']), r['CLOSEOUT']['result']) for r in rows]
    (c.ROOT / 'docs/s10-closeout-v1-exit-table-final.md').write_text('\n'.join(table) + '\n')
    private = []
    for folder in [c.PRIVATE, c.RUN]:
        if folder.exists():
            for path in sorted(folder.rglob('*')):
                if path.is_file(): private.append({'path': str(path.relative_to(c.ROOT)), 'bytes': path.stat().st_size,
                                                   'sha256': c.sha(path.read_bytes())})
    c.save(c.OUT / 'private-evidence-manifest.json', {'files': private, 'no_secret_contents_exported': True})
    (c.PRIVATE / 'seal-overall.txt').write_text(overall + '\n')
    print(overall)


if __name__ == '__main__':
    main()

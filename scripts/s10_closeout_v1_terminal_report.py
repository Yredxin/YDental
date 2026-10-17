"""Offline terminal receipt: preserve actual partial groups and all 22 historic rows.

Does not reconnect, repair snapshots, import Odoo, or resume the crashed process.
"""
from decimal import Decimal
import json
import s10_closeout_v1_contract as c


def main():
    # Only this window's acquired evidence, not P023/P024 or another measurement.
    rows = {}
    raw_path = c.PRIVATE/'capture-0045-server-rows.jsonl'
    count = 0
    for line in raw_path.open():
        item = json.loads(line)
        assert c.sha(item['server_json_text'].encode()) == item['server_sha256']
        value = json.loads(item['server_json_text'], parse_float=Decimal)
        value.update(__physical_table__=item['physical_table'], __physical_oid__=item['physical_oid'])
        # Compare the serializer's exact number-to-string representation without fixing the file.
        rows.setdefault(item['requested_table'], []).append(json.loads(c.canonical(value)))
        count += 1
    disk = c.read(c.PRIVATE/'r2-final-tail-RO.json')
    raw_snapshot = dict(disk, tables=rows)
    changes, index = c.diff(raw_snapshot, disk)
    c.save(c.PRIVATE/'terminal-tail-acquired-layer-differences.json', changes)
    c.save(c.OUT/'terminal-tail-acquired-layer-index.json', {
        'one_acquired_capture_not_independent_measurements': True, 'raw_rows': count,
        'server_raw_line_hashes_match': True, 'stored_file_not_repaired_or_accepted_as_baseline': True,
        'changes': index, 'raw_schema_not_independently_rebuilt': True,
        'save_time_in_memory_object_unavailable': True,
        'conclusion': 'Saved raw-row/file comparison is limited; original in-memory/save-readback failure remains unresolved.'})
    initial = c.read(c.PRIVATE/'clone-initial-RO.json')
    last = c.read(c.PRIVATE/'r2-A-correct-committed-RO.json')
    protected = dict(initial, tables={name: initial['tables'][name] for name in last['tables']})
    differences, difference_index = c.diff(protected, last)
    c.save(c.PRIVATE/'terminal-last-valid-vs-initial-full-diff.json', differences)
    c.save(c.OUT/'terminal-last-valid-vs-initial-index.json', {
        'last_valid_checkpoint': 'r2-A-correct-committed', 'economic_changes': [r for r in difference_index if r['economic']],
        'all_changes': difference_index, 'not_a_valid_final_tail_claim': True})
    assert not [row for row in differences if row['economic']]
    doc = next(r for r in last['tables']['ydental_clinical_document'] if r['id'] == 1)
    versions = [r for r in last['tables']['ydental_clinical_version'] if r['ydental_document_id'] == 1]
    old_versions = {r['id'] for r in initial['tables']['ydental_clinical_version']}
    facts = {'state': doc['state'], 'version': doc['ydental_version'], 'writer': doc['write_uid'],
             'editor': doc['ydental_editor_id'], 'session': doc['ydental_session_id'],
             'new_versions': [{k: r[k] for k in ['id','ydental_number','ydental_kind','ydental_author_id','ydental_previous_id','ydental_reason']}
                              for r in versions if r['id'] not in old_versions]}
    files = c.filetree(c.RUN/'data/filestore'/c.NAME)
    inherited_files = c.read(c.PRIVATE/'source-before-files.json')
    assert files == inherited_files
    c.save(c.OUT/'terminal-verified-partial-facts.json', {
        'last_valid_independent_checkpoint': facts, 'old_economic_storage_exact_at_last_valid_checkpoint': True,
        'clone_filestore_198_files_current_bytes_exact': True,
        'old_original_rows_at_last_valid_checkpoint_exact': initial['tables']['ydental_settlement_bill_original'] == last['tables']['ydental_settlement_bill_original'],
        'release': 'CALL_DISPATCHED_NO_COMMIT_NO_SUCCESS_MARKER; native crashed during evidence save',
        'current_editor_after_crash_not_asserted': True,
        'final_tail': 'SERIALIZED_READBACK_MISMATCH; NOT_VALID_BASELINE',
        'final_source': c.read(c.OUT/'source-final-preserved-r2.json')})
    groups = {
        'A': {'result': 'PARTIAL_COMMITTED_THEN_NATIVE_SIGSEGV', 'completed': ['acquire', 'confirm v3', 'wording-only correct v4'],
              'uncompleted': ['committed release', 'real UI retake of original'],
              'evidence': ['r2-A-acquire-checkpoint.json','r2-A-confirm-checkpoint.json','r2-A-correct-checkpoint.json','r2-prepare-all-result.json']},
        'B': {'result': 'NOT_RUN_AFTER_NATIVE_STOP', 'uncompleted': ['six MODEL write/unlink', 'six actual RPC write/unlink']},
        'C': {'result': 'NOT_RUN_AFTER_NATIVE_STOP', 'uncompleted': ['original/attachment permission matrix and bodies']},
        'D': {'result': 'NOT_RUN_AFTER_NATIVE_STOP', 'new_upstream_or_money_actions': 0, 'uncompleted': ['D admission', 'failed recovery', 'lost response verification and deduplication']},
        'E': {'result': 'NOT_RUN_AFTER_NATIVE_STOP', 'upgrade': 0, 'uncompleted': ['S10-only upgrade and affected UI regression']}}
    c.save(c.OUT/'five-group-actual-results.json', groups)
    old = c.read(c.ROOT/'docs/evidence/s10-p0-21/exit-table-final.json')
    required = {'F4':['A','E'],'F6':['C','E'],'T05':['D','E'],'T08':['A','E'],
                'T10':['C','E'],'T11':['C','D','E'],'T12':['A','E'],'T14':['C','E'],'T15':['A','E'],'T16':['B','E']}
    result_rows = []
    text = ['# S10-CLOSEOUT v1.1 最终22行退出表', '',
            'S10技术退出仍BLOCKED。P021历史行全文保存在对应JSON中，不重判旧FAIL/UNKNOWN；本包新增独立层。', '',
            '|行|正式需求|已有成果/复用理由|本包实测与待补|最终版本/结论|', '|---|---|---|---|---|']
    for row in old['rows']:
        ident = row['id']; history = row['P021']; needs = required.get(ident, ['E'])
        scope = ('A仅confirm/correct已提交；release与原件UI未完成；E未运行' if 'A' in needs else
                 '、'.join(needs)+'未运行，具体见五组结果')
        reuse = history['actual_assertion'] + ' 产品未变，来源独立，限P021正式裁定采纳范围。'
        record = {'id': ident, 'P021_original_row': row, 'requirement': row['P020_historical_row_unchanged']['requirement_verbatim_current'],
                  'CLOSEOUT': {'required_groups': needs, 'group_results': {g: groups[g] for g in needs},
                               'history_reuse_reason': reuse, 'remaining': scope,
                               'final_tested_execution_commit': c.current_freeze()['execution_commit'],
                               'product_unchanged': True, 'result': 'EXIT_BLOCKED; HISTORY_SCOPED_RESULTS_RETAINED',
                               'no_new_concurrency_or_network_PASS': True}}
        result_rows.append(record)
        text.append('|%s|%s|%s|%s|00e6c4a1 / BLOCKED|' % (ident, record['requirement'].replace('|','/'), reuse.replace('|','/'), scope))
    c.save(c.OUT/'exit-table-reviewed-terminal.json', {'overall':'S10_TECHNICAL_EXIT_BLOCKED', 'rows':result_rows,
        'formal_P021_ruling':'https://github.com/Yredxin/YDental/issues/34#issuecomment-6230102263',
        'history_22_rows_unchanged': True, 'not_GPT_acceptance': True})
    (c.ROOT/'docs/s10-closeout-v1-exit-table-terminal.md').write_text('\n'.join(text)+'\n')
    print('TERMINAL_PARTIAL_FACTS_AND_22_ROWS_SAVED; NO_DB_OR_BUSINESS')


if __name__ == '__main__': main()

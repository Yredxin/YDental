"""Offline artifact verification only. No database, Odoo, browser or HTTP imports."""
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/evidence/s10-p0-10'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((OUT / name).read_text())


def verify():
    pre = read('preflight.json')
    assert sha(ROOT/'scripts/s10_p0_10_readonly.py')==pre['script_sha256']
    check = read('preflight-api-readback.json')
    assert check['verbatim_equal'] and check['script_sha256']==pre['script_sha256']
    assert check['body_length']==len(check['body']) and check['body_sha256']==hashlib.sha256(check['body'].encode()).hexdigest()
    assert check['preflight_sha256']==sha(OUT/'preflight.json')
    for f in pre['historical_inputs']:
        assert sha(ROOT/f['path'])==f['sha256']
    for path in ROOT.glob('scripts/s10_p0_10_*.py'):
        ast.parse(path.read_text())
    coverage = read('coverage.json')
    old = json.loads((ROOT/'docs/evidence/s10-gap-01/coverage.json').read_text())
    assert len(coverage['rows'])==22
    assert [r['old_gap01_row'] for r in coverage['rows']]==old['rows']
    assert {r['id'] for r in coverage['rows']}=={f'F{i}' for i in range(1,7)}|{f'T{i:02d}' for i in range(1,17)}
    assert Counter(r['gap02_row_status'] for r in coverage['rows'])=={'SCOPED_ACCEPTED':7,'PARTIAL':14,'BLOCKED':1}
    assert not coverage['full_pass_rows']
    for row in coverage['rows']:
        assert row['historical_status']==row['gap02_row_status']
        assert row['original_assertion'] and row['historical_codex_gpt_commit_db']
        for e in row['historical_codex_gpt_commit_db']+row['delta_evidence']:
            assert len(e['commit'])==40 and e['codex_receipt_comment_id'] and e['gpt_comment_id']
        assert row['funds_or_inventory_write_for_remaining'] and row['next_budget_note']
    assert set(coverage['p0_02_to_09_delta_sources'])=={f'P0-{n:02d}' for n in range(2,10)}
    for e in coverage['p0_02_to_09_delta_sources'].values():
        for f in e['files']:
            assert sha(ROOT/f['path'])==f['sha256']
    sql = read('read-only-sql.json')
    assert len(sql['sources'])==5 and sql['source_attempts']==5
    assert set(s['oid'] for s in sql['sources'].values())=={2100324,2056451,2100285,2100301,2100310}
    assert all(x==0 for x in sql['budget'].values())
    for src in sql['sources'].values():
        assert src['status']=='READONLY_SOURCE_MATCH' and src['rolled_back'] and src['closed']
        assert src['transaction_read_only']=='on' and src['transaction_isolation']=='repeatable read'
        assert not src['baseline_mismatches']
    after=json.loads((ROOT/'docs/evidence/s10-p0-09/business-before-after.json').read_text())['after_all_643_table_signatures']
    p009=sql['sources']['P009']
    assert len(after)==643 and p009['table_signatures']==after
    line=read('same-source-lineage.json')
    assert len(line['clone_edges'])==2 and all(e['clone_exact_38_match'] for e in line['clone_edges'])
    assert line['stable_after_payment_31_match'] and line['p009_after_checks']['mutex_revision']==244
    assert all(line['R3_P009_protected_signature_equal'].values())
    assert all(x['matches'] and x['pdf_magic'] for x in line['R3_existing_pdf_files'])
    fields=read('field-lineage.json')['W5_four_fees']
    assert sum(x['amount'] for x in fields)==740 and [x['quantity'] for x in fields[2:]]==[4,2]
    assert len({x['oid'] for x in fields})==1 and all(x['patient_id']==x['store_id']==x['company_id']==1 for x in fields)
    proposals=read('p0-11-proposals.json')
    assert not proposals['authorized'] and [p['rank'] for p in proposals['proposals']]==['PRIMARY','BACKUP']
    assert proposals['original_reprint_candidate']=='P0_11_NOT_AUTHORIZABLE_PENDING_SOURCE'
    for f in read('source-entry-review.json')['files']:
        assert sha(ROOT/f['path'])==f['sha256']
    for name in ('gap02-coverage','same-source-feasibility'):
        report=(ROOT/f'docs/s10-p0-10-{name}-report.md').read_text()
        for row in coverage['rows']:
            assert f"| {row['id']} |" in report
        assert report.count('| T12 |')==1 and 'P0_11_NOT_AUTHORIZABLE_PENDING_SOURCE' in report
        assert 'final_audit NOT_RUN' in report and 'BLOCKED' in report
    # Every existing tracked file is untouched; this batch consists solely of new allowed files.
    diff=subprocess.check_output(['git','diff','--name-only',pre['base']],cwd=ROOT,text=True).splitlines()
    assert all(p.startswith(('scripts/s10_p0_10_','docs/s10-p0-10-','docs/evidence/s10-p0-10/')) for p in diff)
    result={'result':'PASS','rows':22,'old_rows_deep_equal':True,'status_counts':dict(Counter(r['gap02_row_status'] for r in coverage['rows'])),
            'FULL_PASS':0,'fixed_historical_files':len(pre['historical_inputs']),'readonly_sources':5,
            'p009_after_643_exact':True,'clone_edges_38_exact':2,'W5_stable_tables':31,'R3_existing_pdf_hashes':8,
            'proposals':2,'all_zero_execution_budgets':sql['budget'],'sql_script_unchanged_after_checkpoint':True,
            'verification_scope':'STATIC_ARTIFACT_CHECK_ONLY; no new SQL, browser, Odoo or business simulation',
            'no_new_business_test':True}
    (OUT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':
    verify()

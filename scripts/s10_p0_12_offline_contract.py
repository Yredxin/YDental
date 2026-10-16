"""Audit the P0-12 connection/proof contract using files only.

This entry point cannot connect to PostgreSQL, create a clone, start Odoo or
Firefox, or submit a business request. It records an offline planning blocker.
Historical signatures remain historical evidence, not a new source snapshot.
"""
import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / '.local/s10-p0-12-6210207391'
OUT = ROOT / 'docs/evidence/s10-p0-12'
BASE = '0b64b1b143ca99dac0404d202d410a782d08421f'
CORE = 'f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb'
AUTH = 6210207391
BRANCH = 'codex/s10-settlement-finance-r1-20261013'
SOURCE = 'ydental_s10_test_20261015073500_e50f4a71'
ZERO_BUDGET = {
    'W5_SQL_CONNECTION': 0, 'TARGET_SQL_CONNECTION': 0,
    'MAINTENANCE_SQL_CONNECTION': 0, 'CREATE': 0, 'ODOO_HTTP_LAUNCH': 0,
    'FIREFOX_LAUNCH': 0, 'NATIVE_LOGIN_POST': 0, 'STORE_SWITCH_POST': 0,
    'CLINICAL_GET': 0, 'ACQUIRE_POST': 0, 'CONFIRM_POST': 0,
    'RELEASE_POST': 0, 'HEARTBEAT_POST': 0, 'OTHER_BUSINESS_POST': 0,
    'PDF': 0, 'FUNDS_STOCK_WRITE': 0, 'ODOO_SHELL_UPGRADE_INSTALL_INIT_TEST': 0,
    'DIRECT_BUSINESS_ORM': 0, 'SUDO': 0,
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_text())


def save(name, value):
    with (OUT / name).open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2)
        stream.write('\n')


def git(*args, cwd=ROOT):
    return subprocess.check_output(['git', '-C', str(cwd), *args], text=True).strip()


def comments(name):
    return [comment for page in read(PRIVATE / (name + '.json')) for comment in page]


def projection(value):
    body = value['body']
    return {
        'id': value['id'], 'url': value['html_url'],
        'created_at': value['created_at'], 'updated_at': value['updated_at'],
        'body_characters': len(body), 'body_utf8_bytes': len(body.encode()),
        'body_sha256': sha(body.encode()), 'title': body.splitlines()[0],
        'minimized': value.get('minimized'),
    }


def main():
    os.umask(0o077)
    assert git('rev-parse', 'HEAD') == BASE
    assert git('branch', '--show-current') == BRANCH
    assert git('remote', 'get-url', 'origin') == 'https://github.com/Yredxin/YDental.git'
    remote = git('ls-remote', 'origin', 'refs/heads/' + BRANCH).split()[0]
    assert remote == BASE
    assert git('rev-parse', 'HEAD', cwd=ROOT.parent) == CORE
    assert not git('status', '--porcelain', '--untracked-files=no', cwd=ROOT.parent)
    assert not git('diff', '--name-only') and not git('diff', '--cached', '--name-only')
    for line in git('status', '--porcelain').splitlines():
        assert line[:2] == '??' and line[3:].startswith((
            'scripts/s10_p0_12_', 'docs/s10-p0-12-', 'docs/evidence/s10-p0-12/'))
    c23, c34 = comments('comments23'), comments('comments34')
    issues = {str(n): read(PRIVATE / ('issue' + str(n) + '.json')) for n in (23, 34, 35)}
    assert len(c23) == issues['23']['comments'] == 3
    assert len(c34) == issues['34']['comments'] == 217
    assert issues['34']['state'] == issues['35']['state'] == 'open'
    assert issues['35']['comments'] == 0
    assert len({c['id'] for c in c34}) == len(c34) and c34[-1]['id'] == AUTH
    assert [c['id'] for c in c34 if 'S10-P0-12' in c['body'].splitlines()[0]] == [AUTH]
    by_id = {c['id']: c for c in c34}
    assert all(i in by_id for i in (6209310360, 6209454407, 6209987413, 6210167613, AUTH))
    assert read(PRIVATE / 'auth.json')['body'] == by_id[AUTH]['body']
    auth = by_id[AUTH]['body']
    clauses = {
        'one_strict_source_connection': '一次独立W5严格READ ONLY / REPEATABLE READ只读SQL连接',
        'source_after_proof': '旧W5全程永久只读/前后全表SHA不变',
        'source_connection_budget': 'W5只读SQL连接≤1',
        'clone_from_source': '从旧W5只读模板',
    }
    assert all(text in auth for text in clauses.values())
    for key, expected in (('commit-base', BASE), ('commit-core', CORE)):
        assert read(PRIVATE / (key + '.json'))['sha'] == expected
    base_commit = read(PRIVATE / 'commit-base.json')
    assert [p['sha'] for p in base_commit['parents']] == ['0c972e1949191d62d84536f987a40f26dba57e03']

    # Audit the existing candidate's source-connection consumption without
    # importing or running any of its entry points.
    candidate = ROOT / 'scripts/s10_p0_11_control.py'
    tree = ast.parse(candidate.read_text())
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    assert "dbname=ro.NAME" in ast.get_source_segment(candidate.read_text(), functions['clone'])
    assert "snapshot(ro.NAME)" in ast.get_source_segment(candidate.read_text(), functions['clone'])
    assert "snapshot(ro.NAME)" in ast.get_source_segment(candidate.read_text(), functions['run'])

    history_paths = [
        'docs/evidence/s10-p0-11/read-only-sql.json',
        'docs/evidence/s10-p0-11/preflight.json',
        'docs/evidence/s10-p0-11/eligibility-corrected.json',
        'docs/evidence/s10-p0-10/read-only-sql.json',
        'docs/evidence/s10-e2e-w5-ro1-r1/read-only-sql.json',
        'scripts/s10_p0_11_control.py', 'scripts/s10_p0_11_readonly.py',
    ]
    historical = {path: {'sha256': sha((ROOT / path).read_bytes()),
                         'bytes': (ROOT / path).stat().st_size} for path in history_paths}
    sql_history = read(ROOT / history_paths[0])
    assert historical[history_paths[0]]['sha256'] == '3506708c4c88d10d555a4ca5d3074a52294db3e68a7dfa21a21d8711b50a93ee'
    assert len(sql_history['all_table_signatures']) == 643
    eligibility = read(ROOT / history_paths[2])
    assert len(eligibility['checks']) == 25 and all(eligibility['checks'].values())
    links = eligibility['facts']['explicit_source_fee_links']
    assert {r['source_id']: r['fee_id'] for r in links} == {1: 4, 2: 3, 3: 2, 4: 1}

    OUT.mkdir(parents=True, exist_ok=True)
    save('github-start.json', {
        'captured_at': datetime.now(timezone.utc).isoformat(),
        'issues': {n: projection(v) | {'state': v['state'], 'comment_count': v['comments']}
                   for n, v in issues.items()},
        'comments23': [projection(c) for c in c23],
        'comments34': [projection(c) for c in c34],
        'latest_authorization': AUTH, 'existing_p012_preflight_or_delivery': False,
        'local_head': BASE, 'remote_head': remote, 'core_head': CORE,
        'commit_base_parents': [p['sha'] for p in base_commit['parents']],
        'fixed_commit_api_sha_match': True, 'branch': BRANCH,
        'origin': 'https://github.com/Yredxin/YDental.git',
        'raw_api_responses_private_only': True,
    })
    save('historical-references.json', {
        'scope': 'fixed historical files only; no current W5 SQL or medical-content access',
        'files': historical, 'historical_public_tables': 643,
        'historical_eligibility_checks': 25,
        'historical_source_fee_links': links,
        'current_source_identity_or_signature_verified': False,
    })
    save('offline-contract.json', {
        'authorization': AUTH, 'authorization_body_sha256': sha(auth.encode()),
        'status': 'BLOCKED_PREFLIGHT',
        'reason': 'STRICT_SINGLE_W5_CONNECTION_AND_POST_WEB_SOURCE_FULL_TABLE_PROOF_NOT_JOINTLY_PLANNABLE',
        'evidence_level': 'offline contract analysis; not a PostgreSQL execution failure',
        'exact_authorization_fragments': clauses,
        'analysis': [
            'A separate maintenance CREATE backend conflicts with a still-connected W5 read-only backend.',
            'Closing the sole W5 connection before CREATE leaves no connection budget for an independently observed post-Web W5 full-table snapshot.',
            'Keeping one REPEATABLE READ snapshot does not provide a fresh post-Web observation.',
            'PostgreSQL exempts the CREATE caller itself from the source-backend check. Using that exception would require executing DDL on the W5 connection outside its strictly read-only transaction contract.',
            'Clone signatures and filesystem seals do not substitute for a new source-database full-table observation.',
            'No source connection, CREATE, executable Web plan, or execution checkpoint was attempted.',
        ],
        'primary_sources': [
            {'url': 'https://www.postgresql.org/docs/current/sql-createdatabase.html',
             'supports': 'CREATE outside transaction blocks; other template sessions prevent cloning'},
            {'url': 'https://www.postgresql.org/docs/current/sql-set-transaction.html',
             'supports': 'REPEATABLE READ snapshot semantics; CREATE disallowed in read-only transactions'},
            {'url': 'https://github.com/postgres/postgres/blob/REL_17_STABLE/src/backend/commands/dbcommands.c#L1271',
             'supports': 'the current CREATE caller is exempt; other source backends are checked'},
        ],
        'candidate_p011_source_connections_if_run_after_its_capture': 4,
        'p011_entry_points_executed': False,
        'execution_checkpoint': 'NOT_PUBLISHED_OFFLINE_PLANNING_BLOCKED',
        'freeze_or_budget_relaxation': False,
        'script_sha256': sha(Path(__file__).read_bytes()),
        'actual_budget': ZERO_BUDGET,
    })
    save('verification.json', {
        'authorization': AUTH, 'base': BASE, 'core': CORE,
        'result': 'BLOCKED_PREFLIGHT_OFFLINE_CONTRACT', 'actual_budget': ZERO_BUDGET,
        'clinical_confirm': 'NOT_RUN', 'current_w5_sql': 'NOT_RUN',
        'source_before_after_table_comparison': 'NOT_RUN',
        'target_before_after_table_comparison': 'NOT_RUN',
        'new_version3': 'NOT_RUN', 'odoo_exit': 'NOT_STARTED',
        'firefox_exit': 'NOT_STARTED', 'execution_preflight_api_readback': 'NOT_RUN',
        'current_source_personnel_eligibility': 'NOT_RUN',
        'historical_evidence_not_promoted_to_current_pass': True,
        'product_acl_core_issue_project_changes': 0,
        'p011_or_other_historical_files_changed': 0,
        'next_batch_or_pdf_started': False,
        'continuing_blocks': ['S10_STAGE', 'PRODUCTION', 'T12',
            'NATIVE_SIGSEGV_ROOT_CAUSE_UNKNOWN', 'W4_METADATA_STOP',
            'W5_OLD_BROWSER_EXIT1_FINAL_AUDIT_NOT_RUN', 'ORIGINAL_PDF_SAME_SOURCE_UNAVAILABLE'],
    })
    print(json.dumps({'status': 'BLOCKED_PREFLIGHT', 'SQL_CREATE_HTTP_FIREFOX_POST': 0}))


if __name__ == '__main__':
    main()

"""P0-05 hard-stop receipt: file/authority reads only, no SQL or Odoo launch.

The formal config digest contains 62 hexadecimal characters. This script does
not substitute the 64-character sealed digest or resume the execution window.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / '.local/s10-p0-05'
OUTPUT = ROOT / 'docs/evidence/s10-p0-05/blocked.json'
HEAD = '8802bfee708bb854ac4ef1599796ee1f958db6d6'
CORE_HEAD = 'f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb'
BRANCH = 'codex/s10-settlement-finance-r1-20261013'
AUTH = 6206097763
SOURCE = 'ydental_s10_test_20261016_p004_9a6e37f2'
SOURCE_OID = 2100320
AUTHORIZED_CONFIG = '578a1304e65dab36440c6e51374276903d7b9ba989e4b75697c1fb9ae62abc'
SEALED_CONFIG = '578a1304e65dab36440c6e51374276903f9d7b9ba989e4b75697c1fb9ae62abc'
SOURCE_MARKER = '8afd6122428c723fafa597536c64f146b5b5a339bbb866229d8660f648173f29'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git(*args, cwd=ROOT):
    return subprocess.check_output(['git', *args], cwd=cwd, text=True).strip()


def main():
    os.umask(0o077)
    assert not OUTPUT.exists(), 'one-use evidence output; do not overwrite'
    assert git('branch', '--show-current') == BRANCH and git('rev-parse', 'HEAD') == HEAD
    assert git('remote', 'get-url', 'origin') == 'https://github.com/Yredxin/YDental.git'
    assert git('ls-remote', 'origin', 'refs/heads/' + BRANCH).split()[0] == HEAD
    assert git('rev-parse', 'HEAD', cwd=ROOT.parent) == CORE_HEAD
    assert not git('diff', '--name-only') and not git('diff', '--cached', '--name-only')
    auth = json.loads((PRIVATE / 'authorization-readback.json').read_text())
    assert auth['id'] == AUTH and AUTHORIZED_CONFIG in auth['body']
    latest = json.loads((PRIVATE / 'latest-readback.json').read_text())
    assert len(latest) == 1 and latest[0]['id'] == AUTH
    expected_files = {
        'docs/evidence/s10-p0-04/blocked.json': '1738cbd133eda97234ab621f4bc622e5301b8cbaa9330a958e94e9d97b463e1a',
        'docs/evidence/s10-p0-04/business-before-after.json': '5b99aa655057a3e54c06aefbb17aa9d9e552cac4ea69940931412b96873c26a7',
    }
    assert {p: digest(ROOT / p) for p in expected_files} == expected_files
    run = ROOT / '.local' / SOURCE
    actual_config = digest(run / 'odoo.conf')
    actual_marker = digest(run / 'database.json')
    marker = json.loads((run / 'database.json').read_text())
    sealed = json.loads((ROOT / 'docs/evidence/s10-p0-04/blocked.json').read_text())['target']
    assert actual_marker == SOURCE_MARKER
    assert marker['database'] == SOURCE and marker['oid'] == SOURCE_OID
    assert marker['config_sha256'] == sealed['config_sha256'] == actual_config == SEALED_CONFIG
    assert not re.fullmatch('[0-9a-f]{64}', AUTHORIZED_CONFIG)
    assert AUTHORIZED_CONFIG != actual_config
    historical = {}
    for name, oid in (
        ('ydental_s10_test_20261014020300_8b6c1d4e', 2056451),
        ('ydental_s10_test_20261015_p002_6d84a2c1', 2100311),
        ('ydental_s10_test_20261016_p003_75c1e9b2', 2100319),
        (SOURCE, SOURCE_OID),
    ):
        folder = ROOT / '.local' / name
        m = json.loads((folder / 'database.json').read_text())
        # Historical marker formats differ; file SHA, not guessed fields, is evidence.
        assert m.get('oid', m.get('database_oid')) == oid
        historical[name] = {'marker_oid': oid, 'marker_sha256': digest(folder / 'database.json'),
                            'config_sha256': digest(folder / 'odoo.conf'),
                            'live_sql_identity': 'NOT_RUN'}
    archives = {}
    for n in (23, 34, 35):
        p = PRIVATE / f'ydental-p005-issue{n}.json'
        value = json.loads(p.read_text())
        archives[str(n)] = {'body_sha256': hashlib.sha256(value['body'].encode()).hexdigest(),
                            'api_sha256': digest(p), 'state': value['state'],
                            'comments': value['comments']}
        if n != 35:
            p = PRIVATE / f'ydental-p005-comments{n}.json'
            comments = json.loads(p.read_text())
            assert len(comments) == value['comments']
            archives[str(n)]['comment_index'] = [{'id': x['id'], 'updated_at': x['updated_at'],
                'body_sha256': hashlib.sha256(x['body'].encode()).hexdigest()} for x in comments]
    assert archives['35']['state'] == 'open' and archives['35']['comments'] == 0
    drafts = {str(p.relative_to(ROOT)): digest(p) for p in sorted((PRIVATE/'unexecuted-drafts').glob('*.py'))}
    budget = {'create': [0,1], 'odoo_http': [0,1], 'firefox': [0,1],
        'user14_cross_store_unlock9_post': [0,1], 'user6_unlock9_post': [0,1],
        'user10_unlock_post': [0,0], 'refund_reject_post': [0,0],
        'new_refund_payment_credit_bill_close_stock': [0,0],
        'upgrade_init_install_prepare_shell': [0,0], 'sudo': [0,0]}
    evidence = {
        'status': 'S10_P0_05_BLOCKED_PREFLIGHT_AUTHORIZED_CONFIG_DIGEST_MISMATCH',
        'authorization_comment': AUTH, 'previous_gpt_review': 6206056107,
        'branch': BRANCH, 'start_head': HEAD, 'core_head': CORE_HEAD,
        'utc': datetime.now(timezone.utc).isoformat(),
        'failure': {'gate': 'authority/source config SHA256',
                    'authorized_sha256': AUTHORIZED_CONFIG, 'authorized_length': len(AUTHORIZED_CONFIG),
                    'actual_sha256': actual_config, 'actual_length': len(actual_config),
                    'actual_matches_sealed_p004_json_and_marker': True,
                    'missing_authorization_characters': 'f9 after ...74276903',
                    'initial_result': 'AssertionError before capture()/source_gate()/CREATE'},
        'source': {'name': SOURCE, 'marker_oid': SOURCE_OID, 'marker_sha256': actual_marker,
                    'config_sha256': actual_config, 'live_sql_oid': 'NOT_RUN'},
        'protected_history_files': historical, 'fixed_p004_evidence_sha256': expected_files,
        'authority_archive': archives, 'unexecuted_private_drafts_sha256': drafts,
        'results': {
            'HISTORICAL_REAL_WEB_REFUND14_REJECT': 'PRESERVED_PRIOR_EVIDENCE_ONLY; not rerun',
            'HISTORICAL_P004_USER10_DENIAL': 'PRESERVED_PRIOR_EVIDENCE_ONLY; not rerun',
            'NEW_READONLY_P004_SOURCE': 'PARTIAL: marker/config files verified; full SQL/filestore gate NOT_RUN',
            'NEW_USER14_CROSS_STORE_DENIAL': 'NOT_RUN',
            'NEW_USER6_REAL_WEB_UNLOCK9': 'NOT_RUN', 'BOUND_INVOICE_VIEW_AUDIT': 'NOT_RUN',
            'NATIVE_FINANCE_UNCHANGED': 'NOT_REVERIFIED: no SQL/business process launched',
            'SIMULATED_PASS': 'NOT_RUN', 'ODOO20_CLI_PARSER': 'NOT_RUN',
            'DOM_STABLE_FORM_POSITIVE_NEGATIVE': 'NOT_RUN'},
        'budgets_used_and_limit': budget,
        'target': {'planned_name': 'ydental_s10_test_20261016_p005_b7e42a91',
                   'planned_port': 18288, 'created': False, 'oid': None},
        'create_checkpoint': 'NOT_PUBLISHED: failed preconditions',
        'scripts_sha256': {'scripts/s10_p0_05_preflight.py': digest(__file__)},
        'next_step': 'GPT formal review/corrected authorization required; Codex STOP',
    }
    OUTPUT.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with OUTPUT.open('x') as stream:
        json.dump(evidence, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    print(json.dumps({'status': evidence['status'], 'evidence_sha256': digest(OUTPUT),
                      'budgets': budget}, ensure_ascii=False))


if __name__ == '__main__':
    main()

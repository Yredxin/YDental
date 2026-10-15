"""Read-only R3 source audit and offline HTML contract simulation for P0-01."""

import configparser
import hashlib
import json
from pathlib import Path

import psycopg2


ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'ydental_s10_test_20261014020300_8b6c1d4e'
RUN = ROOT / '.local' / SOURCE
OUT = ROOT / 'docs/evidence/s10-p0-01/preflight.json'
EXPECTED_OID = 2056451
EXPECTED_CLUSTER = '7694897083368259627'
EXPECTED_CONFIG = '34f2a7cff12ef31c69090fb7b1f990b008bebf850290e2747d868c6a9d8ae778'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def query(cur, statement, params=()):
    cur.execute(statement, params)
    return cur.fetchall()


def table_digest(cur, table):
    # Fixed internal table names only. The digest keeps rows out of committed evidence.
    digest = hashlib.sha256()
    cur.execute(f'SELECT row_to_json(t)::text FROM {table} t ORDER BY id')
    count = 0
    for (row,) in cur:
        digest.update(row.encode() + b'\n')
        count += 1
    return {'rows': count, 'sha256': digest.hexdigest()}


def main():
    marker = json.loads((RUN / 'database.json').read_text())
    config = configparser.ConfigParser(interpolation=None)
    assert config.read(RUN / 'odoo.conf')
    assert (marker['database'], marker['oid'], marker['cluster'], marker['config_sha256']) == (
        SOURCE, EXPECTED_OID, EXPECTED_CLUSTER, EXPECTED_CONFIG)
    assert config['options']['db_name'] == SOURCE
    assert sha((RUN / 'odoo.conf').read_bytes()) == EXPECTED_CONFIG
    kwargs = {'host': '127.0.0.1', 'port': 5432, 'user': 'odoo',
              'password': config['options']['db_password'], 'dbname': SOURCE,
              'options': '-c default_transaction_read_only=on'}
    with psycopg2.connect(**kwargs) as conn:
        conn.set_session(readonly=True)
        with conn.cursor() as cur:
            identity = query(cur, 'SELECT (SELECT oid FROM pg_database WHERE datname=current_database()), '
                             '(SELECT system_identifier::text FROM pg_control_system()), current_database()')[0]
            assert identity == (EXPECTED_OID, EXPECTED_CLUSTER, SOURCE)
            modules = query(cur, "SELECT name,state FROM ir_module_module WHERE name IN "
                            "('ydental_settlement','ydental_settlement_test') ORDER BY name")
            assert modules == [('ydental_settlement', 'installed'),
                               ('ydental_settlement_test', 'installed')]
            views = {}
            for key, active, arch in query(cur, "SELECT key,active,arch_db->>'en_US' FROM ir_ui_view "
                                           "WHERE key LIKE 'ydental_settlement.%%' ORDER BY key"):
                views[key] = {'active': active, 'sha256': sha(arch.encode()),
                              'has_output_html': 'name="output" value="html"' in arch,
                              'has_refund_reject': 'value="refund_reject"' in arch,
                              'has_unlock': 'value="unlock"' in arch,
                              'has_page_links': 'ydental_settlement_page_links' in arch}
            refunds = query(cur, "SELECT r.id,r.ydental_state,r.ydental_requester_id,p.ydental_store_id,"
                            "r.ydental_payment_id,r.ydental_amount,r.ydental_native_payment_id,"
                            "r.ydental_credit_note_id FROM ydental_settlement_refund r "
                            "JOIN ydental_settlement_payment p ON p.id=r.ydental_payment_id "
                            "WHERE p.ydental_store_id=1 ORDER BY r.id DESC OFFSET 50 LIMIT 50")
            closes = query(cur, "SELECT id,ydental_state,ydental_cashier_id,ydental_business_date,"
                           "ydental_channel,ydental_cycle,ydental_gross,ydental_refunded,ydental_pending "
                           "FROM ydental_settlement_close WHERE ydental_store_id=1 "
                           "ORDER BY id DESC OFFSET 50 LIMIT 50")
            counts = {
                'refund_store1': query(cur, 'SELECT count(*) FROM ydental_settlement_refund r JOIN '
                                       'ydental_settlement_payment p ON p.id=r.ydental_payment_id '
                                       'WHERE p.ydental_store_id=1')[0][0],
                'close_store1': query(cur, 'SELECT count(*) FROM ydental_settlement_close '
                                      'WHERE ydental_store_id=1')[0][0],
            }
            grants = query(cur, "SELECT m.ydental_user_id,m.ydental_store_id,g.ydental_category,"
                           "g.ydental_level FROM ydental_access_grant g JOIN ydental_access_membership m "
                           "ON m.id=g.ydental_membership_id WHERE m.active AND "
                           "m.ydental_user_id IN (5,6,10,14) AND "
                           "g.ydental_category IN ('settlement','finance_approval') ORDER BY 1,2,3")
            latest = query(cur, "SELECT id FROM ydental_settlement_close WHERE ydental_store_id=1 "
                           "AND ydental_cashier_id=5 AND ydental_business_date='2026-07-15' "
                           "AND ydental_channel='card' ORDER BY ydental_cycle DESC LIMIT 1")[0][0]
            native = query(cur, "SELECT r.id,ap.payment_type,ap.state,am.state FROM "
                           "ydental_settlement_refund r LEFT JOIN account_payment ap "
                           "ON ap.id=r.ydental_native_payment_id LEFT JOIN account_move am "
                           "ON am.id=ap.move_id WHERE r.id=14")[0]
            signatures = {table: table_digest(cur, table) for table in (
                'ydental_settlement_refund', 'ydental_settlement_close',
                'ydental_settlement_payment', 'account_payment', 'account_move',
                'account_partial_reconcile', 'ydental_access_grant')}
    filestore = RUN / 'data/filestore' / SOURCE
    files = sorted(path for path in filestore.rglob('*') if path.is_file())
    manifest = sha(b''.join((str(path.relative_to(filestore)) + ' ' + sha(path.read_bytes()) + '\n').encode()
                           for path in files))
    installed_tokens = views['ydental_settlement.ydental_settlement_tokens']
    current_tokens = (ROOT / 'ydental_settlement/views/ydental_settlement_templates.xml').read_text()
    controller = (ROOT / 'ydental_settlement/controllers/settlement.py').read_text()
    assert counts['refund_store1'] > 50 and counts['close_store1'] > 50
    assert any(row[0] == 14 and row[1] == 'requested' and row[2] == 5 for row in refunds)
    assert any(row[0] == 9 and row[1] == 'confirmed' for row in closes) and latest == 9
    assert (6, 1, 'finance_approval', 'write') in grants
    assert native == (14, None, None, None)
    assert 'name="output" value="html"' in current_tokens
    assert "post.get('output') == 'html'" in controller
    # Fake DOM -> form fields -> current controller route. The installed token
    # template omits output=html, so a native click receives JSON, not HTML PRG.
    simulated_post = {'operation': 'refund_reject', 'refund_id': '14',
                      'revision': '1', 'key': 'simulated-only', 'csrf_token': 'simulated-only',
                      'reason': 'simulated-only'}
    html_route = simulated_post.get('output') == 'html'
    assert not installed_tokens['has_output_html'] and not html_route
    result = {
        'status': 'BLOCKED_PREFLIGHT_INSTALLED_QWEB_DRIFT',
        'authorization_comment': 6190937428,
        'source': {'name': SOURCE, 'oid': EXPECTED_OID, 'cluster': EXPECTED_CLUSTER,
                   'marker_sha256': sha((RUN / 'database.json').read_bytes()),
                   'config_sha256': EXPECTED_CONFIG, 'filestore_files': len(files),
                   'filestore_manifest_sha256': manifest},
        'modules': modules, 'views': views,
        'product_sha256': {
            'controller': sha((ROOT / 'ydental_settlement/controllers/settlement.py').read_bytes()),
            'service': sha((ROOT / 'ydental_settlement/models/ydental_settlement_service.py').read_bytes()),
            'templates': sha((ROOT / 'ydental_settlement/views/ydental_settlement_templates.xml').read_bytes()),
        },
        'business': {'counts': counts, 'refund_page2_ids': [row[0] for row in refunds],
                     'close_page2_ids': [row[0] for row in closes],
                     'fixed_refund_id': 14, 'fixed_refund_requester': 5,
                     'fixed_close_id': 9, 'fixed_close_latest_id': latest,
                     'eligible_approver_user_id': 6,
                     'refund_14_native_payment_and_credit_note': [None, None],
                     'close_9_snapshot': [str(v) for v in next(row for row in closes if row[0] == 9)[6:]],
                     'grants': grants},
        'table_signatures': signatures,
        'offline_simulation': {'case': 'installed_form_to_current_controller',
                               'input_output_html': False, 'controller_html_branch': html_route,
                               'expected_http_response_kind': 'JSON',
                               'result': 'EXPECTED_FAIL_HTML_CONTRACT'},
        'budgets_used': {'create': 0, 'odoo_http': 0, 'firefox': 0,
                         'business_post': 0, 'odoo_shell': 0},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str) + '\n')
    print(json.dumps({'status': result['status'], 'source_oid': EXPECTED_OID,
                      'refund_page2': result['business']['refund_page2_ids'],
                      'close_page2': result['business']['close_page2_ids'],
                      'create': 0, 'http': 0, 'firefox': 0}))


if __name__ == '__main__':
    main()

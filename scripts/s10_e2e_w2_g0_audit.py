"""W2-G0: fixed-source, read-only business snapshot; never invokes Odoo.

Output contains only synthetic numeric IDs, states, amounts and file digests.
The private database configuration is read locally and never serialized.
"""

import configparser
from datetime import date, datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path

import psycopg2


ROOT = Path(__file__).resolve().parents[1]
NAME = 'ydental_s10_test_20261015051000_e2e1a7b4'
RUN = ROOT / '.local' / NAME
OID = 2100269
CLUSTER = '7694897083368259627'
CONFIG_SHA = 'f0a8ad4d715e4a6f316d7c1117e39ce9f743953284af2fa7088ce3eb66feed86'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def values(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, tuple):
        return [values(item) for item in value]
    if isinstance(value, list):
        return [values(item) for item in value]
    return value


QUERIES = {
    'snapshot': 'SELECT id,ydental_catalog_id,ydental_quantity,ydental_unit_price,ydental_amount FROM ydental_intake_snapshot ORDER BY id',
    'event': 'SELECT id,ydental_patient_id,ydental_execution_id,ydental_document_id,ydental_document_version,ydental_price_snapshot_id,state,ydental_quantity FROM ydental_treatment_event ORDER BY id',
    'fee': 'SELECT id,ydental_patient_id,ydental_event_id,ydental_price_snapshot_id,ydental_amount FROM ydental_treatment_fee ORDER BY id',
    'stock': 'SELECT e.id,e.ydental_kind,e.state,e.ydental_quantity,e.ydental_move_id,m.state,m.quantity FROM ydental_inventory_event e JOIN stock_move m ON m.id=e.ydental_move_id ORDER BY e.id',
    'order': 'SELECT id,ydental_patient_id,ydental_execution_id,ydental_document_id,ydental_document_version,ydental_version,ydental_kind,state FROM ydental_treatment_order ORDER BY id',
    'line': 'SELECT id,ydental_patient_id,ydental_order_id,ydental_mapping_id,ydental_task_id,ydental_quantity,state FROM ydental_treatment_line ORDER BY id',
    'task': 'SELECT id,ydental_patient_id,ydental_mapping_id,ydental_parent_task_id,ydental_source_execution_id,ydental_version,state,ydental_source_kind FROM ydental_intake_task ORDER BY id',
    'execution': 'SELECT id,ydental_patient_id,ydental_task_id,ydental_entry_id,ydental_lease_id,state,ydental_version,ydental_started_at,ydental_ended_at FROM ydental_queue_execution ORDER BY id',
    'entry': 'SELECT id,ydental_patient_id,ydental_task_id,ydental_lease_id,state,ydental_version FROM ydental_queue_entry ORDER BY id',
    'lease': 'SELECT id,ydental_actor_id,ydental_station_id,ydental_active,ydental_expires_at,ydental_release_reason,ydental_session_id IS NOT NULL,ydental_token_hash IS NOT NULL,ydental_connection_hash IS NOT NULL FROM ydental_queue_lease ORDER BY id',
    'lease_session': 'SELECT l.id,s.id,s.ydental_user_id,s.ydental_store_id,s.ydental_revision,l.ydental_revision,(s.ydental_revision=l.ydental_revision) FROM ydental_queue_lease l JOIN ydental_access_session s ON s.id=l.ydental_session_id ORDER BY l.id',
    'hold': 'SELECT id,ydental_patient_id,ydental_task_id,ydental_target_task_id,ydental_execution_id,ydental_lease_id,state FROM ydental_queue_hold ORDER BY id',
    'position': 'SELECT id,ydental_patient_id,ydental_task_id,ydental_active,ydental_version FROM ydental_intake_position ORDER BY id',
    'document': 'SELECT d.id,d.ydental_patient_id,d.ydental_execution_id,d.ydental_current_execution_id,d.ydental_version,d.state,d.ydental_editor_id,d.ydental_editor_expires,d.ydental_saved_at,v.id,v.ydental_number,(d.ydental_content=v.ydental_content) FROM ydental_clinical_document d LEFT JOIN ydental_clinical_version v ON v.ydental_document_id=d.id AND v.ydental_number=d.ydental_version ORDER BY d.id',
    'audit': "SELECT ydental_event,ydental_target_model,ydental_target_id,ydental_result FROM ydental_access_audit WHERE ydental_event IN ('clinical.save','treatment.actual_execution','treatment.order_issued','inventory.movement') ORDER BY id",
    'module': "SELECT name,state FROM ir_module_module WHERE name IN ('ydental_queue','ydental_clinical','ydental_treatment','ydental_exam','ydental_settlement') ORDER BY name",
}
COUNTS = ('ydental_exam_result', 'ydental_settlement_source', 'ydental_settlement_receipt',
          'ydental_settlement_payment', 'ydental_settlement_refund', 'ydental_settlement_close',
          'account_move', 'account_payment', 'account_partial_reconcile')
HASH_TABLES = ('ydental_treatment_event', 'ydental_treatment_fee', 'ydental_intake_snapshot',
               'ydental_inventory_event', 'stock_move', 'ydental_treatment_order',
               'ydental_treatment_line', 'ydental_intake_task', 'ydental_queue_execution',
               'ydental_queue_entry', 'ydental_queue_lease', 'ydental_queue_hold',
               'ydental_clinical_document', 'ydental_clinical_version', 'ydental_access_audit')


def audit():
    assert digest(RUN / 'odoo.conf') == CONFIG_SHA
    marker = json.loads((RUN / 'database.json').read_text())
    assert (marker['database'], marker['oid'], marker['cluster'], marker['config_sha256']) == (NAME, OID, CLUSTER, CONFIG_SHA)
    cfg = configparser.ConfigParser(interpolation=None)
    assert cfg.read(RUN / 'odoo.conf')
    opts = cfg['options']
    assert (opts['db_name'], opts['dbfilter']) == (NAME, '^' + NAME + '$')
    conn = psycopg2.connect(dbname=NAME, host=opts['db_host'], port=opts['db_port'],
                            user=opts['db_user'], password=opts['db_password'], connect_timeout=5)
    conn.set_session(readonly=True)
    try:
        with conn.cursor() as cur:
            cur.execute('SHOW transaction_read_only')
            assert cur.fetchone() == ('on',)
            cur.execute('SELECT oid,datname FROM pg_database WHERE datname=current_database()')
            assert cur.fetchone() == (OID, NAME)
            cur.execute('SELECT system_identifier::text FROM pg_control_system()')
            assert cur.fetchone() == (CLUSTER,)
            cur.execute('SELECT now()')
            now = cur.fetchone()[0]
            rows = {}
            for label, query in QUERIES.items():
                assert query.lstrip().upper().startswith('SELECT ')
                cur.execute(query)
                rows[label] = values(cur.fetchall())
            counts = {}
            for table in COUNTS:
                assert table.replace('_', '').isalnum()
                cur.execute('SELECT count(*) FROM ' + table)
                counts[table] = cur.fetchone()[0]
            row_hashes = {}
            for table in HASH_TABLES:
                assert table.replace('_', '').isalnum()
                cur.execute('SELECT id,row_to_json(t)::text FROM ' + table + ' t ORDER BY id')
                rows_for_hash = cur.fetchall()
                row_hashes[table] = {
                    'count': len(rows_for_hash),
                    'sha256': hashlib.sha256('\n'.join(
                        str(row_id) + ':' + body for row_id, body in rows_for_hash
                    ).encode()).hexdigest(),
                }
            cur.execute('SELECT store_fname,checksum FROM ir_attachment WHERE store_fname IS NOT NULL ORDER BY id')
            attachments = cur.fetchall()
    finally:
        conn.rollback()
        conn.close()
    fs = RUN / 'data' / 'filestore' / NAME
    file_paths = sorted(p for p in fs.rglob('*') if p.is_file())
    for rel, checksum in attachments:
        item = fs / rel
        assert item.is_file() and not item.is_symlink()
        assert hashlib.sha1(item.read_bytes()).hexdigest() == checksum
    assert rows['event'] == [[1, 1, 1, 1, 1, 1, 'confirmed', '1.00']]
    assert rows['fee'] == [[1, 1, 1, 1, '600.00']]
    assert rows['line'] == [[1, 1, 1, 3, 2, '1.00', 'issued']]
    assert rows['task'][1][0:2] == [2, 1] and rows['task'][1][6] == 'pending'
    assert rows['stock'][2] == [3, 'treatment', 'done', '1.00', 3, 'done', '1.00']
    assert all(count == 0 for count in counts.values())
    lease = rows['lease'][0]
    document = rows['document'][0]
    return {
        'task': 'S10-E2E-W2-G0', 'classification': 'OBSERVED_READONLY',
        'source_name': NAME, 'source_oid': OID, 'cluster': CLUSTER,
        'db_now': now.isoformat(), 'config_sha256': CONFIG_SHA,
        'marker_sha256': digest(RUN / 'database.json'),
        'filestore_files': len(file_paths), 'attachment_pointers_checked': len(attachments),
        'filestore_inventory_sha256': hashlib.sha256('\n'.join(
            str(p.relative_to(fs)) + ':' + digest(p) for p in file_paths).encode()).hexdigest(),
        'rows': rows, 'counts': counts, 'private_row_hashes': row_hashes,
        'lease_expired_at_snapshot': datetime.fromisoformat(lease[4]).replace(tzinfo=timezone.utc) <= now,
        'document_editor_expired_at_snapshot': datetime.fromisoformat(document[7]).replace(tzinfo=timezone.utc) <= now,
    }


if __name__ == '__main__':
    print(json.dumps(audit(), ensure_ascii=False, indent=2, sort_keys=True))

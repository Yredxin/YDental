"""Read-only S09 source, fee and version invariants on a guarded synthetic DB."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re

from psycopg2 import sql

run = Path(os.environ['YDENTAL_S09_RUN_DIR'])
assert run.name == env.cr.dbname and re.fullmatch(r'ydental_s09_test_[0-9]{14}_[a-f0-9]{8}', env.cr.dbname)
marker = json.loads((run / 'database.json').read_text())
env.cr.execute('SELECT oid FROM pg_database WHERE datname=%s', [env.cr.dbname])
assert marker['database'] == env.cr.dbname and marker['oid'] == env.cr.fetchone()[0]
assert marker['cluster'] == '7694897083368259627'

tables = ('ydental_exam_result', 'ydental_exam_version', 'ydental_exam_receipt',
          'ydental_exam_template', 'ydental_exam_qualification', 'ydental_treatment_order',
          'ydental_treatment_line', 'ydental_treatment_event', 'ydental_treatment_fee',
          'ydental_treatment_consumption', 'ydental_intake_snapshot',
          'ydental_intake_task', 'ydental_queue_execution', 'ydental_queue_entry',
          'ydental_clinical_document', 'ydental_inventory_event', 'stock_move',
          'stock_move_line', 'stock_quant')
signatures = {}
for table in tables:
    env.cr.execute(sql.SQL('SELECT row_to_json(t)::text FROM {} t ORDER BY id').format(sql.Identifier(table)))
    rows = [row[0] for row in env.cr.fetchall()]
    signatures[table] = {'count': len(rows),
        'sha256': hashlib.sha256('\n'.join(rows).encode()).hexdigest()}

queries = {
    'exam_result_source': """SELECT count(*) FROM ydental_exam_result r
        JOIN ydental_treatment_line l ON l.id=r.ydental_line_id
        JOIN ydental_treatment_order o ON o.id=l.ydental_order_id
        WHERE o.ydental_kind<>'exam' OR r.ydental_patient_id<>l.ydental_patient_id
           OR r.ydental_store_id<>l.ydental_store_id""",
    'exam_event_source': """SELECT count(*) FROM ydental_exam_result r
        JOIN ydental_treatment_event e ON e.id=r.ydental_event_id
        WHERE e.ydental_order_line_id<>r.ydental_line_id OR e.ydental_kind<>'exam'
           OR e.ydental_execution_id<>r.ydental_execution_id
           OR e.ydental_patient_id<>r.ydental_patient_id""",
    'exam_event_unique': """SELECT count(*) FROM (
        SELECT ydental_order_line_id FROM ydental_treatment_event
        WHERE ydental_kind='exam' GROUP BY 1 HAVING count(*)>1) q""",
    'exam_version_count': """SELECT count(*) FROM ydental_exam_result r WHERE r.ydental_version<>
        (SELECT count(*) FROM ydental_exam_version v WHERE v.ydental_result_id=r.id)""",
    'exam_version_source': """SELECT count(*) FROM ydental_exam_version v
        JOIN ydental_exam_result r ON r.id=v.ydental_result_id
        WHERE v.ydental_patient_id<>r.ydental_patient_id OR v.ydental_store_id<>r.ydental_store_id""",
    'exam_version_latest': """SELECT count(*) FROM ydental_exam_result r
        JOIN ydental_exam_version v ON v.ydental_result_id=r.id AND v.ydental_number=r.ydental_version
        WHERE v.ydental_findings IS DISTINCT FROM r.ydental_findings
           OR v.ydental_measurements IS DISTINCT FROM r.ydental_measurements
           OR v.ydental_conclusion IS DISTINCT FROM r.ydental_conclusion""",
    'confirmed_fee_unique': """SELECT count(*) FROM ydental_treatment_event e WHERE
        (e.state='confirmed' AND (SELECT count(*) FROM ydental_treatment_fee f
             WHERE f.ydental_event_id=e.id)<>1)
        OR (e.state='pending' AND EXISTS(SELECT 1 FROM ydental_treatment_fee f
             WHERE f.ydental_event_id=e.id))""",
    'exam_fee_snapshot': """SELECT count(*) FROM ydental_treatment_event e
        JOIN ydental_treatment_fee f ON f.ydental_event_id=e.id
        LEFT JOIN ydental_intake_snapshot s ON s.id=f.ydental_price_snapshot_id
        WHERE e.ydental_kind='exam' AND (s.id IS NULL
            OR e.ydental_price_snapshot_id<>s.id
            OR f.ydental_unit_price<>s.ydental_unit_price
            OR f.ydental_amount<>round((e.ydental_quantity*f.ydental_unit_price)::numeric,2))""",
    'unperformed_exam_fee': """SELECT count(*) FROM ydental_treatment_line l
        JOIN ydental_treatment_order o ON o.id=l.ydental_order_id
        JOIN ydental_treatment_event e ON e.ydental_order_line_id=l.id
        WHERE o.ydental_kind='exam' AND l.state IN ('issued','cancelled','aborted')""",
    'duplicate_active_execution': """SELECT count(*) FROM (SELECT ydental_patient_id
        FROM ydental_queue_execution WHERE state IN ('serving','verify')
        GROUP BY 1 HAVING count(*)>1) q""",
    'duplicate_continuation': """SELECT count(*) FROM (SELECT ydental_source_execution_id
        FROM ydental_intake_task WHERE ydental_source_kind='continuation'
        GROUP BY 1 HAVING count(*)>1) q""",
    'negative_internal_quant': """SELECT count(*) FROM stock_quant q
        JOIN stock_location l ON l.id=q.location_id
        WHERE l.ydental_store_id IS NOT NULL AND l.usage='internal' AND q.quantity < -0.000001""",
}
invariants = {}
for name, query in queries.items():
    env.cr.execute(query)
    invariants[name] = env.cr.fetchone()[0]
env.cr.execute("SELECT ydental_event,count(*) FROM ydental_access_audit WHERE ydental_event LIKE 'exam.%' GROUP BY 1 ORDER BY 1")
audit_events = dict(env.cr.fetchall())
result = {'database': env.cr.dbname, 'oid': marker['oid'], 'cluster': marker['cluster'],
          'signatures': signatures, 'invariants': invariants, 'audit_events': audit_events,
          'result': 'PASS' if not any(invariants.values()) else 'FAIL'}
path = run / ('audit-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f') + '.json')
path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print('S09_AUDIT', json.dumps({'result': result['result'], 'invariants': invariants, 'file': path.name}))
assert result['result'] == 'PASS'

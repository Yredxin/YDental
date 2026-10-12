"""Read-only signatures and invariants; no content, credentials or tokens exported."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

from psycopg2 import sql

run=Path(os.environ['YDENTAL_S08A_RUN_DIR']);assert run.name==env.cr.dbname and re.fullmatch(r'ydental_s08a_test_[0-9]{14}_[a-f0-9]{8}',env.cr.dbname)
result={'database':env.cr.dbname,'tested_commit':subprocess.check_output(['git','-C',str(Path(__file__).resolve().parents[1]),'rev-parse','HEAD'],text=True).strip(),'signatures':{},'invariants':{}}
env.cr.execute('SELECT name,setting FROM pg_settings WHERE name=ANY(%s)', [
    ['max_parallel_workers_per_gather','max_parallel_maintenance_workers','maintenance_work_mem']])
result['session_settings']=dict(env.cr.fetchall())
assert result['session_settings']=={'max_parallel_workers_per_gather':'0','max_parallel_maintenance_workers':'0','maintenance_work_mem':'16384'}

# Fixed server identifiers, never supplied by a client.
for table in ('ydental_clinical_document','ydental_clinical_version','ydental_queue_execution','ydental_intake_task','ydental_inventory_event','ydental_inventory_batch','stock_move','stock_move_line','stock_quant','ydental_intake_snapshot'):
    env.cr.execute(sql.SQL('SELECT row_to_json(t)::text FROM {} t ORDER BY id').format(sql.Identifier(table)))
    rows=env.cr.fetchall();result['signatures'][table]={'count':len(rows),'sha256':hashlib.sha256('\n'.join(r[0] for r in rows).encode()).hexdigest()}
queries={
 'version_count':'''SELECT count(*) FROM ydental_clinical_document d WHERE d.ydental_version<>(SELECT count(*) FROM ydental_clinical_version v WHERE v.ydental_document_id=d.id)''',
 'latest_content':'''SELECT count(*) FROM ydental_clinical_document d JOIN ydental_clinical_version v ON v.ydental_document_id=d.id AND v.ydental_number=d.ydental_version WHERE d.ydental_content<>v.ydental_content''',
 'version_source':'''SELECT count(*) FROM ydental_clinical_version v JOIN ydental_clinical_document d ON v.ydental_document_id=d.id WHERE v.ydental_store_id<>d.ydental_store_id OR v.ydental_patient_id<>d.ydental_patient_id''',
 'document_source':'''SELECT count(*) FROM ydental_clinical_document d JOIN ydental_queue_execution e ON d.ydental_execution_id=e.id WHERE d.ydental_store_id<>e.ydental_store_id OR d.ydental_patient_id<>e.ydental_patient_id''',
 'duplicate_continuation':'''SELECT count(*) FROM (SELECT ydental_source_execution_id FROM ydental_intake_task WHERE ydental_source_execution_id IS NOT NULL GROUP BY ydental_source_execution_id HAVING count(*)>1) q''',
 'duplicate_actual_execution':'''SELECT count(*) FROM (SELECT ydental_patient_id FROM ydental_queue_execution WHERE state IN ('serving','verify') GROUP BY ydental_patient_id HAVING count(*)>1) q''',
 'terminal_unmarked_draft':'''SELECT count(*) FROM ydental_clinical_document d JOIN ydental_queue_execution e ON d.ydental_current_execution_id=e.id WHERE e.state IN ('handover','interrupted') AND d.state='draft' ''',
 'negative_internal_quant':'''SELECT count(*) FROM stock_quant q JOIN stock_location l ON l.id=q.location_id WHERE l.usage='internal' AND q.quantity<0''',
}
for name,query in queries.items():env.cr.execute(query);result['invariants'][name]=env.cr.fetchone()[0]
env.cr.execute("SELECT ydental_event,count(*) FROM ydental_access_audit WHERE ydental_event LIKE 'clinical.%' GROUP BY ydental_event ORDER BY ydental_event")
result['audit_events']=dict(env.cr.fetchall());result['result']='PASS' if not any(result['invariants'].values()) else 'FAIL'
root=Path(__file__).resolve().parents[1];out=root/'docs/evidence/s08a/audit-attempts';out.mkdir(parents=True,exist_ok=True)
(out/(run.name+'-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.json')).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'result':result['result'],'invariants':result['invariants']}))
assert result['result']=='PASS'

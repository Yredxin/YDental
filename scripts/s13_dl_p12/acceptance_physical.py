"""Independent physical RO review using the stage's unchanged complete projection.

Only redirect the new snapshot output and record the newly opened physical PID.
No target, permissions, scope, expiry, branch or projection guard is replaced.
"""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace

root=Path.cwd()
p=argparse.ArgumentParser()
p.add_argument('--candidate',required=True)
p.add_argument('--checkpoint',required=True)
p.add_argument('--checkpoint-sha256',required=True)
p.add_argument('--label',required=True)
a=p.parse_args()
assert a.label.replace('-','').isalnum() and len(a.label)<50
checkpoint=(root/a.checkpoint).resolve()
assert checkpoint.is_relative_to(root/'.local/dl-p12/verification')
assert hashlib.sha256(checkpoint.read_bytes()).hexdigest()==a.checkpoint_sha256
source=root/'scripts/s13_dl_p12/protected_snapshot.py'
spec=importlib.util.spec_from_file_location('p12_independent_complete_projection',source)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
real_connect=m.psycopg2.connect
pids=[]
supplements={}
class ReviewedConnection(m.psycopg2.extensions.connection):
    def set_session(self,*args,**kwargs):
        super().set_session(*args,**kwargs)
        with self.cursor() as q:
            q.execute("SELECT current_database(),(SELECT oid FROM pg_database WHERE datname=current_database()),(pg_control_system()).system_identifier::text,current_user,current_setting('transaction_read_only'),current_setting('transaction_isolation')")
            identity=q.fetchone()
            assert identity==(m.TARGET,m.OID,m.CLUSTER,m.TARGET,'on','repeatable read')
            q.execute("SELECT d.id,d.name,d.module_id,d.auto_install_required FROM ir_module_module_dependency d JOIN ir_module_module module ON module.id=d.module_id WHERE module.name='ydental_settlement' ORDER BY d.id")
            dependencies=[dict(zip(('id','name','module_id','auto_install_required'),r)) for r in q.fetchall()]
            q.execute("SELECT id,store_fname FROM ir_attachment WHERE (res_model LIKE 'ydental.%' OR res_model IN ('account.move','purchase.order')) AND store_fname IS NOT NULL ORDER BY id")
            references=[{'attachment_id':ident,'file_path_sha256':hashlib.sha256(name.encode()).hexdigest()} for ident,name in q.fetchall()]
        supplements[self.get_backend_pid()]={'same_physical_identity':identity,'native_settlement_dependencies':dependencies,'protected_reference_paths':references,'native_queries_same_READ_ONLY_REPEATABLE_READ_transaction':True}
def connect(*args,**kwargs):
    assert 'connection_factory' not in kwargs
    kwargs['connection_factory']=ReviewedConnection
    connection=real_connect(*args,**kwargs)
    pids.append(connection.get_backend_pid())
    return connection
m.psycopg2.connect=connect
out=root/'.local/dl-p12/acceptance'/f'{a.label}-physical-snapshot.json'
def output_only(requested,result):
    assert requested==root/'.local/dl-p12/verification'/f'upgrade-independent-{a.label}-baseline.json'
    assert len(pids)==1
    supplement=supplements[pids[0]]
    files={r['attachment_id']:r for r in result['attachments'] if r['file_present']}
    records=[]
    for ref in supplement['protected_reference_paths']:
        entry=files[ref['attachment_id']]
        records.append(dict(ref,file_size=entry['file_size'],file_sha256=entry['file_sha256']))
    assert len(files)==len(records)
    supplement['protected_reference_file_inventory']={'protected_attachment_reference_count':len(records),'unique_physical_path_count':len({v['file_path_sha256'] for v in records}),'distinct_file_sha256_count':len({v['file_sha256'] for v in records}),'all_reference_files_really_opened_and_hashed_by_complete_projection':True,'references':records}
    del supplement['protected_reference_paths']
    result['independent_native_supplement_same_new_physical']=supplement
    result.update(reviewer='/root/acceptance_p12 (no product or corresponding runtime/test tool implementation; shared OS)',
        actual_new_physical_backend_pids=list(pids),root_checkpoint_sha256=a.checkpoint_sha256,
        independent_output_path=str(out.relative_to(root)),
        output_redirect_only_no_projection_target_or_guard_change=True)
    data=(json.dumps(m.canonical(result),ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
    fd=os.open(out,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
    return hashlib.sha256(data).hexdigest()
m.write_new=output_only
code=m.collect(SimpleNamespace(label='independent-'+a.label,phase='baseline',candidate=a.candidate,
    modules='ydental_settlement',initial_s12_baseline=False,freeze_receipt=None))
snapshot=json.loads(out.read_text())
assert code==0 and snapshot['connection_closed'] and snapshot['rollback_idle']
reference=json.loads(checkpoint.read_text())
sections=['business','technical_metadata','attachments','config_presence','nonsecret_config',
    'smtp_server_count','business_schema_constraints','business_schema_indexes','omitted_columns']
comparisons={key:snapshot[key]==reference[key] for key in sections}
value={'status':'NEW_PHYSICAL_COMPLETE_RO_NINE_SECTIONS_EXACT_ROOT' if all(comparisons.values()) else 'NEW_PHYSICAL_RO_DIFFERENCE_REQUIRES_REVIEW',
    'reviewed_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'reviewer':'/root/acceptance_p12',
    'reviewed_no_product_or_test_tool_implementation':True,'candidate_commit':a.candidate,
    'checkpoint_path':a.checkpoint,'checkpoint_sha256':a.checkpoint_sha256,
    'new_physical_backend_pids':pids,'readonly_repeatable_read_identity':snapshot['identity'],
    'rollback_idle':snapshot['rollback_idle'],'connection_closed':snapshot['connection_closed'],
    'snapshot_path':str(out.relative_to(root)),'snapshot_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),
    'supplemental_native_metadata_same_new_physical':snapshot['independent_native_supplement_same_new_physical'],
    'complete_projection_tool_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
    'independent_reviewer_tool_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'nine_sections_exact':comparisons,'business_table_count':len(snapshot['business']),
    'technical_table_count':len(snapshot['technical_metadata']),
    'protected_files_actual_count':sum(1 for item in snapshot['attachments'] if item['file_present']),
    'business_write_or_service_start_performed':False,'shared_os_not_isolation':True}
rp=root/'.local/dl-p12/acceptance'/f'{a.label}-native-connection.json'
data=(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
fd=os.open(rp,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
print(json.dumps({'status':value['status'],'output':str(out.relative_to(root)),'sha256':value['snapshot_sha256'],
    'receipt_sha256':hashlib.sha256(data).hexdigest(),'new_physical_backend_pids':pids,
    'business_tables':value['business_table_count'],'technical_tables':value['technical_table_count'],
    'actual_files':value['protected_files_actual_count']}))
raise SystemExit(0 if all(comparisons.values()) else 2)

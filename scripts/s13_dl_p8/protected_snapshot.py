"""Read-only S13 final-freeze pre/post upgrade snapshot, reusing the S11 projection. Never executes an upgrade.

The main operator first stops all writers and creates a private freeze receipt:
{candidate_commit, database, database_oid, modules, writers_quiescent: true}.
Invoke collect only at the actual final freeze, before/after the separately owned
limited upgrade. Compare is offline and never connects to a database. Raw clinical
text, attachments, contact data, request IDs and audit JSON are hashed privately.
Authentication secrets, session material and security hashes are never selected.
"""
from __future__ import annotations
import argparse, datetime as dt, decimal, hashlib, json, os, pathlib, re, sys
import psycopg2
from psycopg2 import sql
ROOT=pathlib.Path(__file__).resolve().parents[2]
PRIVATE=ROOT/'.local/dl-p8'; TARGET='ydental_s11_synth_20261023_01'; OID=2171423
CLUSTER='7694897083368259627'; CORE='f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb'
ALLOWED_MODULES={'ydental_print'}
# Never read application authentication/connection bearer material, even as a hash.
DROP=re.compile(r'password|secret|token|credential|session|connection_hash|editor_hash|lease_hash|api_key',re.I)
EXCLUDED_TABLES={'ydental_access_session','ydental_s11_clock_session','ydental_queue_screen_token',
                'ydental_lab_charge_credit_wizard','ydental_lab_code_bind','ydental_lab_code_scan','ydental_lab_post_fit_repair'}
# Text allowed in clear is technical state/model/enum data, not clinical content or identifiers.
CLEAR_TEXT={'state','move_state','payment_state','move_type','type','model','res_model','res_field','mimetype',
 'ydental_state','ydental_kind','ydental_category','ydental_level','ydental_method','ydental_outcome',
 'ydental_event_type','ydental_source_model','ydental_source_namespace','ydental_source','ydental_result',
 'ydental_timezone','ydental_channel_mode','ydental_appointment_status','ydental_rework_kind',
 'ydental_exception_disposition','ydental_phone_status','ydental_event','operation','module','name_module',
 'ydental_lab_contact_stage','ydental_external_mode','ydental_followup_type','ydental_channel','ydental_operation','ydental_mode'}
# Narrow native tables related to this new synthetic target and its module metadata.
NATIVE_BUSINESS={
 'ir_access':('TRUE',()),
 'res_users':('TRUE',()),
 'res_groups':('TRUE',()),'res_groups_users_rel':('TRUE',()),
 'res_groups_implied_rel':('TRUE',()),'res_company_users_rel':('TRUE',()),
 'res_company':('TRUE',()),
 'res_partner':('TRUE',()),
 'hr_employee':('TRUE',()),'hr_employee_public':None,
 'purchase_order':('id>=7',()),'purchase_order_line':('order_id>=7',()),
 'stock_warehouse':('TRUE',()),'stock_location':('TRUE',()),'stock_lot':('TRUE',()),
 'stock_quant':('TRUE',()),'stock_move':('TRUE',()),'stock_move_line':('TRUE',()),
 'stock_picking':('TRUE',()),'stock_picking_type':('TRUE',()),
 'product_product':('TRUE',()),'product_template':('TRUE',()),
 'product_pricelist':('TRUE',()),'product_pricelist_item':('TRUE',()),'product_supplierinfo':('TRUE',()),
 'uom_uom':('TRUE',()),'res_currency':('TRUE',()),
 'account_account':('TRUE',()),'account_account_res_company_rel':('TRUE',()),'account_journal':('TRUE',()),
 'account_move':('TRUE',()),'account_move_line':('TRUE',()),'account_payment':('TRUE',()),
 'account_partial_reconcile':('TRUE',()),'account_full_reconcile':('TRUE',()),
 'mail_activity':("res_model LIKE 'ydental.%'",()),
 'mail_message':("model LIKE 'ydental.%'",()),
 'mail_tracking_value':("mail_message_id IN (SELECT id FROM mail_message WHERE model LIKE 'ydental.%')",()),
 'ir_attachment':("res_model LIKE 'ydental.%' OR res_model IN ('account.move','purchase.order')",()),
}
TECH_TABLES={'ir_model','ir_model_fields','ir_model_access','ir_rule','ir_ui_view','ir_ui_menu','ir_model_data',
             'ir_module_module','ir_cron','ir_actions','ir_act_window',
             'ir_act_report_xml','report_paperformat','ir_act_url','res_lang'}

def canonical(v):
 if isinstance(v,(dt.datetime,dt.date,dt.time)):return v.isoformat()
 if isinstance(v,decimal.Decimal):return str(v)
 if isinstance(v,memoryview):return bytes(v).hex()
 if isinstance(v,bytes):return v.hex()
 if isinstance(v,dict):return {str(k):canonical(z) for k,z in sorted(v.items())}
 if isinstance(v,(tuple,list)):return [canonical(z) for z in v]
 return v

def raw(v):return json.dumps(canonical(v),sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def digest(v):return hashlib.sha256(raw(v)).hexdigest()
def file_digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def private_json(p):
 if PRIVATE.resolve() not in p.resolve().parents:raise RuntimeError('Input must remain under existing private project provider')
 st=p.lstat()
 if p.is_symlink() or st.st_uid!=os.geteuid() or st.st_mode&0o077:raise RuntimeError('Private input ownership/mode mismatch')
 return json.loads(p.read_text())
def write_new(p,v):
 if (PRIVATE/'verification').resolve() not in p.resolve().parents:raise RuntimeError('Snapshot output must remain under private verification directory')
 p.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
 b=(json.dumps(canonical(v),sort_keys=True,indent=2,ensure_ascii=False)+'\n').encode()
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
 return hashlib.sha256(b).hexdigest()
def projected_row(row,types):
 result={}
 for k,v in row.items():
  if v is None or isinstance(v,(bool,int,float,decimal.Decimal,dt.date,dt.time)) or k in CLEAR_TEXT:
   result[k]=canonical(v)
  else:
   # Noncredential text/json/binary content is represented by a private digest.
   result[k]={'sha256':digest(v),'type':types[k],'length':len(v) if hasattr(v,'__len__') else None}
 return result

def collect(args):
 if not re.fullmatch('[A-Za-z0-9_-]{1,60}',args.label):raise RuntimeError('Unsafe label')
 modules=set(args.modules.split(','))
 if not modules or not modules <= ALLOWED_MODULES:raise RuntimeError('Only the named S13 affected modules are allowed')
 baseline=args.phase=='baseline'
 if args.initial_s12_baseline and not baseline:raise RuntimeError('The initial provider flag is only for a baseline, never an upgrade snapshot')
 freeze={} if baseline else private_json(args.freeze_receipt.resolve())
 if not baseline and not(freeze.get('writers_quiescent') is True and freeze.get('candidate_commit')==args.candidate and freeze.get('database')==TARGET and freeze.get('database_oid')==OID and set(freeze.get('modules',[]))==modules):raise RuntimeError('Actual final freeze receipt mismatch; do not use an interim state as the final baseline')
 import subprocess
 # The S12 provider is only for the initial, pre-S13 baseline. Once S13
 # resources exist, a baseline must carry the actual current S13 scope too.
 runtime_path=PRIVATE/'runtime.json'
 if baseline and args.initial_s12_baseline:
  if runtime_path.exists():raise RuntimeError('S13 resources already exist; use the current S13 baseline scope')
  runtime_path=ROOT/'.local/s12/runtime.json'
 if baseline:
  info=runtime_path.lstat()
  if runtime_path.is_symlink() or info.st_uid!=os.geteuid() or info.st_mode&0o077:raise RuntimeError('Existing baseline provider is not private and owned')
  runtime=json.loads(runtime_path.read_text())
 else:runtime=private_json(runtime_path)
 branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()
 candidate=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
 if branch!='codex/s13-dl-p8-documents-actions-icons-r1' or candidate!=args.candidate:raise RuntimeError('Frozen execution candidate mismatch')
 changed=subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=ROOT,text=True).splitlines()
 untracked=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()
 if not baseline and any(p!='CURRENT_TASK.md' and not p.startswith('docs/reports/s13-dl-p8/') for p in changed+untracked):raise RuntimeError('Execution-relevant dirty paths')
 actual_core=subprocess.check_output(['git','-C',str(ROOT.parent),'rev-parse','HEAD'],text=True).strip()
 if actual_core!=CORE:raise RuntimeError('Pinned core mismatch')
 cfg=runtime['database']
 if cfg['name']!=TARGET or cfg['expected_oid']!=OID or str(cfg['expected_cluster_ref'])!=CLUSTER or cfg['user']!=TARGET:raise RuntimeError('Target configuration mismatch')
 result={'status':'INCOMPLETE_READONLY_SNAPSHOT','phase':args.phase,'label':args.label,'reviewer':'/root/runtime (stage adapter author; independent acceptance separate)',
  'started_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'database':TARGET,'database_oid':OID,'cluster':CLUSTER,
  'candidate_commit':candidate,'report_head':candidate,'core_commit':actual_core,'branch':branch,
  'runtime_config_sha256':file_digest(runtime_path),'runtime_application':runtime['application'],'modules':sorted(modules),'freeze_receipt_sha256':None if baseline else file_digest(args.freeze_receipt),'tool_sha256':file_digest(pathlib.Path(__file__)),
  'baseline_only_no_upgrade_authorization':baseline,'execution_dirty_paths':changed+untracked if baseline else [],'scope_id':runtime['scope']['id'],'scope_expires_at_utc':runtime['scope']['expires_at_utc'],
  'protected_scope':'All non-authentication project tables in the sole authorized target, native business/access/configuration and original files; S11 committed anchors preserved and S13 rows included',
  'database_write_performed':False,'service_or_upgrade_executed':False,'old_database_connections_performed':False,
  'secret_values_or_authentication_hashes_selected':False,'plan_id':'YD-S13-DL-P8','business':{},'technical_metadata':{},'omitted_columns':{},'attachments':[]}
 c=None
 try:
  c=psycopg2.connect(dbname=cfg['name'],host=cfg['host'],port=cfg['port'],user=cfg['user'],password=cfg['password'],connect_timeout=5,options='-c default_transaction_read_only=on -c statement_timeout=15000 -c TimeZone=UTC');c.set_session(readonly=True,isolation_level='REPEATABLE READ')
  with c.cursor() as q:
   q.execute("SELECT current_database(),(SELECT oid FROM pg_database WHERE datname=current_database()),(pg_control_system()).system_identifier::text,current_user,current_setting('transaction_read_only'),current_setting('transaction_isolation')");ident=q.fetchone()
   if ident!=(TARGET,OID,CLUSTER,TARGET,'on','repeatable read'):raise RuntimeError('Actual protected target/readonly transaction mismatch')
   result['identity']=ident
   q.execute('SELECT count(*) FROM ydental_patient WHERE id BETWEEN 26 AND 38');assert q.fetchone()[0]==13, 'Previously committed synthetic patients missing'
   q.execute("SELECT count(*) FROM ydental_treatment_event e JOIN ydental_treatment_fee f ON f.ydental_event_id=e.id WHERE e.id BETWEEN 26 AND 42 AND e.state='confirmed' AND f.ydental_amount=137.25");assert q.fetchone()[0]==17, 'Committed clinical event/fee anchor changed'
   q.execute('SELECT count(*) FROM ydental_lab_order WHERE id BETWEEN 16 AND 32');assert q.fetchone()[0]==17, 'Committed lab ancestry missing'
   q.execute("SELECT state,ydental_completed_event_id,ydental_completed_execution_id FROM ydental_followup WHERE id=35");assert q.fetchone()==('done',42,44), 'Preserved prior completed follow-up changed'
   q.execute("SELECT state,ydental_amount,ydental_settlement_source_id FROM ydental_lab_charge WHERE id=4");anchor=q.fetchone();assert anchor and anchor[0]=='billed' and anchor[1]==decimal.Decimal('28.50') and anchor[2]==5, 'Committed additional charge anchor changed'
   q.execute('SELECT count(*) FROM ydental_settlement_source WHERE (id=5 AND ydental_lab_charge_id=4 AND ydental_invoice_id=6 AND ydental_original_amount=28.5) OR (id=6 AND ydental_lab_charge_adjustment_id=3 AND ydental_invoice_id=7 AND ydental_original_amount=-5)');assert q.fetchone()[0]==2, 'Committed charge/credit source missing'
   q.execute("SELECT id,state,ydental_completed_event_id,ydental_completed_execution_id FROM ydental_followup WHERE id IN (24,26,78) ORDER BY id");assert q.fetchall()==[(24,'done',41,43),(26,'done',39,41),(78,'done',87,93)], 'Current committed follow-up anchors changed'
   q.execute("SELECT id,state,ydental_exam_validated_date FROM ydental_treatment_line WHERE id IN (7,8) ORDER BY id");assert q.fetchall()==[(7,'done',dt.date(2026,10,26)),(8,'done',dt.date(2026,10,27))], 'Committed T11 continuation anchors changed'
   q.execute("SELECT id,ydental_event_id,ydental_amount FROM ydental_treatment_fee WHERE id IN (88,89) ORDER BY id");assert q.fetchall()==[(88,88,decimal.Decimal('35.50')),(89,89,decimal.Decimal('62.75'))], 'Committed T11 fee anchors changed'
   result['current_new_target_anchors_and_uid335_native_protection_added']=True
   q.execute("SELECT id,state,ydental_appointment_status,ydental_completed_event_id FROM ydental_followup WHERE id IN (52,53) ORDER BY id");assert q.fetchall()==[(52,'to_notify','not_arrived',None),(53,'to_notify','arrived',None)], 'Actual appointment day-end outcomes changed'
   q.execute("SELECT id,state,ydental_source_event_id,ydental_inventory_event_id,ydental_fit_event_id FROM ydental_lab_order WHERE id IN (78,79,80) ORDER BY id");assert q.fetchall()==[(78,'available',86,227,None),(79,'available',111,316,None),(80,'cancelled',112,None,None)], 'Actual ordinary F4 branch anchors changed'
   result['committed_business_anchors_verified']=True
   q.execute("SELECT table_name,column_name,data_type FROM information_schema.columns WHERE table_schema='public' ORDER BY table_name,ordinal_position");schema={}
   for t,n,typ in q.fetchall():schema.setdefault(t,{})[n]=typ
   if 'ir_access' not in schema:raise RuntimeError('Locked core native ir.access permission table missing')
   selected={t:('TRUE',()) for t in schema if t.startswith('ydental_') and t not in EXCLUDED_TABLES and not DROP.search(t)}
   selected.update({t:w for t,w in NATIVE_BUSINESS.items() if t in schema and w is not None})
   technical_where={
    'ir_model':"model LIKE 'ydental.%'",
    'ir_model_fields':"model LIKE 'ydental.%' OR name LIKE 'ydental_%'",
    'ir_model_access':"model_id IN (SELECT id FROM ir_model WHERE model LIKE 'ydental.%')",
    'ir_rule':"model_id IN (SELECT id FROM ir_model WHERE model LIKE 'ydental.%')",
    'ir_ui_view':"model LIKE 'ydental.%' OR id IN (SELECT res_id FROM ir_model_data WHERE model='ir.ui.view' AND module LIKE 'ydental%')",
    'ir_ui_menu':"id IN (SELECT res_id FROM ir_model_data WHERE model='ir.ui.menu' AND module LIKE 'ydental%')",
    'ir_model_data':"module LIKE 'ydental%'",
    'ir_module_module':'TRUE',
    'ir_cron':"id IN (SELECT res_id FROM ir_model_data WHERE model='ir.cron' AND module LIKE 'ydental%')",
    'ir_actions':"id IN (SELECT res_id FROM ir_model_data WHERE model LIKE 'ir.actions.%' AND module LIKE 'ydental%')",
    'ir_act_window':"id IN (SELECT res_id FROM ir_model_data WHERE model='ir.actions.act_window' AND module LIKE 'ydental%')",
    'ir_act_report_xml':'TRUE',
    'report_paperformat':'TRUE',
    'ir_act_url':'TRUE',
    'res_lang':'TRUE',
   }
   for t,where in technical_where.items():
    if t in schema:selected[t]=(where,())
   for table,(where,params) in sorted(selected.items()):
    info=schema[table];omit=[n for n in info if DROP.search(n) or (table=='ir_attachment' and n in ('access_token',))]
    cols=[n for n in info if n not in omit];result['omitted_columns'][table]=omit
    stmt=sql.SQL('SELECT {} FROM {} WHERE '+where).format(sql.SQL(',').join(map(sql.Identifier,cols)),sql.Identifier('public',table))
    q.execute(stmt,params) if params else q.execute(stmt)
    data=q.fetchmany(20001)
    if len(data)>20000:raise RuntimeError('Protected table bound exceeded: '+table)
    values=[]
    for vals in data:
     row=dict(zip(cols,vals));v=projected_row(row,info)
     key=str(row['id']) if 'id' in row else digest(v)
     values.append({'key':key,'fields':v,'sha256':digest(v)})
    values.sort(key=lambda v:v['key']);dest=result['technical_metadata'] if table in TECH_TABLES else result['business'];dest[table]={'row_count':len(values),'sha256':digest(values),'rows':values}
   # Values for credentials are never selected. Exact configured booleans are enough.
   q.execute("SELECT key,value IS NOT NULL AND value<>'' FROM ir_config_parameter WHERE key LIKE 'ydental%' ORDER BY key")
   result['config_presence']=[{'key':k,'configured':b} for k,b in q.fetchall()]
   q.execute("SELECT key,value FROM ir_config_parameter WHERE key IN ('ydental_followup_test.local_sink_enabled','web.base.url','auth_signup.invitation_scope') ORDER BY key")
   result['nonsecret_config']=[{'key':k,'value':v} for k,v in q.fetchall()]
   q.execute('SELECT count(*) FROM ir_mail_server');result['smtp_server_count']=q.fetchone()[0]
   if result['smtp_server_count']!=0:raise RuntimeError('External SMTP boundary changed')
   q.execute("SELECT c.relname,con.conname,pg_get_constraintdef(con.oid) FROM pg_constraint con JOIN pg_class c ON c.oid=con.conrelid JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relname LIKE 'ydental_%' ORDER BY c.relname,con.conname");result['business_schema_constraints']=q.fetchall()
   q.execute("SELECT tablename,indexname,indexdef FROM pg_indexes WHERE schemaname='public' AND tablename LIKE 'ydental_%' ORDER BY tablename,indexname");result['business_schema_indexes']=q.fetchall()
   # Hash only attachments belonging to protected synthetic business objects. No token/url/body output.
   q.execute("SELECT id,store_fname,db_datas FROM ir_attachment WHERE res_model LIKE 'ydental.%' OR res_model IN ('account.move','purchase.order') ORDER BY id")
   filestore=ROOT/'.local/s11/new-target-data/filestore'/TARGET
   for ident,stored,binary in q.fetchall():
    item={'attachment_id':ident,'file_present':False,'db_data_present':binary is not None}
    if binary is not None:item['db_data_sha256']=hashlib.sha256(bytes(binary)).hexdigest()
    if stored:
     rel=pathlib.PurePosixPath(stored)
     if rel.is_absolute() or any(x in ('..','.') for x in rel.parts):raise RuntimeError('Unsafe native filestore path')
     path=filestore.joinpath(*rel.parts)
     if not path.is_file() or path.is_symlink() or filestore.resolve() not in path.resolve().parents:raise RuntimeError('Protected attachment file missing or escaped')
     item.update(file_present=True,file_size=path.stat().st_size,file_sha256=file_digest(path))
    result['attachments'].append(item)
  result['status']='READONLY_PROTECTED_BASELINE_COMPLETE_NO_UPGRADE_AUTHORIZATION' if baseline else 'READONLY_PROTECTED_UPGRADE_SNAPSHOT_COMPLETE'
 except Exception as e:
  result['status']='READONLY_SNAPSHOT_FAILED_NO_UPGRADE_AUTHORIZATION';result['error_class']=type(e).__name__
  result['safe_error']=str(e).splitlines()[0][:180] if str(e) else ''
 finally:
  if c:c.rollback();result['rollback_idle']=c.get_transaction_status()==psycopg2.extensions.TRANSACTION_STATUS_IDLE;c.close();result['connection_closed']=bool(c.closed)
  result['finished_at_utc']=dt.datetime.now(dt.timezone.utc).isoformat()
 output=PRIVATE/'verification'/('upgrade-'+args.label+'-'+args.phase+'.json');h=write_new(output,result)
 print(json.dumps({'status':result['status'],'output':str(output.relative_to(ROOT)),'sha256':h,'business_table_count':len(result['business']),'metadata_table_count':len(result['technical_metadata']),'error_class':result.get('error_class')}))
 return 0 if result['status'] in ('READONLY_PROTECTED_UPGRADE_SNAPSHOT_COMPLETE','READONLY_PROTECTED_BASELINE_COMPLETE_NO_UPGRADE_AUTHORIZATION') else 2

def compare(args):
 pre=private_json(args.pre.resolve());post=private_json(args.post.resolve())
 if pre['status']!='READONLY_PROTECTED_UPGRADE_SNAPSHOT_COMPLETE' or post['status']!='READONLY_PROTECTED_UPGRADE_SNAPSHOT_COMPLETE':raise RuntimeError('Incomplete snapshots')
 if pre.get('phase')!='pre' or post.get('phase')!='post':raise RuntimeError('Expected distinct pre/post phases')
 for k in ('candidate_commit','database','database_oid','cluster','core_commit','runtime_config_sha256','runtime_application','modules','freeze_receipt_sha256'):
  if pre[k]!=post[k]:raise RuntimeError('Pre/post identity/freeze mismatch: '+k)
 result={'reviewer':'/root/runtime (stage adapter author; independent acceptance separate)','status':'DIFF_REQUIRES_INDEPENDENT_CLASSIFICATION','pre_sha256':file_digest(args.pre),'post_sha256':file_digest(args.post),'database_write_performed':False,'database_connection_performed':False,'business_changes':{},'metadata_changes':{},'other_changes':{}}
 for group,out in [('business','business_changes'),('technical_metadata','metadata_changes')]:
  for table in sorted(set(pre[group])|set(post[group])):
   left={v['key']:v for v in pre[group].get(table,{}).get('rows',[])};right={v['key']:v for v in post[group].get(table,{}).get('rows',[])}
   added=sorted(set(right)-set(left));removed=sorted(set(left)-set(right));changed={}
   for k in sorted(set(left)&set(right)):
    if left[k]['sha256']!=right[k]['sha256']:
     changed[k]=[f for f in sorted(set(left[k]['fields'])|set(right[k]['fields'])) if left[k]['fields'].get(f)!=right[k]['fields'].get(f)]
   if added or removed or changed:result[out][table]={'added_keys':added,'removed_keys':removed,'changed_fields_by_key':changed}
 for k in ('attachments','config_presence','nonsecret_config','smtp_server_count','business_schema_constraints','business_schema_indexes','omitted_columns'):
  if pre[k]!=post[k]:result['other_changes'][k]={'before_sha256':digest(pre[k]),'after_sha256':digest(post[k])}
 if not result['business_changes'] and not result['other_changes']:result['status']='PROTECTED_BUSINESS_IDENTICAL_METADATA_REVIEW_REQUIRED'
 h=write_new(args.output.resolve(),result);print(json.dumps({'status':result['status'],'output':str(args.output),'sha256':h,'changed_business_tables':list(result['business_changes']),'changed_metadata_tables':list(result['metadata_changes']),'other_changed_sections':list(result['other_changes'])}));return 0

def main():
 p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
 c=sub.add_parser('collect');c.add_argument('--phase',choices=['pre','post','baseline'],required=True);c.add_argument('--label',required=True);c.add_argument('--candidate',required=True);c.add_argument('--modules',required=True);c.add_argument('--freeze-receipt',type=pathlib.Path);c.add_argument('--initial-s12-baseline',action='store_true',help='Only before any S13 runtime exists; retain the explicit initial S12 scope')
 d=sub.add_parser('compare');d.add_argument('--pre',type=pathlib.Path,required=True);d.add_argument('--post',type=pathlib.Path,required=True);d.add_argument('--output',type=pathlib.Path,required=True)
 a=p.parse_args();return collect(a) if a.command=='collect' else compare(a)
if __name__=='__main__':raise SystemExit(main())

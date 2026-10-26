import argparse,datetime as dt,hashlib,json,os,subprocess,stat
from pathlib import Path
R=Path.cwd();P=R/'.local/dl-p12'
p=argparse.ArgumentParser();p.add_argument('--probe',required=True);p.add_argument('--checkpoint',required=True);p.add_argument('--label',required=True);a=p.parse_args()
assert a.label.replace('-','').isalnum()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name):
 path=R/name if not Path(name).is_absolute() else Path(name);assert P in path.parents
 st=path.lstat();assert stat.S_ISREG(st.st_mode) and st.st_uid==os.geteuid() and not st.st_mode&0o077 and not path.is_symlink();return json.loads(path.read_text())
r=load('.local/dl-p12/runtime.json');probe=load(a.probe);cp=load(a.checkpoint)
head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();assert head==r['candidate_commit']==probe['candidate_commit']
assert subprocess.check_output(['git','branch','--show-current'],text=True).strip()=='codex/s13-dl-p12-settlement-readonly-actions-spacing-r1'
assert subprocess.check_output(['git','-C',str(R.parent),'rev-parse','HEAD'],text=True).strip()=='f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb'
assert probe['status']=='READONLY_TARGET_IDENTITY_AND_GRANTS_OBSERVED' and probe['rollback_idle'] and probe['connection_closed']
ident=probe['identity'];assert (ident['name'],ident['role'],ident['oid'],ident['cluster_ref'],ident['read_only'],ident['isolation'])==('ydental_s11_synth_20261023_01','ydental_s11_synth_20261023_01',2171423,'7694897083368259627','on','repeatable read')
assert not any(probe['role'][k] for k in ['rolsuper','rolcreatedb','rolcreaterole','rolreplication','rolbypassrls']);assert probe['role']['rolcanlogin']
assert probe['database_ownership']==[{'owns_only_target':True,'owned_database_count':1}]
assert all(probe['target_grants'].values()) and probe['target_object_ownership']['object_count']==probe['target_object_ownership']['owned_or_owner_role_count']
assert probe['smtp_servers']==0 and not any(row['configured'] for row in probe['outbound_parameter_flags']) and not any(row['ydental_enabled'] for row in probe['notification_policies'])
assert probe['s11_clock_memberships_including_inactive']==0
assert all(row['state']=='installed' for row in probe['modules'])
assert cp['rollback_idle'] and cp['connection_closed'] and cp['database_oid']==2171423
assert len(cp['business'])==145 and len(cp['technical_metadata'])==13 and sum(x['file_present'] for x in cp['attachments'])==83
scope=r['scope'];now=dt.datetime.now(dt.UTC);assert scope['plan_id']=='YD-S13-DL-P12' and not scope['platform_permission_claimed']
assert dt.datetime.fromisoformat(scope['issued_at_utc'])<now<dt.datetime.fromisoformat(scope['expires_at_utc'])
assert dt.timedelta()<=now-dt.datetime.fromisoformat(probe['finished_at_utc'])<=dt.timedelta(minutes=30)
assert r['application']=={'host':'127.0.0.1','port':18411,'workers':0,'max_cron_threads':0,'db_maxconn':16,'dbfilter':'^ydental_s11_synth_20261023_01$','list_db':False}
old=json.loads((R/'.local/dl-p11/acceptance/final-complete-physical-snapshot.json').read_text())
sections=['business','technical_metadata','attachments','config_presence','nonsecret_config','smtp_server_count','business_schema_constraints','business_schema_indexes','omitted_columns']
# First checkpoint remains baseline. Later admissions classify changed audit/native metadata separately.
comparisons={k:cp[k]==old[k] for k in sections}
v={'status':'DLP12_RUNTIME_ADMISSION_REVIEWED','reviewer':'/root/acceptance_p12','candidate_commit':head,'probe_sha256':sha(R/a.probe),'checkpoint_sha256':sha(R/a.checkpoint),'runtime_sha256':sha(P/'runtime.json'),'launcher_sha256':sha(R/'scripts/s13_dl_p12/launcher.py'),'reviewed_no_product_or_test_tool_implementation':True,'shared_os_not_isolation':True,'reviewed_at_utc':now.isoformat(),'source_runtime_adapters_reviewed':True,'scope_id':scope['id'],'scope_expiry_unchanged':scope['expires_at_utc'],'new_scope_not_platform_permission_claim':True,'current_role_native_grants_ownership_target_verified':True,'initial_checkpoint_comparison_P11_final':comparisons,'not_product_or_user_effect_acceptance':True,'allowed_actions':'Normal authentication/store switch; original settlement GET/patient search/explicit selection/read-only fee trace and pagination/other-store summary. Necessary native settlement XML load separately frozen pre/exit/post. No document/print/template/inherited/stock/economic write.','audit_tool_sha256':sha(Path(__file__))}
path=P/'acceptance'/(a.label+'-runtime-review.json');raw=(json.dumps(v,indent=2,sort_keys=True)+'\n').encode();fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.write(fd,raw);os.close(fd);print(json.dumps({'status':v['status'],'path':str(path.relative_to(R)),'sha256':sha(path),'candidate':head}))

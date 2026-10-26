from pathlib import Path
import json,hashlib,os,collections,datetime
from PIL import Image
r=Path.cwd();ev=r/'.local/dl-p9/testing/evidence'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
clients=[];pngs=[]
for p in sorted(ev.glob('*/result.json')):
 if p.parent.name.startswith('process-'):continue
 v=json.loads(p.read_text());process=ev/('process-'+p.parent.name);end=process/'result.json';start=process/'start.json';s=json.loads(start.read_text());e=json.loads(end.read_text()) if end.exists() else None
 if e is None:
  assert p.parent.name=='after-webkit-stress-v1','Unobserved client exit must remain UNKNOWN; do not infer 143'
  observed=json.loads((r/'.local/dl-p9/testing/webkit-stress-v1-wrapper-termination-observed.json').read_text())
  assert observed['actual_exec_command_exit_code']==143 and observed['node_exit_code']=='UNKNOWN'
 sources=list(process.glob('executed-1-*.cjs'));assert len(sources)==1 and sha(sources[0])==v['source_sha256']
 for x in v.get('screenshots',[]):
  im=r/x['file'];assert im.exists() and sha(im)==x['sha256'] and im.stat().st_size==x['bytes']
  with Image.open(im) as z:z.load();assert z.format=='PNG'
  pngs.append({'source':x['file'],'sha256':x['sha256'],'bytes':x['bytes']})
 clients.append({'label':p.parent.name,'engine':v['engine'],'mode':v['mode'],'stage':v['stage'],'candidate':v['binding']['candidate_commit'],'actor':v.get('actor'),'status':v['status'],'checks':len(v.get('checks',[])),'screenshots':len(v.get('screenshots',[])),'browser_result_sha256':sha(p),'actual_node_exit':e['actual_child_returncode'] if e else 'UNKNOWN','wrapper_observed_exit':(0 if e['actual_child_returncode']==0 else 2) if e else 143,'process_receipt_sha256':sha(end) if e else None,'start_receipt_sha256':sha(start),'native':v.get('native_main_lifecycle'),'source_sha256':v['source_sha256'],'executed_source':str(sources[0].relative_to(r)),'command':s['command'],'business_write_requests':v['business_write_requests'],'guard_blocks':len(v.get('guard_blocks',[]))})
assert len({x['source'] for x in pngs})==len(pngs)
value={'status':'P9_ALL_ACTUAL_CLIENT_RAW_SOURCE_EXIT_AND_UNIQUE_PNG_INDEX','generated_at_utc':datetime.datetime.now(datetime.UTC).isoformat(),'clients':clients,'client_count':len(clients),'node_exit_counts':dict(collections.Counter(str(x['actual_node_exit']) for x in clients)),'native_exit_counts':dict(collections.Counter(str(x['native'].get('exitCode')) if x['native'] else 'NO_LIFECYCLE' for x in clients)),'original_png_count':len(pngs),'unique_png_sha_count':len({x['sha256'] for x in pngs}),'pngs':pngs,'whole_wrapper_failure_not_resigned':True,'all_business_write_requests':sum(x['business_write_requests'] for x in clients),'all_guard_blocks':sum(x['guard_blocks'] for x in clients)}
p=r/'.local/dl-p9/testing/client-index-final-v2.json'
with os.fdopen(os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'w') as f:json.dump(value,f,ensure_ascii=False,indent=2)
print(json.dumps({k:value[k] for k in ['client_count','node_exit_counts','native_exit_counts','original_png_count','unique_png_sha_count','all_business_write_requests','all_guard_blocks']}));print(sha(p))

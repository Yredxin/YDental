from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import hashlib,json,subprocess
from pathlib import Path
root=Path.cwd();src=Path('/tmp/ydental-s07-rework-sources');out=root/'docs/evidence/s07-rework/sources'
requests={'plan23':'repos/Yredxin/YDental/issues/23','comments23':'repos/Yredxin/YDental/issues/23/comments?per_page=100','issue31':'repos/Yredxin/YDental/issues/31','comments31':'repos/Yredxin/YDental/issues/31/comments?per_page=100'}
def read(item):
 name,url=item
 for retry in range(3):
  p=subprocess.run(['gh','api',url],capture_output=True,text=True,timeout=45)
  if p.returncode==0:
   v=json.loads(p.stdout);(out/(name+'-final.json')).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');return name,v
 raise RuntimeError(name+' fetch failed')
with ThreadPoolExecutor(max_workers=4) as ex:values=dict(ex.map(read,requests.items()))
for n,k in ((23,'plan23'),(31,'issue31')):assert values[k]['body']==json.loads((src/f'{n}.json').read_text())['body']
for n,k in ((23,'comments23'),(31,'comments31')):
 old=[c for pg in json.loads((src/f'{n}-comments.json').read_text()) for c in pg]
 assert len(old)==len(values[k]);assert [(c['id'],c['body']) for c in old]==[(c['id'],c['body']) for c in values[k]]
oldproject=json.loads((src/'project-before.json').read_text())
for n in ('final','second'):
 for tries in range(3):
  p=subprocess.run(['gh','api','graphql','-F','query=@docs/evidence/s00-a/project-query.graphql'],capture_output=True,text=True,timeout=45)
  if not p.returncode:break
 assert p.returncode==0
 v=json.loads(p.stdout);assert v==oldproject
 (out/('project-'+n+'-read.json')).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
summary={'result':'PASS','read_utc':datetime.now(timezone.utc).isoformat(),'all_bodies_and_comment_bodies_unchanged':True,'comment_ids':{k:[c['id'] for c in values[k]] for k in ('comments23','comments31')},'two_full_project_reads_deep_equal_to_before':True,'project_mutations':0,'workflow_mutations':0}
(out.parent/'source-final-check.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))

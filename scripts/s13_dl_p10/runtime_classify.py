"""Offline full projection comparison; facts only, no automatic acceptance."""
import argparse,collections,hashlib,json,os
from pathlib import Path
root=Path.cwd();private=root/'.local/dl-p10'
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--before',type=Path,required=True);p.add_argument('--after',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
def load(path):
 path=path.resolve();info=path.lstat()
 allowed=(private.resolve(),(root/'.local/dl-p9').resolve())
 if not any(parent in path.parents for parent in allowed) or path.is_symlink() or info.st_uid!=os.geteuid() or info.st_mode&0o077:raise RuntimeError('Explicit private stage snapshot required')
 v=json.loads(path.read_text());assert v.get('connection_closed') and v.get('rollback_idle')
 assert v.get('status') in ('READONLY_PROTECTED_BASELINE_COMPLETE_NO_UPGRADE_AUTHORIZATION','READONLY_PROTECTED_UPGRADE_SNAPSHOT_COMPLETE')
 return v
left=load(a.before);right=load(a.after)
for k in ('database','database_oid','cluster','core_commit'):assert left[k]==right[k],k
out={'status':'FULL_DIFF_REQUIRES_INDEPENDENT_CLASSIFICATION','layer':'OFFLINE_FULL_PROJECTED_ROWS_AND_FILE_HASHES','tool_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'before_sha256':hashlib.sha256(a.before.read_bytes()).hexdigest(),'after_sha256':hashlib.sha256(a.after.read_bytes()).hexdigest(),'database_connections':0,'business_changes':{},'technical_changes':{},'other_changes':{},'projection_table_counts':{}}
for group,key in (('business','business_changes'),('technical_metadata','technical_changes')):
 assert set(left[group])==set(right[group]),'Projection tables changed: '+group
 out['projection_table_counts'][group]=len(left[group])
 for table in sorted(left[group]):
  before={v['key']:v for v in left[group][table]['rows']};after={v['key']:v for v in right[group][table]['rows']}
  added=sorted(set(after)-set(before));removed=sorted(set(before)-set(after));changed={}
  for ident in sorted(set(before)&set(after)):
   fields1=before[ident]['fields'];fields2=after[ident]['fields']
   if fields1!=fields2:changed[ident]=[k for k in sorted(set(fields1)|set(fields2)) if fields1.get(k)!=fields2.get(k)]
  if added or removed or changed:out[key][table]={'added_keys':added,'removed_keys':removed,'changed_fields_by_key':changed}
  if table=='ydental_access_audit':
   summary=collections.Counter(tuple(after[k]['fields'].get(f) for f in ('ydental_event','ydental_category','ydental_result')) for k in added)
   out['audit']={'before_count':len(before),'after_count':len(after),'new_count':len(added),'old_rows_unchanged_and_present':not removed and not changed,'new_event_category_result':[{'event':k[0],'category':k[1],'result':k[2],'count':v} for k,v in sorted(summary.items(),key=str)]}
for key in ('attachments','config_presence','nonsecret_config','smtp_server_count','business_schema_constraints','business_schema_indexes','omitted_columns'):
 if left[key]!=right[key]:out['other_changes'][key]={'before_sha256':hashlib.sha256(json.dumps(left[key],sort_keys=True).encode()).hexdigest(),'after_sha256':hashlib.sha256(json.dumps(right[key],sort_keys=True).encode()).hexdigest()}
refs=[v for v in right['attachments'] if v['file_present']]
out['attachment_reference_count']=len(refs);out['attachment_reference_size_sha_pairs_unchanged']=left['attachments']==right['attachments'];out['unique_physical_path_count_not_derivable_from_redacted_projection']=True
outpath=a.output.resolve()
if (private/'verification').resolve() not in outpath.parents:raise RuntimeError('Output must be fresh P10 verification path')
b=(json.dumps(out,sort_keys=True,indent=2)+'\n').encode()
with os.fdopen(os.open(outpath,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as stream:stream.write(b);stream.flush();os.fsync(stream.fileno())
print(json.dumps({'status':out['status'],'sha256':hashlib.sha256(b).hexdigest(),'business_tables_changed':list(out['business_changes']),'technical_tables_changed':list(out['technical_changes']),'other_sections_changed':list(out['other_changes']),'audit':out.get('audit')}))

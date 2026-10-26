"""Build one private P10 viewing package from explicitly selected original PNGs."""
import argparse,datetime,hashlib,json,os,zipfile
from pathlib import Path
from PIL import Image
ROOT=Path.cwd();BASE=ROOT/'.local/dl-p10'
def digest(raw):return hashlib.sha256(raw).hexdigest()
def encoded(v):return (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode()
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--selection',required=True);parser.add_argument('--revision',default='r1');args=parser.parse_args()
 assert args.revision in ('r1','r2','r3')
 config=json.loads((ROOT/args.selection).read_text());selected=[];members={};measurements=[]
 for entry in config['screenshots']:
  client=BASE/'testing/evidence'/entry['client'];source=client/'result.json';result=json.loads(source.read_text())
  rows=[x for x in result['screenshots'] if Path(x['file']).name==entry['filename']];assert len(rows)==1
  meta=rows[0];p=ROOT/meta['file'];raw=p.read_bytes();assert digest(raw)==meta['sha256'] and len(raw)==meta['bytes']
  with Image.open(p) as im:im.load();assert im.format=='PNG'
  member='images/%03d-%s-%s'%(len(selected)+1,entry['client'],p.name)
  viewport=meta.get('viewport',meta.get('observed',{}).get('viewport'))
  assert viewport is not None and 'scrollY' in viewport,'Actual screenshot viewport/scrollY required'
  row={'member':member,'source_client':entry['client'],'source_file':meta['file'],'source_result_sha256':digest(source.read_bytes()),'source_status':result['status'],'candidate':meta.get('candidate',result['binding']['candidate_commit']),'actor':meta.get('actor',result.get('actor')),'actual_engine':result['actual_engine_version'],'engine':result['engine'],'stage':result['stage'],'mode':result['mode'],'viewport':viewport,'layer':meta['layer'],'condition':entry['condition'],'bytes':len(raw),'sha256':digest(raw),'image_pixels_edited':False}
  selected.append(row);members[member]=raw
 for name in config.get('measurements',[]):
  p=ROOT/name;assert BASE in p.parents and p.suffix=='.json';v=json.loads(p.read_text());measurements.append({'source':name,'sha256':digest(p.read_bytes()),'data':v})
 members={'README.md':config['readme'].encode(),'SCREENSHOTS.json':encoded(selected),'SPACING.json':encoded({'ownership':config['ownership'],'measurements':measurements}),**members}
 # Every payload is a selected PNG or a bounded prose/measurement index. No CSV,
 # PDFs, configs, DB projections, requests, sessions, programs or fonts belong.
 assert all(n.endswith('.png') or n in ('README.md','SCREENSHOTS.json','SPACING.json') for n in members)
 members['MANIFEST.json']=encoded({'manifest_excludes_itself':True,'nonself_members':[{'path':n,'bytes':len(b),'sha256':digest(b)} for n,b in members.items()]})
 out=BASE/'viewing';out.mkdir(mode=0o700,exist_ok=True)
 target=out/('S13-DL-P10-view-only-'+datetime.datetime.now(datetime.UTC).strftime('%Y%m%d')+'-'+args.revision+'.zip')
 with target.open('xb') as stream:
  with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
   for name,raw in members.items():archive.writestr(name,raw)
 target.chmod(0o400)
 with zipfile.ZipFile(target) as archive:
  assert archive.testzip() is None and set(archive.namelist())==set(members)
  for name,raw in members.items():assert archive.read(name)==raw
 receipt={'status':'PRIVATE_VIEWING_PACKAGE_CONSTRUCTED_NOT_INDEPENDENT_ACCEPTANCE','file':str(target.relative_to(ROOT)),'bytes':target.stat().st_size,'sha256':digest(target.read_bytes()),'members':len(members),'PNG_count':len(selected),'measurement_records':len(measurements),'public_upload':False,'image_pixels_edited':False}
 p=out/('constructor-'+args.revision+'-result.json')
 with os.fdopen(os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600),'wb') as stream:stream.write(encoded(receipt))
 print(json.dumps(receipt))
if __name__=='__main__':main()

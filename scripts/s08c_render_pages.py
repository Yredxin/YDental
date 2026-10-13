"""Offline page geometry, Chinese text and raster checks of actual synthetic PDFs."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import subprocess
import unicodedata

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.local/s00-b-deps/verify-lib'))
import pymupdf
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('result',type=Path);args=parser.parse_args()
source=json.loads(args.result.read_text());assert source['database'].startswith('ydental_s08c_test_')
summary={'database':source['database'],'tested_commit':source['tested_commit'],'pdfs':[],'visual_review':'PENDING','validator_commit':subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip(),'renderer_version':pymupdf.VersionBind,'result':'RUNNING'}
try:
 for artifact in source['artifacts']:
  path=ROOT/artifact['path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==artifact['sha256']
  doc=pymupdf.open(path);item={'path':artifact['path'],'sha256':artifact['sha256'],'pages':[],'fonts':[]};summary['pdfs'].append(item)
  text=''
  for i,page in enumerate(doc):
   words=page.get_text('words');txt=unicodedata.normalize('NFKC',page.get_text());text+=txt
   png=path.with_name(path.stem+'-page-%02d.png'%(i+1));page.get_pixmap(matrix=pymupdf.Matrix(1.5,1.5),alpha=False).save(png)
   page_record={'number':i+1,'path':str(png.relative_to(ROOT)),'sha256':hashlib.sha256(png.read_bytes()).hexdigest(),'characters':len(txt),'a4':abs(page.rect.width-595)<2 and abs(page.rect.height-842)<2,'size':[page.rect.width,page.rect.height],'overlap_pairs':[]};item['pages'].append(page_record)
   assert len(words)>10,(path,i,'empty or only fragment page')
   assert '\ufffd' not in txt,(path,i,'replacement glyph')
   assert all(w[0]>=0 and w[1]>=0 and w[2]<=page.rect.width+1 and w[3]<=page.rect.height+1 for w in words),(path,i,'clipped words')
   for left in range(len(words)):
    a=words[left];area_a=(a[2]-a[0])*(a[3]-a[1])
    for right in range(left+1,len(words)):
     b=words[right]
     if a[4]==b[4]:continue
     width=max(0,min(a[2],b[2])-max(a[0],b[0]));height=max(0,min(a[3],b[3])-max(a[1],b[1]))
     if width*height>.35*min(area_a,(b[2]-b[0])*(b[3]-b[1])):
      page_record['overlap_pairs'].append({'word_indices':[left,right],'bounds':[list(a[:4]),list(b[:4])]})
   assert not page_record['overlap_pairs'],(path,i,'overlapping PDF text positions')
   item['fonts'].extend(f[3] for f in page.get_fonts())
  assert re.search('[\u4e00-\u9fff]',text),path
  assert '演示' in text and 'SHA256' in text,(path,'missing warning or provenance')
  assert any('Noto' in f for f in item['fonts']),(path,'Chinese font not embedded')
  txtpath=path.with_suffix('.txt');txtpath.write_text(text)
  item['text']=str(txtpath.relative_to(ROOT));item['fonts']=sorted(set(item['fonts']));item['result']='PASS'
 summary['result']='PASS'
except Exception as error:
 summary['result']='FAIL';summary['failure']={'type':type(error).__name__,'detail':str(error)}
finally:
 target=args.result.with_name('rendered-pages.json')
 # Rechecks retain the earlier validator result as independent evidence.
 if target.exists():
  from datetime import datetime,timezone
  target=target.with_name('rendered-pages-recheck-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.json')
 target.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'result':summary['result'],'pdfs':len(summary['pdfs']),'pages':sum(len(p['pages']) for p in summary['pdfs']),'visual_review':'PENDING'}))
assert summary['result']=='PASS',summary.get('failure')

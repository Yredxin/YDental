"""Offline rendering of actual generated synthetic PDFs; no database access."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.local/s00-b-deps/verify-lib'))
import fitz
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('result',type=Path);args=parser.parse_args()
source=json.loads(args.result.read_text());assert source['database'].startswith('ydental_s08c_test_')
summary={'database':source['database'],'tested_commit':source['tested_commit'],'pdfs':[],'visual_review':'PENDING'}
for artifact in source['artifacts']:
 path=ROOT/artifact['path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==artifact['sha256']
 doc=fitz.open(path);item={'path':artifact['path'],'sha256':artifact['sha256'],'pages':[],'fonts':[]}
 text=''
 for i,page in enumerate(doc):
  words=page.get_text('words');assert len(words)>10,(path,i,'empty page')
  txt=page.get_text();text+=txt
  assert '\ufffd' not in txt,(path,i,'replacement glyph')
  assert all(w[0]>=0 and w[1]>=0 and w[2]<=page.rect.width+1 and w[3]<=page.rect.height+1 for w in words),(path,i,'clipped words')
  png=path.with_name(path.stem+'-page-%02d.png'%(i+1));page.get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False).save(png)
  item['pages'].append({'number':i+1,'path':str(png.relative_to(ROOT)),'sha256':hashlib.sha256(png.read_bytes()).hexdigest(),'characters':len(txt),'a4':abs(page.rect.width-595)<2 and abs(page.rect.height-842)<2,'size':[page.rect.width,page.rect.height]})
  item['fonts'].extend(f[3] for f in page.get_fonts())
 assert re.search('[\u4e00-\u9fff]',text),path
 assert '演示' in text and 'SHA256' in text,(path,'missing warning or provenance')
 assert any('Noto' in f for f in item['fonts']),(path,'Chinese font not embedded')
 txtpath=path.with_suffix('.txt');txtpath.write_text(text)
 item['text']=str(txtpath.relative_to(ROOT));item['fonts']=sorted(set(item['fonts']));item['result']='PASS';summary['pdfs'].append(item)
summary['result']='PASS';target=args.result.with_name('rendered-pages.json');target.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'result':'PASS','pdfs':len(summary['pdfs']),'pages':sum(len(p['pages']) for p in summary['pdfs']),'visual_review':'PENDING'}))

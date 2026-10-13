"""Offline page geometry, Chinese text and raster checks of actual synthetic PDFs."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import subprocess
import unicodedata
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.local/s00-b-deps/verify-lib'))
import pymupdf

def normalized(value):
 value=unicodedata.normalize('NFKC',str(value)).translate(str.maketrans({'⻓':'长','⻅':'见','⻔':'门','⽬':'目','∕':'/','，':',','：':':'}))
 value=re.sub(r'YDental\s*\|\s*\d+/\d+','',value)
 return re.sub(r'\s+','',value)

def line_matrix(artifact,pages):
 lines=artifact['fields'].get('lines',[])
 if artifact['fields']['kind']!='prescription':return []
 whole=normalized(''.join(page['text'] for page in pages))
 for label in ('SKU／药品／规格','用法／频次／疗程','开立数量／实际已发／未领数量','状态／原因'):
  assert normalized(label) in whole,('untranslated prescription label',label)
 headings=list(re.finditer(r'(?:明细编号|LineID):(\d+)',whole))
 actual=[int(match.group(1)) for match in headings]
 expected=[line['id'] for line in lines]
 assert actual==expected,('missing, duplicated or reordered lines',actual,expected)
 matrix=[]
 for position,line in enumerate(lines):
  start=headings[position].end();end=headings[position+1].start() if position+1<len(headings) else len(whole)
  content=whole[start:end];fields={}
  for name in ('sku','name','product_specification','specification','usage','frequency','course','unit','state','reason'):
   value=line[name];fields[name]=not value or normalized(value) in content
   assert fields[name],('missing field',line['id'],name)
  for name,label in (('approved','(?:开立数量|Approved)'),('dispensed','(?:实际已发|Actuallydispensed)'),('remaining','(?:未领数量|Uncollected)')):
   fields[name]=bool(re.search(label+':'+re.escape(normalized(line[name]))+r'(?![\d.])',content))
   assert fields[name],('missing quantity',line['id'],name,line[name])
  marker_pages={}
  for name in ('specification','usage','frequency','course'):
   markers=re.findall(r'S08C-'+name+r'-\d\d-END',str(line[name]))
   if markers:
    hits=[page['number'] for page in pages if markers[0] in normalized(page['text'])]
    assert len(hits)==1,('missing/duplicated end marker',line['id'],name,hits)
    marker_pages[name]=hits[0]
  matrix.append({'line_id':line['id'],'source_fields':fields,'end_marker_pages':marker_pages})
 return matrix
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
   png=path.with_name(path.stem+'-page-%02d.png'%(i+1))
   rendered=page.get_pixmap(matrix=pymupdf.Matrix(1.5,1.5),alpha=False).tobytes('png')
   if png.exists():assert hashlib.sha256(png.read_bytes()).digest()==hashlib.sha256(rendered).digest(),('preserved image changed',png)
   else:png.write_bytes(rendered)
   with Image.open(png) as image:
    gray=image.convert('L');body_image=gray.crop((0,0,gray.width,int(gray.height*.93)))
    dark_pixels=sum(body_image.histogram()[:220])
   body=re.sub(r'YDental\s*\|\s*\d+/\d+','',txt).strip()
   page_record={'number':i+1,'path':str(png.relative_to(ROOT)),'sha256':hashlib.sha256(rendered).hexdigest(),'characters':len(txt),'business_characters':len(normalized(body)),'body_dark_pixels':dark_pixels,'a4':abs(page.rect.width-595)<2 and abs(page.rect.height-842)<2,'size':[page.rect.width,page.rect.height],'overlap_pairs':[]};item['pages'].append(page_record)
   assert page_record['a4'],(path,i,'not A4')
   assert len(normalized(body))>=60 and dark_pixels>=1200,(path,i,'blank or sparse body')
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
  pages=[{'number':number+1,'text':page.get_text()} for number,page in enumerate(doc)]
  item['source_line_matrix']=line_matrix(artifact,pages)
  txtpath=path.with_suffix('.txt')
  if txtpath.exists():assert txtpath.read_text()==text,('preserved extraction changed',txtpath)
  else:txtpath.write_text(text)
  item['text']=str(txtpath.relative_to(ROOT));item['fonts']=sorted(set(item['fonts']));item['result']='AUTOMATED_PASS_VISUAL_PENDING'
 summary['result']='AUTOMATED_PASS_VISUAL_PENDING'
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
assert summary['result']!='FAIL',summary.get('failure')

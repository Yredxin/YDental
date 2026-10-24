"""Render every delivered PDF page and decode identification QR in software.

This creates separate review PNGs; original PDF bytes are never changed. Text
and decoder facts do not constitute visual acceptance, signing or device output.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[2]
PRIVATE=ROOT/'.local/s13'
sys.path.insert(0,str(ROOT/'.local/s12/visual-deps'))
sys.path.insert(0,str(PRIVATE/'qr-deps'))
import pypdfium2 as pdfium
import zxingcpp


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def owned(path,directory=False):
    if PRIVATE.resolve() not in path.resolve().parents or path.is_symlink():raise RuntimeError('Only actual S13 private artifact paths are allowed')
    info=path.stat()
    if info.st_uid!=os.geteuid() or info.st_mode&0o077:raise RuntimeError('Artifacts must remain private and owned')
    if directory and not path.is_dir():raise RuntimeError('Expected private artifact directory')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pdf-directory',type=Path,required=True);p.add_argument('--output-directory',type=Path,required=True)
    p.add_argument('--expected-qr',type=Path)
    a=p.parse_args();source=a.pdf_directory.resolve();out=a.output_directory.resolve();owned(source,True)
    if out.exists():raise RuntimeError('Do not overwrite an earlier page review result')
    if PRIVATE.resolve() not in out.parents:raise RuntimeError('Output must remain in S13 private artifacts')
    out.mkdir(mode=0o700,parents=True)
    expected=json.loads(a.expected_qr.read_text()) if a.expected_qr else {}
    dependency={'package':'zxing-cpp','version':'2.3.0','private_directory':str((PRIVATE/'qr-deps').relative_to(ROOT)),
                'files':[{'path':str(path.relative_to(PRIVATE/'qr-deps')),'bytes':path.stat().st_size,'sha256':sha(path)} for path in sorted((PRIVATE/'qr-deps').rglob('*')) if path.is_file() and '__pycache__' not in path.parts and path.name!='.lock']}
    record={'status':'INCOMPLETE_PDF_PAGE_INDEX','physical_scan_or_output':'NOT_RUN','visual_acceptance':'NOT_PERFORMED_BY_THIS_TOOL',
            'original_bytes_modified':False,'tool_sha256':sha(Path(__file__)),'qr_decoder_dependency':dependency,'files':[]}
    try:
        for pdf in sorted(source.glob('*.pdf')):
            owned(pdf);original_sha=sha(pdf);document=pdfium.PdfDocument(str(pdf));item={'file':str(pdf.relative_to(ROOT)),'bytes':pdf.stat().st_size,'sha256':original_sha,'page_count':len(document),'pages':[]}
            try:
                for number in range(len(document)):
                    page=document[number]
                    try:
                        width,height=page.get_size();text_page=page.get_textpage()
                        try:text=text_page.get_text_range()
                        finally:text_page.close()
                        bitmap=page.render(scale=2.0)
                        try:image=bitmap.to_pil().copy()
                        finally:bitmap.close()
                        png=out/(pdf.stem+'-page-%02d.png'%(number+1));image.save(png);os.chmod(png,0o600)
                        qr=[{'text':value.text,'format':str(value.format)} for value in zxingcpp.read_barcodes(image)]
                        facts={'number':number+1,'width_pt':width,'height_pt':height,'width_mm':width*25.4/72,'height_mm':height*25.4/72,
                               'text_characters':len(text),'text_sha256':hashlib.sha256(text.encode()).hexdigest(),'contains_chinese':bool(re.search('[\u3400-\u9fff]',text)),
                               'image':str(png.relative_to(ROOT)),'image_sha256':sha(png),'qr_decoded':qr,'visual_review':'PENDING_INDEPENDENT_REVIEW'}
                        item['pages'].append(facts)
                    finally:page.close()
            finally:document.close()
            if sha(pdf)!=original_sha:raise RuntimeError('Original PDF bytes changed during read-only inspection')
            if pdf.name in expected:
                decoded=[q['text'] for page in item['pages'] for q in page['qr_decoded']]
                item['expected_qr']=expected[pdf.name];item['qr_payload_matches']=expected[pdf.name] in decoded
            record['files'].append(item)
        record['status']='PDF_PAGES_RENDERED_QR_SOFTWARE_FACTS_ONLY'
    except Exception as error:
        record.update(status='PDF_INDEX_FAILED_ORIGINALS_PRESERVED',error_class=type(error).__name__)
    payload=(json.dumps(record,indent=2,ensure_ascii=False)+'\n').encode();fd=os.open(out/'index.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'wb') as f:f.write(payload)
    print(json.dumps({'status':record['status'],'pdfs':len(record['files']),'pages':sum(v['page_count'] for v in record['files']),
                      'output':str((out/'index.json').relative_to(ROOT)),'sha256':hashlib.sha256(payload).hexdigest(),
                      'qr_matches':{Path(v['file']).name:v['qr_payload_matches'] for v in record['files'] if 'qr_payload_matches' in v}}))
    return 0 if record['status']=='PDF_PAGES_RENDERED_QR_SOFTWARE_FACTS_ONLY' else 2


if __name__=='__main__':raise SystemExit(main())

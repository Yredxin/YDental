#!/usr/bin/env python3
"""Compare bounded P10 raw before/after; classify only native query timestamp."""
import argparse,copy,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--before',required=True);p.add_argument('--after',required=True);p.add_argument('--output',required=True);a=p.parse_args();before=ROOT/a.before;after=ROOT/a.after;results=[]
 for metric in ('collections','refunds','receivables','unique_patients','lab_pending'):
  x=next(before.glob('query-'+metric+'-*.json'));y=next(after.glob('query-'+metric+'-*.json'));b=json.loads(x.read_bytes());c=json.loads(y.read_bytes());bt=b['filters']['query_at_utc'];ct=c['filters']['query_at_utc'];assert re.fullmatch(r'\d{4}-\d\d-\d\d \d\d:\d\d:\d\d',bt);assert re.fullmatch(r'\d{4}-\d\d-\d\d \d\d:\d\d:\d\d',ct);b['filters']['query_at_utc']='<CLASSIFIED_NATIVE_QUERY_TIMESTAMP>';c['filters']['query_at_utc']='<CLASSIFIED_NATIVE_QUERY_TIMESTAMP>';assert b==c,metric+' full typed JSON mismatch';results.append({'metric':metric,'before':{'file':str(x.relative_to(ROOT)),'sha256':digest(x),'query_at_utc':bt},'after':{'file':str(y.relative_to(ROOT)),'sha256':digest(y),'query_at_utc':ct},'exact_remaining_whole_JSON':True,'fields_removed_or_sorted':False})
 output={'status':'PASS','layer':'FULL_TYPED_JSON_EXCEPT_ONE_TYPED_NATIVE_QUERY_TIMESTAMP','queries':results,'other_normalizations':[]};out=ROOT/a.output;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(output,ensure_ascii=False,indent=2));out.chmod(0o600);print(json.dumps({'status':'PASS','output':a.output,'sha256':digest(out),'queries':len(results)}))
if __name__=='__main__':main()

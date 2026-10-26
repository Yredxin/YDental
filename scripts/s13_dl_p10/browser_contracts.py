#!/usr/bin/env python3
"""Offline P10 CSV verification against complete same-scope native JSON."""
import argparse,csv,hashlib,io,json
from pathlib import Path
COLUMNS=['source_model','source_id','store_id','company_id','value','unit','event_date','state','patient_id','facts','source_url']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--csv',type=Path,required=True);p.add_argument('--json',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--decoded-webkit-response-body',action='store_true',help='Explicit decoded-body layer only; never proves raw wire BOM or native download file');a=p.parse_args();raw=a.csv.read_bytes();has_bom=raw.startswith(b'\xef\xbb\xbf');assert (not has_bom) if a.decoded_webkit_response_body else has_bom;rows=list(csv.reader(io.StringIO(raw.decode('utf-8-sig'))));value=json.loads(a.json.read_bytes());assert rows[0]==['YDental operating report; synthetic configuration subject to business review'];assert rows[1][0]=='filters';assert rows[2][0]=='totals_by_unit';assert rows[3][0]=='event_counts_by_unit';assert rows[4]==COLUMNS
 filters=json.loads(rows[1][1]);old=filters['query_at_utc'];new=value['filters']['query_at_utc'];left=dict(filters,query_at_utc='<NATIVE_QUERY_TIMESTAMP>');right=dict(value['filters'],query_at_utc='<NATIVE_QUERY_TIMESTAMP>');assert left==right;assert json.loads(rows[2][1])==value['totals'];assert json.loads(rows[3][1])==value['event_counts_by_unit'];assert len(value['rows'])==value['source_row_count'];expected=[]
 for row in value['rows']:
  cells=[]
  for key in COLUMNS:
   v=row[key];text=json.dumps(v,ensure_ascii=False,sort_keys=True) if isinstance(v,dict) else str(v);cells.append("'"+text if text.startswith(('=','+','-','@','\t','\r')) else text)
  expected.append(cells)
 assert rows[5:]==expected,'Exact 11-column source rows/order/value/serialization mismatch'
 result={'status':'PASS','layer':'EXPLICIT_WEBKIT_DECODED_BODY_COMPLETE_COMPARE' if a.decoded_webkit_response_body else 'ACTUAL_NATIVE_CSV_OFFLINE_COMPLETE_COMPARE','csv':{'file':str(a.csv),'bytes':len(raw),'sha256':sha(a.csv)},'source_json':{'file':str(a.json),'sha256':sha(a.json)},'columns':COLUMNS,'rows':len(expected),'totals':value['totals'],'filters':filters,'classified_native_query_at':{'csv':old,'json':new},'all_remaining_typed_filters_exact':True,'all_source_rows_columns_order_values_exact':True,'formula_prefix_contract_exact':True,'not_business_original_or_PDF':True,'captured_body_has_BOM':has_bom,'decoded_body_only':a.decoded_webkit_response_body,'raw_wire_BOM_not_claimed':a.decoded_webkit_response_body,'native_download_file_not_claimed':a.decoded_webkit_response_body,'BOM_prepend_or_bytes_modified':False};a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2));a.output.chmod(0o600);print(json.dumps({'status':'PASS','rows':len(expected),'output':str(a.output),'sha256':sha(a.output)}))
if __name__=='__main__':main()

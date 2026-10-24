"""Normal-role HTTP checks for current S13 reports/search/original access.

No economic business is submitted, no grants or old originals are changed.
Unknown responses are retained without retry; independent committed protection
and browser/PDF visual results are separate evidence.
"""
import argparse
import csv
from decimal import Decimal
import hashlib
import io
import json
import math
from pathlib import Path
import re
import sys
from urllib.parse import urlencode, urlsplit
from lxml import html

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/s13'))
from admission_probe import PLAN,PRIVATE,write_receipt
from http_client import HttpActor,owned_service

MONEY=('original_billing','credits','collections','refunds','approved_pending','receivables')
JOBS={'settlement':MONEY,'doctor':('unique_patients','arrivals','executions','lab_pending'),
      'warehouse':('consumption',),'followup':('followups',)}


def signature(row):
    result={}
    for name in ('source_model','source_id','store_id','company_id','value','unit','event_date','state','patient_id','facts','source_url'):
        value=row[name]
        if isinstance(value,str) and len(value)>1 and value[0]=="'" and value[1] in ('=', '+', '-', '@', '\t', '\r'):
            value=value[1:]
        if name in ('source_id','store_id','company_id'):
            value=int(value)
        elif name=='patient_id':
            value=False if value in (False,None,'False','None','') else int(value)
        elif name=='value':
            value=str(Decimal(str(value)).normalize())
        elif name=='facts' and isinstance(value,str):
            value=json.loads(value)
        result[name]=value
    return json.dumps(result,sort_keys=True,ensure_ascii=False)



def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run-id',required=True);parser.add_argument('--label',required=True)
    args=parser.parse_args()
    if not re.fullmatch('[A-Za-z0-9_-]{1,60}',args.label):raise RuntimeError('Explicit bounded run label required')
    service=owned_service(args.run_id);directory=PRIVATE/'verification'/('http-'+args.label);directory.mkdir(mode=0o700,parents=True)
    result={'status':'INCOMPLETE_HTTP_UX','plan_id':PLAN,'service':service,'actors':{},'metrics':[],'negatives':[],
            'tool_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'business_actions_submitted':False,
            'source_layer':'NORMAL_HTTP_AUTHENTICATION_AND_STORE_FORM','independent_acceptance':False,'automatic_replay':False}
    write_receipt(directory/'intent.json',result)
    first_source=None
    try:
        for alias,metrics in JOBS.items():
            actor_dir=directory/alias;actor_dir.mkdir(mode=0o700)
            actor=HttpActor(alias,actor_dir)
            try:
                result['actors'][alias]=actor.login(1)
                for metric in metrics:
                    owned_service(args.run_id)
                    values=dict(metric=metric,date_from='2026-10-01',date_to='2026-11-30',store_ids='1')
                    if metric in MONEY:values['currency_id']='1'
                    path='/ydental/reports?'+urlencode(values)
                    response=actor.request('GET',path+'&output=json');assert response.status_code==200, 'Expected authorized report JSON'
                    data=response.json();rows=list(data['rows']);pages=math.ceil(data['source_row_count']/data['page_size'])
                    for page in range(2,pages+1):
                        paged=actor.request('GET',path+'&output=json&page='+str(page));assert paged.status_code==200
                        page_data=paged.json();assert page_data['totals']==data['totals'];rows.extend(page_data['rows'])
                    assert len(rows)==data['source_row_count'], 'All source rows must be paginated'
                    page=actor.request('GET',path);assert page.status_code==200
                    tree=html.fromstring(page.content)
                    assert tree.xpath('//select[@name="store_ids"]') and tree.xpath('//select[@name="company_id"]'), 'Authorized selectors absent'
                    assert bool(tree.xpath('//select[@name="currency_id"]'))==(metric in MONEY), 'Currency selector applicability differs'
                    assert not tree.xpath('//input[@name="store_ids" or @name="company_id" or @name="currency_id"][not(@type="hidden")]'), 'Internal ID fields remain in filters'
                    assert not tree.xpath('//pre[not(ancestor::details)]'), 'Technical pre is not folded'
                    item={'metric':metric,'alias':alias,'source_count':len(rows),'page_count':max(1,pages),'totals':data['totals'],
                          'effective_filters':data['filters'],'complete_source_signatures_sha256':hashlib.sha256('\n'.join(signature(row) for row in rows).encode()).hexdigest(),
                          'normal_html_status':page.status_code,'title':tree.xpath('string(//h2[1])'),'selectors_checked':True,'technical_trace_folded':True}
                    if rows:
                        source=actor.request('GET',rows[0]['source_url']+'&page=1');assert source.status_code==200, 'Authorized source drill unavailable'
                        source_tree=html.fromstring(source.content);assert source_tree.xpath('//details//pre'), 'Complete source trace unavailable'
                        assert source_tree.xpath('//a[starts-with(@href,"/ydental/reports?")]'), 'Return filter link missing'
                        item['drill']={'status':source.status_code,'path':urlsplit(rows[0]['source_url']).path,'source_model':rows[0]['source_model'],'source_id':rows[0]['source_id'],'return_link':source_tree.xpath('//a[starts-with(@href,"/ydental/reports?")]/@href')[0]}
                        if metric=='collections':first_source=rows[0]['source_url']
                    exported=actor.request('POST','/ydental/reports/export',data={'csrf_token':actor.csrf,'revision':actor.revision,**values},record_operation='report_export')
                    item['export_status']=exported.status_code
                    if exported.status_code==200:
                        records=list(csv.reader(io.StringIO(exported.content.decode('utf-8-sig'))));columns=records[4];csv_rows=[dict(zip(columns,row)) for row in records[5:]]
                        assert len(csv_rows)==len(rows), 'CSV and all page counts differ'
                        assert json.loads(records[2][1])==data['totals'], 'CSV and normal report totals differ'
                        csv_signatures=[signature(row) for row in csv_rows]
                        api_signatures=[signature(row) for row in rows]
                        assert csv_signatures==api_signatures, 'CSV full source facts, identity, dates, amounts or order differ'
                        item['csv_full_source_signatures_sha256']=hashlib.sha256('\n'.join(csv_signatures).encode()).hexdigest()
                        item['csv_effective_filters']=json.loads(records[1][1])
                        assert {key:value for key,value in item['csv_effective_filters'].items() if key!='query_at_utc'}=={key:value for key,value in data['filters'].items() if key!='query_at_utc'}, 'CSV effective scope or timezone boundaries differ'
                        item['query_time_metadata_may_differ']=True
                        item['csv_matches_all_pages']=True
                    else:
                        assert exported.status_code==403, 'Only explicit source/export refusal is expected'
                        item['export_refused_by_product']=True
                    if metric not in MONEY:
                        invalid=actor.request('GET',path+'&currency_id=1&output=json');assert invalid.status_code==409
                        result['negatives'].append({'alias':alias,'metric':metric,'case':'nonmonetary_currency','status':invalid.status_code})
                    invalid=actor.request('GET','/ydental/reports?'+urlencode(dict(values,store_ids='999999',output='json')));assert invalid.status_code==403
                    result['negatives'].append({'alias':alias,'metric':metric,'case':'unavailable_store','status':invalid.status_code})
                    result['metrics'].append(item)
            finally:actor.close()
        none_dir=directory/'none';none_dir.mkdir(mode=0o700)
        actor=HttpActor('none',none_dir)
        try:
            result['actors']['none']=actor.login(1)
            for path in ['/ydental/reports?metric=collections&date_from=2026-10-01&date_to=2026-11-30&store_ids=1&currency_id=1&output=json',first_source]:
                if path:
                    response=actor.request('GET',path);assert response.status_code==403
                    result['negatives'].append({'alias':'none','case':'no_source_permission','path':urlsplit(path).path,'status':response.status_code})
        finally:actor.close()
        result['status']='HTTP_UX_ASSERTIONS_PASSED'
    except Exception as error:
        result.update(status='HTTP_UX_FAILED_NO_BUSINESS_REPLAY',error_class=type(error).__name__)
        if isinstance(error,AssertionError):result['assertion']=str(error)
    digest=write_receipt(directory/'result.json',result)
    print(json.dumps({'status':result['status'],'metrics':len(result['metrics']),'negatives':len(result['negatives']),'assertion':result.get('assertion'),'error_class':result.get('error_class'),'sha256':digest,'output':str((directory/'result.json').relative_to(ROOT))}))
    return 0 if result['status']=='HTTP_UX_ASSERTIONS_PASSED' else 2


if __name__=='__main__':raise SystemExit(main())

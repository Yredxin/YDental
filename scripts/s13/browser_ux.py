"""Normal-role browser software checks for the fixed S13 limited UX candidate.

Only login, store selection, GET navigation, native details and cancel links.
Economic forms are never submitted. No injected CSS or edited PDF is used.
"""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import urlencode, urlsplit, parse_qs

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/s13'))
from admission_probe import PLAN,PRIVATE,write_receipt
from http_client import BASE,ROLE_PROVIDER,owned_service,private_json

import browser_client as view
SOURCE=ROOT/'scripts/s13/browser_client.py'

def now():return dt.datetime.now(dt.UTC).isoformat()


def screenshot(page,directory,label):
    if page.locator('input[type="password"]').count():raise RuntimeError('No login-page screenshots')
    out=directory/(label+'.png')
    if out.exists():raise RuntimeError('Screenshots are never overwritten')
    page.screenshot(path=str(out),full_page=True,timeout=30000);os.chmod(out,0o600)
    return {'path':str(out.relative_to(ROOT)),'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'visual_review':'NOT_PERFORMED_BY_THIS_TOOL'}


def measure(page):
    return page.evaluate('''() => ({root:{scrollWidth:document.documentElement.scrollWidth,clientWidth:document.documentElement.clientWidth},
        body:{scrollWidth:document.body.scrollWidth,clientWidth:document.body.clientWidth},devicePixelRatio:devicePixelRatio,
        localScrollRegions:[...document.querySelectorAll('[role="region"], .o_ydental_access_scroll')].map(e=>({scrollWidth:e.scrollWidth,clientWidth:e.clientWidth,overflowX:getComputedStyle(e).overflowX})),
        clippedContainers:[...document.querySelectorAll('main, main div, main section, main article, main table, main pre, main details')].filter(e=>getComputedStyle(e).overflowX==='hidden' && e.scrollWidth>e.clientWidth+1).slice(0,20).map(e=>({tag:e.tagName,classes:e.className}))})''')


def visit(page,path,directory,label):
    native=urlsplit(path).path.startswith('/odoo/')
    response=page.goto(BASE+path,wait_until='domcontentloaded',timeout=40000)
    if native:
        page.locator('.o_form_view').wait_for(state='visible',timeout=30000)
        identification=page.locator('.o_form_view .o_field_widget[name="ydental_internal_code"]')
        identification.wait_for(state='visible',timeout=15000)
        if not identification.inner_text().strip():raise RuntimeError('Native form source identification content is not loaded')
    else:page.wait_for_load_state('networkidle',timeout=40000)
    page.evaluate('() => document.fonts.ready.then(()=>true)')
    dimensions=measure(page)
    item={'path':urlsplit(path).path,'query':parse_qs(urlsplit(path).query),'status':response.status if response else None,
          'headings':page.locator('h1,h2').all_text_contents()[:12],'dimensions':dimensions,
          'screenshot':screenshot(page,directory,label),'layer':'BROWSER'}
    if native:item['native_object_ready']='FORM_VISIBLE_WITH_SOURCE_IDENTIFICATION'
    item['root_no_overflow']=dimensions['root']['scrollWidth']<=dimensions['root']['clientWidth']+1
    item['no_clipped_container']=not dimensions['clippedContainers']
    return item



def search_interaction(page,directory,prefix,label):
    form=page.locator('form[method="get"]').filter(has=page.locator('input[name="q"]')).first
    if not form.count():return {'available':False}
    if label=='documents':
        options=page.locator('select[name="selection"] option').all_text_contents()
        selected=next((value for value in options if ' / ' in value),'')
        term=selected.split(' / ')[0].strip()
    elif label=='external-originals':
        options=page.locator('select[name="invoice_id"] option[value]:not([value=""])').all_text_contents()
        term=options[0].split(' · ')[1].split(' / ')[-1].strip() if options else ''
    elif label=='settlement':
        links=page.locator('.o_ydental_access_search li a').all_text_contents()
        term=links[0].split(' · ')[-1].strip() if links else ''
    else:
        cells=page.locator('main table tbody tr td:first-child').all_text_contents()
        term=next((value.strip() for value in cells if value.strip()),'')
    if not term:return {'available':True,'result':'NO_EXISTING_AUTHORIZED_SEARCH_CHOICE'}
    form.locator('input[name="q"]').fill(term)
    form.locator('button').click();page.wait_for_load_state('networkidle',timeout=40000)
    found={'business_text_search':term,'query_preserved':parse_qs(urlsplit(page.url).query).get('q')==[term],
           'screenshot':screenshot(page,directory,prefix+'-search'),'dimensions':measure(page)}
    if label=='external-originals':
        select=page.locator('select[name="invoice_id"]')
        choices=select.locator('option[value]:not([value=""])').evaluate_all('(rows)=>rows.map(row=>({value:row.value,label:row.textContent}))')
        if not choices:raise RuntimeError('Business search returned no authorized bill choices')
        select.select_option(label=choices[0]['label'])
        with page.expect_navigation(wait_until='domcontentloaded',timeout=40000):select.locator('xpath=..').locator('xpath=..').locator('button').click()
        page.wait_for_load_state('networkidle',timeout=40000)
        found['normal_bill_selected_by_business_label']=True
        found['detail_screenshot']=screenshot(page,directory,prefix+'-selected-bill')
        found['detail_dimensions']=measure(page)
        if page.locator('input[name="invoice_id"]:not([type="hidden"]), input[name="previous_id"]:not([type="hidden"])').count():raise RuntimeError('External original workbench still requires internal keys')
        found['internal_key_text_inputs_absent']=True
    if label=='settlement':
        links=page.locator('.o_ydental_access_search li a')
        if links.count():
            links.first.click();page.wait_for_load_state('networkidle',timeout=40000)
            found['normal_result_opened']=True;found['detail_screenshot']=screenshot(page,directory,prefix+'-search-detail')
    form=page.locator('form[method="get"]').filter(has=page.locator('input[name="q"]')).first
    form.locator('input[name="q"]').fill('S13-no-result-unique-query')
    form.locator('button').click();page.wait_for_load_state('networkidle',timeout=40000)
    found['no_result_screenshot']=screenshot(page,directory,prefix+'-no-result')
    found['no_result_dimensions']=measure(page)
    return found


def report_selector_interaction(page,directory,prefix,metric):
    form=page.locator('form.o_ydental_reporting_filters')
    options=form.locator('select[name="metric"] option').evaluate_all('(rows)=>rows.map(row=>({value:row.value,label:row.textContent}))')
    target=next((row for row in options if row['value']!=metric),None)
    if not target:return {'result':'ONLY_ONE_AUTHORIZED_METRIC'}
    with page.expect_navigation(wait_until='domcontentloaded',timeout=30000):
        form.locator('select[name="metric"]').select_option(label=target['label'])
    page.wait_for_load_state('networkidle',timeout=40000)
    changed=parse_qs(urlsplit(page.url).query)
    result={'selected_metric_by_label':target['label'],'metric':target['value'],'stale_currency_company_state_cleared':not any(k in changed for k in ('currency_id','company_id','state'))}
    form=page.locator('form.o_ydental_reporting_filters')
    form.locator('input[name="date_from"]').fill('2026-10-01');form.locator('input[name="date_to"]').fill('2026-11-30')
    stores=form.locator('select[name="store_ids"] option').evaluate_all('(rows)=>rows.map(row=>({value:row.value,label:row.textContent}))')
    store=next((row for row in stores if row['value']=='1'),None)
    if not store:raise RuntimeError('Current authorized store was absent from selector')
    form.locator('select[name="store_ids"]').select_option(label=store['label']);result['store_selected_by_label']=store['label']
    if form.locator('select[name="currency_id"]').count():
        form.locator('select[name="currency_id"]').select_option(label='USD');result['currency_selected_by_label']='USD'
    form.locator('button[type="submit"]').click();page.wait_for_load_state('networkidle',timeout=40000)
    result['effective_query']=parse_qs(urlsplit(page.url).query);result['screenshot']=screenshot(page,directory,prefix+'-selector-submit');result['dimensions']=measure(page)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run-id',required=True);parser.add_argument('--label',required=True)
    args=parser.parse_args()
    if not re.fullmatch('[A-Za-z0-9_-]{1,60}',args.label):raise RuntimeError('Explicit bounded label required')
    service=owned_service(args.run_id)
    directory=PRIVATE/'verification'/('browser-'+args.label);directory.mkdir(mode=0o700,parents=True)
    record={'status':'INCOMPLETE_BROWSER_CHECK','plan_id':PLAN,'service':service,'started_at_utc':now(),'actors':{},'pages':[],
            'tool_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'layer':'BROWSER_HEADLESS_SOFTWARE',
            'user_hand_verified':False,'credentials_profile_session_recorded':False,'business_actions_submitted':False,'automatic_replay':False,
            'existing_browser_helper_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest()}
    write_receipt(directory/'intent.json',record)
    accounts=private_json(ROLE_PROVIDER)['users']
    report=lambda metric:'/ydental/reports?'+urlencode(dict(metric=metric,date_from='2026-10-01',date_to='2026-11-30',store_ids='1',**({'currency_id':1} if metric in ('original_billing','credits','collections','refunds','approved_pending','receivables') else {})))
    jobs={'settlement':[('/ydental/access','access'),('/ydental/settlement?patient_id=521','settlement'),('/ydental/settlement/external-originals','external-originals')]+[(report(metric),metric) for metric in ('original_billing','credits','collections','refunds','approved_pending','receivables')],
          'doctor':[('/ydental/documents','documents'),('/odoo/ydental.lab.order/214','native-lab214')]+[(report(metric),metric) for metric in ('unique_patients','arrivals','executions','lab_pending')],
          'warehouse':[('/ydental/inventory','inventory'),(report('consumption'),'consumption')],
          'followup':[('/ydental/followups','followups'),('/ydental/followups?followup_id=280#followup-280','followup280'),('/ydental/followups?followup_id=277#followup-277','closed-followup277'),(report('followups'),'followups-report')]}
    sync=view.import_browser()
    record['browser_environment']=view.loaded_browser_environment_facts()
    try:
        with sync() as pw:
            browser=pw.chromium.launch(headless=True,executable_path=str(view.CHROMIUM))
            try:
                for alias,cases in jobs.items():
                    owned_service(args.run_id)
                    context=browser.new_context(locale='zh-CN',timezone_id='UTC',viewport={'width':1366,'height':768})
                    observer=view.Observer(context);page=context.new_page()
                    auth=view.login(page,accounts[alias],accounts[alias]['id']);selected=view.switch_store(page,1)
                    record['actors'][alias]={'authentication':auth,'store':selected}
                    for width,height in ((1366,768),(1440,900)):
                        page.set_viewport_size({'width':width,'height':height})
                        for path,label in cases:
                            owned_service(args.run_id)
                            record['current_case']={'alias':alias,'path':urlsplit(path).path,'label':label,'viewport':{'width':width,'height':height}}
                            prefix=f'{alias}-{label}-{width}x{height}'
                            item=visit(page,path,directory,prefix);item.update(alias=alias,viewport={'width':width,'height':height})
                            record['pages'].append(item)
                            item['visible_form_labels']=page.locator('label').all_text_contents()[:20]
                            if label=='documents':
                                nav=page.locator('main nav, main summary').all_text_contents()
                                untranslated=('Clinical workbench','Treatment and pharmacy','Current store and permissions','Explicit clinical source collection','Controlled device failure demonstration','Consent upload and verification')
                                if any(term in text for text in nav for term in untranslated):raise RuntimeError('Required document navigation remains untranslated')
                            if label=='closed-followup277':
                                closed=page.locator('#followup-277')
                                item['closed_row_present']=closed.count()==1
                                item['closed_row_form_count']=closed.locator('form').count() if closed.count() else None
                                item['closed_contact_form_count']=closed.locator('input[name="operation"][value="contact"]').count() if closed.count() else None
                            item['chinese_visible_heading']=any(re.search('[\u3400-\u9fff]',value) for value in item['headings'])
                            if label in ('documents','settlement','inventory','external-originals') and item['status']==200:
                                item['search_interaction']=search_interaction(page,directory,prefix,label)
                                page.goto(BASE+path,wait_until='networkidle',timeout=40000)
                            if '/reports?' in path and item['status']==200:
                                drill=page.locator('a[href^="/ydental/reports/source/"]').first
                                if drill.count():
                                    origin=page.url;href=drill.get_attribute('href');drill.click();page.wait_for_load_state('networkidle',timeout=40000)
                                    source={'path':urlsplit(page.url).path,'screenshot':screenshot(page,directory,prefix+'-source'),'dimensions':measure(page)}
                                    traces=page.locator('details').filter(has=page.locator('pre'))
                                    if traces.count():
                                        traces.first.locator('summary').click();source['trace_open_screenshot']=screenshot(page,directory,prefix+'-trace');source['trace_dimensions']=measure(page)
                                    back=page.locator('a[href^="/ydental/reports?"]').first
                                    back.click();page.wait_for_load_state('networkidle',timeout=40000)
                                    source['origin_url']=origin;source['returned_url']=page.url
                                    effective=('metric','date_from','date_to','store_ids','company_id','currency_id','state','page')
                                    initial=parse_qs(urlsplit(origin).query);returned=parse_qs(urlsplit(page.url).query)
                                    def normalized(query,key):
                                        if key=='page':return query.get(key,['1'])
                                        if key=='store_ids':return sorted(part for value in query.get(key,[]) for part in value.split(','))
                                        return query.get(key,[''])
                                    source['return_filters_preserved']=all(normalized(initial,key)==normalized(returned,key) for key in effective)
                                    item['source_drill']=source
                            if '/reports?' in path and item['status']==200 and width==1366:
                                item['selector_interaction']=report_selector_interaction(page,directory,prefix,parse_qs(urlsplit(path).query)['metric'][0])
                                page.goto(BASE+path,wait_until='networkidle',timeout=40000)
                            if label=='settlement' and item['status']==200:
                                panels=page.locator('details.o_ydental_access_operation')
                                item['operation_panels']=panels.count();item['default_open_operations']=page.locator('details.o_ydental_access_operation[open]').count()
                                if panels.count():
                                    before=len(observer.responses);panels.first.locator('summary').click();page.wait_for_timeout(200)
                                    item['entered_operation_screenshot']=screenshot(page,directory,prefix+'-operation');item['operation_dimensions']=measure(page)
                                    cancel=panels.first.locator('a').last;cancel.click();page.wait_for_load_state('networkidle',timeout=40000)
                                    item['cancel_no_settlement_post']=not any(e['method']=='POST' and e['path']=='/ydental/settlement/action' for e in observer.responses[before:])
                    record['actors'][alias]['observation']=observer.facts();context.close()
            finally:browser.close()
        issues=[]
        def add_issue(item,assertion):
            issues.append({'alias':item['alias'],'path':item['path'],'viewport':item['viewport'],'assertion':assertion})
        def check_dimensions(item,dimensions,where):
            if dimensions['root']['scrollWidth']>dimensions['root']['clientWidth']+1:add_issue(item,where+'_ROOT_OVERFLOW')
            if dimensions['clippedContainers']:add_issue(item,where+'_CONTENT_CLIPPED')
        for item in record['pages']:
            if item['status']!=200:add_issue(item,'HTTP_STATUS')
            check_dimensions(item,item['dimensions'],'PAGE')
            if not item.get('chinese_visible_heading') and not ('/odoo/' in item['path']):add_issue(item,'BUSINESS_HEADING_NOT_CHINESE')
            if '/odoo/' in item['path'] and not any(re.search('[\u3400-\u9fff]',text) for text in item.get('visible_form_labels',[])):
                add_issue(item,'NATIVE_FORM_LABELS_NOT_CHINESE_OR_NOT_LOADED')
            if 'source_drill' in item:
                source=item['source_drill']
                if not source.get('return_filters_preserved'):add_issue(item,'SOURCE_RETURN_FILTERS_LOST')
                check_dimensions(item,source['dimensions'],'SOURCE')
                if 'trace_dimensions' in source:check_dimensions(item,source['trace_dimensions'],'SOURCE_TRACE')
            if 'search_interaction' in item:
                search=item['search_interaction']
                if search.get('query_preserved') is not True:add_issue(item,'BUSINESS_TEXT_SEARCH_NOT_SUBMITTED')
                if 'dimensions' in search:check_dimensions(item,search['dimensions'],'SEARCH')
                if 'no_result_dimensions' in search:check_dimensions(item,search['no_result_dimensions'],'NO_RESULT')
            if 'selector_interaction' in item:
                selection=item['selector_interaction']
                if selection.get('result')!='ONLY_ONE_AUTHORIZED_METRIC':
                    if selection.get('stale_currency_company_state_cleared') is not True:add_issue(item,'METRIC_CHANGE_LEFT_STALE_FILTERS')
                    selected=selection.get('effective_query',{})
                    if selected.get('metric')!=[selection['metric']] or selected.get('date_from')!=['2026-10-01'] or selected.get('date_to')!=['2026-11-30'] or selected.get('store_ids')!=['1']:
                        add_issue(item,'SELECTOR_SUBMIT_EFFECTIVE_FILTERS_DIFFER')
                    if selection.get('currency_selected_by_label')=='USD' and selected.get('currency_id')!=['1']:add_issue(item,'CURRENCY_SELECTION_NOT_SUBMITTED')
                    check_dimensions(item,selection['dimensions'],'SELECTOR_SUBMIT')
            if item.get('default_open_operations',0)!=0:add_issue(item,'WRITE_PANELS_OPEN_BY_DEFAULT')
            if item.get('cancel_no_settlement_post') is False:add_issue(item,'CANCEL_SUBMITTED_SETTLEMENT_ACTION')
            if 'operation_dimensions' in item:check_dimensions(item,item['operation_dimensions'],'OPERATION_PANEL')
            if 'closed_row_present' in item and (item['closed_row_present'] is not True or item.get('closed_contact_form_count')!=0 or item.get('closed_row_form_count')!=0):add_issue(item,'CLOSED_FOLLOWUP_CONTACT_FORM_OR_HISTORY_MISSING')
        record.update(status='BROWSER_ASSERTIONS_PASSED_VISUAL_REVIEW_SEPARATE' if not issues else 'BROWSER_SOFTWARE_ASSERTIONS_FAILED',issues=issues)
    except Exception as error:
        record.update(status='BROWSER_CHECK_FAILED_NO_BUSINESS_REPLAY',error_class=type(error).__name__)
    record['finished_at_utc']=now();digest=write_receipt(directory/'result.json',record)
    print(json.dumps({'status':record['status'],'pages':len(record['pages']),'issues':len(record.get('issues',[])),'output':str((directory/'result.json').relative_to(ROOT)),'sha256':digest}))
    return 0 if record['status']=='BROWSER_ASSERTIONS_PASSED_VISUAL_REVIEW_SEPARATE' else 2


if __name__=='__main__':raise SystemExit(main())

"""Render loaded reporting QWeb branches with explicit memory-only values.

No service/model query is dispatched, no source or permission is fabricated as
real, and no database or HTTP write is performed. Product dictionaries provide
the twelve keys and money/state field applicability; browser tests separately
exercise authorized real query results. All output remains private.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

from admission_probe import PRIVATE, ROOT, write_receipt
import launcher


SCRIPT = r'''
import copy,datetime as dt,hashlib,io,json,os,subprocess
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlencode
from babel.messages import pofile
from lxml import etree,html
from odoo.tools.translate import trans_export
from odoo.addons.ydental_reporting.models.ydental_reporting_service import METRICS
from odoo.addons.ydental_reporting.models.ydental_reporting_presentation import METRIC_STATES
root=Path.cwd();private=root/'.local/dl-p10'
env.cr.rollback();env.cr.execute('SET TRANSACTION READ ONLY')
env.cr.execute("SELECT pg_backend_pid(),current_database(),(SELECT oid FROM pg_database WHERE datname=current_database()),(pg_control_system()).system_identifier::text,current_user,current_setting('transaction_read_only'),current_setting('transaction_isolation')")
identity=env.cr.fetchone()
assert identity[1:]==('ydental_s11_synth_20261023_01',2171423,'7694897083368259627','ydental_s11_synth_20261023_01','on','repeatable read')
assert len(METRICS)==12
qweb=env['ir.qweb'].with_context(lang='zh_CN')
view=env.ref('ydental_reporting.ydental_operating_report_page').with_context(lang='zh_CN')
combined=view._get_combined_arch();main=combined.xpath('.//main')[0]
choices=[{'key':k,'label':qweb.env._(v[0]),'timing':v[2]} for k,v in METRICS.items()]
marker='【明确内存组件，不是真实岗位/来源/金额】'
components=[];mapping=[]

def render(name,metric,empty=False,page=1,count=1):
 label,category,timing=METRICS[metric]
 money=category=='settlement';states=METRIC_STATES.get(metric,[])
 values={'metric':metric,'date_from':'2099-01-01','date_to':'2099-01-02','store_ids':'1','company_id':'','currency_id':'','state':''}
 filters=dict(values,store_ids=[1],period_or_snapshot=timing,query_at_utc='2099-01-02 00:00:00')
 report={'filters':filters,'page':page,'page_size':100,'source_row_count':0 if empty else count}
 options={'money':money,'states':[{'value':v,'label':marker+v} for v in states],
  'stores':[{'id':1,'label':marker+'门店','company_id':1,'timezone':'Asia/Shanghai'}],
  'companies':[{'id':1,'label':marker+'法人'}],'currencies':[{'id':1,'label':marker+'币种'}]}
 row={'store_label':marker+'门店','company_label':marker+'法人','source_label':marker+'文号',
  'patient_label':marker+'合成显示','event_label':'2099-01-01 00:00:00 UTC','state_label':marker+'状态',
  'quantity':{'value':marker+'1','label':marker+('币种' if money else '数量')},
  'source_url':'/ydental/reports/source/'+metric+'/900000001?'+urlencode(values)}
 display={'title':qweb.env._(label),'scope':marker+'门店范围','companies':marker+'法人范围',
  'currency':marker+('分币种' if money else '按单位'),'state_label':marker+'全部适用状态',
  'bounds':[{'label':marker+'门店','timezone':'Asia/Shanghai','start_utc':'2098-12-31 16:00:00','end_exclusive_utc':'2099-01-02 16:00:00'}],
  'rows':[] if empty else [row],
  'totals':[] if empty else [{'value':marker+'1','label':marker+('币种' if money else '数量'),'events':1}],
  'store_totals':[] if empty else [{'label':marker+'门店','totals':[{'label':marker+'数量','value':marker+'1'}]}]}
 context={'request':SimpleNamespace(csrf_token=lambda:''),'revision':'','choices':choices,
  'values':values,'report':report,'options':options,'selected_stores':[1],'display':display,
  'previous_url':'/ydental/reports?'+urlencode(dict(values,page=max(1,page-1))),
  'next_url':'/ydental/reports?'+urlencode(dict(values,page=page+1))}
 rendered=str(qweb.with_context(minimal_qcontext=True)._render(copy.deepcopy(main),context))
 fragment=html.fragment_fromstring(rendered,create_parent='div')
 forms=fragment.xpath('.//form');assert len(forms)==2
 for n in fragment.xpath('.//input[@name="csrf_token" or @name="revision"]'):assert n.get('value','')==''
 assert bool(fragment.xpath('.//select[@name="currency_id"]'))==money
 assert bool(fragment.xpath('.//select[@name="state"]'))==bool(states)
 assert len(fragment.xpath('.//select[@name="metric"]/option'))==12
 assert len(fragment.xpath('.//form[@action="/ydental/reports/export"]'))==1
 assert not fragment.xpath('.//form//form')
 def classes(node):return set(node.get('class','').split())
 def marked(node,variant):
  assert node.get('data-dl-actions')=='report-actions',(name,node.tag,dict(node.attrib))
  expected='o_ydental_reporting_main_disclosure' if variant=='disclosure' else 'o_ydental_reporting_main_action_'+variant
  assert expected in classes(node),(name,expected,dict(node.attrib))
 def svg_count(node):return len(node.xpath('.//*[local-name()="svg"]'))
 navigation=fragment.xpath('.//nav')[0]
 nav_links=navigation.xpath('./a')
 assert [n.get('href') for n in nav_links]==['/ydental/access','/ydental/documents','/ydental/settlement']
 assert 'o_ydental_reporting_main_spacing_navigation' in classes(navigation)
 for node in nav_links:marked(node,'quiet');assert svg_count(node)==0
 scope=fragment.xpath(".//div[contains(concat(' ',normalize-space(@class),' '),' o_ydental_reporting_scope ')]")
 assert len(scope)==1 and 'o_ydental_reporting_main_spacing_scope' in classes(scope[0])
 scope_summary=scope[0].xpath('.//details/summary');assert len(scope_summary)==1
 marked(scope_summary[0],'disclosure');assert svg_count(scope_summary[0])==0
 query=fragment.xpath('.//form[@action="/ydental/reports"]//button');assert len(query)==1
 marked(query[0],'primary');assert svg_count(query[0])==1
 export=fragment.xpath('.//form[@action="/ydental/reports/export"]//button');assert len(export)==1
 marked(export[0],'secondary');assert svg_count(export[0])==0
 row_links=fragment.xpath('.//table/tbody/tr/td/a');assert len(row_links)==(0 if empty else 1)
 for node in row_links:marked(node,'quiet');assert svg_count(node)==1
 pager_links=fragment.xpath(".//nav[contains(concat(' ',normalize-space(@class),' '),' o_ydental_reporting_main_spacing_pagination ')]/a")
 assert len(pager_links)==int(page>1)+int(page*100<report['source_row_count'])
 for node in pager_links:marked(node,'secondary');assert svg_count(node)==1
 store_summary=fragment.xpath(".//details[contains(concat(' ',normalize-space(@class),' '),' o_ydental_reporting_main_spacing_store_totals ')]/summary")
 assert len(store_summary)==(0 if empty else 1)
 for node in store_summary:marked(node,'disclosure');assert svg_count(node)==0
 components.append({'name':name,'metric':metric,'html':rendered,
  'layer':'ACTUAL_LOADED_QWEB_EXPLICIT_MEMORY_COMPONENT_NOT_REAL_ROLE_SOURCE_OR_BUSINESS',
  'money':money,'state_keys':states,'page':page,'source_row_count':report['source_row_count'],
  'empty':empty,'rendered_controls':{tag:len(fragment.xpath('.//'+tag)) for tag in ('button','a','summary')},
  'control_family_checks':{'navigation_quiet_no_svg':len(nav_links),'scope_native_disclosure_no_svg':len(scope_summary),
   'query_primary_search':len(query),'export_secondary_no_svg':len(export),'source_quiet_arrow':len(row_links),
   'pager_secondary_chevrons':len(pager_links),'store_native_disclosure_no_svg':len(store_summary)},
  'html_sha256':hashlib.sha256(rendered.encode()).hexdigest()})
 return fragment

for key in METRICS:
 render('metric-'+key,key)
 mapping.append({'metric':key,'money':METRICS[key][1]=='settlement','state_keys':METRIC_STATES.get(key,[]),'timing':METRICS[key][2]})
empty=render('empty','collections',empty=True)
assert len(empty.xpath('.//summary'))==1
both=render('page-both','collections',page=2,count=201)
assert len(both.xpath(".//nav[contains(concat(' ',normalize-space(@class),' '),' o_ydental_reporting_main_spacing_pagination ')]/a"))==2
last=render('page-last','collections',page=3,count=201)
assert len(last.xpath(".//nav[contains(concat(' ',normalize-space(@class),' '),' o_ydental_reporting_main_spacing_pagination ')]/a"))==1
assert len(both.xpath('.//button'))==2 and len(both.xpath('.//summary'))==2 and len(both.xpath('.//a'))==6

labels=['Query authorized sources','Export all matching sources (store export permission required)',
 'Current store and permissions','Document originals','Settlement workbench',
 'View source and allocations','Previous page','Next page',
 'Store timezones and effective UTC boundaries','Totals by authorized store']
stream=io.BytesIO();trans_export('zh_CN',['ydental_reporting'],stream,'po',qweb.env)
catalog=pofile.read_po(io.BytesIO(stream.getvalue()))
repository=pofile.read_po(io.BytesIO((root/'ydental_reporting/i18n/zh_CN.po').read_bytes()))
joined='\n'.join(v['html'] for v in components);translation_checks=[]
for text in labels:
 expected=repository[text].string
 actual=catalog[text].string if text in catalog else None
 assert expected and expected!=text and actual==expected and expected in joined,(text,actual,expected)
 translation_checks.append({'source':text,'expected_zh_CN':expected,'native_extracted':text in catalog,
  'native_export_zh_CN':actual,'loaded_memory_render_contains_zh_CN':expected in joined})
for component in components:
 tree=html.fragment_fromstring(component['html'],create_parent='div')
 for svg in tree.xpath('.//*[local-name()="svg"]'):
  assert svg.get('aria-hidden')=='true' and svg.get('focusable')=='false'
  assert not svg.xpath('.//*[@href or @*[starts-with(name(),"on")]]')
env.cr.rollback()
value={'status':'P10_LOADED_QWEB_MEMORY_COMPONENTS_AND_TRANSLATIONS_COMPLETE',
 'layer':'ACTUAL_LOADED_QWEB_MEMORY_COMPONENTS_READONLY','candidate_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
 'identity':identity,'components':components,'metric_field_mapping':mapping,'translation_checks':translation_checks,
 'loaded_combined_arch_sha256':hashlib.sha256(etree.tostring(combined)).hexdigest(),
 'native_translation_export_sha256':hashlib.sha256(stream.getvalue()).hexdigest(),
 'business_dispatches':0,'database_writes':False,'real_role_or_source_or_permission_claimed':False,
 'request_tokens_empty':True,'rollback_performed':True,'collected_at_utc':dt.datetime.now(dt.UTC).isoformat()}
output=Path(os.environ['YDENTAL_P10_COMPONENT_OUTPUT']);assert output.parent==private/'runtime'
raw=(json.dumps(value,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode()
with os.fdopen(os.open(output,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
print(json.dumps({'status':value['status'],'components':len(components),'metrics':len(mapping),
 'translation_checks':len(translation_checks),'backend_pid':identity[0],'sha256':hashlib.sha256(raw).hexdigest()}))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', required=True)
    parser.add_argument('--output', type=Path, default=PRIVATE / 'runtime/qweb-components.json')
    args = parser.parse_args()
    if not re.fullmatch('[A-Za-z0-9_-]{1,60}', args.label):
        raise RuntimeError('Use an explicit unique safe label.')
    output = args.output.resolve()
    if output.parent != (PRIVATE / 'runtime').resolve() or output.exists():
        raise RuntimeError('Use a fresh file within the P10 private runtime directory.')
    runtime, admission, database, branch, candidate = launcher.validate_pair()
    directory = PRIVATE / 'verification' / ('native-components-' + args.label)
    directory.mkdir(mode=0o700, parents=True)
    config = launcher.render_odoo_config(database, directory)
    environment, _proof = launcher.runtime_child_environment(runtime)
    environment['YDENTAL_P10_COMPONENT_OUTPUT'] = str(output)
    with os.fdopen(os.open(directory / 'executed-source.py', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400), 'w') as stream:
        stream.write(SCRIPT)
    command = [str(launcher.PYTHON), str(launcher.ODOO_BIN), 'shell', '-c', str(config),
               '--no-http', '--shell-interface=python']
    result = {'candidate_commit': candidate, 'branch': branch, 'command': command,
              'started_at_utc': dt.datetime.now(dt.UTC).isoformat(),
              'source_sha256': hashlib.sha256(SCRIPT.encode()).hexdigest(),
              'wrapper_sha256': launcher.file_sha256(Path(__file__)),
              'runtime_sha256': launcher.file_sha256(PRIVATE / 'runtime.json'),
              'admission_sha256': launcher.file_sha256(PRIVATE / 'admission.json'),
              'no_upgrade': True, 'no_http': True, 'no_business_dispatch': True,
              'no_automatic_retry': True}
    write_receipt(directory / 'intent.json', result)
    logfile = directory / 'native.log'
    with logfile.open('xb') as log:
        os.chmod(logfile, 0o600)
        child = subprocess.Popen(command, cwd=ROOT, env=environment, stdin=subprocess.PIPE,
                                 stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        write_receipt(directory / 'child.json', {'pid': child.pid, 'start_ticks': launcher.proc_start_ticks(child.pid)})
        try:
            child.communicate(SCRIPT.encode(), timeout=180)
            code = child.returncode
        except subprocess.TimeoutExpired:
            code = None
        log.flush()
        os.fsync(log.fileno())
    if code is not None:
        config.unlink()
    complete = False
    if code == 0 and output.exists():
        value = json.loads(output.read_text())
        complete = (value.get('status') == 'P10_LOADED_QWEB_MEMORY_COMPONENTS_AND_TRANSLATIONS_COMPLETE'
                    and len(value.get('components', [])) == 15 and value.get('rollback_performed') is True)
        result['artifact_sha256'] = launcher.file_sha256(output)
    result.update(exit_code=code, native_signal=code is not None and code < 0,
                  unknown_child_preserved=code is None, artifact_complete=complete,
                  finished_at_utc=dt.datetime.now(dt.UTC).isoformat(),
                  log_sha256=launcher.file_sha256(logfile), temporary_secret_config_removed=code is not None)
    digest = write_receipt(directory / 'result.json', result)
    print(json.dumps({'exit_code': code, 'native_signal': result['native_signal'],
                      'artifact_complete': complete, 'result_sha256': digest}))
    return 0 if code == 0 and complete else 2


if __name__ == '__main__':
    raise SystemExit(main())

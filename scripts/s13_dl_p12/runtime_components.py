"""Render four loaded settlement lookup QWeb branches using marked memory fixtures.

No settlement service query, business source creation or permission claim is made.
All SQL is read-only and output stays in private evidence for browser coverage.
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
import copy,datetime as dt,decimal,hashlib,json,os,subprocess
from pathlib import Path
from types import SimpleNamespace as NS
from urllib.parse import urlencode
from lxml import etree,html
root=Path.cwd();private=root/'.local/dl-p12'
env.cr.rollback();env.cr.execute('SET TRANSACTION READ ONLY')
env.cr.execute("SELECT pg_backend_pid(),current_database(),(SELECT oid FROM pg_database WHERE datname=current_database()),(pg_control_system()).system_identifier::text,current_user,current_setting('transaction_read_only'),current_setting('transaction_isolation')")
identity=env.cr.fetchone()
assert identity[1:]==('ydental_s11_synth_20261023_01',2171423,'7694897083368259627','ydental_s11_synth_20261023_01','on','repeatable read')
qweb=env['ir.qweb'].with_context(lang='zh_CN')
view=env.ref('ydental_settlement.ydental_settlement_page').with_context(lang='zh_CN')
combined=view._get_combined_arch()
lookup=combined.xpath('.//div[@data-dl-scope="settlement-lookup"]')[0]
assert not lookup.xpath('.//details[@name="settlement-operation"]')
marker='【P12夹具】'
components=[]
for name,selected,populated,paged,long in [('empty-unselected',False,False,False,False),('selected-three-sections',True,True,False,False),('two-way-pagination',False,True,True,False),('long-mixed-values',True,True,True,True)]:
 suffix='长中文混合ABCDEFGHIJ-0123456789'*12 if long else ''
 patient=NS(id=900000001,ydental_number=marker+'业务号PN-900000001'+suffix) if selected else None
 catalog=NS(name=marker+'费用项目'+suffix)
 currency=NS(name='FIXTURE',decimal_places=2)
 actor=NS(name=marker+'执行人'+suffix)
 source_patient=patient or NS(id=900000001,ydental_number=marker+'费用来源患者PN-900000001'+suffix)
 event=NS(id=900000011,name=marker+'完整执行原始名'+suffix,ydental_catalog_id=catalog,ydental_patient_id=source_patient,ydental_business_date=dt.date(2026,10,26),ydental_actor_id=actor,ydental_pending_reason=marker+'待核对原因，禁止出账'+suffix)
 fee=NS(id=900000021,name=marker+'完整费用原始名'+suffix,ydental_event_id=event,ydental_patient_id=source_patient,ydental_amount=decimal.Decimal('123456789.67'),ydental_currency_id=currency)
 today=[fee] if populated else [];history=[copy.deepcopy(fee)] if populated else [];pending=[event] if populated else []
 if history:history[0].id=900000022;history[0].ydental_event_id.id=900000012;history[0].ydental_event_id.ydental_business_date=dt.date(2026,10,25)
 pages={key:(2 if paged else 1) for key in ('today','history','pending','invoices','settled','payments','refunds','closes')}
 counts={key:(151 if paged and key in ('today','history','pending') else int(populated and key in ('today','history','pending'))) for key in pages}
 search_term=marker+'候选查询'+suffix if populated else marker+'无匹配'
 options={'rows':[{'id':900000101+n,'name':marker+'候选患者'+str(n+1)+suffix,'number':marker+'候选号PN-'+str(900000101+n)+suffix} for n in range(2)] if populated else [],'page':2 if paged else 1,'has_more':paged}
 def patient_search_url(page):return '/ydental/settlement?'+urlencode({'q':search_term,'search_page':page})
 def page_url(kind,page):
  params={key+'_page':value for key,value in pages.items()};params[kind+'_page']=page
  if patient:params['patient_id']=patient.id
  return '/ydental/settlement?'+urlencode(params)
 def money(amount,currency):return currency.name+' '+format(amount,'.2f')
 context={'patient':patient,'search_term':search_term,'patient_options':options,'today':today,'history':history,'pending':pending,'pages':pages,'page_counts':counts,'patient_search_url':patient_search_url,'page_url':page_url,'money':money}
 rendered=str(qweb.with_context(minimal_qcontext=True)._render(copy.deepcopy(lookup),context))
 tree=html.fragment_fromstring(rendered,create_parent='div')
 assert len(tree.xpath('.//div[@data-dl-scope="settlement-lookup"]'))==1
 assert not tree.xpath('.//details[@name="settlement-operation"]|.//form[@method="post"]')
 assert len(tree.xpath('.//form[@method="get"]'))==1
 assert len(tree.xpath('.//table'))==3*int(populated)
 assert len(tree.xpath('.//tbody/tr'))==3*int(populated)
 assert len(tree.xpath('.//div[@data-dl-region="fee-overview"]//details/summary'))==3*int(populated)
 assert len(tree.xpath('.//a[contains(@href,"other-stores")]'))==int(selected)
 assert tree.xpath('.//input[@name="q"]')[0].get('value')==search_term
 for svg in tree.xpath('.//*[local-name()="svg"]'):
  assert svg.get('aria-hidden')=='true' and svg.get('focusable')=='false'
 expected_fees=[]
 for kind,rows in [('today',today),('history',history),('pending',pending)]:
  section=tree.xpath('.//section[@data-fee-kind=$kind]',kind=kind)[0]
  original=[]
  if rows:
   row=rows[0]
   if kind=='pending':
    original=[row.ydental_catalog_id.name,row.ydental_patient_id.ydental_number,str(row.ydental_business_date),row.ydental_actor_id.name,row.ydental_pending_reason]
   else:original=[row.ydental_event_id.ydental_catalog_id.name,row.ydental_patient_id.ydental_number,money(row.ydental_amount,row.ydental_currency_id),str(row.ydental_event_id.ydental_business_date)]
   text=''.join(section.itertext())
   for value in original:assert value in text
  expected_fees.append({'kind':kind,'original_cell_values':original,'row_count':len(rows),'page':pages[kind],'page_count':counts[kind],'expected_previous_href':page_url(kind,pages[kind]-1) if paged else None,'expected_next_href':page_url(kind,pages[kind]+1) if paged else None})
 components.append({'name':name,'html':rendered,'html_sha256':hashlib.sha256(rendered.encode()).hexdigest(),'layer':'LOADED_QWEB_MEMORY_COMPONENT','real_source_or_permissions_claimed':False,'business_records_created':0,'selected_patient':selected,'populated':populated,'paged':paged,'long_text':long,'search_term':search_term,'patient_options':options,'expected_fees':expected_fees,'expected_search_previous_href':patient_search_url(1) if paged else None,'expected_search_next_href':patient_search_url(3) if paged else None,'rendered_control_counts':{tag:len(tree.xpath('.//'+tag)) for tag in ('a','summary','button')}})
env.cr.rollback()
value={'status':'P12_LOADED_QWEB_SETTLEMENT_MEMORY_COMPONENTS_COMPLETE','layer':'ACTUAL_LOADED_QWEB_MEMORY_COMPONENTS_READONLY','candidate_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'identity':identity,'components':components,'loaded_combined_arch_sha256':hashlib.sha256(etree.tostring(combined)).hexdigest(),'business_dispatches':0,'database_writes':False,'real_role_or_source_or_permission_claimed':False,'request_tokens_empty':True,'rollback_performed':True,'collected_at_utc':dt.datetime.now(dt.UTC).isoformat()}
output=Path(os.environ['YDENTAL_P12_COMPONENT_OUTPUT']);assert output.parent==private/'runtime'
raw=(json.dumps(value,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode()
with os.fdopen(os.open(output,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
print(json.dumps({'status':value['status'],'components':len(components),'backend_pid':identity[0],'sha256':hashlib.sha256(raw).hexdigest()}))
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
        raise RuntimeError('Use a fresh file within the P12 private runtime directory.')
    output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    runtime, admission, database, branch, candidate = launcher.validate_pair()
    directory = PRIVATE / 'verification' / ('native-components-' + args.label)
    directory.mkdir(mode=0o700, parents=True)
    config = launcher.render_odoo_config(database, directory)
    environment, _proof = launcher.runtime_child_environment(runtime)
    environment['YDENTAL_P12_COMPONENT_OUTPUT'] = str(output)
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
        complete = (value.get('status') == 'P12_LOADED_QWEB_SETTLEMENT_MEMORY_COMPONENTS_COMPLETE'
                    and len(value.get('components', [])) == 4 and value.get('rollback_performed') is True)
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

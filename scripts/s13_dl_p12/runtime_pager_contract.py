"""Verify the loaded shared settlement pager and native call-local opt-in contract.

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
import copy,datetime as dt,hashlib,json,os,subprocess
from pathlib import Path
from urllib.parse import urlencode
from lxml import etree,html
root=Path.cwd();private=root/'.local/dl-p12'
env.cr.rollback();env.cr.execute('SET TRANSACTION READ ONLY')
env.cr.execute("SELECT pg_backend_pid(),current_database(),(SELECT oid FROM pg_database WHERE datname=current_database()),(pg_control_system()).system_identifier::text,current_user,current_setting('transaction_read_only'),current_setting('transaction_isolation')")
identity=env.cr.fetchone();assert identity[1:]==('ydental_s11_synth_20261023_01',2171423,'7694897083368259627','ydental_s11_synth_20261023_01','on','repeatable read')
baseline_path=private/'verification/combined-views-before.json';baseline=json.loads(baseline_path.read_text())
assert baseline['status']=='P12_ACTUAL_NATIVE_COMBINED_ARCH_COMPLETE'
assert baseline['identity'][1:]==list(identity[1:])
xmlid='ydental_settlement.ydental_settlement_page_links'
current=env.ref(xmlid)._get_combined_arch()
assert not current.xpath('.//form|.//input|.//button')
kinds=('today','history','pending','invoices','settled','payments','refunds','closes')
checks=[]
def parsed(raw):return html.fragment_fromstring(raw,create_parent='div')
def semantic(tree):
 return {'nav_count':len(tree.xpath('.//nav')),'aria_labels':tree.xpath('.//nav/@aria-label'),'count_labels':[''.join(n.itertext()).strip() for n in tree.xpath('.//nav/span')],'anchors':[{'href':n.get('href'),'text':''.join(n.itertext()).strip()} for n in tree.xpath('.//a')]}
for lang in ('en_US','zh_CN'):
 qweb=env['ir.qweb'].with_context(lang=lang,minimal_qcontext=True)
 old=etree.fromstring(baseline['languages']['ydental_settlement_page_links'][lang]['combined_arch'].encode())
 for kind in kinds:
  for total,page in [(0,1),(50,1),(51,1),(151,1),(151,2),(151,4)]:
   pages={k:2 for k in kinds};pages[kind]=page
   counts={k:151 for k in kinds};counts[kind]=total
   def page_url(selected,pagenumber):
    params={k+'_page':v for k,v in pages.items()};params[selected+'_page']=pagenumber
    params.update(patient_id=900000001,q='【P12夹具】共享分页',search_page=2)
    return '/ydental/settlement?'+urlencode(params)
   base={'page_kind':kind,'pages':pages,'page_counts':counts,'page_url':page_url}
   original=str(qweb._render(copy.deepcopy(old),dict(base)))
   expected=semantic(parsed(original))
   for mode in ('missing','false','true'):
    context=dict(base)
    if mode!='missing':context['settlement_readonly_actions']=mode=='true'
    actual=str(qweb._render(xmlid,context));tree=parsed(actual)
    assert semantic(tree)==expected,(lang,kind,total,page,mode,'ORIGINAL_HREF_TEXT_CONDITION_CHANGED')
    decorated=tree.xpath('.//*[@data-dl-actions="settlement-readonly-actions"]')
    svgs=tree.xpath('.//*[local-name()="svg"]')
    if mode!='true':
     assert actual==original,(lang,kind,total,page,mode,'DEFAULT_OR_FALSE_HTML_NOT_EXACT_BASELINE')
     assert not decorated and not svgs,(lang,kind,mode,'DEFAULT_CALL_STYLED')
    elif kind in ('today','history','pending') and total>50:
     assert len(svgs)==len(expected['anchors']) and len(decorated)>=len(expected['anchors']),(lang,kind,total,page,'SCOPE_ON_ICONS_OR_OPTIN_MISSING')
     for svg in svgs:assert svg.get('aria-hidden')=='true' and svg.get('focusable')=='false'
    checks.append({'lang':lang,'page_kind':kind,'count':total,'page':page,'flag':mode,'actual_html':actual,'actual_html_sha256':hashlib.sha256(actual.encode()).hexdigest(),'baseline_html_sha256':hashlib.sha256(original.encode()).hexdigest(),'default_or_false_raw_exact':actual==original if mode!='true' else None,'original_semantics':expected,'original_semantics_exact':True,'decorated_count':len(decorated),'svg_count':len(svgs),'actual_flag_true_other_kind_is_artificial_unused_call':mode=='true' and kind not in ('today','history','pending')})
sequence_checks=[]
for lang in ('en_US','zh_CN'):
 qweb=env['ir.qweb'].with_context(lang=lang,minimal_qcontext=True)
 old=etree.fromstring(baseline['languages']['ydental_settlement_page_links'][lang]['combined_arch'].encode())
 parent=etree.Element('div',{'data-p12-component':'loaded-sequential-call-locality'})
 for kind in kinds:
  box=etree.SubElement(parent,'div',{'data-pager-kind':kind})
  call=etree.SubElement(box,'t',{'t-call':xmlid,'page_kind':repr(kind)})
  if kind in ('today','history','pending'):call.set('settlement_readonly_actions','True')
 etree.SubElement(parent,'span',{'data-parent-flag-after':'1','t-out':"'LEAKED' if settlement_readonly_actions else 'ABSENT'"})
 pages={kind:2 for kind in kinds};counts={kind:151 for kind in kinds}
 def page_url(selected,pagenumber):
  params={k+'_page':v for k,v in pages.items()};params[selected+'_page']=pagenumber
  params.update(patient_id=900000001,q='【P12夹具】局部调用顺序',search_page=2)
  return '/ydental/settlement?'+urlencode(params)
 context={'pages':pages,'page_counts':counts,'page_url':page_url}
 rendered=str(qweb._render(copy.deepcopy(parent),context));tree=parsed(rendered)
 assert tree.xpath('.//span[@data-parent-flag-after]/text()')==['ABSENT'],'NATIVE_CALL_FLAG_LEAKED_INTO_PARENT'
 branch_checks=[]
 for kind in kinds:
  box=tree.xpath('.//div[@data-pager-kind=$kind]',kind=kind)[0]
  original=str(qweb._render(copy.deepcopy(old),dict(context,page_kind=kind)))
  originaltree=parsed(original);assert semantic(box)==semantic(originaltree)
  if kind in ('today','history','pending'):
   assert len(box.xpath('.//*[local-name()="svg"]'))==2
   assert len(box.xpath('.//*[@data-dl-actions="settlement-readonly-actions"]'))>=2
   raw_equal_required=False
  else:
   assert not box.xpath('.//*[local-name()="svg"]|.//*[@data-dl-actions="settlement-readonly-actions"]')
   actualnav=box.xpath('./nav')[0];originalnav=originaltree.xpath('./nav')[0]
   assert etree.tostring(actualnav,method='c14n',with_tail=False)==etree.tostring(originalnav,method='c14n',with_tail=False),('LATER_DEFAULT_CALL_CHANGED',lang,kind)
   raw_equal_required=True
  branch_checks.append({'page_kind':kind,'passed_flag':kind in ('today','history','pending'),'original_href_text_condition_exact':True,'default_canonical_nav_exact':True if raw_equal_required else None,'svg_count':len(box.xpath('.//*[local-name()="svg"]'))})
 sequence_checks.append({'lang':lang,'native_parent_source':etree.tostring(parent,encoding='unicode'),'actual_html':rendered,'actual_html_sha256':hashlib.sha256(rendered.encode()).hexdigest(),'three_optin_followed_by_five_unmodified_default_calls':True,'parent_flag_after_calls':'ABSENT','branches':branch_checks})

env.cr.rollback()
value={'status':'P12_ACTUAL_LOADED_SHARED_PAGER_DEFAULT_FALSE_EXACT_BASELINE_OPTIN_AND_ORIGINAL_CONTRACT_PASS','layer':'NATIVE_LOADED_QWEB_READ_ONLY_MEMORY_COMPONENT','identity':identity,'candidate_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'baseline_loaded_view_path':str(baseline_path.relative_to(root)),'baseline_loaded_view_sha256':hashlib.sha256(baseline_path.read_bytes()).hexdigest(),'current_loaded_combined_arch_sha256':hashlib.sha256(etree.tostring(current)).hexdigest(),'checks':checks,'parent_sequence_checks':sequence_checks,'database_writes':False,'real_multi_page_business_or_permissions_claimed':False,'business_dispatches':0,'rollback_performed':True,'collected_at_utc':dt.datetime.now(dt.UTC).isoformat()}
output=Path(os.environ['YDENTAL_P12_PAGER_OUTPUT']);assert output.parent==private/'runtime'
raw=(json.dumps(value,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode()
with os.fdopen(os.open(output,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
print(json.dumps({'status':value['status'],'checks':len(checks),'backend_pid':identity[0],'sha256':hashlib.sha256(raw).hexdigest()}))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', required=True)
    parser.add_argument('--output', type=Path, default=PRIVATE / 'runtime/loaded-pager-contract.json')
    args = parser.parse_args()
    if not re.fullmatch('[A-Za-z0-9_-]{1,60}', args.label):
        raise RuntimeError('Use an explicit unique safe label.')
    output = args.output.resolve()
    if output.parent != (PRIVATE / 'runtime').resolve() or output.exists():
        raise RuntimeError('Use a fresh file within the P12 private runtime directory.')
    output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    runtime, admission, database, branch, candidate = launcher.validate_pair()
    directory = PRIVATE / 'verification' / ('native-pager-contract-' + args.label)
    directory.mkdir(mode=0o700, parents=True)
    config = launcher.render_odoo_config(database, directory)
    environment, _proof = launcher.runtime_child_environment(runtime)
    environment['YDENTAL_P12_PAGER_OUTPUT'] = str(output)
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
        complete = (value.get('status') == 'P12_ACTUAL_LOADED_SHARED_PAGER_DEFAULT_FALSE_EXACT_BASELINE_OPTIN_AND_ORIGINAL_CONTRACT_PASS'
                    and len(value.get('checks', [])) == 288
                    and len(value.get('parent_sequence_checks', [])) == 2 and value.get('rollback_performed') is True)
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

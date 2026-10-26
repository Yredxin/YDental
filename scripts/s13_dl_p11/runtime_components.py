"""Render four loaded source-detail QWeb branches using marked memory fixtures.

No report service query, business source creation or permission claim is made.
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
root=Path.cwd();private=root/'.local/dl-p11'
env.cr.rollback();env.cr.execute('SET TRANSACTION READ ONLY')
env.cr.execute("SELECT pg_backend_pid(),current_database(),(SELECT oid FROM pg_database WHERE datname=current_database()),(pg_control_system()).system_identifier::text,current_user,current_setting('transaction_read_only'),current_setting('transaction_isolation')")
identity=env.cr.fetchone()
assert identity[1:]==('ydental_s11_synth_20261023_01',2171423,'7694897083368259627','ydental_s11_synth_20261023_01','on','repeatable read')
qweb=env['ir.qweb'].with_context(lang='zh_CN')
view=env.ref('ydental_reporting.ydental_operating_report_source').with_context(lang='zh_CN')
combined=view._get_combined_arch();main=combined.xpath('.//main')[0]
marker='【P11夹具】'
values={'metric':'collections','date_from':'2026-10-01','date_to':'2026-10-26','store_ids':'1,2','company_id':'1','currency_id':'1','state':'posted','page':2}
return_url='/ydental/reports?'+urlencode(values)
filters=dict(values,store_ids=[1,2],query_at_utc=dt.datetime.now(dt.UTC).replace(tzinfo=None).isoformat(sep=' ',timespec='seconds'),period_or_snapshot='period')
base={'source_label':marker+'来源合成示意','patient_label':marker+'患者显示，无真实患者',
 'quantity':{'value':'12345.67','label':marker+'币种'},'state_label':marker+'领域状态',
 'event_label':'2026-10-26 02:30:00 UTC','facts_display':[(marker+'价源',marker+'原字段保持'),(marker+'SHA','0123456789abcdef'*4)],
 'allocations':[],'requires_store_switch':False,'business_url':'/ydental/settlement?patient_id=900000001',
 'native_url':'/odoo/action-account.action_move_out_invoice_type/900000001','source_model':'account.payment',
 'source_id':900000001,'trace':marker+'完整技术追溯\nmodel=account.payment\nid=900000001\nsha='+'0123456789abcdef'*4}
allocations=[{'url':'/ydental/settlement?invoice_id='+str(900000001+n),'number':marker+'账单'+str(n+1),'total':'12345.67','allocated':'10.01','balance':'12335.66'} for n in range(3)]
components=[]
for name,count,allocated,cross,long in [('single-plain',1,False,False,False),('single-allocation-cross',1,True,True,False),('two-source-cards',2,False,False,False),('long-mixed-allocation-trace',2,True,True,True)]:
 rows=[]
 for index in range(count):
  row=copy.deepcopy(base);row['source_id']+=index;row['source_label']+=str(index+1)
  row['allocations']=copy.deepcopy(allocations) if allocated else [];row['requires_store_switch']=cross
  if long:
   row['source_label']+=('长中文来源及编号ABCDEFGHIJ-0123456789混排'*9)
   row['patient_label']+=('长中文患者显示用于换行观察'*10)
   row['facts_display'] += [(marker+'长中文原字段',marker+'长中文说明与业务编号ABCDEFGHIJ-0123456789'*40),(marker+'长连续哈希','0123456789abcdef'*30)]
   row['trace'] += '\n'+ '\n'.join(marker+'完整追溯行'+str(n)+' SHA='+'0123456789abcdef'*10 for n in range(60))
  rows.append(row)
 display={'scope':marker+'两个授权门店范围','companies':marker+'法人范围','currency':marker+'分币种',
  'state_label':marker+'全部适用状态','bounds':[{'label':marker+'门店一','timezone':'Asia/Shanghai','start_utc':'2026-09-30 16:00:00','end_exclusive_utc':'2026-10-26 16:00:00'}], 'rows':rows}
 context={'title':marker+'来源钻取详情','return_url':return_url,'display':display,'report':{'filters':filters,'page':2,'page_size':100}}
 rendered=str(qweb.with_context(minimal_qcontext=True)._render(copy.deepcopy(main),context))
 tree=html.fragment_fromstring(rendered,create_parent='div');articles=tree.xpath('.//article');assert len(articles)==count
 returns=tree.xpath('.//a[@href=$u]',u=return_url);assert len(returns)==2
 assert len(tree.xpath('.//article//table'))==int(allocated)*count
 assert len(tree.xpath('.//article//table/tbody/tr'))==int(allocated)*count*3
 for article,row in zip(articles,rows):
  assert article.xpath('.//pre')[0].text==row['trace']
  assert article.xpath('.//dl/dt/text()')==[v[0] for v in row['facts_display']]
  assert article.xpath('.//dl/dd/text()')==[v[1] for v in row['facts_display']]
  assert article.xpath('.//a/@href')==[v['url'] for v in row['allocations']]+[row['business_url'],row['native_url']]
  assert len(article.xpath('.//details/summary'))==1
 for svg in tree.xpath('.//*[local-name()="svg"]'):
  assert svg.get('aria-hidden')=='true' and svg.get('focusable')=='false'
 components.append({'name':name,'html':rendered,'html_sha256':hashlib.sha256(rendered.encode()).hexdigest(),
  'layer':'LOADED_QWEB_MEMORY_COMPONENT','real_source_or_permissions_claimed':False,
  'row_count':count,'has_allocations':allocated,'requires_store_switch':cross,'long_text':long,
  'return_url':return_url,'filters':filters,'original_rows':rows,'rendered_control_counts':{tag:len(tree.xpath('.//'+tag)) for tag in ('a','summary','button')}})
env.cr.rollback()
value={'status':'P11_LOADED_QWEB_SOURCE_MEMORY_COMPONENTS_COMPLETE','layer':'ACTUAL_LOADED_QWEB_MEMORY_COMPONENTS_READONLY',
 'candidate_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'identity':identity,
 'components':components,'loaded_combined_arch_sha256':hashlib.sha256(etree.tostring(combined)).hexdigest(),
 'business_dispatches':0,'database_writes':False,'real_role_or_source_or_permission_claimed':False,
 'request_tokens_empty':True,'rollback_performed':True,'collected_at_utc':dt.datetime.now(dt.UTC).isoformat()}
output=Path(os.environ['YDENTAL_P11_COMPONENT_OUTPUT']);assert output.parent==private/'runtime'
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
        raise RuntimeError('Use a fresh file within the P11 private runtime directory.')
    output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    runtime, admission, database, branch, candidate = launcher.validate_pair()
    directory = PRIVATE / 'verification' / ('native-components-' + args.label)
    directory.mkdir(mode=0o700, parents=True)
    config = launcher.render_odoo_config(database, directory)
    environment, _proof = launcher.runtime_child_environment(runtime)
    environment['YDENTAL_P11_COMPONENT_OUTPUT'] = str(output)
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
        complete = (value.get('status') == 'P11_LOADED_QWEB_SOURCE_MEMORY_COMPONENTS_COMPLETE'
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

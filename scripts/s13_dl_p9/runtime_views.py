"""Collect actual native combined view inheritance in a read-only shell.

Requires independently bound current admission. It never upgrades a module,
starts HTTP, renders a business action or commits a transaction. Unknown native
outcomes preserve the exact child and config for investigation, without retry.
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
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
from lxml import etree
root=Path.cwd(); private=root/'.local/dl-p9'
env.cr.rollback();env.cr.execute('SET TRANSACTION READ ONLY')
env.cr.execute("SELECT pg_backend_pid(),current_database(),(SELECT oid FROM pg_database WHERE datname=current_database()),(pg_control_system()).system_identifier::text,current_user,current_setting('transaction_read_only'),current_setting('transaction_isolation')")
identity=env.cr.fetchone()
assert identity[1:]==('ydental_s11_synth_20261023_01',2171423,'7694897083368259627','ydental_s11_synth_20261023_01','on','repeatable read')
base=env.ref('ydental_print.ydental_document_page')
view_records=base | base._get_inheriting_views()
views=[]
for v in view_records:
 views.append({'id':v.id,'xmlid':v.get_external_id().get(v.id),'inherit_id':v.inherit_id.id or None,'mode':v.mode,'active':v.active,'priority':v.priority,'key':v.key,'arch_db':v.with_context(lang='en_US').arch_db})
arches={}
for lang in ('en_US','zh_CN'):
 view=base.with_context(lang=lang)
 combined=view._get_combined_arch()
 arch=etree.tostring(combined,encoding='unicode')
 details=[]
 for n in combined.xpath('.//main//details'):
  summary=n.find('summary')
  details.append({'xpath':combined.getroottree().getpath(n),'name':n.get('name'),'class':n.get('class'),'summary':'' if summary is None else ''.join(summary.itertext()).strip(),'parent':n.getparent().tag,'top_level':n.getparent().tag=='main','form_actions':n.xpath('.//form/@action')})
 arches[lang]={'combined_arch':arch,'sha256':hashlib.sha256(arch.encode()).hexdigest(),'details':details}
env.cr.rollback()
value={'status':'P9_ACTUAL_NATIVE_COMBINED_ARCH_COMPLETE','layer':'NATIVE_LOADED_VIEW_READONLY','identity':identity,'database_writes':False,'business_dispatches':0,'rollback_performed':True,'view_records':views,'languages':arches,'collected_at_utc':dt.datetime.now(dt.UTC).isoformat()}
path=private/'verification'/('combined-views-'+os.environ['YDENTAL_P9_VIEW_LABEL']+'.json')
raw=(json.dumps(value,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode()
with os.fdopen(os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
print(json.dumps({'status':value['status'],'view_count':len(views),'backend_pid':identity[0],'sha256':hashlib.sha256(raw).hexdigest()}))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', required=True)
    args = parser.parse_args()
    if not re.fullmatch('[A-Za-z0-9_-]{1,60}', args.label):
        raise RuntimeError('Use an explicit safe label.')
    runtime, admission, database, branch, candidate = launcher.validate_pair()
    directory = PRIVATE / 'verification' / ('native-views-' + args.label)
    directory.mkdir(mode=0o700, parents=True)
    config = launcher.render_odoo_config(database, directory)
    environment, proof = launcher.runtime_child_environment(runtime)
    environment['YDENTAL_P9_VIEW_LABEL'] = args.label
    executed = directory / 'executed-source.py'
    with os.fdopen(os.open(executed, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400), 'w') as stream:
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
    artifact = PRIVATE / 'verification' / ('combined-views-' + args.label + '.json')
    complete = False
    if code == 0 and artifact.exists():
        value = json.loads(artifact.read_text())
        complete = value.get('status') == 'P9_ACTUAL_NATIVE_COMBINED_ARCH_COMPLETE' and value.get('rollback_performed') is True
        result['artifact_sha256'] = launcher.file_sha256(artifact)
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

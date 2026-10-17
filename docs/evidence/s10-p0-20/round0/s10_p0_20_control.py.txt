"""One-use P0-20 coordinator; every runtime operation requires the REST gate."""
import configparser
import io
import json
import os
import secrets
import re
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from collections import Counter
from urllib.parse import urlsplit,parse_qs
import s10_p0_20_contract as c

os.umask(0o077)

def readonly(label,name,oid):
    import psycopg2
    c.save(c.PRIVATE/(label+'-intent.json'),{'database':name,'attempt':1,'readonly':True})
    conn=None
    try:
        conn=psycopg2.connect(dbname=name,connect_timeout=5,application_name='s10-p0-20-'+label,options=c.OPTIONS,**c.credentials())
        conn.set_session(readonly=True,isolation_level='REPEATABLE READ',autocommit=False)
        with conn.cursor() as cur:
            cur.execute('SHOW transaction_read_only');assert cur.fetchone()[0]=='on'
            cur.execute('SHOW transaction_isolation');assert cur.fetchone()[0]=='repeatable read'
            snap=c.capture_cursor(cur,name,oid,source=name==c.SOURCE)
        c.save(c.PRIVATE/(label+'-rows.json'),snap)
        c.save(c.OUT/(label+'.json'),c.public_snapshot(snap)|{'READ_ONLY':True,'REPEATABLE_READ':True})
        return snap
    finally:
        if conn is not None:
            conn.rollback();conn.close()
            c.save(c.PRIVATE/(label+'-closed.json'),{'rolled_back':True,'closed':bool(conn.closed)})

def clone(checkpoint):
    import psycopg2
    from psycopg2 import sql
    assert c.read(c.PRIVATE/'source-before-closed.json')['closed']
    assert not c.RUN.exists()
    with socket.socket() as sock:sock.bind(('127.0.0.1',c.PORT))
    c.RUN.mkdir(mode=0o700)
    shutil.copytree(c.SOURCE_RUN/'data/filestore'/c.SOURCE,c.RUN/'data/filestore'/c.NAME,copy_function=shutil.copy2)
    assert c.filestore(c.RUN,c.NAME)==c.filestore(c.SOURCE_RUN,c.SOURCE)
    c.save(c.PRIVATE/'maintenance-intent.json',{'attempt':1,'dbname':'postgres'})
    conn=None
    try:
        conn=psycopg2.connect(dbname='postgres',connect_timeout=5,options='-c statement_timeout=30000 -c lock_timeout=3000',**c.credentials())
        conn.autocommit=True
        with conn.cursor() as cur:
            cur.execute('SELECT oid,datname FROM pg_database ORDER BY oid')
            databases=dict(cur.fetchall())
            assert databases[c.SOURCE_OID]==c.SOURCE and c.NAME not in databases.values()
            cur.execute('SELECT system_identifier::text FROM pg_control_system()');assert cur.fetchone()[0]==c.CLUSTER
            cur.execute('SELECT pid FROM pg_stat_activity WHERE datname=%s',(c.SOURCE,));assert not cur.fetchall()
            assert conn.info.transaction_status==psycopg2.extensions.TRANSACTION_STATUS_IDLE
            c.save(c.PRIVATE/'create-intent.json',{'attempt':1,'checkpoint':checkpoint['comment_id'],'name':c.NAME,'source':c.SOURCE})
            cur.execute(sql.SQL('CREATE DATABASE {} WITH TEMPLATE {}').format(sql.Identifier(c.NAME),sql.Identifier(c.SOURCE)))
            cur.execute('SELECT oid FROM pg_database WHERE datname=%s',(c.NAME,));oid=cur.fetchone()[0]
            assert oid not in databases
            c.save(c.PRIVATE/'created.json',{'database':c.NAME,'oid':oid,'old_oids':sorted(databases)})
    finally:
        if conn is not None:conn.close()
    parser=configparser.ConfigParser(interpolation=None)
    parser['options']={'db_host':'127.0.0.1','db_port':'5432','db_user':'odoo','db_password':c.credentials()['password'],
        'db_name':c.NAME,'dbfilter':'^'+c.NAME+'$','db_maxconn':'8',
        'addons_path':','.join(str(p) for p in (c.CORE_ROOT/'odoo/addons',c.CORE_ROOT/'addons',c.ROOT)),
        'data_dir':str(c.RUN/'data'),'http_interface':'127.0.0.1','http_port':str(c.PORT),
        'list_db':'False','workers':'0','max_cron_threads':'0','log_handler':'odoo.sql_db.connection:DEBUG','admin_passwd':secrets.token_urlsafe(32),
        'smtp_server':'127.0.0.1','smtp_port':'1'}
    text=io.StringIO();parser.write(text)
    (c.RUN/'odoo.conf').write_text(text.getvalue())
    c.save(c.RUN/'database.json',{'database':c.NAME,'oid':oid,'cluster':c.CLUSTER,'source':c.SOURCE,
        'source_oid':c.SOURCE_OID,'head':c.BASE,'core':c.CORE,'checkpoint':checkpoint['comment_id'],
        'config_sha256':c.sha((c.RUN/'odoo.conf').read_bytes())})
    return oid

def native_env():
    env=os.environ.copy()
    env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONFAULTHANDLER='1',
        PYTHONPATH=str(c.ROOT/'.local/s04-deps'),PGAPPNAME='s10-p0-20-native',
        PGOPTIONS='-c statement_timeout=15000 -c lock_timeout=3000 -c idle_in_transaction_session_timeout=15000 -c timezone=UTC',
        FONTCONFIG_FILE=str(c.ROOT/'.local/s00-b-deps/browser-fonts.conf'),
        DEBUG='pw:browser')
    return env

def metadata_after(before,after):
    return c.persist_review('metadata-independent',before,after,lambda a,b:c.metadata_gate(a,b,postcommit=True))

def native_connections(path, cap):
    text=path.read_text() if path.exists() else ''
    pids=[int(p) for p in re.findall(r'Create new connection backend PID (\d+)',text)]
    # Pool occupancy and cumulative creations are different native facts.
    occupancy=[int(x) for x in re.findall(r'ConnectionPool\([^)]*count=(\d+)',text)]
    assert not occupancy or max(occupancy)<=8,'NATIVE_POOL_OCCUPANCY'
    if 'Fatal Python error: Segmentation fault' in text:raise RuntimeError('NATIVE_SIGSEGV')
    return pids

def run():
    ck=c.checkpoint()
    c.save(c.PRIVATE/'execution-intent.json',{'authorization':c.AUTH,'checkpoint':ck['comment_id'],'attempt':1})
    process=None;source=None;oid=None;after_meta=None
    result={'authorization':c.AUTH,'base':c.BASE,'status':'BLOCKED','failed_phase':None,'runtime_zero_budget':dict.fromkeys(c.ZERO,0)}
    phase='source-before'
    try:
        c.seal()
        source=readonly('source-before',c.SOURCE,c.SOURCE_OID)
        expected=c.read(c.ROOT/'docs/evidence/s10-p0-18/source-after.json')['signatures']
        assert source['signatures']==expected, 'SEALED_W5_DRIFT'
        c.actions_consistent(source)
        for name,old in c.old_metadata().items():
            _model,table,ident,xid=c.IDS[name]
            assert c.row_map(source['tables'][table])[ident]==old['record']
            assert c.row_map(source['tables']['ir_model_data'])[xid]==old['xmlid']
        phase='create';oid=clone(ck)
        phase='target-before';before=readonly('target-before',c.NAME,oid)
        c.persist_review('clone-initial',source,before,c.same_snapshot)
        phase='metadata-process'
        argv=[str(c.PYTHON),str(c.ROOT/'scripts/s10_p0_20_metadata.py')]
        c.save(c.PRIVATE/'metadata-process-intent.json',{'argv':argv,'attempt':1})
        with (c.RUN/'metadata.log').open('xb') as log:
            p=subprocess.Popen(argv,cwd=c.ROOT,env=native_env(),stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
            try:rc=p.wait(timeout=120)
            except subprocess.TimeoutExpired:
                p.terminate();p.wait(timeout=20);raise
        result['metadata_exit_code']=rc
        result['native_metadata_backend_pids']=native_connections(c.RUN/'metadata.log',4)
        assert rc==0, 'METADATA_PROCESS_FAILED'
        phase='target-metadata-after';after_meta=readonly('target-metadata-after',c.NAME,oid)
        metadata_after(before,after_meta)
        assert c.filestore(c.RUN,c.NAME)==c.filestore(c.SOURCE_RUN,c.SOURCE),'METADATA_FILESTORE_DRIFT'
        phase='web-start'
        assert c.sha((c.RUN/'odoo.conf').read_bytes())==c.read(c.RUN/'database.json')['config_sha256']
        argv=[str(c.PYTHON),str(c.CORE_ROOT/'odoo-bin'),'-c',str(c.RUN/'odoo.conf')]
        c.save(c.PRIVATE/'http-intent.json',{'argv':argv,'attempt':1})
        with (c.RUN/'http.log').open('xb') as log:
            process=subprocess.Popen(argv,cwd=c.ROOT,env=native_env(),stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        began=time.monotonic()
        while True:
            assert process.poll() is None, 'HTTP_PROCESS_EARLY_EXIT'
            try:
                with socket.create_connection(('127.0.0.1',c.PORT),timeout=1):break
            except OSError:
                assert time.monotonic()-began<60,'HTTP_START_TIMEOUT';time.sleep(0.25)
        phase='firefox'
        native_connections(c.RUN/'http.log',4)
        c.save(c.PRIVATE/'browser-process-intent.json',{'attempt':1})
        argv=[str(c.PYTHON),str(c.ROOT/'scripts/s10_p0_20_browser.py')]
        with (c.RUN/'browser.log').open('xb') as log:
            p=subprocess.Popen(argv,cwd=c.ROOT,env=native_env(),stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
            try:
                start=time.monotonic()
                while p.poll() is None:
                    native_connections(c.RUN/'http.log',4)
                    if time.monotonic()-start>150:raise subprocess.TimeoutExpired(argv,150)
                    time.sleep(0.2)
                rc=p.returncode
            except subprocess.TimeoutExpired:
                p.terminate();p.wait(timeout=20);raise
            except BaseException:
                if p.poll() is None:
                    p.terminate();p.wait(timeout=20)
                raise
        result['browser_exit_code']=rc
        assert rc==0,'BROWSER_FAILED'
        result['status']='RUNTIME_COMPLETE_PENDING_PDF_VISUAL_AND_GPT'
    except BaseException as e:
        result.update(status='BLOCKED',failed_phase=phase,error_type=type(e).__name__,error_sha256=c.sha(str(e).encode()))
        c.save(c.PRIVATE/'execution-error.json',{'phase':phase,'error':str(e)})
    finally:
        if process is not None:
            if process.poll() is None:
                process.terminate()
                try:process.wait(timeout=20)
                except subprocess.TimeoutExpired:process.kill();process.wait()
            result['http_exit_code']=process.returncode
            if process.returncode!=0:result['status']='BLOCKED'
        if oid is not None:
            try:
                final=readonly('target-after',c.NAME,oid)
                if after_meta is not None and (c.PRIVATE/'browser-success.json').exists():
                    context=c.read(c.PRIVATE/'browser-success.json')
                    def web_decision(a,b):
                        c.actions_consistent(a);c.actions_consistent(b)
                        for label in ('action_projection','action_only','action_inherits'):
                            assert a[label]==b[label],'WEB_ACTION_PROJECTION_CHANGED'
                        return c.web_gate(a['tables'],b['tables'],context)
                    facts=c.persist_review('web-final',after_meta,final,web_decision)
                    source_files=c.filestore(c.SOURCE_RUN,c.SOURCE)
                    target_files=c.filestore(c.RUN,c.NAME)
                    assert all(target_files.get(p)==h for p,h in source_files.items()),'OLD_FILESTORE_CHANGED'
                    new_assets=c.append_only(after_meta['tables']['ir_attachment'],final['tables']['ir_attachment'],12)
                    assert set(target_files)-set(source_files)<={r['store_fname'] for r in new_assets},'NON_ASSET_FILE_ADDED'
                    for row in new_assets:
                        data=(c.RUN/'data/filestore'/c.NAME/row['store_fname']).read_bytes()
                        assert len(data)==row['file_size'] and __import__('hashlib').sha1(data).hexdigest()==row['checksum']
                    facts['old_filestore152_unchanged']=True
                    c.save(c.OUT/'economic-web-verification.json',facts)
                    result['target_final_invariants']='PASS'
                else:
                    result['target_final_invariants']='CAPTURED_INCOMPLETE_EXECUTION'
                    c.persist_review('stopped-final',source,final,lambda a,b:{'STOPPED':True,'changed_tables':[t for t in a['tables'] if a['tables'][t]!=b['tables'][t]],'not_a_success_gate':True})
                    c.save(c.OUT/'stopped-target-table-diff.json',{'changed_tables':[t for t in source['tables'] if source['tables'][t]!=final['tables'][t]],'economic_tables_unchanged':all(source['tables'][t]==final['tables'][t] for t in source['tables'] if t.startswith(('account_','stock_','ydental_settlement_','ydental_treatment_','ydental_clinical_','ydental_intake_','ydental_patient_')))})
                    result['stopped_clone_filestore_exact']=c.filestore(c.RUN,c.NAME)==c.filestore(c.SOURCE_RUN,c.SOURCE)
            except BaseException as e:
                result.update(status='BLOCKED',target_final_error_type=type(e).__name__,target_final_error_sha256=c.sha(str(e).encode()))
                c.save(c.PRIVATE/'target-final-error.json',{'error':str(e)})
        if (c.OUT/'browser-result.json').exists():
            try:
                browser=c.read(c.OUT/'browser-result.json')
                log=(c.RUN/'http.log').read_text()
                server=[]
                for method,url,status in re.findall(r'"(GET|POST) ([^ ]+) HTTP/[0-9.]+" (\d{3})',log):
                    u=urlsplit(url)
                    server.append({'method':method,'path':u.path,'query':parse_qs(u.query,keep_blank_values=True),'status':int(status)})
                key=lambda r:(r['method'],r['path'],c.canonical(r.get('query',{})))
                requests=Counter(key(r) for r in browser['requests'])
                response_counts=Counter(key(r) for r in browser['responses'])
                server_counts=Counter(key(r) for r in server)
                response_status=Counter((key(r),r['status']) for r in browser['responses'])
                server_status=Counter((key(r),r['status']) for r in server)
                equal=requests==response_counts==server_counts and response_status==server_status
                c.save(c.OUT/'http-reconciliation.json',{'browser_requests':len(browser['requests']),'browser_responses':len(browser['responses']),'server_requests':server,'complete_counter_and_status_equal':equal,'redirect_GET_included':True})
                result['browser_counts']=browser['counts'];result['HTTP_reconciliation']=equal
                assert equal,'REQUEST_RESPONSE_SERVER_MISMATCH'
            except BaseException as e:
                result.update(status='BLOCKED',http_reconciliation_error_type=type(e).__name__)
        if source is not None and result['status']!='RUNTIME_COMPLETE_PENDING_PDF_VISUAL_AND_GPT':
            try:
                end=readonly('source-after',c.SOURCE,c.SOURCE_OID)
                c.persist_review('source-final',source,end,c.same_snapshot)
                c.seal();result['source_final643']='PASS'
            except BaseException as e:
                result.update(status='BLOCKED',source_final_error_type=type(e).__name__,source_final_error_sha256=c.sha(str(e).encode()))
        labels=['source-before','source-after','target-before','target-metadata-after','target-after','maintenance','create','metadata-process','xml-import','http','browser-process']
        result['actual_attempts']={label:int((c.PRIVATE/(label+'-intent.json')).exists()) for label in labels}
        try:
            result['native_web_backend_pids']=native_connections(c.RUN/'http.log',4)
            if (c.RUN/'browser.log').exists():
                log=(c.RUN/'browser.log').read_text()
                result['firefox_exits']=re.findall(r'<process did exit: exitCode=(\S+), signal=(\S+)>',log)
                if (c.PRIVATE/'firefox-launch-intent.json').exists():
                    assert result['firefox_exits']==[('0','null')], 'FIREFOX_EXIT_UNKNOWN'
        except BaseException as e:
            result.update(status='BLOCKED',native_or_browser_exit_error_type=type(e).__name__)
        result['native_connections']='Native connection DEBUG backend-create records counted separately; cumulative metadata/Web physical creations fully recorded separately, contemporaneous pool<=8, no retry on failure.'
        result['metadata_commit_attempts']=int((c.PRIVATE/'metadata-commit-intent.json').exists())
        result['metadata_committed_marker']=int((c.PRIVATE/'metadata-committed.json').exists())
        c.save(c.OUT/'execution-result.json',result)
    print(json.dumps(result))
    return 0 if result['status']=='RUNTIME_COMPLETE_PENDING_PDF_VISUAL_AND_GPT' else 1

if __name__=='__main__':
    if len(sys.argv)==2 and sys.argv[1]=='source-final':
        c.checkpoint()
        before=c.read(c.PRIVATE/'source-before-rows.json')
        end=readonly('source-after',c.SOURCE,c.SOURCE_OID)
        c.persist_review('source-final',before,end,c.same_snapshot);c.seal()
        print('FINAL_W5_643_FILES_PASS')
    else:sys.exit(run())

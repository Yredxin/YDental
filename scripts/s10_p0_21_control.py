"""One new B, bound commands, finite attempts, no old business connections."""
import configparser
import io
import json
import os
from pathlib import Path
import re
import secrets
import socket
import subprocess
import sys
import s10_p0_21_contract as c

SCENARIOS=['f1_740','document_original','f5_270_200','f2_f3_refund_close','discount_waive','quantity_correction','drug_return','t09_trade','same_company_transfer','audit_integrity','security_matrix','idempotency','late_close','original_security']

def native_env(action):
    e=os.environ.copy();e.update(PYTHONDONTWRITEBYTECODE='1',PYTHONFAULTHANDLER='1',PYTHONPATH=str(c.ROOT/'.local/s04-deps'),
      PGAPPNAME='s10-p0-21-'+action,PGOPTIONS=c.OPTIONS,FONTCONFIG_FILE=str(c.ROOT/'.local/s00-b-deps/browser-fonts.conf'),
      YDENTAL_S10_RUN_DIR=str(c.RUN),YDENTAL_P021_ACTION=action,DEBUG='pw:browser')
    return e

def create():
    import psycopg2
    from psycopg2 import sql
    c.gate();assert not c.RUN.exists()
    with socket.socket() as s:s.bind(('127.0.0.1',c.PORT))
    c.event('maintenance_intent',database='postgres',target=c.NAME)
    conn=psycopg2.connect(dbname='postgres',connect_timeout=5,options='-c statement_timeout=30000 -c lock_timeout=3000',**c.credentials())
    try:
        conn.autocommit=True
        with conn.cursor() as cur:
            cur.execute('SELECT oid,datname FROM pg_database ORDER BY oid');old=dict(cur.fetchall());assert c.NAME not in old.values()
            cur.execute('SELECT system_identifier::text FROM pg_control_system()');assert cur.fetchone()[0]==c.CLUSTER
            c.event('CREATE_intent',database=c.NAME)
            cur.execute(sql.SQL('CREATE DATABASE {} TEMPLATE template0 ENCODING %s').format(sql.Identifier(c.NAME)),('UTF8',))
            cur.execute('SELECT oid FROM pg_database WHERE datname=%s',(c.NAME,));oid=cur.fetchone()[0];assert oid not in old and oid not in c.PROTECTED
    finally:conn.close()
    c.RUN.mkdir(mode=0o700)
    p=configparser.ConfigParser(interpolation=None);p['options']={'db_host':'127.0.0.1','db_port':'5432','db_user':'odoo','db_password':c.credentials()['password'],
      'db_name':c.NAME,'dbfilter':'^'+c.NAME+'$','db_maxconn':'8','addons_path':','.join(str(p) for p in (c.CORE_ROOT/'odoo/addons',c.CORE_ROOT/'addons',c.ROOT)),
      'data_dir':str(c.RUN/'data'),'http_interface':'127.0.0.1','http_port':str(c.PORT),'list_db':'False','workers':'0','max_cron_threads':'0','log_handler':'odoo.sql_db.connection:DEBUG','admin_passwd':secrets.token_urlsafe(32),'smtp_server':'127.0.0.1','smtp_port':'1'}
    f=io.StringIO();p.write(f);(c.RUN/'odoo.conf').write_text(f.getvalue())
    c.save(c.RUN/'database.json',{'database':c.NAME,'oid':oid,'cluster':c.CLUSTER,'port':c.PORT,'core':c.CORE,'authorization':c.AUTH,'parent':c.BASE,'config_sha256':c.sha((c.RUN/'odoo.conf').read_bytes()),'source':'template0 normal native install; no old business source'})
    c.save(c.OUT/'created.json',{'database':c.NAME,'oid':oid,'cluster':c.CLUSTER,'port':c.PORT,'not_old_oid':True});c.event('CREATE_returned',oid=oid)

def action(name):
    plan=c.gate();assert name in ['install','configure','upgrade','audit-before-upgrade','audit-after-upgrade']+SCENARIOS
    assert not (c.PRIVATE/'GLOBAL-STOP.json').exists()
    attempt=plan.get('round',0);label='r'+str(attempt)+'-'+name
    c.save(c.PRIVATE/(label+'-process-intent.json'),{'action':name,'commit':c.git('rev-parse','HEAD')})
    if name in ('install','upgrade'):
        argv=[str(c.PYTHON),str(c.CORE_ROOT/'odoo-bin'),'-c',str(c.RUN/'odoo.conf'),'-i' if name=='install' else '-u','l10n_cn,ydental_settlement_test' if name=='install' else 'ydental_settlement','--without-demo=all','--load-language','en_US,zh_CN','--stop-after-init','--no-http'];timeout=480
    else:argv=[str(c.PYTHON),str(c.ROOT/'scripts/s10_p0_21_native.py'),name];timeout=360
    log=c.RUN/(label+'.log')
    with log.open('xb') as f:
        p=subprocess.Popen(argv,cwd=c.ROOT,env=native_env(label),stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT)
        try:rc=p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=20);rc=p.returncode
    raw=log.read_bytes();fatal=rc in (-11,139) or b'Fatal Python error: Segmentation fault' in raw
    backend=[int(x) for x in re.findall(rb'Create new connection backend PID (\d+)',raw)]
    pools=[int(x) for x in re.findall(rb'ConnectionPool\([^)]*count=(\d+)',raw)]
    result={'action':name,'round':attempt,'pid':p.pid,'exit_code':rc,'SIGSEGV':fatal,'backend_creations':backend,'native_cumulative':len(backend),'observed_pool_max':max(pools,default=0),'DSNs_observed':sorted(set(x.decode() for x in re.findall(rb'dbname=([^ ]+)',raw))),'per_PID_DSN':'UNKNOWN if not in creation log','log_sha256':c.sha(raw),'log_bytes':len(raw),'argv':argv}
    c.save(c.OUT/(label+'-result.json'),result)
    if fatal:c.save(c.PRIVATE/'GLOBAL-STOP.json',result)
    print(json.dumps(result));return rc

if __name__=='__main__':
    os.umask(0o077)
    if sys.argv[1]=='create':create()
    elif sys.argv[1]=='final-audit':c.gate();c.readonly('final')
    else:sys.exit(action(sys.argv[1]))

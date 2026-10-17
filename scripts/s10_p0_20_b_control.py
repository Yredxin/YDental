"""Bounded fresh B installation and three grouped native-service scenarios."""
import configparser
import io
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time
import s10_p0_20_contract as c
from s10_p0_20_control import native_env

NAME='ydental_s10_test_20261017040000_20b0cafe'
RUN=c.ROOT/'.local'/NAME
PORT=18321
SCENARIOS=['f1_740','f5_270_200','f2_f3_refund_close','discount_waive','quantity_correction','drug_return','t09_trade','same_company_transfer','audit_integrity','security_matrix','idempotency','late_close']

def create():
    import psycopg2
    from psycopg2 import sql
    c.checkpoint()
    assert not RUN.exists()
    with socket.socket() as sock:sock.bind(('127.0.0.1',PORT))
    c.save(c.PRIVATE/'B-create-intent.json',{'name':NAME,'maintenance':1,'CREATE':1,'template':'template0'})
    conn=psycopg2.connect(dbname='postgres',connect_timeout=5,options='-c statement_timeout=30000 -c lock_timeout=3000',**c.credentials())
    try:
        conn.autocommit=True
        with conn.cursor() as cur:
            cur.execute('SELECT oid,datname FROM pg_database ORDER BY oid');old=dict(cur.fetchall());assert NAME not in old.values()
            cur.execute('SELECT system_identifier::text FROM pg_control_system()');assert cur.fetchone()[0]==c.CLUSTER
            cur.execute(sql.SQL('CREATE DATABASE {} TEMPLATE template0 ENCODING %s').format(sql.Identifier(NAME)),('UTF8',))
            cur.execute('SELECT oid FROM pg_database WHERE datname=%s',(NAME,));oid=cur.fetchone()[0];assert oid not in old
    finally:conn.close()
    RUN.mkdir(mode=0o700)
    parser=configparser.ConfigParser(interpolation=None)
    parser['options']={'db_host':'127.0.0.1','db_port':'5432','db_user':'odoo','db_password':c.credentials()['password'],
      'db_name':NAME,'dbfilter':'^'+NAME+'$','db_maxconn':'8','addons_path':','.join(str(p) for p in (c.CORE_ROOT/'odoo/addons',c.CORE_ROOT/'addons',c.ROOT)),
      'data_dir':str(RUN/'data'),'http_interface':'127.0.0.1','http_port':str(PORT),'list_db':'False','workers':'0','max_cron_threads':'0','log_handler':'odoo.sql_db.connection:DEBUG','admin_passwd':secrets.token_urlsafe(32),'smtp_server':'127.0.0.1','smtp_port':'1'}
    s=io.StringIO();parser.write(s);(RUN/'odoo.conf').write_text(s.getvalue())
    c.save(RUN/'database.json',{'database':NAME,'oid':oid,'cluster':c.CLUSTER,'port':PORT,'core':c.CORE,'source_commit':c.BASE,'authorization':c.AUTH,'config_sha256':c.sha((RUN/'odoo.conf').read_bytes()),'source':'template0; native normal install; not W5 family'})
    c.save(c.OUT/'B-created.json',{'database':NAME,'oid':oid,'cluster':c.CLUSTER,'port':PORT,'old_oid_reuse':False})

def action(name):
    c.checkpoint()
    assert name in ['install','upgrade']+SCENARIOS+['snapshot-before-upgrade','snapshot-after-upgrade']
    marker=c.read(RUN/'database.json');assert marker['database']==NAME and marker['cluster']==c.CLUSTER and marker['authorization']==c.AUTH
    assert marker['oid'] not in [2100310,2100325,2100326,2100327,2100330]
    assert marker['config_sha256']==c.sha((RUN/'odoo.conf').read_bytes())
    assert not (c.PRIVATE/'GLOBAL-STOP.json').exists(),'GLOBAL_STOP'
    round_id=c.read(c.PRIVATE/'active-increment.json')['round'] if (c.PRIVATE/'active-increment.json').exists() else 0
    label='B-r'+str(round_id)+'-'+name
    c.save(c.PRIVATE/(label+'-intent.json'),{'action':name,'attempt':1,'commit':c.git('rev-parse','HEAD').decode().strip()})
    env=native_env();env['YDENTAL_S10_RUN_DIR']=str(RUN)
    if name in ('install','upgrade'):
        argv=[str(c.PYTHON),str(c.CORE_ROOT/'odoo-bin'),'-c',str(RUN/'odoo.conf'),'-i' if name=='install' else '-u','l10n_cn,ydental_settlement_test' if name=='install' else 'ydental_settlement','--without-demo=all','--load-language','en_US,zh_CN','--stop-after-init','--no-http']
        timeout=480
    else:
        argv=[str(c.PYTHON),str(c.ROOT/'scripts/s10_p0_20_b_native.py'),name];timeout=180
    log=RUN/(name+'-r'+str(round_id)+'.log')
    with log.open('xb') as f:
        p=subprocess.Popen(argv,cwd=c.ROOT,env=env,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT)
        try:rc=p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=20);rc=p.returncode
    raw=log.read_bytes();fatal=rc in (-11,139) or b'Fatal Python error: Segmentation fault' in raw
    facts={'action':name,'pid':p.pid,'exit_code':rc,'SIGSEGV':fatal,'log_sha256':c.sha(raw),'log_bytes':len(raw),'command':argv,'timeout_seconds':timeout}
    c.save(c.OUT/(label+'-result.json'),facts)
    if fatal:c.save(c.PRIVATE/'GLOBAL-STOP.json',facts)
    print(json.dumps(facts),flush=True)
    return rc

if __name__=='__main__':
    os.umask(0o077)
    if sys.argv[1]=='create':create()
    else:sys.exit(action(sys.argv[1]))

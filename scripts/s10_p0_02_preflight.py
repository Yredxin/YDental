"""CREATE-before checkpoint material: source, parser, full fault injection, hashes."""

import hashlib
import json
import socket
import subprocess
from pathlib import Path

import psycopg2

from s10_p0_02_control import (AUTH, BROWSER_ARGV, BRANCH, CORE, CORE_HEAD,
    HEAD, HTTP_ARGV, PORT, PREFLIGHT, PRIVATE, ROOT, SCRIPTS, SOURCE,
    SOURCE_CONFIG, SOURCE_MARKER, TARGET, TARGET_RUN, UPGRADE_ARGV,
    authority, compact, source_gate)
from s10_p0_02_snapshot import (SOURCE_RUN, connect, file_sha, identity, public,
    snapshot)


def old_signature(cur,table):
    digest=hashlib.sha256(); count=0
    cur.execute(f'SELECT row_to_json(t)::text FROM {table} t ORDER BY id')
    for (row,) in cur:
        digest.update(row.encode()+b'\n');count+=1
    return {'rows':count,'sha256':digest.hexdigest()}


def prior_source_check():
    old=json.loads((ROOT/'docs/evidence/s10-p0-01/preflight.json').read_text())
    with connect(SOURCE) as conn,conn.cursor() as cur:
        verified={name:old_signature(cur,name)==value
                  for name,value in old['table_signatures'].items()}
    assert all(verified.values()) and len(verified)==7
    assert old['source']['marker_sha256']==SOURCE_MARKER
    assert old['source']['config_sha256']==SOURCE_CONFIG
    return {'seven_prior_table_signatures_equal':verified}


def module_candidates():
    old='ydental_s10_test_20261015060000_b6c7d8e9'
    new='ydental_s10_test_20261015064000_d41e7b62'
    output=[]
    with connect(old) as conn,conn.cursor() as cur:
        cur.execute('SELECT name,state,latest_version,write_date FROM ir_module_module ORDER BY name')
        old_rows={row[0]:row[1:] for row in cur.fetchall()}
    with connect(new) as conn,conn.cursor() as cur:
        cur.execute('SELECT name,state,latest_version,write_date FROM ir_module_module ORDER BY name')
        new_rows={row[0]:row[1:] for row in cur.fetchall()}
    assert set(old_rows)==set(new_rows) and len(old_rows)==702
    for name in old_rows:
        old_state,old_version,old_date=old_rows[name]
        new_state,new_version,new_date=new_rows[name]
        assert (old_state,old_version)==(new_state,new_version)
        if old_date!=new_date: output.append(name)
    assert len(output)==682 and 'ydental_settlement_test' in output
    return sorted(output)


def main():
    authority()
    rows,activity=identity()
    assert TARGET not in rows and not activity and not TARGET_RUN.exists()
    with socket.socket() as sock: sock.bind(('127.0.0.1',PORT))
    source=snapshot(SOURCE,business=True)
    source_gate(source)
    prior=prior_source_check()
    candidates=module_candidates()
    compile_command=[str(CORE/'.venv/bin/python'),'-m','py_compile']+[str(p) for p in SCRIPTS]
    subprocess.run(compile_command,cwd=ROOT,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    cli=subprocess.run([str(CORE/'.venv/bin/python'),str(ROOT/'scripts/s10_p0_02_cli_offline.py')],
        cwd=ROOT,check=True,text=True,capture_output=True,timeout=30)
    offline=subprocess.run([str(CORE/'.venv/bin/python'),str(ROOT/'scripts/s10_p0_02_offline.py')],
        cwd=ROOT,check=True,text=True,capture_output=True,timeout=60)
    cli_result=json.loads(cli.stdout); offline_result=json.loads(offline.stdout)
    assert cli_result['status']=='REAL_CLI_PARSER_PASS'
    assert offline_result['status']=='SIMULATED_PASS' and offline_result['count']>=28
    result={'status':'PREFLIGHT_PASS_NO_CREATE_YET','authorization_comment':AUTH,
        'branch':BRANCH,'head':HEAD,'core':CORE_HEAD,'source':public(source),
        'source_config_sha256':file_sha(SOURCE_RUN/'odoo.conf'),
        'source_marker_sha256':file_sha(SOURCE_RUN/'database.json'),
        'prior_source_check':prior,'target':TARGET,'port':PORT,
        'module_write_date_candidates':candidates,
        'allowed_views':sorted(__import__('s10_p0_02_snapshot').ALLOWED_VIEWS),
        'upgrade_argv':list(UPGRADE_ARGV),'http_argv':list(HTTP_ARGV),
        'browser_argv':list(BROWSER_ARGV),
        'create_sql':'CREATE DATABASE "'+TARGET+'" WITH TEMPLATE "'+SOURCE+'"',
        'scripts_sha256':{str(path.relative_to(ROOT)):file_sha(path) for path in SCRIPTS},
        'cli_parser':cli_result,'offline':offline_result,
        'budgets':{'create':1,'upgrade':1,'http':1,'firefox':1,
                   'reject':1,'unlock':1,'negative_posts':2,'shell':0},
        'budgets_used':{'create':0,'upgrade':0,'http':0,'firefox':0,
                        'reject':0,'unlock':0,'negative_posts':0,'shell':0}}
    PREFLIGHT.parent.mkdir(parents=True,exist_ok=True)
    PREFLIGHT.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':result['status'],'source_oid':source['oid'],
        'tables':len(source['tables']),'schema':source['schema'],
        'module_candidates':len(candidates),'offline_cases':offline_result['count'],
        'preflight_sha256':file_sha(PREFLIGHT)}))


if __name__=='__main__':
    main()

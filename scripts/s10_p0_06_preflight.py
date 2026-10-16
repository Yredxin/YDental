"""Fresh P006 read-only source/role/SQL/DOM/CLI gates, before any CREATE or Odoo."""
import json
import socket
import subprocess
from pathlib import Path
import s10_p0_06_control as c
s=c.s

HISTORY={
 'ydental_s10_test_20261014020300_8b6c1d4e': (2056451,'.local/s10-p0-02/source-before.json',None),
 'ydental_s10_test_20261015_p002_6d84a2c1': (2100311,'.local/s10-p0-03/source-before.json','managed'),
 'ydental_s10_test_20261016_p003_75c1e9b2': (2100319,'.local/s10-p0-03/stopped-readonly.json','managed'),
 s.SOURCE:(s.SOURCE_OID,'.local/s10-p0-04/stopped-readonly.json','managed')}


def history_gate():
    result={}
    for name,(oid,filename,key) in HISTORY.items():
        old=json.loads((s.ROOT/filename).read_text());old=old[key] if key else old
        now=s.snapshot(name)
        for field in ('database','oid','cluster','tables','schema','modules','views','view_rows',
                      'filestore','attachment_pointers'):
            assert now[field]==old[field],(name,field)
        assert now['oid']==oid
        folder=s.ROOT/'.local'/name
        marker=json.loads((folder/'database.json').read_text())
        assert marker.get('oid',marker.get('database_oid'))==oid
        result[name]={'oid':oid,'marker_sha256':s.file_sha(folder/'database.json'),
            'config_sha256':s.file_sha(folder/'odoo.conf'),'managed':s.public(now)}
    return result


def workbench_facts():
    results={}
    with s.connect(s.SOURCE) as conn,conn.cursor() as cur:
        for store in (1,3):
            cur.execute("SELECT m.id FROM account_move m WHERE m.state='posted' AND m.move_type='out_invoice' AND m.amount_residual>0 AND m.company_id=(SELECT company_id FROM ydental_access_store WHERE id=%s) AND EXISTS(SELECT 1 FROM ydental_settlement_source t WHERE t.ydental_invoice_id=m.id AND t.ydental_store_id=%s) ORDER BY invoice_date,id LIMIT 50",(store,store))
            invoices=[r[0] for r in cur.fetchall()]
            assert invoices==([] if store==1 else [5,6,8,9])
            cur.execute("SELECT f.id FROM ydental_treatment_fee f JOIN ydental_treatment_event e ON e.id=f.ydental_event_id WHERE f.ydental_store_id=%s AND e.state='confirmed' AND NOT EXISTS(SELECT 1 FROM ydental_settlement_source t WHERE t.ydental_fee_id=f.id)",(store,))
            assert cur.fetchall()==[]
            cur.execute("SELECT id FROM ydental_treatment_event WHERE ydental_store_id=%s AND state='pending'",(store,))
            assert cur.fetchall()==[]
            results[str(store)]={'invoice_ids':invoices,'source_view_ids':[],'pending_view_ids':[]}
        cur.execute('SELECT ydental_store_id,ydental_state FROM ydental_settlement_close WHERE id=63')
        assert cur.fetchall()==[(3,'confirmed')]
    return results


def authority_archive():
    results={}
    for n in (23,34,35):
        p=c.PRIVATE/f'issue{n}.json';i=json.loads(p.read_text())
        comments=json.loads((c.PRIVATE/f'comments{n}.json').read_text())
        assert len(comments)==i['comments']
        assert not any(x.get('minimized') for x in comments)
        results[str(n)]={'state':i['state'],'body_sha256':s.sha(i['body'].encode()),
            'api_sha256':s.file_sha(p),'comments':[{'id':x['id'],'updated_at':x['updated_at'],
                'body_sha256':s.sha(x['body'].encode())} for x in comments]}
    assert results['35']['state']=='open' and not results['35']['comments']
    assert results['34']['comments'][-1]['id']==c.AUTH
    return results


def main():
    product=c.authority()
    assert not s.TARGET_RUN.exists() and not (c.PRIVATE/'create-attempt.json').exists()
    with socket.socket() as sock: sock.bind(('127.0.0.1',s.PORT))
    names,active=s.identity();assert s.TARGET not in names and not active
    expected={'docs/evidence/s10-p0-04/blocked.json':'1738cbd133eda97234ab621f4bc622e5301b8cbaa9330a958e94e9d97b463e1a',
        'docs/evidence/s10-p0-04/business-before-after.json':'5b99aa655057a3e54c06aefbb17aa9d9e552cac4ea69940931412b96873c26a7'}
    assert {p:s.file_sha(s.ROOT/p) for p in expected}==expected
    source=c.capture(s.SOURCE,business=True);c.source_gate(source)
    old=json.loads((s.ROOT/'docs/evidence/s10-p0-04/business-before-after.json').read_text())
    assert source['all']['signatures']==old['after_all_643_table_signatures']
    assert source['managed']['tables']==old['after_265_managed_table_signatures']
    histories=history_gate();facts=workbench_facts()
    assert json.loads(json.dumps(c.load_capture(c.PRIVATE/'source-initial-readonly.json')))==json.loads(json.dumps(source))
    cli=json.loads(subprocess.check_output([str(c.PYTHON),'-B',str(s.ROOT/'scripts/s10_p0_06_cli_offline.py')],text=True))
    dom=json.loads(subprocess.check_output([str(c.PYTHON),'-B',str(s.ROOT/'scripts/s10_p0_06_dom_offline.py')],text=True))
    offline=json.loads(subprocess.check_output([str(c.PYTHON),'-B',str(s.ROOT/'scripts/s10_p0_06_offline.py')],text=True))
    assert cli['status']=='REAL_CLI_PARSER_PASS' and dom['status']=='SIMULATED_DOM_PASS' and offline['status']=='SIMULATED_PASS'
    assert offline['cases']['PASS']==offline['cases']['read_positive']=='SIMULATED_PASS'
    assert all(value=='FAIL_CLOSED' for key,value in offline['cases'].items() if key not in ('PASS','read_positive'))
    archive=authority_archive()
    data={'status':'PREFLIGHT_PASS','authorization_comment':c.AUTH,'head':s.HEAD,'core_head':s.CORE_HEAD,
        'branch':c.BRANCH,'source':{'name':s.SOURCE,'oid':s.SOURCE_OID,
            'config_sha256':s.SOURCE_CONFIG,'marker_sha256':s.SOURCE_MARKER,
            'filestore_manifest_sha256':s.SOURCE_MANIFEST,'schema':source['managed']['schema'],
            'public_table_count':643,'managed_table_count':265,'filestore_count':194,'attachment_pointers':1075,
            'module_count':702,'installed_count':92},
        'source_all_signatures':source['all']['signatures'],'source_tables':source['managed']['tables'],
        'source_business':source['managed']['business'],'historical_sources':histories,'authority_archive':archive,
        'workbench_facts':facts,'frozen_p004_files':expected,
        'allowlist':{'actors':{'6':'store1','14':'store3'},'invoice_view':{'actor':14,'store':3,
            'target_model':'account.move','targets':[5,6,8,9],'per_actual_GET':4,'max_GETs':2,'max_new_rows':8,
            'fields_template_audits':[2671,2672,2673,2674],'allowed_changed_fields':['id','create_date','write_date','ydental_target_id']},
            'user6_GETs_max':3,'user6_read_audits':0,'s01_total_new_max':15,'login_scope_switch_per_actor_max':3,
            'successful_unlock_audit':1,'close9_fields':['ydental_state','ydental_unlocked_by_id','ydental_unlock_reason','ydental_unlocked_at','write_uid','write_date'],
            'mutex':'only ID1 revision243->244','receipt':'only one new actor6/store1 unlock exact key/fingerprint/result; old rows exact',
            'mail_tracking_new_max':0,'device_log_new_max':2,'user_log_new_max':2,'access_session_new_max':2,
            'assets_new_max':10,'files_new_max':20,'asset_size_each_max':3000000,'orm_signal_max':3,
            'default_all_643_tables_exact':True,'native_finance_stock_exact':sorted(s.MONEY_TABLES)},
        'target':s.TARGET,'port':s.PORT,'target_absent':True,'port_free':True,
        'create_sql':f'CREATE DATABASE "{s.TARGET}" WITH TEMPLATE "{s.SOURCE}"',
        'http_argv':list(c.HTTP_ARGV),'browser_argv':list(c.BROWSER_ARGV),
        'scripts_sha256':{str(p.relative_to(s.ROOT)):s.file_sha(p) for p in c.SCRIPTS},
        'product_hashes':product,'offline':offline,'dom':dom,'cli':cli,
        'budgets':{'create':1,'odoo_http':1,'firefox':1,'user14_unlock9':1,'user6_unlock9':1,
            'user10_POST':0,'refund_reject_POST':0,'new_money_stock_close':0,'upgrade_init_install_prepare_shell':0,'sudo':0},
        'stop_conditions':['source/clone/permission/field drift','unknown response or commit','denial not authoritative',
            'unbound GET/audit','any disallowed table or field or request','no retry/new library'],
        'source_snapshot_sha256':s.file_sha(c.PRIVATE/'source-initial-readonly.json')}
    c.save_once(c.PREFLIGHT,data)
    print(json.dumps({'status':'PREFLIGHT_PASS','sha256':s.file_sha(c.PREFLIGHT),'offline_count':offline['count'],
                      'source_oid':s.SOURCE_OID,'target':s.TARGET,'port':s.PORT}))


if __name__=='__main__': main()

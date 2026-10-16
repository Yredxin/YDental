"""P008 formal immutable preflight: full read-only history, actual DOM/CLI/control simulation."""
import json
import socket
import subprocess
from pathlib import Path
import s10_p0_08_control as c
s=c.s

HISTORY={
 'ydental_s10_test_20261014020300_8b6c1d4e':(2056451,'.local/s10-p0-02/source-before.json',None),
 'ydental_s10_test_20261015_p002_6d84a2c1':(2100311,'.local/s10-p0-03/source-before.json','managed'),
 'ydental_s10_test_20261016_p003_75c1e9b2':(2100319,'.local/s10-p0-03/stopped-readonly.json','managed'),
 'ydental_s10_test_20261016_p004_9a6e37f2':(2100320,'.local/s10-p0-04/stopped-readonly.json','managed'),
 'ydental_s10_test_20261016_p006_4e8a91c7':(2100321,'.local/s10-p0-06/stopped-readonly.json','managed'),
 s.SOURCE:(s.SOURCE_OID,'.local/s10-p0-07-6206799419/stopped-readonly.json','managed')}


def history_gate():
    result={}
    for name,(oid,filename,key) in HISTORY.items():
        old=json.loads((s.ROOT/filename).read_text());old=old[key] if key else old
        now=s.snapshot(name)
        for field in ('database','oid','cluster','tables','schema','modules','views','view_rows','filestore','attachment_pointers'):
            assert now[field]==old[field],('HISTORY_DRIFT',name,field)
        assert now['oid']==oid
        folder=s.ROOT/'.local'/name
        marker=json.loads((folder/'database.json').read_text())
        assert marker.get('oid',marker.get('database_oid'))==oid
        result[name]={'oid':oid,'marker_sha256':s.file_sha(folder/'database.json'),
            'config_sha256':s.file_sha(folder/'odoo.conf'),'managed':s.public(now)}
    c.historical_activity_gate()
    return result


def authority_archive():
    result={}
    for n in (23,34,35):
        path=c.PRIVATE/f'issue{n}.json';issue=json.loads(path.read_text())
        rows=sum(json.loads((c.PRIVATE/f'comments{n}.json').read_text()),[]) if n!=35 else []
        assert issue['comments']==len(rows)
        assert not any(x.get('minimized') for x in rows)
        result[str(n)]={'state':issue['state'],'body_sha256':s.sha(issue['body'].encode()),
            'api_sha256':s.file_sha(path),'comments':[{'id':x['id'],'updated_at':x['updated_at'],
            'body_sha256':s.sha(x['body'].encode())} for x in rows]}
    assert result['35']['state']=='open' and not result['35']['comments']
    assert result['34']['comments'][-1]['id']==c.AUTH
    return result


def main():
    product=c.authority()
    assert not s.TARGET_RUN.exists() and not (c.PRIVATE/'create-attempt.json').exists()
    with socket.socket() as sock:sock.bind(('127.0.0.1',s.PORT))
    names,active=s.identity();assert s.TARGET not in names and not active
    expected={'docs/evidence/s10-p0-07/verification.json':'5118bb12bc712bc9a326b335066a2c057ae9e83936c43b7855adafcf00e45a1d',
        'docs/evidence/s10-p0-07/business-before-after.json':'63de2e86f97daf6ded2c9fb33e60135adb1e8431b7ccef727ab59b9bcefda4b9'}
    assert {p:s.file_sha(s.ROOT/p) for p in expected}==expected
    source=c.capture(s.SOURCE,business=True);c.source_gate(source)
    assert c.equivalent(source,c.load_capture(c.PRIVATE/'source-initial-readonly.json'))
    with s.connect(s.SOURCE) as conn,conn.cursor() as cur:
        cur.execute("SELECT model,res_id FROM ir_model_data WHERE module='ydental_settlement' AND name='ydental_settlement_mutex'")
        assert cur.fetchall()==[('ydental.settlement.mutex',1)]
    histories=history_gate();facts=c.workbench_facts(s.SOURCE)
    candidate=json.loads((c.PRIVATE/'preflight-candidate.json').read_text())
    for store,page in ((1,1),(1,2),(3,1)):
        assert c.refund_sql(s.SOURCE,store,page)==candidate['refund_pages'][f'{store}-{page}']
    assert facts==candidate['workbench_facts']
    selected=candidate['selection']['selected']
    assert selected=={'id':13,'state':'requested','store':1,'amount':'1.00','position':52,'page':2}
    assert candidate['refund_pages']['1-2']['rows'][1]==selected
    outcomes={}
    for kind in ('offline','dom_offline','cli_offline'):
        command=[str(c.PYTHON),'-B',str(s.ROOT/f'scripts/s10_p0_08_{kind}.py')]
        result=subprocess.run(command,capture_output=True,text=True)
        c.save_once(c.PRIVATE/f'formal-{kind}-execution.json',{'argv':command,'returncode':result.returncode,
            'stdout':result.stdout,'stderr':result.stderr})
        assert result.returncode==0,(kind,result.stderr[-500:])
        outcomes[kind]=json.loads(result.stdout)
    assert outcomes['offline']['status']=='SIMULATED_PASS'
    assert outcomes['dom_offline']['status']=='SIMULATED_DOM_PASS'
    assert outcomes['cli_offline']['status']=='REAL_CLI_PARSER_PASS'
    rows=source['all']['rows']
    data={'status':'PREFLIGHT_PASS','authorization_comment':c.AUTH,'previous_gpt_review':6207285901,
        'start_head':s.HEAD,'core_head':s.CORE_HEAD,'branch':c.BRANCH,
        'source':{'name':s.SOURCE,'oid':s.SOURCE_OID,'config_sha256':s.SOURCE_CONFIG,'marker_sha256':s.SOURCE_MARKER,
            'filestore_manifest_sha256':s.SOURCE_MANIFEST,'filestore_count':194,'attachment_pointers':1075,
            'public_table_count':643,'managed_table_count':265,'module_count':702,'installed_count':92,
            'schema':source['managed']['schema']},
        'native_contract':json.loads((c.PRIVATE/'native-contract.json').read_text()),
        'source_all_signatures':source['all']['signatures'],'source_tables':source['managed']['tables'],
        'source_business':source['managed']['business'],'source_snapshot_sha256':s.file_sha(c.PRIVATE/'source-initial-readonly.json'),
        'frozen_p007_files':expected,'historical_sources':histories,'authority_archive':authority_archive(),
        'selection':candidate['selection'],'refund_pages':candidate['refund_pages'],'workbench_facts':facts,
        'historical_mutex_revision':244,'historical_receipt_ids':[242,243],
        'allowlist':{'actors':{'6':{'store':1,'partner':7,'employee':2,'hr_version':2},
            '14':{'store':3,'partner':16,'employee':10,'hr_version':10}},
            'workbench_GETs':{'6':2,'14':1,'planned_total':3,'authorization_ceiling':3},
            'invoice_view':{'actor':14,'store':3,'model':'account.move','targets':[5,6,8,9],
                'per_GET':4,'max_new':4,'template_audit':rows['ydental_access_audit'][2671],
                'changed_fields':['id','create_date','write_date','ydental_target_id']},
            'source_view_new':0,'pending_event_view_new':0,'user6_read_audits':0,
            'S01_total_new_max':10,'login_login_scope_store_switch_per_actor':[1,1,1],
            'identity_audit_templates':{str(i):rows['ydental_access_audit'][i] for i in (2662,2663,2664,2668,2669,2670)},
            'identity_audit_changed_fields':['id','create_date','write_date','ydental_target_id'],
            'session_templates':[179,181],'session_new_max':2,'one_per_actor':True,
            'session_changed_fields':['id','ydental_key_hash','ydental_revision','ydental_store_id','create_date','write_date'],
            'device_templates':[3,5],'device_new_max':2,'device_fields':['id','session_identifier','user_agent','first_activity','last_activity'],
            'user_log_templates':[3,5],'user_log_new_max':2,'user_log_fields':['id','create_date','write_date'],
            'metadata_fields':{'res_users':['write_uid','write_date'],
                'res_partner':['tz','write_uid','write_date'],'hr_employee':['write_uid','write_date'],
                'hr_version':['last_modified_date','last_modified_uid','write_uid','write_date'],
                'resource_resource':['write_uid','write_date']},
            'mail_tracking_new_max':0,'assets_new_max':0,'files_new_max':0,'asset_size_each_max':3000000,
            'asset_template':1075,'asset_regex':c.ASSET_PATTERN.pattern,'asset_checksum_sha1_and_manifest_sha256':True,
            'asset_fields':['id','url','name','checksum','mimetype','file_size','write_date','create_date','store_fname','index_content'],
            'old_files_exact':True,'new_checklist_empty_only':True,'orm_signal_max':3,
            'all_receipts_mutex_refunds_closes_exact':True,'default_all_643_tables_exact':True,
            'native_account_stock_and_ydental_economy_exact':True},
        'target':s.TARGET,'port':s.PORT,'target_absent':True,'port_free':True,
        'create_sql':f'CREATE DATABASE "{s.TARGET}" WITH TEMPLATE "{s.SOURCE}"',
        'http_argv':list(c.HTTP_ARGV),'browser_argv':list(c.BROWSER_ARGV),
        'network_policy_sha256':s.file_sha(s.ROOT/'scripts/s08c_network_policy.py'),
        'scripts_sha256':{str(p.relative_to(s.ROOT)):s.file_sha(p) for p in c.SCRIPTS},
        'product_hashes':product,'offline':outcomes,
        'budgets':{'create':1,'odoo_http':1,'firefox':1,'workbench_GET':3,'planned_GET':3,
            'native_login_switch_POST':4,'settlement_POST':0,'operate_calls':0,'new_business_writes':0,
            'upgrade_init_install_prepare_shell':0,'sudo':0,'http_seconds':1200,'firefox_seconds':1200,'readiness_seconds':180},
        'STOP':['identity/source/history/clone drift','unknown response','wrong permission/DOM/SQL/audit/field',
            'any settlement POST or money/stock/business write','budget or native signal11','no retry or replacement database']}
    c.save_once(c.PREFLIGHT,data)
    print(json.dumps({'status':'PREFLIGHT_PASS','sha256':s.file_sha(c.PREFLIGHT),'selected':selected,
        'simulation_cases':outcomes['offline']['count'],'DOM_cases':outcomes['dom_offline']['count']}))


if __name__=='__main__':main()

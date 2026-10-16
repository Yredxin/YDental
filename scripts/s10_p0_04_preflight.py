"""P0-04 read-only three-source preflight. No CREATE, HTTP or Firefox."""
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

import s10_p0_02_snapshot as r3
import s10_p0_03_snapshot as p003
import s10_p0_04_snapshot as s
import s10_p0_04_control as c

os.umask(0o077)


def main():
    product_hashes=c.authority()
    assert not s.TARGET_RUN.exists()
    if c.PRIVATE.exists():
        assert (c.PRIVATE/'checkpoint.json').exists()
        assert not (c.PRIVATE/'create-attempt.json').exists()
    with socket.socket() as port:
        port.bind(('127.0.0.1',s.PORT))
    dbs,active=s.identity()
    assert s.TARGET not in dbs and not active
    r3_now=r3.snapshot(r3.SOURCE,business=True)
    p002_now=p003.snapshot(p003.SOURCE,business=True)
    source=c.capture(s.SOURCE,business=True)
    # The fixed P0-03 public and private snapshots are both checked before writing evidence.
    stopped=c.load_capture(c.ROOT/'.local/s10-p0-03/stopped-readonly.json')
    assert source['all']['signatures']==stopped['all']['signatures']
    assert {k:source['all']['rows'][k] for k in stopped['all']['rows']}==stopped['all']['rows']
    assert {k:v for k,v in source['managed'].items() if k!='business'}=={
        k:v for k,v in stopped['managed'].items() if k!='business'}
    b=source['managed']['business']
    grants=set(b['grants'])
    assert {(6,1,'settlement','write'),(6,1,'finance_approval','write'),
            (14,3,'settlement','write'),(14,3,'finance_approval','write')} <= grants
    assert not any(g[0]==10 and g[1]==1 for g in grants)
    assert not any(g[0]==14 and g[1]==1 for g in grants)
    assert b['close9']==['confirmed','1','5','2026-07-15','card','1','0.00','0.00','0.00']
    assert b['close9_latest']==9 and 9 in b['close_page2_ids']
    assert b['refund14'][:3]==['rejected','5','1'] and b['refund14'][4:]==[None,None]
    row=source['all']['rows']['ydental_settlement_refund'][14]
    assert row['ydental_state']=='rejected' and row['ydental_approver_id']==6
    assert row['ydental_native_payment_id'] is None and row['ydental_credit_note_id'] is None
    audits=source['all']['rows']['ydental_access_audit']
    assert audits[2661]['ydental_event']=='settlement.refund.reject'
    assert audits[2661]['ydental_result']=='accepted' and audits[2661]['ydental_user_id']==6
    receipts=source['all']['rows']['ydental_settlement_receipt']
    receipt=receipts[242]
    assert len(receipts)==242 and receipt['ydental_operation']=='refund_reject'
    assert receipt['ydental_actor_id']==6 and receipt['ydental_store_id']==1
    assert receipt['ydental_result']=={'refund_id':14,'state':'rejected',
                                      'actually_refunded':0,'credit_note_id':False}
    prior=hashlib.sha256(json.dumps(['refund_reject',1,{
        'refund_id':14,'reason':row['ydental_decision_reason']}],
        sort_keys=True,ensure_ascii=True).encode()).hexdigest()
    assert receipt['ydental_fingerprint']==prior
    assert source['all']['rows']['ydental_settlement_mutex'][1]['ydental_revision']==243
    with s.connect(s.SOURCE) as conn,conn.cursor() as cur:
        cur.execute("SELECT model,res_id FROM ir_model_data WHERE module='ydental_settlement' AND name='ydental_settlement_mutex'")
        assert cur.fetchall()==[('ydental.settlement.mutex',1)]
    conn.close()
    assert all(x['has_output_html'] for x in source['managed']['views'][
        'ydental_settlement.ydental_settlement_tokens']['languages'].values())
    assert len(source['all']['signatures'])==643 and len(source['managed']['tables'])==265
    assert source['managed']['attachment_pointers']==1075
    assert source['managed']['filestore']['count']==194
    assert len(source['managed']['modules'])==702
    assert sum(x['state']=='installed' for x in source['managed']['modules'].values())==92
    # Cross-check already sealed historical snapshots, without accessing any historical Web process.
    old_r3=json.loads((c.ROOT/'.local/s10-p0-02/source-before.json').read_text())
    assert r3_now['tables']==old_r3['tables'] and r3_now['filestore']==old_r3['filestore']
    old_p002=json.loads((c.ROOT/'.local/s10-p0-03/source-before.json').read_text())['managed']
    assert json.loads(json.dumps(p002_now,default=str))==old_p002
    cli=json.loads(subprocess.check_output([str(c.PYTHON),str(c.ROOT/'scripts/s10_p0_04_cli_offline.py')],text=True))
    offline=json.loads(subprocess.check_output([str(c.PYTHON),str(c.ROOT/'scripts/s10_p0_04_offline.py')],text=True))
    assert cli['status']=='REAL_CLI_PARSER_PASS' and offline['status']=='SIMULATED_PASS'
    assert offline['count']==41 and all(v=='FAIL_CLOSED' for k,v in offline['cases'].items() if k!='PASS')
    scripts={str(p.relative_to(c.ROOT)):s.file_sha(p) for p in c.SCRIPTS}
    data={'status':'PREFLIGHT_PASS','authorization_comment':c.AUTH,'head':s.HEAD,
        'core_head':s.CORE_HEAD,'branch':c.BRANCH,
        'source':{'name':s.SOURCE,'oid':s.SOURCE_OID,'marker_sha256':s.SOURCE_MARKER,
                  'config_sha256':s.SOURCE_CONFIG,'filestore_count':194,
                  'filestore_manifest_sha256':s.SOURCE_MANIFEST,'attachment_pointers':1075,
                  'public_table_count':643,'managed_table_count':265,'schema':source['managed']['schema'],
                  'module_count':702,'installed_module_count':92},
        'r3':{'name':r3.SOURCE,'oid':r3.SOURCE_OID,'marker_sha256':r3.SOURCE_MARKER,
              'config_sha256':r3.SOURCE_CONFIG,'filestore_manifest_sha256':r3.SOURCE_MANIFEST},
        'p002':{'name':p003.SOURCE,'oid':p003.SOURCE_OID,'marker_sha256':p003.SOURCE_MARKER,
                'config_sha256':p003.SOURCE_CONFIG,'filestore_manifest_sha256':p003.SOURCE_MANIFEST},
        'source_all_signatures':source['all']['signatures'],
        'source_tables':source['managed']['tables'],
        'source_business':b,
        'refund14':{'state':'rejected','approver_id':6,'audit_id':2661,
                    'native_outbound':False,'credit_note':False},
        'receipt242':{'operation':'refund_reject','actor_id':6,'store_id':1,
                      'key_sha256':s.sha(receipt['ydental_key'].encode()),
                      'fingerprint':receipt['ydental_fingerprint'],'result':receipt['ydental_result']},
        'mutex':{'xmlid':'ydental_settlement.ydental_settlement_mutex','id':1,'revision':243},
        'close9':{'state':'confirmed','store_id':1,'cashier_id':5,'date':'2026-07-15',
                  'channel':'card','cycle':1,'latest_cycle':True,'gross':0,'refunded':0,'pending':0},
        'actors':{'6':'store1 settlement+finance_approval write',
                  '10':'store1 no settlement/finance_approval',
                  '14':'store3 settlement+finance_approval write; no store1'},
        'allowlist':{'all_other_public_tables_exact':True,'refund14_and_all_other_refunds_exact':True,
            'close9_only':['ydental_state','ydental_unlocked_by_id','ydental_unlock_reason',
                            'ydental_unlocked_at','write_uid','write_date'],
            'mutex_id1_only':'revision 243 to 244 once, all other fields and rows exact',
            'receipt':'only one new unlock command matching actor6/store1/key/fingerprint/result; all old rows exact',
            'audit':'one accepted settlement.unlock actor6/store1/close9, optional correctly attributed denied',
            'assets_max':10,'new_files_max':20,'asset_size_each_max':3000000,
            'mail_tracking_max':4,'res_users_log_max':3,'res_device_log_max':3,
            's01_session_max':3,'s01_audit_max':11,'orm_signaling_default_max':3,
            'native_finance_stock_exact':sorted(s.MONEY_TABLES),
            'module_view_schema_acl_exact':True},
        'target':s.TARGET,'port':s.PORT,
        'create_sql':f'CREATE DATABASE "{s.TARGET}" WITH TEMPLATE "{s.SOURCE}"',
        'http_argv':list(c.HTTP_ARGV),'browser_argv':list(c.BROWSER_ARGV),
        'scripts_sha256':scripts,'product_hashes':product_hashes,
        'offline':offline,'cli':cli,
        'budgets':{'create':1,'http':1,'firefox':1,'unlock9':1,
                   'denied_unlock_posts':2,'refund_reject_posts':0,
                   'new_money_stock_writes':0,'odoo_upgrade_install_init_shell':0,'sudo':0},
        'stop_conditions':['source or clone drift','unknown response or commit',
                           'negative accepted or not authoritative','field gate failure',
                           'unknown funds, stock, ACL, module, asset, mail or audit writes']}
    c.save_once(c.PREFLIGHT,data)
    c.source_gate(r3_now,p002_now,source)
    print(json.dumps({'status':'PREFLIGHT_PASS','sha256':s.file_sha(c.PREFLIGHT),
        'source_oid':s.SOURCE_OID,'target':s.TARGET,'simulated_count':offline['count'],
        'all_tables':643},ensure_ascii=False))


if __name__=='__main__': main()

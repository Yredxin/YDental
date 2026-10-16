"""Post-STOP evidence projection from existing files only.

No DB, native service, browser, HTTP or business-action entrypoint. This file
was added after execution solely to preserve the blocked outcome and compare
already-captured snapshots. The five execution scripts stay frozen unchanged.
"""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

from lxml import html

import s10_p0_13_control as c


def safe_comment(value):
    body = value['body']
    return {'id': value.get('id'), 'url': value.get('html_url', value.get('url')),
            'characters': len(body), 'utf8_bytes': len(body.encode()),
            'body_sha256': c.sha(body.encode()), 'title': body.splitlines()[0]}


def main():
    c.verify_freeze()
    before = c.ro.read(c.PRIVATE / 'w5-private-rows.json')
    source_after = c.ro.read(c.PRIVATE / 'w5-after-private-rows.json')
    target_before = c.ro.read(c.PRIVATE / 'clone-before-http.json')
    target_after = c.ro.read(c.PRIVATE / 'target-after-rows.json')
    a, b = c.rows(before), c.rows(target_after)
    assert len(a) == len(b) == 643
    assert source_after['tables'] == target_before['tables'] == before['tables']
    changes = sorted(t for t in a if a[t] != b[t])
    assert changes == ['res_device_log', 'res_users_log', 'ydental_access_audit', 'ydental_access_session']
    plan = c.ro.read(c.OUT / 'execution-preflight.json')
    assert all(a[t] == b[t] for t in plan['locked_tables'])
    table_diffs = {t: {'before': before['signatures'][t], 'after': target_after['signatures'][t],
                       'exact_rows_equal': a[t] == b[t], 'locked': t in plan['locked_tables']} for t in a}
    c.save(c.OUT / 'all643-target-comparison.json', {'total_tables':643, 'unchanged_tables':639,
        'changed_tables':changes, 'comparison':table_diffs,'locked627_exact':True})
    added = {}
    for t in changes:
        old, new = {r['id']:r for r in a[t]}, {r['id']:r for r in b[t]}
        assert old.keys() <= new.keys() and all(new[i] == row for i,row in old.items())
        added[t] = [r for r in b[t] if r['id'] not in old]
    audits = [{k:r[k] for k in ('id','ydental_event','ydental_category','ydental_user_id','ydental_store_id',
        'ydental_source','ydental_target_model','ydental_target_id','ydental_result','create_uid','write_uid',
        'ydental_before','ydental_after','ydental_reason','create_date','write_date')} for r in added['ydental_access_audit']]
    assert all(r['ydental_event'] in ('login','login.scope','store.switch','clinical.view','source.view') for r in audits)
    assert all(not r['ydental_before'] and not r['ydental_after'] for r in audits if r['ydental_event'] != 'store.switch')
    old_session = next(r for r in a['ydental_access_session'] if r['ydental_user_id']==7)
    session = added['ydental_access_session'][0]
    session_diff = sorted(c.changed(old_session,session))
    expected_session_fields = {'id','ydental_key_hash','create_date','write_date'}
    extra_session = sorted(set(session_diff)-expected_session_fields)
    assert extra_session == ['write_uid'] and session['write_uid'] == 7
    events = {event:sum(r['ydental_event']==event for r in audits) for event in sorted({r['ydental_event'] for r in audits})}
    assert events == {'clinical.view':1,'login':1,'login.scope':1,'source.view':1,'store.switch':1}
    allowed_events = set(plan['whitelist']['audit']['allowed_events'])
    unexpected_events = sorted(set(events)-allowed_events)
    assert unexpected_events == ['source.view']
    # Reuse the unchanged frozen comparator, without any database connection.
    try:
        c.gate(target_after, 'login-view', {})
    except AssertionError as error:
        gate_result = {'status':'FAIL','exception_type':type(error).__name__,
                       'exception_message_sha256':c.sha(str(error).encode())}
    else:
        raise AssertionError('frozen_whitelist_unexpectedly_accepted')
    c.save(c.OUT / 'login-audit-field-review.json', {'status':'BLOCKED_FROZEN_WHITELIST',
        'comparison_mode':'offline only on actual captured target-after; no new SQL or relaxed rules',
        'frozen_comparator':gate_result,'old_rows_in_all4_changed_tables_unchanged':True,
        'new_row_counts':{t:len(rs) for t,rs in added.items()},'audits':audits,
        'audit_event_counts':events,'unallowlisted_events':unexpected_events,
        'session_template_id':old_session['id'],'session_new_id':session['id'],
        'session_template_write_uid':old_session['write_uid'],'session_new_write_uid':session['write_uid'],
        'session_template_different_fields':session_diff,'session_unallowlisted_different_fields':extra_session,
        'session_actual_actor_store_revision':[session['ydental_user_id'],session['ydental_store_id'],session['ydental_revision']],
        'posthoc_whitelist_relaxation':False,'scope_new_key_or_sid_published':False})
    raw_html = c.ro.read(c.PRIVATE / 'clinical-get-0.html.json')
    tree = html.fromstring(raw_html['body'])
    root = tree.xpath('//*[contains(concat(" ",normalize-space(@class)," ")," o_ydental_clinical ")]')[0]
    attributes = {k:v for k,v in root.attrib.items() if k.startswith('data-')}
    assert 'data-execution' not in attributes
    fields = {node.attrib['name']:node.text or '' for node in root.xpath('.//textarea[@name]')}
    content_equal = fields == {k:v for k,v in a['ydental_clinical_document'][0]['ydental_content'].items() if k!='teeth'}
    assert content_equal and not root.xpath('.//*[@id="tooth-summary"]/*')
    browser = c.ro.read(c.OUT / 'browser-result.json')
    requests = browser['requests'];responses = browser['responses']
    native_responses = [r for r in responses if r['method']=='GET' and r['path']=='/ydental/clinical']
    assert len(native_responses)==1 and native_responses[0]['status']==200
    http_log = (c.RUN / 'http.log').read_text()
    server_requests = [{'method':m.group(1),'path':m.group(2),'status':int(m.group(3))} for m in
        re.finditer(r'"(GET|POST) ([^ ?"]+)(?:[^\"]*)" (\d{3})',http_log)]
    server_clinical = [r for r in server_requests if r['method']=='GET' and r['path']=='/ydental/clinical']
    assert len(server_clinical)==1 and server_clinical[0]['status']==200
    c.save(c.OUT / 'native-dom-http-review.json', {'status':'BLOCKED_NATIVE_DOM_CONTRACT',
        'source':'saved actual native Firefox clinical HTTP200 HTML; offline parsing only, no new render or screenshot',
        'html_private_sha256':c.sha((c.PRIVATE/'clinical-get-0.html.json').read_bytes()),
        'root_data_attributes':attributes,'data_execution_attribute_present':False,
        'execution_expected_by_frozen_browser':'0','actual_js_dataset_execution':'undefined from absent attribute; original evaluated object was not saved',
        'initial_metadata_tuple_assertion':"(document,revision,version,state,execution,heartbeat,canHandover)==('1','1','2','pending','0','2','no')",
        'runtime_failure':'AssertionError with empty message; full traceback/evaluated DOM were not retained by frozen handler',
        'diagnosis_level':'saved HTML and unchanged JS establish execution-attribute incompatibility; not a recovered runtime traceback',
        'complete_original_text_equal':content_equal,'teeth_row_count':0,'version_rows':len(root.xpath('.//*[@id="version-history"]/li')),
        'route_counter_clinical_GET':browser['counts']['CLINICAL_GET'],'actual_clinical_GET':len(server_clinical),
        'independent_browser_response_clinical_GET':len(native_responses),
        'counter_mismatch':'redirect target absent from route-handler observations, but present in real response and native server log; original counter preserved',
        'server_requests':server_requests,'original_browser_result_unchanged':True,
        'screenshots':'NOT_CAPTURED; flow stopped before first screenshot','medical_text_published':False})
    assert a['ydental_clinical_document'] == b['ydental_clinical_document']
    assert a['ydental_clinical_version'] == b['ydental_clinical_version']
    doc=b['ydental_clinical_document'][0]
    actual=dict(browser['counts']);actual['CLINICAL_GET']=len(server_clinical)
    result=c.ro.read(c.OUT/'execution-result.json')
    assert result['actual_connections']=={'maintenance':1,'source-after':1,'source-before':1,'target-after':1,'target-before':1}
    assert result['odoo_returncode']==0 and result['firefox_engine_exits']==[{'exit_code':'0','signal':'null'}]
    c.save(c.OUT/'verification.json', {'authorization':c.ro.AUTH,'base':c.ro.BASE,'core':c.ro.CORE,
        'status':'S10_P0_13_BLOCKED_NATIVE_DOM_AND_LOGIN_AUDIT_CONTRACT','codex_self_test_only':True,
        'preflight_comment':6211482453,'preflight_rest_verbatim':True,
        'source_before_after643_exact':True,'source_before_backend':before['backend_pid'],'source_after_backend':source_after['backend_pid'],
        'source_before_closed_before_CREATE':c.ro.read(c.PRIVATE/'source-before-connection-closed.json')['utc_epoch'] < c.ro.read(c.PRIVATE/'create-intent.json')['utc_epoch'],
        'clone_initial643_exact':True,'clone_oid':target_before['oid'],'target639_tables_exact':True,
        'locked627_tables_exact':True,'all_old_rows_exact':True,'only_new_identity_and_view_audit_rows':True,
        'doc1_state':doc['state'],'doc1_version':doc['ydental_version'],'editor_empty':not doc['ydental_editor_id'],
        'old_versions1_2_full_rows_exact':True,'new_version3':'NOT_RUN','clinical_actions':'NOT_RUN',
        'frozen_login_whitelist_pass':False,'unallowlisted_audit':['source.view'],'session_template_field_mismatch':['write_uid'],
        'actual_browser_budget_reconciled_with_server':actual,'original_route_counter_clinical_GET':0,
        'actual_connections':result['actual_connections'],'CREATE':1,'ODOO_HTTP':1,
        'odoo_pid':result['odoo_pid'],'odoo_exit':result['odoo_returncode'],
        'firefox_engine_pids':result['firefox_engine_pids'],'firefox_engine_exits':result['firefox_engine_exits'],
        'controller_exit':0,'controller_catches_flow_failure':True,'zero_exit_does_not_mean_business_PASS':True,
        'new_Odoo_SIGSEGV_observed':False,'browser_pageerror_count':browser['page_errors_count'],
        'funds_stock_fee_write':0,'PDF':0,'historical_replay':0,'product_core_acl_old_evidence_issue_project_change':0,
        'SUDO_DIRECT_ORM_INSTALL_UPGRADE_SHELL_TEST':0,'source_write':0,'source_filestore_seal_unchanged':True,'target_filestore_unchanged':result['target_filestore_unchanged'],
        'no_database_or_native_operation_after_source_after':True,'scope':'one bounded attempt stopped; no retry or product change',
        'continue_blocks':['S10_STAGE','PRODUCTION','T12','NATIVE_SIGSEGV_UNKNOWN','W4_METADATA_STOP','W5_OLD_BROWSER_EXIT1_FINAL_AUDIT_NOT_RUN','SAME_SOURCE_ORIGINAL_PDF_UNAVAILABLE']})
    projections={}
    for n in (23,34,35):
        old=c.ro.read(c.PRIVATE/f'issue{n}.json');new=c.ro.read(c.PRIVATE/f'issue{n}-delivery.json')
        assert old['body']==new['body'] and new['state']=='open'
        projections[str(n)]=safe_comment(new)|{'state':new['state'],'comments':new['comments'],'issue_body_unchanged':True}
    old34=c.ro.read(c.PRIVATE/'comments34-connector.json');new34=c.ro.read(c.PRIVATE/'comments34-delivery.json')
    assert [x['id'] for x in new34]==[x['id'] for x in old34]+[6211482453]
    assert all(x['body']==y['body'] for x,y in zip(old34,new34))
    old23=c.ro.read(c.PRIVATE/'comments23-connector.json');new23=c.ro.read(c.PRIVATE/'comments23-delivery.json')
    assert [x['body'] for x in old23]==[x['body'] for x in new23]
    c.save(c.OUT/'github-delivery-read.json', {'captured_at':datetime.now(timezone.utc).isoformat(),
        'issues':projections,'comments23':[safe_comment(x) for x in new23],
        'comments34':[safe_comment(x) for x in new34],'only_new_comment_before_delivery':6211482453,
        'no_parallel_new_authorization_or_delivery':True,'project_mutations':0})
    c.save(c.OUT/'private-artifact-index.json',{'directory':'.local/s10-p0-13 (700)',
        'raw_files':{p.name:{'bytes':p.stat().st_size,'sha256':c.sha(p.read_bytes())} for p in sorted(c.PRIVATE.iterdir()) if p.is_file()},
        'run_files':{p.name:{'bytes':p.stat().st_size,'sha256':c.sha(p.read_bytes())} for p in sorted(c.RUN.iterdir()) if p.is_file()},
        'raw_contents_not_published':True,'privacy':'all raw rows, HTML, HTTP, passwords/cookies/tokens stay private'})
    print(json.dumps({'status':'BLOCKED','source643_unchanged':True,'target639_unchanged':True,
        'changed_tables':changes,'clinical_GET_actual':1,'clinical_POST':0,'audit_unallowlisted':unexpected_events,
        'session_template_write_uid':old_session['write_uid'],'session_new_write_uid':session['write_uid']}))


if __name__=='__main__':
    main()

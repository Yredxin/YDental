"""After-run evidence projection from saved files only; no native operation.

Execution scripts remain frozen. Raw rows, HTML/HTTP, credentials and images
stay private. This entrypoint cannot create a connection or browser/service.
"""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re

from lxml import html
import s10_p0_14_control as c


def main():
    c.verify_freeze()
    source=c.baseline();source_after=c.ro.read(c.PRIVATE/'w5-after-private-rows.json')
    clone=c.ro.read(c.PRIVATE/'clone-before-http.json');target=c.ro.read(c.PRIVATE/'target-after-rows.json')
    assert source['tables']==source_after['tables']==clone['tables']
    a,b=c.rows(source),c.rows(target)
    plan=c.ro.read(c.OUT/'execution-preflight.json')
    assert len(a)==len(b)==643
    changes=sorted(t for t in a if a[t]!=b[t])
    assert set(changes)=={'res_device_log','res_users_log','ydental_access_audit','ydental_access_session',
        'ydental_clinical_document','ydental_clinical_version',*c.FENCES}
    assert all(a[t]==b[t] for t in plan['locked_tables']) and len(plan['locked_tables'])==627
    c.save(c.OUT/'all643-target-comparison.json',{'total_tables':643,'unchanged_tables':633,'changed_tables':changes,
        'locked627_exact':True,'tables':{t:{'before':source['signatures'][t],'after':target['signatures'][t],
        'full_rows_equal':a[t]==b[t],'locked':t in plan['locked_tables']} for t in a}})
    frozen=c.gate(target,'final-view',c.ro.read(c.PRIVATE/'accepted-context.json'))
    assert frozen['PASS']
    def newrows(table):
        old={r['id']:r for r in a[table]};new={r['id']:r for r in b[table]}
        assert old.keys()<=new.keys() and all(old[i]==new[i] for i in old)
        return [r for r in b[table] if r['id'] not in old]
    versions=newrows('ydental_clinical_version');assert len(versions)==1
    version=versions[0];doc=b['ydental_clinical_document'][0]
    assert (doc['state'],doc['ydental_version'])==('confirmed',3)
    assert version['ydental_number']==3 and version['ydental_kind']=='confirm' and version['ydental_previous_id']==2 and version['ydental_author_id']==7
    assert version['ydental_content']==doc['ydental_content']==a['ydental_clinical_document'][0]['ydental_content']
    assert all(not doc[k] for k in c.EDITOR_FIELDS)
    content_sha=c.sha(json.dumps(doc['ydental_content'],ensure_ascii=False,sort_keys=True).encode())
    audits=newrows('ydental_access_audit')
    assert len(audits)==9 and [r['ydental_event'] for r in audits]==['login','login.scope','store.switch','clinical.view','source.view','clinical.edit_acquire','clinical.confirm','clinical.edit_release','clinical.view']
    session=newrows('ydental_access_session')[0];oldsession=next(r for r in a['ydental_access_session'] if r['ydental_user_id']==7)
    c.save(c.OUT/'document-audit-fields.json',{'frozen_final_full643_gate':'PASS','document':{'id':1,'patient':1,'store':1,'company':1,'state':doc['state'],'version':3,'author':doc['ydental_author_id'],'responsible':doc['ydental_responsible_id'],'content_sha256':content_sha,'content_full_equal':True,'editor_released':True,'saved_at':doc['ydental_saved_at']},
        'new_version':{k:version[k] for k in ['id','ydental_number','ydental_kind','ydental_author_id','ydental_previous_id','ydental_recorded_at','create_uid','write_uid']},
        'old_versions1_2_full_rows_exact':True,'new_version_content_sha256':content_sha,'native_new_key_sha256':c.sha(version['ydental_request_key'].encode()),
        'new_session':{'id':session['id'],'actor':session['ydental_user_id'],'store':session['ydental_store_id'],'revision':session['ydental_revision'],'create_uid':session['create_uid'],'write_uid':session['write_uid'],'template_id':oldsession['id'],'template_write_uid':oldsession['write_uid'],'different_template_fields':sorted(c.changed(oldsession,session))},
        'audits':[{k:r[k] for k in ['id','ydental_event','ydental_category','ydental_user_id','ydental_store_id','ydental_source','ydental_target_model','ydental_target_id','ydental_result','ydental_reason','ydental_before','ydental_after','create_uid','write_uid','create_date','write_date']} for r in audits],
        'source_view_initial_GET':1,'source_view_final_GET':0,'all_old_audit_session_device_login_rows_exact':True,
        'fences':{t:{'before':a[t][0]['ydental_revision'],'after':b[t][0]['ydental_revision'],'only_changed_field':'ydental_revision'} for t in c.FENCES},'orm_signaling_append_actual':len(b['orm_signaling_default'])-len(a['orm_signaling_default'])})
    doms={}
    for num in (1,2):
        raw=c.ro.read(c.PRIVATE/f'clinical-get-{num}.html.json');tree=html.fromstring(raw['body'])
        root=tree.xpath('//*[contains(concat(" ",normalize-space(@class)," ")," o_ydental_clinical ")]')[0]
        attrs={k:v for k,v in root.attrib.items() if k.startswith('data-')}
        assert 'data-execution' not in attrs
        expected_state,expected_version=('pending',2) if num==1 else ('confirmed',3)
        assert attrs['data-state']==expected_state and attrs['data-version']==str(expected_version)
        fields={r.attrib['name']:r.text or '' for r in root.xpath('.//textarea[@name]')}
        assert fields=={k:v for k,v in doc['ydental_content'].items() if k!='teeth'}
        doms[str(num)]={'status':raw['status'],'metadata':attrs,'content_equal':True,'version_rows':len(root.xpath('.//*[@id="version-history"]/li')),
            'pending_rows':len(root.xpath('.//table[last()]/tbody/tr')),'HTML_private_file_sha256':c.sha((c.PRIVATE/f'clinical-get-{num}.html.json').read_bytes())}
    screenshots=[{'name':p.name,'bytes':p.stat().st_size,'sha256':c.sha(p.read_bytes()),'visually_reviewed':True} for p in sorted(c.PRIVATE.glob('*.png'))]
    assert len(screenshots)==5
    c.save(c.OUT/'native-dom-visual-review.json',{'real_saved_HTML':doms,'screenshots':screenshots,
        'visual_result':'5 actual native screenshots reviewed; final confirmed3/three authored versions/empty pending list/read-only released editor; transient pre-navigation header/history retain old page while server-version is3',
        'no_DOM_attribute_injection':True,'no_image_upload_to_GitHub':True,'UI_language_observed':'English; no new translation/full language acceptance claimed'})
    intents={op:c.ro.read(c.PRIVATE/f'intent-{op}.json')['utc'] for op in ['native-login','acquire','confirm','release']}
    c.save(c.OUT/'native-action-times.json',{'post_intent_UTC':intents,
        'acquire_intent_to_confirm_intent_seconds':(datetime.fromisoformat(intents['confirm'])-datetime.fromisoformat(intents['acquire'])).total_seconds(),
        'confirm_to_release_intent_seconds':(datetime.fromisoformat(intents['release'])-datetime.fromisoformat(intents['confirm'])).total_seconds(),
        'heartbeat_actual_POST':0,'interval_seconds_unchanged':2,'note':'intent includes readonly gate delay; native saving stays true during confirm/release; timing alone is not heartbeat proof, real HTTP budget is'})
    log=(c.PRIVATE/'execution.log').read_text()
    diagnostics=[s for s in log.splitlines() if any(k in s for k in ['NS_ERROR_ABORT','NS_ERROR_FAILURE','error in channel'])]
    c.save(c.OUT/'browser-engine-diagnostics.json',{'stderr_line_count':len(diagnostics),'line_sha256':[c.sha(s.encode()) for s in diagnostics],
        'label_occurrences':{k:log.count(k) for k in ['NS_ERROR_ABORT','NS_ERROR_FAILURE','error in channel']},
        'root_cause':'UNKNOWN; retained engine diagnostics, distinct from zero business-page pageerror and validated native responses',
        'not_claimed_clean_browser_or_production_stability':True})
    result=c.ro.read(c.OUT/'execution-result.json');browser=c.ro.read(c.OUT/'browser-result.json');http=c.ro.read(c.OUT/'http-reconciliation.json')
    assert result['status']=='SCOPED_CODEX_SELF_TEST_COMPLETE_PENDING_GPT' and http['all_equal']
    assert browser['counts']=={'ACQUIRE':1,'CLINICAL_GET':2,'CONFIRM':1,'FIREFOX_LAUNCH':1,'HEARTBEAT':0,'NATIVE_LOGIN_POST':1,'OTHER_POST':0,'PDF':0,'RELEASE':1,'STORE_SWITCH_POST':0}
    assert result['actual_connections']=={'maintenance':1,'source-after':1,'source-before':1,'target-after':1,'target-before':1}
    assert result['odoo_returncode']==0 and result['firefox_engine_exits']==[{'exit_code':'0','signal':'null'}]
    c.save(c.OUT/'verification.json',{'authorization':c.ro.AUTH,'base':c.ro.BASE,'core':c.ro.CORE,'status':'SCOPED_CODEX_SELF_TEST_COMPLETE_PENDING_GPT',
        'requested_GPT_scope_only':'S10_P0_14_W5_DOC1_NATIVE_CONFIRM_SOURCE_BEFORE_AFTER_AND_MONEY_STOCK_ZERO_SCOPED_TECH_PASS',
        'not_GPT_PASS_or_S10_stage_PASS':True,'preflight_comment':6212387399,'preflight_REST_verbatim':True,
        'source_before_backend':source['backend_pid'],'source_after_backend':source_after['backend_pid'],'source_backends_distinct':source['backend_pid']!=source_after['backend_pid'],
        'source_before_closed_before_CREATE':c.ro.read(c.PRIVATE/'source-before-connection-closed.json')['utc_epoch']<c.ro.read(c.PRIVATE/'create-intent.json')['utc_epoch'],
        'source_before_after643_exact':True,'clone_initial643_exact':True,'clone_oid':clone['oid'],'clone_source_oid':c.ro.OID,
        'target_before_after643_compared':True,'target633_tables_full_equal':True,'locked627_full_equal':True,'exact_whitelist_PASS':True,
        'new_versions':1,'doc_state':'confirmed','doc_version':3,'editor_released':True,'complete_original_content_equal':True,'old_v1_v2_full_equal':True,
        'counts':browser['counts'],'actual_connections':result['actual_connections'],'CREATE':1,'HTTP':1,'network_response_server_GET_POST_equal':True,
        'pageerror_count':browser['page_errors_count'],'engine_stderr_unknown_diagnostics_preserved':True,
        'odoo_PID':result['odoo_pid'],'odoo_exit':result['odoo_returncode'],'firefox_PIDs':result['firefox_engine_pids'],'firefox_exits':result['firefox_engine_exits'],
        'funds_fee_stock_changes':0,'attachments_filestore_changes':0,'historical_transaction_replay':0,'P013_clone_touched':False,
        'product_core_ACL_AGENTS_historical_evidence_issue_project_changes':0,'executor_sudo_directORM_shell_upgrade_install_init_test':0,
        'no_DB_or_native_operation_after_source_after':True,'S10_STAGE_PRODUCTION_T12':'BLOCKED','NATIVE_SIGSEGV_ROOT_CAUSE':'UNKNOWN',
        'continuing_blocks':['W4_METADATA_STOP','W5_OLD_BROWSER_EXIT1_FINAL_AUDIT_NOT_RUN','SAME_SOURCE_ORIGINAL_PDF_UNAVAILABLE','FORMAL_ACCOUNT_TAX_CURRENCY_PAYMENT_POLICY_UNAPPROVED']})
    c.save(c.OUT/'private-artifact-index.json',{'directory':'.local/s10-p0-14 (700)',
        'raw_files':{p.name:{'bytes':p.stat().st_size,'sha256':c.sha(p.read_bytes())} for p in sorted(c.PRIVATE.iterdir()) if p.is_file()},
        'run_files':{p.name:{'bytes':p.stat().st_size,'sha256':c.sha(p.read_bytes())} for p in sorted(c.RUN.iterdir()) if p.is_file()},
        'raw_medical_text_credentials_HTTP_HTML_screenshots_not_published':True})
    print(json.dumps({'status':'SCOPED_CODEX_SELF_TEST_COMPLETE_PENDING_GPT','source643_equal':True,'target633_equal':True,'changed_tables':changes,'document':'confirmed3','audits':len(audits)}))


if __name__=='__main__':
    main()

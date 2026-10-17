"""File-only preparation: deterministic metadata negatives and full execution freeze."""
import ast
from copy import deepcopy
from datetime import datetime, timezone
import json
import re
import shutil
from lxml import etree
import s10_p0_18_contract as c

def main():
    c.repo_gate();seal=c.seal()
    assert not c.RUN.exists() and not (c.PRIVATE/'execution-intent.json').exists()
    assert shutil.which('wkhtmltopdf')=='/usr/local/bin/wkhtmltopdf','FIXED_RENDERER_PATH'
    idx=c.read(c.ROOT/'docs/evidence/s10-p0-17/sha256-index.json')
    checks=[]
    for p,e in idx['files'].items():
        data=(c.ROOT/p).read_bytes()
        assert c.sha(data)==e['sha256'] and len(data)==e['bytes'] and data==c.git('show',c.BASE+':'+p)
    assert len(idx['files'])==18
    assert c.sha((c.ROOT/'docs/evidence/s10-p0-17/sha256-index.json').read_bytes())=='e1082ddc013e0708363791d6a88ecc8e19cab9e2c2db8c115e4783c8dd1f3598'
    assert c.git('rev-parse',c.BASE+':docs/evidence/s10-p0-17/sha256-index.json').decode().strip()=='11becf8361bf8e38096e6c4e51398afd35838adb'
    checks.append('18_fixed_file_SHAs_and_fixed_index_object_no_old_test_rerun')
    metadata=c.old_metadata()
    old=c.read(c.ROOT/'.local/s10-p0-14/w5-private-rows.json')['tables']
    before={t:[json.loads(r) for r in rows] for t,rows in old.items()}
    assert len(before)==643
    after=deepcopy(before)
    for name,(model,table,ident,xid) in c.IDS.items():
        r=c.row_map(after[table])[ident]
        r.update(write_uid=1,write_date='2026-10-17T02:00:00')
        if table=='ir_ui_view':
            r['arch_prev']=r['arch_db']['en_US']
            r['arch_db']={lang:etree.tostring(c.template(name),encoding='unicode') for lang in r['arch_db']}
            r['arch_fs']=c.XML;r['arch_updated']=False
    c.metadata_gate(before,after);checks.append('positive_exact5_metadata_fixture')
    def reject(label,mutate):
        fixture=deepcopy(after);mutate(fixture)
        try:c.metadata_gate(before,fixture)
        except AssertionError:checks.append(label)
        else:raise AssertionError('UNSAFE_COMPARATOR:'+label)
    reject('reject_account_balance',lambda t:c.row_map(t['account_move'])[1].update(amount_residual=1))
    reject('reject_grant_change',lambda t:t['ydental_access_grant'][0].update(ydental_level='none'))
    reject('reject_unrelated_view',lambda t:next(r for r in t['ir_ui_view'] if r['id'] not in c.VIEWS).update(write_uid=999))
    reject('reject_menu_action_change',lambda t:c.row_map(t['ir_ui_menu'])[320].update(action='ir.actions.act_url,999'))
    reject('reject_module_state',lambda t:t['ir_module_module'][0].update(state='to upgrade'))
    reject('reject_xmlid_remap',lambda t:c.row_map(t['ir_model_data'])[51388].update(res_id=1))
    reject('reject_main_old_arch',lambda t:c.row_map(t['ir_ui_view'])[1599].update(arch_db=c.row_map(before['ir_ui_view'])[1599]['arch_db']))
    reject('reject_language_key_widening',lambda t:c.row_map(t['ir_ui_view'])[1599]['arch_db'].update(fr_FR='bad'))
    corefiles=['odoo/init.py','odoo/cli/command.py','odoo/tools/convert.py','odoo/addons/base/models/ir_ui_view.py',
        'odoo/addons/base/models/ir_ui_menu.py','odoo/addons/base/models/ir_model.py','odoo/orm/registry.py',
        'odoo/orm/environments.py','odoo/sql_db.py','odoo/addons/base/models/res_users.py',
        'odoo/addons/base/models/res_device.py','odoo/addons/base/models/assetsbundle.py','addons/web/controllers/home.py']
    sources=[c.XML,'ydental_settlement/controllers/settlement.py','ydental_settlement/models/ydental_settlement_service.py',
        'ydental_settlement/models/report_ydental_settlement_pdf.py','ydental_settlement/report/ydental_settlement_templates.xml',
        'ydental_access/controllers/access.py','ydental_access/models/ydental_access_service.py','ydental_access/models/res_users.py',
        'ydental_access/models/ir_http.py','ydental_supply/models/ydental_access_service.py','ydental_access_test/models/ydental_access_service.py',
        'ydental_patient/models/ydental_patient_service.py','scripts/s10_e2e_w5_browser.py',
        'docs/evidence/s10-p0-16/readonly-result.json','docs/evidence/s10-p0-11/read-only-sql.json']
    hashes={}
    for p in sources:
        data=(c.ROOT/p).read_bytes();assert data==c.git('show',c.BASE+':'+p);hashes[p]=c.sha(data)
    for p in corefiles:
        data=(c.CORE_ROOT/p).read_bytes();assert data==c.git('show',c.CORE+':'+p,cwd=c.CORE_ROOT);hashes['../'+p]=c.sha(data)
    converter=(c.CORE_ROOT/'odoo/tools/convert.py').read_text()
    node=next(n for n in ast.parse(converter).body if isinstance(n,ast.FunctionDef) and n.name=='convert_file')
    assert [a.arg for a in node.args.args][:4]==['env','module','filename','idref']
    checks.append('fixed_convert_file_actual_env_module_filename_explicit_idref_mode_update')
    assert set(c.IDS)==set(etree.fromstring((c.ROOT/c.XML).read_bytes()).xpath('./*/@id'))
    checks.append('exact_existing_XMLID_set5_no_schema_or_report_load')
    assert len(c.table_sql())==643 and all(q.startswith('SELECT ') for q in c.table_sql().values())
    checks.append('all643_literal_READONLY_SELECTs')
    import s10_p0_18_browser as browser
    browser.login_credentials(before)
    checks.append('existing_private_user5_credential_matches_saved_synthetic_hash_no_password_reset')
    for p in sorted(c.ROOT.glob('scripts/s10_p0_18_*.py')):
        compile(ast.parse(p.read_text()),str(p),'exec');hashes[str(p.relative_to(c.ROOT))]=c.sha(p.read_bytes())
    private_deps=['.local/s10-p0-14/w5-private-rows.json','.local/s10-p0-16/projections.json',
                  '.local/ydental_s10_test_20261015060000_b6c7d8e9/fixture.json',
                  '.local/s00-b-deps/browser-fonts.conf','.local/s00-b-deps/verify-lib/pymupdf/__init__.py',
                  '.local/s00-b-deps/verify-lib/pymupdf/_mupdf.so','.local/s00-b-deps/verify-lib/playwright/async_api/_generated.py']
    hashes.update({p:c.sha((c.ROOT/p).read_bytes()) for p in private_deps})
    c.save(c.OUT/'metadata-contract.json',{'fixed_XML':c.XML,'old5':metadata,
        'expected_arch_structures':{n:norm for n in c.IDS if c.IDS[n][1]=='ir_ui_view' for norm in [c.norm(c.template(n))]},
        'allowed_columns':{'ir_ui_view':sorted(c.VIEW_FIELDS),'ir_ui_menu':sorted(c.TECH_FIELDS),'ir_act_url':sorted(c.TECH_FIELDS),'ir_model_data':sorted(c.TECH_FIELDS)},
        'native_signaling':{'orm_signaling_default':1,'orm_signaling_templates':1},
        'other_metadata_business_language_group_relation_schema_report_fields':'EXACT_UNCHANGED',
        'main_view_delta':'Only P017 settled-bills plus fixed converter/arch inverse serialization; both en_US and zh_CN structural equality required',
        'no_old_view_customization_or_COW':True})
    c.save(c.OUT/'sql-contract.json',{'schema':c.schema(),'table_queries':c.table_sql(),
        'identity':c.IDENTITY_SQL,'source_active':c.ACTIVE_SQL,'catalog':c.CATALOG_SQL,
        'first_statements':['SHOW transaction_read_only','SHOW transaction_isolation'],
        'maintenance':['SELECT oid,datname FROM pg_database ORDER BY oid','SELECT system_identifier::text FROM pg_control_system()',
            'SELECT pid FROM pg_stat_activity WHERE datname=%s','CREATE DATABASE "'+c.NAME+'" WITH TEMPLATE "'+c.SOURCE+'"','SELECT oid FROM pg_database WHERE datname=%s'],
        'source_max_statements_per_connection':648,'target_max_statements_per_connection':647,
        'read_only':'READ ONLY / REPEATABLE READ; ROLLBACK and CLOSE; no retained transaction',
        'source_expected_all643':'P016 readonly-result sealed signatures; no P016 qualification script executed'})
    c.save(c.OUT/'offline-result.json',{'status':'PURE_FILE_PREFLIGHT_PASS','checks':checks,'count':len(checks),'exit_code':0,'all_runtime_budgets':0,
        'initial_inspection_failures':['system python lacks lxml; used existing target3.12.15 venv','pdftotext/pdfinfo absent from PATH; freeze existing PyMuPDF pure-file parser/rasterizer instead, no installation','first preflight exit1: assumed all helper views had zh_CN; exact saved row languages used instead, no runtime operation','second preflight exit1: negative fixture wrote existing write_uid1 and did not mutate; changed fixture to999 to exercise actual rejection'],
        'not_Odoo_PDF_or_UI_execution':True})
    for p in sorted(c.OUT.glob('*.json')):hashes[str(p.relative_to(c.ROOT))]=c.sha(p.read_bytes())
    c.save(c.OUT/'execution-freeze.json',{'authorization':c.AUTH,'base':c.BASE,'core':c.CORE,'branch':c.BRANCH,
        'source':{'name':c.SOURCE,'oid':c.SOURCE_OID,'cluster':c.CLUSTER,'seal':seal},
        'target':{'name':c.NAME,'port':c.PORT,'directory':str(c.RUN),'OID':'Only new CREATE result; distinct from catalog all existing OIDs; immutable marker'},
        'file_sha256':hashes,'maximum_budget':c.BUDGET,
        'argv':{'executor':[str(c.PYTHON),str(c.ROOT/'scripts/s10_p0_18_control.py')],
            'metadata':[str(c.PYTHON),str(c.ROOT/'scripts/s10_p0_18_metadata.py')],
            'http':[str(c.PYTHON),str(c.CORE_ROOT/'odoo-bin'),'-c',str(c.RUN/'odoo.conf')],
            'browser':[str(c.PYTHON),str(c.ROOT/'scripts/s10_p0_18_browser.py')]},
        'native_environment':{'PYTHONFAULTHANDLER':'1','PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(c.ROOT/'.local/s04-deps'),'FONTCONFIG_FILE':str(c.ROOT/'.local/s00-b-deps/browser-fonts.conf'),'connection_logging':'odoo.sql_db.connection:DEBUG; no core/driver hooks or monkey patches'},
        'HTTP_exact_routes':{'GET /web/login?redirect=/ydental/settlement':1,'POST /web/login':1,
            'GET /ydental/settlement (native login redirect)':1,'GET /ydental/settlement?patient_id=1 (native filter form)':1,
            'GET /ydental/settlement/pdf/bill/1 (one real link click)':1,
            'GET /website/translations?hash=&lang=zh_CN':1,
            'GET existing source /web/assets/ URLs; no query':100,'other':0},
        'audit_exact6':{'login':1,'login.scope':1,'store.switch':1,'settlement.invoice_view account.move1':2,'settlement.report_download account.move1 PDF_SHA':1},
        'audit_binding':'actor/create_uid/write_uid5; scope store1/revision1; login no store; login.scope and store.switch new native session; settlement category/source unchanged; old rows exact',
        'web_identity_fields':{'res_users5,res_partner6,hr_employee1,resource_resource1':['write_date','write_uid5'],
            'hr_version1':['write_date','write_uid5','last_modified_date','last_modified_uid5'],
            'res_users_log':'append1 uid5 dates equal','res_device_log':'append1 native SID prefix,Firefox,127.0.0.1,no geo/revoked,raw-SQL technical nulls',
            'ydental_access_session':'append1 uid5/store1/revision1 create/write5 SID hash',
            'orm_signaling_default':'append<=1 id/date only after Web'},
        'assets_append_only':{'maximum':5,'model':'ir.attachment','URL':'/web/assets/<existing basename version>','MIMEs':c.ASSETS,
            'actor':1,'res_model':'ir.ui.view','res_id':0,'public':True,'type':'binary','file_size_max':5000000,
            'nonempty':['store_fname','checksum'],'empty':['res_field','access_token','original_id','description','db_datas'],
            'original_rows_and_files':'all unchanged; no deletion/replacement; no patient/report attachments'},
        'stop':'Any identity/precision/budget/assertion/crash/unknown request fails STOP; no CREATE/import/login/click retry; only bounded final source/target readonly audits and stop own processes',
        'PDF':'one download, %PDF,<=10MB/20pages, response SHA=bytes SHA; PyMuPDF text+rasters; actual human image inspection required; report_pdf_no_attachment retained',
        'source_connection_order':'source-before rollback/close BEFORE maintenance/CREATE; source-after only after clone stopped',
        'clone_connections':'Three independent READONLY/RR: preimport; postimport/preWeb; after browser stopped; native backend-create logs separate',
        'protected_libraries_and_economics':'Every one of643 tables compared; no economic/clinical/permission fields exempt; only exact5 metadata then exact Web fields above',
        'no_new_product_or_old_evidence_changes':True})
    print(json.dumps({'checks':len(checks),'exit_code':0,'runtime_budget_used':0,'freeze_sha256':c.sha((c.OUT/'execution-freeze.json').read_bytes())}))

if __name__=='__main__':
    main()

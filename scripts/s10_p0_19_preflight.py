"""Pure-file tests of the actual P0-19 comparators and transaction wrapper."""
import ast
from collections import Counter
from copy import deepcopy
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import shutil
from lxml import etree
import s10_p0_19_contract as c

def subset(s,tables=(),projection=False):
    result=dict(s);result['tables']=dict(s['tables'])
    for t in tables:result['tables'][t]=deepcopy(s['tables'][t])
    if projection:
        result['action_projection']=deepcopy(s['action_projection'])
        result['action_only']=deepcopy(s['action_only'])
    return result

def project(s):
    """Fixture identities only: SQL tableoid is never fabricated at runtime."""
    fields=c.schema()['ir_actions']
    records=deepcopy(s.get('action_only',[]))
    for number,table in enumerate(c.ACTION_CHILDREN,101):
        records += [{'schema':'public','physical_table':table,'table_oid':number,'id':r['id'],
                     'row':{k:deepcopy(r[k]) for k in fields}} for r in s['tables'][table]]
    s['action_projection']=sorted(records,key=lambda r:(r['schema'],r['physical_table'],r['id'],c.canonical(r)))
    s['tables']['ir_actions']=sorted([deepcopy(r['row']) for r in records],key=lambda r:(r['id'],c.canonical(r)))
    return s

def fixture(history):
    tables={t:[] for t in c.schema()}
    for t in ('ir_actions',*c.ACTION_CHILDREN):tables[t]=deepcopy(history['tables'][t])
    for t,ids in {'ir_ui_view':c.VIEWS,'ir_ui_menu':{320},'ir_model_data':{v[3] for v in c.IDS.values()}}.items():
        selected=[r for r in history['tables'][t] if r['id'] in ids]
        selected.append(next(r for r in history['tables'][t] if r['id'] not in ids))
        tables[t]=deepcopy(selected)
    tables['account_move']=[deepcopy(c.row_map(history['tables']['account_move'])[1])]
    tables['ir_module_module']=[deepcopy(next(r for r in history['tables']['ir_module_module'] if r['name']=='ydental_settlement'))]
    tables['ydental_access_grant']=[deepcopy(history['tables']['ydental_access_grant'][0])]
    fields=c.schema()['ir_actions']
    children=Counter(c.canonical({k:r[k] for k in fields}) for t in c.ACTION_CHILDREN for r in tables[t])
    assert children==Counter(map(c.canonical,tables['ir_actions'])),'HISTORICAL_ACTION_PHYSICAL_SOURCE_AMBIGUOUS'
    before={'database':'STATIC_FILE_FIXTURE_NOT_NATIVE_SQL','tables':tables,'action_only':[],
        'action_inherits':[['public','ir_actions','public',t,1] for t in c.ACTION_CHILDREN]}
    project(before)
    good=subset(before,('ir_act_url','ir_ui_menu','ir_ui_view'),True)
    for name,(_,table,ident,_) in c.IDS.items():
        row=c.row_map(good['tables'][table])[ident]
        row.update(write_uid=1,write_date='2026-10-17T03:00:00')
        if table=='ir_ui_view':
            row['arch_prev']=row['arch_db']['en_US']
            row['arch_db']={lang:etree.tostring(c.template(name),encoding='unicode') for lang in row['arch_db']}
            row.update(arch_fs=c.XML,arch_updated=False)
    return before,project(good)

class FileCursor:
    """A pure-file fixture ledger, not an Odoo cursor or an ORM adapter."""
    def __init__(self,private,out,unknown=False):
        self.private=private;self.out=out;self.unknown=unknown
        self.commits=0;self.rollbacks=0;self.closes=0
    def commit(self):
        assert (self.private/'metadata-precommit-before.json').exists()
        assert (self.private/'metadata-precommit-after.json').exists()
        assert (self.private/'metadata-precommit-full-diff.json').exists()
        assert c.read(self.out/'metadata-precommit-decision.json')['PASS']
        self.commits+=1
        if self.unknown:raise OSError('FIXTURE_COMMIT_UNKNOWN')
    def rollback(self):self.rollbacks+=1
    def close(self):self.closes+=1

def tests(history,work,checks):
    before,good=fixture(history)
    assert len(before['tables'])==643 and len(before['action_projection'])==571
    c.metadata_gate(before,good);checks.append('actual_comparator_accepts_child571_technical_write_and_consistent_parent')
    def reject(name,mutator,tables=(),projection=False):
        s=subset(good,tables,projection)
        mutator(s)
        try:c.metadata_gate(before,s)
        except AssertionError:checks.append(name)
        else:raise AssertionError('COMPARATOR_FAILED_TO_REJECT:'+name)
    def inconsistent(s):
        c.row_map(s['tables']['ir_actions'])[571]['write_date']='mismatch'
        next(r for r in s['action_projection'] if (r['physical_table'],r['id'])==('ir_act_url',571))['row']['write_date']='mismatch'
    reject('reject_parent_child_shared_field_inconsistency',inconsistent,('ir_actions',),True)
    for field,value in [('url','/wrong'),('name',{'en_US':'wrong'}),('type','ir.actions.act_window')]:
        def mutate(s,field=field,value=value):
            c.row_map(s['tables']['ir_act_url'])[571][field]=value;project(s)
        reject('reject_action571_'+field,mutate,('ir_act_url',),True)
    def other_action(s):s['tables']['ir_act_window'][0]['write_date']='wrong';project(s)
    reject('reject_other_physical_action_technical_write',other_action,('ir_act_window',),True)
    reject('reject_duplicate_physical_key',lambda s:s['action_projection'].append(deepcopy(s['action_projection'][0])),projection=True)
    reject('reject_logical_parent_omission',lambda s:s['tables']['ir_actions'].pop(),('ir_actions',))
    reject('reject_noninherited_duplicate_id',lambda s:s['tables']['ir_act_url'].append(deepcopy(s['tables']['ir_act_url'][0])),('ir_act_url',))
    reject('reject_extra_view',lambda s:next(r for r in s['tables']['ir_ui_view'] if r['id'] not in c.VIEWS).update(write_date='wrong'),('ir_ui_view',))
    reject('reject_extra_XMLID',lambda s:next(r for r in s['tables']['ir_model_data'] if r['id'] not in {v[3] for v in c.IDS.values()}).update(write_date='wrong'),('ir_model_data',))
    reject('reject_XMLID_mapping',lambda s:c.row_map(s['tables']['ir_model_data'])[51388].update(res_id=1),('ir_model_data',))
    reject('reject_extra_language',lambda s:c.row_map(s['tables']['ir_ui_view'])[1599]['arch_db'].update(fr_FR='wrong'),('ir_ui_view',))
    reject('reject_wrong_arch_prev',lambda s:c.row_map(s['tables']['ir_ui_view'])[1599].update(arch_prev='wrong'),('ir_ui_view',))
    reject('reject_module_state',lambda s:s['tables']['ir_module_module'][0].update(state='to upgrade'),('ir_module_module',))
    reject('reject_permission',lambda s:s['tables']['ydental_access_grant'][0].update(ydental_level='none' if s['tables']['ydental_access_grant'][0]['ydental_level']!='none' else 'write'),('ydental_access_grant',))
    reject('reject_invoice_amount',lambda s:s['tables']['account_move'][0].update(amount_residual=1),('account_move',))
    reject('reject_menu_action',lambda s:c.row_map(s['tables']['ir_ui_menu'])[320].update(action='ir.actions.act_url,1'),('ir_ui_menu',))
    # Legal equal IDs in different physical tables must remain separate.
    a=subset(before,('ir_act_window',),True);b=subset(good,('ir_act_window',),True)
    duplicate=deepcopy(a['tables']['ir_act_window'][0]);duplicate['id']=571
    assert 571 not in c.row_map(a['tables']['ir_act_window'])
    a['tables']['ir_act_window'].append(deepcopy(duplicate));b['tables']['ir_act_window'].append(deepcopy(duplicate))
    project(a);project(b);c.metadata_gate(a,b)
    assert ('public','ir_act_window',571) in c.physical_map(a['action_projection'])
    assert ('public','ir_act_url',571) in c.physical_map(a['action_projection'])
    checks.append('same_id_different_physical_tables_preserved_and_accepted_unchanged')
    c.row_map(b['tables']['ir_act_window'])[571]['write_date']='wrong';project(b)
    try:c.metadata_gate(a,b)
    except AssertionError:checks.append('same_id_other_physical_table_mutation_rejected_no_silent_overwrite')
    else:raise AssertionError('DUPLICATE_ID_OVERWRITE')
    own=deepcopy(before['action_projection'][0]);own.update(physical_table='ir_actions',table_oid=100,id=571)
    own['row'].update(id=571,type='ir.actions.act_window_close')
    a=subset(before,projection=True);b=subset(good,projection=True)
    a['action_only']=[deepcopy(own)];b['action_only']=[deepcopy(own)]
    project(a);project(b);c.metadata_gate(a,b);checks.append('ONLY_parent_own_same_id_preserved_separately')
    b['action_only'][0]['row']['write_date']='wrong';project(b)
    try:c.metadata_gate(a,b)
    except AssertionError:checks.append('ONLY_parent_own_change_rejected')
    else:raise AssertionError('ONLY_PARENT_WAIVED')
    post=subset(good,('orm_signaling_default','orm_signaling_templates'))
    for t in ('orm_signaling_default','orm_signaling_templates'):post['tables'][t].append({'id':1,'date':'2026-10-17T03:00:00'})
    c.metadata_gate(before,post,postcommit=True);checks.append('actual_postcommit_gate_accepts_one_native_signal_each')
    post['tables']['orm_signaling_default'].append({'id':2,'date':'2026-10-17T03:00:00'})
    try:c.metadata_gate(before,post,postcommit=True)
    except AssertionError:checks.append('postcommit_extra_signal_rejected')
    else:raise AssertionError('SIGNAL_BUDGET_WAIVED')
    # Execute the actual shared transaction wrapper with a file-only ledger.
    for name,after,kind in [('pass',good,'pass'),('reject',b,'reject'),('load_error',good,'load_error'),
                            ('capture_error',good,'capture_error'),('IO_error',good,'IO_error'),('commit_unknown',good,'commit_unknown')]:
        path=work/name;private=path/'private';out=path/'public'
        if kind=='IO_error':path.mkdir(parents=True);out.write_text('fixture blocked parent directory')
        cr=FileCursor(private,out,unknown=kind=='commit_unknown');calls={'load':0,'capture':0}
        def load():
            calls['load']+=1
            if kind=='load_error':raise ValueError('FIXTURE_LOAD_ERROR')
        def capture():
            calls['capture']+=1
            if kind=='capture_error':raise OSError('FIXTURE_CAPTURE_ERROR')
            return after
        try:c.guarded_import(cr,before,load,capture,private,out)
        except (AssertionError,OSError,ValueError):
            assert kind!='pass' and cr.rollbacks==cr.closes==1
            assert cr.commits==(1 if kind=='commit_unknown' else 0)
            assert not (private/'metadata-committed.json').exists()
            if kind=='reject':
                assert (private/'metadata-precommit-before.json').exists()
                assert (private/'metadata-precommit-after.json').exists()
                assert (private/'metadata-precommit-full-diff.json').exists()
                assert not c.read(out/'metadata-precommit-decision.json')['PASS']
        else:assert kind=='pass' and (cr.commits,cr.rollbacks,cr.closes)==(1,0,1)
        checks.append('actual_evidence_transaction_wrapper_'+kind+'_order_and_exit')
    return before,good

def main():
    os.umask(0o077);c.repo_gate();seal=c.seal()
    assert not c.RUN.exists() and not (c.PRIVATE/'execution-intent.json').exists()
    run_no=len(list(c.PRIVATE.glob('offline-run-*')))+1
    work=c.PRIVATE/f'offline-run-{run_no:02}';work.mkdir(mode=0o700)
    checks=[]
    try:
        idx=c.read(c.ROOT/'docs/evidence/s10-p0-18/sha256-index.json')
        for p,e in idx['files'].items():
            data=(c.ROOT/p).read_bytes();assert c.sha(data)==e['sha256'] and len(data)==e['bytes'] and data==c.git('show',c.BASE+':'+p)
        assert len(idx['files'])==23
        assert c.sha((c.ROOT/'docs/evidence/s10-p0-18/sha256-index.json').read_bytes())=='e9f33c2fdc54d8fb3ae265fcf05a0c5023075fe1fe53f02746dc0bfa79c8fbc4'
        assert c.git('rev-parse',c.BASE+':docs/evidence/s10-p0-18/sha256-index.json').decode().strip()=='9430b1ed99a75dc2ce48472155ad93c294501fb0'
        checks.append('P018_23_SHA_and_index_fixed_object_preserved_no_old_execution')
        history=c.read(c.ROOT/'.local/s10-p0-18/source-after-rows.json')
        before,good=tests(history,work,checks)
        import s10_p0_19_browser as browser
        browser.login_credentials(history['tables']);checks.append('existing_private_user5_credentials_match_historical_synthetic_hash')
        assert shutil.which('wkhtmltopdf')=='/usr/local/bin/wkhtmltopdf'
        corefiles=['odoo/init.py','odoo/cli/command.py','odoo/tools/convert.py','odoo/addons/base/data/base_data.sql',
            'odoo/addons/base/models/ir_actions.py','odoo/addons/base/models/ir_ui_view.py','odoo/addons/base/models/ir_ui_menu.py',
            'odoo/addons/base/models/ir_model.py','odoo/orm/registry.py','odoo/orm/environments.py','odoo/sql_db.py',
            'odoo/addons/base/models/res_users.py','odoo/addons/base/models/res_device.py','odoo/addons/base/models/assetsbundle.py','addons/web/controllers/home.py']
        sources=[c.XML,'ydental_settlement/controllers/settlement.py','ydental_settlement/models/ydental_settlement_service.py',
            'ydental_settlement/models/report_ydental_settlement_pdf.py','ydental_settlement/report/ydental_settlement_templates.xml',
            'ydental_access/models/ydental_access_service.py','ydental_access/models/res_users.py','ydental_access/models/ir_http.py',
            'ydental_supply/models/ydental_access_service.py','ydental_access_test/models/ydental_access_service.py',
            'ydental_patient/models/ydental_patient_service.py','scripts/s10_e2e_w5_browser.py',
            'docs/evidence/s10-p0-18/source-after.json','docs/evidence/s10-p0-18/sha256-index.json','docs/evidence/s10-p0-11/read-only-sql.json']
        hashes={}
        for p in sources:
            data=(c.ROOT/p).read_bytes();assert data==c.git('show',c.BASE+':'+p);hashes[p]=c.sha(data)
        for p in corefiles:
            data=(c.CORE_ROOT/p).read_bytes();assert data==c.git('show',c.CORE+':'+p,cwd=c.CORE_ROOT);hashes['../'+p]=c.sha(data)
        assert 'CREATE TABLE ir_act_url (primary key(id)) INHERITS (ir_actions)' in (c.CORE_ROOT/'odoo/addons/base/data/base_data.sql').read_text()
        converter=ast.parse((c.CORE_ROOT/'odoo/tools/convert.py').read_text())
        fn=next(n for n in converter.body if isinstance(n,ast.FunctionDef) and n.name=='convert_file')
        assert [a.arg for a in fn.args.args][:4]==['env','module','filename','idref']
        checks.append('fixed_native_convert_API_and_PG_inheritance_SQL_proved')
        for p in sorted(c.ROOT.glob('scripts/s10_p0_19_*.py')):
            compile(ast.parse(p.read_text()),str(p),'exec');hashes[str(p.relative_to(c.ROOT))]=c.sha(p.read_bytes())
        private_deps=['.local/s10-p0-18/source-after-rows.json','.local/ydental_s10_test_20261015060000_b6c7d8e9/fixture.json',
            '.local/s00-b-deps/browser-fonts.conf','.local/s00-b-deps/verify-lib/pymupdf/__init__.py',
            '.local/s00-b-deps/verify-lib/pymupdf/_mupdf.so','.local/s00-b-deps/verify-lib/playwright/async_api/_generated.py']
        hashes.update({p:c.sha((c.ROOT/p).read_bytes()) for p in private_deps})
        c.save(c.OUT/'metadata-contract.json',{'old5':c.old_metadata(),'fixed_XML':c.XML,
            'expected_arch_structures':{n:c.norm(c.template(n)) for n,v in c.IDS.items() if v[1]=='ir_ui_view'},
            'direct_allowed_columns':{'ir_ui_view':sorted(c.VIEW_FIELDS),'ir_ui_menu':sorted(c.TECH_FIELDS),'ir_act_url':sorted(c.TECH_FIELDS),'ir_model_data':sorted(c.TECH_FIELDS)},
            'impact_map':{'action571':['ir_act_url physical571','ir_actions same physical ir_act_url571 projection'],
                'menu320':['ir_ui_menu physical320','ir_ui_menu_group_rel exact unchanged'],
                'view1597_1598_1599':['ir_ui_view exact IDs','ir_ui_view_group_rel exact unchanged'],
                'XMLID51384_51385_51386_51387_51388':['ir_model_data exact IDs'],'commit_signals':{'orm_signaling_default':1,'orm_signaling_templates':1}},
            'parent_permission':'Only public/ir_act_url/571 shared TECH_FIELDS after child gate and exact all shared field equality; all other physical keys and ONLY-own rows exact',
            'other_objects_business_language_grants_schema_reports':'EXACT_UNCHANGED'})
        c.save(c.OUT/'sql-contract.json',{'schema':c.schema(),'original643_queries':c.table_sql(),
            'identity':c.IDENTITY_SQL,'active':c.ACTIVE_SQL,'catalog':c.CATALOG_SQL,
            'additional3_queries':{'pg_inherits':c.INHERITS_SQL,'full_action_family_tableoid_projection':c.PROJECTION_SQL,'ONLY_parent_own_supplement':c.ONLY_SQL},
            'expected_inheritance_edges':before['action_inherits'],'expected_family_rows':571,'expected_ONLY_own_rows':0,
            'stable_key':['schema','physical_table','id'],'duplicate_physical_keys':'reject, never overwrite; complete evidence persists first',
            'source_statements_max_per_connection':651,'target_statements_max_per_connection':650,'native_explicit_snapshot_SELECTs':648,
            'SHOW_first':['transaction_read_only=on','transaction_isolation=repeatable read'],'snapshot_seconds_max':150,'statement_timeout_ms':15000,'lock_timeout_ms':3000,
            'maintenance':['SELECT oid,datname FROM pg_database ORDER BY oid','SELECT system_identifier::text FROM pg_control_system()',
                'SELECT pid FROM pg_stat_activity WHERE datname=%s','CREATE DATABASE "'+c.NAME+'" WITH TEMPLATE "'+c.SOURCE+'"','SELECT oid FROM pg_database WHERE datname=%s'],
            'baseline':'P018 source-after historical signatures only; current before/after are new authorized READONLY snapshots'})
        c.save(c.OUT/'offline-result.json',{'status':'PURE_FILE_COMPARATOR_AND_TRANSACTION_TESTS_PASS','checks':checks,'count':len(checks),'exit_code':0,
            'fixture_scope':'actual comparator, all571 historical action family records and both parent/child, selected other real metadata; synthetic fixture tableoids101..105 only; no native SQL or Odoo',
            'transaction_scope':'actual shared guarded_import with file-only ledger; fake commits are not native commits',
            'runtime_budget_used':0,'old_windows_reexecuted':False,'private_fixture_directory':str(work.relative_to(c.ROOT))})
        for p in sorted(c.OUT.glob('*.json')):hashes[str(p.relative_to(c.ROOT))]=c.sha(p.read_bytes())
        previous=c.read(c.ROOT/'docs/evidence/s10-p0-18/execution-freeze.json')
        c.save(c.OUT/'execution-freeze.json',{'authorization':c.AUTH,'base':c.BASE,'core':c.CORE,'branch':c.BRANCH,
            'source':{'name':c.SOURCE,'oid':c.SOURCE_OID,'cluster':c.CLUSTER,'seal':seal},
            'target':{'name':c.NAME,'port':c.PORT,'directory':str(c.RUN),'OID':'new result distinct from all old catalog; immutable marker'},
            'file_sha256':hashes,'maximum_budget':c.BUDGET,
            'argv':{'executor':[str(c.PYTHON),str(c.ROOT/'scripts/s10_p0_19_control.py')],
                'metadata':[str(c.PYTHON),str(c.ROOT/'scripts/s10_p0_19_metadata.py')],
                'http':[str(c.PYTHON),str(c.CORE_ROOT/'odoo-bin'),'-c',str(c.RUN/'odoo.conf')],
                'browser':[str(c.PYTHON),str(c.ROOT/'scripts/s10_p0_19_browser.py')]},
            'config':{'db_name':c.NAME,'dbfilter':'^'+c.NAME+'$','http_interface':'127.0.0.1','http_port':c.PORT,'data_dir':str(c.RUN/'data'),'workers':0,'max_cron_threads':0,'list_db':False,'db_maxconn':4},
            'native_environment':previous['native_environment']|{'PGOPTIONS':'-c statement_timeout=15000 -c lock_timeout=3000 -c idle_in_transaction_session_timeout=15000 -c timezone=UTC','connection_logging':'odoo.sql_db.connection:DEBUG; backend-create logs; no driver patches'},
            'HTTP_exact_routes':previous['HTTP_exact_routes'],'audit_exact6':previous['audit_exact6'],
            'audit_binding':previous['audit_binding'],'web_identity_fields':previous['web_identity_fields'],'assets_append_only':previous['assets_append_only'],
            'evidence_gate':'Before gate: fsync private full before/after/diff+actual physical source mapping; fsync and read back redacted complete diff index. Any capture/save/decision failure prohibits commit and rolls back/closes. One commit only after PASS. Independent postcommit gate includes only exact default/templates signal append<=1.',
            'connection_order':'W5-before closed before maintenance/CREATE; clone before, after metadata and final max3 independent READONLY/RR; metadata/Web native connections separate<=4 each; W5-after after owned service stopped',
            'protected_OIDs':[2100325,2100326,2100327],'stop':'Any actual failure/unknown: stop further actions, only remaining readonly tail + own process stop; no frozen edits/retry/new clone',
            'PDF':'one real page link click; %PDF<=10MB/20pages; bytes SHA=response SHA=audit SHA; existing PyMuPDF text+all-page raster+actual visual review required',
            'all_other_metadata_economic_clinical_permission_attachment_fields':'EXACT_UNCHANGED; original643 kept; 152 old filestore preserved; only listed asset files may append',
            'not_authorized':['old window replay','protected clone connection/reuse','product edits','full module upgrade','sudo','OS PG Docker network special','P020 S11 merge deploy']})
        print(json.dumps({'checks':len(checks),'exit_code':0,'runtime_budget_used':0,'freeze_sha256':c.sha((c.OUT/'execution-freeze.json').read_bytes())}))
    except BaseException as error:
        c.save(c.OUT/f'offline-attempt-{run_no:02}.json',{'status':'STATIC_PREPARATION_FAILED','exit_code':1,'checks_completed':checks,'error_type':type(error).__name__,'detail_sha256':c.sha(str(error).encode()),'runtime_budget_used':0})
        raise

if __name__=='__main__':
    main()

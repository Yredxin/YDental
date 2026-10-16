"""File-only STATIC_REVIEW for the P0-14 native DOM/session/source audit contract.

No PostgreSQL, Odoo, HTTP or browser imports. Historical saved rows are static
inputs, not a current qualification check or a simulated business transaction.
"""
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import subprocess
from types import SimpleNamespace

from lxml import html, etree

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / '.local/s10-p0-14'
OLD = ROOT / '.local/s10-p0-13'
OUT = ROOT / 'docs/evidence/s10-p0-14'
BASE = '6c64403f9c015c669e50e750aff6e0e7a2eab3c0'
AUTH = 6212000008


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_text())


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2)
        stream.write('\n')


def validate_dom(attributes, *, state, version, no_actor_execution):
    expected = {'data-document':'1','data-revision':'1','data-version':str(version),
                'data-state':state,'data-heartbeat':'2','data-can-handover':'no'}
    assert all(attributes.get(k)==v for k,v in expected.items()), 'DOM_IDENTITY_OR_STATE'
    assert no_actor_execution is True, 'CURRENT_ACTOR_EXECUTION'
    assert attributes.get('data-execution') in (None, '0'), 'NONZERO_EXECUTION'
    # This accepts an absent attribute. It never writes or synthesizes one.
    return True


def session_row_rule(template, row):
    diff = {k for k in template.keys() | row.keys() if template.get(k)!=row.get(k)}
    assert diff <= {'id','ydental_key_hash','create_date','write_date','write_uid'}
    assert (row['ydental_user_id'],row['ydental_store_id'],row['ydental_revision'])==(7,1,1)
    assert row['create_uid']==row['write_uid']==7
    return True


def source_view_row_rule(row):
    expected={'ydental_user_id':7,'ydental_store_id':1,'ydental_event':'source.view',
              'ydental_category':'medical','ydental_source':'source_model',
              'ydental_target_model':'ydental.clinical.document','ydental_target_id':1,
              'ydental_result':'accepted','create_uid':7,'write_uid':7}
    assert all(row.get(k)==v for k,v in expected.items())
    assert not row['ydental_reason'] and not row['ydental_before'] and not row['ydental_after']
    assert row['create_date']==row['write_date']
    return True


def method(path, class_name, name):
    tree=ast.parse((ROOT/path).read_text())
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==class_name)
    node=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name==name)
    return node, ast.get_source_segment((ROOT/path).read_text(),node)


def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==BASE
    assert read(PRIVATE/'remote-ref.json')['object']['sha']==BASE
    assert read(PRIVATE/'auth.json')['id']==AUTH
    comments=read(PRIVATE/'comments34.json')
    assert len(comments)==224 and comments[-1]['id']==AUTH
    assert [c['id'] for c in comments if 'S10-P0-14' in c['body'].splitlines()[0]]==[AUTH]
    OUT.mkdir(parents=True,exist_ok=True)
    checks=[];evidence={}
    index=read(ROOT/'docs/evidence/s10-p0-13/private-artifact-index.json')['raw_files']
    for name in ('clinical-get-0.html.json','target-after-rows.json','w5-private-rows.json','response-native-login.json'):
        assert sha((OLD/name).read_bytes())==index[name]['sha256'],name
    page=read(OLD/'clinical-get-0.html.json')
    root=html.fromstring(page['body']).xpath('//*[contains(concat(" ",normalize-space(@class)," ")," o_ydental_clinical ")]')[0]
    attrs={k:v for k,v in root.attrib.items() if k.startswith('data-')}
    assert 'data-execution' not in attrs
    before=read(OLD/'w5-private-rows.json');after=read(OLD/'target-after-rows.json')
    tables={t:[json.loads(r) for r in rs] for t,rs in before['tables'].items()}
    ended={t:[json.loads(r) for r in rs] for t,rs in after['tables'].items()}
    own_leases={r['id'] for r in tables['ydental_queue_lease'] if r['ydental_actor_id']==7}
    idle=not any(r['ydental_lease_id'] in own_leases and r['state'] in ('serving','verify') for r in tables['ydental_queue_execution'])
    assert idle and tables['ydental_clinical_document'][0]['ydental_current_execution_id']==1
    validate_dom(attrs,state='pending',version=2,no_actor_execution=idle)
    validate_dom(attrs|{'data-execution':'0'},state='pending',version=2,no_actor_execution=idle)
    checks+=['saved_real_HTML_missing_execution_accepted_under_actor_idle_predicate','literal_zero_accepted_under_same_predicate']
    def reject(label,fn):
        try:fn()
        except AssertionError:checks.append(label)
        else:raise AssertionError('gate_did_not_reject_'+label)
    reject('nonzero_execution_rejected',lambda:validate_dom(attrs|{'data-execution':'1'},state='pending',version=2,no_actor_execution=True))
    reject('wrong_actor_execution_rejected',lambda:validate_dom(attrs,state='pending',version=2,no_actor_execution=False))
    reject('version_drift_rejected',lambda:validate_dom(attrs|{'data-version':'3'},state='pending',version=2,no_actor_execution=True))
    tpl=etree.parse(str(ROOT/'ydental_clinical/views/ydental_clinical_templates.xml'))
    expression=tpl.xpath('//*[@t-att-data-execution]/@t-att-data-execution')[0]
    assert expression=='execution.id if execution else 0'
    assert eval(compile(ast.parse(expression,mode='eval'),'<fixed-QWeb-expression>','eval'),{}, {'execution':False})==0
    qweb=(ROOT/'../odoo/addons/base/models/ir_qweb.py').read_text()
    assert 'if value or isinstance(value, str):' in qweb
    condition='value or isinstance(value, str)'
    assert not eval(condition,{}, {'value':0}) and eval(condition,{}, {'value':'0'})
    js=(ROOT/'ydental_clinical/static/src/document/document.js').read_text()
    assert 'holder && Number(root.dataset.execution)' in js
    node_result=json.loads(subprocess.check_output(['node','-e',"console.log(JSON.stringify({missingIsNaN:Number.isNaN(Number(undefined)),missingBranch:Boolean(Number(undefined)),zeroBranch:Boolean(Number('0'))}))"],text=True))
    assert node_result=={'missingIsNaN':True,'missingBranch':False,'zeroBranch':False}
    checks+=['fixed_QWeb_numeric_zero_is_omitted_string_zero_is_kept','actual_JS_Number_missing_is_NaN_and_falsy']
    evidence['DOM']={'QWeb_expression':expression,'numeric_zero_attribute_emitted':False,'string_zero_attribute_emitted':True,
        'saved_HTML_metadata':attrs,'node_expression_only':node_result,'no_HTML_or_product_changes':True,
        'runtime_condition':'current source and target must still prove actor7 has no serving/verify execution, doc1 handover/pending2'}
    session=next(r for r in ended['ydental_access_session'] if r['id']==16)
    template=next(r for r in tables['ydental_access_session'] if r['ydental_user_id']==7)
    assert template['id']==4 and template['write_uid']==8
    session_row_rule(template,session)
    reject('new_session_wrong_write_uid_rejected',lambda:session_row_rule(template,session|{'write_uid':8}))
    reject('new_session_wrong_create_uid_rejected',lambda:session_row_rule(template,session|{'create_uid':8}))
    reject('new_session_wrong_store_rejected',lambda:session_row_rule(template,session|{'ydental_store_id':2}))
    _,creation=method('ydental_access/models/ydental_access_service.py','YDentalAccessService','_session_for_key')
    _,switch=method('ydental_access/models/ydental_access_service.py','YDentalAccessService','_switch')
    assert "Session = self.env['ydental.access.session'].sudo()" in creation
    assert "Session.create({'ydental_key_hash': digest, 'ydental_user_id': self.env.uid})" in creation
    assert "session.write({'ydental_store_id': store_id, 'ydental_revision': session.ydental_revision + 1})" in switch
    models=(ROOT/'../odoo/orm/models.py').read_text()
    assert "vals.setdefault('create_uid', self.env.uid)" in models and "vals.setdefault('write_uid', self.env.uid)" in models
    assert "log_vals = {'write_uid': self.env.uid, 'write_date': self.env.cr.now()}" in models
    assert 'superuser mode does not change the\n        current user' in models
    checks.append('new_session_uid7_from_native_create_switch_and_ORM_log_access')
    evidence['session']={'old_template_id':4,'old_template_write_uid':8,'saved_new_id':16,'required_new_create_uid':7,
        'required_new_write_uid':7,'only_added_template_difference':'write_uid strictly7; other existing4 differences unchanged',
        'old_rows':'exact full rows; no additional writes allowed'}
    _,controller=method('ydental_clinical/controllers/clinical.py','YDentalClinical','workbench')
    assert "pending = service.env['ydental.clinical.document'].search([" in controller
    assert "('ydental_store_id', '=', store.id), ('state', '=', 'pending')" in controller
    _,search=method('../odoo/orm/models.py','BaseModel','search')
    assert 'return self.search_fetch(domain, [], offset=offset, limit=limit, order=order)' in search
    _,search_fetch=method('ydental_access/models/ydental_access_source.py','YDentalAccessSource','search_fetch')
    assert "if not self.env.su:" in search_fetch and "records._source_audit('source.view')" in search_fetch
    _,audit=method('ydental_access/models/ydental_access_source.py','YDentalAccessSource','_source_audit')
    assert "session = service._scope()" in audit and "source='source_model', before=before, after=after" in audit
    assert 'for source in self' in audit and 'if self:' in audit
    _,source_domain=method('ydental_clinical/models/ydental_clinical_document.py','YDentalClinicalDocument','_source_domain')
    assert "self.env['ydental.clinical.service']._access()" in source_domain
    _,access_domain=method('ydental_access/models/ydental_access_source.py','YDentalAccessSource','_access_domain')
    assert 'super()._access_domain(operation) & self._source_domain(operation)' in access_domain
    # Execute only the actual pure audit-value builder AST: no ORM/database or
    # mocked service operation. Its dictionary output is deterministic.
    node,_=method('ydental_access/models/ydental_access_service.py','YDentalAccessService','_audit_values')
    fn=deepcopy(node);fn.decorator_list=[];module=ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[]));namespace={}
    exec(compile(module,'<fixed-source-pure-dict-builder>','exec'),namespace)
    values=namespace['_audit_values'](SimpleNamespace(env=SimpleNamespace(uid=7)),'source.view','medical',SimpleNamespace(_name='ydental.clinical.document',id=1),1,source='source_model')
    actual=next(r for r in ended['ydental_access_audit'] if r['id']==335)
    assert all(actual[k]==v or not actual[k] and not v for k,v in values.items())
    source_view_row_rule(actual)
    for key,value in [('ydental_user_id',8),('ydental_store_id',2),('ydental_target_id',2),('ydental_source','other'),('ydental_category','exam')]:
        reject('source_view_wrong_'+key,lambda key=key,value=value:source_view_row_rule(actual|{key:value}))
    pending=[r for r in tables['ydental_clinical_document'] if r['ydental_store_id']==1 and r['state']=='pending']
    assert len(pending)==1 and pending[0]['id']==1
    checks.append('source_view_actual_controller_search_ORM_dispatch_S01_pure_builder_path_proved')
    evidence['source.view']={'source_path':['clinical.workbench pending non-sudo search(store1,pending)','BaseModel.search -> self.search_fetch','YDentalAccessSource.search_fetch -> _source_audit','_source_audit -> _scope / _audit_values / immutable audit.create'],
        'pure_builder_matches_saved_audit335':True,'pending_doc_ids':[1],'exact_initial_GET_source_views':1,
        'final_confirmed_GET_source_views':0,'maximum_one_per_actual_GET':True,'absolute_cap':2,
        'frozen_plan_uses_stricter_total':1,'purpose':'authorized source-read trace on pending-document listing, independent of explicit clinical.view',
        'exact_identity':{k:actual[k] for k in values if k not in ('ydental_reason','ydental_before','ydental_after')}}
    pw=(ROOT/'.local/s00-b-deps/verify-lib/playwright/async_api/_generated.py').read_text()
    assert 'The handler will only be called for the first url if the response is a redirect.' in pw
    response=read(OLD/'response-native-login.json')
    assert response['status']==303 and response['headers']['location']=='/ydental/clinical?document_id=1'
    old_browser=read(ROOT/'docs/evidence/s10-p0-13/browser-result.json')
    assert old_browser['counts']['CLINICAL_GET']==0
    responses=[r for r in old_browser['responses'] if r['method']=='GET' and r['path']=='/ydental/clinical']
    assert len(responses)==1 and responses[0]['status']==200
    server=read(ROOT/'docs/evidence/s10-p0-13/native-dom-http-review.json')['server_requests']
    assert sum(r['method']=='GET' and r['path']=='/ydental/clinical' for r in server)==1
    checks.append('redirect_request_response_and_server_count1_independent_of_route_callback0')
    evidence['redirect']={'saved_login_status':303,'saved_redirect':'/ydental/clinical?document_id=1','old_route_count':0,
        'browser_response_count':1,'saved_server_count':1,'new_counter':'synchronous BrowserContext request event unique Request identities, including redirected_from; response+server reconciliation',
        'POST_gate':'route validation once per operation plus request/response/server equality; unknown or duplicate stops before continue'}
    assert 'if (saving || needsReconcile) { return; }' in js and 'if (token) { await action(\'heartbeat\'' in js
    assert "await action('release', {document_id: documentId, editor_token: token})" in js
    assert 'saving = true;' in js and 'token = null;' in js
    checks.append('native_timer_unmodified_saving_blocks_heartbeat_during_confirm_auto_release')
    evidence['heartbeat']={'interval_seconds':2,'timeout_seconds':600,'patch_timer':False,
        'plan':'native acquire then immediate confirm; before-forward compact read-only gates; saving=true during confirm/release; any heartbeat request hard STOP, never forwarded'}
    dependencies=['ydental_clinical/controllers/clinical.py','ydental_clinical/models/ydental_clinical_service.py',
        'ydental_clinical/models/ydental_clinical_document.py','ydental_clinical/static/src/document/document.js',
        'ydental_clinical/views/ydental_clinical_templates.xml','ydental_access/models/ydental_access_source.py',
        'ydental_access/models/ydental_access_service.py','ydental_access/models/ydental_access_session.py',
        '../odoo/orm/models.py','../odoo/addons/base/models/ir_qweb.py',
        '.local/s00-b-deps/verify-lib/playwright/async_api/_generated.py']
    save(OUT/'static-contract.json',{'status':'STATIC_REVIEW_PASS','authorization':AUTH,'base':BASE,'checks':checks,'count':len(checks),
        'evidence':evidence,'dependencies':{p:sha((ROOT/p).read_bytes()) for p in dependencies},
        'saved_private_inputs':{name:index[name] for name in ('clinical-get-0.html.json','target-after-rows.json','w5-private-rows.json','response-native-login.json')},
        'current_runtime_qualification':'NOT_RUN','SQL_CREATE_HTTP_FIREFOX_POST':0,'old_evidence_modified':False,
        'not_real_web_or_business_PASS':True})
    print(json.dumps({'status':'STATIC_REVIEW_PASS','checks':len(checks),'SQL_CREATE_HTTP_FIREFOX_POST':0}))


if __name__=='__main__':
    main()

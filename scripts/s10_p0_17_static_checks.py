"""P0-17 file-only checks. No Odoo imports, registry, SQL, HTTP or PDF calls.

Domain fixtures interpret the actual product expression in a small symbolic
predicate algebra. They do not execute the Odoo ORM or its SQL compiler.
"""
import ast
import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace as NS
import subprocess
import sys
import urllib.parse
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BASE = '21dc2dc243200336959482fcfa9d3b5f5f5ad271'
CORE = 'f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb'
BRANCH = 'codex/s10-settlement-finance-r1-20261013'
PRIVATE = ROOT / '.local/s10-p0-17'
OUT = ROOT / 'docs/evidence/s10-p0-17'
SERVICE = 'ydental_settlement/models/ydental_settlement_service.py'
CONTROLLER = 'ydental_settlement/controllers/settlement.py'
TEMPLATE = 'ydental_settlement/views/ydental_settlement_templates.xml'
PRODUCT = [SERVICE, CONTROLLER, TEMPLATE]
ZERO = dict.fromkeys(('DATABASE_CONNECTION','CREATE','ODOO_HTTP','FIREFOX','BUSINESS_GET_POST',
    'PDF_GENERATION','DIRECT_ORM','ODOO_SHELL_INSTALL_UPGRADE_INIT_TEST','EXECUTOR_SUDO',
    'OS_PG_DOCKER_NETWORK_SPECIAL','ISSUE_PROJECT_MUTATION','MERGE_DEPLOY_S11'),0)
CORE_PATHS = ['odoo/fields/__init__.py','odoo/orm/domains.py','odoo/orm/fields_relational.py','odoo/orm/models.py',
    'addons/account/models/account_move.py']
SOURCE_PATHS = ['ydental_settlement/models/ydental_settlement_source.py',
    'ydental_settlement/models/ydental_settlement_source_inverse.py',
    'ydental_access/models/ydental_access_service.py','ydental_access/models/constants.py',
    'ydental_access/models/ydental_access_source.py','ydental_patient/models/ydental_patient_service.py',
    'ydental_treatment/models/ydental_treatment_fee.py','ydental_treatment/models/ydental_treatment_event.py']


def sha(b):
    return hashlib.sha256(b).hexdigest()


def git(*args, core=False):
    assert args[0] in ('show','rev-parse','branch','remote','status','ls-tree','diff')
    return subprocess.check_output(['git',*args],cwd=ROOT.parent if core else ROOT)


def baseline(path,core=False):
    return git('show',(CORE if core else BASE)+':'+path,core=core).decode()


def save(name,obj):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n')


def method(text,name):
    nodes=[n for n in ast.walk(ast.parse(text)) if isinstance(n,ast.FunctionDef) and n.name==name]
    assert len(nodes)==1,(name,len(nodes))
    return nodes[0]


def ast_key(node):
    return ast.dump(node,include_attributes=False)


def canonical(node):
    return [node.tag,sorted(node.attrib.items()),(node.text or '').strip(),
        [[canonical(c),(c.tail or '').strip()] for c in node]]


def inventory():
    assert git('rev-parse','HEAD').decode().strip()==BASE
    assert git('branch','--show-current').decode().strip()==BRANCH
    assert git('remote','get-url','origin').decode().strip()=='https://github.com/Yredxin/YDental.git'
    assert git('rev-parse','HEAD',core=True).decode().strip()==CORE
    assert not git('status','--porcelain','--untracked-files=no',core=True).strip()
    files={}
    for path in PRODUCT+SOURCE_PATHS:
        b=(ROOT/path).read_bytes()
        assert b.decode()==baseline(path)
        files[path]={'git':BASE,'sha256':sha(b)}
    for path in CORE_PATHS:
        b=(ROOT.parent/path).read_bytes()
        assert b.decode()==baseline(path,core=True)
        files['CORE/'+path]={'git':CORE,'sha256':sha(b)}
    domains=baseline('odoo/orm/domains.py',core=True)
    relational=baseline('odoo/orm/fields_relational.py',core=True)
    models=baseline('odoo/orm/models.py',core=True)
    assert "'any', 'not any'" in domains and 'def __invert__(self)' in domains
    assert "exists = operator in ('any', 'any!')" in relational
    assert 'comodel = table._model.env[self.comodel_name]' in relational
    assert 'if self.env.su or bypass_access:' in models
    proofs=[('odoo/fields/__init__.py',20,20,'fields.Domain alias'),
        ('odoo/orm/domains.py',81,101,'any/not any semantics'),
        ('odoo/orm/domains.py',207,224,'three-argument Domain constructor'),
        ('odoo/orm/domains.py',318,339,'AND and inversion'),
        ('odoo/orm/fields_relational.py',847,889,'x2many comodel env and exists/non-exists query'),
        ('odoo/orm/models.py',1432,1447,'search uses model environment, not current record IDs'),
        ('odoo/orm/models.py',4852,4890,'existing gated su environment sees all sources; no hidden foreign source')]
    plan={'authorization':6215375331,'previous_ruling':6215317877,'base':BASE,'core':CORE,
        'original_and_dependency_SHA':files,'core_proofs':[{'path':p,'line':a,'end_line':b,'basis':label} for p,a,b,label in proofs],
        'old_modified_file_allowlist':PRODUCT,'new_file_allowlist':['scripts/s10_p0_17_*.py','docs/s10-p0-17-*.md','docs/evidence/s10-p0-17/*'],
        'service_scope':'_workbench only; append settled page/count/list, same _workbench_page limit50; stable invoice_date asc,id asc; audit invoice_view each displayed settled invoice',
        'settled_header':['company_id=current store.company','state=posted','move_type=out_invoice','payment_state=paid','amount_residual=0'],
        'all_source_rule':'EXISTS(valid source) AND NOT EXISTS(NOT valid source); current store, real fee, fee/event same store, event confirmed; filter source/fee/event patients by legal family when selected',
        'existing_environment':'reuse invoices account.move environment already gated by _access and existing sudo; add no sudo and no any! bypass; protected source models have no active field hiding rows',
        'controller_scope':'workbench only; settled_page decimal string 1..5 digits and value1..10000; retain old guards; page_url carries settled page and patient; can_export exact current _levels(member)[export]==write',
        'template_scope':'append section name=settled-bills only; no forms or payment checkbox; ID/date/amount/residual; current internal PDF label; can_export link guard; dedicated nav next<=10000 preserves all old XML',
        'protected':'all other methods including _workbench_page,_invoice,_pdf,_report_payload,PDF controller,POST handlers and all old QWeb elements unchanged',
        'static_matrix':['cross company','cross store','same-company mixed source','missing/foreign/pending fee source',
            'patient family alias/filter/mixed patient','no settlement read','no export write','manager not exemption',
            'wrong store/session owner/revision','revoked next-request grant and old PDF guard unchanged',
            'invalid/type/overflow/upper page','50 rows stable/no overlap/repeated page','patient and other page URL preservation',
            'old invoices/payment/waive unchanged','no additional sudo/ORM writes/imports/routes'],
        'actual_execution_budget':ZERO,'evidence_level':'CODE_ONLY / STATIC_FILE_FIXTURES; not Odoo Domain/ORM/HTTP/QWeb runtime'}
    save('preflight-plan.json',plan)
    api={'base':BASE,'issues':{},'comments':{}}
    for number in (23,34,35):
        issue=json.loads((PRIVATE/f'issue{number}.json').read_text())
        comments=json.loads((PRIVATE/f'comments{number}.json').read_text())
        assert len(comments)=={23:3,34:236,35:0}[number]
        api['issues'][str(number)]={'state':issue['state'],'body_sha256':sha(issue['body'].encode()),'comments':len(comments)}
        api['comments'][str(number)]=[{'id':c['id'],'url':c['url'],'updated_at':c['updated_at'],
            'body_sha256':sha(c['body'].encode()),'characters':len(c['body'])} for c in comments]
    assert json.loads((PRIVATE/'ref.json').read_text())['object']['sha']==BASE
    assert json.loads((PRIVATE/'comments34.json').read_text())[-1]['id']==6215375331
    save('github-start.json',api)
    print(json.dumps({'plan_sha256':sha((OUT/'preflight-plan.json').read_bytes()),'product_original_SHA':{p:files[p]['sha256'] for p in PRODUCT},'budget':ZERO}))


class Predicate:
    def __init__(self,*args):
        self.node=args if len(args)!=1 else args[0]
    def __and__(self,other):
        return Predicate(('and',self,other))
    def __invert__(self):
        return Predicate(('not',self))
    def matches(self,row):
        n=self.node
        if n[0]=='and':
            return n[1].matches(row) and n[2].matches(row)
        if n[0]=='not':
            return not n[1].matches(row)
        field,op,value=n
        got=row
        for key in field.split('.'):
            got=got.get(key,False) if isinstance(got,dict) else False
        if op=='any':
            return any(value.matches(x) for x in got or [])
        if op=='not any':
            return not any(value.matches(x) for x in got or [])
        if op=='=':
            return got==value
        if op=='!=':
            return got!=value
        if op=='in':
            return got in value
        if op=='>':
            return got>value
        raise AssertionError(('unsupported symbolic operator',op))


def pure_eval(node,names):
    if isinstance(node,ast.Constant):
        return node.value
    if isinstance(node,ast.Name):
        return names[node.id]
    if isinstance(node,ast.Attribute):
        assert node.attr in ('Domain','id','company_id')
        return getattr(pure_eval(node.value,names),node.attr)
    if isinstance(node,ast.BinOp) and isinstance(node.op,ast.BitAnd):
        return pure_eval(node.left,names)&pure_eval(node.right,names)
    if isinstance(node,ast.UnaryOp) and isinstance(node.op,ast.Invert):
        return ~pure_eval(node.operand,names)
    if isinstance(node,ast.Call):
        assert ast.unparse(node.func)=='fields.Domain' and not node.keywords
        return Predicate(*(pure_eval(a,names) for a in node.args))
    if isinstance(node,ast.Compare) and len(node.ops)==1 and isinstance(node.ops[0],ast.IsNot):
        return pure_eval(node.left,names) is not pure_eval(node.comparators[0],names)
    raise AssertionError(('not a pure Domain expression',ast.dump(node)))


def domain_from_product(body,family=(101,102),store=1,company=1):
    names={'fields':NS(Domain=Predicate),'store':NS(id=store,company_id=NS(id=company)),
        'family':None if family is None else list(family)}
    allowed={'patient_domain','source_domain','settled_source_domain','settled_domain'}
    def walk(nodes):
        for node in nodes:
            if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in allowed:
                names[node.targets[0].id]=pure_eval(node.value,names)
            elif isinstance(node,ast.AugAssign) and isinstance(node.target,ast.Name) and node.target.id in allowed:
                assert isinstance(node.op,ast.BitAnd)
                names[node.target.id]=names[node.target.id]&pure_eval(node.value,names)
            elif isinstance(node,ast.If) and ast.unparse(node.test)=='family is not None' and family is not None:
                walk(node.body)
    walk(body)
    return names['settled_domain']


def expr(node,names):
    # Execute only a selected, pure scalar validation expression, never a
    # controller/service function, decorator, Odoo call or model method.
    return eval(compile(ast.Expression(node),'<pure scalar fixture>','eval'),
        {'__builtins__':{'any':any,'isinstance':isinstance,'str':str,'int':int,'len':len,'dict':dict,'type':type}},names)


def tests():
    receipt=json.loads((PRIVATE/'preflight-api-readback.json').read_text())
    assert receipt['verbatim_equal'] and receipt['plan_sha256']==sha((OUT/'preflight-plan.json').read_bytes())
    results=[]
    def check(name,condition):
        assert condition,name
        results.append({'case':name,'result':'PASS','layer':'STATIC_FILE_FIXTURE'})
    src=(ROOT/SERVICE).read_text();ctl=(ROOT/CONTROLLER).read_text()
    work=method(src,'_workbench');route=method(ctl,'workbench')
    for p in (SERVICE,CONTROLLER):
        compile((ROOT/p).read_text(),p,'exec')
    check('Python_AST_and_in_memory_compile',True)
    for p,name in [(SERVICE,'_workbench'),(CONTROLLER,'workbench')]:
        old=baseline(p);new=(ROOT/p).read_text();a=method(old,name);b=method(new,name)
        restored='\n'.join(new.splitlines()[:b.lineno-1]+old.splitlines()[a.lineno-1:a.end_lineno]+new.splitlines()[b.end_lineno:])+'\n'
        check('all_other_source_bytes_unchanged:'+p,restored==old)
    check('no_new_sudo_calls',sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='sudo' for n in ast.walk(work))==
        sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='sudo' for n in ast.walk(method(baseline(SERVICE),'_workbench'))))
    check('no_new_privileged_quantifier',not any(isinstance(n,ast.Constant) and n.value in ('any!','not any!') for n in ast.walk(work)))
    original=method(baseline(SERVICE),'_workbench')
    class RemoveNew(ast.NodeTransformer):
        def visit_Assign(self,node):
            names={n.id for t in node.targets for n in ast.walk(t) if isinstance(n,ast.Name)}
            if names & {'settled_source_domain','settled_domain','settled','settled_count'}:
                return None
            return self.generic_visit(node)
        def visit_If(self,node):
            if node.body and all(isinstance(n,ast.AugAssign) and isinstance(n.target,ast.Name) and n.target.id=='settled_source_domain' for n in node.body):
                return None
            return self.generic_visit(node)
        def visit_For(self,node):
            if isinstance(node.iter,ast.Name) and node.iter.id=='settled':
                return None
            return self.generic_visit(node)
        def visit_Tuple(self,node):
            node.elts=[n for n in node.elts if not isinstance(n,ast.Constant) or n.value!='settled']
            return self.generic_visit(node)
        def visit_Dict(self,node):
            pairs=[(k,v) for k,v in zip(node.keys,node.values) if not isinstance(k,ast.Constant) or k.value!='settled']
            node.keys=[k for k,v in pairs];node.values=[v for k,v in pairs]
            return self.generic_visit(node)
    check('entire_old_workbench_AST_preserved_after_removing_additions',ast_key(RemoveNew().visit(copy.deepcopy(work)))==ast_key(original))
    def source(patient=101,store=1,fee_store=None,event_store=None,state='confirmed'):
        return {'ydental_store_id':store,'ydental_patient_id':patient,'ydental_fee_id':{
            'ydental_store_id':store if fee_store is None else fee_store,'ydental_patient_id':patient,
            'ydental_event_id':{'ydental_store_id':store if event_store is None else event_store,'ydental_patient_id':patient,'state':state}}}
    def bill(**kw):
        return dict({'id':1001,'company_id':1,'state':'posted','move_type':'out_invoice','payment_state':'paid',
            'amount_residual':0,'invoice_date':'2099-01-01','ydental_settlement_source_ids':[source()]},**kw)
    pred=domain_from_product(work.body)
    scenarios=[('valid_own_paid_bill',bill(),True),('legal_patient_alias',bill(ydental_settlement_source_ids=[source(102)]),True),
        ('cross_company_header',bill(company_id=2),False),('cross_store_only',bill(ydental_settlement_source_ids=[source(store=2)]),False),
        ('same_company_mixed_store',bill(ydental_settlement_source_ids=[source(),source(store=2)]),False),
        ('no_source',bill(ydental_settlement_source_ids=[]),False),('mixed_patient_family',bill(ydental_settlement_source_ids=[source(),source(301)]),False),
        ('patient_filter_mismatch',bill(ydental_settlement_source_ids=[source(301)]),False),
        ('foreign_fee_store',bill(ydental_settlement_source_ids=[source(fee_store=2)]),False),
        ('foreign_event_store',bill(ydental_settlement_source_ids=[source(event_store=2)]),False),
        ('pending_fee_event',bill(ydental_settlement_source_ids=[source(state='pending')]),False)]
    missing=source();missing['ydental_fee_id']=False
    scenarios.append(('mixed_real_and_missing_fee',bill(ydental_settlement_source_ids=[source(),missing]),False))
    fee_patient=source();fee_patient['ydental_fee_id']['ydental_patient_id']=301
    scenarios.append(('fee_patient_filter_mismatch',bill(ydental_settlement_source_ids=[fee_patient]),False))
    event_patient=source();event_patient['ydental_fee_id']['ydental_event_id']['ydental_patient_id']=301
    scenarios.append(('event_patient_filter_mismatch',bill(ydental_settlement_source_ids=[event_patient]),False))
    for field,value in [('state','draft'),('move_type','out_refund'),('payment_state','in_payment'),('amount_residual',1),('amount_residual',-1)]:
        scenarios.append(('invalid_header:'+field+':'+str(value),bill(**{field:value}),False))
    for name,row,wanted in scenarios:
        check(name,pred.matches(row)==wanted)
    check('no_filter_all_current_store_patients',domain_from_product(work.body,None).matches(bill(ydental_settlement_source_ids=[source(301)])))
    check('wrong_current_store_excludes_old_store_invoice',not domain_from_product(work.body,store=2).matches(bill()))
    check('current_store2_own_source_allowed',domain_from_product(work.body,store=2).matches(bill(ydental_settlement_source_ids=[source(store=2)])))
    rows=[bill(id=i,invoice_date='2099-01-01') for i in reversed(range(1001,1106))]
    ordered=sorted([r for r in rows if pred.matches(r)],key=lambda r:(r['invoice_date'],r['id']))
    page=lambda n:[r['id'] for r in ordered[(n-1)*50:n*50]]
    check('105_rows_pages_50_50_5',list(map(len,[page(1),page(2),page(3)]))==[50,50,5])
    check('stable_order_no_overlap_repeated_page',page(1)+page(2)+page(3)==list(range(1001,1106)) and page(2)==page(2))
    check('page4_and_upper_page_empty',page(4)==page(10000)==[])
    paginator=method(src,'_workbench_page')
    check('actual_shared_page_helper_limit50_unchanged',ast_key(paginator)==ast_key(method(baseline(SERVICE),'_workbench_page')))
    settled_call=next(n.value for n in work.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='settled' for t in n.targets for x in ast.walk(t)))
    check('actual_settled_search_reuses_original_environment_and_order',ast.unparse(settled_call)=="self._workbench_page(invoices, settled_domain, page_numbers['settled'], 'invoice_date asc, id asc')")
    returned=next(n.value for n in work.body if isinstance(n,ast.Return))
    mapping={k.value:v for k,v in zip(returned.keys,returned.values)}
    check('service_returns_settled_records_and_pages',ast.unparse(mapping['settled'])=='settled' and ast.unparse(mapping['pages'])=='page_numbers')
    counts=mapping['page_counts']
    check('service_returns_settled_count',any(isinstance(k,ast.Constant) and k.value=='settled' and ast.unparse(v)=='settled_count' for k,v in zip(counts.keys,counts.values)))
    numbers=next(n.value for n in work.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='page_numbers' for t in n.targets))
    check('model_populates_settled_default_page',isinstance(numbers,ast.DictComp) and isinstance(numbers.generators[0].iter,ast.Tuple) and numbers.generators[0].iter.elts[-1].value=='settled')
    raw=next(n.value for n in route.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='raw_pages' for t in n.targets))
    check('controller_passes_settled_page_to_model',any(k.value=='settled' and ast.unparse(v)=='settled_page' for k,v in zip(raw.keys,raw.values)))
    defaults_by_arg=dict(zip([n.arg for n in route.args.args[-len(route.args.defaults):]],route.args.defaults))
    check('controller_settled_default_is_one',isinstance(defaults_by_arg['settled_page'],ast.Constant) and defaults_by_arg['settled_page'].value=='1')
    for path,field in [('ydental_settlement/models/ydental_settlement_source.py','ydental_fee_id'),
        ('ydental_treatment/models/ydental_treatment_fee.py','ydental_event_id'),
        ('ydental_treatment/models/ydental_treatment_record.py','ydental_patient_id'),
        ('ydental_access/models/ydental_access_source.py','ydental_store_id')]:
        node=next(n.value for n in ast.walk(ast.parse(baseline(path))) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==field for t in n.targets))
        check('real_model_field_chain:'+field, isinstance(node,ast.Call) and ast.unparse(node.func)=='fields.Many2one')
    guard=next(n.test for n in route.body if isinstance(n,ast.If))
    defaults={k:'1' for k in ('today','history','pending','invoices','payments','refunds','closes','settled')}
    def controller_valid(value,patient=None):
        return not expr(guard,{'settled_page':value,'patient_id':patient,'raw_pages':dict(defaults,settled=value)})
    for value in ('1','2','9999','10000','00001','١'):
        check('valid_controller_page:'+value,controller_valid(value,'101'))
    for value in ('','0','-1','10001','999999','9'*5000,'1.0','1e2',' 1','1 ',None,True,1,[],{}):
        check('invalid_controller_page:'+str(value)[:32],not controller_valid(value))
    check('invalid_patient_filter_not_relaxed',not controller_valid('1','x'))
    model_guard=next(n.test for n in work.body if isinstance(n,ast.If) and 'Select a valid workbench page' in ast.unparse(n))
    for value in (0,-1,10001,True,'2',1.5):
        check('invalid_model_page:'+repr(value),expr(model_guard,{'pages':{'settled':value}}))
    check('valid_model_page10000',not expr(model_guard,{'pages':{'settled':10000}}))
    check('unknown_model_page_rejected',expr(model_guard,{'pages':{'other':1}}))
    pagefn=next(n for n in route.body if isinstance(n,ast.FunctionDef) and n.name=='page_url')
    namespace={'pages':dict.fromkeys(defaults,1),'patient_id':'101','urlencode':urllib.parse.urlencode}
    namespace['pages']['payments']=3
    exec(compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(pagefn)],type_ignores=[])),'<pure page URL fixture>','exec'),namespace)
    url=namespace['page_url']('settled',2)
    check('URL_keeps_patient_other_pages_and_settled',urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)=={'patient_id':['101'],'payments_page':['3'],'settled_page':['2']})
    check('URL_repeated_no_mutation',namespace['page_url']('settled',2)==url and namespace['pages']['settled']==1)
    check('URL_default_page_omitted','settled_page' not in namespace['page_url']('settled',1))
    export=next(v for n in ast.walk(route) if isinstance(n,ast.Dict) for k,v in zip(n.keys,n.values) if isinstance(k,ast.Constant) and k.value=='can_export')
    check('can_export_exact_native_membership_expression',ast.unparse(export)=="access._levels(member)['export'] == 'write'")
    for value in ('none','read','write'):
        check('export_level:'+value,expr(export,{'access':NS(_levels=lambda m:m),'member':{'export':value}})==(value=='write'))
    check('manager_without_export_no_exemption',not expr(export,{'access':NS(_levels=lambda m:m),'member':{'export':'none','manager':True}}))
    native=baseline('ydental_access/models/ydental_access_service.py')
    rank=next(ast.literal_eval(n.value) for n in ast.parse(baseline('ydental_access/models/constants.py')).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='RANK' for t in n.targets))
    read_guard=next(n.test for n in method(native,'_check').body if isinstance(n,ast.If) and 'RANK[self._levels' in ast.unparse(n.test))
    for value in ('none','read','write'):
        check('settlement_read_native_guard:'+value,expr(read_guard,{'RANK':rank,'self':NS(_levels=lambda m:m),'membership':{'settlement':value},'category':'settlement','level':'read'})==(value=='none'))
    scope=method(native,'_scope')
    binding_guard=next(n.test for n in scope.body if isinstance(n,ast.If) and 'binding.user_id' in ast.unparse(n.test))
    revision_guard=next(n.test for n in scope.body if isinstance(n,ast.If) and 'session.ydental_revision !=' in ast.unparse(n.test))
    class Binding:
        def __init__(self,user_id,revision):self.user_id=user_id;self.revision=revision
    check('wrong_session_owner_rejected',expr(binding_guard,{'Binding':Binding,'binding':Binding(8,1),'self':NS(env=NS(uid=5))}))
    check('old_session_revision_rejected',expr(revision_guard,{'session':NS(ydental_revision=2),'binding':Binding(5,1)}))
    employment_guard=next(n.test for n in method(native,'_check').body if isinstance(n,ast.If) and 'membership.ydental_employee_id.active' in ast.unparse(n.test))
    check('missing_membership_rejected',expr(employment_guard,{'membership':False}))
    check('inactive_employee_rejected',expr(employment_guard,{'membership':NS(ydental_employee_id=NS(active=False))}))
    relation_guard=next(n.test for n in method(baseline('ydental_patient/models/ydental_patient_service.py'),'_current_relation').body if isinstance(n,ast.If))
    check('missing_current_store_patient_relation_rejected',expr(relation_guard,{'required':True,'relation':False}))
    check('revocation_next_expression_hides_old_link',not expr(export,{'access':NS(_levels=lambda m:m),'member':{'export':'none'}}))
    check('PDF_server_export_check_unchanged',"_check('export', 'write')" in ast.unparse(method(src,'_report_payload')))
    check('settlement_revocation_server_access_first',ast.unparse(method(src,'_report_payload').body[0])=='store = self._access()'
        and expr(read_guard,{'RANK':rank,'self':NS(_levels=lambda m:m),'membership':{'settlement':'none','export':'write'},'category':'settlement','level':'read'}))
    check('PDF_server_current_store_source_guard_unchanged',ast_key(method(src,'_invoice'))==ast_key(method(baseline(SERVICE),'_invoice'))
        and any(isinstance(n,ast.Compare) and ast.unparse(n.left)=='source.ydental_store_id'
            and isinstance(n.ops[0],ast.NotEq) and ast.unparse(n.comparators[0])=='store'
            for n in ast.walk(method(src,'_invoice'))))
    tree=ET.fromstring((ROOT/TEMPLATE).read_text());oldtree=ET.fromstring(baseline(TEMPLATE))
    section=next(n for n in tree.iter('section') if n.get('name')=='settled-bills')
    parents={child:parent for parent in tree.iter() for child in parent}
    parents[section].remove(section)
    check('all_original_QWeb_XML_structure_unchanged',canonical(tree)==canonical(oldtree))
    check('template_consumes_same_settled_variable',any(n.get('t-foreach')=='settled' and n.get('t-as')=='invoice' for n in section.iter()))
    check('settled_section_no_forms_or_checkboxes',not list(section.iter('form')) and not list(section.iter('input')))
    link=next(n for n in section.iter('a') if 'pdf/bill/' in n.get('t-att-href',''))
    check('new_PDF_link_exact_guard_and_label',link.get('t-if')=='can_export' and ''.join(link.itertext())=='下载当前内部账单 PDF')
    check('new_link_only_selected_invoice_id',link.get('t-att-href')=="'/ydental/settlement/pdf/bill/%s' % invoice.id")
    nextlink=next(n for n in section.iter('a') if ''.join(n.itertext())=='下一页')
    for page,count,wanted in [(1,51,True),(2,51,False),(10000,500001,False)]:
        expression=ast.parse(nextlink.get('t-if'),mode='eval').body
        check('nav_upper_bound:'+str(page)+':'+str(count),expr(expression,{'pages':{'settled':page},'page_counts':{'settled':count}})==wanted)
    check('no_live_imports_in_static_checker',not any(isinstance(n,(ast.Import,ast.ImportFrom)) and any(x.name.split('.')[0] in ('odoo','psycopg2','requests','playwright') for x in n.names) for n in ast.walk(ast.parse(Path(__file__).read_text()))))
    # Independent counterexample verifies the negative quantifier is essential.
    weakened=copy.deepcopy(work.body)
    class RemoveNegative(ast.NodeTransformer):
        def visit_Call(self,node):
            if isinstance(node.func,ast.Attribute) and node.func.attr=='Domain' and len(node.args)==3 and isinstance(node.args[1],ast.Constant) and node.args[1].value=='not any':
                return ast.copy_location(ast.Call(func=copy.deepcopy(node.func),args=[ast.Constant('company_id'),ast.Constant('='),ast.Constant(1)],keywords=[]),node)
            return self.generic_visit(node)
    weakened=[RemoveNegative().visit(n) for n in weakened]
    check('mutation_removing_negative_quantifier_caught',domain_from_product(weakened).matches(bill(ydental_settlement_source_ids=[source(),source(store=2)])))
    protected=[]
    for encoded in git('ls-tree','-r','--name-only','-z',BASE).split(b'\0'):
        if encoded and encoded.decode() not in PRODUCT:
            p=encoded.decode();b=(ROOT/p).read_bytes()
            check('protected_bytes:'+p,b==git('show',BASE+':'+p))
            protected.append((p,sha(b)))
    assert git('rev-parse','HEAD',core=True).decode().strip()==CORE and not git('status','--porcelain','--untracked-files=no',core=True).strip()
    save('static-results.json',{'status':'CODE_STATIC_CHECKS_PASS_PENDING_GPT','exit_code':0,'PASS_count':len(results),
        'cases':results,'protected_files_count':len(protected),'protected_manifest_sha256':sha(json.dumps(protected).encode()),
        'actual_budget':ZERO,'native_ORM_SQL_HTTP_QWeb_engine':'NOT_RUN','product_sha256':{p:sha((ROOT/p).read_bytes()) for p in PRODUCT},
        'base':BASE,'core':CORE,'requested_ceiling':'S10_P0_17_PAID_BILL_WORKBENCH_CODE_STATIC_TECH_ACCEPTED'})
    print(json.dumps({'status':'PASS','static_checks':len(results),'protected_files':len(protected),'actual_budget':ZERO}))


if __name__=='__main__':
    assert len(sys.argv)==2
    if sys.argv[1]=='--inventory':inventory()
    elif sys.argv[1]=='--test':tests()
    else:raise AssertionError('file-only --inventory or --test required')

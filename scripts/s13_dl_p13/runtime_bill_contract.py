"""Read the actual loaded first-bill contract and render explicit RO fixtures.

No business service is dispatched. Synthetic marker records and non-secret test
nonce literals exist only in the QWeb render context. Actual request token values
are never obtained, stored or hashed by this collector.
"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'scripts/s13_dl_p12/runtime_components.py'
source = SOURCE.read_text().replace('.local/dl-p12', '.local/dl-p13')
source = source.replace('P12_LOADED_QWEB_SETTLEMENT_MEMORY_COMPONENTS_COMPLETE',
                        'P13_LOADED_QWEB_SETTLEMENT_MEMORY_COMPONENTS_COMPLETE')
spec = importlib.util.spec_from_file_location('p13_bill_contract_runner', SOURCE)
engine = importlib.util.module_from_spec(spec)
exec(compile(source, str(SOURCE), 'exec'), engine.__dict__)
engine.SCRIPT = r'''
import copy, datetime as dt, decimal, hashlib, json, os, subprocess
from pathlib import Path
from types import SimpleNamespace as NS
from lxml import etree, html
root=Path.cwd();private=root/'.local/dl-p13'
env.cr.rollback();env.cr.execute('SET TRANSACTION READ ONLY')
env.cr.execute("SELECT pg_backend_pid(),current_database(),(SELECT oid FROM pg_database WHERE datname=current_database()),(pg_control_system()).system_identifier::text,current_user,current_setting('transaction_read_only'),current_setting('transaction_isolation')")
identity=env.cr.fetchone()
assert identity[1:]==('ydental_s11_synth_20261023_01',2171423,'7694897083368259627','ydental_s11_synth_20261023_01','on','repeatable read')
base=env.ref('ydental_settlement.ydental_settlement_page')
qweb=env['ir.qweb'].with_context(lang='zh_CN',minimal_qcontext=True)
contracts={};combined=None;panel=None
for language in ('en_US','zh_CN'):
 arch=base.with_context(lang=language)._get_combined_arch()
 forms=arch.xpath('.//form[@method="post"][@action="/ydental/settlement/action"][input[@name="operation"][@value="bill"]]')
 assert len(forms)==1
 form=forms[0];details=form.xpath('ancestor::details[@name="settlement-operation"][1]')[0]
 assert details.tag=='details' and details.get('name')=='settlement-operation'
 assert details.get('t-if')=='can_write and (today or history)'
 assert len(details.xpath('./summary'))==1 and len(details.xpath('.//form'))==1
 assert details.getprevious().get('data-dl-scope')=='settlement-lookup'
 assert len(details.xpath('.//a'))==1 and not form.xpath('.//a')
 assert form.xpath('./t[@t-call="ydental_settlement.ydental_settlement_tokens"]')
 assert not details.xpath('.//input[@name="fee_ids"][@checked]')
 controls=[]
 for node in form.xpath('.//input | .//button | .//select | .//textarea | .//t[@t-call]'):
  controls.append({'tag':node.tag,'attributes':{k:v for k,v in node.attrib.items() if k not in ('class','style') and not k.startswith('data-')},'text':''.join(node.itertext()).strip()})
 conditions=[{'tag':node.tag,'condition':node.get('t-if'),'iteration':node.get('t-foreach'),'alias':node.get('t-as')} for node in details.iter() if node.get('t-if') is not None or node.get('t-foreach') is not None]
 contracts[language]={'first_bill_c14n':etree.tostring(details,method='c14n').decode(),'first_bill_c14n_sha256':hashlib.sha256(etree.tostring(details,method='c14n')).hexdigest(),'controls_in_original_DOM_order':controls,'conditions_and_iterations':conditions,'summary_text':''.join(details.find('summary').itertext()).strip(),'cancel_attributes':dict(details.xpath('.//a')[0].attrib),'cancel_outside_form':True,'details_direct_previous_scope':details.getprevious().get('data-dl-scope'),'lookup_c14n_sha256':hashlib.sha256(etree.tostring(details.getprevious(),method='c14n')).hexdigest()}
 if language=='zh_CN':combined=arch;panel=details
class Rows(list):
 def __or__(self,other):
  result=Rows(self);seen={row.id for row in self}
  result.extend(row for row in other if row.id not in seen)
  return result
marker='【P13内存夹具】'
components=[]
for name,can_write,populated,long in [('normal-first-bill',True,True,False),('long-multiple-fees',True,True,True),('empty-no-fees',True,False,False),('no-write-permission',False,True,False)]:
 suffix='长中文费用项目内容ABCDEFGHIJ-0123456789'*8 if long else ''
 patient=NS(id=900000001,ydental_number=marker+'PN-900000001'+suffix)
 currency=NS(name='FIXTURE',decimal_places=2)
 rows=Rows()
 for index in range(8 if long else 2):
  catalog=NS(name=marker+'费用项目'+str(index+1)+suffix)
  event=NS(id=900001001+index,ydental_catalog_id=catalog,ydental_business_date=dt.date(2026,10,27))
  rows.append(NS(id=900002001+index,ydental_event_id=event,ydental_patient_id=patient,ydental_amount=decimal.Decimal('1234.56'),ydental_currency_id=currency))
 today=Rows(rows[:len(rows)//2]) if populated else Rows()
 history=Rows(rows[len(rows)//2:]) if populated else Rows()
 context={'can_write':can_write,'today':today,'history':history,'patient':patient,'request':NS(csrf_token=lambda:'P13_FIXTURE_CSRF_NOT_A_REAL_TOKEN'),'revision':'P13_FIXTURE_REVISION_NOT_A_REAL_TOKEN','new_key':lambda:'P13_FIXTURE_KEY_NOT_A_REAL_TOKEN','money':lambda amount,currency:currency.name+' '+format(amount,'.2f')}
 rendered=str(qweb._render(copy.deepcopy(panel),context))
 tree=html.fragment_fromstring(rendered,create_parent='div')
 forms=tree.xpath('.//form')
 shown=bool(can_write and (today or history));assert len(forms)==int(shown)
 expected_ids=[str(fee.id) for fee in (today|history)] if shown else []
 if shown:
  form=forms[0]
  assert form.get('method')=='post' and form.get('action')=='/ydental/settlement/action'
  assert form.xpath('./input[@name="operation"]/@value')==['bill']
  assert form.xpath('.//input[@name="fee_ids"]/@value')==expected_ids
  assert not form.xpath('.//input[@name="fee_ids"][@checked]')
  assert len(form.xpath('.//button[@type="submit"]'))==1
  assert [node.get('name') for node in form.xpath('./input[@type="hidden"]')]==['csrf_token','revision','key','output','operation']
  assert not form.xpath('.//a') and len(tree.xpath('.//details//a'))==1
 components.append({'name':name,'html':rendered,'html_sha256':hashlib.sha256(rendered.encode()).hexdigest(),'layer':'LOADED_QWEB_MEMORY_COMPONENT_FIRST_BILL','real_role_or_business_or_permission_claimed':False,'business_records_created':0,'permission_context_is_fixture':True,'can_write_fixture':can_write,'populated':populated,'long_text':long,'expected_visible':shown,'expected_fee_ids':expected_ids,'synthetic_nonce_literals_not_real_request_tokens':True,'actual_request_tokens_obtained_saved_or_hashed':False})
inheriting_ids=[view.id for view in base._get_inheriting_views()]
env.cr.rollback()
value={'status':'P13_LOADED_QWEB_SETTLEMENT_MEMORY_COMPONENTS_COMPLETE','layer':'ACTUAL_LOADED_QWEB_FIRST_BILL_CONTRACT_AND_MARKED_MEMORY_COMPONENTS_READONLY','candidate_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'identity':identity,'components':components,'native_contracts_by_language':contracts,'loaded_combined_arch_sha256':hashlib.sha256(etree.tostring(combined)).hexdigest(),'actual_inheriting_view_ids':inheriting_ids,'business_dispatches':0,'database_writes':False,'real_role_or_source_or_permission_claimed':False,'actual_request_token_values_obtained_saved_or_hashed':False,'rollback_performed':True,'collected_at_utc':dt.datetime.now(dt.UTC).isoformat()}
output=Path(os.environ['YDENTAL_P12_COMPONENT_OUTPUT']);assert output.parent==private/'runtime'
raw=(json.dumps(value,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode()
with os.fdopen(os.open(output,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
print(json.dumps({'status':value['status'],'components':len(components),'backend_pid':identity[0],'sha256':hashlib.sha256(raw).hexdigest()}))
'''

if __name__ == '__main__':
    raise SystemExit(engine.main())

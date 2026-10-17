"""Prepare a concrete file freeze; not a runtime operation or an authorization."""
import hashlib
import json
from pathlib import Path
import sys
import s10_p0_21_contract as c
name=sys.argv[1] if len(sys.argv)>1 else 'initial-freeze.json'
commit=c.git('rev-parse','HEAD')
files={}
for p in c.ROOT.glob('scripts/s10_p0_21_*.py'):files[str(p.relative_to(c.ROOT))]=c.sha(p.read_bytes())
for p in c.OUT.glob('*.json'):
    if p.name.endswith('freeze.json'):continue
    files[str(p.relative_to(c.ROOT))]=c.sha(p.read_bytes())
proposal=c.read(c.OUT/'proposed-product-contract.json')
for target,f in proposal['files'].items():
    files[f['proposed_file']]=f['sha256']
    if commit!=c.BASE:files[target]=c.sha((c.ROOT/target).read_bytes())
corepaths=['odoo/addons/base/models/ir_binary.py','odoo/addons/base/models/ir_attachment.py','odoo/orm/models.py','odoo/orm/fields_relational.py','odoo/sql_db.py']
for p in corepaths:files['../'+p]=c.sha((c.CORE_ROOT/p).read_bytes())
freeze={'authorization':c.AUTH,'parent':c.BASE,'execution_commit':commit,'core':c.CORE,'branch':c.BRANCH,'round':0,'file_sha256':files,
 'database':{'name':c.NAME,'port':c.PORT,'directory':str(c.RUN),'source':'template0 fresh normal install','OID':'new distinct from full old catalog','cluster':c.CLUSTER},
 'old_business_connections':0,'protected_OIDs':c.PROTECTED,'budgets':{'maintenance':1,'CREATE':1,'install':1,'configure':1,'upgrade':1,'scenario_processes':14,'native_audit_processes':2,'independent_RO_RR_connections':32,'native_pool_max':8,'native_cumulative':'record all, not capped by pool occupancy','HTTP_process':1,'Firefox_process':1,'Firefox_contexts':2,'login_GET':2,'login_POST':2,'switch_POST':2,'settlement_GET':8,'real_UI_pay_POST':1,'real_UI_original_generate_POST':1,'real_UI_original_download_GET':1,'native_attachment_negative_GET':2,'all_HTTP_requests':350,'staff':120,'stores':30,'patients':25,'fees':80,'payments':30,'refunds':20,'native_stock_moves':150,'bill_originals':5,'PDF_renders':12,'S01_audits':10000,'fix_rounds':2},
 'commands':['python scripts/s10_p0_21_apply_product.py','git commit only seven frozen product files; then test-only linear commit; runtime SHA freeze REST before DB','python scripts/s10_p0_21_control.py create','python scripts/s10_p0_21_control.py install','python scripts/s10_p0_21_control.py configure','python scripts/s10_p0_21_control.py <14 frozen scenario names in control.py>','python scripts/s10_p0_21_web.py','python scripts/s10_p0_21_control.py audit-before-upgrade','python scripts/s10_p0_21_control.py upgrade','python scripts/s10_p0_21_control.py audit-after-upgrade','python scripts/s10_p0_21_control.py final-audit'],
 'timeouts':{'install_upgrade':480,'scenario':360,'browser':240,'Web_readiness':60,'statement':15,'lock':3,'readonly_snapshot':150},
 'native_config':{'workers':0,'max_cron_threads':0,'db_maxconn':8,'list_db':False,'exact_dbfilter':True},
 'initial_features':['stock.group_stock_multi_warehouses','stock.group_stock_multi_locations','product.group_product_pricelist'],'mutations':'only legal new-B fixtures/services; no SQL fake state, no executor sudo, no old replay',
 'original_contract':'new default-deny model + immutable private native file; source/store/company/patient-family/export checked each controlled operation; native token/RPC/thumbnail denied; retrieval never renders; version/key/source/template/checksum saved',
 'stop':'Unknown funds/stored economic changes, identity/permissions/native SIGSEGV/out-of-scope defect: STOP, retain complete before/after/diff, readonly tail. No unknown economic re-submit.'}
c.save(c.OUT/name,freeze);print(c.sha((c.OUT/name).read_bytes()))

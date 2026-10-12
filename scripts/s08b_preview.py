"""New guarded synthetic UI fixtures; real clinical document actions are untouched."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import secrets
from types import SimpleNamespace

from odoo import api
from odoo.addons.ydental_treatment_test.tests.common import accepted, price, key
from odoo.addons.ydental_treatment_test.tests.treatment_common import setup, receive

run=Path(os.environ['YDENTAL_S08B_RUN_DIR']);assert run.name==env.cr.dbname and re.fullmatch(r'ydental_s08b_test_[0-9]{14}_[a-f0-9]{8}',env.cr.dbname)
with env.registry.cursor() as cr:
    f=SimpleNamespace(env=api.Environment(cr,1,{}));setup(f)
    f.root['ir.config_parameter'].set_str('ydental_queue.timeout_seconds','600')
    f.admin._grant(f.users['reader'].id,f.stores[0].id,{'medical':'read'})
    f.admin._grant(f.users['manager'].id,f.stores[0].id,{'warehouse':'write'})
    f.admin._grant(f.users['doctor'].id,f.stores[0].id,{'export':'write'})
    f.stores[0].write({'name':'S08-B 合成演示门店甲'});f.stores[1].write({'name':'S08-B 合成演示门店乙'})
    receive(f,20);receive(f,20,'medicine')
    price(f,amount=600);price(f,catalog=f.drug_catalog,amount=10)
    original_price=f.group._operate('snapshot',{'catalog_id':f.catalogs[0].id,'currency_id':f.currency.id,'quantity':1,'source':'S08B-preexisting-demo-'+key(),'policy':'demo_confirmation'},key())
    task=accepted(f);task.ydental_patient_id._save({'name':'合成患者一号'})
    f.users['doctor2']=f.second
    f.users['pharmacy']=f.pharmacist
    credentials={}
    for role,user in f.users.items():
        password=secrets.token_urlsafe(24);user.write({'password':password,'lang':'zh_CN','name':'合成人员 '+role})
        credentials[role]={'login':user.login,'password':password}
    preview={'store':f.stores[0].id,'other_store':f.stores[1].id,'station':f.stations[0][0].id,
        'other_station':f.other_station.id,'task':task.id,'patient':task.ydental_patient_id.id,
        'price_snapshot':original_price['id'], 'price_amount':original_price['amount'],
        'pharmacy_station':f.pharmacy_station.id,'pharmacy_mapping':f.drug_mapping.id,'medicine':f.products['medicine'],'medicine_lot':f.lots['medicine'],'material_lot':f.lots['material'],'uom':f.uom.id,'catalog':f.catalogs[0].id,'exam_mapping':f.mappings[0][2].id,'cbct_mapping':f.mappings[0][3].id,'target_mapping':f.mappings[1][0].id,'start':str(f.start),'end':str(f.end),'doctor':f.users['doctor'].id,'doctor2':f.second.id,'mapping':f.mappings[0][0].id}
    cr.commit() # Own fixture cursor, never a business method.
for name,data in [('access.json',credentials),('preview.json',preview)]:
    path=run/name
    if path.exists():path.rename(run/(name+'.preserved-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')))
    with os.fdopen(os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'w') as h:json.dump(data,h,indent=2)
print(json.dumps({'result':'PASS','scope':'new synthetic UI inputs, no clinical adapter'}))

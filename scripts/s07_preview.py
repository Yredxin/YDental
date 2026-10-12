"""Create new synthetic UI fixtures, preserving all previous inventory facts."""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
import json
import os
from pathlib import Path
import re
import secrets
from types import SimpleNamespace

from odoo import api, fields
from odoo.addons.ydental_inventory_test.tests.common import setup, bind, key
from odoo.addons.ydental_inventory_test.models.adapter import SyntheticSource

run=Path(os.environ['YDENTAL_S07_RUN_DIR']);assert run.name==env.cr.dbname and re.fullmatch(r'ydental_s07_test_[0-9]{14}_[a-f0-9]{8}',env.cr.dbname)
with env.registry.cursor() as cr:
    f=SimpleNamespace(env=api.Environment(cr,1,{}));setup(f)
    stock=f.stock;doctor=bind(f,f.users['doctor'])
    def receipt(lot,q):return stock._operate('receive',{'lot_id':lot,'quantity':q,'uom_id':f.uom.id,'source_key':key(),'reason':'S07 actual synthetic UI receipt'},key())
    receipt(f.lots['medicine'],10);receipt(f.lots['prosthesis'],1)
    pending=doctor._source_action(SyntheticSource(f.users['doctor'].id,f.stores[0].id,key(),'treatment',f.lots['material'],2,f.uom.id,already_performed=True))
    stock._operate('policy',{'near_days':60,'wait_days':0,'low_quantity':3,'reason':'S07 synthetic UI thresholds only'},key())
    history=[]
    for expired in (True,False):
        expiration=fields.Datetime.now()+timedelta(days=-1 if expired else 45)
        lot=stock._operate('lot',{'product_id':f.products['material'],'name':'REWORK-'+key(),
            'expiration':fields.Datetime.to_string(expiration)},key())['id']
        # Simulate time passage via private clock before source creation; never
        # rewrite batch expiry to make bookkeeping succeed.
        when=expiration-timedelta(days=1) if expired else fields.Datetime.now()
        with patch.object(type(stock),'_now',return_value=when):
            original=doctor._source_action(SyntheticSource(f.users['doctor'].id,f.stores[0].id,key(),'treatment',lot,2,f.uom.id,already_performed=True))
        if not expired:stock._operate('lot_edit',{'lot_id':lot,'enabled':False,'reason':'Stopped after original actual event'},key())
        history.append({'expired':expired,'lot':lot,'event':original['id']})
    credentials={}
    for role,user in f.users.items():
        password=secrets.token_urlsafe(24);user.write({'password':password,'lang':'zh_CN'});credentials[role]={'login':user.login,'password':password}
    preview={'store':f.stores[0].id,'other_store':f.stores[1].id,'legal_store':f.stores[2].id,
        'lot':f.lots['medicine'],'material':f.lots['material'],'pending':pending['id'],'prosthesis':f.lots['prosthesis'],
        'unit':f.uom.id,'pack':f.pack.id,'products':f.products,'history':history}
    cr.commit() # Own fixture cursor, never a business method.
for name,data in [('access.json',credentials),('preview.json',preview)]:
    path=run/name
    if path.exists():path.rename(run/(name+'.preserved-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')))
    with os.fdopen(os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'w') as h:json.dump(data,h,indent=2)
print(json.dumps({'result':'PASS','scope':'new synthetic UI fixtures; previous facts preserved'}))

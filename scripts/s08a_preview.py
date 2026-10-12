"""New guarded synthetic UI fixtures; real clinical document actions are untouched."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import secrets
from types import SimpleNamespace

from odoo import api
from odoo.addons.ydental_clinical_test.tests.common import setup, accepted

run=Path(os.environ['YDENTAL_S08A_RUN_DIR']);assert run.name==env.cr.dbname and re.fullmatch(r'ydental_s08a_test_[0-9]{14}_[a-f0-9]{8}',env.cr.dbname)
with env.registry.cursor() as cr:
    f=SimpleNamespace(env=api.Environment(cr,1,{}));setup(f)
    f.root['ir.config_parameter'].set_str('ydental_queue.timeout_seconds','600')
    f.admin._grant(f.users['reader'].id,f.stores[0].id,{'medical':'read'})
    f.admin._grant(f.users['manager'].id,f.stores[0].id,{'warehouse':'write'})
    f.admin._grant(f.users['doctor'].id,f.stores[0].id,{'export':'write'})
    f.stores[0].write({'name':'S08-A 合成演示门店甲'});f.stores[1].write({'name':'S08-A 合成演示门店乙'})
    f.stations[0][0].write({'name':'根管合成演示诊椅甲'});f.other_station.write({'name':'根管合成演示诊椅乙'})
    task=accepted(f);task.ydental_patient_id._save({'name':'合成患者一号'})
    f.users['doctor2']=f.second
    credentials={}
    for role,user in f.users.items():
        password=secrets.token_urlsafe(24);user.write({'password':password,'lang':'zh_CN','name':'合成人员 '+role})
        credentials[role]={'login':user.login,'password':password}
    preview={'store':f.stores[0].id,'other_store':f.stores[1].id,'station':f.stations[0][0].id,
        'other_station':f.other_station.id,'task':task.id,'patient':task.ydental_patient_id.id,
        'doctor':f.users['doctor'].id,'doctor2':f.second.id,'mapping':f.mappings[0][0].id}
    cr.commit() # Own fixture cursor, never a business method.
for name,data in [('access.json',credentials),('preview.json',preview)]:
    path=run/name
    if path.exists():path.rename(run/(name+'.preserved-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')))
    with os.fdopen(os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'w') as h:json.dump(data,h,indent=2)
print(json.dumps({'result':'PASS','scope':'new synthetic UI inputs, no clinical adapter'}))

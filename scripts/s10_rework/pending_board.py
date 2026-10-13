import json,os
from pathlib import Path
from types import SimpleNamespace
from odoo import api
from odoo.exceptions import AccessError
from odoo.addons.ydental_treatment_test.tests.common import key,bind
from odoo.addons.ydental_treatment_test.tests.treatment_common import setup,receive,opened_actual,execute_args
run=Path(os.environ['YDENTAL_S10_RUN_DIR'])
assert run.name==env.cr.dbname
with env.registry.cursor() as cr:
 f=SimpleNamespace(env=api.Environment(cr,1,{}))
 setup(f)
 f.admin._grant(f.users['manager'].id,f.stores[0].id,{'settlement':'write'})
 receive(f)
 treatment,clinical,queue,lease,execution,doc,args=opened_actual(f)
 actual=treatment._operate('execute',execute_args(f,args,actual=True),key())
 assert actual['state']=='pending' and not actual['fee_id']
 manager=bind(f,f.users['manager']).env['ydental.settlement.service']
 board=manager._workbench()
 assert actual['event_id'] in board['pending'].ids
 assert actual['event_id'] not in board['today'].mapped('ydental_event_id').ids
 try:
  bind(f,f.users['none']).env['ydental.settlement.service']._workbench()
 except AccessError: pass
 else: raise AssertionError('Unprivileged board access succeeded')
 print('S10_PENDING_BOARD',json.dumps({'event_id':actual['event_id'],'reason':actual['pending_reason'],'pending_count':len(board['pending']),'fee_id':actual['fee_id']},ensure_ascii=False),flush=True)
 cr.commit()

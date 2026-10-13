import json,os,time
from pathlib import Path
from types import SimpleNamespace
from odoo import api
from odoo.addons.ydental_treatment_test.tests.common import key,bind
run=Path(os.environ['YDENTAL_S10_RUN_DIR']);assert run.name==env.cr.dbname
actor=os.environ['YDENTAL_S10_ACTOR'];assert actor in ('a','b')
fixture=json.loads((run/'concurrency-fixture.json').read_text())
with env.registry.cursor() as cr:
 root=api.Environment(cr,1,{})
 cr.execute('select pg_backend_pid()');pid=cr.fetchone()[0]
 store=root['ydental.access.store'].browse(fixture['store_id'])
 manager=root['res.users'].browse(fixture['manager_id'])
 marker=run/('barrier-'+actor+'.json')
 with marker.open('x') as out:out.write(json.dumps({'backend_pid':pid,'actor':actor})+'\n')
 other=run/('barrier-'+('b' if actor=='a' else 'a')+'.json')
 for _ in range(2400):
  if other.is_file():break
  time.sleep(.05)
 else:raise AssertionError('second PostgreSQL backend did not reach barrier')
 service=bind(SimpleNamespace(root=root,stores=[store]),manager).env['ydental.settlement.service']
 result=service._operate('bill',{'fee_ids':[fixture['fee_id']],'discount':0,'reason':''},key())
 cr.commit()
 (run/('concurrent-'+actor+'.json')).write_text(json.dumps({'actor':actor,'backend_pid':pid,'invoice_id':result['invoice_id'],'amount':result['amount'],'result':result['result']})+'\n')
 print('S10_CONCURRENT_BILL',actor,pid,result,flush=True)

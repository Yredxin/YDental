"""B-shaped task lifetime unique fixture followed by real -u, on a fresh C DB."""
import json
import os
from pathlib import Path
from types import SimpleNamespace
from odoo import api
from odoo.addons.ydental_queue_test.models.adapter import guard
from odoo.addons.ydental_queue_test.tests.common import setup, accepted

guard(env)
run=Path(os.environ['YDENTAL_S06C_RUN_DIR'])
if migration_action=='legacy_seed':
    with env.registry.cursor() as cr:
        f=SimpleNamespace(env=api.Environment(cr,1,{}));setup(f);task=accepted(f)
        task._save({'ydental_missed_count':3})
        row=f.root['ydental.queue.entry'].search([('ydental_task_id','=',task.id)])
        row._save({'ydental_missed_count':0})
        snapshot={k:str(row[k]) for k in ('id','ydental_number','ydental_business_date','ydental_reported_at','state')}
        cr.execute('ALTER TABLE ydental_queue_entry DROP CONSTRAINT ydental_queue_entry_one_task_day')
        cr.execute('ALTER TABLE ydental_queue_entry ADD CONSTRAINT ydental_queue_entry_one_task UNIQUE(ydental_task_id)')
        cr.commit()
        (run/'migration-before.json').write_text(json.dumps(snapshot))
else:
    before=json.loads((run/'migration-before.json').read_text())
    row=env['ydental.queue.entry'].sudo().browse(int(before['id']))
    assert all(str(row[k])==v for k,v in before.items())
    assert row.ydental_missed_count==3
    env.cr.execute("SELECT conname FROM pg_constraint WHERE conrelid='ydental_queue_entry'::regclass")
    names={r[0] for r in env.cr.fetchall()}
    assert 'ydental_queue_entry_one_task' not in names and 'ydental_queue_entry_one_task_day' in names
    result={'result':'PASS','scope':'B-shaped old constraint/row plus real C module upgrade; not full B source install',
            'history_identity_preserved':True,'missed_backfill':True,'new_task_day_unique':True}
    output=Path(__file__).resolve().parents[1]/'docs/evidence/s06c/migration-attempts';output.mkdir(parents=True,exist_ok=True)
    (output/(env.cr.dbname+'.json')).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

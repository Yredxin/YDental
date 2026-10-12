"""Fixed guarded midnight fixture steps for the matching live C browser preview."""
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
from odoo import api
from odoo.addons.ydental_queue_test.models.adapter import guard
from odoo.addons.ydental_queue_test.models.day_adapter import DaySource

guard(env)
p=Path(os.environ['YDENTAL_S06C_RUN_DIR'])
c=json.loads((p/'preview-c.json').read_text())['midnight']
instant=datetime.fromisoformat(c['day'])+timedelta(days=1,minutes={'time_midnight':0,'time_cleanup':10,'time_delayed':30}[migration_action])
with env.registry.cursor() as cr:
    e=api.Environment(cr,c['manager'],{})
    access=e['ydental.access.service'];session=access._session_for_key('s06c-time-fixture-'+str(c['store']))
    access=access._bind(session);access._switch(c['store']);q=access._bind(session).env['ydental.queue.service']
    q._test_day_clock(DaySource(c['store'],instant))
    result={'result':'accepted','local_time':str(instant)}
    if migration_action!='time_midnight':result['cleanup']=q._cleanup_day(e['ydental.access.store'].sudo().browse(c['store']),datetime.fromisoformat(c['day']).date())
    cr.commit()
    print(json.dumps(result))

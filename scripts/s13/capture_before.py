#!/usr/bin/env python3
"""Read-only UX baseline from the explicitly existing S12 process.

This is not a fixed S13 candidate result. Current dirty paths are recorded.
Only normal login/store selection and GETs occur; screenshots exclude login.
"""
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / '.local/s12/verification/browser_effects_settled.py'
spec = importlib.util.spec_from_file_location('s12_before_browser_helpers', SOURCE)
view = importlib.util.module_from_spec(spec)
spec.loader.exec_module(view)
OUT = ROOT / '.local/s13/verification/before'


def write(path, value):
    raw = (json.dumps(value, indent=2, ensure_ascii=False, default=str) + '\n').encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
    return hashlib.sha256(raw).hexdigest()


def owner():
    marker = view.private_json(ROOT / '.local/s12/active.json')
    if marker.get('plan_id') != 'YD-S12-DOCUMENTS-REPORTS-V1' or marker.get('run_id') != '20261024T035253Z-ab4dc7b8a006':
        raise RuntimeError('Explicit old owner mismatch')
    old = sys.modules['http_client'].launcher
    if not old.own_process_matches(marker['supervisor_pid'], marker['supervisor_start_ticks'], expected_script=True):
        raise RuntimeError('Old supervisor birth/script mismatch')
    if old.proc_start_ticks(marker['child_pid']) != marker['child_start_ticks']:
        raise RuntimeError('Old child birth mismatch')
    status = Path('/proc', str(marker['child_pid']), 'status').read_text()
    if int(next(line.split()[1] for line in status.splitlines() if line.startswith('PPid:'))) != marker['supervisor_pid']:
        raise RuntimeError('Old child owner relationship mismatch')
    return {k: marker[k] for k in ('plan_id','run_id','candidate_commit','core_commit','supervisor_pid','supervisor_start_ticks','child_pid','child_start_ticks','database_name','database_oid','cluster_ref')}


def main():
    OUT.mkdir(mode=0o700, parents=True)
    records = {'status':'INCOMPLETE_OLD_SERVICE_READONLY_BASELINE', 'layer':'BROWSER', 'started_at_utc':view.now(),
               'old_service':owner(), 'current_worktree_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
               'current_dirty_paths':subprocess.check_output(['git','status','--porcelain','--untracked-files=all'],cwd=ROOT,text=True).splitlines(),
               'claims_fixed_s13_candidate':False,'business_generation_or_execution':False,'user_hand_verified':False,
               'provenance':'Existing S12 process and database-loaded views; in-progress worktree noted separately. Static assets may reflect current filesystem.',
               'pages':[]}
    write(OUT/'intent.json',records)
    accounts = view.private_json(view.ROLE_PROVIDER)['users']
    jobs = {'settlement': [('/ydental/settlement?patient_id=521','settlement'),
             *[('/ydental/reports?'+urlencode(dict(metric=m,date_from='2026-10-23',date_to='2026-10-24',store_ids='1',currency_id=1)),m)
               for m in ('collections','refunds','receivables')]],
            'doctor':[('/ydental/documents','documents')], 'warehouse':[('/ydental/inventory','inventory')],
            'followup':[('/ydental/followups','followups')]}
    sync = view.import_browser()
    with sync() as pw:
        browser=pw.chromium.launch(headless=True,executable_path=str(view.CHROMIUM))
        try:
            for alias,pages in jobs.items():
                context=browser.new_context(locale='zh-CN',timezone_id='UTC',viewport={'width':1366,'height':768})
                observer=view.Observer(context);page=context.new_page()
                auth=view.login(page,accounts[alias],accounts[alias]['id']);selected=view.switch_store(page,1)
                for width,height in ((1366,768),(1440,900)):
                    page.set_viewport_size({'width':width,'height':height})
                    for path,label in pages:
                        owner()
                        item=view.open_page(page,path,OUT,f'{alias}-{label}-{width}x{height}')
                        item.update(alias=alias,uid=auth['uid'],store=selected['store_id'],viewport={'width':width,'height':height},
                                    dimensions=page.evaluate('() => ({scrollWidth:document.documentElement.scrollWidth,clientWidth:document.documentElement.clientWidth,devicePixelRatio:devicePixelRatio})'))
                        records['pages'].append(item)
                context.close()
        finally:
            browser.close()
    records.update(status='OLD_S12_SERVICE_READONLY_BASELINE_CAPTURED',finished_at_utc=view.now(),owner_after=owner())
    digest=write(OUT/'result.json',records)
    print(json.dumps({'status':records['status'],'pages':len(records['pages']),'sha256':digest,'output':str((OUT/'result.json').relative_to(ROOT))}))


if __name__=='__main__':
    main()

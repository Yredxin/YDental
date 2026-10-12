"""Real Firefox S06C UI evidence on a recorded isolated preview only."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from urllib.parse import urlsplit

# Reuse only the already provisioned process-local browser assets. No install.
_BROWSER_DEPS = Path(__file__).resolve().parents[1] / '.local/s00-b-deps'
if (_BROWSER_DEPS / 'verify-lib/playwright/__init__.py').is_file():
    sys.path.insert(0, str(_BROWSER_DEPS / 'verify-lib'))
    os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH', str(_BROWSER_DEPS / 'browsers'))
    os.environ.setdefault('LD_LIBRARY_PATH', str(_BROWSER_DEPS / 'browser-libs/usr/lib/x86_64-linux-gnu'))
    os.environ.setdefault('FONTCONFIG_FILE', str(_BROWSER_DEPS / 'browser-fonts.conf'))

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]


def require(condition, reason):
    if not condition:
        raise RuntimeError(reason)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', required=True)
    parser.add_argument('--port', type=int, default=18136)
    args = parser.parse_args()
    require(re.fullmatch(r'ydental_s06c_test_[0-9]{14}_[a-f0-9]{8}', args.db), 'Database name refused')
    require(18000 <= args.port <= 18999, 'Isolated port refused')
    run = ROOT / '.local' / args.db
    require(not run.is_symlink(), 'Symlink run refused')
    metadata = json.loads((run / 'database.json').read_text())
    require(metadata['database'] == args.db and metadata['port'] == args.port and
            metadata['cluster'] == '7694897083368259627' and metadata['endpoint'] == {
                'host': '127.0.0.1', 'port': '5432', 'user': 'odoo'}, 'Preview identity mismatch')
    require(sha(run / 'odoo.conf') == metadata['config_sha256'], 'Runtime config changed')
    pid = int((run / 'serve.pid').read_text())
    require(str(run / 'odoo.conf').encode() in Path('/proc/%s/cmdline' % pid).read_bytes().split(b'\0'), 'Preview PID mismatch')
    require(not any(os.environ.get(k) for k in ('MOZ_DISABLE_CONTENT_SANDBOX', 'MOZ_DISABLE_RDD_SANDBOX',
        'MOZ_DISABLE_GMP_SANDBOX', 'WEBKIT_DISABLE_SANDBOX_THIS_IS_DANGEROUS', 'DEBUG', 'PWDEBUG')), 'Unsafe browser overrides refused')
    credentials = run / 'access-c.json'
    require(not credentials.is_symlink() and stat.S_IMODE(credentials.stat().st_mode) == 0o600 and
            credentials.stat().st_uid == os.getuid(), 'Private credentials permission mismatch')
    access = json.loads(credentials.read_text())
    preview = json.loads((run / 'preview-c.json').read_text())
    commit = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
    require(not subprocess.check_output(['git', '-C', str(ROOT), 'status', '--porcelain', '--',
        'ydental_queue', 'ydental_queue_test', 'scripts/s06c*'], text=True), 'Commit implementation and verification first')
    evidence = ROOT / 'docs/evidence/s06c/browser-attempts' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    evidence.mkdir(parents=True)
    result = {'scope': 'S06-B real queue, unscheduled workstation leases and actual start UI', 'database': args.db, 'tested_commit': commit,
              'browser': 'Firefox', 'sandbox': 'default, no overrides', 'checks': [], 'screenshots': []}
    sensitive = {str(v[k]) for v in access.values() for k in ('login', 'password')}
    base = 'http://127.0.0.1:%s' % args.port

    def check(name, success):
        require(success, name)
        result['checks'].append({'check': name, 'result': 'PASS'})

    def screenshot(page, context, name):
        sensitive.update(c['value'] for c in context.cookies() if re.search('session|csrf|token|auth', c['name'], re.I))
        visible = page.locator('body').inner_text()
        require(not any(s and s in visible for s in sensitive), 'Visible credential, screenshot refused')
        require(page.locator('input[type=password]:visible').count() == 0, 'Visible password field')
        require(not re.search(r'(?:csrf_token|session_id|authorization|password)\s*[:=]', visible, re.I), 'Visible sensitive label')
        target = evidence / name
        page.screenshot(path=str(target), full_page=True)
        require(not any(s.encode() in target.read_bytes() for s in sensitive if s), 'Screenshot credential scan failed')
        result['screenshots'].append({'path': str(target.relative_to(ROOT)), 'sha256': sha(target)})

    with sync_playwright() as playwright:
        browser=playwright.firefox.launch(headless=True)
        result['browser_version']=browser.version;errors=[]
        contexts=[]
        def context():
            ctx=browser.new_context(viewport={'width':1360,'height':1000});contexts.append(ctx)
            ctx.route('**/*',lambda route:route.continue_() if urlsplit(route.request.url).hostname=='127.0.0.1' and urlsplit(route.request.url).port==args.port else route.abort())
            ctx.on('page',lambda page:page.on('pageerror',lambda error:errors.append(str(error))))
            return ctx
        def login(kind,role):
            ctx=context();page=ctx.new_page();credentials=access[kind+'_'+role]
            page.goto(base+'/web/login?redirect=/ydental/access',wait_until='domcontentloaded')
            page.locator('input[name=login]').fill(credentials['login']);page.locator('input[name=password]').fill(credentials['password'])
            page.locator('button[type=submit]').click();page.wait_for_url(lambda url:'/web/login' not in url)
            page.goto(base+'/ydental/access',wait_until='domcontentloaded')
            selected=page.evaluate('''async store_id=>{const body=new URLSearchParams({operation:'switch',revision:document.querySelector('[name=revision]').value,
                csrf_token:document.querySelector('[name=csrf_token]').value,output:'json',payload:JSON.stringify({store_id})});return (await fetch('/ydental/access/action',{method:'POST',body})).json();}''',preview[kind]['store'])
            require(type(selected.get('revision')) is int,'store selected')
            page.goto(base+'/ydental/queue',wait_until='domcontentloaded');page.wait_for_timeout(300)
            return ctx,page
        def submit(page,selector,success=True):
            form=page.locator(selector)
            if success:
                with page.expect_navigation(wait_until='domcontentloaded'):
                    with page.expect_response(lambda response:'/ydental/queue/action' in response.url or '/ydental/intake/action' in response.url) as response:
                        form.locator('button[type=submit]').click()
                require(response.value.status==200,'form accepted: '+selector)
                page.wait_for_timeout(200)
            else:
                with page.expect_response(lambda response:'/ydental/queue/action' in response.url or '/ydental/intake/action' in response.url) as response:form.locator('button[type=submit]').click()
                require(response.value.status>=400,'form refused: '+selector)
        def button(page,selector):
            with page.expect_navigation(wait_until='domcontentloaded'):
                with page.expect_response(lambda response:'/ydental/queue/action' in response.url) as response:page.locator(selector).click()
            require(response.value.status==200,'button accepted '+selector);page.wait_for_timeout(200)
        def business(page,c,state,success=True):
            form=page.locator('[data-business-area="%s"] [data-queue-form=business]'%c['area'])
            form.locator('select[name=state]').select_option(state);form.locator('[name=reason]').fill('S06C Firefox explicit business reason')
            submit(page,'[data-business-area="%s"] [data-queue-form=business]'%c['area'],success)
        def taskrow(page,c,field='task'):return page.locator('[data-task="%s"]'%c[field]).last
        def pending(c):return '[data-pending-task="%s"]'%c['pending']
        def time_step(step):
            log=run/('browser-'+step+'.log')
            with log.open('w') as handle:
                r=subprocess.run([str(ROOT.parent/'.venv/bin/python'),str(ROOT/'scripts/s06c.py'),step,'--db',args.db,'--port',str(args.port)],stdout=handle,stderr=subprocess.STDOUT)
            require(r.returncode==0,'guarded server clock/cleanup '+step)
            result.setdefault('clock_commands',[]).append({'step':step,'exit_code':r.returncode,'log_sha256':sha(log)})
        try:
            c=preview['business'];mc,manager=login('business','manager');fc,front=login('business','frontdesk');dc,doctor=login('business','doctor')
            check('open existing ordinary report is waiting',taskrow(front,c).locator('.queue-state').inner_text()=='waiting')
            button(doctor,'[data-operation=enter][data-station="%s"]'%c['station'])
            business(manager,c,'draining');check('stop ordinary reporting UI becomes draining',manager.locator('[data-business-area="%s"] .business-state'%c['area']).inner_text()=='draining')
            submit(front,pending(c)+' [data-queue-form=report]',False);check('draining rejects new ordinary report',front.locator('#queue-result').inner_text()!='')
            business(manager,c,'closed',False);check('nonempty close rejected',manager.locator('[data-business-area="%s"] .business-state'%c['area']).inner_text()=='draining')
            screenshot(manager,mc,'01-draining-nonempty-close-refused.png')
            button(doctor,'[data-operation=call]');check('draining existing task can call',taskrow(doctor,c).locator('.queue-state').inner_text()=='calling')
            button(doctor,'[data-operation=start][data-entry="%s"]'%c['entry']);check('draining existing call can start',taskrow(doctor,c).locator('.queue-state').inner_text()=='serving')
            manager.reload();business(manager,c,'closed');check('cleared waiting and calling allows closed despite serving',manager.locator('[data-business-area="%s"] .business-state'%c['area']).inner_text()=='closed')
            screenshot(manager,mc,'02-closed-serving-continues.png')
            submit(doctor,'[data-queue-form=handover]');check('B save handover continues under closed',doctor.locator('[data-queue-form=handover]').count()==0)
            # Ordinary call is refused with no eligible permitted task.
            with doctor.expect_response(lambda r:'/ydental/queue/action' in r.url) as response:doctor.locator('[data-operation=call]').click()
            check('closed ordinary call denied',response.value.status==409)
            front.reload();submit(front,pending(c)+' [data-queue-form=report]',False)
            append=front.locator(pending(c)+' [data-queue-form=append]');append.locator('[name=reason]').fill('S06C Firefox closed explicit append');submit(front,pending(c)+' [data-queue-form=append]')
            submit(front,pending(c)+' [data-queue-form=report]');doctor.reload();button(doctor,'[data-operation=call]')
            check('closed valid append can report and call',taskrow(doctor,c,'pending').locator('.queue-state').inner_text()=='calling')
            screenshot(doctor,dc,'03-closed-append-calling.png')
            manager.reload()
            with manager.expect_response(lambda r:'/ydental/queue/action' in r.url) as response:manager.locator('[data-business-area="%s"] [data-queue-form=screen_create] button'%c['area']).click()
            credential=response.value.json();sensitive.add(credential['token'])
            sc=context();screen=sc.new_page();screen.goto(base+'/ydental/queue/screen?lang=zh_CN#token='+credential['token'],wait_until='domcontentloaded')
            screen.wait_for_function("document.querySelector('.o_ydental_queue_screen').dataset.version !== undefined")
            screen.wait_for_function("document.querySelector('.o_ydental_queue_screen').dataset.websocket==='open'")
            check('native Odoo WebSocket connected',True)
            text=screen.locator('tbody').inner_text();station=doctor.locator('[data-station="%s"] td'%c['station']).first.inner_text()
            source_station=doctor.locator('[data-station="%s"] td'%c['source_station']).first.inner_text()
            check('screen only masked name and actual calling station', '李***' in text and '李合成患者' not in text and station in text and source_station not in text)
            check('screen has no raw task patient phone clinical or money fields',len(screen.locator('thead th').all_text_contents())==4 and str(c['pending']) not in screen.locator('tbody td').all_text_contents())
            voice=screen.evaluate("""async () => {const {QueueScreen}=await import('/ydental_queue/static/src/screen/screen.js');const s=new QueueScreen(document.querySelector('.o_ydental_queue_screen'),'');return s.voiceText({number:'Q',station:document.querySelector('tbody tr td:last-child').textContent});}""")
            check('voice text points at actual calling station',voice=='Q / '+station)
            screenshot(screen,sc,'04-area-screen-masked-actual-station.png')
            previous=int(screen.locator('.o_ydental_queue_screen').get_attribute('data-version'))
            called=taskrow(doctor,c,'pending').get_attribute('data-entry');button(doctor,'[data-operation=missed][data-entry="%s"]'%called)
            screen.wait_for_function("!document.querySelector('tbody').textContent.includes('calling')")
            latest=int(screen.locator('.o_ydental_queue_screen').get_attribute('data-version'));check('native bus update snapshot retracts call',latest>previous)
            screen.evaluate("""v=>document.querySelector('.o_ydental_queue_screen').dispatchEvent(new CustomEvent('ydental:version',{detail:{version:v}}))""",previous)
            screen.wait_for_timeout(300);check('old version ignored without withdrawn call replay','calling' not in screen.locator('tbody').inner_text())
            screen.evaluate("""v=>document.querySelector('.o_ydental_queue_screen').dispatchEvent(new CustomEvent('ydental:version',{detail:{version:v+9}}))""",latest)
            screen.wait_for_timeout(300);check('version gap forces database snapshot','calling' not in screen.locator('tbody').inner_text())
            screen.evaluate("document.querySelector('.o_ydental_queue_screen').dispatchEvent(new CustomEvent('ydental:reconnect'))")
            screen.wait_for_timeout(300);check('reconnect full snapshot keeps retracted call absent','calling' not in screen.locator('tbody').inner_text())
            check('settlement never appears in queue screen','settlement' not in screen.locator('tbody').inner_text().lower())
            screenshot(screen,sc,'05-retract-old-version-reconnect.png')
            manager.reload();submit(manager,'[data-queue-form=screen_revoke]:has([name=credential_id][value="%s"])'%credential['credential_id'])
            screen.wait_for_function("document.querySelector('.o_ydental_queue_screen').dataset.denied==='yes'")
            check('credential revoked next request empties and rejects screen',screen.locator('tbody tr').count()==0)
            screenshot(screen,sc,'06-token-revoked.png')
            c=preview['midnight'];tc,tm=login('midnight','manager');vc,vd=login('midnight','doctor')
            check('2355 real execution visible serving',taskrow(vd,c).locator('.queue-state').inner_text()=='serving')
            time_step('time_midnight');vd.reload();check('0000 execution remains original serving',taskrow(vd,c).locator('.queue-state').inner_text()=='serving')
            screenshot(vd,vc,'07-midnight-serving-continues.png')
            time_step('time_cleanup');vd.reload();check('0010 actual execution not terminated',taskrow(vd,c).locator('.queue-state').inner_text()=='serving')
            check('0010 yesterday calling is terminal history',vd.locator('[data-entry="%s"] .queue-state'%c['old_call']).inner_text()=='day_closed')
            check('0010 yesterday waiting is terminal history',vd.locator('[data-task="%s"] .queue-state'%c['waiting_task']).last.inner_text()=='day_closed')
            screenshot(vd,vc,'08-0010-old-queue-ended-serving-kept.png')
            tm.reload();business(tm,c,'open');vd.reload();check('today open does not resurrect yesterday queue',vd.locator('[data-entry="%s"] .queue-state'%c['old_call']).inner_text()=='day_closed')
            time_step('time_delayed');vd.reload();check('0030 idempotent rerun keeps yesterday terminal',vd.locator('[data-entry="%s"] .queue-state'%c['old_call']).inner_text()=='day_closed')
            check('Chinese workspace readable', '工位' in vd.locator('body').inner_text())
            screenshot(vd,vc,'09-today-open-delayed-cleanup.png')
            check('zero Firefox pageerrors',not errors);result.update(result='PASS',pageerror_count=len(errors),errors=[])
        finally:
            result.setdefault('result','FAIL_OR_INTERRUPTED');result.setdefault('pageerror_count',len(errors));result.setdefault('errors',errors)
            (evidence/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
            browser.close()
    print(json.dumps({'result':result['result'],'checks':len(result['checks']),'screenshots':len(result['screenshots']),'pageerrors':len(errors)}))


if __name__=='__main__':main()

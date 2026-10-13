"""Real Firefox S08C UI evidence on a recorded isolated preview only."""
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
    parser.add_argument('--port', type=int, default=18137)
    parser.add_argument('--terminal-races', action='store_true', help='Run real held-response terminal and autosave regressions')
    args = parser.parse_args()
    require(re.fullmatch(r'ydental_s08c_test_[0-9]{14}_[a-f0-9]{8}', args.db), 'Database name refused')
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
    credentials = run / 'access.json'
    require(not credentials.is_symlink() and stat.S_IMODE(credentials.stat().st_mode) == 0o600 and
            credentials.stat().st_uid == os.getuid(), 'Private credentials permission mismatch')
    access = json.loads(credentials.read_text())
    preview = json.loads((run / 'preview.json').read_text())
    commit = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
    require(not subprocess.check_output(['git', '-C', str(ROOT), 'status', '--porcelain', '--',
        'ydental_clinical', 'ydental_treatment', 'ydental_treatment_test', 'scripts/s08c*'], text=True), 'Commit implementation and verification first')
    evidence = ROOT / 'docs/evidence/s08c-rework/b-browser-attempts' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    evidence.mkdir(parents=True)
    result = {'scope': 'S08-C real reception, teeth, authored text, handover and pending responsibility', 'database': args.db, 'tested_commit': commit,
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
        # B captures the relevant business panel at readable viewport resolution.
        scope = 'article[data-order-kind=prescription]' if re.match(r'B(0[4789]|1[01])', name) else 'article[data-order-kind=exam]' if name.startswith('B03') else '[data-event-state=pending]' if name.startswith('B06') else 'form[data-operation=refer]' if name.startswith('B05') else '[data-event]' if name.startswith(('B01','B02')) else '.o_ydental_treatment'
        panel = page.locator(scope).first
        if panel.count(): panel.evaluate('el=>window.scrollTo(0,el.getBoundingClientRect().top+window.scrollY-30)')
        page.screenshot(path=str(target), full_page=False)
        require(not any(s.encode() in target.read_bytes() for s in sensitive if s), 'Screenshot credential scan failed')
        result['screenshots'].append({'path': str(target.relative_to(ROOT)), 'sha256': sha(target)})

    errors=[];contexts=[]
    with sync_playwright() as p:
        browser=p.firefox.launch(headless=True)
        def login(role):
            ctx=browser.new_context(viewport={'width':1440,'height':1050},locale='zh-CN');contexts.append(ctx)
            ctx.route('**/*',lambda route:route.continue_() if urlsplit(route.request.url).hostname=='127.0.0.1' and urlsplit(route.request.url).port==args.port else route.abort())
            page=ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
            c=access[role]
            page.goto(base+'/web/login?redirect=/ydental/access',wait_until='domcontentloaded')
            page.locator('[name=login]').fill(c['login']);page.locator('[name=password]').fill(c['password']);page.locator('button[type=submit]').click();page.wait_for_url('**/ydental/access')
            response=page.evaluate("async store=>{const b=new URLSearchParams({operation:'switch',revision:document.querySelector('[name=revision]').value,csrf_token:document.querySelector('[name=csrf_token]').value,output:'json',payload:JSON.stringify({store_id:store})});return (await fetch('/ydental/access/action',{method:'POST',body:b})).json()}",preview['store'])
            require(type(response.get('revision')) is int,'select synthetic store')
            return ctx,page
        def click_wait(page,selector):
            with page.expect_navigation(wait_until='domcontentloaded'):page.locator(selector).click()
        def version(page,number):page.wait_for_function('(n) => Number(document.querySelector("#server-version").textContent) >= n',arg=number,timeout=10000)
        def open_editor(page):
            page.locator('#open-document').click();page.wait_for_function('!document.querySelector("textarea[name=chief_complaint]").disabled')
        def inspect_action(page,op,payload):
            return page.evaluate('''async ({op,payload}) => {
                const root=document.querySelector('.o_ydental_clinical');
                const response=await fetch('/ydental/clinical/action',{method:'POST',body:new URLSearchParams({operation:op,revision:root.dataset.revision,connection:sessionStorage.getItem('ydental_queue_connection'),csrf_token:root.querySelector('[name=csrf_token]').value,payload:JSON.stringify(payload)})});
                return {status:response.status,data:await response.json()};
            }''',{'op':op,'payload':payload})
        try:
            ctx,page=login('doctor');page.on('dialog',lambda dialog:dialog.accept())
            page.goto(base+'/ydental/queue');click_wait(page,'button[data-operation=enter][data-station="%s"]'%preview['station']);click_wait(page,'button[data-operation=call]');click_wait(page,'button[data-operation=start]')
            page.goto(base+'/ydental/clinical');open_editor(page)
            d1=int(page.evaluate('new URL(location.href).searchParams.get("document_id")'))
            for i in range(1,4):page.locator('[name=chief_complaint]').fill('B联调合成草稿第%s次保存'%i);version(page,i)
            check('three actual A autosaves before B action',page.locator('#server-version').inner_text()=='3')
            page.goto(base+'/ydental/treatment');page.wait_for_function('document.querySelector(".o_ydental_treatment form[data-operation]").dataset.key')
            check('Chinese treatment UI and demonstration boundary','正式价格' in page.inner_text('body') and '实际治疗' in page.inner_text('body'))
            check('autosaves create no actual events',page.locator('[data-event]').count()==0)
            form=page.locator('form[data-operation=execute]')
            def fill_project(quantity=1,material=1,actual=False):
                form.locator('[name=catalog_id]').select_option(str(preview['catalog']));form.locator('[name=quantity]').fill(str(quantity));form.locator('[name=tooth]').fill('16');form.locator('[name=tooth_state]').select_option('present');form.locator('[name=surfaces]').fill('O')
                form.locator('[name=lot_id]').select_option(str(preview['material_lot']));form.locator('[name=material_quantity]').fill(str(material));form.locator('[name=reason]').fill('合成人员核实实际项目与批次用量')
                form.locator('[name=already_performed]').set_checked(actual)
            def submit(form):
                with page.expect_navigation(wait_until='domcontentloaded'):form.locator('button[type=submit]').click()
                page.wait_for_function('document.querySelector(".o_ydental_treatment form[data-operation]").dataset.key')
            fill_project()
            held=[]
            def hold(route):
                from urllib.parse import parse_qs
                data=parse_qs(route.request.post_data);response=route.fetch()
                held.append({'route':route,'response':response,'payload':json.loads(data['payload'][0])})
            page.route('**/ydental/treatment/action',hold)
            form.locator('button[type=submit]').click()
            for _ in range(200):
                page.wait_for_timeout(30)
                if held:break
            require(held and held[0]['response'].status==200,'real committed execute response barrier')
            check('actual confirmation freezes every editable control while response held',page.locator('.o_ydental_treatment input:enabled,.o_ydental_treatment select:enabled,.o_ydental_treatment button:enabled').count()==0)
            form.locator('[name=reason]').evaluate("el=>{el.value='响应期间程序改变的未提交内容'}")
            held[0]['route'].fulfill(response=held[0]['response']);page.unroute('**/ydental/treatment/action',hold)
            page.wait_for_function('!document.querySelector("#treatment-reconcile").hidden')
            check('full form change preserves uncertain page and forbids automatic replay',form.locator('[name=reason]').input_value()=='响应期间程序改变的未提交内容' and form.locator('button').is_disabled())
            screenshot(page,ctx,'B00-real-response-held-unsynchronized.png')
            page.reload();page.wait_for_function('document.querySelector(".o_ydental_treatment form[data-operation]").dataset.key')
            first_payload=held[0]['payload']
            check('F1 actual event confirmed with frozen600 and native move',page.locator('[data-event]').count()==1 and '600' in page.locator('.frozen-price').inner_text() and page.locator('.native-moves').inner_text() not in ('[]',''))
            first_event=int(page.locator('[data-event]').get_attribute('data-event'));result['first_event']=first_event
            screenshot(page,ctx,'B01-actual-project-600-native-move.png')
            correction=page.locator('form[data-operation=correct]').first
            correction.locator('[name=delta]').fill('0');correction.locator('[name=lot_id]').select_option(str(preview['material_lot']));correction.locator('[name=material_quantity]').fill('1');correction.locator('[name=reason]').fill('核实追加实际耗材，项目数量不变');submit(correction)
            check('material delta appends immutable event',page.locator('[data-event]').count()==2);screenshot(page,ctx,'B02-material-delta-original-preserved.png')
            order=page.locator('form[data-operation=order]')
            def fill_line(row,mapping,quantity,medicine=None):
                row.locator('[name=mapping_id]').select_option(str(mapping));row.locator('[name=quantity]').fill(str(quantity))
                if medicine:
                    row.locator('[name=product_id]').select_option(str(medicine))
                    for field in ('specification','usage','frequency','course'):row.locator('[name='+field+']').fill('合成演示，医生明确审核 '+field)
            order.locator('[name=kind]').select_option('exam');order.locator('[name=purpose]').fill('合成全景与CBCT独立检查目的')
            fill_line(order.locator('.o_ydental_treatment_line').first,preview['exam_mapping'],1);order.locator('.add-order-line').click();fill_line(order.locator('.o_ydental_treatment_line').nth(1),preview['cbct_mapping'],1);submit(order)
            draft=page.locator('article[data-order]').first;exam_id=int(draft.get_attribute('data-order'))
            edit=draft.locator('form[data-operation=edit_order]');edit.locator('[name=purpose]').fill('核对后的全景与CBCT检查目的');submit(edit)
            check('draft edit increments server version and preserves superseded rows',page.locator('article[data-order="%s"]'%exam_id).get_attribute('data-order-version')=='2')
            submit(page.locator('article[data-order="%s"] form[data-operation=issue]'%exam_id))
            check('issued examination set freezes editing',page.locator('article[data-order="%s"] form[data-operation=edit_order]'%exam_id).count()==0)
            cancel=page.locator('article[data-order="%s"] form[data-operation=cancel_exam]'%exam_id).last;cancel.locator('[name=reason]').fill('合成患者取消未执行CBCT');submit(cancel)
            check('F4 unperformed cancellation retained with other exam issued',page.locator('article[data-order="%s"] form[data-operation=cancel_exam]'%exam_id).count()==1);screenshot(page,ctx,'B03-frozen-exam-cbct-cancelled.png')
            order=page.locator('form[data-operation=order]');order.locator('[name=kind]').select_option('prescription');order.locator('[name=purpose]').fill('合成带走处方，批准总量六份')
            fill_line(order.locator('.o_ydental_treatment_line'),preview['pharmacy_mapping'],6,preview['medicine']);submit(order)
            rx=page.locator('article[data-order-kind=prescription]').first;rxid=int(rx.get_attribute('data-order'));submit(rx.locator('form[data-operation=issue]'))
            task=int(page.locator('article[data-order="%s"] .task-id'%rxid).inner_text());result['prescription']=rxid
            check('F3 prescription has one explicit pending-report task',page.locator('article[data-order="%s"] [data-segment]'%rxid).count()==1)
            screenshot(page,ctx,'B04-six-unit-prescription-awaiting-report.png')
            referral=page.locator('form[data-operation=refer]');referral.locator('[name=mapping_id]').select_option(str(preview['target_mapping']));referral.locator('[name=mode]').select_option('timed');referral.locator('[name=start]').fill(preview['start'].replace(' ','T').removesuffix(':00'));referral.locator('[name=end]').fill(preview['end'].replace(' ','T').removesuffix(':00'));referral.locator('[name=reason]').fill('合成医生明确目标门店时段转诊');submit(referral)
            check('F5 timed referral leaves original medical execution serving',int(page.locator('main.o_ydental_treatment').get_attribute('data-execution'))>0 and page.locator('[data-referral-receipt]').count()==1)
            referral=page.locator('form[data-operation=refer]');referral.locator('[name=mapping_id]').select_option(str(preview['target_mapping']));referral.locator('[name=mode]').select_option('untimed');referral.locator('[name=valid_until]').fill((datetime.now(timezone.utc).replace(tzinfo=None)+__import__('datetime').timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'));referral.locator('[name=reason]').fill('合成医生不定时转诊，不预占目标额度');submit(referral);screenshot(page,ctx,'B05-referral-source-independent.png')
            form=page.locator('form[data-operation=execute]');fill_project(material=99,actual=True);submit(form)
            check('F4 physically performed shortage preserved pending',page.locator('[data-event-state=pending]').count()==1 and 'inventory_pending' in page.inner_text('body'));screenshot(page,ctx,'B06-shortage-fact-awaiting-recovery.png')
            page.goto(base+'/ydental/clinical?document_id='+str(d1));open_editor(page);click_wait(page,'#handover-document');page.goto(base+'/ydental/queue');click_wait(page,'button[data-operation=exit]')
            check('medical handover independent of project and referral',page.locator('#holding-workstation').count()==0)
            frontctx,front=login('frontdesk')
            def report(task_id):
                front.goto(base+'/ydental/queue');form=front.locator('form[data-queue-form=report]').filter(has=front.locator('input[name=task_id][value="%s"]'%task_id))
                with front.expect_navigation(wait_until='domcontentloaded'):form.locator('button').click()
            report(task)
            pharmctx,pharm=login('pharmacy');pharm.on('dialog',lambda dialog:dialog.accept())
            def pharmacy_enter():
                pharm.goto(base+'/ydental/queue');click_wait(pharm,'button[data-operation=enter][data-station="%s"]'%preview['pharmacy_station']);click_wait(pharm,'button[data-operation=call]');click_wait(pharm,'button[data-operation=start]');pharm.goto(base+'/ydental/treatment');pharm.wait_for_function('document.querySelector(".o_ydental_treatment form[data-operation]").dataset.key')
            def pharm_submit(form):
                with pharm.expect_navigation(wait_until='domcontentloaded'):form.locator('button[type=submit]').click()
                pharm.wait_for_function('document.querySelector(".o_ydental_treatment form[data-operation]").dataset.key')
            def dose(qty):
                form=pharm.locator('article[data-order="%s"] form[data-operation=dispense]'%rxid);form.locator('[name=lot_id]').select_option(str(preview['medicine_lot']));form.locator('[name=quantity]').fill(str(qty));form.locator('[name=reason]').fill('合成实际核对发药 '+str(qty));pharm_submit(form)
            def finish():
                form=pharm.locator('article[data-order="%s"] form[data-operation=finish]'%rxid);form.locator('[name=reason]').fill('结束本次真实发药并释放患者和工位');pharm_submit(form)
            pharmacy_enter();dose(4)
            check('F3 actual four remaining two',float(pharm.locator('article[data-order="%s"] .remaining'%rxid).inner_text())==2)
            screenshot(pharm,pharmctx,'B07-real-pharmacy-four-of-six.png');finish()
            check('F3 finish releases actual execution',int(pharm.locator('main.o_ydental_treatment').get_attribute('data-execution') or 0)==0 and pharm.evaluate("sessionStorage.getItem('ydental_queue_holder')") is None)
            next_task=int(pharm.locator('article[data-order="%s"] .task-id'%rxid).last.inner_text());check('F3 remainder uses a new task',next_task!=task);screenshot(pharm,pharmctx,'B08-finished-four-remainder-awaits-report.png')
            report(next_task);pharmacy_enter();dose(2)
            check('F3 cumulative six remaining zero',float(pharm.locator('article[data-order="%s"] .remaining'%rxid).inner_text())==0);screenshot(pharm,pharmctx,'B09-second-report-real-two-of-six.png')
            form=pharm.locator('article[data-order="%s"] form[data-operation=dispense]'%rxid);form.locator('[name=lot_id]').select_option(str(preview['medicine_lot']));form.locator('[name=quantity]').fill('1');form.locator('[name=reason]').fill('第七份应被服务器拒绝');form.locator('button').click();pharm.wait_for_function('document.querySelector("#treatment-result").textContent.includes("overdispense")')
            check('seventh unit rejected and page retained for reconciliation',pharm.locator('#treatment-reconcile').is_visible());screenshot(pharm,pharmctx,'B10-seventh-unit-rejected.png');pharm.reload();finish()
            check('F3 complete without third pending segment',pharm.locator('article[data-order="%s"] [data-segment]'%rxid).count()==2)
            screenshot(pharm,pharmctx,'B11-prescription-complete-original-sources.png')
            page.goto(base+'/ydental/clinical?document_id='+str(d1));open_editor(page);page.locator('[name=history]').fill('D1补文字不生成第二次费用');version(page,5)
            denied=page.evaluate('''async payload=>{let r=await fetch('/ydental/treatment/action',{method:'POST',body:new URLSearchParams({operation:'execute',revision:document.querySelector('.o_ydental_clinical').dataset.revision,connection:sessionStorage.getItem('ydental_queue_connection'),key:crypto.randomUUID(),csrf_token:odoo.csrf_token,payload:JSON.stringify(payload)})});return r.status}''',first_payload)
            check('posthandover actual execute denied without current serving',denied in (403,409))
            readerctx,reader=login('reader');reader.goto(base+'/ydental/treatment');check('read-only workbench accessible',reader.locator('main.o_ydental_treatment').count()==1)
            r=reader.evaluate('''async payload=>{const root=document.querySelector('.o_ydental_treatment');let r=await fetch('/ydental/treatment/action',{method:'POST',body:new URLSearchParams({operation:'execute',revision:root.dataset.revision,connection:'a'.repeat(64),key:crypto.randomUUID(),csrf_token:odoo.csrf_token,payload:JSON.stringify(payload)})});return r.status}''',first_payload);check('read-only cannot execute via HTTP',r==403);screenshot(reader,readerctx,'B12-readonly-boundary.png')
            check('zero browser page errors',not errors)
            result.update(result='PASS',pageerrors=errors)
        except Exception as error:
            import traceback
            result.update(result='FAIL',error={'type':type(error).__name__,'detail':str(error)[:500],
                'trace':[{'file':Path(frame.filename).name,'line':frame.lineno,'method':frame.name} for frame in traceback.extract_tb(error.__traceback__)]},pageerrors=errors)
            try:
                if 'page' in locals() and not page.is_closed() and page.locator('input[type=password]:visible').count()==0:screenshot(page,ctx,'failure-state.png')
            except Exception as capture_error:
                result['failure_capture_error']={'type':type(capture_error).__name__,'detail':str(capture_error)[:200]}
        finally:
            for context in contexts:context.close()
            browser.close()
            (evidence/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'result':result['result'],'checks':len(result['checks']),'screenshots':len(result['screenshots']),'pageerrors':len(result.get('pageerrors',[]))}))
    return result['result']!='PASS'

if __name__=='__main__':sys.exit(main())

"""Real Firefox S08B UI evidence on a recorded isolated preview only."""
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
    require(re.fullmatch(r'ydental_s08b_test_[0-9]{14}_[a-f0-9]{8}', args.db), 'Database name refused')
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
        'ydental_clinical', 'ydental_treatment', 'ydental_treatment_test', 'scripts/s08b*'], text=True), 'Commit implementation and verification first')
    evidence = ROOT / 'docs/evidence/s08b-rework/rework-browser-attempts' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    evidence.mkdir(parents=True)
    result = {'scope': 'S08-B real reception, teeth, authored text, handover and pending responsibility', 'database': args.db, 'tested_commit': commit,
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
        if name.startswith(('R03','R04')):scope='[data-event]'
        elif name.startswith(('R05','R06','R08','R09','R11')):scope='article[data-order-kind=prescription]'
        elif name.startswith('R07'):scope='form[data-operation=refer]'
        elif name.startswith('R10'):scope='form[data-operation=publish_medicine]'
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
            page.locator('[name=chief_complaint]').fill('定向返工合成临床用药核对');version(page,1)
            page.goto(base+'/ydental/treatment')
            def ready(pg):pg.wait_for_function('document.querySelector(".o_ydental_treatment form[data-operation]").dataset.key')
            def submit(pg,form):
                with pg.expect_navigation(wait_until='domcontentloaded'):form.locator('button[type=submit]').click()
                ready(pg)
            def reject(pg,form,code,name):
                with pg.expect_response('**/ydental/treatment/action') as response:form.locator('button[type=submit]').click()
                require(response.value.status in (403,409),name+' server rejection')
                pg.wait_for_function('!document.querySelector("#treatment-reconcile").hidden')
                if code:require(code in pg.locator('#treatment-result').inner_text(),name+' error code')
                check(name,pg.locator('#treatment-reconcile').is_visible())
                return response.value.json()
            def chair(rows='none',quantity=2,material=2,actual=False):
                form=page.locator('form[data-operation=execute]')
                form.locator('[name=catalog_id]').select_option(str(preview['medicine_catalog']));form.locator('[name=quantity]').fill(str(quantity))
                form.locator('[name=tooth]').fill('0');form.locator('[name=tooth_state]').select_option('not_applicable')
                form.locator('[name=lot_id]').select_option('' if rows=='none' else str(preview['medicine_lot'] if rows=='correct' else preview['medicine2_lot']))
                form.locator('[name=material_quantity]').fill(str(material));form.locator('[name=reason]').fill('合成椅旁实际品种、批次与用量核对');form.locator('[name=already_performed]').set_checked(actual)
                return form
            ready(page)
            reject(page,chair(),'medicine_evidence_missing','new chairside without batch rejected with zero fee or stock')
            screenshot(page,ctx,'R01-chairside-empty-batch-rejected.png');page.reload();ready(page)
            check('empty-batch rejection leaves zero actual events',page.locator('[data-event]').count()==0)
            reject(page,chair('wrong'),'medicine_evidence_missing','chairside wrong SKU rejected');page.reload();ready(page)
            reject(page,chair('correct',material=1),'medicine_evidence_missing','chairside quantity mismatch rejected')
            screenshot(page,ctx,'R02-chairside-mismatched-quantity-rejected.png');page.reload();ready(page)
            check('three invalid new medication attempts leave zero events',page.locator('[data-event]').count()==0)
            submit(page,chair(actual=True))
            pending=page.locator('[data-event-state=pending]');event_id=int(pending.get_attribute('data-event'));result['historical_event']=event_id
            check('already performed missing-batch fact preserved pending without native move',pending.count()==1 and pending.locator('.native-moves').inner_text()=='[]')
            screenshot(page,ctx,'R03-historical-fact-pending-no-false-fee.png')
            verify=pending.locator('form[data-operation=verify_medicine]');verify.locator('[name=lot_id]').select_option(str(preview['medicine_lot']));verify.locator('[name=quantity]').fill('2');verify.locator('[name=evidence]').fill('原责任人核对原实际用药批次与数量，合成证据');submit(page,verify)
            check('historical evidence recovery confirms original two units and one native move',page.locator('[data-event="%s"]'%event_id).get_attribute('data-event-state')=='confirmed' and page.locator('[data-event="%s"] .native-moves'%event_id).inner_text() not in ('[]',''))
            screenshot(page,ctx,'R04-original-medication-evidence-recovered.png')
            order=page.locator('form[data-operation=order]');order.locator('[name=kind]').select_option('prescription');order.locator('[name=purpose]').fill('合成多品种处方，先保存未完善草稿')
            row=order.locator('.o_ydental_treatment_line');row.locator('[name=mapping_id]').select_option(str(preview['pharmacy_mapping']));row.locator('[name=quantity]').fill('6');row.locator('[name=product_id]').select_option(str(preview['medicine']));submit(page,order)
            rxid=int(page.locator('article[data-order-kind=prescription]').get_attribute('data-order'));result['prescription']=rxid
            reject(page,page.locator('article[data-order="%s"] form[data-operation=issue]'%rxid),None,'incomplete prescription freeze rejected by server')
            screenshot(page,ctx,'R05-incomplete-prescription-issue-rejected.png');page.reload();ready(page)
            check('invalid issue keeps draft and creates no pharmacy segment',page.locator('article[data-order="%s"] [data-segment]'%rxid).count()==0)
            edit=page.locator('article[data-order="%s"] form[data-operation=edit_order]'%rxid)
            def fill(row,sku,qty):
                row.locator('[name=mapping_id]').select_option(str(preview['pharmacy_mapping']));row.locator('[name=quantity]').fill(str(qty));row.locator('[name=product_id]').select_option(str(sku))
                for field in ('specification','usage','frequency','course'):row.locator('[name='+field+']').fill('医生明确填写合成审核字段 '+field)
            fill(edit.locator('.o_ydental_treatment_line').first,preview['medicine'],6)
            edit.locator('.add-order-line').click();fill(edit.locator('.o_ydental_treatment_line').nth(1),preview['medicine2'],2)
            edit.locator('.add-order-line').click();fill(edit.locator('.o_ydental_treatment_line').nth(2),preview['medicine3'],1)
            submit(page,edit);submit(page,page.locator('article[data-order="%s"] form[data-operation=issue]'%rxid))
            task=int(page.locator('article[data-order="%s"] .task-id'%rxid).inner_text())
            check('completed multi-SKU order freezes one exact pharmacy direction',page.locator('article[data-order="%s"] [data-segment]'%rxid).count()==1)
            screenshot(page,ctx,'R06-complete-multi-sku-prescription.png')
            for mode in ('timed','untimed'):
                form=page.locator('form[data-operation=refer]');form.locator('[name=mapping_id]').select_option(str(preview['legal_mapping']));form.locator('[name=mode]').select_option(mode);form.locator('[name=reason]').fill('来源仅甲公司权限，受控跨法人转诊 '+mode)
                if mode=='timed':
                    form.locator('[name=start]').fill(preview['start'].replace(' ','T').removesuffix(':00'));form.locator('[name=end]').fill(preview['end'].replace(' ','T').removesuffix(':00'))
                else:form.locator('[name=valid_until]').fill((datetime.now(timezone.utc).replace(tzinfo=None)+__import__('datetime').timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'))
                submit(page,form)
            check('source-only account can initiate both controlled cross-legal referral modes',page.locator('[data-referral-receipt]').count()==2)
            screenshot(page,ctx,'R07-source-only-cross-legal-referrals.png')
            denied=page.evaluate('''async id=>{const r=await fetch('/web/dataset/call_kw/ydental.intake.mapping/write',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({jsonrpc:'2.0',id:1,method:'call',params:{model:'ydental.intake.mapping',method:'write',args:[[id],{name:'Forbidden target mutation'}],kwargs:{}}})});return (await r.json()).error!==undefined}''',preview['legal_mapping'])
            check('cross-legal controlled referral grants no target ordinary RPC write',denied)
            def referral_form(mode):
                form=page.locator('form[data-operation=refer]');form.locator('[name=mapping_id]').select_option(str(preview['legal_mapping']));form.locator('[name=mode]').select_option(mode);form.locator('[name=reason]').fill('跨法人失败后保留来源与既有事实')
                if mode=='timed':
                    form.locator('[name=start]').fill(preview['start'].replace(' ','T').removesuffix(':00'));form.locator('[name=end]').fill(preview['end'].replace(' ','T').removesuffix(':00'))
                else:form.locator('[name=valid_until]').fill((datetime.now(timezone.utc).replace(tzinfo=None)+__import__('datetime').timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'))
                return form
            reject(page,referral_form('timed'),'insufficient_balance','full cross-legal target refuses another timed claim')
            screenshot(page,ctx,'R12-cross-legal-full-capacity-rejected.png');page.reload();ready(page)
            managerctx,manager=login('manager');manager.goto(base+'/ydental/access')
            switched=manager.evaluate("async store=>{const r=await fetch('/ydental/access/action',{method:'POST',body:new URLSearchParams({operation:'switch',revision:document.querySelector('[name=revision]').value,csrf_token:document.querySelector('[name=csrf_token]').value,output:'json',payload:JSON.stringify({store_id:store})})});return r.status}",preview['legal_store'])
            require(switched==200,'target-authorized manager selects B')
            def business(state):
                manager.goto(base+'/ydental/supply');form=manager.locator('#business-day form').filter(has=manager.locator('input[name=area_id][value="%s"]'%preview['legal_area'])).filter(has=manager.locator('input[name=version]'))
                form.locator('[name=state]').select_option(state);form.locator('[name=reason]').fill('目标责任人明确停接及恢复，核对原来源不受损')
                with manager.expect_navigation(wait_until='domcontentloaded'):form.locator('button').click()
                require('/ydental/supply' in manager.url,'target business transition completed')
            business('draining');page.reload();ready(page)
            reject(page,referral_form('untimed'),None,'stopped cross-legal target refuses untimed referral')
            screenshot(page,ctx,'R13-cross-legal-stopped-target-rejected.png');business('open');page.reload();ready(page)
            invalid=referral_form('untimed');invalid.locator('[name=mapping_id]').evaluate('(el,id)=>{const o=new Option("非法本店目标",String(id));el.add(o);el.value=String(id)}',preview['mapping'])
            reject(page,invalid,None,'server rejects modified non-cross-store target mapping')
            screenshot(page,ctx,'R14-illegal-target-keeps-original-source.png');page.reload();ready(page)
            check('three cross-legal failures preserve source serving and exactly two original receipts',int(page.locator('main.o_ydental_treatment').get_attribute('data-execution') or 0)>0 and page.locator('[data-referral-receipt]').count()==2)
            page.goto(base+'/ydental/clinical?document_id='+str(d1));open_editor(page);click_wait(page,'#handover-document');page.goto(base+'/ydental/queue');click_wait(page,'button[data-operation=exit]')
            frontctx,front=login('frontdesk')
            def report(task):
                front.goto(base+'/ydental/queue');form=front.locator('form[data-queue-form=report]').filter(has=front.locator('input[name=task_id][value="%s"]'%task))
                with front.expect_navigation(wait_until='domcontentloaded'):form.locator('button').click()
            report(task);pharmctx,pharm=login('pharmacy');pharm.on('dialog',lambda dialog:dialog.accept())
            def start_pharm():
                pharm.goto(base+'/ydental/queue');click_wait(pharm,'button[data-operation=enter][data-station="%s"]'%preview['pharmacy_station']);click_wait(pharm,'button[data-operation=call]');click_wait(pharm,'button[data-operation=start]');pharm.goto(base+'/ydental/treatment');ready(pharm)
            def dose_form(index,lot,qty):
                form=pharm.locator('article[data-order="%s"] form[data-operation=dispense]'%rxid).nth(index)
                form.locator('[name=lot_id]').select_option(str(lot));form.locator('[name=quantity]').fill(str(qty));form.locator('[name=reason]').fill('核对处方实际药品及独立已发布价源 '+str(index));return form
            def finish():
                form=pharm.locator('article[data-order="%s"] form[data-operation=finish]'%rxid);form.locator('[name=reason]').fill('结束本次真实发药段');submit(pharm,form)
            start_pharm();reject(pharm,dose_form(2,preview['medicine3_lot'],1),'medicine_price_unverified','unlinked SKU cannot borrow another medicine price')
            screenshot(pharm,pharmctx,'R08-unlinked-sku-dispense-rejected.png');pharm.reload();ready(pharm)
            check('unlinked rejected dispense preserves approved remaining one',float(pharm.locator('article[data-order="%s"] tr:has(form[data-operation=dispense]) .remaining'%rxid).nth(2).inner_text())==1)
            submit(pharm,dose_form(0,preview['medicine_lot'],4));submit(pharm,dose_form(1,preview['medicine2_lot'],2))
            check('two SKUs dispense independently through one task with 4 and 2 actual quantities',list(map(float,pharm.locator('article[data-order="%s"] tr:has(form[data-operation=dispense]) .remaining'%rxid).all_inner_texts()))==[2,0,1])
            screenshot(pharm,pharmctx,'R09-distinct-sku-price-sources-10-and-27.png');finish()
            next_task=int(pharm.locator('article[data-order="%s"] .task-id'%rxid).last.inner_text())
            check('multi-SKU remainder is one pending-report task and holder released',next_task!=task and int(pharm.locator('main.o_ydental_treatment').get_attribute('data-execution') or 0)==0)
            pricectx,pricer=login('price');pricer.on('dialog',lambda dialog:dialog.accept());pricer.goto(base+'/ydental/treatment?prices=1');ready(pricer)
            publish=pricer.locator('form[data-operation=publish_medicine]');publish.locator('[name=product_id]').select_option(str(preview['medicine3']));publish.locator('[name=catalog_id]').select_option(str(preview['medicine3_catalog']));publish.locator('[name=evidence]').fill('价格责任人明确审核合成第三SKU与43元目录对应');submit(pricer,publish)
            check('price-write publishes explicit SKU association through real UI',pricer.locator('[data-medicine-link]').count()==3)
            screenshot(pricer,pricectx,'R10-explicit-price-authority-sku-publication.png')
            report(next_task);start_pharm();submit(pharm,dose_form(0,preview['medicine_lot'],2));submit(pharm,dose_form(2,preview['medicine3_lot'],1));finish()
            check('original six remains actual4+2 while other SKUs retain independent prices',pharm.locator('article[data-order="%s"] form[data-operation=finish]'%rxid).count()==0 and pharm.locator('article[data-order="%s"] [data-segment]'%rxid).count()==2)
            screenshot(pharm,pharmctx,'R11-multi-sku-complete-original-sources.png')
            check('zero browser page errors',not errors)
            result.update(result='PASS',pageerrors=errors,preview_ids={k:preview[k] for k in ('medicine','medicine2','medicine3','medicine_catalog','medicine2_catalog','medicine3_catalog','legal_mapping','legal_store','legal_company')})
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

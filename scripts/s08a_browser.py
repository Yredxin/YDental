"""Real Firefox S08A UI evidence on a recorded isolated preview only."""
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
    require(re.fullmatch(r'ydental_s08a_test_[0-9]{14}_[a-f0-9]{8}', args.db), 'Database name refused')
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
        'ydental_clinical', 'ydental_clinical_test', 'scripts/s08a*'], text=True), 'Commit implementation and verification first')
    evidence = ROOT / 'docs/evidence/s08a/browser-attempts' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    evidence.mkdir(parents=True)
    result = {'scope': 'S08-A real reception, teeth, authored text, handover and pending responsibility', 'database': args.db, 'tested_commit': commit,
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
            ctx,page=login('doctor');page.goto(base+'/ydental/queue')
            click_wait(page,'button[data-operation=enter][data-station="%s"]'%preview['station'])
            check('real S06 chair entered',page.locator('#holding-workstation').count()==1)
            click_wait(page,'button[data-operation=call]');click_wait(page,'button[data-operation=start]')
            check('real S06 execution serving',page.locator('[data-execution]').count()>0)
            page.goto(base+'/ydental/clinical');check('Chinese real treatment workbench','治疗接诊工作台' in page.inner_text('body'))
            check('patient and actual serving segment visible before document creation','合成患者' in page.inner_text('body') and page.locator('#execution-state').get_attribute('data-state')=='serving')
            check('existing S05 price source retains independent permission',page.locator('a[href="/ydental/intake/prices"]').count()==1 and '不生成费用' in page.inner_text('body'))
            open_editor(page);d1=int(page.evaluate('new URL(location.href).searchParams.get("document_id")'))
            check('52 clickable permanent and primary teeth',page.locator('[data-tooth]').count()==52)
            for i in range(1,4):page.locator('[name=chief_complaint]').fill('合成演示主诉第%s次保存'%i);version(page,i)
            check('three real server autosaves',page.locator('#server-version').inner_text()=='3')
            page.locator('[data-tooth="11"]').click();page.locator('#tooth-state').select_option('present');page.locator('#surfaces input[value=I]').check();page.locator('#surfaces input[value=M]').check();version(page,4)
            check('anterior I enabled and O refused',page.locator('#surfaces input[value=O]').is_disabled())
            screenshot(page,ctx,'01-permanent-anterior-autosave.png')
            page.locator('[data-tooth="55"]').click();page.locator('#tooth-state').select_option('present');page.locator('#surfaces input[value=O]').check();version(page,5)
            check('primary posterior O enabled I refused',page.locator('#surfaces input[value=I]').is_disabled())
            page.locator('[data-tooth="48"]').click();page.locator('#tooth-state').select_option('missing');version(page,6)
            check('missing tooth cannot select surfaces',page.locator('#surfaces input:enabled').count()==0)
            page.locator('[data-tooth="51"]').click();page.locator('#tooth-state').select_option('unknown');version(page,7)
            page.locator('#no-tooth').click();version(page,8)
            screenshot(page,ctx,'02-primary-missing-unknown.png')
            page.locator('[name=findings]').fill('合成所见，不构成真实临床结论');version(page,9)
            page.locator('[name=diagnosis]').fill('合成诊断草案，待业务审核');version(page,10)
            payload=page.evaluate('''() => ({document_id:Number(new URL(location.href).searchParams.get('document_id')),editor_token:sessionStorage.getItem('ydental_clinical_editor_'+new URL(location.href).searchParams.get('document_id')),expected_version:0,key:crypto.randomUUID(),content:Object.fromEntries([...document.querySelectorAll('textarea[name]')].map(f=>[f.name,f.value]).concat([['teeth',[]]]))})''')
            stale=inspect_action(page,'save',payload);check('stale version server rejects',stale['status']==409 and 'version_conflict' in stale['data']['error'])
            payload['expected_version']=int(page.locator('#server-version').inner_text());payload['content']['teeth']=[{'tooth':99,'state':'present','surfaces':['M']}];payload['key']='invalid-fdi-browser-request'
            invalid=inspect_action(page,'save',payload);check('invalid FDI server rejects',invalid['status']==409 and 'invalid_tooth' in invalid['data']['error'])
            screenshot(page,ctx,'03-structured-draft.png')
            click_wait(page,'#handover-document');check('D1 pending after real handover','文书待完善' in page.inner_text('body'))
            check('pending document cannot handover again',page.locator('#handover-document').is_disabled())
            screenshot(page,ctx,'04-D1-pending-after-handover.png')
            # S06 releases the patient but retains the doctor's idle chair; explicitly exit it.
            page.goto(base+'/ydental/queue');click_wait(page,'button[data-operation=exit]')
            check('D1 supplementation does not occupy a chair',page.locator('#holding-workstation').count()==0)
            page.goto(base+'/ydental/clinical?document_id='+str(d1));open_editor(page)
            page.locator('[name=history]').fill('D1交还后独立补记合成病史');version(page,12)
            screenshot(page,ctx,'05-D1-pending-independent-editor.png')
            frontctx,front=login('frontdesk');front.goto(base+'/ydental/queue')
            form=front.locator('form[data-queue-form=report]').filter(has=front.locator('input[name=task_id]'))
            continuation=form.locator('input[name=task_id]').evaluate_all('(xs)=>xs.map(x=>Number(x.value))')
            check('one pending continuation offered',len(continuation)==1)
            click_wait(front,'form[data-queue-form=report] button')
            ctx2,p2=login('doctor2');p2.goto(base+'/ydental/queue')
            click_wait(p2,'button[data-operation=enter][data-station="%s"]'%preview['other_station'])
            click_wait(p2,'button[data-operation=call]');click_wait(p2,'button[data-operation=start]');p2.goto(base+'/ydental/clinical');open_editor(p2)
            d2=int(p2.evaluate('new URL(location.href).searchParams.get("document_id")'));check('D2 new independent document',d2!=d1)
            p2.locator('[name=chief_complaint]').fill('D2新接诊的独立合成草稿');version(p2,1)
            screenshot(p2,ctx2,'06-D2-new-reception.png')
            # Active D1 editor prevents transfer even for its responsible actor.
            page.locator('#transfer-user').select_option(str(preview['doctor2']));page.locator('#transfer-reason').fill('合成责任交接演示');page.locator('#transfer-document').click()
            page.wait_for_function('document.querySelector("#clinical-result").textContent.includes("editor_busy")')
            check('responsibility transfer refuses valid editor',True);screenshot(page,ctx,'07-valid-editor-transfer-denied.png')
            page.locator('#release-document').click();page.wait_for_function('document.querySelector("textarea").disabled')
            click_wait(page,'#transfer-document')
            check('D1 responsible person legally transferred','合成人员 doctor2' in page.inner_text('body'))
            # Release D2's independent editor before showing its author's D1 completion.
            p2.locator('#release-document').click();p2.wait_for_function('document.querySelector("textarea").disabled')
            p2.goto(base+'/ydental/clinical?document_id='+str(d1));open_editor(p2)
            p2.locator('[name=follow_up]').fill('新责任人核对后补充的合成后续建议');version(p2,13)
            click_wait(p2,'#confirm-document');check('D1 text confirmed by new contributor','文字已确认' in p2.inner_text('body'))
            screenshot(p2,ctx2,'08-D1-confirmed-author-history.png')
            open_editor(p2);p2.locator('[name=chief_complaint]').fill('合成主诉文字更正，不改变经济事实');p2.locator('#correction-reason').fill('更正合成录入文字');click_wait(p2,'#correct-document')
            check('confirmed text correction appends version',int(p2.locator('#server-version').inner_text())==15)
            screenshot(p2,ctx2,'09-text-correction-new-version.png')
            p2.goto(base+'/ydental/clinical?document_id='+str(d2));check('D1 confirmation leaves D2 draft unconfirmed','草稿' in p2.locator('#text-state').inner_text())
            check('D2 real segment continues serving',p2.locator('#execution-state').get_attribute('data-state')=='serving')
            readerctx,reader=login('reader');reader.goto(base+'/ydental/clinical?document_id='+str(d1));reader.locator('#open-document').click()
            reader.wait_for_function('document.querySelector("#clinical-result").textContent.includes("access_denied")')
            check('read-only medical user cannot edit',reader.locator('[name=chief_complaint]').is_disabled());screenshot(reader,readerctx,'10-readonly-medical-denied.png')
            # Genuine browser offline leaves content visibly unsynchronized.
            open_editor(p2);ctx2.set_offline(True);p2.locator('[name=history]').fill('未同步合成文本')
            p2.wait_for_function('document.querySelector("#clinical-result").textContent.includes("未同步") || document.querySelector("#clinical-result").textContent.includes("连接")');check('offline never claims success','已保存' not in p2.locator('#clinical-result').inner_text())
            ctx2.set_offline(False);p2.locator('#open-document').click()
            check('reacquire cannot mark unsent local text saved','未同步' in p2.locator('#clinical-result').inner_text() and '已保存' not in p2.locator('#clinical-result').inner_text())
            screenshot(p2,ctx2,'11-offline-unsynchronized.png')
            # Drop only this page's unsent demonstration text by explicit navigation.
            p2.on('dialog',lambda dialog:dialog.accept());p2.reload();check('refresh restores committed server text',p2.locator('[name=history]').input_value()!='未同步合成文本')
            if args.terminal_races:
                from s08a_terminal_browser import run_terminal_races
                result['documents']={'D1':d1,'D2':d2}
                run_terminal_races(page=p2,context=ctx2,front=front,base=base,d1=d1,d2=d2,
                    check=check,screenshot=screenshot,open_editor=open_editor,version=version,
                    click_wait=click_wait,inspect_action=inspect_action,result=result)
            check('zero browser page errors',not errors)
            result.update(result='PASS',pageerrors=errors,documents=result.get('documents',{'D1':d1,'D2':d2}))
        except Exception as error:
            import traceback
            result.update(result='FAIL',error={'type':type(error).__name__,'detail':str(error)[:500],
                'trace':[{'file':Path(frame.filename).name,'line':frame.lineno,'method':frame.name} for frame in traceback.extract_tb(error.__traceback__)]},pageerrors=errors)
            if 'p2' in locals() and not p2.is_closed():
                result['failure_ui']={'message':p2.locator('#clinical-result').inner_text(),
                    'version':p2.locator('#server-version').inner_text(),
                    'readonly':p2.locator('textarea[name=chief_complaint]').is_disabled()}
                screenshot(p2,ctx2,'failure-state.png')
        finally:
            for context in contexts:context.close()
            browser.close()
            (evidence/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'result':result['result'],'checks':len(result['checks']),'screenshots':len(result['screenshots']),'pageerrors':len(result.get('pageerrors',[]))}))
    return result['result']!='PASS'

if __name__=='__main__':sys.exit(main())

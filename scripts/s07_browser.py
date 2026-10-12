"""Real Firefox S07 UI evidence on a recorded isolated preview only."""
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
    args = parser.parse_args()
    require(re.fullmatch(r'ydental_s07_test_[0-9]{14}_[a-f0-9]{8}', args.db), 'Database name refused')
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
        'ydental_inventory', 'ydental_inventory_test', 'scripts/s07*'], text=True), 'Commit implementation and verification first')
    evidence = ROOT / 'docs/evidence/s07-rework/browser-attempts' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    evidence.mkdir(parents=True)
    result = {'scope': 'S07 native inventory workbench and security', 'database': args.db, 'tested_commit': commit,
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

    with sync_playwright() as p:
        browser=p.firefox.launch(headless=True)
        contexts=[];errors=[]
        def login(role='stock',upstream=False):
            ctx=browser.new_context(viewport={'width':1440,'height':1050},locale='zh-CN')
            contexts.append(ctx)
            ctx.route('**/*',lambda route:route.continue_() if urlsplit(route.request.url).hostname=='127.0.0.1' and urlsplit(route.request.url).port==args.port else route.abort())
            page=ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
            c=access[role]
            page.goto(base+'/web/login?redirect=/ydental/access',wait_until='domcontentloaded')
            page.locator('[name=login]').fill(c['login']);page.locator('[name=password]').fill(c['password']);page.locator('button[type=submit]').click()
            page.wait_for_url(lambda u:'/web/login' not in u)
            page.goto(base+'/ydental/access',wait_until='domcontentloaded')
            result=page.evaluate('''async store=>{const b=new URLSearchParams({operation:'switch',revision:document.querySelector('[name=revision]').value,csrf_token:document.querySelector('[name=csrf_token]').value,output:'json',payload:JSON.stringify({store_id:store})});return (await fetch('/ydental/access/action',{method:'POST',body:b})).json()}''',preview['store'])
            require(type(result.get('revision')) is int,'select synthetic store')
            if upstream:
                response=page.goto(base+'/ydental/queue',wait_until='domcontentloaded')
                check('S06 upstream medical read entry after login and store switch',response.status==200)
                return ctx,page
            page.goto(base+'/ydental/inventory',wait_until='domcontentloaded')
            return ctx,page
        def go(page):page.goto(base+'/ydental/inventory',wait_until='domcontentloaded')
        def fill(page,operation,values,scope=''):
            form=page.locator(scope+' [data-inventory-form="'+operation+'"]' if scope else '[data-inventory-form="'+operation+'"]')
            for name,value in values.items():
                field=form.locator('[name="'+name+'"]')
                if field.evaluate('(e)=>e.tagName')=='SELECT':field.select_option(str(value))
                else:field.fill(str(value))
            return form
        def submit(page,form,ok=True):
            operation=form.get_attribute('data-inventory-form')
            with page.expect_navigation(wait_until='domcontentloaded'):
                with page.expect_response(lambda r:'/ydental/inventory/action' in r.url) as response:form.locator('button[type=submit]').click()
            check('actual form submit '+operation,response.value.status in (200,303) if ok else response.value.status>=400)
            return response.value.status
        def shot(page,ctx,name,target=None):
            if target:page.locator(target).scroll_into_view_if_needed()
            # Visible viewport captures the relevant state with readable text.
            sensitive.update(c['value'] for c in ctx.cookies() if re.search('session|csrf|token|auth',c['name'],re.I))
            visible=page.locator('body').inner_text()
            require(not any(x and x in visible for x in sensitive),'visible credential refused')
            path=evidence/name;page.screenshot(path=str(path),full_page=False)
            result['screenshots'].append({'path':str(path.relative_to(ROOT)),'sha256':sha(path)})
        def rpc(page,model,method,args0):
            return page.evaluate('''async x=>{return(await fetch('/web/dataset/call_kw/'+x.model+'/'+x.method,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({jsonrpc:'2.0',id:1,method:'call',params:{model:x.model,method:x.method,args:x.args,kwargs:{}}})})).json()}''',{'model':model,'method':method,'args':args0})
        def action_json(page,operation,payload):
            return page.evaluate('''async x=>{const b=new URLSearchParams({operation:x.operation,revision:document.querySelector('[name=revision]').value,csrf_token:document.querySelector('[name=csrf_token]').value,key:crypto.randomUUID(),payload:JSON.stringify(x.payload),output:'json'});const r=await fetch('/ydental/inventory/action',{method:'POST',body:b});return{status:r.status,body:await r.json()}}''',{'operation':operation,'payload':payload})
        lot=preview['lot'];u=preview['unit']
        def qty(page):return float(page.locator('[data-lot="%s"] .available'%lot).inner_text())
        try:
            ctx,page=login()
            check('Chinese workbench rendered', '库存工作台' in page.locator('h1').inner_text())
            check('F1 actual native receipt ten is visible',qty(page)==10)
            shot(page,ctx,'01-chinese-stock-ten.png','table')
            form=fill(page,'issue',{'lot_id':lot,'quantity':3,'uom_id':u,'source_key':'firefox-issue-'+args.db,'reason':'S07 Firefox actual issue three'})
            body=form.evaluate('(e)=>Object.fromEntries(new FormData(e))')
            submit(page,form)
            check('F1 actual issue three leaves seven',qty(page)==7)
            replay=page.evaluate('''async body=>{body.output='json';const r=await fetch('/ydental/inventory/action',{method:'POST',body:new URLSearchParams(body)});return{status:r.status,body:await r.json()}}''',body)
            check('F1 same request returns original receipt',replay['status']==200 and replay['body']['result']=='already_accepted')
            go(page);check('F1 replay leaves seven',qty(page)==7);issued=replay['body']['id']
            scope='[data-event="%s"]'%issued
            form=fill(page,'return',{'quantity':1,'uom_id':u,'source_key':'firefox-return-'+args.db,'reason':'S07 Firefox physical return'},scope)
            submit(page,form);check('F1 physical return does not increase issuable seven',qty(page)==7)
            check('F1 quarantine one',float(page.locator('[data-lot="%s"] .quarantine'%lot).inner_text())==1)
            shot(page,ctx,'02-physical-return-quarantine.png','table')
            ret=int(page.locator('article[data-event]').first.get_attribute('data-event'))
            form=fill(page,'verify',{'quantity':1,'uom_id':u,'source_key':'firefox-verify-'+args.db,'reason':'S07 Firefox actual inspection','disposition':'release'},'[data-event="%s"]'%ret)
            submit(page,form);check('F1 verified return increases stock to eight',qty(page)==8)
            refund=action_json(page,'refund',{'event_id':issued});check('T05 independent refund has no inventory action',refund['status']==403)
            go(page);check('T05 refund refusal leaves eight',qty(page)==8)
            shot(page,ctx,'03-verified-return-eight.png','table')
            form=fill(page,'lot_edit',{'lot_id':lot,'enabled':'no','reason':'S07 Firefox stop batch'});submit(page,form)
            form=fill(page,'issue',{'lot_id':lot,'quantity':1,'uom_id':u,'source_key':'firefox-disabled-'+args.db,'reason':'Disabled must fail'});submit(page,form,False)
            check('T03 disabled batch rejected by server','lot_disabled' in page.locator('body').inner_text())
            shot(page,ctx,'04-disabled-server-rejection.png')
            go(page);form=fill(page,'lot_edit',{'lot_id':lot,'enabled':'yes','reason':'S07 Firefox reopen batch'});submit(page,form)
            pending=preview['pending'];scope='[data-event="%s"]'%pending
            form=fill(page,'recover',{'reason':'Still missing real stock'},scope);submit(page,form,False)
            check('F3 no stock recovery refuses','insufficient_balance' in page.locator('body').inner_text())
            go(page);check('F3 original pending source remains visible',page.locator(scope+' .event-state').get_attribute('data-state')=='pending')
            shot(page,ctx,'05-pending-original-responsible.png',scope)
            form=fill(page,'receive',{'lot_id':preview['material'],'quantity':5,'uom_id':u,'source_key':'firefox-correction-'+args.db,'reason':'Real receipt evidence for reconciliation'});submit(page,form)
            form=fill(page,'recover',{'reason':'Recover original synthetic source after real correction'},scope);submit(page,form)
            check('F3 original event confirmed once',page.locator(scope+' .event-state').get_attribute('data-state')=='done')
            check('F3 material remaining three',float(page.locator('[data-lot="%s"] .available'%preview['material']).inner_text())==3)
            shot(page,ctx,'06-original-event-recovered.png',scope)
            # Both histories are created by the guarded private source adapter.
            # Firefox performs the real receipt, original recovery and negatives.
            for h in preview['history']:
                label='expired' if h['expired'] else 'disabled'; event=h['event']; oldlot=h['lot']
                sc='[data-event="%s"]'%event
                go(page)
                r=action_json(page,'recover',{'event_id':event,'reason':'No correction yet; stay pending'})
                check('REWORK '+label+' no-stock recovery refuses',r['status']==409)
                r=action_json(page,'receive',{'lot_id':oldlot,'quantity':5,'uom_id':u,'source_key':'firefox-historical-'+label+'-'+args.db,'reason':'Evidenced actual receipt for historical event'})
                check('REWORK '+label+' actual receipt succeeds',r['status']==200)
                go(page)
                form=fill(page,'recover',{'reason':'Confirmed original fact and actual receipt'},sc);submit(page,form)
                check('REWORK '+label+' original event done',page.locator(sc+' .event-state').get_attribute('data-state')=='done')
                original=rpc(page,'ydental.inventory.event','read',[[event],['ydental_price_snapshot','ydental_actual_at','ydental_reconciled_at','ydental_correction_id','ydental_move_id']])['result'][0]
                check('REWORK '+label+' original price20 and correction linked',original['ydental_price_snapshot']['unit_price']==20 and bool(original['ydental_correction_id']) and bool(original['ydental_reconciled_at']))
                replay=action_json(page,'recover',{'event_id':event,'reason':'Repeat original reconciliation'})
                check('REWORK '+label+' retry same move',replay['status']==200 and replay['body']['move_id']==original['ydental_move_id'][0])
                new=action_json(page,'issue',{'lot_id':oldlot,'quantity':1,'uom_id':u,'source_key':'firefox-new-'+label+'-'+args.db,'reason':'New issue must remain blocked'})
                check('REWORK '+label+' new issue refuses',new['status']==409 and 'lot_'+label in new['body']['error'])
                go(page);row=page.locator('[data-lot="%s"]'%oldlot)
                check('REWORK '+label+' remains unusable with real onhand3',float(row.locator('.available').inner_text())==0 and label in row.locator('[data-flags]').get_attribute('data-flags'))
                shot(page,ctx,'11-historical-'+label+'.png',sc)
            # Compare S06 read entry and new inventory entry repeatedly in the
            # same clean server process, without S06 business mutations.
            dc,doctor_page=login('doctor',upstream=True)
            for cycle in range(5):
                upstream=doctor_page.goto(base+'/ydental/queue',wait_until='domcontentloaded')
                check('stability S06 read cycle '+str(cycle),upstream.status==200)
                downstream=page.goto(base+'/ydental/inventory',wait_until='domcontentloaded')
                check('stability inventory read cycle '+str(cycle),downstream.status==200)
            # Native access and patient/attachment boundaries from Firefox session.
            check('T07 native lot read denied','error' in rpc(page,'stock.lot','read',[[lot],['product_qty','quant_ids']]))
            check('T07 native quant mutation denied','error' in rpc(page,'stock.quant','create',[{'quantity':999,'product_id':preview['products']['medicine']}]))
            check('T07 source method cannot be forged over RPC','error' in rpc(page,'ydental.inventory.service','_source_action',[{}]))
            check('T07 export requires separate export permission','error' in rpc(page,'ydental.inventory.event','export_data',[[issued],['name']]))
            check('T07 stock role cannot read patient history','error' in rpc(page,'ydental.patient','search_read',[[]]))
            rc,reader=login('reader');check('T07 readonly workbench has no issue form',reader.locator('[data-inventory-form=issue]').count()==0)
            denied=action_json(reader,'issue',{});check('T07 readonly manual POST denied',denied['status']==403)
            shot(reader,rc,'07-readonly-workbench.png','table')
            mc,manager=login('manager');check('T09 group manager has catalog form',manager.locator('[data-inventory-form=product]').count()==1)
            check('T09 stock worker has no catalog mutation form',page.locator('[data-inventory-form=product]').count()==0)
            shot(manager,mc,'08-master-data-authority.png','[data-inventory-form=product]')
            go(page);scan=page.locator('[data-inventory-form=scan]');scan.locator('[name=code]').fill('UNKNOWN-OUTSOURCE-CODE')
            with page.expect_navigation(wait_until='domcontentloaded'):scan.locator('button').click()
            check('T09 scan remains unsupported without S11','unsupported_source' in page.locator('body').inner_text() and 'false' in page.locator('body').inner_text())
            shot(page,ctx,'09-scan-failclosed.png')
            go(page);row=page.locator('[data-lot="%s"]'%preview['prosthesis'])
            check('T09 prosthesis collection starts at actual receipt','collection' in row.locator('[data-flags]').get_attribute('data-flags') and row.inner_text().find('2026')>=0)
            shot(page,ctx,'10-prosthesis-receipt-alert.png','table')
            result['pageerror_count']=len(errors);check('Firefox pageerror zero',not errors)
            result['result']='PASS'
        except Exception as error:
            result['result']='FAIL';result['error_type']=type(error).__name__;result['error']=str(error)[:500];result['pageerror_count']=len(errors)
            raise
        finally:
            for ctx0 in contexts:ctx0.close()
            browser.close();(evidence/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'result':result['result'],'checks':len(result['checks']),'screenshots':len(result['screenshots']),'pageerrors':result['pageerror_count']}))


if __name__=='__main__':main()

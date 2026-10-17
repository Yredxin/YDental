"""One ordinary frontdesk native Firefox payment on new B sources only."""
import asyncio
import json
import os
from urllib.parse import urlsplit
import sys
import s10_p0_20_contract as c
from s10_p0_20_b_control import NAME,RUN,PORT
from s10_p0_20_browser import DEPS
from playwright.async_api import async_playwright

def event(kind,**facts):
    with (c.OUT/'B-request-events.jsonl').open('a') as f:
        f.write(json.dumps({'event':kind,**facts},sort_keys=True)+'\n');f.flush();os.fsync(f.fileno())

async def main():
    c.checkpoint();fixture=c.read(RUN/'b-multi.json')
    actor={'id':fixture['frontdesk_id'],'login':fixture['frontdesk_login']}
    root='http://127.0.0.1:'+str(PORT);counts={'login_GET':0,'login_POST':0,'workbench_GET':0,'business_POST':0,'static_GET':0};stopped=False
    def request(req):event('request',method=req.method,path=urlsplit(req.url).path,request_id=id(req))
    def response(res):event('response',method=res.request.method,path=urlsplit(res.url).path,status=res.status,request_id=id(res.request))
    async def route(rt):
        nonlocal stopped
        req=rt.request;u=urlsplit(req.url)
        try:
            assert not stopped and u.netloc==f'127.0.0.1:{PORT}'
            if u.path=='/web/login':kind='login_POST' if req.method=='POST' else 'login_GET'
            elif u.path=='/ydental/settlement':assert req.method=='GET';kind='workbench_GET'
            elif u.path=='/ydental/settlement/action':assert req.method=='POST';kind='business_POST'
            else:assert req.method=='GET' and (u.path.startswith('/web/assets/') or u.path=='/website/translations');kind='static_GET'
            counts[kind]+=1;assert counts[kind]<={'login_GET':1,'login_POST':1,'workbench_GET':2,'business_POST':1,'static_GET':100}[kind]
            event('dispatch',request_id=id(req),kind=kind)
            await rt.continue_()
        except BaseException as e:stopped=True;event('cancel',request_id=id(req),error=type(e).__name__);await rt.abort()
    browser=None
    try:
        async with async_playwright() as pw:
            browser=await pw.firefox.launch(headless=True,env=os.environ.copy());ctx=await browser.new_context(locale='zh-CN',viewport={'width':1440,'height':1100},service_workers='block')
            ctx.on('request',request);ctx.on('response',response);ctx.on('requestfailed',lambda r:event('failure',request_id=id(r),path=urlsplit(r.url).path))
            await ctx.route('**/*',route);page=await ctx.new_page();page.set_default_timeout(20000)
            event('intent',action='login_GET');await page.goto(root+'/web/login?redirect=/ydental/settlement',wait_until='domcontentloaded')
            form=page.locator('form.oe_login_form');await form.locator('[name=login]').fill(actor['login']);await form.locator('[name=password]').fill('s05-test-password')
            event('intent',action='login_POST');await form.locator('button[type=submit]').click();await page.locator('.o_ydental_settlement').wait_for()
            assert not stopped
            form=page.locator('form').filter(has=page.locator('input[name=operation][value=pay]'))
            assert await form.count()==1
            target=fixture['new_invoice_ids'][3]
            await form.locator(f'input[name=invoice_ids][value="{target}"]').check()
            await form.locator('[name=amount]').fill('3');await form.locator('[name=channel]').select_option('alipay');await form.locator('[name=proof]').fill('P020 B new source ordinary frontdesk actual synthetic payment 3')
            event('intent',action='pay',invoice_id=target,amount=3,actor=actor['id'])
            await form.locator('button[type=submit]').click()
            assert '操作已受理' in await page.locator('body').inner_text();assert not stopped
            await page.screenshot(path=str(c.PRIVATE/'B-frontdesk-payment.png'),full_page=True)
            c.save(c.OUT/'B-browser-result.json',{'status':'NATIVE_FRONTDESK_NEW_B_PAYMENT_ACCEPTED','actor':actor['id'],'invoice_id':target,'amount':3,'counts':counts,'database':NAME,'independent_from_W5':True})
            await browser.close();browser=None
    finally:
        stopped=True;event('stop_new_actions')
        if browser is not None:await browser.close()
        event('closed')

if __name__=='__main__':asyncio.run(main())

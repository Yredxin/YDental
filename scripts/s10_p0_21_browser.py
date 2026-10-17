"""Real new-B ordinary UI across independent legal role sessions; durable events."""
import asyncio
import json
import os
from urllib.parse import urlsplit
import sys
import s10_p0_21_contract as c
DEPS=c.ROOT/'.local/s00-b-deps';sys.path.insert(0,str(DEPS/'verify-lib'))
os.environ.update(PLAYWRIGHT_BROWSERS_PATH=str(DEPS/'browsers'),LD_LIBRARY_PATH=str(DEPS/'browser-libs/usr/lib/x86_64-linux-gnu'),FONTCONFIG_FILE=str(DEPS/'browser-fonts.conf'))
from playwright.async_api import async_playwright

BASE='http://127.0.0.1:'+str(c.PORT)
counts={};stopped=False

def log(kind,**x):
    with (c.OUT/'HTTP-events.jsonl').open('a') as f:f.write(c.canonical({'event':kind,**x})+'\n');f.flush();os.fsync(f.fileno())
async def main():
    global stopped
    c.gate();chain=c.read(c.RUN/'b-chain.json');multi=c.read(c.RUN/'b-multi.json');original=c.read(c.RUN/'original.json')
    async with async_playwright() as pw:
        browser=await pw.firefox.launch(headless=True,env=os.environ.copy())
        try:
            async def session(login,store):
                ctx=await browser.new_context(locale='zh-CN',viewport={'width':1440,'height':1100},accept_downloads=True,service_workers='block')
                ctx.on('request',lambda r:log('request',method=r.method,path=urlsplit(r.url).path,request_id=id(r)))
                ctx.on('response',lambda r:log('response',method=r.request.method,path=urlsplit(r.url).path,status=r.status,request_id=id(r.request)))
                ctx.on('requestfailed',lambda r:log('failure',path=urlsplit(r.url).path,request_id=id(r)))
                async def route(rt):
                    r=rt.request;u=urlsplit(r.url)
                    if stopped or u.netloc!=f'127.0.0.1:{c.PORT}':log('cancel',path=u.path);await rt.abort();return
                    label=r.method+' '+u.path;counts[label]=counts.get(label,0)+1
                    assert sum(counts.values())<=350,'HTTP_REQUEST_BUDGET'
                    assert u.path.startswith(('/web/assets/','/web/static/','/website/translations','/web/login','/ydental/access','/ydental/settlement','/web/content/','/web/image/'))
                    log('dispatch',method=r.method,path=u.path);await rt.continue_()
                await ctx.route('**/*',route)
                page=await ctx.new_page();page.set_default_timeout(25000)
                log('intent',action='native_login',role_login_sha256=c.sha(login.encode()))
                await page.goto(BASE+'/web/login?redirect=/ydental/access',wait_until='domcontentloaded')
                form=page.locator('form.oe_login_form');await form.locator('[name=login]').fill(login);await form.locator('[name=password]').fill('s05-test-password');await form.locator('button[type=submit]').click()
                await page.wait_for_url('**/ydental/access')
                switch=page.locator('form').filter(has=page.locator('[name=operation][value=switch]'))
                await switch.locator('select[name=store_id]').select_option(str(store));log('intent',action='native_store_switch',store_id=store)
                await switch.locator('button[type=submit]').click();await page.wait_for_load_state('domcontentloaded')
                await page.goto(BASE+'/ydental/settlement',wait_until='domcontentloaded')
                return ctx,page
            # Group1/2: real frontdesk selects only one new receivable and pays once.
            ctx,page=await session(multi['frontdesk_login'],multi['store_id'])
            form=page.locator('form').filter(has=page.locator('[name=operation][value=pay]'));assert await form.count()==1
            target=multi['new_invoice_ids'][3];await form.locator(f'[name=invoice_ids][value="{target}"]').check()
            await form.locator('[name=amount]').fill('3');await form.locator('[name=channel]').select_option('alipay');await form.locator('[name=proof]').fill('P021 new-B real ordinary frontdesk synthetic payment3')
            log('intent',action='pay',invoice_id=target,amount=3);await form.locator('button[type=submit]').click()
            assert '操作已受理' in await page.locator('body').inner_text()
            await page.screenshot(path=str(c.PRIVATE/'ordinary-frontdesk-payment.png'),full_page=True);await ctx.close()
            # Group3: actual settled page exposes retained original links; current dynamic link remains separate.
            ctx,page=await session(chain['manager_login'],chain['store_id'])
            generation=page.locator('form[action="/ydental/settlement/bill-original/create/'+str(chain['invoice_id'])+'"]')
            assert await generation.count()==1
            log('intent',action='real_original_generation_POST',invoice_id=chain['invoice_id'])
            await generation.locator('button[type=submit]').click()
            assert '操作已受理' in await page.locator('body').inner_text()
            link=page.locator(f'a[href="/ydental/settlement/bill-original/{original["original_id"]}"]');assert await link.count()==1
            assert '下载已留存内部账单原件' in await link.inner_text()
            await page.screenshot(path=str(c.PRIVATE/'original-workbench.png'),full_page=True)
            log('intent',action='real_original_link_click',original_id=original['original_id'])
            async with page.expect_download() as info:await link.click()
            download=await info.value;assert await download.failure() is None
            target_file=c.PRIVATE/'UI-retained-original.pdf';await download.save_as(str(target_file))
            assert c.sha(target_file.read_bytes())==original['sha256']
            # Direct native file/thumbnail are negative security probes, never substituted for the positive UI click.
            aid=c.read(c.OUT/'original-security-result.json')['attachment_id']
            denied=[]
            for path in [f'/web/content/{aid}?download=true',f'/web/image/{aid}']:
                log('intent',action='native_attachment_denial',path=urlsplit(path).path)
                response=await ctx.request.get(BASE+path);log('response',method='GET',path=urlsplit(path).path,status=response.status,request_kind='API-negative')
                assert response.status in (403,404);denied.append({'path':urlsplit(path).path,'status':response.status})
            await ctx.close()
            c.save(c.OUT/'ordinary-Web-result.json',{'frontdesk_pay':{'invoice_id':target,'amount':3,'store_id':multi['store_id']},'original_real_UI_click':{'original_id':original['original_id'],'sha256':original['sha256']},'native_attachment_denials':denied,'contexts':2,'request_counts':counts,'not_A_replay':True})
        finally:
            stopped=True;log('stop_new_actions');await browser.close();log('browser_closed')
if __name__=='__main__':asyncio.run(main())

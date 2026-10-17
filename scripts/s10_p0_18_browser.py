"""One native Firefox login, two real workbench views and one UI download."""
import asyncio
import ast
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import unicodedata
from urllib.parse import parse_qs, urlsplit
import s10_p0_18_contract as c

DEPS=c.ROOT/'.local/s00-b-deps'
sys.path.insert(0,str(DEPS/'verify-lib'))
os.environ.update(PLAYWRIGHT_BROWSERS_PATH=str(DEPS/'browsers'),
    LD_LIBRARY_PATH=str(DEPS/'browser-libs/usr/lib/x86_64-linux-gnu'),
    FONTCONFIG_FILE=str(DEPS/'browser-fonts.conf'),DEBUG='pw:browser')
from playwright.async_api import async_playwright
import pymupdf

BASE='http://127.0.0.1:'+str(c.PORT)
LOGIN='/web/login?redirect=/ydental/settlement'
PDF='/ydental/settlement/pdf/bill/1'
LOGIN_FIELDS={'csrf_token','login','password','type','webauthn_response','redirect'}

def login_credentials(tables):
    from passlib.context import CryptContext
    fixture=c.read(c.ROOT/'.local/ydental_s10_test_20261015060000_b6c7d8e9/fixture.json')
    assert (fixture['database'],fixture['oid'])==('ydental_s10_test_20261015060000_b6c7d8e9',2100285)
    tree=ast.parse((c.ROOT/'scripts/s10_e2e_w5_browser.py').read_text())
    values=[n.args[0].value for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)
            and n.func.attr=='fill' and n.args and isinstance(n.args[0],ast.Constant) and isinstance(n.args[0].value,str)
            and isinstance(n.func.value,ast.Call) and n.func.value.args and isinstance(n.func.value.args[0],ast.Constant)
            and n.func.value.args[0].value=='[name=password]']
    assert len(values)==1
    user=c.row_map(tables['res_users'])[5]
    assert user['login']==fixture['roles']['manager'] and user['active'] and not user['share'] and user['company_id']==1
    assert CryptContext(schemes=['pbkdf2_sha512']).verify(values[0],user['password'])
    return user['login'],values[0]

async def main():
    c.checkpoint()
    t=c.read(c.PRIVATE/'target-metadata-after-rows.json')['tables']
    login,password=login_credentials(t)
    store=c.row_map(t['ydental_access_store'])[1]
    company=c.row_map(t['res_company'])[1]
    invoice=c.row_map(t['account_move'])[1]
    assert invoice['state']=='posted' and invoice['move_type']=='out_invoice' and invoice['payment_state']=='paid'
    assert float(invoice['amount_total'])==740 and float(invoice['amount_residual'])==0
    member=[r for r in t['ydental_access_membership'] if r['ydental_user_id']==5 and r['ydental_store_id']==1 and r['active']]
    assert len(member)==1
    levels={r['ydental_category']:r['ydental_level'] for r in t['ydental_access_grant'] if r['ydental_membership_id']==member[0]['id']}
    assert levels['settlement']=='write' and levels['export']=='write'
    asset_urls={r['url'] for r in t['ir_attachment'] if (r.get('url') or '').startswith('/web/assets/')}
    counts={'LOGIN_GET':0,'LOGIN_POST':0,'WORKBENCH_GET':0,'PDF_GET':0,'STATIC_RESOURCE_GET':0,'TRANSLATIONS_GET':0,'DOWNLOAD':0,'STORE_SWITCH_POST':0}
    requests=[];responses=[];errors=[];tasks=[];browser=None;failure=None;pdf_header=None
    stop=asyncio.Event();click_armed=False
    def fail(error):
        errors.append(str(error));stop.set()
    def count_request(req):
        u=urlsplit(req.url);q=parse_qs(u.query,keep_blank_values=True)
        requests.append({'method':req.method,'path':u.path,'query':q,'redirected_from':urlsplit(req.redirected_from.url).path if req.redirected_from else None})
        try:
            assert u.scheme=='http' and u.netloc==f'127.0.0.1:{c.PORT}' and not u.fragment
            if u.path=='/web/login':
                key='LOGIN_POST' if req.method=='POST' else 'LOGIN_GET'
                assert q==({'redirect':['/ydental/settlement']} if req.method=='GET' else {})
            elif u.path=='/ydental/settlement':
                assert req.method=='GET' and q in ({},{'patient_id':['1']})
                key='WORKBENCH_GET'
                if counts[key]==0:assert req.redirected_from and req.redirected_from.method=='POST'
                else:assert counts[key]==1 and q=={'patient_id':['1']}
            elif u.path==PDF:
                assert req.method=='GET' and not q and click_armed and counts['WORKBENCH_GET']==2
                key='PDF_GET'
            elif u.path=='/website/translations':
                assert req.method=='GET' and q=={'hash':[''],'lang':['zh_CN']}
                key='TRANSLATIONS_GET'
            else:
                assert req.method=='GET' and not q and u.path in asset_urls, 'REQUEST_NOT_ALLOWLISTED'
                key='STATIC_RESOURCE_GET'
            counts[key]+=1;assert counts[key]<=c.BUDGET[key],('REQUEST_BUDGET',key)
        except Exception as e:fail(e)
    async def route_handler(route):
        req=route.request;u=urlsplit(req.url)
        try:
            assert not stop.is_set(),'PRIOR_FAILURE_STOP'
            if req.method=='POST':
                assert u.path=='/web/login' and counts['LOGIN_POST']==1
                data=parse_qs(req.post_data or '',keep_blank_values=True)
                assert set(data)==LOGIN_FIELDS and all(len(v)==1 for v in data.values())
                assert data['login']==[login] and data['password']==[password] and data['redirect']==['/ydental/settlement']
                assert data['type']==['password'] and data['webauthn_response']==[''] and data['csrf_token'][0]
            await route.continue_()
        except Exception as e:
            fail(e);await route.abort()
    async def response_handler(response):
        nonlocal pdf_header
        req=response.request;u=urlsplit(response.url)
        try:
            assert response.status in (200,303),('HTTP_STATUS',u.path,response.status)
            headers=await response.all_headers()
            responses.append({'method':req.method,'path':u.path,'status':response.status,'content_type':headers.get('content-type'),'pdf_sha256':headers.get('x-ydental-pdf-sha256')})
            if req.method=='POST':assert response.status==303 and headers.get('location')=='/ydental/settlement'
            elif u.path==PDF:
                assert response.status==200 and headers.get('content-type')=='application/pdf'
                pdf_header=headers['x-ydental-pdf-sha256']
            elif u.path=='/ydental/settlement':
                assert response.status==200
                body=await response.body()
                c.save(c.PRIVATE/f'workbench-response-{sum(r["path"]==u.path for r in responses)}.json',{'status':200,'body':body.decode()})
        except Exception as e:fail(e)
    async def guarded(awaitable):
        action=asyncio.ensure_future(awaitable);blocked=asyncio.create_task(stop.wait())
        done,pending=await asyncio.wait([action,blocked],return_when=asyncio.FIRST_COMPLETED)
        for p in pending:p.cancel()
        if stop.is_set():raise AssertionError('BROWSER_STOP:'+errors[0])
        return await action
    async def check_page(page,label):
        root=page.locator('.o_ydental_settlement')
        await guarded(root.wait_for(state='visible'))
        assert await root.get_attribute('data-revision')=='1'
        assert store['name'] in await root.inner_text()
        section=root.locator('section[name=settled-bills]');assert await section.count()==1
        rows=section.locator('tbody tr');assert await rows.count()==1
        cells=await rows.locator('td').all_inner_texts()
        assert cells[0].strip()=='1' and cells[1].strip()==invoice['name']
        assert float(cells[3].strip())==740 and float(cells[4].strip())==0
        link=section.get_by_role('link',name='下载当前内部账单 PDF',exact=True)
        assert await link.count()==1 and await link.get_attribute('href')==PDF and await link.is_visible()
        assert await root.locator('input[name=invoice_ids][value="1"]').count()==0
        assert await section.locator('form,input,button').count()==0
        c.save(c.OUT/(label+'-dom.json'),{'current_store':1,'company':1,'scope_revision':1,'invoice':1,'paid_total':'740','residual':'0','invoice_in_unpaid_checkbox':False,'real_link_label':await link.inner_text(),'real_href':await link.get_attribute('href'),'settled_rows':1,'real_multi_page_sample':False})
        await page.screenshot(path=str(c.PRIVATE/(label+'.png')),full_page=True)
        return link
    try:
        async with async_playwright() as pw:
            c.save(c.PRIVATE/'firefox-launch-intent.json',{'attempt':1,'actor':5,'contexts':1})
            browser=await pw.firefox.launch(headless=True,env=os.environ.copy())
            ctx=await browser.new_context(locale='zh-CN',timezone_id='UTC',viewport={'width':1440,'height':1100},accept_downloads=True,service_workers='block')
            ctx.on('request',count_request)
            ctx.on('response',lambda r:tasks.append(asyncio.create_task(response_handler(r))))
            await ctx.route('**/*',route_handler)
            page=await ctx.new_page();page.set_default_timeout(20000)
            page.on('crash',lambda:fail('FIREFOX_CRASH'));page.on('pageerror',lambda e:fail(e))
            await guarded(page.goto(BASE+LOGIN,wait_until='domcontentloaded'))
            form=page.locator('form.oe_login_form');assert await form.count()==1
            await form.locator('[name=login]').fill(login);await form.locator('[name=password]').fill(password)
            await guarded(form.locator('button[type=submit]').click())
            await check_page(page,'default-page')
            filter_form=page.locator('form[method=get][action="/ydental/settlement"]')
            await filter_form.locator('[name=patient_id]').fill('1')
            await guarded(filter_form.locator('button[type=submit]').click())
            link=await check_page(page,'patient-page')
            assert parse_qs(urlsplit(page.url).query)=={'patient_id':['1']}
            click_armed=True
            c.save(c.PRIVATE/'pdf-click-intent.json',{'attempt':1,'from_real_page':True,'href':PDF,'label':'下载当前内部账单 PDF'})
            async with page.expect_download() as download_info:
                await guarded(link.click())
            download=await guarded(download_info.value)
            assert await download.failure() is None
            pdf=c.PRIVATE/'current-internal-bill.pdf';await download.save_as(str(pdf));counts['DOWNLOAD']=1
            await asyncio.gather(*tasks)
            assert not stop.is_set() and counts['PDF_GET']==1
            raw=pdf.read_bytes();assert raw.startswith(b'%PDF-') and 0<len(raw)<=10000000
            digest=c.sha(raw);assert digest==pdf_header
            with pymupdf.open(stream=raw,filetype='pdf') as doc:
                pages=doc.page_count;assert 1<=pages<=20
                texts=[]
                for i,pdfpage in enumerate(doc):
                    texts.append(pdfpage.get_text())
                    (c.PRIVATE/f'pdf-page-{i+1}.png').write_bytes(pdfpage.get_pixmap(matrix=pymupdf.Matrix(1.5,1.5),alpha=False).tobytes('png'))
            text=unicodedata.normalize('NFKC','\n'.join(texts)).translate(str.maketrans({'⻔':'门'}))
            (c.PRIVATE/'current-internal-bill.txt').write_text(text)
            for term in ['内部结算账单','非税务发票','非银行或支付平台到账证明','原生实收核销','当前应收余额',store['name'],company['name'],'740','600','80','40','20']:
                assert term in text,('PDF_TEXT_TERM',term)
            assert re.search(r'原生实收核销[：:\s]+740(?:\.0+)?\s+当前应收余额[：:\s]+0(?:\.0+)?',text)
            c.save(c.OUT/'pdf-result.json',{'sha256':digest,'response_sha256':pdf_header,'bytes':len(raw),'pages':pages,'readable_Chinese_text_checked':True,'visual_review':'PENDING','received_total':'740','residual':'0','historical_500_plus_240_only_verified_from_unchanged_partials':True,'original_source_amounts':[20,40,80,600],'historical_original_reprint':False})
            c.save(c.PRIVATE/'browser-success.json',{'pdf_sha256':digest})
            await browser.close();browser=None
    except BaseException as e:
        failure={'type':type(e).__name__,'detail_sha256':c.sha(str(e).encode())}
        c.save(c.PRIVATE/'browser-error.json',{'error':str(e),'prior_errors':errors})
    finally:
        if browser is not None:await browser.close()
        c.save(c.OUT/'browser-result.json',{'status':'BLOCKED' if failure else 'NATIVE_UI_PDF_DOWNLOADED_PENDING_VISUAL','counts':counts,'requests':requests,'responses':responses,'failure':failure,'page_errors':len(errors),'page_error_sha256':[c.sha(s.encode()) for s in errors]})
    if failure:raise AssertionError('BROWSER_BLOCKED')

if __name__=='__main__':
    asyncio.run(main())

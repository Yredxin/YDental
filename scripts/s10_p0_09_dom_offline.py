"""Chromium synthetic markup exercises the real refund DOM reader; Firefox/Odoo=0."""
from html import escape
import tempfile
from pathlib import Path
import hashlib
from s10_p0_09_native_contract import login_fixture
from s10_p0_09_browser import form_structure,validate_identity_dom
import json
from s10_p0_09_browser import Browser,validate_page,BASE,sync_playwright
import s10_p0_09_control as c


def markup(facts):
    rows=''.join(f'<div><p>退款 <span>{r["id"]}</span>：<span>{r["amount"]}</span>，状态 <span>{r["state"]}</span><a href="/ydental/settlement/pdf/refund/{r["id"]}">下载退款凭据 PDF</a></p></div>' for r in facts['rows'])
    nav=''
    if facts['count']>50:
        link='<a href="/ydental/settlement?refunds_page=2">下一页</a>' if facts['page']==1 else '<a href="/ydental/settlement">上一页</a>'
        nav=f'<nav aria-label="分页"><span>共 {facts["count"]} 条；第 {facts["page"]} 页</span>{link}</nav>'
    return f'<meta charset="utf-8"><main class="o_ydental_settlement" data-revision="1"><p>当前门店：<strong>{escape(facts["store_name"])}</strong></p><section><h2>线下付款与退款</h2>{rows}{nav}</section></main>'


def main():
    pre=json.loads((c.PRIVATE/'preflight-candidate.json').read_text());cases={}
    reader=Browser.__new__(Browser);reader.errors=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True)
        try:
            page=browser.new_page();page.set_default_timeout(2000)
            # Installed QWeb + auth_passkey fixture, browser native form serialization.
            for fault in ('PASS','missing','extra','duplicate','bad_redirect','bad_csrf'):
                body=login_fixture()
                if fault=='missing':body=body.replace('name="webauthn_response"','name="absent"')
                if fault=='extra':body=body.replace('</form>','<input name="UNKNOWN" value="SIMULATED_SECRET"></form>')
                if fault=='duplicate':body=body.replace('</form>','<input name="redirect" value="SIMULATED_SECRET"></form>')
                if fault=='bad_redirect':body=body.replace('value="/ydental/access"','value="/web/become"')
                if fault=='bad_csrf':body=body.replace('value="SIMULATED_CSRF"','value="WRONG"')
                page.route('**/*',lambda route,request,body=body:route.fulfill(status=200,content_type='text/html',body=body))
                page.goto(BASE+'/web/login?redirect=/ydental/access')
                form=page.locator('form')
                if fault in ('missing','extra','duplicate'):
                    try:validate_identity_dom(form_structure(form),True)
                    except AssertionError:cases['native_DOM_'+fault]='FAIL_CLOSED'
                    else:raise AssertionError(('UNEXPECTED_DOM_PASS',fault))
                else:validate_identity_dom(form_structure(form),True)
                page.unroute('**/*')
                old_private=c.PRIVATE
                with tempfile.TemporaryDirectory(prefix='s10-p008-native-route-') as dirname:
                    c.PRIVATE=Path(dirname)
                    routed=Browser.__new__(Browser)
                    routed.errors=[];routed.posts=set();routed.resource_counts={};routed.route_index=0;routed.route_gets=[]
                    routed.active_intents={6:{'actor':6,'operation':'native_login','path':'/web/login',
                        'csrf_sha256':hashlib.sha256(b'SIMULATED_CSRF').hexdigest(),
                        'login_sha256':hashlib.sha256(b'SYNTHETIC').hexdigest(),
                        'password_sha256':hashlib.sha256(b'SYNTHETIC').hexdigest()}}
                    class Adapter:
                        def __init__(self,route):self.original=route;self.request=route.request
                        def continue_(self):self.original.fulfill(status=200,body='SIMULATED_PASS')
                        def abort(self):self.original.abort()
                    page.route('**/*',lambda route:routed.route(Adapter(route),6))
                    try:
                        with page.expect_request(lambda r:r.method=='POST'):
                            form.locator('button[type=submit]').click()
                        page.wait_for_timeout(100)
                        if fault=='PASS':
                            assert routed.posts=={'login-6'} and not routed.errors
                            cases['native_form_actual_serialization']='SIMULATED_DOM_PASS'
                            allowed=json.loads(next(c.PRIVATE.glob('route-allowed-*.json')).read_text())
                            assert allowed['field_counts']['webauthn_response']==1
                        else:
                            assert routed.errors
                            proof=json.loads(next(c.PRIVATE.glob('route-failure-*.json')).read_text())
                            assert proof['failure_code'] and proof['location']['line']>0
                            assert 'SIMULATED_SECRET' not in json.dumps(proof)
                            cases['native_route_'+fault]='FAIL_CLOSED'
                    finally:
                        c.PRIVATE=old_private
                        page.unroute('**/*')

            # Routed GET fixture, no Odoo or external network.
            for key,actor in (('1-1',6),('1-2',6),('3-1',14)):
                facts=pre['refund_pages'][key];body=markup(facts)
                url=BASE+'/ydental/settlement'+('?refunds_page=2' if facts['page']==2 else '')
                page.route('**/*',lambda route,request,body=body:route.fulfill(status=200,content_type='text/html',body=body))
                page.goto(url,wait_until='domcontentloaded')
                dom=reader.read_dom(page,200);validate_page(dom,facts,actor,pre['selection']['selected'])
                cases[key]='SIMULATED_DOM_PASS';page.unroute('**/*')
            facts=pre['refund_pages']['1-2']
            for fault in ('wrong_id','wrong_state','wrong_link','missing_main','wrong_pagination'):
                body=markup(facts)
                if fault=='wrong_id':body=body.replace('<span>13</span>','<span>99</span>')
                if fault=='wrong_state':body=body.replace('状态 <span>requested</span>','状态 <span>done</span>',1)
                if fault=='wrong_link':body=body.replace('/pdf/refund/13','/pdf/refund/99')
                if fault=='missing_main':body=body.replace('o_ydental_settlement','absent')
                if fault=='wrong_pagination':body=body.replace('共 63 条','共 64 条')
                page.route('**/*',lambda route,request,body=body:route.fulfill(status=200,content_type='text/html',body=body))
                page.goto(BASE+'/ydental/settlement?refunds_page=2',wait_until='domcontentloaded')
                try:
                    dom=reader.read_dom(page,200);validate_page(dom,facts,6,pre['selection']['selected'])
                except Exception:cases[fault]='FAIL_CLOSED'
                else:raise AssertionError(('UNEXPECTED_PASS',fault))
                page.unroute('**/*')
        finally:browser.close()
    print(json.dumps({'status':'SIMULATED_DOM_PASS','count':len(cases),'cases':cases,'firefox':0,'odoo':0}))


if __name__=='__main__':main()

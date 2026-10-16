"""Chromium synthetic markup exercises the real refund DOM reader; Firefox/Odoo=0."""
from html import escape
import json
from s10_p0_07_browser import Browser,validate_page,BASE,sync_playwright
import s10_p0_07_control as c


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

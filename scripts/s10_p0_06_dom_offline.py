"""Same locator/submit with Chromium and synthetic loopback fixture; no Odoo or Firefox."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from urllib.parse import parse_qs, urlsplit
from s10_p0_06_browser import (sync_playwright, Browser, stable_cross_form, read_fields,
    validate_form, validate_response, BASE)


def fixture(record=63, feedback=''):
    return ('<main class="o_ydental_settlement" data-revision="1">'+feedback+
        '<form method="post" action="/ydental/settlement/action">'+''.join(
        f'<input type="hidden" name="{k}" value="{v}">'
        for k,v in {'close_id':record,'operation':'unlock','output':'html',
                    'csrf_token':'OFFLINE_OWN_CSRF','revision':1,'key':'OFFLINE_NEW_KEY'}.items())+
        '<input name="reason" required><button type="submit">Unlock</button></form></main>')


def main():
    cases={}
    posted=[]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def do_GET(self):
            feedback=('<div data-ui1-feedback="1">请求未完成，请核对权限、门店或输入后重试。</div>'
                      if urlsplit(self.path).query else '')
            data=fixture(feedback=feedback).encode()
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8')
            self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
        def do_POST(self):
            assert self.path=='/ydental/settlement/action'
            posted.append(parse_qs(self.rfile.read(int(self.headers['Content-Length'])).decode()))
            self.send_response(303);self.send_header('Location','/ydental/settlement?notice=OFFLINE_DENIED')
            self.send_header('Content-Length','0');self.end_headers()
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    base='http://127.0.0.1:'+str(server.server_port)
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        context=browser.new_context()
        page=context.new_page();page.set_default_timeout(2000)
        context.route('**/*',lambda r:r.continue_() if urlsplit(r.request.url).hostname=='127.0.0.1'
                      and urlsplit(r.request.url).port==server.server_port else r.abort())
        page.goto(base+'/ydental/settlement')
        # The P004 selector is reacquired after mutation and demonstrably loses its target.
        old=page.locator('form:has(input[name=close_id][value="63"])')
        old.locator('input[name=close_id]').evaluate('(el)=>{el.value="9"}')
        assert old.count()==0
        cases['P004_dynamic_selector_after_mutation']='FAIL_CLOSED'
        page.goto(base+'/ydental/settlement')
        form,fields=stable_cross_form(page,'P006 OFFLINE denial')
        assert fields['record']=='9';cases['stable_same_node_63_to_9']='SIMULATED_PASS'
        fake=Browser.__new__(Browser);fake.sent=set();fake.page_users={page:14}
        fake.requests=[];fake.gets=[]
        context.on('request',lambda request:Browser.note_request(fake,14,request))
        response=Browser.submit(fake,page,form,'unlock',9)
        assert len(fake.requests)==1 and 'notice=' in fake.requests[0]['url']
        cases['redirect_GET_observed_by_same_request_event']='SIMULATED_PASS'
        response['server_denial_log']=True
        validate_response(response,'unlock',9,accepted=False)
        assert response['landing_status']==200 and len(posted)==1 and posted[0]['close_id']==['9']
        cases['same_submit_303_denied_redirect200']='SIMULATED_PASS'
        for name,field,value in (('bad_csrf','csrf_token',''),('bad_revision','revision','2'),
                ('bad_key','key',''),('bad_reason','reason',''),('bad_output','output','json'),
                ('bad_operation','operation','refund_reject')):
            page.goto(base+'/ydental/settlement')
            form,_=stable_cross_form(page,'OFFLINE valid reason')
            form.locator('input[name='+field+']').evaluate('(el,v)=>{el.value=v}',value)
            try:
                validate_form(read_fields(page,form),'unlock',9)
            except AssertionError:
                cases[name]='FAIL_CLOSED'
            else: raise AssertionError(('negative unexpectedly passed',name))
        assert len(posted)==1
        context.close();browser.close()
    server.shutdown();server.server_close();thread.join()
    print(json.dumps({'status':'SIMULATED_DOM_PASS','browser':'Chromium + synthetic loopback fixture (no Odoo)',
                      'real_firefox':0,'real_http':0,'cases':cases}))


if __name__=='__main__': main()

import argparse,configparser,hashlib,json,os,re,sys
from pathlib import Path
from urllib.parse import urlsplit
import psycopg2
root=Path('/home/redxin/code/odoo/odoo-sd/code/sd-addons')
deps=root/'.local/s00-b-deps'
sys.path.insert(0,str(deps/'verify-lib'))
os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH',str(deps/'browsers'))
os.environ.setdefault('LD_LIBRARY_PATH',str(deps/'browser-libs/usr/lib/x86_64-linux-gnu'))
os.environ.setdefault('FONTCONFIG_FILE',str(deps/'browser-fonts.conf'))
from playwright.sync_api import sync_playwright
parser=argparse.ArgumentParser();parser.add_argument('--db',required=True);parser.add_argument('--port',required=True,type=int);parser.add_argument('--pid',required=True,type=int);args=parser.parse_args()
assert re.fullmatch(r'ydental_s10_test_[0-9]{14}_[a-f0-9]{8}',args.db)
run=root/'.local'/args.db
marker=json.loads((run/'database.json').read_text())
assert marker['database']==args.db and marker['port']==args.port and marker['cluster']=='7694897083368259627'
assert marker['config_sha256']==hashlib.sha256((run/'odoo.conf').read_bytes()).hexdigest()
pid=args.pid
assert b'.local/'+run.name.encode()+b'/odoo.conf' in Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')
assert Path(f'/proc/{pid}/cwd').resolve()==root
f5=json.loads((run/'f5.json').read_text())
c=configparser.ConfigParser();c.read(run/'odoo.conf')
with psycopg2.connect(host='127.0.0.1',port=5432,user='odoo',password=c['options']['db_password'],dbname=run.name) as db:
 db.set_session(readonly=True)
 with db.cursor() as cr:
  cr.execute('select login from res_users where id=%s',(f5['manager_id'],));login=cr.fetchone()[0]
base=f'http://127.0.0.1:{args.port}'
with sync_playwright() as p:
 browser=p.firefox.launch(headless=True)
 context=browser.new_context(viewport={'width':1440,'height':900},locale='zh-CN')
 context.route('**/*',lambda route:route.continue_() if urlsplit(route.request.url).hostname=='127.0.0.1' and urlsplit(route.request.url).port==args.port else route.abort())
 page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(base+'/web/login?redirect=/ydental/access',wait_until='domcontentloaded')
 page.locator('[name=login]').fill(login);page.locator('[name=password]').fill('s05-test-password');page.locator('button[type=submit]').click()
 page.wait_for_url('**/ydental/access')
 result=page.evaluate('''async store => { const body=new URLSearchParams({operation:'switch',revision:document.querySelector('[name=revision]').value,csrf_token:document.querySelector('[name=csrf_token]').value,output:'json',payload:JSON.stringify({store_id:store})});const r=await fetch('/ydental/access/action',{method:'POST',body});return {status:r.status,data:await r.json()};}''',f5['store_id'])
 assert result['status']==200,result
 page.goto(base+'/ydental/settlement',wait_until='domcontentloaded')
 assert page.locator('h1').inner_text()=='线下结算工作台'
 assert page.get_by_text('170.0',exact=True).count()>=1
 page.screenshot(path=str(run/'firefox-before.png'),full_page=True)
 form=page.locator('form:has(input[name="operation"][value="pay"])')
 assert form.count()==1
 form.locator(f'input[name="invoice_ids"][value="{f5["new_invoice_id"]}"]').check()
 form.locator('input[name="amount"]').fill('10')
 form.locator('select[name="channel"]').select_option('alipay')
 form.locator('input[name="proof"]').fill('Synthetic Firefox actual offline 10')
 with page.expect_response('**/ydental/settlement/action') as response:
  form.locator('button[type=submit]').click()
 reply=response.value
 assert reply.status==200,(reply.status,reply.text())
 data=reply.json();assert data['amount']==10,data
 page.goto(base+'/ydental/settlement',wait_until='domcontentloaded')
 assert page.get_by_text('160.0',exact=True).count()>=1
 page.screenshot(path=str(run/'firefox-after.png'),full_page=True)
 print('S10_FIREFOX_BUTTON',json.dumps({'login':login,'store':f5['store_id'],'invoice':f5['new_invoice_id'],'native_payment':data['native_payment_id'],'amount':data['amount'],'pageerrors':errors,'screenshots':['firefox-before.png','firefox-after.png']}),flush=True)
 assert not errors
 context.close();browser.close()

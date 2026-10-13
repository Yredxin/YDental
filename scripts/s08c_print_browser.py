"""Firefox real controlled PDF previews, downloads, and native print dialogs."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import sys
import time
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1];deps=ROOT/'.local/s00-b-deps';sys.path.insert(0,str(deps/'verify-lib'))
os.environ['PLAYWRIGHT_BROWSERS_PATH']=str(deps/'browsers');os.environ['LD_LIBRARY_PATH']=str(deps/'browser-libs/usr/lib/x86_64-linux-gnu');os.environ['FONTCONFIG_FILE']=str(deps/'browser-fonts.conf')
from playwright.sync_api import sync_playwright
from PIL import ImageGrab

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def require(value,message):
 if not value:raise AssertionError(message)
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--db',required=True);parser.add_argument('--port',type=int,required=True);args=parser.parse_args()
require(re.fullmatch(r'ydental_s08c_test_[0-9]{14}_[a-f0-9]{8}',args.db),'isolated C database required')
run=ROOT/'.local'/args.db;meta=json.loads((run/'database.json').read_text())
require(meta['database']==args.db and meta['port']==args.port and meta['cluster']=='7694897083368259627','database identity')
require(sha(run/'odoo.conf')==meta['config_sha256'],'config identity')
pid=int((run/'serve.pid').read_text());require(str(run/'odoo.conf').encode() in Path('/proc/%s/cmdline'%pid).read_bytes().split(b'\0'),'dedicated preview PID')
creds_path=run/'print-access.json';require(stat.S_IMODE(creds_path.stat().st_mode)==0o600,'private credentials')
access=json.loads(creds_path.read_text());preview=json.loads((run/'print-preview.json').read_text())
require(not any(os.environ.get(k) for k in ['MOZ_DISABLE_CONTENT_SANDBOX','MOZ_DISABLE_RDD_SANDBOX','MOZ_DISABLE_GMP_SANDBOX','DEBUG','PWDEBUG']),'no sandbox overrides')
require(not subprocess.check_output(['git','-C',str(ROOT),'status','--porcelain','--','ydental_print','ydental_print_test','scripts/s08c*'],text=True),'committed implementation')
evidence=ROOT/'docs/evidence/s08c/print-browser-attempts'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f');evidence.mkdir(parents=True)
result={'database':args.db,'tested_commit':subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip(),'browser':'Firefox headed, native print dialog, default sandbox','checks':[],'screenshots':[],'pageerrors':[],'physical_paper':'UNKNOWN'}
sensitive=[v[k] for v in access.values() for k in ('login','password')]
base='http://127.0.0.1:'+str(args.port)
tools=ROOT/'.local/s08c-tools/root/usr/bin';lib=ROOT/'.local/s08c-tools/root/usr/lib/x86_64-linux-gnu'
display=':107';require(not Path('/tmp/.X107-lock').exists(),'display already occupied; do not reuse')
xenv=os.environ|{'LD_LIBRARY_PATH':str(lib)+':'+os.environ['LD_LIBRARY_PATH'],'DISPLAY':display}
log=(run/'xvfb.log').open('a');xvfb=subprocess.Popen(['bwrap','--die-with-parent','--ro-bind','/','/','--bind','/tmp','/tmp','--tmpfs','/usr/bin','--ro-bind','/usr/bin/dash','/usr/bin/sh','--ro-bind',str(tools/'xkbcomp'),'/usr/bin/xkbcomp',str(tools/'Xvfb'),display,'-screen','0','1600x1200x24','-nolisten','tcp','-ac','-noreset'],env=xenv,stdout=log,stderr=log)
def check(name,value):require(value,name);result['checks'].append({'check':name,'result':'PASS'})
def screenshot(page,name,desktop=False):
 if not desktop:
  require(not any(s in page.locator('body').inner_text() for s in sensitive),'visible credential')
  require(page.locator('input[type=password]:visible').count()==0,'password field visible')
 path=evidence/(name+'.png')
 if desktop:ImageGrab.grab(xdisplay=display).save(path)
 else:page.screenshot(path=str(path),full_page=True)
 result['screenshots'].append({'path':str(path.relative_to(ROOT)),'sha256':sha(path),'kind':'native print dialog desktop' if desktop else 'Firefox page'})
def key(name):subprocess.run([str(tools/'xdotool'),'key','--clearmodifiers',name],env=xenv,check=True,capture_output=True)
try:
 for _ in range(50):
  if Path('/tmp/.X11-unix/X107').exists():break
  time.sleep(.1)
 require(xvfb.poll() is None and Path('/tmp/.X11-unix/X107').exists(),'independent Xvfb display')
 with sync_playwright() as engine:
  browser=engine.firefox.launch(headless=False,env=os.environ|{'DISPLAY':display})
  def login(role):
   context=browser.new_context(viewport={'width':1440,'height':1000},locale='zh-CN',accept_downloads=True)
   context.route('**/*',lambda route:route.continue_() if urlsplit(route.request.url).hostname=='127.0.0.1' and urlsplit(route.request.url).port==args.port or route.request.url.startswith('blob:') else route.abort())
   page=context.new_page();page.on('pageerror',lambda error:result['pageerrors'].append(str(error)))
   page.goto(base+'/web/login?redirect=/ydental/access',wait_until='domcontentloaded');page.locator('[name=login]').fill(access[role]['login']);page.locator('[name=password]').fill(access[role]['password']);page.locator('button[type=submit]').click();page.wait_for_url('**/ydental/access')
   response=page.evaluate("async store=>{const b=new URLSearchParams({operation:'switch',revision:document.querySelector('[name=revision]').value,csrf_token:document.querySelector('[name=csrf_token]').value,output:'json',payload:JSON.stringify({store_id:store})});return (await fetch('/ydental/access/action',{method:'POST',body:b})).json()}",preview['store']);check(role+' selects current store',type(response.get('revision')) is int)
   page.goto(base+'/ydental/print',wait_until='networkidle');return context,page
  context,page=login('doctor');screenshot(page,'01-entry')
  def select(source):
   page.locator('#print-kind').select_option(source['kind']);page.locator('#print-source').fill(str(source['source_id']));page.locator('#print-version').fill(str(source['version']))
  def click(operation,status=200):
   selectors={'preview':'preview','generate':'generate','pdf_view':'view','download':'download','print_request':'request'}
   with page.expect_response(lambda r:r.url==base+'/ydental/print/action' and r.request.post_data and 'operation='+operation in r.request.post_data) as response:page.locator('#print-'+selectors[operation]).click()
   response=response.value;check(operation+' HTTP '+str(status),response.status==status);return response
  for name in ('clinical','prescription','consent'):
   select(preview[name]);click('preview');page.wait_for_function("!document.querySelector('#print-generate').disabled")
   text=page.frame_locator('#print-html').locator('body').inner_text();check(name+' real Chinese source preview','演示' in text and ('待完善' in text if name=='clinical' else '未签署' in text if name=='consent' else '未领数量' in text))
   screenshot(page,name+'-review');click('generate');page.wait_for_function("!document.querySelector('#print-view').disabled")
   view=click('pdf_view');check(name+' true PDF binary',view.body().startswith(b'%PDF-'))
   page.wait_for_timeout(1200);screenshot(page,name+'-pdf-view')
   with page.expect_download() as downloaded:click('download')
   target=evidence/(name+'-firefox-download.pdf');downloaded.value.save_as(target);check(name+' downloaded true binary',target.read_bytes().startswith(b'%PDF-'))
   click('print_request');page.wait_for_timeout(3000);screenshot(page,name+'-native-print-dialog',desktop=True)
   # A person inspects the captured native dialog. Cancel without submitting
   # a printer/file output; there is no device receipt or printed claim.
   key('Escape');page.wait_for_timeout(800)
   check(name+' request distinct from physical paper','实际出纸' in page.locator('#print-result').inner_text() or '出纸状态未知' in page.locator('#print-result').inner_text())
  # Hold a real generated HTTP response: inputs stay frozen while in flight.
  select(preview['consent']);click('preview');page.wait_for_function("!document.querySelector('#print-generate').disabled")
  held=[]
  def hold(route):held.append((route,route.fetch()))
  page.route('**/ydental/print/action',hold);page.locator('#print-generate').click()
  page.wait_for_timeout(1300);check('held generation response freezes source',page.locator('#print-source').is_disabled() and page.locator('#print-request').is_disabled());screenshot(page,'held-generation')
  require(len(held)==1,'one actual held response');route,response=held.pop();route.fulfill(response=response);page.unroute('**/ydental/print/action',hold);page.wait_for_function("!document.querySelector('#print-view').disabled")
  # Lose an actual committed response; the browser must not invent success/replay.
  select(preview['consent']);click('preview');page.wait_for_function("!document.querySelector('#print-generate').disabled")
  def lose(route):
   response=route.fetch();result['lost_response_status']=response.status;route.abort()
  page.route('**/ydental/print/action',lose);page.locator('#print-generate').click();page.wait_for_function("document.querySelector('#print-result').textContent.includes('响应未确认')")
  check('lost response disables actions without fake success',page.locator('#print-request').is_disabled() and result['lost_response_status']==200);screenshot(page,'lost-generation-response');page.unroute('**/ydental/print/action',lose)
  context.set_offline(True);page.locator('#print-preview').click();page.wait_for_function("document.querySelector('#print-result').textContent.includes('响应未确认')");check('offline no false PDF success',page.locator('#print-generate').is_disabled());screenshot(page,'offline-failure');context.set_offline(False);context.close()
  denied_context,denied=login('reader');select_source=preview['clinical']
  denied.locator('#print-source').fill(str(select_source['source_id']));denied.locator('#print-version').fill(str(select_source['version']))
  with denied.expect_response(lambda r:r.url==base+'/ydental/print/action') as response:denied.locator('#print-preview').click()
  check('reader without export denied by server',response.value.status==403);denied.wait_for_timeout(300);screenshot(denied,'reader-export-denied');denied_context.close()
  check('no Firefox pageerror',not result['pageerrors']);browser.close()
 result['result']='PASS';result['native_dialog_visual_review']='PENDING'
except Exception as error:
 import traceback
 result['result']='FAIL';result['failure']={'type':type(error).__name__,'detail':str(error)[:700],'trace':traceback.format_exc()}
finally:
 if xvfb.poll() is None:xvfb.terminate()
 result['xvfb_exit']=xvfb.wait(timeout=10);log.close();(evidence/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'result':result['result'],'checks':len(result['checks']),'screenshots':len(result['screenshots']),'pageerrors':len(result['pageerrors'])}))
assert result['result']=='PASS',result.get('failure')

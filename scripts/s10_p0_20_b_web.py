"""Own B service and ordinary Firefox; stop new actions before readonly tail."""
import json
import socket
import subprocess
import time
import s10_p0_20_contract as c
from s10_p0_20_b_control import RUN,PORT
from s10_p0_20_control import native_env
c.checkpoint();c.save(c.PRIVATE/'B-Web-intent.json',{'service':1,'browser_context':1,'ordinary_frontdesk_payment_POST':1})
http=None;browser=None;result={'status':'BLOCKED'}
try:
    with (RUN/'http.log').open('xb') as f:
        http=subprocess.Popen([str(c.PYTHON),str(c.CORE_ROOT/'odoo-bin'),'-c',str(RUN/'odoo.conf')],cwd=c.ROOT,env=native_env(),stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT)
    start=time.monotonic()
    while True:
        assert http.poll() is None
        try:
            with socket.create_connection(('127.0.0.1',PORT),timeout=1):break
        except OSError:
            assert time.monotonic()-start<60;time.sleep(.25)
    with (RUN/'browser.log').open('xb') as f:
        browser=subprocess.Popen([str(c.PYTHON),str(c.ROOT/'scripts/s10_p0_20_b_browser.py')],cwd=c.ROOT,env=native_env(),stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT)
        try:rc=browser.wait(timeout=180)
        except subprocess.TimeoutExpired:
            browser.terminate();browser.wait(timeout=20);raise
    result['browser_exit_code']=rc;assert rc==0
    result['status']='NATIVE_WEB_COMPLETED_PENDING_READONLY_ECONOMIC_AUDIT'
finally:
    c.save(c.PRIVATE/'B-stop-new-actions.json',{'new_business_action_gate':'CLOSED','browser_exit':browser.poll() if browser else None})
    if browser and browser.poll() is None:browser.terminate();browser.wait(timeout=20)
    if http and http.poll() is None:http.terminate();http.wait(timeout=20)
    result['http_exit_code']=http.returncode if http else None
    c.save(c.OUT/'B-Web-result.json',result)
print(json.dumps(result))

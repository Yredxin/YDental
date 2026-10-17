"""Owned B-only service; browser shutdown before independent final audit."""
import json
import socket
import subprocess
import time
import s10_p0_21_contract as c
from s10_p0_21_control import native_env
c.gate();c.save(c.PRIVATE/'Web-intent.json',{'HTTP_process':1,'Firefox_process':1,'contexts':2,'old_business_connections':0})
p=None;b=None;status={'status':'BLOCKED'}
try:
    with (c.RUN/'http.log').open('xb') as f:p=subprocess.Popen([str(c.PYTHON),str(c.CORE_ROOT/'odoo-bin'),'-c',str(c.RUN/'odoo.conf')],cwd=c.ROOT,env=native_env('http'),stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT)
    begin=time.monotonic()
    while True:
        assert p.poll() is None
        try:
            with socket.create_connection(('127.0.0.1',c.PORT),timeout=1):break
        except OSError:assert time.monotonic()-begin<60;time.sleep(.25)
    with (c.RUN/'browser.log').open('xb') as f:
        b=subprocess.Popen([str(c.PYTHON),str(c.ROOT/'scripts/s10_p0_21_browser.py')],cwd=c.ROOT,env=native_env('browser'),stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT)
        try:rc=b.wait(timeout=240)
        except subprocess.TimeoutExpired:b.terminate();b.wait(timeout=20);raise
    status['browser_exit_code']=rc;assert rc==0
    status['status']='ORDINARY_WEB_COMPLETE_PENDING_INDEPENDENT_STORAGE_AUDIT'
finally:
    c.event('Web_stop_new_actions')
    if b and b.poll() is None:b.terminate();b.wait(timeout=20)
    if p and p.poll() is None:p.terminate();p.wait(timeout=20)
    status['HTTP_exit_code']=p.returncode if p else None;c.save(c.OUT/'Web-result.json',status)
print(json.dumps(status))

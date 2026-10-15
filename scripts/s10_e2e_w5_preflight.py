"""W5 pre-CREATE gate.  No database writes, Odoo registry or browser process."""

import hashlib
import json
from lxml import etree
from pathlib import Path
import socket
import subprocess
import sys
import tempfile

import s10_e2e_w5_control as control
from s10_e2e_w5_control import (BROWSER_ARGV, HTTP_ARGV, PREFLIGHT, SCRIPTS,
    file_identity, no_parallel_w5, write_once, write_text_once)
from s10_e2e_w5_snapshot import (BASE, CORE_HEAD, NAME, PORT, ROOT, SOURCE,
    SOURCE_OID, canonical, database_identity, digest, source_audit, state)


def html_contract():
    path = ROOT / 'ydental_settlement/views/ydental_settlement_templates.xml'
    doc = etree.parse(str(path))
    tokens = doc.xpath('//*[@id="ydental_settlement_tokens"]')
    assert len(tokens) == 1
    assert len(tokens[0].xpath('./input[@name="output"][@value="html"]')) == 1
    page = doc.xpath('//*[@id="ydental_settlement_page"]')
    assert len(page) == 1
    forms = page[0].xpath('.//form[.//input[@name="operation"][@value="pay"]]')
    assert len(forms) == 1
    form = forms[0]
    assert form.get('method') == 'post' and form.get('action') == '/ydental/settlement/action'
    assert len(form.xpath('.//*[@t-call="ydental_settlement.ydental_settlement_tokens"]')) == 1
    for name in ('invoice_ids','amount','channel','actual_utc','proof'):
        assert len(form.xpath('.//*[@name="'+name+'"]')) == 1
    assert len(form.xpath('.//option[@value="cash"]')) == 1
    for name in ('amount','actual_utc','proof'):
        assert form.xpath('.//*[@name="'+name+'"]')[0].get('required') == 'required'
    controller = (ROOT / 'ydental_settlement/controllers/settlement.py').read_text()
    assert "post.get('output') == 'html'" in controller
    assert "mimetype == 'application/x-www-form-urlencoded'" in controller
    assert "self._html_feedback('already_accepted' if result.get('result')" in controller
    return {'qweb_sha256': digest(path), 'pay_form_fields': ['invoice_ids','amount','channel','actual_utc','proof'],
            'token_fields': ['csrf_token','revision','key','output'],
            'controller_sha256': digest(ROOT / 'ydental_settlement/controllers/settlement.py')}


def run_offline(name):
    output = subprocess.check_output([sys.executable, str(ROOT / 'scripts' / name)],
                                     cwd=ROOT, text=True)
    return json.loads(output.strip())


def writer_and_checkpoint_contract():
    with tempfile.TemporaryDirectory(prefix='s10-w5-gate-') as folder:
        root = Path(folder)
        path = root / 'typed.json'
        write_once(path, {'amount':500,'complete':True})
        assert json.loads(path.read_text()) == {'amount':500,'complete':True}
        try:
            write_once(path, {'amount':240})
        except FileExistsError:
            pass
        else:
            raise AssertionError('write_once replaced committed evidence')
        plain = root / 'plain.conf'
        write_text_once(plain, 'private_config=SIMULATED_ONLY\n')
        assert plain.read_text() == 'private_config=SIMULATED_ONLY\n'
        simulated_preflight = root / 'preflight.json'
        simulated_preflight.write_text(json.dumps({'source':{'oid':SOURCE_OID},'target':NAME,
            'scripts_sha256':{str(path.relative_to(ROOT)):digest(path) for path in SCRIPTS},
            'http_argv':list(HTTP_ARGV),
            'browser_argv':list(BROWSER_ARGV)}))
        simulated_checkpoint = root / 'checkpoint.json'
        simulated_checkpoint.write_text(json.dumps({'comment_id':6186596168,
            'body_sha256':'a'*64,'preflight_sha256':digest(simulated_preflight)}))
        old_preflight, old_checkpoint = control.PREFLIGHT, control.CHECKPOINT
        try:
            control.PREFLIGHT, control.CHECKPOINT = simulated_preflight, simulated_checkpoint
            assert control.checkpoint()['comment_id'] == 6186596168
            simulated_checkpoint.write_text(json.dumps({'comment_id':6186596168,
                'body_sha256':'a'*64,'preflight_sha256':'0'*64}))
            try:
                control.checkpoint()
            except AssertionError:
                pass
            else:
                raise AssertionError('stale checkpoint did not STOP')
        finally:
            control.PREFLIGHT, control.CHECKPOINT = old_preflight, old_checkpoint
    return {'atomic_writer':'PASS','one_shot_writer':'PASS','checkpoint_positive':'PASS',
            'checkpoint_tamper_stop':'PASS'}


def main():
    assert not PREFLIGHT.exists()
    file_identity(check_remote=True)
    no_parallel_w5()
    rows, activity = database_identity()
    assert rows == {SOURCE:SOURCE_OID} and activity == []
    assert not (ROOT / '.local' / NAME).exists()
    assert not (ROOT / '.local/s10-e2e-w5-create-attempt.json').exists()
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', PORT))
    source = source_audit()
    full_source = state(SOURCE)
    assert source['filestore']['file_count'] == 152
    assert source['filestore']['pointer_count'] == 164
    assert len(source['exact']) == 38
    previous = json.loads((ROOT / 'docs/evidence/s10-e2e-w4/verification.json').read_text())
    assert source['exact'] == previous['source']['exact_signatures']
    assert source['filestore']['manifest_sha256'] == previous['target']['filestore']['manifest_sha256']
    assert source['filestore']['attachment_pointers_sha256'] == previous['target']['filestore']['attachment_pointers_sha256']
    contract = html_contract()
    parser = run_offline('s10_e2e_w5_cli_offline.py')
    assert parser['status'] == 'REAL_ODOO20_CLI_PASS'
    offline = run_offline('s10_e2e_w5_offline.py')
    assert offline['status'] == 'OFFLINE_PASS' and offline['case_count'] >= 24
    writer = writer_and_checkpoint_contract()
    scripts = {str(path.relative_to(ROOT)): digest(path) for path in SCRIPTS}
    authority = {}
    for issue in (23,29,30,31,32,33,34,35):
        stored = json.loads((Path('/tmp/ydental-w5-authority') / f'{issue}.json').read_text())
        authority[str(issue)] = {'state': stored['issue']['state'],
            'comments':len(stored['comments']),
            'last_comment_id':stored['comments'][-1]['id'] if stored['comments'] else None,
            'body_sha256':hashlib.sha256((stored['issue']['body'] or '').encode()).hexdigest()}
    assert authority['34']['last_comment_id'] == 6186596167
    assert authority['35']['state'] == 'open' and authority['35']['comments'] == 0
    result = {'status':'PREFLIGHT_PASS_CREATE0','authorization':6186596167,
        'w4_review':6186530230,'base_head':BASE,'core_head':CORE_HEAD,
        'source':{'database':SOURCE,'oid':SOURCE_OID,'module_count':source['module_count'],
            'module_names_sha256':source['modules_sha256'],'filestore':source['filestore'],
            'exact_table_count':len(source['exact']),'exact_signatures':source['exact'],
            'installed_views':source['view'],
            'money_sha256':hashlib.sha256(canonical(full_source['money']).encode()).hexdigest(),
            'module_meta_sha256':hashlib.sha256(canonical(full_source['module_meta']).encode()).hexdigest(),
            'invoice':{'id':1,'total':'740','residual':'740','posted':True},
            'fees':['600','80','40','20'],'native_payment_count':0,'partial_count':0},
        'target':NAME,'port':PORT,'target_preexisting':False,'port_free':True,
        'html_contract':contract,'cli':parser,'offline':offline,'writer':writer,
        'issue_authority':authority,
        'scripts_sha256':scripts,
        'http_argv':list(HTTP_ARGV),'browser_argv':list(BROWSER_ARGV),
        'resource_budgets':{'create':1,'upgrade':0,'odoo_shell':0,
            'http':1,'http_start_seconds':180,'http_total_seconds':1200,
            'firefox_playwright':1,'browser_seconds':1200,'other_shell':0,
            'successful_payment_amounts':[500,240]}}
    write_once(PREFLIGHT, result)
    print(json.dumps({'status':result['status'],'source_oid':SOURCE_OID,
        'script_count':len(scripts),'offline_cases':offline['case_count'],
        'preflight_sha256':digest(PREFLIGHT)}))


if __name__ == '__main__':
    main()

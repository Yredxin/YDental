"""Real Firefox S02 UI evidence against only a recorded loopback preview.

No security overrides, profile/cookie export or credential output. Screenshots
contain only synthetic store/staff/source data. Failures remain in history.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess

from playwright.sync_api import sync_playwright
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]


def require(condition, reason):
    if not condition:
        raise RuntimeError(reason)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', required=True)
    parser.add_argument('--port', type=int, default=18102)
    parser.add_argument('--evidence', default='s02')
    args = parser.parse_args()
    require(18000 <= args.port <= 18999, 'Isolated port refused')
    require(re.fullmatch(r'ydental_s02_test_[0-9]{14}_[a-f0-9]{8}', args.db), 'Database name refused')
    run = ROOT / '.local' / args.db
    require(not run.is_symlink(), 'Symlink run refused')
    metadata = json.loads((run / 'database.json').read_text())
    require(metadata['database'] == args.db and metadata['cluster'] == '7694897083368259627'
            and metadata['endpoint'] == {'host': '127.0.0.1', 'port': '5432', 'user': 'odoo'}
            and metadata['port'] == args.port, 'Preview identity mismatch')
    require(sha(run / 'odoo.conf') == metadata['config_sha256'], 'Runtime configuration changed')
    pid = int((run / 'serve.pid').read_text())
    require(str(run / 'odoo.conf').encode() in Path('/proc/%s/cmdline' % pid).read_bytes().split(b'\0'), 'Preview PID mismatch')
    require(not any(os.environ.get(k) for k in ('MOZ_DISABLE_CONTENT_SANDBOX', 'MOZ_DISABLE_RDD_SANDBOX',
            'MOZ_DISABLE_GMP_SANDBOX', 'WEBKIT_DISABLE_SANDBOX_THIS_IS_DANGEROUS', 'DEBUG', 'PWDEBUG')), 'Unsafe browser settings refused')
    credentials = run / 'access.json'
    require(not credentials.is_symlink() and stat.S_IMODE(credentials.stat().st_mode) == 0o600
            and credentials.stat().st_uid == os.getuid(), 'Private credential permissions mismatch')
    access = json.loads(credentials.read_text())
    preview = json.loads((run / 'preview.json').read_text())
    base = 'http://127.0.0.1:%s' % args.port
    commit = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
    require(not subprocess.check_output(['git', '-C', str(ROOT), 'status', '--porcelain', '--',
            'ydental_space', 'ydental_space_test', 'scripts/s02.py', 'scripts/s02_probe.py', 'scripts/s02_browser.py'], text=True),
            'Commit implementation and browser code before verification')
    evidence = ROOT / 'docs/evidence' / args.evidence
    evidence.mkdir(parents=True, exist_ok=True)
    attempt = evidence / ('browser-attempts/' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f'))
    attempt.mkdir(parents=True)
    result = {'scope': 'S02 synthetic UI only', 'tested_commit': commit, 'database': args.db,
              'started_utc': datetime.now(timezone.utc).isoformat(), 'browser': 'Firefox',
              'sandbox': 'default; no overrides', 'checks': [], 'screenshots': []}
    secrets = {str(value[k]) for value in access.values() for k in ('login', 'password')}

    def record(name, assertion):
        require(assertion, name)
        result['checks'].append({'check': name, 'result': 'PASS'})

    def snapshot(page, context, name):
        secrets.update(c['value'] for c in context.cookies() if re.search('session|csrf|token|auth', c['name'], re.I))
        text = page.locator('body').inner_text()
        require(not any(s and s in text for s in secrets), 'Visible credential or cookie; screenshot refused')
        require(page.locator('input[type=password]:visible').count() == 0, 'Visible password input')
        require(not re.search(r'(?:csrf_token|session_id|authorization|password)\s*[:=]', text, re.I), 'Sensitive visible label')
        path = attempt / name
        page.screenshot(path=str(path), full_page=True)
        require(not any(s.encode() in path.read_bytes() for s in secrets if s), 'Screenshot credential scan failed')
        result['screenshots'].append({'path': str(path.relative_to(ROOT)), 'sha256': sha(path)})

    with sync_playwright() as playwright:
        browser = playwright.firefox.launch(headless=True)
        result['browser_version'] = browser.version
        errors = []

        def login(role):
            context = browser.new_context(viewport={'width': 1440, 'height': 1000})
            context.route('**/*', lambda route: route.continue_() if (
                urlsplit(route.request.url).hostname == '127.0.0.1' and urlsplit(route.request.url).port == args.port
            ) else route.abort())
            page = context.new_page()
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(base + '/web/login', wait_until='domcontentloaded')
            page.locator('input[name=login]').fill(access[role]['login'])
            page.locator('input[name=password]').fill(access[role]['password'])
            page.locator('button[type=submit]').click()
            page.wait_for_url(lambda url: '/web/login' not in url)
            page.goto(base + '/ydental/access', wait_until='domcontentloaded')
            selected = page.evaluate('''async (store) => {
                const token = document.querySelector('input[name=csrf_token]').value;
                const revision = document.querySelector('input[name=revision]').value;
                const data = new URLSearchParams({operation: 'switch', revision,
                    payload: JSON.stringify({store_id: store}), output: 'json', csrf_token: token});
                return (await fetch('/ydental/access/action', {method: 'POST', body: data})).json();
            }''', preview['stores'][0])
            require(type(selected.get('revision')) is int, 'Preview store selection failed')
            page.goto(base + '/ydental/access', wait_until='domcontentloaded')
            return context, page

        def rpc(page, model, method, values, revision=None):
            return page.evaluate('''async ({model, method, values, revision}) => {
                const response = await fetch('/web/dataset/call_kw', {
                    method: 'POST', headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({jsonrpc: '2.0', method: 'call', id: 1,
                        params: {model, method, args: values, kwargs: {context: {ydental_revision: revision}}}})
                });
                return await response.json();
            }''', {'model': model, 'method': method, 'values': values, 'revision': revision})

        def revision(page):
            # Store workspace emits the numeric page revision, never cookie/token data.
            return int(page.locator('input[name=revision]').first.input_value())

        def plan(page):
            page.goto(base + '/odoo/action-%s' % preview['plan_action_id'], wait_until='domcontentloaded')
            page.wait_for_function("document.querySelector('.o_ydental_space_canvas') || document.querySelector('.o_error_dialog')", timeout=30000)
            require(page.locator('.o_ydental_space_canvas').count() > 0, 'Owl floor plan did not render')
            page.wait_for_function("Array.from(document.querySelectorAll('.o_ydental_space_resources img')).every(image => image.complete)")

        def response_for(method):
            return lambda response: '/web/dataset/call_kw' in response.url and response.request.method == 'POST' and json.loads(
                response.request.post_data or '{}').get('params', {}).get('method') == method

        try:
            writer_context, writer = login('writer')
            writer_revision = revision(writer)
            floor_id = preview['floor_id']
            data = rpc(writer, 'ydental.space.floor', 'action_snapshot', [[floor_id]], writer_revision)['result']
            record('F1 six stable workstations and explicit runtime state', len(data['stations']) == 6 and
                   all(state['state'] == 'not_connected' for state in data['runtime']))
            first_id = preview['station_ids'][0]
            first = next(station for station in data['stations'] if station['id'] == first_id)
            plan(writer)
            record('Owl floor canvas renders', writer.locator('[data-kind=station]').count() == 6)
            snapshot(writer, writer_context, '01-writer-floor.png')

            # Two concurrent real HTTP transactions consume the same content version.
            concurrent = writer.evaluate('''async ({floor, version, station, revision}) => {
                const save = async (x) => (await fetch('/web/dataset/call_kw', {
                    method: 'POST', headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({jsonrpc: '2.0', method: 'call', id: x, params: {
                        model: 'ydental.space.floor', method: 'action_save_geometry',
                        args: [[floor], version, [{kind: 'station', id: station, values: {ydental_x: x}}]],
                        kwargs: {context: {ydental_revision: revision}}
                    }})})).json();
                return await Promise.all([save(78), save(86)]);
            }''', {'floor': floor_id, 'version': data['floor']['ydental_version'],
                   'station': first_id, 'revision': writer_revision})
            record('T06 two concurrent HTTP saves: one accepted, one version conflict',
                   sum('result' in entry for entry in concurrent) == 1 and
                   sum('version_conflict' in entry.get('error', {}).get('data', {}).get('message', '') for entry in concurrent) == 1)

            with writer.expect_response(response_for('action_snapshot')):
                writer.get_by_role('button', name='重新加载', exact=True).click()
            writer.wait_for_timeout(200)
            writer.locator('[data-kind=station]').first.click(position={'x': 10, 'y': 10})
            width = writer.get_by_role('spinbutton', name='宽度', exact=True)
            width.fill('105')
            width.press('Tab')
            with writer.expect_response(response_for('action_save_geometry')):
                writer.get_by_role('button', name='保存布局', exact=True).click()
            writer.wait_for_timeout(300)
            after = rpc(writer, 'ydental.space.floor', 'action_snapshot', [[floor_id]], writer_revision)['result']
            saved = next(station for station in after['stations'] if station['id'] == first_id)
            record('T01 T02 UI geometry save preserves workstation ID', saved['ydental_width'] == 105)
            snapshot(writer, writer_context, '02-saved-floor.png')

            # Configure through the native form; force_save transmits the version.
            writer.locator('[data-kind=station]').first.click(position={'x': 10, 'y': 10})
            writer.get_by_role('button', name='名称、区域和能力', exact=True).click()
            dialog = writer.locator('.o_dialog .o_form_view')
            dialog.wait_for()
            dialog.locator('[name=name] input').fill('S02 Renamed Stable Chair')
            writer.locator('.o_dialog').get_by_role('button', name='保存', exact=True).click()
            writer.locator('.o_dialog').wait_for(state='hidden')
            after = rpc(writer, 'ydental.space.floor', 'action_snapshot', [[floor_id]], writer_revision)['result']
            record('T02 native configuration rename keeps ID and references',
                   next(station for station in after['stations'] if station['id'] == first_id)['name'] == 'S02 Renamed Stable Chair')

            reader_context, reader = login('reader')
            reader_revision = revision(reader)
            plan(reader)
            record('T04 readonly plan has disabled save', reader.get_by_role('button', name='保存布局', exact=True).is_disabled())
            denied = rpc(reader, 'ydental.space.floor', 'action_save_geometry', [[floor_id], after['floor']['ydental_version'], []], reader_revision)
            record('T04 readonly direct layout RPC denied', 'access_denied' in denied.get('error', {}).get('data', {}).get('message', ''))
            snapshot(reader, reader_context, '03-readonly-floor.png')

            writer.goto(base + '/ydental/access', wait_until='domcontentloaded')
            # Use the current form CSRF token in-memory. Never export it.
            switched = writer.evaluate('''async ({store, revision}) => {
                const token = document.querySelector('input[name=csrf_token]').value;
                const data = new URLSearchParams({operation: 'switch', revision: String(revision),
                    payload: JSON.stringify({store_id: store}), output: 'json', csrf_token: token});
                return (await fetch('/ydental/access/action', {method:'POST', body:data})).json();
            }''', {'store': preview['stores'][1], 'revision': writer_revision})
            record('Store switch accepted', type(switched.get('revision')) is int)
            private_svg = writer.request.get(base + '/ydental/space/resource/%s.svg' % preview['private_resource_id'])
            record('T04 private SVG denied from other store', private_svg.status == 403)
            stale = rpc(writer, 'ydental.space.floor', 'action_save_geometry', [[floor_id], after['floor']['ydental_version'], []], writer_revision)
            record('Old store page cannot save layout', 'version_conflict' in stale.get('error', {}).get('data', {}).get('message', ''))
            record('No browser JavaScript errors', not errors)
            result['result'] = 'PASS'
        except Exception as error:
            result['result'] = 'FAIL'
            # Do not serialize request details, browser cookies or credential values.
            result['failure'] = type(error).__name__
            raise
        finally:
            (attempt / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
            browser.close()
    (evidence / 'browser-final.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'result': result['result'], 'checks': len(result['checks']), 'attempt': str(attempt.relative_to(ROOT))}))


if __name__ == '__main__':
    main()


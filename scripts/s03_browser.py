"""Real Firefox S03 UI evidence against only a recorded loopback preview.

No security overrides, profile/cookie export or credential output. Screenshots
contain only synthetic store/staff/source data. Failures remain in history.
"""
import argparse
from datetime import datetime, timedelta, timezone
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
    parser.add_argument('--port', type=int, default=18105)
    parser.add_argument('--evidence', default='s03')
    args = parser.parse_args()
    require(18000 <= args.port <= 18999, 'Isolated port refused')
    require(re.fullmatch(r'ydental_s03_test_[0-9]{14}_[a-f0-9]{8}', args.db), 'Database name refused')
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
            'ydental_supply', 'ydental_supply_test', 'scripts/s03.py', 'scripts/s03_probe.py', 'scripts/s03_browser.py'], text=True),
            'Commit implementation and browser code before verification')
    evidence = ROOT / 'docs/evidence' / args.evidence
    evidence.mkdir(parents=True, exist_ok=True)
    attempt = evidence / ('browser-attempts/' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f'))
    attempt.mkdir(parents=True)
    result = {'scope': 'S03 synthetic schedule and supply UI only', 'tested_commit': commit, 'database': args.db,
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
            page.locator('.o_main_navbar').wait_for()
            page.goto(base + '/ydental/access', wait_until='domcontentloaded')
            select_store(page, preview['stores'][0])
            return context, page

        def select_store(page, store_id):
            selected = page.evaluate('''async store_id => {
                const data = new URLSearchParams({operation:'switch', revision:document.querySelector('input[name=revision]').value,
                    csrf_token:document.querySelector('input[name=csrf_token]').value, output:'json', payload:JSON.stringify({store_id})});
                return (await fetch('/ydental/access/action',{method:'POST',body:data})).json();
            }''', store_id)
            require(type(selected.get('revision')) is int, 'Store selection failed')
            return selected['revision']

        def form(page, operation, index=0):
            detail = page.locator('details').filter(has=page.locator('form input[name=operation][value="' + operation + '"]')).nth(index)
            detail.locator('summary').first.click()
            return detail.locator('form').first

        def submit(page, target):
            target.locator('button').last.click()
            page.wait_for_url('**/ydental/supply')
            page.locator('#weekly-plan').wait_for()

        def times(target, day, hour=9):
            target.locator('input[name=start]').fill(day.strftime('%Y-%m-%dT') + '%02d:00' % hour)
            target.locator('input[name=end]').fill(day.strftime('%Y-%m-%dT') + '%02d:00' % (hour + 1))

        def run_checks():
            writer_context, page = login('writer')
            page.goto(base + '/ydental/supply', wait_until='domcontentloaded')
            record('weekly workstation view rendered', page.locator('#weekly-plan').count() == 1)
            page.goto(base + '/ydental/supply?group_by=person', wait_until='domcontentloaded')
            record('weekly person view rendered', page.locator('#weekly-plan table').count() >= 1)
            copy_form = page.locator('form').filter(has=page.locator('input[name=operation][value=copy]'))
            submit(page, copy_form)
            record('copy previous week survives reopen', 'Replacement' in page.locator('#weekly-plan').inner_text())
            today = datetime.now(timezone.utc)
            target = form(page, 'assign')
            target.locator('select[name=user_id]').select_option(str(access['reader']['id']))
            target.locator('select[name=station_id]').select_option(str(preview['station_ids'][1]))
            times(target, today + timedelta(days=10))
            target.locator('input[name=reason]').fill('Synthetic browser arrangement')
            submit(page, target)
            page.goto(base + '/ydental/supply?week_start=' + (today + timedelta(days=10)).strftime('%Y-%m-%d'), wait_until='domcontentloaded')
            record('mismatched draft remains visible', 'Synthetic Reader' in page.locator('#weekly-plan').inner_text())
            snapshot(page, writer_context, '01-weekly-plan.png')
            target = form(page, 'batch')
            target.locator('select[name=user_id]').select_option(str(preview['staff_id']))
            target.locator('select[name=area_id]').select_option(str(preview['area_id']))
            target.locator('input[name=dates]').fill(','.join((today + timedelta(days=d)).strftime('%Y-%m-%d') for d in (11, 12)))
            target.locator('input[name=start_time]').fill('09:00')
            target.locator('input[name=end_time]').fill('10:00')
            target.locator('input[name=reason]').fill('Synthetic browser batch')
            submit(page, target)
            record('batch template submitted through UI', page.locator('#weekly-plan').count() == 1)
            target = form(page, 'policy')
            target.locator('input[name=name]').fill('Browser explicit demo 1:2')
            target.locator('input[name=reason]').fill('Synthetic browser policy preview')
            target.locator('button').click()
            page.wait_for_url('**/ydental/supply/action')
            policy_result = json.loads(page.locator('body').inner_text())
            record('integer preview Q1 Q2 Q3 Q6', [(v['reservation'],v['walkin']) for v in policy_result['preview']] == [(0,1),(0,2),(1,2),(2,4)])
            page.goto(base + '/ydental/supply', wait_until='domcontentloaded')
            target = form(page, 'slot')
            target.locator('select[name=station_id]').select_option(str(preview['station_ids'][1]))
            target.locator('select[name=capability_ids]').select_option([str(v) for v in preview['capability_ids']])
            times(target, today + timedelta(days=20))
            target.locator('input[name=total]').fill('6')
            target.locator('input[name=reason]').fill('Synthetic browser temporary capacity')
            submit(page, target)
            target = form(page, 'publish')
            target.locator('select[name=user_ids]').select_option(str(preview['staff_id']))
            target.locator('input[name=reason]').fill('Synthetic capability coverage verification')
            submit(page, target)
            record('verified slot published with shared total six', page.locator('[data-slot-state=published]').count() >= 1)
            target = form(page, 'resize')
            slot_id = int(target.locator('input[name=id]').input_value())
            target.locator('input[name=total]').fill('9')
            target.locator('input[name=reason]').fill('Synthetic temporary extra capacity')
            submit(page, target)
            record('extra capacity visible', '9' in page.locator('#capacity-slots tbody').first.inner_text())
            snapshot(page, writer_context, '02-shared-capacity.png')
            open_form = page.locator('#business-day form').filter(has=page.locator('input[name=state][value=open]'))
            open_form.locator('select[name=area_id]').select_option(str(preview['area_id']))
            open_form.locator('input[name=reason]').fill('Synthetic browser opening')
            submit(page, open_form)
            state_form = page.locator('#business-day form').filter(has=page.locator('select[name=state]')).first
            state_form.locator('select[name=state]').select_option('draining')
            state_form.locator('input[name=reason]').fill('Synthetic stop reporting')
            submit(page, state_form)
            record('ordinary reporting stopped', page.locator('[data-business-state=draining]').count() == 1)
            state_form = page.locator('#business-day form').filter(has=page.locator('select[name=state]')).first
            state_form.locator('select[name=state]').select_option('open')
            state_form.locator('input[name=reason]').fill('Synthetic reopen')
            submit(page, state_form)
            record('reopening visible without new slot', page.locator('[data-business-state=open]').count() == 1)
            snapshot(page, writer_context, '03-business-day.png')
            reader_context, reader_page = login('reader')
            reader_page.goto(base + '/ydental/supply', wait_until='domcontentloaded')
            record('readonly has no capacity mutation forms', reader_page.locator('input[name=operation][value=resize]').count() == 0)
            snapshot(reader_page, reader_context, '04-readonly-capacity.png')
            staff_context, staff_page = login('staff')
            staff_page.goto(base + '/ydental/supply/today', wait_until='domcontentloaded')
            record('my today shows own station arrangement', staff_page.locator('article').count() == 1)
            target = form(staff_page, 'feedback')
            target.locator('input[name=reason]').fill('Synthetic browser arrangement error')
            target.locator('button').click()
            staff_page.wait_for_url('**/ydental/supply/today')
            record('arrangement error accepted through UI', staff_page.locator('article').count() == 1)
            snapshot(staff_page, staff_context, '05-my-today-feedback.png')
            staff_page.locator('form').filter(has=staff_page.locator('input[name=operation][value=suggest]')).locator('button').click()
            staff_page.wait_for_url('**/ydental/supply/action')
            record('suggested workbench explicitly awaits integration', 'S06' in staff_page.locator('body').inner_text())
            page.goto(base + '/ydental/supply', wait_until='domcontentloaded')
            record('feedback visible to scheduling writer', 'Synthetic browser arrangement error' in page.locator('#handling').inner_text())
            rework = preview['rework']
            partial_context, partial_page = login('partial_staff')
            partial_page.goto(base + '/ydental/supply/today', wait_until='domcontentloaded')
            target = partial_page.locator('form').filter(has=partial_page.locator('input[name=operation][value=suggest]')).filter(
                has=partial_page.locator('input[name=id][value="%s"]' % rework['area_assignment_id']))
            target.locator('button').click()
            partial_page.wait_for_url('**/ydental/supply/action')
            suggestions = partial_page.locator('main ul').inner_text()
            record('area suggestion requires complete active capabilities', 'S03 Chair 1' in suggestions and 'S03 Chair 2' not in suggestions)
            snapshot(partial_page, partial_context, '06-partial-area-suggestion.png')
            partial_page.goto(base + '/ydental/supply/today', wait_until='domcontentloaded')
            target = partial_page.locator('form').filter(has=partial_page.locator('input[name=operation][value=suggest]')).filter(
                has=partial_page.locator('input[name=id][value="%s"]' % rework['direct_assignment_id']))
            target.locator('button').click()
            partial_page.wait_for_url('**/ydental/supply/action')
            record('direct assignment cannot bypass qualification filter', partial_page.locator('main ul li').count() == 0)
            page.goto(base + '/ydental/supply', wait_until='domcontentloaded')
            target = page.locator('#handling form').filter(has=page.locator('input[name=entity][value=disposition]')).filter(
                has=page.locator('input[name=id][value="%s"]' % rework['handling_disposition_id']))
            record('assignment handling visible without a capacity slot', target.count() == 1)
            snapshot(page, writer_context, '07-assignment-handling.png')
            target.locator('input[name=reason]').fill('Synthetic browser assignment handling reviewed')
            submit(page, target)
            record('assignment handling resolves with history retained', 'Synthetic browser assignment handling reviewed' in page.locator('#handling').inner_text())
            page.goto(base + '/ydental/supply?week_start=2026-11-02', wait_until='domcontentloaded')
            copy_form = page.locator('form').filter(has=page.locator('input[name=operation][value=copy]'))
            submit(page, copy_form)
            page.goto(base + '/ydental/supply?week_start=2026-11-02', wait_until='domcontentloaded')
            weekly = page.locator('#weekly-plan').inner_text()
            record('fall DST week copy includes local Monday and Sunday boundaries',
                '2026-11-02 00:30' in weekly and '2026-11-08 23:30' in weekly and page.locator('#weekly-plan tbody tr').count() == 2)
            snapshot(page, writer_context, '08-dst-week-copy.png')
            for value, end, label, text in [
                ('2026-03-08T02:30', '2026-03-08T03:30', 'nonexistent wall time rejected through form', '不存在'),
                ('2026-11-01T01:30', '2026-11-01T02:30', 'ambiguous wall time rejected through form', '两个时刻'),
            ]:
                page.goto(base + '/ydental/supply', wait_until='domcontentloaded')
                target = form(page, 'assign')
                target.locator('select[name=user_id]').select_option(str(access['writer']['id']))
                target.locator('select[name=area_id]').select_option(str(preview['area_id']))
                target.locator('input[name=start]').fill(value)
                target.locator('input[name=end]').fill(end)
                target.locator('input[name=reason]').fill('Synthetic DST rejection')
                with page.expect_response(lambda response: response.url == base + '/ydental/supply/action') as rejected:
                    target.locator('button').last.click()
                page.wait_for_url('**/ydental/supply/action')
                record(label, rejected.value.status == 409 and text in page.locator('body').inner_text())
            snapshot(page, writer_context, '09-dst-input-rejected.png')
            page.goto(base + '/ydental/supply', wait_until='domcontentloaded')
            target = form(page, 'assign')
            target.locator('select[name=user_id]').select_option(str(access['writer']['id']))
            target.locator('select[name=area_id]').select_option(str(preview['area_id']))
            target.locator('input[name=start]').fill('2026-11-10T09:30')
            target.locator('input[name=end]').fill('2026-11-10T10:30')
            target.locator('input[name=reason]').fill('Synthetic normal local time round trip')
            submit(page, target)
            page.goto(base + '/ydental/supply?week_start=2026-11-09', wait_until='domcontentloaded')
            record('normal wall time round trip preserves local hour', '2026-11-10 09:30' in page.locator('#weekly-plan').inner_text())
            old_revision = int(page.locator('input[name=revision]').first.input_value())
            page.goto(base + '/ydental/access', wait_until='domcontentloaded')
            select_store(page, preview['stores'][1])
            denied = page.evaluate('''async ({revision,id}) => {
                const data = new URLSearchParams({operation:'resize', revision, key:'browser-old-page', output:'json',
                    csrf_token:document.querySelector('input[name=csrf_token]').value,
                    payload:JSON.stringify({id,version:1,total:100,reason:'Synthetic stale page'})});
                return (await fetch('/ydental/supply/action',{method:'POST',body:data})).status;
            }''', {'revision':old_revision,'id':slot_id})
            record('old page rejected after store switch', denied == 409)
            record('Firefox has no unhandled page error', not errors)
            for context in (writer_context, reader_context, staff_context, partial_context):
                context.close()

        try:
            run_checks()
            result['result'] = 'PASS'
        except Exception as error:
            result['result'] = 'FAIL'
            result['error_type'] = type(error).__name__
            raise
        finally:
            browser.close()
            result['finished_utc'] = datetime.now(timezone.utc).isoformat()
            (attempt / 'result.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
            (evidence / 'browser-final.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'result': result['result'], 'checks': len(result['checks']), 'browser_version':result['browser_version']}))


if __name__ == '__main__':
    main()

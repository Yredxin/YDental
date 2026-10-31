"""Firefox clicks real S06 and S09 actions against one isolated synthetic database."""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DEPS = ROOT / '.local/s00-b-deps'
sys.path.insert(0, str(DEPS / 'verify-lib'))
os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH', str(DEPS / 'browsers'))
os.environ.setdefault('LD_LIBRARY_PATH', str(DEPS / 'browser-libs/usr/lib/x86_64-linux-gnu'))
os.environ.setdefault('FONTCONFIG_FILE', str(DEPS / 'browser-fonts.conf'))
from playwright.sync_api import sync_playwright


def require(ok, name):
    if not ok:
        raise AssertionError(name)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', required=True)
    parser.add_argument('--port', required=True, type=int)
    args = parser.parse_args()
    require(re.fullmatch(r'ydental_s09_test_[0-9]{14}_[a-f0-9]{8}', args.db), 'database name')
    run = ROOT / '.local' / args.db
    metadata = json.loads((run / 'database.json').read_text())
    require(metadata['database'] == args.db and metadata['port'] == args.port and
            metadata['cluster'] == '7694897083368259627' and
            metadata['config_sha256'] == digest(run / 'odoo.conf'), 'database guard')
    pid = int((run / 'serve.pid').read_text())
    require(str(run / 'odoo.conf').encode() in Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0'), 'serve PID guard')
    fixtures = sorted(run.glob('ui-seed-*.json'))
    require(bool(fixtures), 'UI seed required')
    fixture_path = fixtures[-1]
    require(stat.S_IMODE(fixture_path.stat().st_mode) == 0o600, 'fixture permission')
    fixture = json.loads(fixture_path.read_text())
    base = f'http://127.0.0.1:{args.port}'
    evidence = ROOT / 'docs/evidence/s09-rework/browser-actions' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    evidence.mkdir(parents=True)
    checks, shots, errors = [], [], []

    def check(name, value):
        require(value, name)
        checks.append(name)

    def screenshot(name, page):
        path = evidence / (name + '.png')
        page.screenshot(path=str(path), full_page=True)
        shots.append({'file': str(path.relative_to(ROOT)), 'sha256': digest(path)})

    with sync_playwright() as playwright:
        browser = playwright.firefox.launch(headless=True)

        def login(role):
            context = browser.new_context(viewport={'width': 1440, 'height': 1000}, locale='zh-CN')
            context.route('**/*', lambda route: route.continue_() if (
                urlsplit(route.request.url).hostname == '127.0.0.1' and
                urlsplit(route.request.url).port == args.port) else route.abort())
            page = context.new_page()
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(base + '/web/login?redirect=/ydental/access', wait_until='domcontentloaded')
            page.locator('[name=login]').fill(fixture[role]['login'])
            page.locator('[name=password]').fill(fixture[role]['password'])
            page.locator('button[type=submit]').click()
            page.wait_for_url('**/ydental/access')
            response = page.evaluate("""async store => {
                const body = new URLSearchParams({operation:'switch',
                    revision:document.querySelector('[name=revision]').value,
                    csrf_token:document.querySelector('[name=csrf_token]').value,
                    output:'json',payload:JSON.stringify({store_id:store})});
                const response=await fetch('/ydental/access/action',{method:'POST',body});
                return {status:response.status,data:await response.json()};
            }""", fixture['store_id'])
            check(role + ' store switch', response['status'] == 200)
            return context, page

        def submit(page, form, button='button[type=submit]'):
            page.once('dialog', lambda dialog: dialog.accept())
            if form.get_attribute('data-operation'):
                with page.expect_response('**/ydental/exam/action') as response:
                    form.locator(button).click()
                reply = response.value
                if reply.status != 200:
                    params = dict(item.split('=', 1) for item in (reply.request.post_data or '').split('&') if '=' in item)
                    from urllib.parse import unquote_plus
                    sent = json.loads(unquote_plus(params.get('payload', '{}')))
                    print('REJECTED_ACTION_KEYS', sorted(sent),
                          {key: sent[key] for key in sent if key not in ('lease_token', 'findings', 'conclusion')},
                          flush=True)
                require(reply.status == 200, 'exam action rejected: ' + json.dumps(reply.json(), ensure_ascii=False))
                page.wait_for_load_state('domcontentloaded')
                page.wait_for_timeout(200)
                return
            with page.expect_navigation(wait_until='domcontentloaded'):
                form.locator(button).click()

        try:
            front_context, front = login('frontdesk')
            front.goto(base + '/ydental/queue', wait_until='domcontentloaded')
            pending = front.locator(f'[data-pending-task="{fixture["panorama_task"]}"]')
            check('panorama S06 pending task visible', pending.count() == 1)
            submit(front, pending.locator('form[data-queue-form="report"]'))
            check('panorama report clicked', front.locator(f'tr[data-task="{fixture["panorama_task"]}"]').count() == 1)
            screenshot('01-frontdesk-report', front)

            exam_context, examiner = login('examiner')
            examiner.goto(base + '/ydental/queue', wait_until='domcontentloaded')
            station = examiner.locator(f'tr[data-station="{fixture["panorama_station"]}"]')
            check('panorama station enter button', station.locator('[data-operation="enter"]').count() == 1)
            with examiner.expect_navigation(wait_until='domcontentloaded'):
                station.locator('[data-operation="enter"]').click()
            check('real S06 station held', examiner.locator('#holding-workstation').count() == 1)
            with examiner.expect_navigation(wait_until='domcontentloaded'):
                examiner.locator('[data-operation="call"]').click()
            entry = examiner.locator(f'tr[data-task="{fixture["panorama_task"]}"]')
            check('panorama call clicked', entry.locator('[data-operation="start"]').count() == 1)
            with examiner.expect_navigation(wait_until='domcontentloaded'):
                entry.locator('[data-operation="start"]').click()
            check('real panorama service started', examiner.locator('#patient-return-actions [data-execution]').count() == 1)
            screenshot('02-queue-call-start', examiner)

            examiner.goto(base + '/ydental/exam', wait_until='domcontentloaded')
            panel = examiner.locator(f'section[data-line="{fixture["panorama_line"]}"]')
            draft = panel.locator('form[data-operation="draft"]')
            check('actual panorama draft form', draft.count() == 1)
            print('EXAM_FORM_DIAGNOSTIC', json.dumps(examiner.evaluate("""() => ({
                root: document.querySelector('.o_ydental_exam')?.dataset,
                allowed: document.querySelector('form[data-operation="draft"]')?.dataset.allowed,
                holderKeys: Object.keys(JSON.parse(sessionStorage.getItem('ydental_queue_holder') || '{}')),
                pageErrors: []
            })"""), ensure_ascii=False), flush=True)
            check('actual draft button enabled', draft.get_attribute('data-allowed') == 'true')
            draft.locator('[name=findings]').fill('Firefox实际阅片所见：结构化全景长度')
            draft.locator('[name=measurement_status]').select_option('known')
            draft.locator('[name=measurement_value]').fill('12.5')
            submit(examiner, draft)
            panel = examiner.locator(f'section[data-line="{fixture["panorama_line"]}"]')
            check('known measurement restored in real form', panel.locator('form[data-operation="draft"] [name=measurement_value]').input_value() == '12.5')
            screenshot('03-measurement-saved', examiner)

            attachment = panel.locator('form[data-operation="attach"]')
            check('attachment button present', attachment.count() == 1)
            png = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/lXcAAAAASUVORK5CYII=')
            attachment.locator('[name=evidence]').set_input_files({'name': 'firefox-synthetic.png',
                'mimeType': 'image/png', 'buffer': png})
            submit(examiner, attachment)
            panel = examiner.locator(f'section[data-line="{fixture["panorama_line"]}"]')
            check('attachment download link visible', panel.locator('a[href*="/ydental/exam/attachment/"]').count() == 1)
            with examiner.expect_download() as download:
                panel.locator('a[href*="/ydental/exam/attachment/"]').click()
            path = evidence / 'firefox-synthetic.png'
            download.value.save_as(path)
            check('attachment downloaded exact bytes', path.read_bytes() == png)
            screenshot('04-attachment', examiner)

            perform = panel.locator('form[data-operation="perform"]')
            perform.locator('[name=reason]').fill('Firefox真实全景检查实施')
            if 'material_lot' in fixture:
                check('real material batch offered in examination form', perform.locator(
                    f'[name=lot_id] option[value="{fixture["material_lot"]}"]').count() >= 1)
                perform.locator('[data-material-row]').first.locator('[name=lot_id]').select_option(str(fixture['material_lot']))
                perform.locator('[data-material-row]').first.locator('[name=quantity]').fill('1')
            submit(examiner, perform)
            panel = examiner.locator(f'section[data-line="{fixture["panorama_line"]}"]')
            check('actual event fee source visible', '价格快照' in panel.inner_text() and 'confirmed' in panel.inner_text())
            confirm = panel.locator('form[data-operation="confirm"]')
            confirm.locator('[name=reason]').fill('Firefox人工确认全景结果')
            submit(examiner, confirm)
            panel = examiner.locator(f'section[data-line="{fixture["panorama_line"]}"]')
            check('confirmed result form visible', panel.locator('form[data-operation="correct"]').count() == 1)
            correct = panel.locator('form[data-operation="correct"]')
            correct.locator('[name=reason]').fill('Firefox追加测量更正')
            correct.locator('[name=findings]').fill('Firefox更正所见：真实人工核对')
            correct.locator('[name=measurement_status]').select_option('known')
            correct.locator('[name=measurement_value]').fill('13')
            submit(examiner, correct)
            details = exam_context.request.get(base + f'/ydental/exam/result/{fixture["panorama_line"]}')
            check('correction created distinct version and measurement', details.status == 200 and
                  details.json()['version'] >= 3 and details.json()['measurements']['length_mm']['value'] == 13)
            panel = examiner.locator(f'section[data-line="{fixture["panorama_line"]}"]')
            finish = panel.locator('form[data-operation="finish"]')
            finish.locator('[name=reason]').fill('Firefox全景检查段完成，CBCT仍未实施')
            submit(examiner, finish)
            print('POST_FINISH_DIAGNOSTIC', json.dumps(examiner.evaluate("""() => ({
                execution:document.querySelector('.o_ydental_exam')?.dataset.execution,
                message:document.querySelector('#exam-message')?.innerText,
                reconcileHidden:document.querySelector('#exam-reconcile')?.hidden,
                holder:!!sessionStorage.getItem('ydental_queue_holder')
            })"""), ensure_ascii=False), flush=True)
            examiner.wait_for_function("Number(document.querySelector('.o_ydental_exam')?.dataset.execution || 0) === 0", timeout=10000)
            check('exam station released', int(examiner.locator('.o_ydental_exam').get_attribute('data-execution') or 0) == 0)
            screenshot('05-finished-partial', examiner)

            front.goto(base + '/ydental/queue', wait_until='domcontentloaded')
            continuation = front.locator(f'[data-pending-task="{fixture["continuation_task"]}"]')
            check('one S06 continuation visible', continuation.count() == 1)
            submit(front, continuation.locator('form[data-queue-form="report"]'))
            check('continuation reported by real button', front.locator(f'tr[data-task="{fixture["continuation_task"]}"]').count() == 1)
            screenshot('06-partial-return-report', front)

            doctor_context, doctor = login('doctor')
            doctor.goto(base + f'/ydental/exam?area_id={fixture["care_area"]}#area-exam-handoff',
                        wait_until='domcontentloaded')
            check('area shared task uses S06 continuation', str(fixture['continuation_task']) in
                  doctor.locator('#area-exam-handoff').inner_text())
            check('partial panorama and unfinished CBCT both visible',
                  doctor.locator(f'section[data-line="{fixture["panorama_line"]}"]').count() == 1 and
                  doctor.locator(f'section[data-line="{fixture["cbct_line"]}"]').count() == 1)
            screenshot('07-area-shared-partial-result', doctor)
            if 'care_station' in fixture:
                doctor.goto(base + '/ydental/queue', wait_until='domcontentloaded')
                station = doctor.locator(f'tr[data-station="{fixture["care_station"]}"]')
                check('continuation doctor enters existing medical station',
                      station.locator('[data-operation="enter"]').count() == 1)
                with doctor.expect_navigation(wait_until='domcontentloaded'):
                    station.locator('[data-operation="enter"]').click()
                with doctor.expect_navigation(wait_until='domcontentloaded'):
                    doctor.locator('[data-operation="call"]').click()
                continuation_entry = doctor.locator(f'tr[data-task="{fixture["continuation_task"]}"]')
                check('one continuation called to new doctor',
                      continuation_entry.locator('[data-operation="start"]').count() == 1)
                with doctor.expect_navigation(wait_until='domcontentloaded'):
                    continuation_entry.locator('[data-operation="start"]').click()
                doctor.goto(base + '/ydental/exam#current-exam-handoff', wait_until='domcontentloaded')
                check('new doctor sees current confirmed result',
                      doctor.locator('#current-exam-handoff').locator(
                          f'a[href="/ydental/exam/result-view/{fixture["panorama_line"]}"]').count() == 1)
                screenshot('08-new-doctor-current-result', doctor)

                doctor.goto(base + '/ydental/clinical', wait_until='domcontentloaded')
                with doctor.expect_response('**/ydental/clinical/action') as opened:
                    doctor.locator('#open-document').click()
                check('new doctor opens own independent clinical document', opened.value.status == 200)
                with doctor.expect_response('**/ydental/clinical/action') as saved:
                    doctor.locator('#save-document').click()
                check('new doctor saves the current medical source', saved.value.status == 200)
                doctor.goto(base + '/ydental/exam', wait_until='domcontentloaded')
                cbct = doctor.locator(f'section[data-line="{fixture["cbct_line"]}"]')
                revalidate = cbct.locator('form[data-operation="revalidate"]')
                check('prior-day unfinished CBCT has doctor revalidation button', revalidate.count() == 1)
                revalidate.locator('[name=reason]').fill('Firefox医生确认本日仍需CBCT')
                submit(doctor, revalidate)
                doctor.goto(base + '/ydental/exam', wait_until='domcontentloaded')
                check('doctor revalidation stored; no repeat button', doctor.locator(
                    f'section[data-line="{fixture["cbct_line"]}"] form[data-operation="revalidate"]').count() == 0)
                screenshot('09-prior-day-doctor-revalidated', doctor)

                doctor.goto(base + '/ydental/clinical', wait_until='domcontentloaded')
                with doctor.expect_response('**/ydental/clinical/action') as reacquired:
                    doctor.locator('#open-document').click()
                check('current doctor reopens saved clinical document', reacquired.value.status == 200)
                with doctor.expect_navigation(wait_until='domcontentloaded'):
                    with doctor.expect_response('**/ydental/clinical/action') as handed:
                        doctor.locator('#handover-document').click()
                check('current doctor hands over saved continuation', handed.value.status == 200)
                doctor.goto(base + '/ydental/queue', wait_until='domcontentloaded')
                with doctor.expect_navigation(wait_until='domcontentloaded'):
                    doctor.locator('[data-operation="exit"]').click()
                check('doctor station released after handover', doctor.locator('#holding-workstation').count() == 0)
                front.goto(base + '/ydental/queue', wait_until='domcontentloaded')
                cbct_pending = front.locator(f'[data-pending-task="{fixture["cbct_task"]}"]')
                check('revalidated CBCT remains one original S06 task', cbct_pending.count() == 1)
                submit(front, cbct_pending.locator('form[data-queue-form="report"]'))
                screenshot('10-cbct-next-day-report', front)

                examiner.goto(base + '/ydental/queue', wait_until='domcontentloaded')
                cbct_station = examiner.locator(f'tr[data-station="{fixture["cbct_station"]}"]')
                with examiner.expect_navigation(wait_until='domcontentloaded'):
                    cbct_station.locator('[data-operation="enter"]').click()
                with examiner.expect_navigation(wait_until='domcontentloaded'):
                    examiner.locator('[data-operation="call"]').click()
                cbct_entry = examiner.locator(f'tr[data-task="{fixture["cbct_task"]}"]')
                check('CBCT called separately from panorama', cbct_entry.locator('[data-operation="start"]').count() == 1)
                with examiner.expect_navigation(wait_until='domcontentloaded'):
                    cbct_entry.locator('[data-operation="start"]').click()
                examiner.goto(base + '/ydental/exam', wait_until='domcontentloaded')
                cbct = examiner.locator(f'section[data-line="{fixture["cbct_line"]}"]')
                draft = cbct.locator('form[data-operation="draft"]')
                draft.locator('[name=findings]').fill('Firefox跨日CBCT所见')
                draft.locator('[name=measurement_status]').select_option('unknown')
                submit(examiner, draft)
                cbct = examiner.locator(f'section[data-line="{fixture["cbct_line"]}"]')
                perform = cbct.locator('form[data-operation="perform"]')
                perform.locator('[name=reason]').fill('Firefox CBCT真实实施')
                submit(examiner, perform)
                cbct = examiner.locator(f'section[data-line="{fixture["cbct_line"]}"]')
                confirm = cbct.locator('form[data-operation="confirm"]')
                confirm.locator('[name=reason]').fill('Firefox人工确认跨日CBCT')
                submit(examiner, confirm)
                cbct = examiner.locator(f'section[data-line="{fixture["cbct_line"]}"]')
                finish = cbct.locator('form[data-operation="finish"]')
                finish.locator('[name=reason]').fill('Firefox跨日CBCT检查结束')
                submit(examiner, finish)
                examiner.wait_for_function("Number(document.querySelector('.o_ydental_exam')?.dataset.execution || 0) === 0")
                check('CBCT original line completed once', exam_context.request.get(
                    base + f'/ydental/exam/result/{fixture["cbct_line"]}').json()['result_state'] == 'confirmed')
                screenshot('11-cbct-completed', examiner)

                doctor.goto(base + f'/ydental/exam?area_id={fixture["care_area"]}#area-exam-handoff',
                            wait_until='domcontentloaded')
                check('area keeps both confirmed results for one S06 continuation', all(doctor.locator(
                    f'#area-exam-handoff a[href="/ydental/exam/result-view/{fixture[key]}"]').count() >= 1
                    for key in ('panorama_line', 'cbct_line')))
                screenshot('12-area-both-results', doctor)

            reader_context, reader = login('reader')
            reader.goto(base + '/ydental/exam', wait_until='domcontentloaded')
            check('read only user has no examination write button',
                  reader.locator('form[data-operation="draft"] button:enabled').count() == 0)
            denied = reader.evaluate("""async line => {
                const root=document.querySelector('.o_ydental_exam');
                const response=await fetch('/ydental/exam/action',{method:'POST',
                    body:new URLSearchParams({operation:'reconcile',revision:root.dataset.revision,
                        connection:'firefox-read-only-negative',key:crypto.randomUUID(),
                        csrf_token:odoo.csrf_token,payload:JSON.stringify({line_id:line,reason:'Denied'})})});
                return response.status;
            }""", fixture['panorama_line'])
            check('read only Firefox RPC write denied', denied == 403)
            screenshot('13-reader-denied', reader)
            none_context, none = login('none')
            check('ungranted Firefox workbench denied', none_context.request.get(base + '/ydental/exam').status == 403)

            check('Firefox page errors zero', not errors)
        finally:
            browser.close()
    outcome = {'database': args.db, 'checks': checks, 'screenshots': shots,
               'pageerrors': errors, 'fixture_line': fixture['panorama_line']}
    (evidence / 'result.json').write_text(json.dumps(outcome, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(outcome, ensure_ascii=False))


if __name__ == '__main__':
    main()

"""Firefox response barriers for the S08-A terminal submission regression.

Called only by s08a_browser after its endpoint/config/PID/egress guards and real
D1/D2 workflow. Routes hold real server responses; no clinical product adapters.
"""
import json
import time
from urllib.parse import parse_qs, urlencode


def run_terminal_races(*, page, context, front, base, d1, d2, check, screenshot,
                       open_editor, version, click_wait, inspect_action, result):
    records = []
    result['terminal_response_barriers'] = records

    def document_id():
        return int(page.evaluate('new URL(location.href).searchParams.get("document_id")'))

    def read(doc_id):
        # The product exposes authorized read through GET workbench, not a
        # public action named "read". Parse the real persisted server rendering.
        response = page.evaluate("""async doc => {
            const response=await fetch('/ydental/clinical?document_id='+doc);
            const fragment=new DOMParser().parseFromString(await response.text(),'text/html');
            const root=fragment.querySelector('.o_ydental_clinical');
            if (!response.ok || !root) return {status:response.status};
            return {status:response.status,data:{document_id:Number(root.dataset.document),
                version:Number(root.querySelector('#server-version').textContent),state:root.dataset.state,
                content:Object.fromEntries([...root.querySelectorAll('textarea[name]')].map(f=>[f.name,f.value]).concat([['teeth',
                    [...root.querySelectorAll('#tooth-summary [data-row]')].map(row=>({tooth:Number(row.dataset.row),state:row.dataset.state,surfaces:row.dataset.surfaces.split(',').filter(Boolean)}))]]))}};
        }""",doc_id)
        check('authorized real server read for document %s' % doc_id, response['status'] == 200 and response['data']['document_id']==doc_id)
        return response['data']

    def text():
        return page.locator('[name=chief_complaint]').input_value()

    def barrier(operation, *, send=True, stale=False):
        pending = []
        def handler(route):
            form = parse_qs(route.request.post_data or '')
            if form.get('operation', [''])[0] != operation:
                route.continue_()
                return
            payload = json.loads(form['payload'][0])
            if stale:
                payload['expected_version'] -= 1
                form['payload'] = [json.dumps(payload)]
            response = route.fetch(post_data=urlencode({k:v[0] for k,v in form.items()})) if send else None
            pending.append({'route':route, 'response':response, 'content':payload.get('content'),
                            'expected_version':payload.get('expected_version'), 'started':time.monotonic()})
        page.route('**/ydental/clinical/action', handler)
        return pending, handler

    def wait_pending(pending):
        for _ in range(150):
            page.wait_for_timeout(40)
            if pending:
                return pending[0]
        raise RuntimeError('Terminal response barrier was not reached')

    def native_attempts(operation):
        before = page.locator('textarea[name]').evaluate_all('(xs)=>xs.map(x=>x.value)')
        selected = page.locator('#selected-tooth').inner_text()
        summary = page.locator('#tooth-summary').inner_text()
        check(operation+' freezes all seven clinical textareas', page.locator('textarea[name]:disabled').count() == 7)
        check(operation+' freezes 52 teeth, state, surfaces and no-tooth',
              page.locator('[data-tooth]:disabled').count() == 52 and
              page.locator('#tooth-state').is_disabled() and
              page.locator('#surfaces input:enabled').count() == 0 and page.locator('#no-tooth').is_disabled())
        for field in page.locator('textarea[name]').all():
            field.scroll_into_view_if_needed()
            box = field.bounding_box()
            page.mouse.click(box['x']+10, box['y']+10)
            page.keyboard.insert_text('终态请求中禁止新增合成内容')
        for selector in ('[data-tooth="37"]', '#no-tooth', '#tooth-state', '#surfaces input[value=M]'):
            target = page.locator(selector)
            target.scroll_into_view_if_needed();box = target.bounding_box()
            page.mouse.click(box['x']+box['width']/2, box['y']+box['height']/2)
            if selector == '#tooth-state':page.keyboard.press('ArrowDown')
        check(operation+' physical text and FDI attempts cannot alter submission',
              before == page.locator('textarea[name]').evaluate_all('(xs)=>xs.map(x=>x.value)') and
              selected == page.locator('#selected-tooth').inner_text() and summary == page.locator('#tooth-summary').inner_text())

    def finish(pending, handler, operation, *, navigate=False, abort=False):
        row = pending[0]
        elapsed = time.monotonic()-row['started']
        if navigate:
            with page.expect_navigation(wait_until='domcontentloaded'):
                row['route'].fulfill(response=row['response'])
        elif abort:row['route'].abort('failed')
        else:row['route'].fulfill(response=row['response'])
        page.unroute('**/ydental/clinical/action',handler)
        records.append({'operation':operation, 'response_status':row['response'].status if row['response'] else None,
                        'response_held_seconds':round(elapsed,3), 'real_request_sent':row['response'] is not None,
                        'response_dropped':abort, 'navigated_on_success':navigate})

    def reconcile(expected, *, handover=False):
        page.wait_for_function('!document.querySelector("#reconcile-document").hidden')
        check('reconciliation keeps local text and never claims saved', text()==expected and
              '未同步' in page.locator('#clinical-result').inner_text() and
              '已保存' not in page.locator('#clinical-result').inner_text())
        check('reconciliation freezes repeat submit and permits text comparison',
              page.locator('textarea[name]:read-only').count()==7 and page.locator('#open-document').is_disabled() and
              page.locator('#correct-document').is_disabled() and page.locator('#handover-document').is_disabled())
        if handover:
            check('committed handover is explicitly irreversible here', '交还已提交' in page.locator('#clinical-result').inner_text() and '不能' in page.locator('#clinical-result').inner_text())
        with page.expect_popup() as popup:
            page.locator('#reconcile-document').click()
        server = popup.value;server.wait_for_load_state('domcontentloaded')
        check('new tab shows real server version without leaving unsent local page', server.locator('#server-version').count()==1 and text()==expected)
        if handover:
            check('recovery exposes actual handed-over reception',server.locator('#execution-state').get_attribute('data-state')=='handover')
        server.close()

    def explicit_reload():
        # The operator has compared the new tab. Explicitly discard this test-only
        # local copy, then use the original session/connection and lawful editor.
        page.reload();open_editor(page)

    # Ordinary save remains editable and catches up both text and structured FDI.
    open_editor(page)
    page.locator('[name=chief_complaint]').fill('合成普通自动保存A')
    pending,handler=barrier('save')
    row=wait_pending(pending)
    check('ordinary in-flight autosave permits clinical input',not page.locator('[name=chief_complaint]').is_disabled())
    page.locator('[name=chief_complaint]').fill('合成普通自动保存B最新文字')
    page.locator('[name=history]').fill('合成普通请求期间最新病史')
    page.locator('[data-tooth="36"]').click();page.locator('#tooth-state').select_option('present');page.locator('#surfaces input[value=O]').check()
    page.wait_for_timeout(1100)
    finish(pending,handler,'save-catch-up')
    version(page,row['expected_version']+2)
    latest=read(d2)
    check('ordinary autosave catches up latest text and tooth on real server',latest['content']['chief_complaint']=='合成普通自动保存B最新文字' and any(r['tooth']==36 and r['surfaces']==['O'] for r in latest['content']['teeth']))
    screenshot(page,context,'12-ordinary-inflight-autosave-catchup.png')

    # Normal confirm and correct: all content is frozen throughout the response.
    for operation in ('confirm','correct'):
        if operation=='correct':
            open_editor(page);page.locator('[name=chief_complaint]').fill('合成延迟文字更正范围');page.locator('#correction-reason').fill('核对延迟更正提交范围')
        pending,handler=barrier(operation)
        page.locator('#'+operation+'-document').click();row=wait_pending(pending)
        native_attempts(operation)
        screenshot(page,context,('13' if operation=='confirm' else '14')+'-'+operation+'-all-inputs-locked.png')
        submitted=row['content'];finish(pending,handler,operation,navigate=True)
        latest=read(d2)
        check(operation+' server content equals the full submitted visible scope',latest['content']==submitted)

    # A forced input event despite disabled native controls must stay for review.
    page.goto(base+'/ydental/clinical?document_id='+str(d1));open_editor(page)
    page.locator('#correction-reason').fill('合成异步事件防丢失核对')
    pending,handler=barrier('correct');page.locator('#correct-document').click();row=wait_pending(pending)
    late='合成异步更正响应前未同步文字'
    page.locator('[name=chief_complaint]').evaluate('(f,v)=>{f.value=v;f.dispatchEvent(new Event("input",{bubbles:true}))}',late)
    finish(pending,handler,'correct-forced-input')
    reconcile(late);latest=read(d1)
    check('forced correct preserves server submitted A and visible unsent B',latest['content']==row['content'] and text()==late)
    screenshot(page,context,'15-correct-forced-input-retained.png')
    explicit_reload();page.locator('#release-document').click();page.wait_for_function('document.querySelector("textarea").disabled')

    # Normal handover with a held response; same frozen scope and real continuation.
    page.goto(base+'/ydental/clinical?document_id='+str(d2));open_editor(page)
    pending,handler=barrier('handover');page.locator('#handover-document').click();row=wait_pending(pending)
    native_attempts('handover');screenshot(page,context,'16-handover-all-inputs-locked.png')
    submitted=row['content'];finish(pending,handler,'handover',navigate=True)
    check('normal handover server scope unchanged',read(d2)['content']==submitted)
    front.goto(base+'/ydental/queue');check('D2 handover offers exactly one continuation',front.locator('form[data-queue-form=report]').count()==1)
    click_wait(front,'form[data-queue-form=report] button')
    page.goto(base+'/ydental/queue');click_wait(page,'button[data-operation=call]');click_wait(page,'button[data-operation=start]')
    page.goto(base+'/ydental/clinical');open_editor(page);d3=document_id()
    check('new D3 lawful reception has independent document',d3 not in (d1,d2))
    page.locator('[name=chief_complaint]').fill('合成D3确认提交范围A')
    page.locator('#save-document').click();version(page,1)
    pending,handler=barrier('confirm');page.locator('#confirm-document').click();row=wait_pending(pending)
    late='合成D3确认响应前未同步B'
    page.locator('[name=chief_complaint]').evaluate('(f,v)=>{f.value=v;f.dispatchEvent(new Event("input",{bubbles:true}))}',late)
    finish(pending,handler,'confirm-forced-input');reconcile(late)
    check('forced confirm never includes unsent B in confirmed A',read(d3)['content']==row['content'])
    screenshot(page,context,'17-confirm-forced-input-retained.png')
    explicit_reload();page.locator('[name=chief_complaint]').fill(late);page.locator('#correction-reason').fill('核对原确认后合法补记B');click_wait(page,'#correct-document')
    check('unsent confirm text can be lawfully appended with reason',read(d3)['content']['chief_complaint']==late)

    # A DOM mutation with no input event is also detected by the content snapshot.
    open_editor(page);pending,handler=barrier('handover');page.locator('#handover-document').click();row=wait_pending(pending)
    late='合成交还响应前异步无事件文字'
    page.locator('[name=chief_complaint]').evaluate('(f,v)=>{f.value=v}',late)
    finish(pending,handler,'handover-forced-no-event');reconcile(late,handover=True)
    check('forced handover preserves committed A and unsent B without undo',read(d3)['content']==row['content'])
    screenshot(page,context,'18-handover-committed-unsent-retained.png')
    explicit_reload();page.locator('[name=chief_complaint]').fill(late);page.locator('#correction-reason').fill('交还后核对并合法补记');click_wait(page,'#correct-document')
    check('pending supplementation does not reoccupy reception',page.locator('#execution-state').get_attribute('data-state')=='handover' and read(d3)['content']['chief_complaint']==late)

    # Lost response after commit, connection failure before POST, and genuine CAS
    # rejection: all preserve text and require server inspection without retry.
    for index,mode in enumerate(('response-lost','request-not-sent','stale-version'),19):
        open_editor(page);before=read(d3)
        late='合成网络或旧版本核对-'+mode
        page.locator('[name=chief_complaint]').fill(late);page.locator('#correction-reason').fill('合成异常恢复验证')
        pending,handler=barrier('correct',send=mode!='request-not-sent',stale=mode=='stale-version')
        page.locator('#correct-document').click();row=wait_pending(pending);page.wait_for_timeout(650)
        finish(pending,handler,'correct-'+mode,abort=mode!='stale-version');reconcile(late)
        after=read(d3)
        check(mode+' real server outcome matches request and is never retried',
              len(pending)==1 and (after['version']==before['version']+1 and after['content']['chief_complaint']==late if mode=='response-lost' else after['version']==before['version'] and after['content']==before['content']))
        screenshot(page,context,str(index)+'-'+mode+'-reconcile.png')
        explicit_reload();page.locator('#release-document').click();page.wait_for_function('document.querySelector("textarea").disabled')
    result['documents']['D3']=d3

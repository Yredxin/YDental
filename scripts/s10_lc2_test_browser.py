"""Focused offline browser-boundary tests; every transport object is a fake.

No Playwright import, Firefox launch, socket, Odoo or database is involved.
These assertions establish tool behavior, never real browser/UI acceptance.
"""
import asyncio
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import traceback
import unittest
from unittest.mock import AsyncMock, patch
from urllib.parse import urlencode

from s10_lc2_browser import BrowserBoundaryError, BrowserSession, Credentials, run_browser
from s10_lc2_family import run_family
from s10_lc2_http import Client, FAMILY_CLINICAL_VALUES, FAMILY_PATIENT_VALUES, _FamilyWriteScope
from s10_lc2_test_http import FakeOpener, FakeResponse


DATABASE = 'ydental_s10_test_20261017105432_810a7d9c'
SCRATCH = 'ydental_s10_test_20261017105432_ce6dcbf8'
BASE = 'http://127.0.0.1:18410'


class FakeBudget:
    def __init__(self, deny=None):
        self.intents = []
        self.deny = deny

    def check_storage(self):
        return 0

    def consume(self, resource):
        if resource == self.deny:
            raise RuntimeError('synthetic-resource-exhausted')
        self.intents.append(resource)


class FakeRequest:
    def __init__(self, page, path, *, method='GET', body=None):
        self.url = path if path.startswith('http') else BASE + path
        self.method = method
        self.post_data = body
        self.headers = {'cookie': 'synthetic-session-cookie'}
        self.redirected_from = None
        self.frame = SimpleNamespace(page=page)


class FakeUpstream:
    def __init__(self, status=200, body=b'{}', headers=None):
        self.status, self.raw = status, body
        self.headers = headers or {'content-type': 'application/json'}
        self.disposed = False

    async def body(self):
        return self.raw

    async def dispose(self):
        self.disposed = True


class FakeRoute:
    def __init__(self, session, request, upstream, transport):
        self.session, self.request = session, request
        self.upstream, self.transport = upstream, transport
        self.fulfilled = None
        self.aborted = None

    async def fetch(self, **options):
        # Observable effects are ordered before the fake network boundary.
        # A missed durable intent or budget would fail at dispatch itself.
        count = len(self.transport) + 1
        if self.session.budget.intents.count('http') != count:
            raise AssertionError('HTTP_BUDGET_WAS_NOT_BEFORE_DISPATCH')
        if len(list(self.session.directory.glob('*.intent.json'))) != count:
            raise AssertionError('DURABLE_INTENT_WAS_NOT_BEFORE_DISPATCH')
        if options.get('max_redirects') != 0 or options.get('max_retries') != 0:
            raise AssertionError('HIDDEN_REDIRECT_OR_RETRY_WAS_ENABLED')
        self.transport.append(self.request)
        return self.upstream

    async def fulfill(self, *, response):
        self.fulfilled = response

    async def abort(self, reason):
        self.aborted = reason

    async def continue_(self):
        self.transport.append(self.request)


class FakePage:
    def __init__(self, session, responses):
        self.session, self.responses = session, iter(responses)
        self.transport, self.routes = [], []
        self.url = 'about:blank'

    async def goto(self, url, **kwargs):
        request = FakeRequest(self, url)
        route = FakeRoute(self.session, request, next(self.responses), self.transport)
        self.routes.append(route)
        await self.session._route(route)
        if route.aborted:
            raise RuntimeError('synthetic-aborted-browser-navigation')
        self.url = url
        observed = SimpleNamespace(request=request, status=route.upstream.status,
                                   headers=route.upstream.headers, url=url)
        self.session._on_response(observed)
        self.session._on_finished(request)
        return observed


class BrowserBoundaryCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='lc2-browser-offline-')
        self.directory = Path(self.temporary.name)
        self.addCleanup(self.temporary.cleanup)

    def session(self, responses=(), *, deny=None, name='case'):
        path = self.directory / name
        session = BrowserSession(BASE, database=DATABASE, owned_targets={DATABASE: BASE},
                                 budget=FakeBudget(deny), directory=path)
        session.page = FakePage(session, responses)
        return session

    def assert_no_secrets(self, session):
        forbidden = [b'synthetic-session-cookie', b'synthetic-password', b'synthetic-csrf',
                     b'synthetic-private-notice', b'synthetic-secondary-secret', b'synthetic-primary-secret']
        for path in session.directory.rglob('*'):
            if path.is_file():
                for value in forbidden:
                    self.assertNotIn(value, path.read_bytes(), path.name)

    def current_session(self, case='A-ORIGINAL'):
        budget = FakeBudget()
        budget.profile = SimpleNamespace(message_id='YD-S10-TECHNICAL-CLOSEOUT-V1',
            require_action=lambda action: None, validate_target=lambda *args: None)
        session = BrowserSession(BASE, database=DATABASE, owned_targets={DATABASE: BASE},
                                 budget=budget, directory=self.directory / 'current', current_case=case,
                                 reader_partner_id=65 if case=='LOG-03' else None)
        session.page = SimpleNamespace()
        return session

    async def test_current_log03_normal_deeplink_restricts_record_and_write(self):
        session=self.current_session('LOG-03')
        def request(model,method,args):
            return FakeRequest(session.page,'/web/dataset/call_kw/'+model+'/'+method,
                method='POST',body=json.dumps({'params':{'model':model,'method':method,'args':args,'kwargs':{}}}))
        self.assertEqual(session._request_allowed(FakeRequest(session.page,
            '/odoo/ydental.access.audit/228')),'/odoo/ydental.access.audit/228')
        self.assertEqual(session._request_allowed(request('ydental.access.audit','web_read',[[228]])),
            '/web/dataset/call_kw/ydental.access.audit/web_read')
        self.assertEqual(session._request_allowed(request('ydental.access.audit','has_access',[[],'read'])),
            '/web/dataset/call_kw/ydental.access.audit/has_access')
        for call in (request('ydental.access.audit','web_read',[[229]]),
                     request('ydental.access.audit','has_access',[[229],'read']),
                     request('ydental.access.audit','write',[[228],{'ydental_reason':'tamper'}]),
                     request('ydental.settlement.payment','read',[[1]])):
            with self.assertRaises(BrowserBoundaryError):session._request_allowed(call)
        self.assertEqual(session._request_allowed(FakeRequest(session.page,
            '/web/image/res.partner/65/avatar_128')),'/web/image/res.partner/65/avatar_128')
        with self.assertRaises(BrowserBoundaryError):
            session._request_allowed(FakeRequest(session.page,'/web/image/res.partner/66/avatar_128'))

    async def test_current_native_exit_debug_window_requires_real_exit_line(self):
        session=self.current_session('E-AFFECTED-REGRESSION');session.native_process_debug=True
        log=self.directory/'parent-stderr.log';raw=b'[pid=123] <launched> pid=123\n[pid=123] <process did exit: exitCode=0, signal=null>\n'
        log.write_bytes(b'prefix-before-this-ui\n'+raw)
        session._native_debug_file=log;session._native_debug_offset=len(b'prefix-before-this-ui\n')
        session._finish_native_debug()
        self.assertEqual((session.directory/'native-browser-debug-window.log').read_bytes(),raw)
        facts=json.loads((session.directory/'native-browser-native-exit.json').read_bytes())
        self.assertEqual(facts['browser_native_processes'],[{'pid':123,'debug_exit_code':'0','debug_exit_signal':'null'}])
        session.directory=self.directory/'missing-exit';session.directory.mkdir(mode=0o700)
        log.write_bytes(b'[pid=123] <launched> pid=123\n');session._native_debug_offset=0
        with self.assertRaisesRegex(BrowserBoundaryError,'NATIVE_BROWSER_EXIT_NOT_CONFIRMED_ZERO'):
            session._finish_native_debug()

    async def test_current_parent_supervisor_correlates_exact_native_pid_and_birth(self):
        from s10_lc2_browser import _current_native_process_supervision
        import os,threading
        parent_thread=threading.current_thread()
        rows={123:{'pid':123,'parent_pid':os.getpid(),'birth_ticks':456,'exe_basename':'firefox'}}
        for label,debug_pid in [('same-owned-pid',123),('unobserved-pid',124)]:
            directory=self.directory/label;directory.mkdir(mode=0o700)
            (directory/'native-browser-native-exit.json').write_text(json.dumps({
                'browser_native_processes':[{'pid':debug_pid,'debug_exit_code':'0','debug_exit_signal':'null'}]}))
            async def operation():await asyncio.sleep(.12);return 'actual-callback-result'
            def tree():return {} if threading.current_thread()is parent_thread else rows
            with patch('s10_lc2_cases.process_tree',side_effect=tree):
                if debug_pid==123:
                    self.assertEqual(await _current_native_process_supervision(operation,directory),'actual-callback-result')
                    facts=json.loads((directory/'independent-process-closure.json').read_bytes())
                    self.assertEqual(facts['native_debug_owned_PID_birth_matches'][0]['birth_ticks'],456)
                    self.assertTrue(facts['current_owned_process_closure_observed'])
                else:
                    with self.assertRaisesRegex(BrowserBoundaryError,'NATIVE_BROWSER_DEBUG_PID_BIRTH_NOT_CORRELATED'):
                        await _current_native_process_supervision(operation,directory)

    async def test_current_process_supervisor_keeps_primary_if_evidence_write_fails(self):
        from s10_lc2_browser import _current_native_process_supervision
        primary=ValueError('synthetic-private-primary')
        async def operation():raise primary
        with patch('s10_lc2_cases.process_tree',return_value={}), \
             patch('s10_lc2_browser.save_once',side_effect=OSError('synthetic-private-secondary')), \
             patch('s10_lc2_browser.os.write') as stderr:
            with self.assertRaises(ValueError) as caught:
                await _current_native_process_supervision(operation,self.directory/'supervised')
        self.assertIs(caught.exception,primary)
        self.assertNotIn('synthetic-private',repr(stderr.call_args_list))

    async def test_current_plan_uses_native_request_without_fetch_or_fulfill(self):
        session = self.current_session()
        request = FakeRequest(session.page, '/web/login?db=' + DATABASE)
        transport = []
        route = FakeRoute(session, request, None, transport)
        await session._route(route)
        self.assertEqual(transport, [request])
        self.assertIsNone(route.fulfilled)
        self.assertIsNone(route.aborted)
        self.assertEqual(session.budget.intents, ['http'])
        intent = json.loads(next(session.directory.glob('*.intent.json')).read_bytes())
        self.assertEqual(intent['transport'], 'NATIVE_BROWSER')
        self.assertEqual(intent['guard_stage'], 'BEFORE_DISPATCH')
        self.assertFalse(intent['strict_redirect_network_isolation'])
        self.assert_no_secrets(session)

    async def test_current_plan_native_route_keeps_scope_before_dispatch(self):
        session = self.current_session()
        transport = []
        for path in ('http://127.0.0.1:18411/web/login', '/ydental/clinical/action',
                     '/ydental/settlement/bill-original/create'):
            route = FakeRoute(session, FakeRequest(session.page, path), None, transport)
            await session._route(route)
            self.assertEqual(route.aborted, 'blockedbyclient')
            session._fatal = None
        self.assertEqual(transport, [])
        self.assertEqual(session.budget.intents, [])

    async def test_current_plan_redirect_is_observed_without_claiming_preinterception(self):
        session = self.current_session()
        previous = FakeRequest(session.page, '/web/login', method='POST')
        request = FakeRequest(session.page, '/ydental/access')
        request.redirected_from = previous
        response = SimpleNamespace(request=request, url=request.url, status=200,
                                   headers={'content-type': 'text/html'})
        session._on_response(response)
        self.assertIsNone(session._fatal)
        intent = session._requests[request]
        self.assertEqual(intent['guard_stage'], 'REDIRECT_OBSERVED_AFTER_DISPATCH')
        self.assertFalse(intent['strict_redirect_network_isolation'])
        self.assert_no_secrets(session)

    async def test_current_revoked_browser_keeps_actor_and_purpose_narrow(self):
        session = self.current_session('C-REVOKED-PAGE')
        session._declared_login_user_id = 59
        request = FakeRequest(session.page, '/web/login', method='POST', body=urlencode({
            'db': DATABASE, 'login': 'synthetic-reader', 'password': 'synthetic-password',
            'csrf_token': 'synthetic-csrf', 'redirect': '/ydental/access'}))
        self.assertEqual(session._request_allowed(request), '/web/login')
        session._declared_login_user_id = 5
        with self.assertRaisesRegex(BrowserBoundaryError, 'LOGIN_ACTOR_MISMATCH'):
            session._request_allowed(request)
        with self.assertRaisesRegex(BrowserBoundaryError, 'PURPOSE_SWITCH_FORBIDDEN'):
            session.label('A-ORIGINAL')

    async def test_current_upgrade_original_needs_its_own_action(self):
        budget = FakeBudget()
        actions = []
        budget.profile = SimpleNamespace(message_id='YD-S10-TECHNICAL-CLOSEOUT-V1',
            require_action=actions.append, validate_target=lambda *args: None)
        session = BrowserSession(BASE, database=DATABASE, owned_targets={DATABASE: BASE},
            budget=budget, directory=self.directory / 'post', current_case='E-AFFECTED-REGRESSION')
        self.assertEqual(actions, ['E-AFFECTED-REGRESSION'])
        self.assertEqual(session.case_id, 'E-AFFECTED-REGRESSION')
        session._declared_login_user_id = 59
        with self.assertRaisesRegex(BrowserBoundaryError, 'LOGIN_ACTOR_MISMATCH'):
            session._request_allowed(FakeRequest(session.page, '/web/login', method='POST', body=''))

    async def test_current_revocation_unknown_does_not_issue_restore(self):
        session = self.current_session('C-REVOKED-PAGE')
        session._original_link = AsyncMock(return_value=object())
        session._screenshot = AsyncMock(return_value='synthetic-before.png')
        revoke = AsyncMock(side_effect=RuntimeError('SYNTHETIC_GRANT_OUTCOME_UNKNOWN'))
        restore = AsyncMock()
        with self.assertRaisesRegex(RuntimeError, 'SYNTHETIC_GRANT_OUTCOME_UNKNOWN'):
            await session.revoked_old_page(1, 1, patient_id=1,
                revoke_callback=revoke, restore_callback=restore)
        restore.assert_not_awaited()

    async def test_actual_nonredirect_upstream_is_forwarded_unchanged(self):
        upstream = FakeUpstream(409, b'{"error":"synthetic-password"}', {
            'content-type': 'application/json', 'set-cookie': 'synthetic-session-cookie'})
        session = self.session()
        request = FakeRequest(session.page, '/ydental/access/action', method='POST', body=urlencode({
            'operation': 'switch', 'store_id': 1, 'csrf_token': 'synthetic-csrf'}))
        route = FakeRoute(session, request, upstream, session.page.transport)
        await session._route(route)
        self.assertIs(route.fulfilled, upstream)
        self.assertIsNone(route.aborted)
        self.assertTrue(upstream.disposed)
        evidence = json.loads(next(session.directory.glob('*.response.json')).read_bytes())
        self.assertEqual((evidence['status'], evidence['bytes'], evidence['sha256']),
                         (409, len(upstream.raw), hashlib.sha256(upstream.raw).hexdigest()))
        self.assertEqual(evidence['transaction_commit'], 'NOT_OBSERVED')
        self.assert_no_secrets(session)

    async def test_scope_and_budget_denials_prevent_any_dispatch(self):
        denied = ['/ydental/queue', '/ydental/intake', '/ydental/supply',
                  '/ydental/treatment', '/ydental/exam', '/ydental/unknown',
                  'http://127.0.0.1:42433/web/login',
                  BASE + '/web/binary/company_logo?dbname=other_database']
        for index, path in enumerate(denied):
            with self.subTest(path=path):
                session = self.session(name='scope-%s' % index)
                route = FakeRoute(session, FakeRequest(session.page, path), FakeUpstream(), [])
                await session._route(route)
                self.assertFalse(route.transport)
                self.assertFalse(session.budget.intents)
                self.assertEqual(route.aborted, 'blockedbyclient')
        session = self.session(deny='http', name='budget')
        route = FakeRoute(session, FakeRequest(session.page, '/ydental/settlement'), FakeUpstream(), [])
        await session._route(route)
        self.assertFalse(route.transport)
        self.assertFalse(list(session.directory.glob('*.intent.json')))
        self.assertEqual(session._fatal, 'BROWSER_GUARD_OR_BUDGET_FAILED')

    async def test_manual_redirect_hops_are_fresh_budgeted_gets(self):
        session = self.session([
            FakeUpstream(303, b'redirect-actual-body', {'location': '/ydental/access', 'content-type': 'text/html'}),
            FakeUpstream(302, b'', {'location': '/ydental/settlement?notice=synthetic-private-notice'}),
            FakeUpstream(200, b'actual-final-page', {'content-type': 'text/html'}),
        ])
        response = await session._goto('/web/login?db=' + DATABASE)
        self.assertEqual(response.status, 200)
        self.assertEqual([request.method for request in session.page.transport], ['GET'] * 3)
        self.assertEqual(session.budget.intents, ['http'] * 3)
        self.assertEqual(session._manual_hop_count, 2)
        self.assertTrue(session.page.routes[0].aborted)
        self.assertTrue(session.page.routes[1].aborted)
        self.assertIsNotNone(session.page.routes[2].fulfilled)
        intents = [json.loads(path.read_bytes()) for path in session.directory.glob('*.intent.json')]
        self.assertEqual(sum(row['manual_redirect_hop'] for row in intents), 2)
        self.assertEqual(sum(row['redirect_parent_request_id'] is not None for row in intents), 2)
        self.assert_no_secrets(session)

    async def test_redirect_outside_origin_or_to_expiring_route_stops_before_follow(self):
        destinations = ['http://127.0.0.1:42433/ydental/settlement',
                        'http://example.invalid/ydental/settlement', '/ydental/queue',
                        '/web/login?db=other_database']
        for index, destination in enumerate(destinations):
            with self.subTest(destination=destination):
                session = self.session([FakeUpstream(303, b'', {'location': destination})], name='redirect-%s' % index)
                with self.assertRaises(BrowserBoundaryError):
                    await session._goto('/ydental/settlement')
                self.assertEqual(len(session.page.transport), 1)
                self.assertEqual(session.budget.intents, ['http'])
                self.assertFalse(session._redirects)

    async def test_manual_redirect_loop_has_a_finite_dispatch_limit(self):
        session = self.session([FakeUpstream(303, b'', {'location': '/ydental/settlement'}) for _ in range(10)])
        with self.assertRaisesRegex(BrowserBoundaryError, 'BROWSER_MANUAL_REDIRECT_LIMIT'):
            await session._goto('/ydental/settlement')
        # Initial request plus at most eight explicitly authorized fresh hops.
        self.assertEqual(len(session.page.transport), 9)
        self.assertEqual(session.budget.intents, ['http'] * 9)

    async def test_post_307_and_308_are_unknown_and_never_replayed(self):
        for status in (307, 308):
            session = self.session(name='post-%s' % status)
            request = FakeRequest(session.page, '/ydental/access/action', method='POST',
                                  body=urlencode({'operation': 'switch', 'store_id': 1}))
            route = FakeRoute(session, request, FakeUpstream(status, b'', {'location': '/ydental/access/action'}), [])
            await session._route(route)
            self.assertEqual(len(route.transport), 1)
            self.assertEqual(session._fatal, 'BROWSER_POST_REDIRECT_OUTCOME_UNKNOWN_STOP')
            self.assertFalse(session._redirects)
            self.assertIsNone(route.fulfilled)

    async def test_original_get_has_both_budget_intents_before_dispatch(self):
        session = self.session([FakeUpstream(200, b'%PDF-synthetic', {'content-type': 'application/pdf'})])
        await session._goto('/ydental/settlement/bill-original/1')
        self.assertEqual(session.budget.intents, ['original_get', 'http'])

    async def test_unavailable_body_has_no_invented_length_or_hash(self):
        session = self.session()
        request = FakeRequest(session.page, '/ydental/settlement')
        session._requests[request] = {'request_id': 'synthetic-request', 'case_id': 'C-SCOPE'}
        class UnavailableResponse:
            status = 303
            headers = {'content-type': 'text/html'}
            async def body(self):
                raise AssertionError('unobserved body must never be read')
        response = UnavailableResponse()
        response.request = request
        evidence = await session._response_evidence(response, body_unavailable=True, label='REDIRECT_BODY_UNAVAILABLE')
        self.assertIsNone(evidence['bytes'])
        self.assertIsNone(evidence['sha256'])
        self.assertEqual(evidence['body_observation'], 'NOT_OBSERVED')

    async def test_cleanup_and_secondary_writer_failure_preserve_first_exception(self):
        session = self.session()
        primary = ValueError('synthetic-primary-secret')
        async def failed_cleanup():
            raise OSError('synthetic-secondary-secret')
        observed = None
        try:
            try:
                raise primary
            except ValueError:
                await session._cleanup(failed_cleanup, 'reader.restore')
                with patch('s10_lc2_browser.save_once', side_effect=OSError('writer')):
                    with patch('s10_lc2_browser.os.write') as fallback:
                        await session._cleanup(failed_cleanup, 'session.close')
                self.assertTrue(fallback.called)
                raise
        except ValueError as error:
            observed = error
        self.assertIs(observed, primary)
        secondary = json.loads(next(session.directory.glob('*.secondary.json')).read_bytes())
        self.assertTrue(secondary['primary_preserved'])
        self.assertEqual(secondary['primary_exception_type'], 'ValueError')
        self.assert_no_secrets(session)

    async def test_cleanup_failure_without_primary_is_an_explicit_stop(self):
        session = self.session()
        async def failed_cleanup():
            raise OSError('synthetic-secondary-secret')
        with self.assertRaisesRegex(BrowserBoundaryError, 'BROWSER_CLEANUP_FAILED_STOP'):
            await session._cleanup(failed_cleanup, 'reader.restore')

    async def test_background_unbudgeted_event_at_exit_cannot_be_success(self):
        session = self.session()
        class FakeBrowser:
            closed = False
            async def close(self):
                self.closed = True
        session.browser = FakeBrowser()
        session._on_response(SimpleNamespace(request=object()))
        with self.assertRaisesRegex(BrowserBoundaryError, 'BROWSER_UNBUDGETED_REQUEST_OBSERVED'):
            await session.__aexit__(None, None, None)
        self.assertTrue(session.browser.closed, 'cleanup must run before fatal propagation')
        self.assertTrue(session._closed)

    async def test_failed_close_still_stops_driver_and_does_not_mark_reaped(self):
        session = self.session()
        class FakeBrowser:
            attempts = 0
            async def close(self):
                self.attempts += 1
                if self.attempts == 1:
                    raise OSError('synthetic-secondary-secret')
        class FakeDriver:
            stops = 0
            async def stop(self):
                self.stops += 1
        session.browser, session.playwright = FakeBrowser(), FakeDriver()
        with self.assertRaisesRegex(BrowserBoundaryError, 'BROWSER_CLEANUP_FAILED_STOP'):
            await session.__aexit__(None, None, None)
        self.assertEqual(session.playwright.stops, 1)
        self.assertFalse(session._closed)
        self.assertFalse(session._closing)
        await session.close()
        self.assertTrue(session._closed)
        self.assertEqual(session.browser.attempts, 2)

    async def test_startup_preserves_actual_primary_chain_before_safe_stop(self):
        session = self.session()
        class FakeFirefox:
            async def launch(self, **kwargs):
                try:
                    raise LookupError('synthetic-password')
                except LookupError as cause:
                    raise RuntimeError('synthetic-session-cookie') from cause
        class FakeDriver:
            firefox = FakeFirefox()
            stopped = False
            async def stop(self):
                self.stopped = True
        driver = FakeDriver()
        class FakeFactory:
            async def start(self):
                return driver
        session.factory = lambda: FakeFactory()
        with patch.dict('os.environ', {'PATH': '/synthetic/bin'}, clear=True):
            with self.assertRaisesRegex(BrowserBoundaryError, 'FIREFOX_CAPABILITY_OR_START_FAILED_STOP'):
                await session.__aenter__()
        chain = json.loads(next(session.directory.glob('*.startup-chain.json')).read_bytes())
        self.assertEqual([node['exception_type'] for node in chain['nodes']], ['RuntimeError', 'LookupError'])
        self.assertEqual(chain['nodes'][0]['link_type'], 'cause')
        self.assertTrue(chain['primary_event_id'])
        self.assertTrue(driver.stopped)
        self.assert_no_secrets(session)

    async def test_password_fill_error_never_escapes_as_message_or_traceback(self):
        session = self.session()
        class FakeLocator:
            def __init__(self, password):
                self.password = password
            async def fill(self, value):
                if self.password:
                    raise TimeoutError('progress.log fill("' + value + '") synthetic-session-cookie')
        class FakePage:
            def locator(self, selector):
                return FakeLocator(selector == 'input[name=password]')
        session.page = FakePage()
        async def local_login_page(path):
            return None
        session._goto = local_login_page
        login, password = 'synthetic-user', 'synthetic-password'
        observed = None
        try:
            await session.login(login, password)
        except BrowserBoundaryError as error:
            observed = error
        self.assertIsNotNone(observed)
        self.assertEqual(str(observed), 'BROWSER_UI_FAILED_STOP')
        public_trace = ''.join(traceback.format_exception(observed))
        self.assertNotIn(password, public_trace)
        self.assertNotIn('synthetic-session-cookie', public_trace)
        chain = json.loads(next(session.directory.glob('*.ui-chain.json')).read_bytes())
        self.assertEqual(chain['nodes'][0]['exception_type'], 'TimeoutError')
        self.assert_no_secrets(session)

    async def test_outer_browser_boundary_covers_post_login_third_party_error(self):
        session = self.session()
        class FakeAsyncSession:
            closed = False
            def __init__(self, *args, **kwargs):
                self.directory = kwargs['directory']
            async def __aenter__(self):
                return self
            async def __aexit__(self, *args):
                self.closed = True
            async def login(self, login, password):
                return None
            async def switch_store(self, store):
                raise TimeoutError('synthetic-password leaked in third-party progress text')
        credentials = Credentials('synthetic-user', 'synthetic-password')
        arguments = dict(base_url=BASE, database=DATABASE, owned_targets={DATABASE: BASE},
            budget=session.budget, directory=session.directory, phase='pre',
            manager_credentials=credentials, reader_credentials=credentials, store_id=1,
            invoice_id=1, original_id=1, original_sha256='a' * 64,
            revoke_reader=None, restore_reader=None)
        observed = None
        with patch('s10_lc2_browser.BrowserSession', FakeAsyncSession):
            try:
                await run_browser(**arguments)
            except BrowserBoundaryError as error:
                observed = error
        self.assertIsNotNone(observed)
        self.assertEqual(str(observed), 'BROWSER_UI_FAILED_STOP')
        self.assertNotIn(credentials.password, ''.join(traceback.format_exception(observed)))
        chain = json.loads(next(session.directory.glob('*.ui-chain.json')).read_bytes())
        self.assertEqual(chain['nodes'][0]['exception_type'], 'TimeoutError')
        self.assertFalse(list(session.directory.glob('*.browser-results.json')))
        self.assert_no_secrets(session)

    async def test_family_exact_new_objects_sequence_and_empty_finance_boundary(self):
        class FakeActor:
            def __init__(self, client, uid):
                self.client, self.uid, self.revision, self.csrf = client, uid, 1, 'synthetic-csrf'
            def action(self, endpoint, operation, payload, *, case, key):
                response = self.client.request('POST', '/ydental/' + endpoint + '/action', form={
                    'operation': operation, 'payload': json.dumps(payload), 'output': 'json',
                    'revision': self.revision, 'csrf_token': self.csrf, 'key': key}, case_id=case)
                response.require_status(200)
                return response.json()
            def rpc(self, model, method, args, *, case):
                response = self.client.rpc(model, method, args, case_id=case)
                return response, response.json()
        def rpc_result(value):
            return FakeResponse(json.dumps({'result': value}).encode())
        def accepted(identity, version=1, **other):
            return FakeResponse(json.dumps(dict(result='accepted', id=identity, version=version, **other)).encode())
        rows = [dict(id=10 + index, ydental_patient_id=[6, 'synthetic'],
                     ydental_origin_patient_id=[5 + index, 'synthetic'],
                     ydental_identity_snapshot={'patient_id': 5 + index, 'name': FAMILY_PATIENT_VALUES[index]['name']},
                     **{'ydental_' + name: value for name, value in FAMILY_CLINICAL_VALUES[index].items()})
                for index in range(2)]
        reader_dir, manager_dir = self.directory / 'family-reader', self.directory / 'family-manager'
        reader_budget, manager_budget = FakeBudget(), FakeBudget()
        reader_responses = [rpc_result([1]), rpc_result([1]), accepted(5), accepted(10),
            accepted(6), accepted(11), accepted(2),
            FakeResponse(FAMILY_PATIENT_VALUES[1]['name'].encode()),
            FakeResponse(' '.join(value for values in FAMILY_CLINICAL_VALUES for value in values.values()).encode()),
            rpc_result(rows), FakeResponse(b'{}', status=403),
            FakeResponse(json.dumps({'error': {'data': {'name': 'odoo.exceptions.AccessError'}}}).encode())]
        empty_workbench = ''.join('<section><h2>' + title + '</h2></section>' for title in (
            '今日未出账费用', '历史未出账费用', '待核对，禁止出账', '已出账未付清', '已结清本店账单', '线下付款与退款'))
        native_denied = FakeResponse(json.dumps({'error': {'data': {'name': 'odoo.exceptions.AccessError'}}}).encode())
        manager_responses = [accepted(2, 2, patient_id=6), FakeResponse(empty_workbench.encode()), native_denied, native_denied]
        reader_opener = FakeOpener(reader_responses, reader_budget, reader_dir)
        manager_opener = FakeOpener(manager_responses, manager_budget, manager_dir)
        reader = FakeActor(Client(BASE, database=DATABASE, owned_targets={DATABASE: BASE}, budget=reader_budget,
                                  directory=reader_dir, opener=reader_opener), 20)
        manager = FakeActor(Client(BASE, database=DATABASE, owned_targets={DATABASE: BASE}, budget=manager_budget,
                                   directory=manager_dir, opener=manager_opener), 5)
        grants, restores = [], []
        result = run_family(reader, manager, grants.append, lambda: restores.append(True),
                            directory=self.directory / 'family-result', protected_patient_ids=[1, 2, 3, 4])
        self.assertEqual(result['patient_ids'], [5, 6])
        self.assertEqual(result['exact_mutation_count'], 6)
        self.assertEqual(result['financial_positive_scope'], 'EMPTY_FAMILY_SCOPE')
        self.assertEqual(result['nonempty_family_financial_positive'], 'NOT_RUN')
        self.assertTrue(result['native_financial_model_rpc_guard_denied'])
        self.assertTrue(result['original_identity_snapshots_preserved'])
        self.assertEqual(restores, [True])
        self.assertEqual(grants[0]['settlement'], 'none')
        self.assertIsNone(reader.client._family_ticket)
        self.assertIsNone(manager.client._family_ticket)
        self.assertFalse(reader_opener.responses)
        self.assertFalse(manager_opener.responses)
        self.assertEqual(len(reader_opener.requests) + len(manager_opener.requests), 16)

    async def test_family_rejects_preexisting_patient_and_out_of_sequence_write(self):
        class NeverOpen:
            handlers = ()
            def open(self, *args, **kwargs):
                raise AssertionError('must not reach transport')
        def client(name):
            return Client(BASE, database=DATABASE, owned_targets={DATABASE: BASE}, budget=FakeBudget(),
                          directory=self.directory / name, opener=NeverOpen())
        reader, manager = client('scope-reader'), client('scope-manager')
        scope = _FamilyWriteScope(reader, manager, reader_uid=20, manager_uid=5,
                                  existing_patients=[1], existing_merges=[1], protected_patient_ids=[1, 2, 3, 4])
        with self.assertRaisesRegex(ValueError, 'FAMILY_WRITE_OUTSIDE_EXACT_NEW_FIXTURE_SEQUENCE'):
            with reader._family_request(scope, 'clinical', {'patient_id': 1, 'values': FAMILY_CLINICAL_VALUES[0]}):
                self.fail('protected patient must never receive a write ticket')
        with self.assertRaisesRegex(ValueError, 'FAMILY_WRITE_OUTSIDE_EXACT_NEW_FIXTURE_SEQUENCE'):
            with manager._family_request(scope, 'create', {'values': FAMILY_PATIENT_VALUES[0]}):
                self.fail('manager must not replace the reader creation actor')
        scope.dispatched = True
        with self.assertRaisesRegex(RuntimeError, 'FAMILY_CREATE_RETURNED_PREEXISTING_PATIENT_STOP'):
            scope.accept('create', {'result': 'accepted', 'id': 4, 'version': 1})
        self.assertFalse(scope.patient_ids)
        self.assertFalse(reader.budget.intents)
        with self.assertRaises(ValueError):
            reader._path('/ydental/patients/action')

    async def test_http_main_cannot_be_relabeled_scratch_to_reach_upstream(self):
        class NeverOpen:
            handlers = ()
            def open(self, *args, **kwargs):
                raise AssertionError('unexpected real dispatch')
        path = self.directory / 'http-main'
        client = Client(BASE, database=DATABASE, owned_targets={DATABASE: BASE},
                        budget=FakeBudget(), directory=path, opener=NeverOpen())
        for endpoint in ('/ydental/queue', '/ydental/intake', '/ydental/supply', '/ydental/treatment'):
            with self.assertRaisesRegex(ValueError, 'HTTP_APPLICATION_ROUTE_NOT_APPROVED_FOR_TARGET_ROLE'):
                client.request('GET', endpoint, case_id='C-SCOPE')
        for operation in ('open', 'save', 'confirm', 'correct', 'handover'):
            with self.assertRaisesRegex(ValueError, 'HTTP_MAIN_CLINICAL_REPLAY_FORBIDDEN'):
                client.request('POST', '/ydental/clinical/action', form={'operation': operation}, case_id='A-EDITOR')
        self.assertFalse(client.budget.intents)
        with self.assertRaisesRegex(ValueError, 'HTTP_TARGET_ROLE_IDENTITY_MISMATCH'):
            Client(BASE, database=DATABASE, owned_targets={DATABASE: BASE}, budget=FakeBudget(),
                   directory=self.directory / 'fake-scratch', opener=NeverOpen(), target_role='scratch')
        scratch_base = 'http://127.0.0.1:18411'
        scratch = Client(scratch_base, database=SCRATCH, owned_targets={SCRATCH: scratch_base},
                         budget=FakeBudget(), directory=self.directory / 'real-scratch-role',
                         opener=NeverOpen(), target_role='scratch')
        self.assertEqual(scratch._path('/ydental/treatment/action')[1], '/ydental/treatment/action')
        for endpoint in ('/ydental/exam', '/ydental/pharmacy', '/ydental/queue/unknown'):
            with self.assertRaises(ValueError):
                scratch._path(endpoint)


if __name__ == '__main__':
    unittest.main(verbosity=2)

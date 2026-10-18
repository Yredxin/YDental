"""Real Firefox UI observations for an explicitly dispatched LC2 owned target.

No browser, network or application starts at import. Credentials and response
text remain in RAM. The caller owns the runtime gate and independent database
verification; these UI observations never establish a committed transaction.
No HAR, browser profile, storage state, console text or full DOM is exported.
"""
import asyncio
from dataclasses import dataclass, field
from functools import wraps
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import time
from urllib.parse import parse_qs, unquote, urlencode, urljoin, urlsplit
import uuid

from s10_lc2_evidence import PROTECTED, save_once
from s10_lc2_http import (_private_directory, _save_bytes, _redacted_json, main_a_get_rule,
                          main_a_path_metadata, main_a_request_boundary)
from s10_lc2_supervisor import save_primary
from s10_lc2_task_profile import (MAIN_A_AUTONOMY, MAIN_A_ENGINEERING, MAIN_A_ORIGINAL_UI,
                                  MAIN_A_PRIVATE_LOG_PROFILES, MAIN_A_PROFILES, MAIN)

CURRENT_PLAN = 'YD-S10-TECHNICAL-CLOSEOUT-V1'


_DATABASE = re.compile(r'ydental_s10_test_[0-9]{14}_[a-f0-9]{8}\Z')
_SHA256 = re.compile(r'[a-f0-9]{64}\Z')
_ORIGINAL = re.compile(r'/ydental/settlement/bill-original/[1-9][0-9]*/?\Z')
_READ_METHODS = frozenset({
    'read', 'web_read', 'web_search_read', 'search', 'search_read', 'search_count',
    'search_fetch', 'fields_get', 'get_views', 'get_view', 'name_search',
    'read_group', 'formatted_read_group', 'formatted_read_grouping_sets',
    'has_group', 'has_groups', 'context_get', 'action_get', 'systray_get_activities',
    'get_discuss_settings', 'get_web_translations', 'get_field_translations',
    'searchpanel_select_range', 'searchpanel_select_multi_range', 'get_metadata',
})
_CASES = frozenset({'A-ORIGINAL', 'A-EDITOR', 'B-RPC-6', 'C-REVOKED-PAGE',
                    'E-AFFECTED-REGRESSION', 'C-SCOPE'})
_NATIVE = frozenset({'odoo.exceptions.AccessError', 'odoo.exceptions.UserError',
                     'odoo.exceptions.ValidationError'})
_INVALID_OPERATION = 'lc2_invalid_operation'


class BrowserBoundaryError(RuntimeError):
    """A fixed reason code; never include a URL, payload or browser traceback."""


_DRIVER_ENV_KEYS = frozenset({
    'PATH', 'HOME', 'USER', 'LOGNAME', 'SHELL', 'LANG', 'LANGUAGE', 'LC_ALL', 'LC_CTYPE',
    'TZ', 'TMPDIR', 'TMP', 'TEMP', 'DISPLAY', 'WAYLAND_DISPLAY', 'XAUTHORITY',
    'XDG_RUNTIME_DIR', 'XDG_CACHE_HOME', 'XDG_CONFIG_HOME', 'XDG_DATA_HOME',
    'SYSTEMROOT', 'WINDIR', 'COMSPEC', 'PATHEXT', 'USERPROFILE', 'LOCALAPPDATA',
})


def driver_environment(ambient):
    """The Python driver inherits ambient env; refuse rather than mutate it.

    async_playwright.start has no env argument. Its coordinator must already
    have this minimal environment; Firefox may add only approved local libraries.
    Unknown/debug/preload/proxy variables never silently reach either child.
    """
    if type(ambient) is not dict or any(type(k) is not str or type(v) is not str
                                       for k, v in ambient.items()):
        raise BrowserBoundaryError('DRIVER_ENVIRONMENT_INVALID')
    if set(ambient) - _DRIVER_ENV_KEYS:
        raise BrowserBoundaryError('DRIVER_ENVIRONMENT_NOT_WHITELISTED')
    return dict(ambient)


def firefox_environment(ambient, executable_path, *, diagnostic=False):
    """Only the selected Firefox child receives its existing local library paths."""
    if type(diagnostic) is not bool or type(ambient) is not dict:
        raise BrowserBoundaryError('FIREFOX_CHILD_ENVIRONMENT_INVALID')
    clean = dict(ambient)
    if diagnostic:
        if clean.pop('DEBUG', None) != 'pw:browser':
            raise BrowserBoundaryError('FIREFOX_DIAGNOSTIC_DEBUG_INVALID')
    clean = driver_environment(clean)
    root = Path(__file__).resolve().parents[1]
    dependencies = root / '.local/s00-b-deps'
    selected = dependencies / 'browsers/firefox-1543/firefox/firefox'
    libraries = dependencies / 'browser-libs/usr/lib/x86_64-linux-gnu'
    executable = Path(executable_path)
    if (executable != selected or not executable.is_file() or executable.is_symlink()
            or not libraries.is_dir() or libraries.is_symlink()
            or not selected.parent.resolve().is_relative_to(dependencies)
            or not libraries.resolve().is_relative_to(dependencies)):
        raise BrowserBoundaryError('FIREFOX_EXISTING_LOCAL_DEPENDENCIES_INVALID')
    clean['LD_LIBRARY_PATH'] = os.pathsep.join((str(selected.parent), str(libraries)))
    if diagnostic:
        clean['DEBUG'] = 'pw:browser'
    return clean


def _preserve_browser_failure(directory, primary, stage):
    """Save structural evidence only, before replacing third-party UI text."""
    try:
        preserved = save_primary(directory, primary, stage=stage)
    except BaseException:
        try:
            os.write(2, b'LC2_BROWSER_PRIMARY_EVIDENCE_UNAVAILABLE\n')
        except OSError:
            pass
        return
    try:
        root = Path(__file__).resolve().parents[1]
        spec = importlib.util.spec_from_file_location('_lc2_browser_diagnostics', root / 'ydental_access/diagnostics.py')
        diagnostics = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(diagnostics)
        chain = diagnostics.safe_exception_chain(primary)
        chain['primary_event_id'] = preserved['event_id']
        if len(json.dumps(chain, ensure_ascii=True).encode()) > diagnostics.MAX_EXCEPTION_CHAIN_BYTES:
            raise ValueError('BROWSER_PRIMARY_CHAIN_EXCEEDS_BOUND')
        suffix = 'startup-chain' if stage == 'browser.startup' else 'ui-chain'
        save_once(Path(directory) / (preserved['event_id'] + '.' + suffix + '.json'), chain)
    except BaseException as secondary:
        try:
            save_primary(directory, secondary, stage='browser.evidence.secondary',
                         root_event_id=preserved['event_id'])
        except BaseException:
            try:
                os.write(2, b'LC2_BROWSER_SECONDARY_EVIDENCE_UNAVAILABLE\n')
            except OSError:
                pass


def _safe_browser_entrypoint(stage):
    def decorate(method):
        @wraps(method)
        async def wrapped(*args, **kwargs):
            try:
                return await method(*args, **kwargs)
            except BaseException as primary:
                directory = args[0].directory if args else kwargs.get('directory')
                _preserve_browser_failure(directory, primary, stage)
                # Playwright fill/timeout messages can include the value just
                # typed. Neither that message nor its displayable context may
                # reach the outer parent's raw stderr or public result.
                raise BrowserBoundaryError('BROWSER_UI_FAILED_STOP') from None
        return wrapped
    return decorate


@dataclass(frozen=True)
class Credentials:
    login: str = field(repr=False)
    password: str = field(repr=False)


@dataclass(frozen=True)
class _ForwardedResponse:
    """Actual upstream bytes, not constructed business results; RAM only."""
    request: object = field(repr=False)
    status: int
    headers: dict = field(repr=False)
    raw: bytes = field(repr=False)

    @property
    def url(self):
        return self.request.url

    async def body(self):
        return self.raw


class BrowserSession:
    """One Firefox launch with serial RAM-only personas.

    Historical profiles retain their forwarded transport. The current plan uses
    native navigation and downloads, guarding intercepted requests and observing
    automatic redirect hops. Firefox does not intercept every redirect hop; this
    is target validation and observation, not strict network isolation.
    """

    def __init__(self, base_url, *, database, owned_targets, budget, directory,
                 executable_path=None, playwright_root=None, locale='zh-CN',
                 playwright_factory=None, maximum_seconds=1200, current_case='A-ORIGINAL'):
        parsed = urlsplit(base_url)
        if (parsed.scheme != 'http' or parsed.hostname != '127.0.0.1'
                or parsed.port not in range(18410, 18420) or parsed.username or parsed.password
                or parsed.path or parsed.query or parsed.fragment
                or base_url != 'http://127.0.0.1:%s' % parsed.port
                or not _DATABASE.fullmatch(database) or database in PROTECTED
                or type(owned_targets) is not dict or owned_targets.get(database) != base_url):
            raise BrowserBoundaryError('BROWSER_TARGET_NOT_OWNED')
        if type(maximum_seconds) not in (int, float) or not 1 <= maximum_seconds <= 1200:
            raise BrowserBoundaryError('BROWSER_DURATION_NOT_APPROVED')
        if locale not in {'zh-CN', 'en-US'}:
            raise BrowserBoundaryError('BROWSER_LOCALE_NOT_APPROVED')
        root = Path(__file__).resolve().parents[1]
        self.executable = Path(executable_path) if executable_path else root / '.local/s00-b-deps/browsers/firefox-1543/firefox/firefox'
        self.playwright_root = Path(playwright_root) if playwright_root else root / '.local/s00-b-deps/verify-lib'
        self.base_url, self.database, self.budget = base_url, database, budget
        self.task_profile = getattr(budget, 'profile', None)
        if self.native_transport:
            if current_case not in {'A-ORIGINAL', 'C-REVOKED-PAGE', 'E-AFFECTED-REGRESSION'}:
                raise BrowserBoundaryError('CURRENT_PLAN_BROWSER_CASE_NOT_DISPATCHED')
            self.task_profile.require_action(current_case)
            self.task_profile.validate_target(database, 2144129, parsed.port)
            if set(owned_targets) != {MAIN}:
                raise BrowserBoundaryError('CURRENT_PLAN_BROWSER_TARGET_SCOPE_INVALID')
        if self.task_profile is not None and self.task_profile.message_id in MAIN_A_PROFILES:
            self.task_profile.validate_target(database, 2144129, parsed.port)
            if set(owned_targets) != {MAIN}:
                raise BrowserBoundaryError('MAIN_A_BROWSER_TARGET_SCOPE_INVALID')
        self.directory = _private_directory(directory)
        self.artifacts = _private_directory(self.directory / 'binary-artifacts')
        self.locale, self.maximum_seconds = locale, maximum_seconds
        self.factory = playwright_factory
        self.browser = self.context = self.page = self.playwright = None
        self.started = None
        self.case_id = current_case if self.native_transport else 'A-ORIGINAL'
        self._current_case = self.case_id
        self.operation_ref = uuid.uuid4().hex
        self._fatal = None
        self._requests = {}
        self._responses = []
        self._forward_waiters = []
        self._redirects = {}
        self._redirect_parent = {}
        self._manual_pages = set()
        self._upstream_count = 0
        self._manual_hop_count = 0
        self._blocked_websockets = 0
        self._pageerrors = 0
        self._context_count = 0
        self._logged_in = False
        self._declared_login_user_id = None
        self._allow_audit = None
        self._allow_invalid_settlement = False
        self._allow_invalid_editor = None
        self._closed = False
        self._closing = False
        self._watchdog = None

    @property
    def native_transport(self):
        return getattr(self.task_profile, 'message_id', None) == CURRENT_PLAN

    def _check(self):
        if self._fatal:
            raise BrowserBoundaryError(self._fatal)
        if self.started is not None and time.monotonic() - self.started >= self.maximum_seconds:
            raise BrowserBoundaryError('BROWSER_SESSION_DURATION_EXHAUSTED')
        self.budget.check_storage()

    def _target_path(self, url):
        parsed = urlsplit(url)
        if (parsed.scheme != 'http' or parsed.netloc != urlsplit(self.base_url).netloc
                or parsed.username or parsed.password or parsed.fragment
                or unquote(parsed.path) != parsed.path or '\\' in parsed.path
                or any(part in {'.', '..'} for part in parsed.path.split('/'))):
            raise BrowserBoundaryError('BROWSER_NETWORK_OUTSIDE_OWNED_TARGET')
        if parsed.path.startswith('/web/database') or 'bill-original/create' in parsed.path:
            raise BrowserBoundaryError('BROWSER_PROTECTED_OPERATION')
        query = parse_qs(parsed.query, keep_blank_values=True)
        for name in ('db', 'dbname'):
            if name in query and query[name] != [self.database]:
                raise BrowserBoundaryError('BROWSER_DATABASE_QUERY_DRIFT')
        return parsed.path

    def _request_allowed(self, request):
        path = self._target_path(request.url)
        if self.native_transport:
            if self.case_id != self._current_case:
                raise BrowserBoundaryError('CURRENT_PLAN_BROWSER_CASE_NOT_DISPATCHED')
            self.task_profile.require_action(self.case_id)
            form = None
            if request.method == 'POST':
                parsed_form = parse_qs(request.post_data or '', keep_blank_values=True)
                if any(len(values) != 1 for values in parsed_form.values()):
                    raise BrowserBoundaryError('CURRENT_PLAN_BROWSER_DUPLICATE_FORM_FIELD')
                form = {key: values[0] for key, values in parsed_form.items()}
                expected_user = 59 if self.case_id == 'C-REVOKED-PAGE' else 5
                if path == '/web/login' and self._declared_login_user_id != expected_user:
                    raise BrowserBoundaryError('CURRENT_PLAN_BROWSER_LOGIN_ACTOR_MISMATCH')
            try:
                main_a_request_boundary(request.method, request.url, form=form,
                                        allow_translations=True, original_ui=True)
            except (TypeError, ValueError):
                raise BrowserBoundaryError('CURRENT_PLAN_BROWSER_REQUEST_FORBIDDEN') from None
            return path
        if self.task_profile is not None and self.task_profile.message_id in MAIN_A_PROFILES:
            self.task_profile.verify()
            allowed_cases = {'A-ORIGINAL'}
            if self.task_profile.message_id in {MAIN_A_AUTONOMY, MAIN_A_ENGINEERING}:
                allowed_cases.add('A-EDITOR')
            if (self.case_id not in allowed_cases
                    or path == '/ydental/clinical' and self.task_profile.message_id not in {MAIN_A_AUTONOMY, MAIN_A_ENGINEERING}):
                raise BrowserBoundaryError('MAIN_A_BROWSER_CASE_FORBIDDEN')
            form = None
            if request.method == 'POST':
                parsed_form = parse_qs(request.post_data or '', keep_blank_values=True)
                if any(len(values) != 1 for values in parsed_form.values()):
                    raise BrowserBoundaryError('MAIN_A_BROWSER_DUPLICATE_FORM_FIELD')
                form = {key: values[0] for key, values in parsed_form.items()}
            try:
                main_a_request_boundary(request.method, request.url, form=form,
                    allow_translations=self.task_profile.message_id in MAIN_A_PRIVATE_LOG_PROFILES,
                    original_ui=self.task_profile.message_id == MAIN_A_ORIGINAL_UI)
            except (TypeError, ValueError):
                raise BrowserBoundaryError('MAIN_A_BROWSER_REQUEST_FORBIDDEN') from None
        if request.method == 'GET':
            if self.task_profile is not None and self.task_profile.message_id == MAIN_A_ORIGINAL_UI:
                # Reuse the same checked rule rather than a second route list.
                main_a_get_rule(request.url, allow_translations=True, original_ui=True)
                return path
            approved = (path in {'/web', '/odoo', '/web/login', '/web/binary/company_logo',
                                 '/web/webclient/load_menus', '/web/webclient/translations',
                                 '/web/manifest.webmanifest', '/logo.png',
                                 '/ydental/access', '/ydental/clinical', '/ydental/settlement'}
                        or path.startswith(('/odoo/', '/web/assets/', '/web/static/',
                                            '/web/image/', '/web/webclient/load_menus/',
                                            '/ydental_clinical/static/'))
                        or bool(_ORIGINAL.fullmatch(path))
                        or bool(re.fullmatch(r'/ydental/settlement/pdf/(?:bill|receipt|refund)/[1-9][0-9]*', path)))
            if not approved:
                raise BrowserBoundaryError('BROWSER_GET_ROUTE_NOT_APPROVED')
            return path
        if request.method != 'POST':
            raise BrowserBoundaryError('BROWSER_METHOD_NOT_APPROVED')
        body = request.post_data or ''  # RAM only; never serialize this value.
        if len(body.encode()) > 128 * 1024:
            raise BrowserBoundaryError('BROWSER_REQUEST_TOO_LARGE')
        if path == '/web/login':
            if (self.task_profile is not None and self.task_profile.message_id == MAIN_A_ORIGINAL_UI
                    and getattr(self, '_declared_login_user_id', None) != 5):
                raise BrowserBoundaryError('ORIGINAL_UI_LOGIN_REQUIRES_USER5_PROVIDER')
            form = parse_qs(body, keep_blank_values=True)
            if 'db' in form and form['db'] != [self.database]:
                raise BrowserBoundaryError('BROWSER_LOGIN_DATABASE_DRIFT')
            return path
        if path == '/ydental/access/action':
            form = parse_qs(body, keep_blank_values=True)
            if form.get('operation') != ['switch']:
                raise BrowserBoundaryError('BROWSER_PERSONNEL_WRITE_NOT_APPROVED')
            return path
        if path == '/ydental/settlement/action' and self._allow_invalid_settlement:
            if parse_qs(body, keep_blank_values=True).get('operation') == [_INVALID_OPERATION]:
                return path
        if (path == '/ydental/clinical/action' and self.task_profile is not None
                and self.task_profile.message_id in {MAIN_A_AUTONOMY, MAIN_A_ENGINEERING}
                and self.case_id == 'A-EDITOR'):
            # The exact acquire/release payload already passed MAIN-A's gate.
            return path
        if path == '/ydental/clinical/action' and self._allow_invalid_editor:
            form = parse_qs(body, keep_blank_values=True)
            try:
                payload = json.loads(form.get('payload', [''])[0])
            except (ValueError, TypeError):
                raise BrowserBoundaryError('BROWSER_EDITOR_PROBE_FORMAT') from None
            if (form.get('operation') == ['heartbeat'] and type(payload) is dict
                    and set(payload) == {'document_id', 'editor_token'}
                    and payload == self._allow_invalid_editor):
                return path
        if path.startswith('/web/dataset/call_kw'):
            try:
                envelope = json.loads(body)
                params = envelope['params']
                model, method = params['model'], params['method']
                if method in _READ_METHODS and type(model) is str and not method.startswith('_'):
                    return path
                allowed = self._allow_audit
                if (allowed and model == 'ydental.access.audit' and method == 'write'
                        and params.get('args') == [[allowed], {'ydental_reason': 'LC2 denied tampering'}]):
                    return path
            except (KeyError, TypeError, ValueError):
                pass
            raise BrowserBoundaryError('BROWSER_RPC_WRITE_NOT_APPROVED')
        # Native webclient loading routes below only obtain already-authorized
        # session/assets/action metadata. No generic public RPC or button calls.
        if path in {'/web/webclient/translations', '/web/action/load', '/web/session/get_session_info',
                    '/web/dataset/search_read', '/web/webclient/load_menus'}:
            return path
        raise BrowserBoundaryError('BROWSER_POST_ROUTE_NOT_APPROVED')

    @staticmethod
    def _category(path):
        if _ORIGINAL.fullmatch(path):
            return 'STORED_ORIGINAL'
        if path.startswith('/ydental/settlement/pdf/'):
            return 'DYNAMIC_PDF'
        if path.startswith(('/web/assets/', '/web/static/', '/ydental_clinical/static/')):
            return 'ASSET'
        if path.startswith('/web/dataset/'):
            return 'RPC'
        return 'APPLICATION'

    @staticmethod
    def _rejected_path_class(url):
        # Return only fixed classifications; never retain the URL or query.
        path = urlsplit(url).path
        if path in {'/web/webclient/translations', '/website/translations'}:
            return 'NATIVE_TRANSLATIONS'
        if path == '/web/login':
            return 'NATIVE_LOGIN'
        if path.startswith('/web/session/'):
            return 'NATIVE_SESSION_ROUTE'
        if _ORIGINAL.fullmatch(path):
            return 'STORED_ORIGINAL'
        if path.startswith(('/web/assets/', '/web/static/')):
            return 'STATIC_ASSET'
        if path == '/ydental/clinical/action':
            return 'CLINICAL_ACTION'
        return 'OTHER_ROUTE'

    async def _route(self, route):
        if self.native_transport:
            await self._native_route(route)
            return
        request = route.request
        upstream = None
        upstream_attempted = False
        request_shape_valid = False
        response_status = None
        try:
            self._check()
            path = self._request_allowed(request)
            request_shape_valid = True
            if request.method == 'GET' and _ORIGINAL.fullmatch(path):
                self.budget.consume('original_get')
            self.budget.consume('http')
            request_id = uuid.uuid4().hex
            metadata = {'request_id': request_id, 'case_id': self.case_id,
                        'operation_ref': self.operation_ref, 'method': request.method,
                        'category': self._category(path), 'dispatched_epoch_ns': time.time_ns(),
                        'redirect_hop': request.redirected_from is not None,
                        'manual_redirect_hop': request.frame.page in self._manual_pages,
                        'redirect_parent_request_id': self._redirect_parent.get(request.frame.page),
                        'transport': 'BROWSER_UPSTREAM_FORWARDED',
                        'body_retention': 'MEMORY_ONLY', 'headers_retention': 'NONE',
                        'server_trace_id': None, 'server_request_id': None,
                        'correlation': 'CASE_OPERATION_HINT_AND_TIME_WINDOW'}
            if self.task_profile is not None and self.task_profile.message_id == MAIN_A_ORIGINAL_UI:
                metadata.update(main_a_path_metadata(request.method, request.url))
                metadata.update(guard_stage='BEFORE_UPSTREAM_VALIDATED', request_shape_valid=True)
                if request.method == 'POST':
                    metadata['matched_rule'] = ('ORIGINAL_UI_STANDARD_LOGIN_FORM' if path == '/web/login'
                                                else 'ORIGINAL_UI_STANDARD_STORE_SWITCH')
            save_once(self.directory / (request_id + '.intent.json'), metadata)
            self._requests[request] = metadata
            headers = dict(request.headers)
            headers.update({'X-YDental-Case-ID': self.case_id,
                            'X-YDental-Operation-Ref': self.operation_ref,
                            'X-YDental-Attempt': '1'})
            # Installed Firefox explicitly does not intercept native redirects.
            # A fetch with zero automatic redirects is the only network dispatch
            # here. Its exact response is forwarded unless navigation must stop.
            self._upstream_count += 1
            upstream_attempted = True
            upstream = await route.fetch(headers=headers, max_redirects=0, max_retries=0, timeout=15000)
            response_status = upstream.status
            raw = await upstream.body()
            if len(raw) > 16 * 1024 * 1024:
                raise BrowserBoundaryError('BROWSER_UPSTREAM_RESPONSE_TOO_LARGE')
            observed = _ForwardedResponse(request, upstream.status, dict(upstream.headers), raw)
            evidence = await self._response_evidence(observed, body=raw, label='REAL_UPSTREAM_RESPONSE')
            if (self.task_profile is not None and self.task_profile.message_id == MAIN_A_ORIGINAL_UI
                    and upstream.status >= 400 and request.method == 'GET'
                    and (path in {'/website/translations', '/web/webclient/translations'}
                         or path.startswith(('/web/assets/', '/web/static/')))):
                self._fatal = self._fatal or 'ORIGINAL_UI_BOOTSTRAP_UPSTREAM_HTTP_ERROR'
            if upstream.status in {301, 302, 303, 307, 308}:
                location = upstream.headers.get('location')
                evidence['redirect_location_present'] = isinstance(location, str)
                if not location:
                    raise BrowserBoundaryError('BROWSER_REDIRECT_WITHOUT_LOCATION')
                next_url = urljoin(request.url, location)
                self._target_path(next_url)
                if upstream.status in {307, 308} and request.method != 'GET':
                    self._fatal = 'BROWSER_POST_REDIRECT_OUTCOME_UNKNOWN_STOP'
                    # The POST has already reached the actual server. Never
                    # replay it just because its response asks for 307/308.
                    await route.abort('aborted')
                    return
                page = request.frame.page
                if page in self._redirects:
                    raise BrowserBoundaryError('BROWSER_CONCURRENT_REDIRECT_NOT_APPROVED')
                self._redirects[page] = (next_url, request_id)
                for predicate, future in tuple(self._forward_waiters):
                    if not future.done() and predicate(observed):
                        future.set_result(observed)
                await route.abort('aborted')
                return
            for predicate, future in tuple(self._forward_waiters):
                if not future.done() and predicate(observed):
                    future.set_result(observed)
            # No fabricated status, headers, JSON or UI response: pass exactly
            # what the owned Odoo upstream returned to the real browser code.
            await route.fulfill(response=upstream)
        except Exception as error:
            self._fatal = self._fatal or (str(error) if isinstance(error, BrowserBoundaryError)
                           else 'BROWSER_GUARD_OR_BUDGET_FAILED')
            try:
                save_once(self.directory / (uuid.uuid4().hex + '.route-rejection.json'), {
                    'kind': 'BROWSER_ROUTE_REJECTION_CLASSIFICATION',
                    'path_class': self._rejected_path_class(request.url),
                    'method': request.method if request.method in {'GET', 'POST'} else 'OTHER',
                    'upstream_attempted': upstream_attempted,
                    'request_shape_valid': request_shape_valid,
                    'guard_stage': 'UPSTREAM' if upstream_attempted else 'REQUEST_GUARD',
                    'response_received': response_status is not None, 'status': response_status,
                    'reason_code': self._fatal if re.fullmatch(r'[A-Z0-9_]{1,96}', self._fatal) else 'OTHER_FAILURE',
                    'query_and_body_retained': False, 'raw_path_retained': False,
                    **(main_a_path_metadata(request.method, request.url)
                       if self.task_profile is not None and self.task_profile.message_id == MAIN_A_ORIGINAL_UI else {}),
                })
            except Exception:
                self._fatal = self._fatal or 'BROWSER_ROUTE_REJECTION_EVIDENCE_FAILED'
            await route.abort('blockedbyclient')
        finally:
            if upstream is not None:
                try:
                    await upstream.dispose()
                except Exception:
                    # Dispose is local evidence-buffer cleanup, never a reason
                    # to repeat a request that already reached the server.
                    self._fatal = self._fatal or 'BROWSER_UPSTREAM_BUFFER_CLEANUP_FAILED_STOP'

    def _native_intent(self, request, *, redirect_observed=False):
        """Reserve before dispatch, or explicitly mark a native redirect observation."""
        self._check()
        path = self._request_allowed(request)
        if request in self._requests:
            return self._requests[request]
        if request.method == 'GET' and _ORIGINAL.fullmatch(path):
            self.budget.consume('original_get')
        self.budget.consume('http')
        request_id = uuid.uuid4().hex
        metadata = {'request_id': request_id, 'case_id': self.case_id,
                    'operation_ref': self.operation_ref, 'method': request.method,
                    'category': self._category(path), 'dispatched_epoch_ns': time.time_ns(),
                    'redirect_hop': request.redirected_from is not None,
                    'transport': 'NATIVE_BROWSER', 'redirect_policy': 'NATIVE_AUTOMATIC',
                    'guard_stage': 'REDIRECT_OBSERVED_AFTER_DISPATCH' if redirect_observed else 'BEFORE_DISPATCH',
                    'strict_redirect_network_isolation': False,
                    'body_retention': 'MEMORY_ONLY', 'headers_retention': 'NONE',
                    'server_trace_id': None, 'server_request_id': None,
                    'correlation': 'CASE_OPERATION_HINT_AND_TIME_WINDOW'}
        save_once(self.directory / (request_id + '.intent.json'), metadata)
        self._requests[request] = metadata
        return metadata

    async def _native_route(self, route):
        try:
            self._native_intent(route.request)
            # Preserve native request headers, cookies, bodies and responses.
            await route.continue_()
        except Exception as error:
            self._fatal = self._fatal or (str(error) if isinstance(error, BrowserBoundaryError)
                                         else 'BROWSER_GUARD_OR_BUDGET_FAILED')
            save_once(self.directory / (uuid.uuid4().hex + '.route-rejection.json'), {
                'kind': 'BROWSER_ROUTE_REJECTION_CLASSIFICATION',
                'path_class': self._rejected_path_class(route.request.url),
                'reason_code': self._fatal if re.fullmatch(r'[A-Z0-9_]{1,96}', self._fatal) else 'OTHER_FAILURE',
                'transport': 'NATIVE_BROWSER', 'response_received': False,
                'query_and_body_retained': False, 'raw_path_retained': False,
            })
            await route.abort('blockedbyclient')

    async def _websocket(self, socket):
        parsed = urlsplit(socket.url)
        if parsed.scheme != 'ws':
            self._fatal = 'BROWSER_WEBSOCKET_OUTSIDE_OWNED_TARGET'
        else:
            try:
                self._target_path('http://' + parsed.netloc + parsed.path + ('?' + parsed.query if parsed.query else ''))
                if parsed.path != '/websocket':
                    raise BrowserBoundaryError('BROWSER_WEBSOCKET_ROUTE_NOT_APPROVED')
            except BrowserBoundaryError:
                self._fatal = 'BROWSER_WEBSOCKET_OUTSIDE_OWNED_TARGET'
        # This UI assertion does not depend on the bus. Do not connect or claim
        # bus compatibility/performance; no actual handshake is dispatched.
        self._blocked_websockets += 1
        save_once(self.directory / (uuid.uuid4().hex + '.websocket-policy.json'), {
            'transport': 'WEBSOCKET_BLOCKED_BEFORE_NETWORK', 'dispatched': False,
            'bus_compatibility': 'NOT_TESTED', 'boundary_failure': self._fatal,
        })
        await socket.close(code=1008, reason='LC2 boundary')

    def _on_response(self, response):
        if self.native_transport:
            try:
                if response.request not in self._requests and response.request.redirected_from is not None:
                    self._native_intent(response.request, redirect_observed=True)
                intent = self._requests.get(response.request)
                if intent is None:
                    raise BrowserBoundaryError('BROWSER_UNBUDGETED_REQUEST_OBSERVED')
                location = response.headers.get('location')
                if response.status in {301, 302, 303, 307, 308} and location:
                    self._target_path(urljoin(response.url, location))
                save_once(self.directory / (uuid.uuid4().hex + '.native-response.json'), {
                    'request_id': intent['request_id'], 'case_id': intent['case_id'],
                    'status': response.status, 'transport': 'NATIVE_BROWSER',
                    'redirect_policy': 'NATIVE_AUTOMATIC', 'transaction_commit': 'NOT_OBSERVED',
                    'body_retention': 'NONE', 'headers_retention': 'NONE',
                })
                for predicate, future in tuple(self._forward_waiters):
                    if not future.done() and predicate(response):
                        future.set_result(response)
            except Exception as error:
                self._fatal = self._fatal or (str(error) if isinstance(error, BrowserBoundaryError)
                                             else 'BROWSER_NATIVE_RESPONSE_OBSERVATION_FAILED')
        if response.request not in self._requests:
            self._fatal = self._fatal or 'BROWSER_UNBUDGETED_REQUEST_OBSERVED'
        self._responses.append(response)

    def _on_finished(self, request):
        if request not in self._requests:
            self._fatal = self._fatal or 'BROWSER_UNBUDGETED_REQUEST_OBSERVED'

    async def _deadline(self):
        await asyncio.sleep(self.maximum_seconds)
        self._fatal = self._fatal or 'BROWSER_SESSION_DURATION_EXHAUSTED'
        if self.browser:
            try:
                await self.browser.close()
            except Exception:
                self._fatal = 'BROWSER_DEADLINE_CLOSE_FAILED_STOP'

    async def __aenter__(self):
        if self.started is not None:
            raise BrowserBoundaryError('BROWSER_SESSION_ALREADY_STARTED')
        # Validate before imports, factory.start, or any budget/child dispatch.
        child_env = driver_environment(dict(os.environ))
        if self.factory is None:
            if not self.executable.is_absolute() or not self.executable.is_file():
                raise BrowserBoundaryError('EXISTING_FIREFOX_UNAVAILABLE')
            if not self.playwright_root.is_absolute() or not (self.playwright_root / 'playwright').is_dir():
                raise BrowserBoundaryError('EXISTING_PLAYWRIGHT_UNAVAILABLE')
            if any(value and value != '0' for key, value in os.environ.items()
                   if key.startswith('MOZ_DISABLE_') and 'SANDBOX' in key):
                raise BrowserBoundaryError('SANDBOX_DISABLE_ENVIRONMENT_NOT_APPROVED')
            if str(self.playwright_root) not in sys.path:
                sys.path.insert(0, str(self.playwright_root))
            self.factory = importlib.import_module('playwright.async_api').async_playwright
        if self.task_profile is not None and self.task_profile.message_id in MAIN_A_PRIVATE_LOG_PROFILES:
            self.budget.consume('firefox', firefox_purpose='ui')
        else:
            self.budget.consume('firefox')
        self.started = time.monotonic()
        try:
            child_env = driver_environment(dict(os.environ))
            self.playwright = await self.factory().start()
            # No sandbox-disabling flags, preferences, proxy, persistent profile
            # or dependency installation. Capability refusal is a hard STOP.
            firefox_env = (firefox_environment(child_env, self.executable)
                if self.native_transport or self.task_profile is not None and self.task_profile.message_id in MAIN_A_PRIVATE_LOG_PROFILES
                else child_env)
            self.browser = await self.playwright.firefox.launch(
                executable_path=str(self.executable), headless=True, env=firefox_env)
            self._watchdog = asyncio.create_task(self._deadline())
            await self._new_context()
            return self
        except BaseException as primary:
            _preserve_browser_failure(self.directory, primary, 'browser.startup')
            await self._cleanup(self.close, 'startup.close')
            raise BrowserBoundaryError('FIREFOX_CAPABILITY_OR_START_FAILED_STOP') from None

    async def _new_context(self):
        self._check()
        if self.context:
            await self.context.close()
        self.context = await self.browser.new_context(
            locale=self.locale, viewport={'width': 1280, 'height': 900},
            accept_downloads=True, service_workers='block')
        self._context_count += 1
        self._logged_in = False
        self._declared_login_user_id = None
        await self.context.route('**/*', self._route)
        if not hasattr(self.context, 'route_web_socket'):
            raise BrowserBoundaryError('EXISTING_WEBSOCKET_GUARD_UNAVAILABLE')
        await self.context.route_web_socket('**/*', self._websocket)
        self.context.on('response', self._on_response)
        self.context.on('requestfinished', self._on_finished)
        self.page = await self.context.new_page()
        self.page.set_default_timeout(30000)
        self.page.on('pageerror', lambda error: self._count_pageerror())

    def _count_pageerror(self):
        self._pageerrors += 1  # Never save error text or console output.
        if self.task_profile is not None and self.task_profile.message_id == MAIN_A_ORIGINAL_UI:
            self._fatal = self._fatal or 'ORIGINAL_UI_UNHANDLED_PAGEERROR'

    def label(self, case_id):
        if case_id not in _CASES:
            raise BrowserBoundaryError('BROWSER_CASE_NOT_APPROVED')
        if self.native_transport and case_id != self._current_case:
            raise BrowserBoundaryError('CURRENT_PLAN_BROWSER_PURPOSE_SWITCH_FORBIDDEN')
        self.case_id, self.operation_ref = case_id, uuid.uuid4().hex

    async def _navigate_once(self, page, url):
        self._check()
        self._target_path(url)
        try:
            value = await page.goto(url, wait_until='domcontentloaded')
        except Exception:
            self._check()
            if page not in self._redirects:
                raise BrowserBoundaryError('BROWSER_NAVIGATION_FAILED_STOP') from None
            value = None  # Native follow was deliberately aborted after capture.
        self._check()
        return value

    async def _follow_redirects(self, page):
        last = None
        for _ in range(8):
            if page not in self._redirects:
                return last
            next_url, parent_id = self._redirects.pop(page)
            self._target_path(next_url)
            self._redirect_parent[page] = parent_id
            self._manual_pages.add(page)
            self._manual_hop_count += 1
            try:
                last = await self._navigate_once(page, next_url)
            finally:
                self._manual_pages.discard(page)
                self._redirect_parent.pop(page, None)
        if page in self._redirects:
            self._fatal = 'BROWSER_MANUAL_REDIRECT_LIMIT'
            raise BrowserBoundaryError(self._fatal)
        return last

    async def _perform(self, action, *, page=None):
        page = page or self.page
        try:
            await action()
        except Exception:
            self._check()
            if page not in self._redirects:
                raise BrowserBoundaryError('BROWSER_UI_ACTION_FAILED_STOP') from None
        self._check()
        return await self._follow_redirects(page)

    async def _forwarded_action(self, action, predicate):
        future = asyncio.get_running_loop().create_future()
        waiter = (predicate, future)
        self._forward_waiters.append(waiter)
        try:
            await self._perform(action)
            result = await asyncio.wait_for(future, timeout=30)
            await self._follow_redirects(self.page)
            return result
        finally:
            self._forward_waiters.remove(waiter)

    async def _goto(self, path):
        self._check()
        self._target_path(self.base_url + path)
        response = await self._navigate_once(self.page, self.base_url + path)
        final = await self._follow_redirects(self.page)
        self._check()
        return final or response

    async def _response_evidence(self, response, *, body=None, label, body_unavailable=False):
        self._check()
        intent = self._requests.get(response.request)
        if intent is None:
            raise BrowserBoundaryError('BROWSER_RESPONSE_NOT_BUDGETED')
        raw = None if body_unavailable else (await response.body() if body is None else body)
        if raw is not None and len(raw) > 16 * 1024 * 1024:
            raise BrowserBoundaryError('BROWSER_RESPONSE_TOO_LARGE')
        mime = response.headers.get('content-type', '').split(';')[0].lower()
        value = {'request_id': intent['request_id'], 'case_id': intent['case_id'],
                 'observation_ref': uuid.uuid4().hex, 'label': label,
                 'status': response.status, 'mime': mime if mime in {
                     'application/pdf', 'application/json', 'text/html', 'text/plain'} else 'other',
                 'bytes': len(raw) if raw is not None else None,
                 'sha256': hashlib.sha256(raw).hexdigest() if raw is not None else None,
                 'body_observation': 'NOT_OBSERVED' if raw is None else 'OBSERVED',
                 'body_retention': 'NONE' if raw is None else 'REDACTED_ONLY',
                 'redacted': {} if raw is None else _redacted_json(raw),
                 'transaction_commit': 'NOT_OBSERVED', 'server_trace_id': None,
                 'transport': 'NATIVE_BROWSER' if self.native_transport else 'BROWSER_UPSTREAM_FORWARDED',
                 'redirect_policy': 'NATIVE_AUTOMATIC' if self.native_transport else 'MANUAL_REDIRECT',
                 'correlation': 'CASE_OPERATION_HINT_AND_TIME_WINDOW'}
        if self.task_profile is not None and self.task_profile.message_id == MAIN_A_ORIGINAL_UI:
            value.update({key: intent[key] for key in (
                'route_template', 'static_resource_recognized', 'asset_bundle_filename',
                'query_keys', 'unknown_query_key_present', 'query_single_values',
                'query_shape_valid', 'matched_rule', 'request_shape_valid') if key in intent})
            value.update(guard_stage='UPSTREAM_RESPONSE_RECEIVED', upstream_attempted=True, response_received=True)
        save_once(self.directory / (value['observation_ref'] + '.response.json'), value)
        return value

    async def _screenshot(self, locator, *, mask=()):
        """Capture only the selected UI, with explicit masks, into private bytes."""
        self._check()
        raw = await locator.screenshot(type='png', mask=list(mask), animations='disabled')
        path = self.artifacts / (uuid.uuid4().hex + '.redacted-ui.png')
        _save_bytes(path, raw)
        return {'artifact': path.name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
                'retention': 'PRIVATE_REDACTED_SCREENSHOT'}

    async def _login_initialization_snapshot(self):
        """Observe only selected bootstrap configuration and input-state booleans."""
        result = {'phase': 'BEFORE_CREDENTIAL_INPUT', 'configuration_observed': False,
                  'translation_route': 'NOT_OBSERVED', 'bundle_language': 'NOT_OBSERVED',
                  'configuration_source': 'NOT_OBSERVED',
                  'html_language': 'NOT_OBSERVED',
                  'login_form_exists': False, 'login_form_visible': False,
                  'login_exists': False, 'login_visible': False, 'login_editable': False,
                  'password_exists': False, 'password_visible': False, 'password_editable': False,
                  'password_type_preserved': False, 'known_form_fields': [],
                  'unknown_form_fields_present': False, 'passkey_response_empty': True,
                  'boundary_failure_present': bool(self._fatal),
                  'observed_response_count': len(self._responses),
                  'failed_response_count': sum(getattr(row, 'status', 0) >= 400 for row in self._responses),
                  'dom_or_input_values_retained': False}
        try:
            configuration = await self.page.evaluate("""() => {
                // require() only returns an already-exported module. Native
                // @web/session deletes the bootstrap global after exporting it.
                const exported = window.odoo?.loader?.require('@web/session')?.session;
                const bootstrap = window.odoo?.__session_info__;
                const info = exported && typeof exported === 'object' ? exported
                    : bootstrap && typeof bootstrap === 'object' ? bootstrap : null;
                const observed = !!info && typeof info.bundle_params?.lang === 'string'
                    && info.bundle_params.lang.length > 0;
                const route = observed ? (info.translationURL || '/web/webclient/translations') : null;
                const language = observed ? info.bundle_params.lang : null;
                const html = document.documentElement.lang || '';
                const form = document.querySelector('form.oe_login_form');
                const passkey = form?.querySelector('[name=webauthn_response]');
                const knownFields = new Set(['csrf_token', 'db', 'login', 'password',
                    'redirect', 'type', 'webauthn_response']);
                const fields = form ? Array.from(form.elements).map(el => el.name).filter(Boolean) : [];
                return {configuration_observed: observed,
                    configuration_source: !info ? 'NOT_OBSERVED' : info === exported ? 'NATIVE_EXPORTED_MODULE'
                        : info === bootstrap ? 'BOOTSTRAP_GLOBAL' : 'NOT_OBSERVED',
                    translationURL: route === null ? null :
                        ['/website/translations', '/web/webclient/translations'].includes(route)
                            ? route : 'UNRECOGNIZED_TRANSLATION_ROUTE',
                    language: language === null ? null : ['en_US', 'zh_CN'].includes(language)
                        ? language : 'UNRECOGNIZED_LANGUAGE',
                    html_language: !html ? 'EMPTY' :
                        ['en', 'en-US', 'en_US', 'zh', 'zh-CN', 'zh_CN'].includes(html)
                            ? html : 'UNRECOGNIZED_LANGUAGE',
                    fields: fields.filter(name => knownFields.has(name)),
                    unknown_fields: fields.some(name => !knownFields.has(name)),
                    passkey_empty: !passkey || passkey.value === ''};
            }""")
            result['configuration_observed'] = configuration.get('configuration_observed') is True
            source = configuration.get('configuration_source')
            if source in {'NATIVE_EXPORTED_MODULE', 'BOOTSTRAP_GLOBAL'}:
                result['configuration_source'] = source
            if result['configuration_observed']:
                routes = {'/website/translations', '/web/webclient/translations'}
                result['translation_route'] = (configuration.get('translationURL')
                    if configuration.get('translationURL') in routes else 'UNRECOGNIZED_TRANSLATION_ROUTE')
                result['bundle_language'] = (configuration.get('language')
                    if configuration.get('language') in {'en_US', 'zh_CN'} else 'UNRECOGNIZED_LANGUAGE')
            html_language = configuration.get('html_language', '')
            result['html_language'] = (html_language if html_language in {
                'en', 'en-US', 'en_US', 'zh', 'zh-CN', 'zh_CN', 'EMPTY'}
                else 'EMPTY' if not html_language else 'UNRECOGNIZED_LANGUAGE')
            known_fields = {'csrf_token', 'db', 'login', 'password', 'redirect', 'type', 'webauthn_response'}
            fields = set(configuration.get('fields', []))
            result['known_form_fields'] = sorted(fields & known_fields)
            result['unknown_form_fields_present'] = configuration.get('unknown_fields') is True or bool(fields - known_fields)
            result['passkey_response_empty'] = configuration.get('passkey_empty') is True
            form = self.page.locator('form.oe_login_form')
            result['login_form_exists'] = await form.count() == 1
            if result['login_form_exists']:
                result['login_form_visible'] = await form.is_visible()
            for label in ('login', 'password'):
                field = form.locator('input[name=' + label + ']')
                result[label + '_exists'] = await field.count() == 1
                if result[label + '_exists']:
                    result[label + '_visible'] = await field.is_visible()
                    result[label + '_editable'] = await field.is_editable(timeout=1000)
                    if label == 'password':
                        result['password_type_preserved'] = await field.get_attribute('type') == 'password'
        except Exception as error:
            result['observation_exception_type'] = type(error).__name__
        return result

    async def _wait_login_form_ready(self, timeout=15):
        """Poll first-failure state while native bootstrap exposes its own form."""
        deadline = time.monotonic() + timeout
        observation = None
        try:
            while True:
                self._check()
                observation = await self._login_initialization_snapshot()
                self._check()
                if (observation['configuration_observed'] and (
                        observation['translation_route'] == 'UNRECOGNIZED_TRANSLATION_ROUTE'
                        or observation['bundle_language'] == 'UNRECOGNIZED_LANGUAGE'
                        or observation['unknown_form_fields_present']
                        or not observation['passkey_response_empty'])):
                    raise BrowserBoundaryError('ORIGINAL_UI_FRONTEND_CONFIGURATION_NOT_ADMITTED')
                required = ('configuration_observed', 'login_form_exists', 'login_form_visible', 'login_exists',
                    'login_visible', 'login_editable', 'password_exists', 'password_visible',
                    'password_editable', 'password_type_preserved')
                if (all(observation[key] for key in required)
                        and not observation['unknown_form_fields_present']
                        and observation['passkey_response_empty']):
                    return
                if time.monotonic() >= deadline:
                    raise BrowserBoundaryError('ORIGINAL_UI_NATIVE_LOGIN_FORM_NOT_READY')
                await asyncio.sleep(.1)
        finally:
            if observation is None:
                observation = await self._login_initialization_snapshot()
            save_once(self.directory / (uuid.uuid4().hex + '.login-readiness.json'), observation)

    @_safe_browser_entrypoint('browser.login')
    async def login(self, login, password, *, user_id=None):
        """Fresh context per persona; login/password/session/csrf stay in RAM."""
        self._check()
        if self._logged_in:
            await self._new_context()
        original_ui = self.task_profile is not None and self.task_profile.message_id == MAIN_A_ORIGINAL_UI
        current_ui = self.native_transport
        if original_ui and (type(user_id) is not int or user_id != 5):
            raise BrowserBoundaryError('ORIGINAL_UI_LOGIN_REQUIRES_USER5_PROVIDER')
        if current_ui and (type(user_id) is not int
                or user_id != (59 if self._current_case == 'C-REVOKED-PAGE' else 5)):
            raise BrowserBoundaryError('CURRENT_PLAN_BROWSER_LOGIN_ACTOR_MISMATCH')
        self._declared_login_user_id = user_id
        try:
            await self._goto('/web/login?' + urlencode({'db': self.database,
                'redirect': '/ydental/access' if original_ui or current_ui else '/ydental/settlement'}))
        finally:
            if original_ui:
                save_once(self.directory / (uuid.uuid4().hex + '.login-initialization.json'),
                          await self._login_initialization_snapshot())
        if original_ui:
            await self._wait_login_form_ready()
            await self._perform(lambda: self.page.locator('input[name=login]').fill(login, timeout=3000))
            await self._perform(lambda: self.page.locator('input[name=password]').fill(password, timeout=3000))
        else:
            # Native actionability waits decide readiness. Bootstrap diagnostics
            # never become an extra authentication prerequisite for this plan.
            form = self.page.locator('form.oe_login_form')
            await form.locator('input[name=login]').fill(login)
            await form.locator('input[name=password]').fill(password)
        submit = self.page.locator('form.oe_login_form button[type=submit]') if current_ui else self.page.locator('button[type=submit]')
        await self._perform(submit.click)
        if original_ui and urlsplit(self.page.url).path == '/web/login':
            raise BrowserBoundaryError('ORIGINAL_UI_NORMAL_LOGIN_NOT_ACCEPTED')
        await self.page.wait_for_url(lambda url: urlsplit(str(url)).path != '/web/login')
        self._check()
        self._logged_in = True

    async def switch_store(self, store_id):
        if type(store_id) is not int or store_id <= 0:
            raise BrowserBoundaryError('BROWSER_STORE_ID_INVALID')
        await self._goto('/ydental/access')
        form = self.page.locator('form').filter(has=self.page.locator('input[name=operation][value=switch]'))
        await form.locator('select[name=store_id]').select_option(str(store_id))
        await self._perform(form.locator('button[type=submit]').click)
        await self.page.wait_for_load_state('domcontentloaded')
        self._check()

    async def _original_link(self, invoice_id, original_id, patient_id=None):
        for number in (invoice_id, original_id):
            if type(number) is not int or number <= 0:
                raise BrowserBoundaryError('BROWSER_ORIGINAL_ID_INVALID')
        path = '/ydental/settlement'
        if patient_id is not None:
            if type(patient_id) is not int or patient_id <= 0:
                raise BrowserBoundaryError('BROWSER_PATIENT_ID_INVALID')
            path += '?' + urlencode({'patient_id': patient_id})
        await self._goto(path)
        rows = self.page.locator('section[name=settled-bills] tbody > tr')
        row = None
        for index in range(await rows.count()):
            candidate = rows.nth(index)
            if (await candidate.locator('td').first.inner_text()).strip() == str(invoice_id):
                row = candidate
                break
        if row is None:
            raise BrowserBoundaryError('SETTLED_INVOICE_ROW_NOT_OBSERVED')
        link = row.locator('a[href="/ydental/settlement/bill-original/%d"]' % original_id)
        if await link.count() != 1:
            raise BrowserBoundaryError('EXISTING_ORIGINAL_LINK_NOT_UNIQUE')
        # The real template renders its stored version. Do not create a new one
        # or silently substitute the current dynamic PDF link.
        if not re.search(r'版本\s*1\s*[）)]', await link.inner_text()):
            raise BrowserBoundaryError('EXISTING_ORIGINAL_IS_NOT_VERSION_ONE')
        return link

    async def download_original(self, invoice_id, original_id, expected_sha, *, patient_id=None, phase='pre'):
        if not _SHA256.fullmatch(expected_sha) or phase not in {'pre', 'post'}:
            raise BrowserBoundaryError('BROWSER_ORIGINAL_EXPECTATION_INVALID')
        self.label('A-ORIGINAL' if phase == 'pre' else 'E-AFFECTED-REGRESSION')
        link = await self._original_link(invoice_id, original_id, patient_id)
        screenshot = await self._screenshot(link)
        path = '/ydental/settlement/bill-original/%d' % original_id
        async with self.page.expect_response(lambda response: urlsplit(response.url).path == path) as observed:
            async with self.page.expect_download() as download_event:
                await link.click()
        response, download = await observed.value, await download_event.value
        temporary = await download.path()
        if temporary is None or Path(temporary).stat().st_size > 16 * 1024 * 1024:
            raise BrowserBoundaryError('BROWSER_DOWNLOAD_NOT_BOUNDED')
        raw = Path(temporary).read_bytes()
        destination = self.artifacts / (uuid.uuid4().hex + '.stored-original.pdf')
        _save_bytes(destination, raw)
        evidence = await self._response_evidence(response, body=raw, label='STORED_ORIGINAL_DOWNLOAD')
        evidence.update({'artifact': destination.name, 'screenshot': screenshot,
                         'stored_version': 1, 'actual_settled_row_link_clicked': True})
        save_once(self.directory / (uuid.uuid4().hex + '.original-check.json'), evidence)
        if response.status != 200 or evidence['mime'] != 'application/pdf' or not raw.startswith(b'%PDF'):
            raise BrowserBoundaryError('ORIGINAL_RESPONSE_IS_NOT_REAL_PDF')
        if evidence['sha256'] != expected_sha:
            raise BrowserBoundaryError('STORED_ORIGINAL_SHA_MISMATCH')
        self._check()
        return evidence

    async def revoked_old_page(self, invoice_id, original_id, *, revoke_callback,
                               restore_callback, patient_id=None):
        self.label('C-REVOKED-PAGE')
        link = await self._original_link(invoice_id, original_id, patient_id)
        before = await self._screenshot(link)
        path = '/ydental/settlement/bill-original/%d' % original_id
        verified_denial = False
        try:
            # No reload: the same already-authorized page and real link remain.
            await revoke_callback()
            async with self.page.expect_response(lambda response: urlsplit(response.url).path == path) as observed:
                await link.click()
            response = await observed.value
            raw = await response.body()
            evidence = await self._response_evidence(response, body=raw, label='REVOKED_OLD_PAGE_NEXT_REQUEST')
            evidence.update({'old_page_link_clicked_after_revocation': True,
                             'before_screenshot': before, 'pdf_body_returned': raw.startswith(b'%PDF')})
            save_once(self.directory / (uuid.uuid4().hex + '.revoked-page.json'), evidence)
            if response.status != 403 or raw.startswith(b'%PDF'):
                raise BrowserBoundaryError('REVOKED_PAGE_DID_NOT_DENY_NEXT_REQUEST')
            verified_denial = True
            return evidence
        finally:
            # Caller implements normal S01 grants for the new reader only.
            # No retry or public fixture bypass is performed by this adapter.
            # The current caller independently confirms each S01 grant before
            # returning. Unknown grants or unexpected content stop this path;
            # do not issue another permission write from a failure finally.
            if not self.native_transport or verified_denial:
                await self._cleanup(restore_callback, 'reader.restore')

    async def native_warning_dialog(self, audit_id, *, expected_name='odoo.exceptions.AccessError',
                                    expected_message='审计事件不可修改。'):
        if type(audit_id) is not int or audit_id <= 0 or expected_name not in _NATIVE:
            raise BrowserBoundaryError('BROWSER_NATIVE_PROBE_INVALID')
        self.label('B-RPC-6')
        await self._goto('/odoo')
        await self.page.wait_for_function('Boolean(window.odoo?.__WOWL_DEBUG__?.root?.env?.services?.orm)')
        # Open the normal YDental workspace first to establish the real SID
        # binding and take its already-rendered primitive revision, no ORM query.
        workspace = await self.context.new_page()
        try:
            await self._navigate_once(workspace, self.base_url + '/ydental/access')
            await self._follow_redirects(workspace)
            revision = int(await workspace.locator('input[name=revision]').first.input_value())
        finally:
            await self._cleanup(workspace.close, 'native.workspace.close')
        self._allow_audit = audit_id
        try:
            async with self.page.expect_response(lambda response: '/web/dataset/call_kw/' in urlsplit(response.url).path
                                                and response.request.method == 'POST'
                                                and 'ydental.access.audit' in (response.request.post_data or '')) as observed:
                # A genuine rejected orm.call promise enters the existing
                # unhandledrejection/error_service/registry path. No Error or
                # dialog is constructed here and no response is mocked.
                await self.page.evaluate('''([id, revision]) => {
                    window.odoo.__WOWL_DEBUG__.root.env.services.orm.call(
                        'ydental.access.audit', 'write', [[id], {ydental_reason: 'LC2 denied tampering'}],
                        {context: {ydental_revision: revision, lang: 'zh_CN'}});
                }''', [audit_id, revision])
            response = await observed.value
            raw = await response.body()
            evidence = await self._response_evidence(response, body=raw, label='REAL_NATIVE_RPC_ERROR')
            value = json.loads(raw)
            error_data = value.get('error', {}).get('data', {})
            actual_name = error_data.get('name')
            actual_arguments = error_data.get('arguments')
            actual_message = error_data.get('message')
            if actual_name != expected_name or actual_arguments != [expected_message] or actual_message != expected_message:
                raise BrowserBoundaryError('NATIVE_RPC_EXCEPTION_NAME_MISMATCH')
            dialog = self.page.locator('[role=dialog] .modal-dialog.modal-sm .o_error_dialog')
            await dialog.wait_for(state='visible')
            if (await dialog.locator('[role=alert] p.text-prewrap').count() != 1
                    or await dialog.locator('details, pre, code').count()
                    or await dialog.locator('button.o-default-button').count() != 1):
                raise BrowserBoundaryError('NATIVE_WARNING_DIALOG_SHAPE_MISMATCH')
            body_text = (await dialog.locator('[role=alert] p.text-prewrap').inner_text()).strip()
            if body_text != actual_arguments[0]:
                raise BrowserBoundaryError('NATIVE_WARNING_DIALOG_MESSAGE_MISMATCH')
            screenshot = await self._screenshot(dialog, mask=(dialog.locator('[role=alert]'),))
            evidence.update({'native_exception_name': actual_name, 'real_orm_rpc': True,
                             'dialog_observed': 'NATIVE_WARNING_DIALOG', 'screenshot': screenshot,
                             'native_arguments_match_expected_zh_cn': True,
                             'explicit_rpc_language_context': 'zh_CN',
                             'browser_locale_is_not_rpc_language_evidence': True,
                             'ui_message_matches_actual_rpc_arguments': True,
                             'message_sha256': hashlib.sha256(actual_message.encode()).hexdigest(),
                             'registry_contract': 'web.WarningDialog', 'handmade_dialog': False})
            evidence['bus_compatibility'] = 'NOT_TESTED_WEBSOCKET_BLOCKED_BEFORE_NETWORK'
            save_once(self.directory / (uuid.uuid4().hex + '.native-dialog.json'), evidence)
            await dialog.locator('button.o-default-button').click()
            return evidence
        finally:
            self._allow_audit = None

    async def safe_inline_error(self, document_id):
        """Existing clinical open button uses a known-invalid RAM token.

        This exercises real inline 403 handling. It cannot acquire an editor,
        save, confirm, correct or release clinical state. It is not a native
        WarningDialog test and is not the legitimate A editor-tail workflow.
        """
        if type(document_id) is not int or document_id <= 0:
            raise BrowserBoundaryError('BROWSER_DOCUMENT_ID_INVALID')
        self.label('A-EDITOR')
        await self._goto('/ydental/clinical?' + urlencode({'document_id': document_id}))
        invalid_token = uuid.uuid4().hex + uuid.uuid4().hex
        self._allow_invalid_editor = {'document_id': document_id, 'editor_token': invalid_token}
        try:
            await self.page.evaluate('([id, token]) => sessionStorage.setItem("ydental_clinical_editor_" + id, token)',
                                     [document_id, invalid_token])
            async with self.page.expect_response(lambda response: urlsplit(response.url).path == '/ydental/clinical/action') as observed:
                await self.page.locator('#open-document').click()
            response = await observed.value
            raw = await response.body()
            evidence = await self._response_evidence(response, body=raw, label='REAL_CLINICAL_INLINE_403')
            error = json.loads(raw).get('error')
            if response.status != 403 or not isinstance(error, str):
                raise BrowserBoundaryError('CLINICAL_INLINE_403_CONTRACT_FAILED')
            await self.page.wait_for_function('(expected) => document.querySelector("#clinical-result")?.textContent === expected', error)
            screenshot = await self._screenshot(self.page.locator('#open-document'))
            evidence.update({'ui': 'CUSTOM_CLINICAL_INLINE_ERROR', 'native_dialog': False,
                             'error_text_matches_actual_response': True, 'screenshot': screenshot})
            save_once(self.directory / (uuid.uuid4().hex + '.inline-error.json'), evidence)
            return evidence
        finally:
            async def remove_invalid_token():
                await self.page.evaluate('(id) => sessionStorage.removeItem("ydental_clinical_editor_" + id)', document_id)
            await self._cleanup(remove_invalid_token, 'editor.ram.cleanup')
            self._allow_invalid_editor = None

    async def settlement_error_contract(self):
        """Actual controller 409 JSON and native HTML form 303 notice.

        Only the operation input of an existing workbench form is replaced by
        a guaranteed unknown operation. No economic handler can be selected.
        """
        self.label('C-SCOPE')
        await self._goto('/ydental/settlement')
        form = self.page.locator('form[action="/ydental/settlement/action"]').first
        if not await form.count():
            raise BrowserBoundaryError('NO_EXISTING_SETTLEMENT_ACTION_FORM')
        self._allow_invalid_settlement = True
        try:
            async with self.page.expect_response(lambda response: urlsplit(response.url).path == '/ydental/settlement/action') as observed:
                await form.evaluate('''(form, operation) => {
                    const fields = new URLSearchParams(new FormData(form));
                    fields.set('operation', operation); fields.set('output', 'json');
                    fetch(form.action, {method: 'POST', body: fields});
                }''', _INVALID_OPERATION)
            response = await observed.value
            json_evidence = await self._response_evidence(response, label='REAL_CONTROLLER_JSON_409')
            if response.status != 409:
                raise BrowserBoundaryError('SETTLEMENT_JSON_409_CONTRACT_FAILED')
            async def submit_invalid_html():
                await form.evaluate('''(form, operation) => {
                    form.querySelector('[name=operation]').value = operation;
                    form.noValidate = true; form.requestSubmit();
                }''', _INVALID_OPERATION)
            redirected = await self._forwarded_action(submit_invalid_html,
                lambda response: urlsplit(response.url).path == '/ydental/settlement/action')
            # A redirect body may be unavailable to Firefox. Never invent
            # empty bytes or a SHA for an unobserved body.
            try:
                raw = await redirected.body()
            except Exception:
                raw = None
            html_evidence = await self._response_evidence(redirected, body=raw,
                body_unavailable=raw is None, label='REAL_CONTROLLER_HTML_REDIRECT')
            await self.page.locator('[data-ui1-feedback="1"]').wait_for(state='visible')
            notice = (await self.page.locator('[data-ui1-feedback="1"]').inner_text()).strip()
            html_evidence.update({'custom_html_notice_visible': notice == '请求未完成，请核对权限、门店或输入后重试。',
                                  'native_dialog': False})
            save_once(self.directory / (uuid.uuid4().hex + '.html-contract.json'), html_evidence)
            if redirected.status != 303 or not html_evidence['custom_html_notice_visible']:
                raise BrowserBoundaryError('SETTLEMENT_HTML_303_NOTICE_CONTRACT_FAILED')
            self._check()
            return {'json_409': json_evidence, 'html_303': html_evidence}
        finally:
            self._allow_invalid_settlement = False

    async def _cleanup(self, callback, stage):
        """A cleanup failure is secondary when an earlier failure is active."""
        primary = sys.exc_info()[1]
        try:
            await callback()
        except BaseException as secondary:
            try:
                save_once(self.directory / (uuid.uuid4().hex + '.secondary.json'), {
                    'kind': 'BROWSER_CLEANUP_SECONDARY', 'stage': stage,
                    'exception_type': type(secondary).__name__,
                    'primary_exception_type': type(primary).__name__ if primary is not None else None,
                    'primary_preserved': primary is not None,
                })
            except Exception:
                try:
                    os.write(2, b'LC2_BROWSER_CLEANUP_EVIDENCE_FAILED\n')
                except OSError:
                    pass
            if primary is None:
                raise BrowserBoundaryError('BROWSER_CLEANUP_FAILED_STOP') from None

    async def close(self):
        if self._closed:
            return
        if self._closing:
            raise BrowserBoundaryError('BROWSER_REENTRANT_CLOSE_STOP')
        self._closing = True
        if self._watchdog and self._watchdog is not asyncio.current_task():
            self._watchdog.cancel()
        async def stop_driver():
            if self.playwright:
                await self.playwright.stop()
        try:
            try:
                if self.browser:
                    await self.browser.close()
            finally:
                await self._cleanup(stop_driver, 'driver.stop')
            save_once(self.directory / (uuid.uuid4().hex + '.browser-close.json'), {
                'firefox_launches': int(self.started is not None), 'serial_ram_contexts': self._context_count,
                'routed_requests': len(self._requests), 'observed_responses': len(self._responses),
                'actual_upstream_fetches': self._upstream_count,
                'manual_redirect_hops': self._manual_hop_count,
                'blocked_websocket_handshakes': self._blocked_websockets,
                'transport': 'NATIVE_BROWSER' if self.native_transport else 'BROWSER_UPSTREAM_FORWARDED',
                'redirect_policy': 'NATIVE_AUTOMATIC' if self.native_transport else 'MANUAL_REDIRECT',
                'strict_redirect_network_isolation': False if self.native_transport else None,
                'pageerror_count': self._pageerrors, 'boundary_failure': self._fatal,
                'elapsed_seconds': round(time.monotonic() - self.started, 3) if self.started else 0,
                'credentials_retention': 'MEMORY_ONLY', 'browser_storage_exported': False,
                'process_exit_observation': 'PARENT_SUPERVISOR_REQUIRED',
            })
            self._closed = True
        finally:
            self._closing = False

    async def __aexit__(self, error_type, error, traceback):
        await self._cleanup(self.close, 'session.close')
        if error is None:
            # Background response/restore failures can arrive after the final
            # visible assertion. Reap first, then refuse a silent success.
            self._check()


@_safe_browser_entrypoint('browser.ui')
async def run_browser(*, base_url, database, owned_targets, budget, directory, phase,
                      manager_credentials, reader_credentials, store_id, invoice_id,
                      original_id, original_sha256, revoke_reader, restore_reader,
                      doctor_credentials=None, audit_id=None, document_id=None,
                      patient_id=None, **session_options):
    """Sequential A/C/GPR UI adapter, reused after E; no positive money action.

    Optional audit/document inputs are explicit NOT_RUN when omitted, so partial
    invocation cannot silently become acceptance of the complete UI matrix.
    Callbacks must use normal S01 HTTP grants for the new reader only.
    """
    if phase not in {'pre', 'post'}:
        raise BrowserBoundaryError('BROWSER_PHASE_INVALID')
    results = {'phase': phase, 'evidence_kind': 'REAL_FIREFOX_UI_UPSTREAM_FORWARDED',
               'redirect_policy': 'MANUAL_REDIRECT', 'native_automatic_redirect_acceptance': False,
               'native_warning': {'status': 'NOT_RUN'}, 'clinical_inline': {'status': 'NOT_RUN'}}
    async with BrowserSession(base_url, database=database, owned_targets=owned_targets,
                              budget=budget, directory=directory, **session_options) as session:
        await session.login(manager_credentials.login, manager_credentials.password)
        await session.switch_store(store_id)
        results['original'] = await session.download_original(invoice_id, original_id, original_sha256,
                                                               patient_id=patient_id, phase=phase)
        if audit_id is not None:
            results['native_warning'] = await session.native_warning_dialog(audit_id)
        if phase == 'pre':
            results['settlement_contract'] = await session.settlement_error_contract()
        if doctor_credentials is not None and document_id is not None:
            await session.login(doctor_credentials.login, doctor_credentials.password)
            await session.switch_store(store_id)
            results['clinical_inline'] = await session.safe_inline_error(document_id)
        await session.login(reader_credentials.login, reader_credentials.password)
        await session.switch_store(store_id)
        results['revoked_page'] = await session.revoked_old_page(invoice_id, original_id,
            patient_id=patient_id, revoke_callback=revoke_reader, restore_callback=restore_reader)
    save_once(Path(directory) / (uuid.uuid4().hex + '.browser-results.json'), results)
    return results


@_safe_browser_entrypoint('browser.main_a')
async def run_main_a_browser(*, base_url, database, owned_targets, budget, directory,
                             credentials, store_id, invoice_id, original_id,
                             original_sha256, patient_id, phase='pre', **session_options):
    """Only the authorized MAIN-A existing-v1 workbench click and download."""
    profile = getattr(budget, 'profile', None)
    current = getattr(profile, 'message_id', None) == CURRENT_PLAN
    if (phase not in {'pre', 'post'} or phase == 'post' and not current
            or profile is None or profile.message_id not in MAIN_A_PROFILES and not current
            or (store_id, invoice_id, original_id, patient_id) != (1, 1, 1, 1)
            or original_sha256 != '05928780e7d97a06cf29019634f64b010eb4994c2f1c5032d561008a50b059b4'):
        raise BrowserBoundaryError('MAIN_A_ORIGINAL_SCOPE_INVALID')
    profile.verify()
    if current:
        profile.require_action('A-ORIGINAL' if phase == 'pre' else 'E-AFFECTED-REGRESSION')
    async with BrowserSession(base_url, database=database, owned_targets=owned_targets,
                              budget=budget, directory=directory,
                              current_case='A-ORIGINAL' if phase == 'pre' else 'E-AFFECTED-REGRESSION',
                              **session_options) as session:
        await session.login(credentials.login, credentials.password,
                            **({'user_id': 5} if current or profile.message_id == MAIN_A_ORIGINAL_UI else {}))
        await session.switch_store(store_id)
        original = await session.download_original(invoice_id, original_id, original_sha256,
                                                    patient_id=patient_id, phase=phase)
    results = {'case_id': 'A-ORIGINAL' if phase == 'pre' else 'E-AFFECTED-REGRESSION', 'original': original,
               'evidence_kind': 'REAL_FIREFOX_UI_NATIVE' if current else 'REAL_FIREFOX_UI_UPSTREAM_FORWARDED',
               'redirect_policy': 'NATIVE_AUTOMATIC' if current else 'MANUAL_REDIRECT',
               'native_automatic_redirect_acceptance': current,
               'independent_verification': 'PENDING'}
    save_once(Path(directory) / (uuid.uuid4().hex + '.main-a-browser-results.json'), results)
    return results


@_safe_browser_entrypoint('browser.current_revoked_page')
async def run_current_revoked_browser(*, base_url, database, owned_targets, budget,
                                      directory, credentials, reader_id, store_id,
                                      patient_id, invoice_id, original_id,
                                      revoke_reader, restore_reader, **session_options):
    """Only new reader59's next real request from one already-open page.

    Both callbacks must use manager5's normal S01 action and independently
    verify the committed new-reader permission state before returning.
    This entry does not download the original while it is authorized.
    """
    profile = getattr(budget, 'profile', None)
    if (getattr(profile, 'message_id', None) != CURRENT_PLAN
            or (reader_id, store_id, patient_id, invoice_id, original_id) != (59, 1, 1, 1, 1)
            or not callable(revoke_reader) or not callable(restore_reader)):
        raise BrowserBoundaryError('CURRENT_REVOKED_PAGE_SCOPE_INVALID')
    profile.verify()
    profile.require_action('C-REVOKED-PAGE')
    async with BrowserSession(base_url, database=database, owned_targets=owned_targets,
                              budget=budget, directory=directory,
                              current_case='C-REVOKED-PAGE', **session_options) as session:
        await session.login(credentials.login, credentials.password, user_id=reader_id)
        await session.switch_store(store_id)
        observation = await session.revoked_old_page(invoice_id, original_id,
            patient_id=patient_id, revoke_callback=revoke_reader, restore_callback=restore_reader)
    result = {'case_id': 'C-REVOKED-PAGE', 'actor_id': reader_id,
              'evidence_kind': 'REAL_FIREFOX_UI_NATIVE', 'same_previously_open_page': True,
              'next_request': observation, 'independent_verification': 'PENDING'}
    save_once(Path(directory) / (uuid.uuid4().hex + '.current-revoked-browser-results.json'), result)
    return result

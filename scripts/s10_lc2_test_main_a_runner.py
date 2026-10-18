"""Offline regressions tied to actual access controller/service source.

These exercise the real extracted controller methods without importing Odoo or
opening a database. They are contract regressions, never application acceptance.
"""
import ast
from contextlib import nullcontext
from dataclasses import dataclass
import json
import inspect
from pathlib import Path
from types import SimpleNamespace
import unittest

import s10_lc2_main_a_runner as runner
import s10_lc2_main_a_browser_diag as browser_diag

ROOT = Path(__file__).resolve().parents[1]


class AccessError(Exception):
    pass


class UserError(Exception):
    pass


class ValidationError(Exception):
    pass


@dataclass(frozen=True)
class Binding:
    user_id: int
    session_id: int
    revision: int


class Response:
    def __init__(self, status, value=None, body=None):
        self.status = status
        self.value = value
        self.body = body if body is not None else json.dumps(value).encode()
        self.headers = {}

    def json(self):
        return self.value


def extracted(relative, class_name, method, namespace):
    tree = ast.parse((ROOT / relative).read_bytes())
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name)
    function = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == method)
    function.decorator_list = []
    module = ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[]))
    exec(compile(module, relative, 'exec'), namespace)
    return namespace[method]


class Session:
    def __init__(self, uid=7, store=0, revision=0):
        self.id = 500
        self.ydental_user_id = SimpleNamespace(id=uid)
        self.ydental_store_id = SimpleNamespace(id=store)
        self.ydental_revision = revision

    def sudo(self):
        return self

    def ensure_one(self):
        pass

    def exists(self):
        return self

    def write(self, values):
        self.ydental_revision = values['ydental_revision']
        self.ydental_store_id = SimpleNamespace(id=values['ydental_store_id'])

    def invalidate_recordset(self):
        pass


class Environment:
    def __init__(self, session):
        self.uid = 7
        self.context = {}
        self.session = session
        self.cr = SimpleNamespace(savepoint=nullcontext, execute=lambda *a: None)

    def _(self, message):
        return message

    def __getitem__(self, model):
        if model == 'ydental.access.session':
            return SimpleNamespace(sudo=lambda: SimpleNamespace(browse=lambda ident: self.session))
        if model == 'ydental.access.store':
            return SimpleNamespace(sudo=lambda: SimpleNamespace(browse=lambda ident:
                SimpleNamespace(exists=lambda: SimpleNamespace(id=ident, active=ident == 1))))
        raise AssertionError('unexpected model')


class AccessService:
    def __init__(self, session):
        self.env = Environment(session)
        self.session = session
        self.deny_membership = False
        self.audits = []

    def _require_internal(self):
        pass

    def with_context(self, **values):
        self.env.context.update(values)
        return self

    def _denial(self, operation):
        self.audits.append(operation)

    def _membership(self, uid, store):
        if self.deny_membership:
            return None
        return SimpleNamespace(ydental_employee_id=SimpleNamespace(active=True))

    def _audit(self, *args, **kwargs):
        self.audits.append(args[0])


service_namespace = {'AccessError': AccessError, 'UserError': UserError, 'Binding': Binding}
for method in ('_bind', '_scope', '_switch'):
    setattr(AccessService, method, extracted('ydental_access/models/ydental_access_service.py',
            'YDentalAccessService', method, service_namespace))


class AccessController:
    def __init__(self, service):
        self.service = service

    def _service(self, revision=None):
        return self.service._bind(self.service.session, revision)


def controller_for(service):
    request = SimpleNamespace(env=service.env, make_json_response=lambda value, status=200, headers=None:
                              Response(status, value))
    namespace = {'AccessError': AccessError, 'UserError': UserError,
                 'ValidationError': ValidationError, 'request': request, 'json': json}
    for method in ('_execute', 'action'):
        setattr(AccessController, method, extracted('ydental_access/controllers/access.py',
                'YDentalAccess', method, namespace))
    return AccessController(service)


class ContractClient:
    def __init__(self, *, store=0, switch_mode='normal', uid=7, metadata_uid=7,
                 metadata_store='Synthetic store 1', metadata_revision=None, refreshed_revision=None):
        self.service = AccessService(Session(uid=uid, store=store, revision=1 if store else 0))
        self.controller = controller_for(self.service)
        self.switch_mode = switch_mode
        self.metadata_uid = metadata_uid
        self.metadata_store = metadata_store
        self.metadata_revision = metadata_revision
        self.refreshed_revision = refreshed_revision
        self.dashboard_reads = 0
        self.clinical_calls = []

    def login(self, *args, **kwargs):
        return Response(303, {})

    def request(self, method, path, *, form=None, json_body=None, **kwargs):
        if method == 'GET' and path == '/ydental/access':
            self.dashboard_reads += 1
            revision = self.service.session.ydental_revision
            if self.dashboard_reads > 1 and self.refreshed_revision is not None:
                revision = self.refreshed_revision
            # Same hidden-field names as the actual QWeb dashboard and CSRF parser.
            return Response(200, body=('<input name="revision" value="%d">'
                '<input name="csrf_token" value="offline-not-a-real-csrf">' % revision).encode())
        if path == '/ydental/access/action':
            if self.switch_mode == 'denied':
                self.service.deny_membership = True
            revision = form['revision'] - 1 if self.switch_mode == 'stale' else form['revision']
            return self.controller.action('switch', revision, payload=form['payload'], output='json')
        if path == '/web/session/get_session_info':
            revision = self.service.session.ydental_revision if self.metadata_revision is None else self.metadata_revision
            return Response(200, {'jsonrpc': '2.0', 'id': 1, 'result': {
                'uid': self.metadata_uid, 'user_context': {'ydental_revision': revision},
                'ydental_store_name': self.metadata_store}})
        if path == '/ydental/clinical/action':
            payload = json.loads(form['payload'])
            self.clinical_calls.append((form['operation'], payload, form['connection'], form['revision']))
            if form['operation'] == 'acquire':
                return Response(200, {'result': 'accepted', 'document_id': 1, 'version': 4,
                    'state': 'confirmed', 'responsible_id': 7, 'editor_token': 'offline-not-a-real-token'})
            return Response(200, {'document_id': 1, 'result': 'accepted'})
        raise AssertionError('unexpected request')


GATE = {'identity_valid': True, 'clinical_user7_eligible': True,
        'no_other_valid_editor': True, 'store1_name': 'Synthetic store 1'}


class RunnerContractTests(unittest.TestCase):
    def test_debug_exit_parser_matches_real_playwright_producer_delimiter(self):
        producer = (browser_diag.PLAYWRIGHT_ROOT / 'playwright/driver/package/lib/coreBundle.js').read_text()
        self.assertIn('<process did exit: exitCode=${exitCode}, signal=${signal}>', producer)
        actual_format = '[pid=123] <process did exit: exitCode=0, signal=null>'
        self.assertEqual(browser_diag.parse_browser_debug(actual_format), [
            {'pid': 123, 'debug_exit_code': '0', 'debug_exit_signal': 'null'}])
        crashed = '[pid=123] <process did exit: exitCode=null, signal=SIGSEGV>'
        self.assertEqual(browser_diag.parse_browser_debug(crashed)[0]['debug_exit_signal'], 'SIGSEGV')

    def test_diagnostic_admission_requires_worker_and_actual_browser_clean_exit(self):
        outcome = {'returncode': 0, 'timed_out': False, 'native_crash': False}
        process = {'currently_exists': False, 'debug_exit_code': '0', 'debug_exit_signal': 'null'}
        self.assertTrue(browser_diag.diagnostic_admitted(True, outcome, [process]))
        for delta in ({'returncode': 1}, {'timed_out': True}, {'native_crash': True}):
            self.assertFalse(browser_diag.diagnostic_admitted(True, outcome | delta, [process]))
        for delta in ({'debug_exit_code': '1'}, {'debug_exit_code': 'UNKNOWN'},
                      {'debug_exit_signal': 'SIGSEGV'}, {'currently_exists': True}):
            self.assertFalse(browser_diag.diagnostic_admitted(True, outcome, [process | delta]))
        self.assertFalse(browser_diag.diagnostic_admitted(False, outcome, [process]))
        self.assertFalse(browser_diag.diagnostic_admitted(True, outcome, []))

    def execute(self, client, **gate_changes):
        events = []
        runner.run_editor(client, {'login': 'offline-fixture', 'password': 'offline-fixture'},
                          gate=GATE | gate_changes, emit=lambda name, value: events.append((name, value)))
        return events

    def test_actual_controller_normal_switch_has_only_revision_and_reaches_release(self):
        client = ContractClient()
        events = self.execute(client)
        self.assertEqual([x[0] for x in client.clinical_calls], ['acquire', 'release'])
        self.assertEqual(client.clinical_calls[1][1]['editor_token'], 'offline-not-a-real-token')
        self.assertEqual(client.clinical_calls[0][2], client.clinical_calls[1][2])
        self.assertEqual(client.clinical_calls[0][3], 1)
        self.assertEqual(events[-1][1]['status'], 'HTTP_ACQUIRE_RELEASE_RETURNED')
        self.assertNotIn('offline-not-a-real-token', json.dumps(events))

    def test_same_store_actual_switch_need_not_increment_revision(self):
        client = ContractClient(store=1)
        self.execute(client)
        self.assertEqual(client.clinical_calls[0][3], 1)

    def test_actual_controller_access_denied_403_stops_before_acquire(self):
        client = ContractClient(switch_mode='denied')
        with self.assertRaises(runner.ContractError):
            self.execute(client)
        self.assertEqual(client.clinical_calls, [])
        self.assertIn('action.denied', client.service.audits)

    def test_actual_bind_stale_maps_controller_409_and_stops_before_acquire(self):
        client = ContractClient(switch_mode='stale')
        with self.assertRaises(runner.ContractError):
            self.execute(client)
        self.assertEqual(client.clinical_calls, [])
        response = client.controller.action('switch', -1, payload='{"store_id":1}', output='json')
        self.assertEqual(response.status, 409)

    def test_actual_scope_rejects_revision_changed_after_binding(self):
        service = AccessService(Session(store=1, revision=1))
        service._bind(service.session, 1)
        service.session.ydental_revision = 2
        with self.assertRaises(UserError):
            service._scope(write=True)

    def test_actual_bind_rejects_user_mismatch(self):
        service = AccessService(Session(uid=8))
        with self.assertRaises(AccessError):
            service._bind(service.session, 0)

    def test_native_uid_store_or_revision_mismatch_never_acquires(self):
        for kwargs in ({'metadata_uid': 5}, {'metadata_store': 'Other store'}, {'metadata_revision': 99}):
            with self.subTest(kwargs=kwargs):
                client = ContractClient(**kwargs)
                with self.assertRaises(runner.ContractError):
                    self.execute(client)
                self.assertEqual(client.clinical_calls, [])

    def test_refreshed_revision_mismatch_never_acquires(self):
        client = ContractClient(refreshed_revision=99)
        with self.assertRaises(runner.ContractError):
            self.execute(client)
        self.assertEqual(client.clinical_calls, [])

    def test_actual_clinical_release_and_operate_supply_accepted_contract(self):
        class ClinicalService:
            def __init__(self):
                self.env = SimpleNamespace(cr=SimpleNamespace(savepoint=nullcontext))
                self.events = []

            def _held(self, document_id, editor_token):
                self.events.append('held')
                return SimpleNamespace(id=document_id)

            def _clear_editor(self, doc):
                self.events.append('clear')

            def _audit(self, event, doc):
                self.events.append(event)

            def _access(self, write=False):
                pass

            def _queue(self):
                return SimpleNamespace(_connection=lambda: None, _locks=lambda: None)

        for method in ('_open', '_acquire', '_heartbeat', '_save', '_confirm', '_correct', '_handover', '_transfer'):
            setattr(ClinicalService, method, lambda *args, **kwargs: {})
        namespace = {'ValidationError': ValidationError, 'inspect': inspect}
        for method in ('_release', '_operate'):
            setattr(ClinicalService, method, extracted('ydental_clinical/models/ydental_clinical_service.py',
                'YDentalClinicalService', method, namespace))
        service = ClinicalService()
        result = service._operate('release', {'document_id': 1, 'editor_token': 'offline-fixture'})
        self.assertEqual(result, {'document_id': 1, 'result': 'accepted'})
        self.assertEqual(service.events, ['held', 'clear', 'edit_release'])

    def test_boolean_or_old_result_shape_is_not_legal_switch_revision(self):
        for value in ({'revision': True}, {'revision': -1}, {'revision': 1, 'result': 'accepted'}):
            with self.assertRaises(runner.ContractError):
                runner.switch_revision(Response(200, value))

    def test_not_qualified_or_already_released_never_acquires(self):
        client = ContractClient()
        with self.assertRaises(runner.ContractError):
            self.execute(client, clinical_user7_eligible=False)
        self.assertEqual(client.clinical_calls, [])
        client = ContractClient()
        events = self.execute(client, editor_already_legally_released=True)
        self.assertEqual(client.clinical_calls, [])
        self.assertEqual(events[-1][1]['status'], 'ALREADY_RELEASED_VERIFIED_NO_REPEAT')


if __name__ == '__main__':
    unittest.main()

"""Pure source/fake tests for the restored report boundary, never actual PDF/ORM."""
import ast
from dataclasses import dataclass
import hashlib
import io
import inspect
import json
from pathlib import Path
from types import SimpleNamespace
import unittest


ROOT = Path(__file__).resolve().parents[1]


class UserError(Exception):
    pass


class AccessError(Exception):
    pass


def source_method(relative, model, method, **namespace):
    """Execute only an actual method AST with explicit stdlib/fake globals."""
    tree = ast.parse((ROOT / relative).read_text())
    owner = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == model)
    function = next(node for node in owner.body if isinstance(node, ast.FunctionDef) and node.name == method)
    scope = {'AccessError': AccessError, 'UserError': UserError, 'hashlib': hashlib, **namespace}
    exec(compile(ast.Module(body=[function], type_ignores=[]), relative, 'exec'), scope)
    return scope[method]


@dataclass(frozen=True)
class FakeSettlementPdfScope:
    actor_id: int
    session_id: int
    revision: int
    kind: str
    source_id: int
    digest: str


def observer_fixture(*, code=0, exception=None, result=None,
                     report_name='ydental_settlement.ydental_settlement_pdf'):
    """Actual observer methods, fake native core shape, and RAM-only event capture."""
    observed, events, primaries = {}, [], []
    service_tree = ast.parse((ROOT / 'ydental_settlement/models/ydental_settlement_service.py').read_text())
    scope_class = next(node for node in service_tree.body if isinstance(node, ast.ClassDef)
                       and node.name == 'SettlementPdfScope')
    scope_namespace = {'__name__': '_pure_actual_scope', 'dataclass': dataclass}
    exec(compile(ast.Module(body=[scope_class], type_ignores=[]), 'actual_scope_ast', 'exec'), scope_namespace)
    scope_type = scope_namespace['SettlementPdfScope']

    class EnvironmentFake:
        def __init__(self):
            self.context = {'ydental_settlement_pdf_scope': scope_type(7, 9, 10, 'bill', 44, 'synthetic')}
            self.validations = 0
            self.invalid = False

        def __getitem__(self, model):
            assert model == 'ydental.settlement.service'
            return self

        def _validate_pdf_scope(self):
            self.validations += 1
            if self.invalid:
                raise AccessError('synthetic-stale-bound-scope')
            return {'source_id': 44}

        def _(self, message):
            return message

    environment = EnvironmentFake()
    native_result = result if result is not None else SimpleNamespace(
        returncode=code, stdout='SENTINEL-private-stdout', stderr='SENTINEL-private-stderr')
    native_args = ['SENTINEL-native-command', 'SENTINEL-cookie-jar', 'SENTINEL-original-path']

    class NativeCoreFake:
        def __init__(self, env=environment, record_ids=()):
            self.env, self.ids = env, record_ids

        def __len__(self):
            return len(self.ids)

        @property
        def report_name(self):
            assert self.ids, 'native callers begin with an empty record set'
            return report_name

        @property
        def id(self):
            assert len(self.ids) == 1
            return self.ids[0]

        def _get_report(self, reference):
            observed['resolved_ref'] = reference
            return NativeCoreFake(env=object(), record_ids=(77,))

        def browse(self, record_id):
            return type(self)(self.env, (record_id,))

        def _run_pdf_engine_without_processing(self, engine_name, bodies, report_ref=False, **kwargs):
            observed['engine_call'] = (self, engine_name, bodies, report_ref, kwargs)
            return self._run_wkhtmltopdf(native_args)

        def _run_wkhtmltopdf(self, args):
            observed['native_call'] = (self.env, args)
            if exception is not None:
                raise exception
            return native_result

    def primary(error, component, stage, **kwargs):
        primaries.append((error, component, stage, kwargs))
        return 'synthetic-primary'

    namespace = {'__name__': '_pure_observer_ast', 'models': SimpleNamespace(Model=NativeCoreFake),
                 'AccessError': AccessError, 'SettlementPdfScope': scope_type,
                 'emit_event': lambda event, **fields: events.append({'event': event, **fields}),
                 'record_exception': primary}
    tree = ast.parse((ROOT / 'ydental_settlement/models/ir_actions_report.py').read_text())
    tree.body = [node for node in tree.body if not isinstance(node, (ast.Import, ast.ImportFrom))]
    exec(compile(tree, 'actual_observer_ast', 'exec'), namespace)
    return SimpleNamespace(report=namespace['IrActionsReport'](), env=environment, scope_type=scope_type,
                           observed=observed, events=events, primaries=primaries,
                           native_result=native_result, native_args=native_args)


class ReportBoundaryCase(unittest.TestCase):
    def test_native_report_handoff_preserves_scope_payload_and_audit(self):
        # The actual service still hands bytes to/from the existing native report API.
        observed = {}
        content = b'%PDF-synthetic-bytes-not-an-actual-render'

        class NativeReportFake:
            def with_context(self, **context):
                observed['context'] = context
                return self

            def _render_qweb_pdf(self, report_name, docids):
                observed['native_call'] = (report_name, docids)
                return content, 'pdf'

        class EnvironmentFake:
            uid = 7
            def __getitem__(self, model):
                if model == 'ir.actions.report':
                    return NativeReportFake()
                assert model == 'ydental.access.service'
                return SimpleNamespace(_scope=lambda: SimpleNamespace(id=9, ydental_revision=10))

        payload = {'source_id': 44, 'amount': 6}
        target, store = object(), object()
        service = SimpleNamespace(env=EnvironmentFake(),
            _report_payload=lambda kind, source_id: (target, payload), _access=lambda: store,
            _audit=lambda *args, **kwargs: observed.update(audit=(args, kwargs)))
        method = source_method('ydental_settlement/models/ydental_settlement_service.py',
            'YDentalSettlementService', '_pdf', SettlementPdfScope=FakeSettlementPdfScope,
            json=json, io=io, PdfFileReader=lambda value: SimpleNamespace(pages=[object()]),
            QWebError=type('FakeQWebError', (Exception,), {}),
            PdfReadError=type('FakePdfReadError', (Exception,), {}))
        self.assertEqual(method(service, 'bill', 44), (content, hashlib.sha256(content).hexdigest()))
        self.assertEqual(observed['native_call'], ('ydental_settlement.ydental_settlement_pdf', [44]))
        scope = observed['context']['ydental_settlement_pdf_scope']
        self.assertEqual((scope.actor_id, scope.session_id, scope.revision, scope.kind, scope.source_id),
                         (7, 9, 10, 'bill', 44))
        self.assertEqual(scope.digest, hashlib.sha256(json.dumps(payload, sort_keys=True,
                                                               ensure_ascii=True).encode()).hexdigest())
        self.assertEqual(observed['context']['lang'], 'zh_CN')
        self.assertTrue(observed['context']['force_report_rendering'])
        self.assertTrue(observed['context']['report_pdf_no_attachment'])
        self.assertEqual(observed['audit'][0], ('report_download', target, store))

    def test_empty_native_record_set_binds_actual_report_in_original_environment(self):
        fixture = observer_fixture()
        bodies, header, footer, specific = object(), object(), object(), object()
        kwargs = {'header': header, 'footer': footer, 'specific_paperformat_args': specific,
                  'landscape': True, 'existing_option': object()}
        before = kwargs.copy()
        result = fixture.report._run_pdf_engine_without_processing('wkhtmltopdf', bodies,
            'ydental_settlement.ydental_settlement_pdf', **kwargs)
        self.assertIs(result, fixture.native_result)
        bound, engine, seen_bodies, reference, seen_kwargs = fixture.observed['engine_call']
        self.assertEqual(bound.ids, (77,))
        self.assertIs(bound.env, fixture.env)
        self.assertIs(fixture.observed['native_call'][0], fixture.env)
        self.assertIs(fixture.observed['native_call'][1], fixture.native_args)
        self.assertIs(seen_bodies, bodies)
        self.assertEqual(seen_kwargs, before)
        self.assertTrue(all(seen_kwargs[key] is value for key, value in kwargs.items()))
        self.assertEqual(kwargs, before)
        self.assertEqual(fixture.observed['resolved_ref'], reference)
        self.assertEqual(fixture.events[-1]['outcome'], 'EXITED')
        self.assertNotIn('renderer_pid', fixture.events[-1])
        self.assertEqual(fixture.env.validations, 2)

    def test_native_signal_positive_code_and_unknown_result_are_observed_without_rewrite(self):
        for code, outcome, signal, exit_code in [(-11, 'NATIVE_CRASH', 11, None),
                (1, 'NONZERO_NOT_NATIVE', None, 1), (None, 'UNKNOWN', None, None)]:
            fixture = observer_fixture(code=code)
            result = fixture.report._run_pdf_engine_without_processing(
                'wkhtmltopdf', object(), 'ydental_settlement.ydental_settlement_pdf')
            self.assertIs(result, fixture.native_result)
            event = fixture.events[-1]
            self.assertEqual((event['event'], event['outcome'], event['renderer_signal'],
                              event['renderer_exit_code']), ('renderer.exit', outcome, signal, exit_code))
            self.assertNotIn('renderer_pid', event)
            self.assertNotIn('SENTINEL', json.dumps(fixture.events))
            self.assertEqual(event['commit_observation'], 'NOT_OBSERVED')

    def test_native_exception_identity_arguments_and_cause_survive_observation(self):
        original = OSError('SENTINEL-private-engine-error')
        cause = LookupError('SENTINEL-private-cause')
        original.__cause__ = cause
        before = (type(original), original.args, original.__cause__, original.__context__,
                  original.__suppress_context__)
        fixture = observer_fixture(exception=original)
        try:
            fixture.report._run_pdf_engine_without_processing(
                'wkhtmltopdf', object(), 'ydental_settlement.ydental_settlement_pdf')
        except OSError as observed:
            self.assertIs(observed, original)
        else:
            self.fail('native exception was swallowed')
        self.assertEqual((type(original), original.args, original.__cause__, original.__context__,
                          original.__suppress_context__), before)
        self.assertIs(fixture.primaries[0][0], original)
        self.assertEqual(fixture.primaries[0][3], {'investigate': True})
        self.assertEqual(fixture.events[-1]['event'], 'renderer.error')
        self.assertEqual(fixture.events[-1]['root_event_id'], 'synthetic-primary')
        self.assertEqual(fixture.events[-1]['outcome'], 'UNKNOWN')
        self.assertNotIn('SENTINEL', json.dumps(fixture.events))

    def test_returncode_property_error_preserves_structural_primary_and_original_result(self):
        original = RuntimeError('SENTINEL-private-observation-error')
        original.__cause__ = LookupError('SENTINEL-private-observation-cause')
        before = (type(original), original.args, original.__cause__, original.__context__,
                  original.__suppress_context__, original.__dict__.copy())

        class NativeResultWithBrokenObservation:
            @property
            def returncode(self):
                raise original

        native_result = NativeResultWithBrokenObservation()
        fixture = observer_fixture(result=native_result)
        returned = fixture.report._run_pdf_engine_without_processing(
            'wkhtmltopdf', object(), 'ydental_settlement.ydental_settlement_pdf')
        self.assertIs(returned, native_result)
        self.assertIs(fixture.primaries[0][0], original)
        self.assertEqual(fixture.primaries[0][1:], ('ydental_settlement.report',
                         'evidence.renderer', {'investigate': True}))
        self.assertEqual((type(original), original.args, original.__cause__, original.__context__,
                          original.__suppress_context__, original.__dict__), before)
        event = fixture.events[-1]
        self.assertEqual((event['event'], event['outcome'], event['root_event_id']),
                         ('renderer.exit', 'UNKNOWN', 'synthetic-primary'))
        self.assertIsNone(event['renderer_exit_code'])
        self.assertIsNone(event['renderer_signal'])
        self.assertNotIn('renderer_pid', event)
        self.assertNotIn('SENTINEL', json.dumps(fixture.events))

    def test_unrelated_report_or_engine_remains_native_without_settlement_observation(self):
        for engine, report_name in [('wkhtmltopdf', 'other.report'),
                                    ('other-engine', 'ydental_settlement.ydental_settlement_pdf')]:
            fixture = observer_fixture(report_name=report_name)
            result = fixture.report._run_pdf_engine_without_processing(engine, object(), report_name)
            self.assertIs(result, fixture.native_result)
            self.assertEqual(fixture.events, [])
            self.assertEqual(fixture.env.validations, 0)
            self.assertEqual(fixture.observed['engine_call'][0].ids, ())

    def test_exact_scope_type_and_existing_scope_validation_reject_before_native_dispatch(self):
        for kind in ('wrong-type', 'subclass', 'stale'):
            fixture = observer_fixture()
            if kind == 'wrong-type':
                fixture.env.context['ydental_settlement_pdf_scope'] = object()
            elif kind == 'subclass':
                class SubScope(fixture.scope_type):
                    pass
                fixture.env.context['ydental_settlement_pdf_scope'] = SubScope(7, 9, 10, 'bill', 44, 'synthetic')
            else:
                fixture.env.invalid = True
            with self.assertRaises(AccessError):
                fixture.report._run_pdf_engine_without_processing(
                    'wkhtmltopdf', object(), 'ydental_settlement.ydental_settlement_pdf')
            self.assertNotIn('native_call', fixture.observed)
            self.assertEqual(fixture.events, [])

    def test_observer_keeps_native_argument_contract_and_has_no_render_replacement_hooks(self):
        fixture = observer_fixture()
        parameters = inspect.signature(type(fixture.report)._run_pdf_engine_without_processing).parameters
        self.assertEqual(list(parameters)[:4], ['self', 'engine_name', 'bodies', 'report_ref'])
        self.assertEqual(parameters['kwargs'].kind, inspect.Parameter.VAR_KEYWORD)
        tree = ast.parse((ROOT / 'ydental_settlement/models/ir_actions_report.py').read_text())
        owner = next(node for node in tree.body if isinstance(node, ast.ClassDef))
        methods = {node.name for node in owner.body if isinstance(node, ast.FunctionDef)}
        self.assertFalse(methods & {'_get_layout', '_prepare_wkhtmltopdf_html', '_build_wkhtmltopdf_args'})
        self.assertFalse(any(isinstance(node, ast.Import) and any(alias.name in {
            'subprocess', 'tempfile', 'shutil'} for alias in node.names) for node in ast.walk(tree)))

    def test_report_values_validate_scope_then_reject_arbitrary_documents_or_debug(self):
        method = source_method('ydental_settlement/models/report_ydental_settlement_pdf.py',
                               'YDentalSettlementPdf', '_get_report_values')
        calls = []
        payload = {'source_id': 44}

        class EnvironmentFake:
            def __getitem__(self, model):
                assert model == 'ydental.settlement.service'
                return SimpleNamespace(_validate_pdf_scope=lambda: calls.append('validated') or payload)

            def _(self, message):
                return message

        report = SimpleNamespace(env=EnvironmentFake())
        accepted = method(report, [44], {'report_type': 'pdf', 'debug': False})
        self.assertIs(accepted['p'], payload)
        for docids, data in [([45], None), ([44], {'debug': True}), ([44], {'arbitrary': 1})]:
            before = len(calls)
            with self.assertRaises(AccessError):
                method(report, docids, data)
            self.assertEqual(len(calls), before + 1)

    def original_fixture(self, corrupt=False):
        calls = []
        stored = b'%PDF-synthetic-old-v1-unchanged'
        company, invoice = object(), object()
        store, patient = SimpleNamespace(company_id=company), SimpleNamespace(id=8)
        original = SimpleNamespace(id=12, _name='ydental.settlement.bill.original', version=1,
            store_id=store, company_id=company, patient_id=patient,
            invoice_id=SimpleNamespace(id=44),
            pdf_sha256='0' * 64 if corrupt else hashlib.sha256(stored).hexdigest())
        original.attachment_id = SimpleNamespace(res_model=original._name, res_id=12,
            company_id=company, public=False, access_token=False,
            raw=SimpleNamespace(content=stored))
        original.exists = lambda: original

        class EnvironmentFake:
            def __getitem__(self, model):
                assert model == 'ydental.access.service'
                return SimpleNamespace(_check=lambda *args: calls.append(('access', args)))

            def _(self, message):
                return message

        def forbidden_render(*args, **kwargs):
            self.fail('old original download attempted a new render')

        service = SimpleNamespace(env=EnvironmentFake(), _access=lambda: calls.append('scope'),
            _positive_id=lambda value: value,
            _model=lambda model: SimpleNamespace(browse=lambda record_id: original),
            _original_invoice=lambda invoice_id: (invoice, [], patient, store),
            _patient_family_ids=lambda value: [patient.id], _pdf=forbidden_render,
            _audit=lambda *args, **kwargs: calls.append(('audit', args, kwargs)))
        method = source_method('ydental_settlement/models/ydental_settlement_original_service.py',
                               'YDentalSettlementOriginalService', '_bill_original_bytes')
        return method, service, original, stored, calls

    def test_old_original_returns_exact_stored_bytes_without_render(self):
        method, service, original, stored, calls = self.original_fixture()
        before = (original.version, original.pdf_sha256, original.attachment_id.raw.content)
        self.assertEqual(method(service, original.id), (stored, hashlib.sha256(stored).hexdigest()))
        self.assertEqual((original.version, original.pdf_sha256, original.attachment_id.raw.content), before)
        self.assertEqual(calls[-1][0:2], ('audit', ('bill_original_download',
                         service._original_invoice(44)[0], original.store_id)))

    def test_corrupt_old_original_is_denied_without_regeneration_or_success_audit(self):
        method, service, original, stored, calls = self.original_fixture(corrupt=True)
        with self.assertRaises(UserError):
            method(service, original.id)
        self.assertEqual(original.attachment_id.raw.content, stored)
        self.assertFalse(any(isinstance(call, tuple) and call[0] == 'audit' for call in calls))


if __name__ == '__main__':
    unittest.main(verbosity=2)

"""Pure stage-boundary checks; no DB, service, authentication or business action."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import admission_probe
import launcher
import protected_snapshot
import http_client
import runtime_config


class RuntimeBoundaryTests(unittest.TestCase):
    def test_stage_keeps_original_target_and_filestore(self):
        self.assertEqual(admission_probe.PLAN, 'YD-S13-DL-P8')
        self.assertEqual(admission_probe.BRANCH, 'codex/s13-dl-p8-documents-actions-icons-r1')
        self.assertEqual(admission_probe.TARGET, launcher.EXPECTED_DATABASE)
        self.assertEqual(launcher.DATA_DIR, admission_probe.ROOT / '.local/s11/new-target-data')
        self.assertEqual(launcher.PRIVATE_ROOT, admission_probe.ROOT / '.local/dl-p8')
        self.assertEqual(launcher.RUNTIME_CONFIG, launcher.PRIVATE_ROOT / 'runtime.json')
        self.assertEqual(launcher.SCRIPT_PATH, Path(launcher.__file__).resolve())

    def test_old_stage_owner_prevents_new_runtime_admission(self):
        with patch.object(launcher, '_validate', return_value=(None, {}, None, None, None)):
            with patch.object(Path, 'exists', return_value=True):
                with self.assertRaisesRegex(launcher.Refusal, 'S12/S13 owner'):
                    launcher.validate_pair()

    def test_reused_pdf_adapter_requires_exact_source_binding(self):
        with patch.object(launcher, '_validate', return_value=(None, {}, None, None, None)):
            with patch.object(Path, 'exists', return_value=False):
                with self.assertRaisesRegex(launcher.Refusal, 'PDF environment adapter'):
                    launcher.validate_pair()

    def test_only_current_document_module_may_load(self):
        self.assertEqual(protected_snapshot.ALLOWED_MODULES, {'ydental_print'})

    def test_prior_p5_p6_p7_owners_each_prevent_p8_runtime(self):
        for stage in ('p5', 'p6', 'p7'):
            with self.subTest(stage=stage):
                with patch.object(launcher, '_validate', return_value=(None, {}, None, None, None)):
                    with patch.object(Path, 'exists', lambda p: str(p).endswith('.local/dl-' + stage + '/active.json')):
                        with self.assertRaisesRegex(launcher.Refusal, 'S12/S13 owner'):
                            launcher.validate_pair()

    def test_candidate_descends_from_final_p7_report(self):
        self.assertEqual(runtime_config.ANCHOR,
                         '9f5ce4626895cb8f3da0562d9170e79220728378')

    def test_stock_and_scan_posts_refused_before_network(self):
        actor = object.__new__(http_client.HttpActor)
        for path in ('/ydental/inventory/action', '/ydental/inventory/scan',
                     '/ydental/access/action', '/ydental/documents/action'):
            with self.subTest(path=path):
                with self.assertRaisesRegex(RuntimeError, 'business writes are prohibited'):
                    actor.request('POST', path)

    def test_document_write_operations_refused_before_network(self):
        actor = object.__new__(http_client.HttpActor)
        for operation in ('generate', 'print_request', 'template_create', 'template_review', 'export'):
            with self.subTest(operation=operation):
                with self.assertRaisesRegex(RuntimeError, 'business writes are prohibited'):
                    actor.request('POST', '/ydental/documents/action',
                                  record_operation=operation, data={'operation': operation})

    def test_document_read_operation_must_match_actual_form_body(self):
        actor = object.__new__(http_client.HttpActor)
        for operation in ('preview', 'pdf_view', 'download'):
            with self.subTest(operation=operation):
                for body in ({'operation': 'generate'}, None):
                    with self.assertRaisesRegex(RuntimeError, 'business writes are prohibited'):
                        actor.request('POST', '/ydental/documents/action',
                                      record_operation=operation, data=body)

    def test_document_read_operations_reach_only_memory_session(self):
        for operation in ('preview', 'pdf_view', 'download'):
            with self.subTest(operation=operation):
                actor = object.__new__(http_client.HttpActor)
                actor.alias = 'PURE_MEMORY_NO_LOGIN'
                actor.directory = Path('/not-created-pure-memory')
                actor.events = []
                response = Mock(status_code=200, headers={}, is_redirect=False)
                actor.session = Mock()
                actor.session.request.return_value = response
                body = {'operation': operation}
                with patch.object(http_client, 'write_receipt', return_value='PURE'):
                    self.assertIs(actor.request('POST', '/ydental/documents/action',
                                               record_operation=operation, data=body), response)
                actor.session.request.assert_called_once_with(
                    'POST', http_client.BASE + '/ydental/documents/action',
                    timeout=60, allow_redirects=False, data=body)
                self.assertEqual(actor.events[0]['operation'], operation)
                self.assertFalse(actor.events[0]['request_body_or_credentials_recorded'])

    def test_sensitive_column_names_excluded_before_projection(self):
        for name in ('password','access_token','totp_secret','api_key','session_id','editor_hash','lease_hash','database_credential'):
            self.assertIsNotNone(protected_snapshot.DROP.search(name), name)
        for name in ('amount_residual','ydental_state','ydental_patient_id','write_date'):
            self.assertIsNone(protected_snapshot.DROP.search(name), name)

    def test_document_only_delta_cannot_hide_product(self):
        self.assertTrue(launcher.candidate_delta_is_documentation_only(['CURRENT_TASK.md','docs/reports/s13-dl-p8/summary.md']))
        self.assertFalse(launcher.candidate_delta_is_documentation_only(['docs/reports/s13-dl-p8/summary.md','ydental_reporting/controllers/reporting.py']))
        self.assertFalse(launcher.candidate_delta_is_documentation_only(['scripts/s13_dl_p8/run_checks.py']))

    def test_scope_plan_cannot_enable_clock(self):
        with patch.dict('os.environ', {'YDENTAL_S11_CLOCK_TEST':'1'}):
            with self.assertRaises(launcher.Refusal):
                launcher.no_legacy_clock(None,None,False)

    def test_evidence_writer_refuses_outside_private_stage(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(RuntimeError, 'private record directory'):
                admission_probe.write_receipt(Path(directory)/'data.json', {'status':'PURE'})


if __name__=='__main__':
    unittest.main()

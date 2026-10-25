"""Pure stage-boundary checks; no DB, service, authentication or business action."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import admission_probe
import launcher
import protected_snapshot


class RuntimeBoundaryTests(unittest.TestCase):
    def test_stage_keeps_original_target_and_filestore(self):
        self.assertEqual(admission_probe.PLAN, 'YD-S13-DL-P6')
        self.assertEqual(admission_probe.BRANCH, 'codex/s13-dl-p6-inventory-lookup-r1')
        self.assertEqual(admission_probe.TARGET, launcher.EXPECTED_DATABASE)
        self.assertEqual(launcher.DATA_DIR, admission_probe.ROOT / '.local/s11/new-target-data')
        self.assertEqual(launcher.PRIVATE_ROOT, admission_probe.ROOT / '.local/dl-p6')
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

    def test_only_current_inventory_module_may_load(self):
        self.assertEqual(protected_snapshot.ALLOWED_MODULES, {'ydental_inventory'})

    def test_p5_owner_alone_prevents_p6_runtime(self):
        with patch.object(launcher, '_validate', return_value=(None, {}, None, None, None)):
            with patch.object(Path, 'exists', lambda p: str(p).endswith('.local/dl-p5/active.json')):
                with self.assertRaisesRegex(launcher.Refusal, 'S12/S13 owner'):
                    launcher.validate_pair()

    def test_sensitive_column_names_excluded_before_projection(self):
        for name in ('password','access_token','totp_secret','api_key','session_id','editor_hash','lease_hash','database_credential'):
            self.assertIsNotNone(protected_snapshot.DROP.search(name), name)
        for name in ('amount_residual','ydental_state','ydental_patient_id','write_date'):
            self.assertIsNone(protected_snapshot.DROP.search(name), name)

    def test_document_only_delta_cannot_hide_product(self):
        self.assertTrue(launcher.candidate_delta_is_documentation_only(['CURRENT_TASK.md','docs/reports/s13-dl-p6/summary.md']))
        self.assertFalse(launcher.candidate_delta_is_documentation_only(['docs/reports/s13-dl-p6/summary.md','ydental_reporting/controllers/reporting.py']))
        self.assertFalse(launcher.candidate_delta_is_documentation_only(['scripts/s13_dl_p6/run_checks.py']))

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

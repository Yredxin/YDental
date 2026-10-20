"""SOURCE/PURE checks for the one-shot S11 lab fixture gate."""

import json
import tempfile
import unittest
from pathlib import Path

import prepare_lab_race_fixture as fixture


class TestPrepareLabRaceFixture(unittest.TestCase):
    def test_explicit_synthetic_marker_requires_stage_and_test_markers(self):
        self.assertTrue(fixture.is_explicit_synthetic_source(
            "S11 Synthetic Patient", "S11-treatment-42", "Synthetic fixture treatment"))
        self.assertTrue(fixture.is_explicit_synthetic_source(
            "S11 Test Patient", "event-S11-42", "Fixture treatment"))
        for patient_name, source, reason in (
            ("Synthetic Patient", "S11-treatment-42", "Synthetic fixture treatment"),
            ("S11 Patient", "S11-treatment-42", "Synthetic fixture treatment"),
            ("S11 Synthetic Patient", "treatment-42", "Synthetic fixture treatment"),
            ("S11 Synthetic Patient", "S11-treatment-42", "Routine clinical treatment"),
            ("S11 Contest Patient", "S11-treatment-42", "Synthetic fixture treatment"),
            ("S11 Latest Patient", "S11-treatment-42", "Synthetic fixture treatment"),
            ("S11 Synthetic Patient", "AS11-treatment-42", "Synthetic fixture treatment"),
            ("S11 Synthetic Patient", "S110-treatment-42", "Synthetic fixture treatment"),
            ("S11 Synthetic Patient", "S11-treatment-42", "Latest clinical visit"),
            ("S11 Synthetic Patient", "S11-treatment-42", "Contest clinical event"),
        ):
            with self.subTest(patient_name=patient_name, source=source, reason=reason):
                self.assertFalse(fixture.is_explicit_synthetic_source(patient_name, source, reason))

    def test_source_lock_identity_is_per_event(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.assertEqual(fixture.source_lock_path(187, root).name, "lab-race-fixture-source-187.lock")
            self.assertNotEqual(fixture.source_lock_path(187, root), fixture.source_lock_path(188, root))
            self.assertEqual(fixture.source_receipt_pattern(188), "*-source-188-lab-race-fixture.json")
            for invalid in (0, -1, True, "188"):
                with self.subTest(invalid=invalid), self.assertRaises(fixture.common.Refusal):
                    fixture.source_lock_path(invalid, root)

    def test_source_lock_is_exclusive_and_cannot_be_replayed(self):
        with tempfile.TemporaryDirectory() as temp:
            lock = fixture.source_lock_path(188, Path(temp))
            fixture.take_one_shot_lock(lock, "a" * 40, "NONCE", 188)
            self.assertTrue(lock.is_file())
            self.assertEqual(json.loads(lock.read_text())['source_event_id'], 188)
            with self.assertRaises(FileExistsError):
                fixture.take_one_shot_lock(lock, "b" * 40, "OTHER", 188)

    def test_prior_receipt_blocks_only_its_source_and_legacy_event187(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            legacy = root / "20261019T111759Z-lab-race-fixture.json"
            legacy.write_text(json.dumps({"intent": {"source_event_id": 187}}))
            self.assertTrue(fixture.has_prior_source_receipt(187, root))
            self.assertFalse(fixture.has_prior_source_receipt(188, root))

            source_receipt = root / "20261020T000000Z-source-188-lab-race-fixture.json"
            source_receipt.write_text(json.dumps({"source_event_id": 188}))
            self.assertTrue(fixture.has_prior_source_receipt(188, root))
            self.assertFalse(fixture.has_prior_source_receipt(189, root))
            self.assertTrue(fixture.legacy_lock_blocks_source(187))
            self.assertFalse(fixture.legacy_lock_blocks_source(188))

    def test_unattributable_legacy_receipt_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "broken-lab-race-fixture.json").write_text("not json")
            with self.assertRaises(fixture.common.Refusal):
                fixture.has_prior_source_receipt(188, root)


if __name__ == "__main__":
    unittest.main()

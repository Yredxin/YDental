"""Pure preflight and result-contract tests for the S11 race harness."""

import argparse
import json
import os
from pathlib import Path
import stat
import tempfile
from types import SimpleNamespace
import unittest

import race_package_code as runner


class TestRacePackageCode(unittest.TestCase):
    def _args(self, **changes):
        values = {
            "candidate": "a" * 40,
            "actor_id": 21,
            "store_id": 34,
            "order_a": 55,
            "order_b": 56,
            "confirm": runner.CONFIRMATION,
        }
        values.update(changes)
        return argparse.Namespace(**values)

    def test_exact_synthetic_opt_in_and_distinct_order_ids_are_required(self):
        runner.validate_cli(self._args())
        for args in (
            self._args(confirm=""),
            self._args(candidate="short"),
            self._args(order_b=55),
            self._args(actor_id=0),
        ):
            with self.subTest(args=args), self.assertRaises(runner.Refusal):
                runner.validate_cli(args)

    def test_current_and_original_synthetic_internal_code_prefixes_are_explicit(self):
        for value in ("S11-RACE-ABC", "S11V12-8d8207d00fdaf5a4a0c8"):
            with self.subTest(value=value):
                self.assertTrue(runner.is_synthetic_internal_code(value))
        for value in (None, False, "", "S11", "S11V12", "S110-ABC", "AS11V12-ABC", "REAL-ABC"):
            with self.subTest(value=value):
                self.assertFalse(runner.is_synthetic_internal_code(value))

    def test_race_result_requires_two_connections_unique_winner_and_unchanged_ledgers(self):
        race = {
            "two_distinct_postgresql_backends": True,
            "expected_outcome_pair": True,
            "exactly_one_action_accepted": True,
        }
        readback = {
            "stock_facts_unchanged": True,
            "stock_quantities_unchanged": True,
            "supplier_cost_sources_unchanged": True,
            "order_snapshot": {"orders": [{"id": 55}, {"id": 56}]},
        }
        self.assertTrue(runner.race_outcome_matches(race, readback))
        self.assertFalse(runner.race_outcome_matches(race | {
            "two_distinct_postgresql_backends": False,
        }, readback))
        self.assertFalse(runner.race_outcome_matches(race, readback | {
            "stock_facts_unchanged": False,
        }))

    def test_actor_must_have_both_medical_and_warehouse_write(self):
        self.assertTrue(runner.actor_has_required_grants({"medical": "write", "warehouse": "write"}))
        for levels in (
            {"medical": "read", "warehouse": "write"},
            {"medical": None, "warehouse": "write"},
            {"medical": "write", "warehouse": "read"},
            {},
        ):
            with self.subTest(levels=levels):
                self.assertFalse(runner.actor_has_required_grants(levels))

    def test_distinct_patients_keep_each_orders_own_confirmed_source(self):
        store = SimpleNamespace(id=34)
        patients = [SimpleNamespace(id=71), SimpleNamespace(id=72)]
        sources = [SimpleNamespace(id=81+i, state="confirmed", ydental_kind="treatment",
                                   ydental_store_id=store, ydental_patient_id=patient)
                   for i, patient in enumerate(patients)]
        orders = [SimpleNamespace(ydental_store_id=store, ydental_patient_id=patient,
                                  ydental_source_event_id=source)
                  for patient, source in zip(patients, sources, strict=True)]
        runner.validate_order_sources(orders, store.id)
        for field, invalid in (
            ("ydental_patient_id", patients[0]),
            ("ydental_patient_id", SimpleNamespace(id=False)),
            ("ydental_store_id", SimpleNamespace(id=35)),
            ("state", "draft"),
            ("ydental_kind", "examination"),
            ("id", False),
        ):
            source = sources[1]
            before = getattr(source, field)
            setattr(source, field, invalid)
            try:
                with self.subTest(field=field, invalid=invalid), self.assertRaises(runner.Refusal):
                    runner.validate_order_sources(orders, store.id)
            finally:
                setattr(source, field, before)
        orders[1].ydental_patient_id = SimpleNamespace(id=False)
        with self.assertRaises(runner.Refusal):
            runner.validate_order_sources(orders, store.id)

    def test_receipt_writer_uses_private_atomic_json(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "nested" / "race.json"
            runner.write_receipt(path, {"phase": "READ_ONLY_PREFLIGHT", "orders": [55, 56]})
            self.assertEqual(json.loads(path.read_text()), {
                "phase": "READ_ONLY_PREFLIGHT", "orders": [55, 56],
            })
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(path.parent.stat().st_mode), 0o700)
            self.assertFalse(any(item.name.endswith(".tmp") for item in path.parent.iterdir()))


if __name__ == "__main__":
    unittest.main()

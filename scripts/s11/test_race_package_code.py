"""Pure preflight and result-contract tests for the S11 race harness."""

import argparse
import json
import os
from pathlib import Path
import stat
import tempfile
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

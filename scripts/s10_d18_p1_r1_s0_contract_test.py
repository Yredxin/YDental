"""Offline synthetic tests; all outcomes are SIMULATED, never Odoo results."""

import copy
import unittest

from s10_d18_p1_r1_s0_contract import (
    SimulatedPolicy,
    assess_simulated,
    require_future_authorization,
)


AVATAR_SHA = "1eb9b55f2eb2b4ec77289bd0e54a4d762071cf0787791edb431b2b222a21b648"
EMPTY_SHA = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
POLICY = SimulatedPolicy(bus_type="mail.record/insert", expected_svg_sha256=AVATAR_SHA)


def example():
    counts = {
        "mail_mail": 0,
        "bus_bus": 6,
        "account_payment": 0,
        "account_partial_reconcile": 0,
    }
    before = {"counts": counts.copy()}
    during = {
        "counts": counts.copy(),
        "source_action": "after_settings_user_create",
        "cross_company_target": False,
        "global_group_changed": False,
        "new_message_models": ["res.partner", "res.users"],
        "bus_intents": [{
            "type": "mail.record/insert",
            "target_model": "res.users",
            "target_role": "settings_actor",
        }],
        "files": [
            {"kind": "avatar_svg", "sha256": AVATAR_SHA, "exact_core_template": True,
             "content_addressed_path": True, "attachment_refs_after_rollback": 0},
            {"kind": "gc_checklist", "sha256": EMPTY_SHA, "for_avatar": True,
             "attachment_refs_after_rollback": 0},
        ],
    }
    return before, during, {"counts": counts.copy()}


class ContractTests(unittest.TestCase):
    def check(self, expected, change=None, *, source_proven=True):
        before, during, rollback = example()
        if change:
            change(before, during, rollback)
        self.assertEqual(
            assess_simulated(before, during, rollback, policy=POLICY, source_proven=source_proven),
            expected,
        )

    def test_gate_closed(self):
        with self.assertRaises(PermissionError):
            require_future_authorization()

    def test_exact_simulated_case(self):
        self.check("SIMULATED_SYNTHETIC_ALLOWED")

    def test_real_redacted_type_is_not_captured(self):
        self.check("NOT_CAPTURED", lambda b, d, r: d["bus_intents"][0].update(type="other"))

    def test_unknown_type_stops(self):
        self.check("STOP_INTENT_SCOPE_OR_TYPE", lambda b, d, r: d["bus_intents"][0].update(type="unknown.event"))

    def test_other_target_stops(self):
        self.check("STOP_INTENT_SCOPE_OR_TYPE", lambda b, d, r: d["bus_intents"][0].update(target_role="other_company"))

    def test_unproven_source_stops(self):
        self.check("STOP_SOURCE_UNPROVEN", source_proven=False)

    def test_wrong_action_stops(self):
        self.check("STOP_SOURCE_ACTION", lambda b, d, r: d.update(source_action="warehouse_setup"))

    def test_multiple_intents_stop(self):
        self.check("STOP_INTENT_COUNT", lambda b, d, r: d["bus_intents"].append(copy.deepcopy(d["bus_intents"][0])))

    def test_cross_company_or_group_stops(self):
        self.check("STOP_CROSS_COMPANY_OR_GROUP", lambda b, d, r: d.update(cross_company_target=True))
        self.check("STOP_CROSS_COMPANY_OR_GROUP", lambda b, d, r: d.update(global_group_changed=True))

    def test_mail_and_finance_components_stop_individually(self):
        for field in ("mail_mail", "bus_bus", "account_payment", "account_partial_reconcile"):
            with self.subTest(field=field):
                self.check("STOP_COMPONENT_" + field.upper(),
                           lambda b, d, r, field=field: d["counts"].update({field: d["counts"][field] + 1}))

    def test_internal_message_sources_bound(self):
        self.check("STOP_MESSAGE_SOURCE", lambda b, d, r: d.update(new_message_models=["res.users", "mail.mail"]))

    def test_rollback_does_not_erase_transaction_anomaly(self):
        def change(before, during, rollback):
            during["counts"]["account_payment"] += 1
            # The separate after-rollback sample still equals the baseline.
        self.check("STOP_COMPONENT_ACCOUNT_PAYMENT", change)
        self.check("STOP_ROLLBACK_MISMATCH", lambda b, d, r: r["counts"].update(mail_mail=1))

    def test_avatar_and_gc_exact_hashes(self):
        self.check("STOP_FILE_PROOF", lambda b, d, r: d["files"][0].update(sha256="0" * 64))
        self.check("STOP_FILE_PROOF", lambda b, d, r: d["files"][1].update(for_avatar=False))
        self.check("STOP_UNKNOWN_FILE", lambda b, d, r: d["files"].append({"kind": "other"}))


if __name__ == "__main__":
    unittest.main()

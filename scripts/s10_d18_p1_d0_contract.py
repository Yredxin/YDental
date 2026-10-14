"""Offline S10 P1 diagnostic contract simulation; no Odoo or database entry point.

This file defines the shape of a future observation, not permission to run it.
Every test below is SIMULATED. The failed P1 transaction was not sampled this way.
"""

from __future__ import annotations

from dataclasses import dataclass


FUTURE_AUTH_COMMENT_ID = None
COMPONENTS = (
    "mail_mail",
    "bus_bus",
    "account_payment",
    "account_partial_reconcile",
)
EXPECTED_BUS = ("stock.warehouse._check_multiwarehouse_group", "stock_group_sync", "actor_user", "precommit")


@dataclass(frozen=True)
class Observation:
    baseline: dict[str, int]
    intra_transaction: dict[str, int]
    bus_intents: tuple[tuple[str, str, str, str], ...] = ()
    group_change_scope: str = "none"  # none, global_authorized, global_unapproved
    unexplained_outbound: bool = False
    rollback_after: dict[str, int] | None = None


def assess(observation: Observation) -> dict[str, object]:
    """Keep all four components and transaction/rollback evidence separate."""
    for snapshot in (observation.baseline, observation.intra_transaction):
        if set(snapshot) != set(COMPONENTS):
            raise ValueError("All four independent component counts are required")
        if any(type(snapshot[name]) is not int or snapshot[name] < 0 for name in COMPONENTS):
            raise ValueError("Counts must be nonnegative integers")
    if observation.rollback_after is not None and set(observation.rollback_after) != set(COMPONENTS):
        raise ValueError("Rollback needs four independent component counts")
    if observation.group_change_scope not in {"none", "global_authorized", "global_unapproved"}:
        raise ValueError("Unknown group scope")

    delta = {
        "mail_mail_delta": observation.intra_transaction["mail_mail"] - observation.baseline["mail_mail"],
        "bus_bus_delta": observation.intra_transaction["bus_bus"] - observation.baseline["bus_bus"],
        "account_payment_delta": observation.intra_transaction["account_payment"] - observation.baseline["account_payment"],
        "account_partial_reconcile_delta": observation.intra_transaction["account_partial_reconcile"] - observation.baseline["account_partial_reconcile"],
    }
    reasons = []
    if delta["mail_mail_delta"]:
        reasons.append("mail queue changed; source and send state unknown")
    if delta["bus_bus_delta"]:
        reasons.append("bus rows changed; source and commit state unknown")
    for key in ("account_payment_delta", "account_partial_reconcile_delta"):
        if delta[key]:
            reasons.append(f"native finance object changed: {key}")
    if any(intent != EXPECTED_BUS for intent in observation.bus_intents):
        reasons.append("unexplained bus intent")
    if observation.bus_intents and observation.group_change_scope != "global_authorized":
        reasons.append("bus intent lacks approved global group provenance")
    if observation.group_change_scope == "global_unapproved":
        reasons.append("unapproved cross-company group implication")
    if observation.unexplained_outbound:
        reasons.append("unexplained outbound side effect")
    rollback_equal = observation.rollback_after == observation.baseline if observation.rollback_after is not None else None
    return {
        **delta,
        "bus_precommit_intent_count": len(observation.bus_intents),
        "rollback_equal_baseline": rollback_equal,
        "stop": bool(reasons),
        "reasons": reasons,
        "classification": "SIMULATED_STOP" if reasons else "SIMULATED_ONLY_NEEDS_REAL_PROVENANCE",
    }


def selftest() -> None:
    base = dict(mail_mail=0, bus_bus=6, account_payment=0, account_partial_reconcile=0)

    def case(name: str, current: dict[str, int] | None = None, *, stop: bool,
             intents=(), scope="none", outbound=False, rollback=None):
        result = assess(Observation(base, current or base, tuple(intents), scope, outbound, rollback))
        assert result["stop"] is stop, (name, result)
        print(f"SIMULATED {name}: {'STOP' if stop else 'NEEDS_REAL_PROVENANCE'}")
        return result

    case("all_four_zero_delta", stop=False)
    case("legal_internal_bus_intent_only", stop=False, intents=(EXPECTED_BUS,), scope="global_authorized")
    case("unexpected_mail_queue", {**base, "mail_mail": 1}, stop=True)
    case("native_payment", {**base, "account_payment": 1}, stop=True)
    case("native_partial_reconcile", {**base, "account_partial_reconcile": 1}, stop=True)
    case("multiple_components", {**base, "mail_mail": 1, "bus_bus": 7, "account_payment": 1}, stop=True)
    case("historical_nonzero_bus_no_delta", stop=False)
    result = case("rollback_does_not_erase_intra_failure", {**base, "mail_mail": 1}, stop=True, rollback=base)
    assert result["rollback_equal_baseline"] is True and result["mail_mail_delta"] == 1
    case("warehouse_staff_unapproved_group", stop=True, scope="global_unapproved")
    case("cross_company_group_effect", stop=True, scope="global_unapproved", intents=(EXPECTED_BUS,))
    case("unknown_external_effect", stop=True, outbound=True)
    case("unknown_bus_intent", stop=True, intents=(("unknown", "x", "unknown", "precommit"),))
    case("unattributed_bus_row", {**base, "bus_bus": 7}, stop=True)
    try:
        assess(Observation({"mail_mail": 0}, base))
    except ValueError:
        print("SIMULATED missing_component: STOP")
    else:
        raise AssertionError("A missing component was accepted")
    assert FUTURE_AUTH_COMMENT_ID is None


if __name__ == "__main__":
    selftest()

#!/usr/bin/env python3
"""Race physical receipt against pre-receipt cancellation on a second S11 order.

Both actions compete for one already-dispatched synthetic work order, using
different stable request keys and real PostgreSQL backends. The laboratory
service serializes these state transitions: exactly one should commit, and the
losing action should be rejected after observing the winner's state.

This is distinct from the duplicate-receipt race. It never puts stock away or
creates a follow-up. Explicit PostgreSQL serialization aborts alone receive a
bounded request retry; other errors and uncertain outcomes are preserved for
readback rather than replayed. Private receipts stay under .local/s11/races.
"""

from __future__ import annotations

# Operational CLI follows race_package_code.py conventions.
# ruff: noqa: TRY002, TRY003, TRY301, EM101, BLE001, T201
import argparse
import datetime as dt
import hashlib
import json
import secrets
import sys
import threading
from typing import Any

import race_lab_receipt_duplicate as common
from psycopg2.errors import SerializationFailure

CONFIRMATION = "S11-SYNTHETIC-LAB-CANCEL-RECEIVE-RACE-V1"
THREAD_TIMEOUT_SECONDS = 30
STATEMENT_TIMEOUT_SECONDS = 15
LOCK_TIMEOUT_SECONDS = 10
MAX_SERIALIZATION_RETRIES = 3


def add_transition_columns(cr, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attach persisted transition values omitted from the ORM projection."""
    if not events:
        return events
    event_ids = [row["id"] for row in events]
    cr.execute(
        "SELECT id, ydental_before_state, ydental_after_state "
        "FROM ydental_lab_event WHERE id = ANY(%s) ORDER BY id",
        [event_ids],
    )
    transitions = {event_id: (before, after) for event_id, before, after in cr.fetchall()}
    if set(transitions) != set(event_ids):
        raise common.Refusal("lab event transition readback did not match ORM event IDs")
    for row in events:
        row["ydental_before_state"], row["ydental_after_state"] = transitions[row["id"]]
    return events


def state_snapshot(env, order_id: int, store_id: int) -> dict[str, Any]:
    order = env["ydental.lab.order"].sudo().browse(order_id).exists()
    if not order or order.ydental_store_id.id != store_id:
        raise common.Refusal("target synthetic order is missing or outside the admitted store")
    if not (order.ydental_internal_code or "").startswith("S11-"):
        raise common.Refusal("target must be an S11-prefixed synthetic laboratory work order")
    if order.state not in ("sent", "processing", "received", "cancelled"):
        raise common.Refusal("target order state is outside the cancel/receive race contract")
    events = env["ydental.lab.event"].sudo().search_read(
        [("ydental_order_id", "=", order.id)],
        ["id", "ydental_kind", "ydental_before_state", "ydental_after_state",
         "ydental_inventory_event_id", "ydental_purchase_line_id", "ydental_vendor_cost",
         "ydental_recorded_at", "ydental_actor_id"], order="id",
    )
    # Read these persisted transition columns on the same transaction so
    # before/after snapshots compare database values, including SQL NULL,
    # rather than differing ORM field projections.
    add_transition_columns(env.cr, events)
    inventory_events = env["ydental.inventory.event"].sudo().search_read(
        [("ydental_store_id", "=", store_id), ("ydental_source_namespace", "=", "warehouse"),
         ("ydental_source_key", "=", "lab-receipt-%s" % order.id)],
        ["id", "ydental_kind", "ydental_quantity", "ydental_source_key"], order="id",
    )
    followups = env["ydental.followup"].sudo().search_read(
        [("ydental_lab_order_id", "=", order.id)],
        ["id", "state", "ydental_lab_cycle_key"], order="id",
    )
    purchase_line = order.ydental_purchase_line_id.sudo()
    cost = False
    if purchase_line:
        cost = {"line_id": purchase_line.id, "purchase_id": purchase_line.order_id.id,
                "purchase_state": purchase_line.order_id.state,
                "quantity": purchase_line.product_qty, "unit_price": purchase_line.price_unit,
                "subtotal": purchase_line.price_subtotal, "total": purchase_line.price_total,
                "currency_id": purchase_line.order_id.currency_id.id}
    quants = env["stock.quant"].sudo().search_read(
        [("product_id", "=", order.ydental_product_id.id),
         ("lot_id", "=", order.ydental_lot_id.id)],
        ["id", "location_id", "quantity", "reserved_quantity"], order="location_id,id",
    ) if order.ydental_lot_id else []
    return {
        "order_id": order.id, "store_id": order.ydental_store_id.id,
        "state": order.state, "version": order.ydental_version,
        "internal_code": order.ydental_internal_code,
        "parent_order_id": order.ydental_parent_order_id.id or None,
        "rework_no": order.ydental_rework_no, "product_id": order.ydental_product_id.id,
        "lot_id": order.ydental_lot_id.id or None, "quantity": order.ydental_quantity,
        "receipt_at": order.ydental_receipt_at.isoformat() if order.ydental_receipt_at else None,
        "receipt_actor_id": order.ydental_receipt_actor_id.id or None,
        "exception_reason": order.ydental_exception_reason or None,
        "inventory_event_id": order.ydental_inventory_event_id.id or None,
        "followup_id": order.ydental_followup_id.id or None,
        "lab_events": events, "inventory_events": inventory_events,
        "stock_quants": quants, "followups": followups, "purchase_cost_source": cost,
    }


def verify_prior_race_order(env, target_id: int, prior_id: int, store_id: int) -> None:
    if target_id == prior_id:
        raise common.Refusal("cancel/receive target must differ from the prior S11 race order")
    previous = env["ydental.lab.order"].sudo().browse(prior_id).exists()
    if (not previous or previous.ydental_store_id.id != store_id or
            not (previous.ydental_internal_code or "").startswith("S11-")):
        raise common.Refusal("prior race reference must identify a distinct S11 synthetic order in this store")


def validate_cancel_receive_target(env, order_id: int, store_id: int) -> dict[str, Any]:
    before = common.snapshot(env, order_id, store_id)
    # common.snapshot intentionally requests a smaller event projection than
    # state_snapshot; normalize the baseline through the same persisted read.
    add_transition_columns(env.cr, before["lab_events"])
    before["version"] = env["ydental.lab.order"].sudo().browse(order_id).ydental_version
    if before["state"] not in ("sent", "processing"):
        raise common.Refusal("cancel/receive race requires an active sent or processing order")
    if not before["lot_id"]:
        raise common.Refusal("cancel/receive target must have a matching receiving lot")
    if any(row["ydental_kind"] == "cancelled" for row in before["lab_events"]):
        raise common.Refusal("target already has a cancellation event; do not replay")
    if before["inventory_events"] or before["followups"] or before["receipt_audits"]:
        raise common.Refusal("target has a previous receipt audit, stock event, or follow-up; do not replay")
    return before


def worker(registry, api, actor_id: int, session_key: str, store_id: int,
           order_id: int, operation: str, payload: dict[str, Any], action_key: str,
           barrier: threading.Barrier, outcomes: list[dict[str, Any]]) -> None:
    first_pid = None
    for attempt in range(1, MAX_SERIALIZATION_RETRIES + 1):
        try:
            with registry.cursor() as cr:
                cr.execute("SET LOCAL statement_timeout = %s", [f"{STATEMENT_TIMEOUT_SECONDS}s"])
                cr.execute("SET LOCAL lock_timeout = %s", [f"{LOCK_TIMEOUT_SECONDS}s"])
                cr.execute("SELECT pg_backend_pid()")
                backend_pid = cr.fetchone()[0]
                first_pid = first_pid or backend_pid
                env = api.Environment(cr, actor_id, {"lang": "en_US"})
                access = env["ydental.access.service"]
                session = access._existing_session_for_key(session_key)
                if not session:
                    raise common.Refusal("worker session is absent")
                bound = access._bind(session)
                if attempt == 1:
                    barrier.wait(timeout=THREAD_TIMEOUT_SECONDS)
                try:
                    response = bound.env["ydental.lab.service"]._operate(operation, payload, action_key)
                    result = {"kind": "accepted", "operation": operation,
                              "result": response.get("result"), "state": response.get("state"),
                              "order_id": response.get("order_id")}
                except SerializationFailure:
                    raise
                except Exception as error:
                    from odoo.exceptions import UserError  # noqa: PLC0415

                    expected = ("Only an active external order can be physically received." if operation == "receive"
                                else "Cancellation is allowed only before physical receipt.")
                    if isinstance(error, UserError) and expected in str(error):
                        result = {"kind": "expected_state_conflict", "operation": operation}
                    else:
                        result = {"kind": "action_error", "operation": operation,
                                  "error_type": type(error).__name__}
                cr.commit()
                outcomes.append({"backend_pid": first_pid, "attempts": attempt, **result})
                return
        except SerializationFailure:
            # A known PostgreSQL abort is safe to retry with the same stable key.
            if attempt == MAX_SERIALIZATION_RETRIES:
                outcomes.append({"backend_pid": first_pid, "attempts": attempt,
                                 "kind": "serialization_retry_exhausted", "operation": operation})
        except Exception as error:
            outcomes.append({"backend_pid": first_pid, "attempts": attempt,
                             "kind": "worker_error", "operation": operation,
                             "error_type": type(error).__name__})
            return


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, help="full admitted S11 commit SHA")
    parser.add_argument("--actor-id", required=True, type=int, help="ordinary store-scoped warehouse actor")
    parser.add_argument("--store-id", required=True, type=int, help="admitted S11 store ID")
    parser.add_argument("--order-id", required=True, type=int, help="second S11 sent/processing order ID")
    parser.add_argument("--prior-race-order-id", required=True, type=int,
                        help="distinct S11 order used by the earlier scan race")
    parser.add_argument("--confirm", required=True)
    args = parser.parse_args()
    if (args.confirm != CONFIRMATION or
            min(args.actor_id, args.store_id, args.order_id, args.prior_race_order_id) <= 0):
        raise common.Refusal("explicit confirmation and positive actor/store/order IDs are required")
    if (len(args.candidate) != 40 or
            any(char not in "0123456789abcdef" for char in args.candidate)):
        raise common.Refusal("candidate must be a full lowercase 40-character commit SHA")

    launcher, runtime, admission, database, branch, commit = common.load_admitted_runtime(args.candidate)
    api, Registry = common.configure_odoo(launcher, database)
    registry = Registry(database["name"])
    with registry.cursor() as cr:
        identity = common.readonly_identity(cr, launcher, database)
        env = api.Environment(cr, args.actor_id, {})
        common.validate_actor(env, admission, args.actor_id, args.store_id)
        verify_prior_race_order(env, args.order_id, args.prior_race_order_id, args.store_id)
        modules = env["ir.module.module"].sudo().search_read(
            [("name", "in", ["ydental_lab", "ydental_followup"]), ("state", "=", "installed")],
            ["name", "state"],
        )
        if {row["name"] for row in modules} != {"ydental_lab", "ydental_followup"}:
            raise common.Refusal("required S11 laboratory and follow-up modules must already be installed")
        before = validate_cancel_receive_target(env, args.order_id, args.store_id)
        cr.rollback()

    race_id = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(4)
    receipt_path = common.RACE_ROOT / f"{race_id}-lab-cancel-receive.json"
    keys = {"receive": "s11-recv-race-" + secrets.token_hex(18),
            "cancel": "s11-cancel-race-" + secrets.token_hex(18)}
    reason = "S11 synthetic concurrent cancellation test"
    payloads = {"receive": {"order_id": args.order_id},
                "cancel": {"order_id": args.order_id, "reason": reason}}
    session_keys = [secrets.token_urlsafe(32), secrets.token_urlsafe(32)]
    phase: dict[str, Any] = {
        "schema": "YD-S11-LAB-CANCEL-RECEIVE-RACE-V1", "plan_id": launcher.PLAN_ID,
        "candidate_commit": commit, "branch": branch,
        "scope_id": runtime["scope"]["id"], "scope_expires_at_utc": runtime["scope"]["expires_at_utc"],
        "database_identity": identity, "actor_id": args.actor_id, "store_id": args.store_id,
        "order_id": args.order_id, "prior_race_order_id": args.prior_race_order_id,
        "session_ids": [],
        "session_key_sha256": [hashlib.sha256(key.encode()).hexdigest() for key in session_keys],
        "action_key_sha256": {name: hashlib.sha256(key.encode()).hexdigest()
                              for name, key in keys.items()},
        "payloads": payloads, "before": before, "phase": "READY_BEFORE_RACE",
        "business_mutation_started": False, "started_at_utc": common.utc_now(),
    }
    common.write_private(receipt_path, phase)
    for index, session_key in enumerate(session_keys, 1):
        session_id = common.prepare_session(registry, api, args.actor_id, args.store_id, session_key)
        phase["session_ids"].append(session_id)
        phase["phase"] = "SESSION_SETUP_COMMITTED"
        phase["session_setup_count"] = index
        phase["session_checkpoint_at_utc"] = common.utc_now()
        common.write_private(receipt_path, phase)
    phase["phase"] = "SESSION_SETUP_COMPLETE"
    common.write_private(receipt_path, phase)
    phase.update({"phase": "TWO_CONNECTION_CANCEL_RECEIVE_PENDING",
                  "business_mutation_started": True, "mutation_started_at_utc": common.utc_now()})
    common.write_private(receipt_path, phase)

    barrier = threading.Barrier(2)
    outcomes: list[dict[str, Any]] = []
    worker_specs = [("receive", 0), ("cancel", 1)]
    threads = [threading.Thread(
        target=worker,
        args=(registry, api, args.actor_id, session_keys[index], args.store_id,
              args.order_id, action, payloads[action], keys[action], barrier, outcomes),
        name=f"s11-cancel-receive-{action}", daemon=True,
    ) for action, index in worker_specs]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(THREAD_TIMEOUT_SECONDS + 25)
    if any(thread.is_alive() for thread in threads):
        phase.update({"phase": "WORKER_TIMEOUT_REQUIRES_READBACK", "worker_results": outcomes,
                      "finished_at_utc": common.utc_now()})
        common.write_private(receipt_path, phase)
        raise common.Refusal(f"bounded race timed out; preserve receipt and independently read back before retry: {receipt_path}")

    with registry.cursor() as cr:
        cr.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        env = api.Environment(cr, args.actor_id, {})
        after = state_snapshot(env, args.order_id, args.store_id)
        operation_rows = env["ydental.lab.operation"].sudo().search_read(
            [("ydental_store_id", "=", args.store_id), ("ydental_key", "in", list(keys.values()))],
            ["id", "ydental_key", "ydental_fingerprint", "ydental_result"], order="id",
        )
        audit_rows = env["ydental.access.audit"].sudo().search_read(
            [("ydental_store_id", "=", args.store_id),
             ("ydental_event", "in", ["lab.received", "lab.cancelled"]),
             ("ydental_target_model", "=", "ydental.lab.order"),
             ("ydental_target_id", "=", args.order_id)],
            ["id", "ydental_event", "ydental_user_id"], order="id",
        )
        cr.rollback()

    accepted = [row for row in outcomes if row.get("kind") == "accepted"]
    rejected = [row for row in outcomes if row.get("kind") == "expected_state_conflict"]
    accepted_action = accepted[0].get("operation") if len(accepted) == 1 else None
    expected_state = "received" if accepted_action == "receive" else "cancelled" if accepted_action == "cancel" else None
    expected_event = "received" if expected_state == "received" else "cancelled"
    event_delta = [row for row in after["lab_events"]
                   if row["ydental_kind"] in ("received", "cancelled")]
    old_event_rows = {row["id"]: row for row in before["lab_events"]}
    new_event_rows = {row["id"]: row for row in after["lab_events"]}
    existing_events_preserved = all(new_event_rows.get(event_id) == row
                                    for event_id, row in old_event_rows.items())
    expected_result = {"order_id": args.order_id, "state": expected_state, "inventory_event_id": False}
    winning_key = keys.get(accepted_action)
    expected_fingerprint = hashlib.sha256(
        json.dumps([accepted_action, args.store_id, payloads.get(accepted_action)],
                   sort_keys=True, ensure_ascii=True).encode()).hexdigest() if accepted_action else None
    one_action = (len(accepted) == 1 and len(rejected) == 1 and
                  {row.get("operation") for row in outcomes} == {"receive", "cancel"} and
                  accepted_action in ("receive", "cancel") and after["state"] == expected_state and
                  after["version"] == before["version"] + 1 and
                  len(after["lab_events"]) == len(before["lab_events"]) + 1 and
                  existing_events_preserved and
                  len(event_delta) == 1 and event_delta[0]["ydental_kind"] == expected_event and
                  event_delta[0]["ydental_before_state"] == before["state"] and
                  event_delta[0]["ydental_after_state"] == expected_state and
                  event_delta[0]["ydental_actor_id"][0] == args.actor_id)
    one_operation = (len(operation_rows) == 1 and operation_rows[0]["ydental_key"] == winning_key and
                     operation_rows[0]["ydental_result"] == expected_result and
                     operation_rows[0]["ydental_fingerprint"] == expected_fingerprint)
    one_audit = (len(audit_rows) == 1 and audit_rows[0]["ydental_event"] == "lab." + expected_event and
                 audit_rows[0]["ydental_user_id"][0] == args.actor_id)
    pids = [row.get("backend_pid") for row in outcomes]
    no_stock_side_effect = (after["inventory_event_id"] is None and after["followup_id"] is None and
                           after["inventory_events"] == before["inventory_events"] and
                           after["followups"] == before["followups"] and
                           after["stock_quants"] == before["stock_quants"] and
                           after["purchase_cost_source"] == before["purchase_cost_source"])
    passed = (len(outcomes) == 2 and len(set(pids)) == 2 and one_action and one_operation and
              one_audit and no_stock_side_effect)
    phase.update({
        "phase": "READBACK_COMPLETE", "worker_results": outcomes,
        "two_distinct_postgresql_backends": len(set(pids)) == 2,
        "after": after, "committed_operation_rows": operation_rows, "matching_audit_rows": audit_rows,
        "exactly_one_action_committed": one_action, "one_idempotency_operation": one_operation,
        "one_matching_audit": one_audit, "stock_followup_and_cost_unchanged": no_stock_side_effect,
        "winner": accepted_action, "expected_final_state": expected_state,
        "outcome": "PASS" if passed else "FAIL", "finished_at_utc": common.utc_now(),
    })
    common.write_private(receipt_path, phase)
    print(json.dumps({"receipt": str(receipt_path), "outcome": phase["outcome"],
                      "winner": accepted_action, "final_state": after["state"],
                      "two_distinct_postgresql_backends": phase["two_distinct_postgresql_backends"],
                      "exactly_one_action_committed": one_action,
                      "stock_followup_and_cost_unchanged": no_stock_side_effect}, sort_keys=True))
    return 0 if passed else 3


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"S11 lab cancel/receive race stopped: {type(error).__name__}: {error}", file=sys.stderr)
        raise SystemExit(2)

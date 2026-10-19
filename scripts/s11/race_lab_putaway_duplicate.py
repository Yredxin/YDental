#!/usr/bin/env python3
"""Race two ordinary workers putting away one received S11 synthetic order.

Both real PostgreSQL requests use the same stable laboratory action key and
payload. The expected result is one put-away, one native receipt movement, one
passive follow-up, and an idempotent result for the duplicate request. This
script never starts Odoo or creates business objects. It requires an already
received synthetic order with its committed receipt and no put-away effects.
"""

from __future__ import annotations

# Operational CLI follows race_package_code.py conventions.
# ruff: noqa: TRY002, TRY003, TRY301, EM101, BLE001, T201
import argparse
import datetime as dt
import hashlib
import json
import math
import secrets
import sys
import threading
from typing import Any

import race_lab_receipt_duplicate as common
from psycopg2.errors import SerializationFailure

CONFIRMATION = "S11-SYNTHETIC-LAB-PUTAWAY-DUPLICATE-RACE-V1"
THREAD_TIMEOUT_SECONDS = 30
STATEMENT_TIMEOUT_SECONDS = 15
LOCK_TIMEOUT_SECONDS = 10
MAX_SERIALIZATION_RETRIES = 3


def relation_id(value: Any) -> int | None:
    return value[0] if isinstance(value, (tuple, list)) and value else value or None


def snapshot(env, order_id: int, store_id: int) -> dict[str, Any]:
    order = env["ydental.lab.order"].sudo().browse(order_id).exists()
    if not order or order.ydental_store_id.id != store_id:
        raise common.Refusal("target synthetic order is missing or outside the admitted store")
    if not (order.ydental_internal_code or "").startswith("S11-"):
        raise common.Refusal("target must be an S11-prefixed synthetic laboratory order")
    events = env["ydental.lab.event"].sudo().search_read(
        [("ydental_order_id", "=", order.id)],
        ["id", "ydental_kind", "ydental_before_state", "ydental_after_state",
         "ydental_inventory_event_id", "ydental_purchase_line_id", "ydental_vendor_cost",
         "ydental_recorded_at", "ydental_actor_id"], order="id",
    )
    inventory_key = "lab-receipt-%s" % order.id
    inventory_events = env["ydental.inventory.event"].sudo().search_read(
        [("ydental_store_id", "=", store_id), ("ydental_source_namespace", "=", "warehouse"),
         ("ydental_source_key", "=", inventory_key)],
        ["id", "ydental_kind", "ydental_quantity", "ydental_product_id", "ydental_lot_id",
         "ydental_source_namespace",
         "ydental_source_key", "ydental_from_id", "ydental_to_id", "ydental_move_id",
         "ydental_actor_id", "state"], order="id",
    )
    followups = env["ydental.followup"].sudo().search_read(
        [("ydental_lab_order_id", "=", order.id)],
        ["id", "ydental_lab_order_id", "ydental_lab_cycle_key", "ydental_followup_type",
         "ydental_patient_id", "ydental_source_event_id", "ydental_responsible_id", "state"], order="id",
    )
    quants = env["stock.quant"].sudo().search_read(
        [("product_id", "=", order.ydental_product_id.id),
         ("lot_id", "=", order.ydental_lot_id.id)],
        ["id", "location_id", "owner_id", "package_id", "quantity", "reserved_quantity"],
        order="location_id,id",
    ) if order.ydental_lot_id else []
    quant_projection = {}
    for quant in quants:
        key = (relation_id(quant["location_id"]), relation_id(quant["owner_id"]),
               relation_id(quant["package_id"]))
        totals = quant_projection.setdefault(key, {"quantity": 0.0, "reserved_quantity": 0.0})
        totals["quantity"] += quant["quantity"]
        totals["reserved_quantity"] += quant["reserved_quantity"]

    purchase_line = order.ydental_purchase_line_id.sudo()
    cost = False
    if purchase_line:
        cost = {"line_id": purchase_line.id, "purchase_id": purchase_line.order_id.id,
                "purchase_state": purchase_line.order_id.state,
                "quantity": purchase_line.product_qty, "unit_price": purchase_line.price_unit,
                "subtotal": purchase_line.price_subtotal, "total": purchase_line.price_total,
                "currency_id": purchase_line.order_id.currency_id.id}
    audits = env["ydental.access.audit"].sudo().search_read(
        [("ydental_store_id", "=", store_id), ("ydental_event", "=", "lab.putaway"),
         ("ydental_target_model", "=", "ydental.lab.order"),
         ("ydental_target_id", "=", order.id)], ["id", "ydental_user_id"], order="id",
    )
    move = False
    if inventory_events and inventory_events[0]["ydental_move_id"]:
        move_record = env["stock.move"].sudo().browse(inventory_events[0]["ydental_move_id"][0]).exists()
        if move_record:
            move = {"id": move_record.id, "state": move_record.state,
                    "product_id": move_record.product_id.id, "product_uom_qty": move_record.product_uom_qty,
                    "uom_id": move_record.product_uom.id, "location_id": move_record.location_id.id,
                    "location_dest_id": move_record.location_dest_id.id,
                    "company_id": move_record.company_id.id, "store_id": move_record.ydental_store_id.id}
    config = env["ydental.inventory.config"].sudo().search(
        [("ydental_store_id", "=", store_id)], limit=1)
    if not config:
        raise common.Refusal("store inventory configuration is missing")
    target_location_id = config.ydental_prosthesis_id.id
    target_location_usage = config.ydental_prosthesis_id.usage
    target_location_company_id = config.ydental_prosthesis_id.company_id.id or None
    return {
        "order_id": order.id, "store_id": order.ydental_store_id.id,
        "state": order.state, "version": order.ydental_version,
        "internal_code": order.ydental_internal_code,
        "patient_id": order.ydental_patient_id.id,
        "source_event_id": order.ydental_source_event_id.id,
        "responsible_id": order.ydental_responsible_id.id,
        "product_id": order.ydental_product_id.id,
        "product_rounding": order.ydental_product_id.uom_id.rounding,
        "product_uom_id": order.ydental_product_id.uom_id.id,
        "company_id": order.ydental_store_id.company_id.id,
        "lot_id": order.ydental_lot_id.id or None,
        "quantity": order.ydental_quantity,
        "inventory_key": inventory_key,
        "target_location_id": target_location_id,
        "target_location_usage": target_location_usage,
        "target_location_company_id": target_location_company_id,
        "supplier_location_id": config.ydental_supplier_id.id,
        "receipt_at": order.ydental_receipt_at.isoformat() if order.ydental_receipt_at else None,
        "receipt_actor_id": order.ydental_receipt_actor_id.id or None,
        "inventory_event_id": order.ydental_inventory_event_id.id or None,
        "followup_id": order.ydental_followup_id.id or None,
        "lab_events": events, "inventory_events": inventory_events,
        "followups": followups, "stock_quants": quants,
        "stock_quant_projection": [
            {"location_id": key[0], "owner_id": key[1], "package_id": key[2], **value}
            for key, value in sorted(quant_projection.items(), key=lambda item: tuple(v or 0 for v in item[0]))
        ],
        "purchase_cost_source": cost, "move": move,
        "putaway_audits": audits,
    }


def validate_target(env, order_id: int, actor_id: int, store_id: int) -> dict[str, Any]:
    before = snapshot(env, order_id, store_id)
    order = env["ydental.lab.order"].sudo().browse(order_id)
    if (order.state != "received" or not before["lot_id"] or
            order.ydental_lot_id.product_id != order.ydental_product_id):
        raise common.Refusal("target must be physically received and have its matching prosthesis lot")
    receipt_events = [row for row in before["lab_events"] if row["ydental_kind"] == "received"]
    if (len(receipt_events) != 1 or receipt_events[0]["ydental_after_state"] != "received" or
            receipt_events[0]["ydental_inventory_event_id"] or
            not before["receipt_at"] or not before["receipt_actor_id"]):
        raise common.Refusal("target must have exactly one committed physical receipt without put-away effects")
    if (any(row["ydental_kind"] == "putaway" for row in before["lab_events"]) or
            order.ydental_inventory_event_id or order.ydental_followup_id or
            before["inventory_events"] or before["followups"] or before["putaway_audits"]):
        raise common.Refusal("target already has put-away stock, follow-up, or audit; do not replay")
    if order.ydental_product_id.ydental_inventory_kind != "prosthesis":
        raise common.Refusal("target product must be configured as a prosthesis")
    if before["target_location_id"] <= 0:
        raise common.Refusal("store prosthesis stock location is missing")
    if (before["target_location_usage"] != "internal" or
            before["target_location_company_id"] != before["company_id"]):
        raise common.Refusal("prosthesis destination must be an internal location of the target company")
    if order.ydental_receipt_actor_id.id <= 0 or actor_id <= 0:
        raise common.Refusal("target receipt actor and current warehouse actor must be present")
    return before


def prepare_inventory_operation(registry, api, actor_id: int, store_id: int,
                                key: str) -> int:
    with registry.cursor() as cr:
        cr.execute("SET TRANSACTION READ ONLY")
        env = api.Environment(cr, actor_id, {})
        rows = env["ydental.inventory.operation"].sudo().search_count(
            [("ydental_store_id", "=", store_id), ("ydental_key", "=", key)])
        cr.rollback()
    return rows


def worker(registry, api, actor_id: int, session_key: str, order_id: int,
           action_key: str, barrier: threading.Barrier, outcomes: list[dict[str, Any]]) -> None:
    first_pid = None
    for attempt in range(1, MAX_SERIALIZATION_RETRIES + 1):
        try:
            with registry.cursor() as cr:
                cr.execute("SET LOCAL statement_timeout = %s", [f"{STATEMENT_TIMEOUT_SECONDS}s"])
                cr.execute("SET LOCAL lock_timeout = %s", [f"{LOCK_TIMEOUT_SECONDS}s"])
                cr.execute("SELECT pg_backend_pid()")
                backend_pid = cr.fetchone()[0]
                first_pid = first_pid or backend_pid
                env = api.Environment(cr, actor_id, {})
                access = env["ydental.access.service"]
                session = access._existing_session_for_key(session_key)
                if not session:
                    raise common.Refusal("worker session is absent")
                bound = access._bind(session)
                if attempt == 1:
                    barrier.wait(timeout=THREAD_TIMEOUT_SECONDS)
                try:
                    response = bound.env["ydental.lab.service"]._operate(
                        "putaway", {"order_id": order_id}, action_key)
                    result = {"kind": response.get("result"), "state": response.get("state"),
                              "order_id": response.get("order_id"),
                              "inventory_event_id": response.get("inventory_event_id")}
                except SerializationFailure:
                    raise
                except Exception as error:
                    result = {"kind": "action_error", "error_type": type(error).__name__}
                cr.commit()
                outcomes.append({"backend_pid": first_pid, "attempts": attempt, **result})
                return
        except SerializationFailure:
            if attempt == MAX_SERIALIZATION_RETRIES:
                outcomes.append({"backend_pid": first_pid, "attempts": attempt,
                                 "kind": "serialization_retry_exhausted"})
        except Exception as error:
            outcomes.append({"backend_pid": first_pid, "attempts": attempt,
                             "kind": "worker_error", "error_type": type(error).__name__})
            return


def quant_effect_is_exact(before: dict[str, Any], after: dict[str, Any], movement_quantity: float) -> bool:
    old = {(row["location_id"], row["owner_id"], row["package_id"]): row
           for row in before["stock_quant_projection"]}
    new = {(row["location_id"], row["owner_id"], row["package_id"]): row
           for row in after["stock_quant_projection"]}
    target_key = (before["target_location_id"], None, None)
    keys = set(old) | set(new)
    if target_key not in keys:
        return False
    rounding = before["product_rounding"]
    tolerance = max(1e-9, rounding * 1e-6)
    changed = []
    for key in keys:
        previous = old.get(key, {"quantity": 0.0, "reserved_quantity": 0.0})
        current = new.get(key, {"quantity": 0.0, "reserved_quantity": 0.0})
        delta = current["quantity"] - previous["quantity"]
        reserved_delta = current["reserved_quantity"] - previous["reserved_quantity"]
        if abs(delta) > tolerance or abs(reserved_delta) > tolerance:
            changed.append((key, delta, reserved_delta))
    return (len(changed) == 1 and changed[0][0] == target_key and
            math.isclose(changed[0][1], movement_quantity, rel_tol=0.0, abs_tol=tolerance) and
            abs(changed[0][2]) <= tolerance)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, help="full admitted S11 commit SHA")
    parser.add_argument("--actor-id", required=True, type=int, help="ordinary store-scoped warehouse actor")
    parser.add_argument("--store-id", required=True, type=int, help="admitted S11 store ID")
    parser.add_argument("--order-id", required=True, type=int, help="received S11 synthetic order ID")
    parser.add_argument("--confirm", required=True)
    args = parser.parse_args()
    if args.confirm != CONFIRMATION or min(args.actor_id, args.store_id, args.order_id) <= 0:
        raise common.Refusal("explicit confirmation and positive actor/store/order IDs are required")
    if len(args.candidate) != 40 or any(char not in "0123456789abcdef" for char in args.candidate):
        raise common.Refusal("candidate must be a full lowercase 40-character commit SHA")

    launcher, runtime, admission, database, branch, commit = common.load_admitted_runtime(args.candidate)
    api, Registry = common.configure_odoo(launcher, database)
    registry = Registry(database["name"])
    with registry.cursor() as cr:
        identity = common.readonly_identity(cr, launcher, database)
        env = api.Environment(cr, args.actor_id, {})
        common.validate_actor(env, admission, args.actor_id, args.store_id)
        modules = env["ir.module.module"].sudo().search_read(
            [("name", "in", ["ydental_lab", "ydental_followup", "ydental_inventory"]),
             ("state", "=", "installed")], ["name", "state"],
        )
        if {row["name"] for row in modules} != {"ydental_lab", "ydental_followup", "ydental_inventory"}:
            raise common.Refusal("required laboratory, follow-up, and inventory modules must already be installed")
        before = validate_target(env, args.order_id, args.actor_id, args.store_id)
        cr.rollback()

    action_key = "s11-putaway-race-" + secrets.token_hex(18)
    inventory_key = "lab-putaway-%s" % args.order_id
    if prepare_inventory_operation(registry, api, args.actor_id, args.store_id, inventory_key):
        raise common.Refusal("the deterministic inner inventory key already exists; preserve state and do not replay")
    race_id = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(4)
    receipt_path = common.RACE_ROOT / f"{race_id}-lab-putaway-duplicate.json"
    session_keys = [secrets.token_urlsafe(32), secrets.token_urlsafe(32)]
    phase: dict[str, Any] = {
        "schema": "YD-S11-LAB-PUTAWAY-DUPLICATE-RACE-V1", "plan_id": launcher.PLAN_ID,
        "candidate_commit": commit, "branch": branch,
        "scope_id": runtime["scope"]["id"], "scope_expires_at_utc": runtime["scope"]["expires_at_utc"],
        "database_identity": identity, "actor_id": args.actor_id, "store_id": args.store_id,
        "order_id": args.order_id, "session_ids": [],
        "session_key_sha256": [hashlib.sha256(key.encode()).hexdigest() for key in session_keys],
        "lab_action_key_sha256": hashlib.sha256(action_key.encode()).hexdigest(),
        "inventory_key": inventory_key, "inventory_action": "receive",
        "request_payload": {"order_id": args.order_id}, "before": before,
        "phase": "READY_BEFORE_RACE", "business_mutation_started": False,
        "started_at_utc": common.utc_now(),
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
    phase.update({"phase": "TWO_CONNECTION_PUTAWAY_PENDING",
                  "business_mutation_started": True, "mutation_started_at_utc": common.utc_now()})
    common.write_private(receipt_path, phase)

    barrier = threading.Barrier(2)
    outcomes: list[dict[str, Any]] = []
    threads = [threading.Thread(
        target=worker,
        args=(registry, api, args.actor_id, session_keys[index], args.order_id,
              action_key, barrier, outcomes),
        name=f"s11-putaway-race-{index + 1}", daemon=True,
    ) for index in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(THREAD_TIMEOUT_SECONDS + 25)
    if any(thread.is_alive() for thread in threads):
        phase.update({"phase": "WORKER_TIMEOUT_REQUIRES_READBACK", "worker_results": outcomes,
                      "finished_at_utc": common.utc_now()})
        common.write_private(receipt_path, phase)
        raise common.Refusal(f"bounded put-away race timed out; preserve receipt and independently read back before retry: {receipt_path}")

    with registry.cursor() as cr:
        cr.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        env = api.Environment(cr, args.actor_id, {})
        after = snapshot(env, args.order_id, args.store_id)
        lab_operations = env["ydental.lab.operation"].sudo().search_read(
            [("ydental_store_id", "=", args.store_id), ("ydental_key", "=", action_key)],
            ["id", "ydental_key", "ydental_fingerprint", "ydental_result", "ydental_actor_id"], order="id",
        )
        inventory_operations = env["ydental.inventory.operation"].sudo().search_read(
            [("ydental_store_id", "=", args.store_id), ("ydental_key", "=", inventory_key)],
            ["id", "ydental_key", "ydental_fingerprint", "ydental_result", "ydental_actor_id"], order="id",
        )
        movement_quantity = after["inventory_events"][0]["ydental_quantity"] if len(after["inventory_events"]) == 1 else 0.0
        cr.rollback()

    putaway_events = [row for row in after["lab_events"] if row["ydental_kind"] == "putaway"]
    receipt_events = [row for row in after["lab_events"] if row["ydental_kind"] == "received"]
    old_events = {row["id"]: row for row in before["lab_events"]}
    new_events = {row["id"]: row for row in after["lab_events"]}
    history_preserved = all(new_events.get(event_id) == row for event_id, row in old_events.items())
    inventory_event = after["inventory_events"][0] if len(after["inventory_events"]) == 1 else {}
    followup = after["followups"][0] if len(after["followups"]) == 1 else {}
    move = after["move"] or {}
    expected_lab_result = {"order_id": args.order_id, "state": "available",
                           "inventory_event_id": inventory_event.get("id", False)}
    lab_fingerprint = hashlib.sha256(
        json.dumps(["putaway", args.store_id, {"order_id": args.order_id}],
                   sort_keys=True, ensure_ascii=True).encode()).hexdigest()
    inventory_payload = {
        "lot_id": before["lot_id"], "quantity": before["quantity"],
        "uom_id": before["product_uom_id"],
        "source_key": before["inventory_key"],
        "reason": "External laboratory work order %s received and put away" % before["internal_code"],
    }
    inventory_fingerprint = hashlib.sha256(
        json.dumps(["receive", args.store_id, inventory_payload],
                   sort_keys=True, ensure_ascii=True).encode()).hexdigest()
    expected_inventory_result = {"id": inventory_event.get("id"), "move_id": move.get("id"),
                                 "state": "done", "result": "accepted"}
    one_putaway = (after["state"] == "available" and len(putaway_events) == 1 and
                   len(receipt_events) == 1 and len(after["lab_events"]) == len(before["lab_events"]) + 1 and
                   history_preserved and putaway_events[0]["ydental_before_state"] == "received" and
                   putaway_events[0]["ydental_after_state"] == "available" and
                   putaway_events[0]["ydental_actor_id"][0] == args.actor_id and
                   putaway_events[0]["ydental_inventory_event_id"][0] == inventory_event.get("id") and
                   after["inventory_event_id"] == inventory_event.get("id"))
    one_stock_event = (len(after["inventory_events"]) == 1 and
                       inventory_event.get("ydental_kind") == "receipt" and
                       inventory_event.get("ydental_source_namespace") == "warehouse" and
                       inventory_event.get("ydental_source_key") == before["inventory_key"] and
                       relation_id(inventory_event.get("ydental_product_id")) == before["product_id"] and
                       relation_id(inventory_event.get("ydental_lot_id")) == before["lot_id"] and
                       relation_id(inventory_event.get("ydental_from_id")) == before["supplier_location_id"] and
                       relation_id(inventory_event.get("ydental_to_id")) == before["target_location_id"] and
                       relation_id(inventory_event.get("ydental_move_id")) == move.get("id") and
                       inventory_event.get("state") == "done" and
                       relation_id(inventory_event.get("ydental_actor_id")) == args.actor_id and
                       move.get("id") and move.get("state") == "done" and
                       move.get("product_id") == before["product_id"] and
                       move.get("location_id") == before["supplier_location_id"] and
                       move.get("location_dest_id") == before["target_location_id"] and
                       move.get("company_id") == before["company_id"] and
                       move.get("store_id") == args.store_id and
                       math.isclose(movement_quantity, before["quantity"], rel_tol=0.0,
                                    abs_tol=max(1e-9, before["product_rounding"] * 1e-6)) and
                       math.isclose(move.get("product_uom_qty", 0.0), movement_quantity, rel_tol=0.0,
                                    abs_tol=max(1e-9, before["product_rounding"] * 1e-6)) and
                       move.get("uom_id") == before["product_uom_id"])
    one_followup = (len(after["followups"]) == 1 and followup.get("id") == after["followup_id"] and
                    relation_id(followup.get("ydental_lab_order_id")) == args.order_id and
                    followup.get("ydental_lab_cycle_key") == "order" and
                    followup.get("ydental_followup_type") == "lab_arrival" and
                    relation_id(followup.get("ydental_patient_id")) == before["patient_id"] and
                    relation_id(followup.get("ydental_source_event_id")) == before["source_event_id"] and
                    relation_id(followup.get("ydental_responsible_id")) == before["responsible_id"])
    one_lab_operation = (len(lab_operations) == 1 and
                         lab_operations[0]["ydental_result"] == expected_lab_result and
                         lab_operations[0]["ydental_fingerprint"] == lab_fingerprint and
                         relation_id(lab_operations[0]["ydental_actor_id"]) == args.actor_id)
    one_inventory_operation = (len(inventory_operations) == 1 and
                               inventory_operations[0]["ydental_key"] == inventory_key and
                               inventory_operations[0]["ydental_fingerprint"] == inventory_fingerprint and
                               inventory_operations[0]["ydental_result"] == expected_inventory_result and
                               relation_id(inventory_operations[0]["ydental_actor_id"]) == args.actor_id)
    audit = after["putaway_audits"]
    one_audit = len(audit) == 1 and audit[0]["ydental_user_id"][0] == args.actor_id
    quant_exact = quant_effect_is_exact(before, after, movement_quantity)
    cost_unchanged = after["purchase_cost_source"] == before["purchase_cost_source"]
    pids = [row.get("backend_pid") for row in outcomes]
    passed = (len(outcomes) == 2 and len(set(pids)) == 2 and
              sorted(row.get("kind") for row in outcomes) == ["accepted", "already_accepted"] and
              all(row.get("state") == "available" and row.get("order_id") == args.order_id
                  for row in outcomes) and one_putaway and one_stock_event and one_followup and
              one_lab_operation and one_inventory_operation and one_audit and quant_exact and cost_unchanged)
    phase.update({
        "phase": "READBACK_COMPLETE", "worker_results": outcomes,
        "two_distinct_postgresql_backends": len(set(pids)) == 2,
        "after": after, "committed_lab_operations": lab_operations,
        "committed_inventory_operations": inventory_operations,
        "exactly_one_putaway": one_putaway, "one_native_inventory_event_and_move": one_stock_event,
        "one_passive_followup": one_followup, "one_lab_idempotency_operation": one_lab_operation,
        "one_inventory_idempotency_operation": one_inventory_operation,
        "one_putaway_audit": one_audit, "exact_product_lot_quant_effect": quant_exact,
        "supplier_cost_snapshot_unchanged": cost_unchanged,
        "inventory_movement_quantity": movement_quantity,
        "outcome": "PASS" if passed else "FAIL", "finished_at_utc": common.utc_now(),
    })
    common.write_private(receipt_path, phase)
    print(json.dumps({"receipt": str(receipt_path), "outcome": phase["outcome"],
                      "two_distinct_postgresql_backends": phase["two_distinct_postgresql_backends"],
                      "exactly_one_putaway": one_putaway,
                      "one_native_inventory_event_and_move": one_stock_event,
                      "one_passive_followup": one_followup,
                      "exact_product_lot_quant_effect": quant_exact,
                      "supplier_cost_snapshot_unchanged": cost_unchanged}, sort_keys=True))
    return 0 if passed else 3


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"S11 lab put-away duplicate race stopped: {type(error).__name__}: {error}", file=sys.stderr)
        raise SystemExit(2)

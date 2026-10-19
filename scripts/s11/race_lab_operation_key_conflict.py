#!/usr/bin/env python3
"""Exercise a same-key collision on two independent synthetic lab orders."""

from __future__ import annotations

# Operational CLI follows the bounded S11 race harness conventions.
# ruff: noqa: BLE001, EM101, T201, TRY002, TRY003, TRY301
import argparse
import datetime as dt
import hashlib
import json
import secrets
import sys
import threading
from pathlib import Path
from typing import Any

from psycopg2.errors import SerializationFailure

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "s11"))
import race_lab_receipt_duplicate as common  # noqa: E402

CONFIRMATION = "S11-SYNTHETIC-LAB-OPERATION-KEY-COLLISION-V1"
MAX_RETRIES = 3
THREAD_TIMEOUT_SECONDS = 35
STATEMENT_TIMEOUT_SECONDS = 20
LOCK_TIMEOUT_SECONDS = 15


def snapshot(env, order_ids: tuple[int, int], store_id: int, key: str) -> dict[str, Any]:
    orders = env["ydental.lab.order"].sudo().browse(order_ids).exists()
    if len(orders) != 2 or any(order.ydental_store_id.id != store_id for order in orders):
        raise common.Refusal("both target orders must exist in the admitted store")
    rows = []
    for order in orders.sorted("id"):
        events = env["ydental.lab.event"].sudo().search_read(
            [("ydental_order_id", "=", order.id), ("ydental_kind", "=", "code_bound")],
            ["id", "ydental_actor_id"], order="id",
        )
        audits = env["ydental.access.audit"].sudo().search_read(
            [("ydental_store_id", "=", store_id), ("ydental_event", "=", "lab.code_bound"),
             ("ydental_target_model", "=", "ydental.lab.order"),
             ("ydental_target_id", "=", order.id)], ["id", "ydental_user_id"], order="id",
        )
        rows.append({
            "order_id": order.id,
            "internal_code": order.ydental_internal_code,
            "source_event_id": order.ydental_source_event_id.id,
            "package_code": order.ydental_package_code or None,
            "code_bound_events": events,
            "code_bound_audits": audits,
        })
    operations = env["ydental.lab.operation"].sudo().search_read(
        [("ydental_store_id", "=", store_id), ("ydental_key", "=", key)],
        ["id", "ydental_fingerprint", "ydental_result", "ydental_actor_id"], order="id",
    )
    return {"orders": rows, "operations": operations}


def validate_targets(env, order_ids: tuple[int, int], store_id: int,
                     key: str, codes: list[str]) -> dict[str, Any]:
    before = snapshot(env, order_ids, store_id, key)
    if before["operations"]:
        raise common.Refusal("random operation key unexpectedly exists")
    orders = env["ydental.lab.order"].sudo().browse(order_ids).exists().sorted("id")
    if (len({order.ydental_source_event_id.id for order in orders}) != 2 or
            any(not (order.ydental_internal_code or "").startswith("S11-") or
                order.ydental_parent_order_id or order.ydental_package_code for order in orders)):
        raise common.Refusal("targets must be distinct, unbound, root S11 synthetic orders")
    if env["ydental.lab.order"].sudo().search_count([("ydental_package_code", "in", codes)]):
        raise common.Refusal("generated package code unexpectedly exists")
    return before


def worker(registry, api, retryable_error, actor_id: int, session_key: str,
           order_id: int, code: str, key: str, barrier: threading.Barrier,
           results: list[dict[str, Any]]) -> None:
    backend = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with registry.cursor() as cr:
                cr.execute("SET LOCAL statement_timeout = %s", [f"{STATEMENT_TIMEOUT_SECONDS}s"])
                cr.execute("SET LOCAL lock_timeout = %s", [f"{LOCK_TIMEOUT_SECONDS}s"])
                cr.execute("SELECT pg_backend_pid()")
                backend = backend or cr.fetchone()[0]
                env = api.Environment(cr, actor_id, {})
                access = env["ydental.access.service"]
                session = access._existing_session_for_key(session_key)
                if not session:
                    raise common.Refusal("worker session disappeared before the action")
                bound = access._bind(session)
                if attempt == 1:
                    barrier.wait(timeout=THREAD_TIMEOUT_SECONDS)
                try:
                    response = bound.env["ydental.lab.service"]._operate(
                        "bind_code", {"order_id": order_id, "code": code}, key)
                    result = {"kind": response.get("result"), "order_id": response.get("order_id")}
                except (SerializationFailure, retryable_error):
                    raise
                except BaseException as error:
                    if type(error).__name__ == "UserError" and "version_conflict:" in str(error):
                        result = {"kind": "version_conflict"}
                    else:
                        result = {"kind": "action_error", "error_type": type(error).__name__}
                cr.commit()
                results.append({"backend_pid": backend, "attempts": attempt, **result})
                return
        except (SerializationFailure, retryable_error):
            if attempt == MAX_RETRIES:
                results.append({"backend_pid": backend, "attempts": attempt,
                                "kind": "retry_exhausted"})
        except BaseException as error:
            results.append({"backend_pid": backend, "attempts": attempt,
                            "kind": "worker_error", "error_type": type(error).__name__})
            return


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--actor-id", required=True, type=int)
    parser.add_argument("--store-id", required=True, type=int)
    parser.add_argument("--order-ids", required=True, nargs=2, type=int)
    parser.add_argument("--confirm", required=True)
    args = parser.parse_args()
    if args.confirm != CONFIRMATION or min(args.actor_id, args.store_id, *args.order_ids) <= 0:
        raise common.Refusal("explicit confirmation and positive IDs are required")
    if len(args.candidate) != 40 or any(c not in "0123456789abcdef" for c in args.candidate):
        raise common.Refusal("candidate must be a full lowercase commit SHA")

    launcher, runtime, admission, database, branch, commit = common.load_admitted_runtime(args.candidate)
    launcher.validate_loopback_port()
    api, Registry = common.configure_odoo(launcher, database)
    from odoo.exceptions import ConcurrencyError  # noqa: PLC0415

    registry = Registry(database["name"])
    order_ids = tuple(args.order_ids)
    key = "s11-lab-key-collision-" + secrets.token_hex(16)
    codes = ["S11-RACE-" + secrets.token_hex(12).upper() for _ in order_ids]
    with registry.cursor() as cr:
        identity = common.readonly_identity(cr, launcher, database)
        env = api.Environment(cr, args.actor_id, {})
        common.validate_actor(env, admission, args.actor_id, args.store_id)
        before = validate_targets(env, order_ids, args.store_id, key, codes)
        cr.rollback()

    race_id = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(4)
    receipt_path = launcher.PRIVATE_ROOT / "races" / f"{race_id}-lab-operation-key-collision.json"
    session_keys = [secrets.token_urlsafe(32), secrets.token_urlsafe(32)]
    receipt: dict[str, Any] = {
        "schema": "YD-S11-LAB-OPERATION-KEY-COLLISION-V1",
        "plan_id": launcher.PLAN_ID, "candidate_commit": commit, "branch": branch,
        "scope_id": runtime["scope"]["id"], "scope_expires_at_utc": runtime["scope"]["expires_at_utc"],
        "database_identity": identity, "actor_id": args.actor_id, "store_id": args.store_id,
        "order_ids": order_ids,
        "code_sha256": [hashlib.sha256(code.encode()).hexdigest() for code in codes],
        "session_key_sha256": [hashlib.sha256(key_value.encode()).hexdigest() for key_value in session_keys],
        "operation_key_sha256": hashlib.sha256(key.encode()).hexdigest(),
        "before": before, "phase": "READY_BEFORE_SESSIONS", "business_mutation_started": False,
        "started_at_utc": dt.datetime.now(dt.UTC).isoformat(),
    }
    common.write_private(receipt_path, receipt)
    session_ids = []
    for session_key in session_keys:
        session_ids.append(common.prepare_session(registry, api, args.actor_id, args.store_id, session_key))
        receipt["session_ids"] = session_ids
        receipt["phase"] = "SESSION_SETUP_COMMITTED"
        common.write_private(receipt_path, receipt)
    receipt["phase"] = "TWO_CONNECTION_KEY_COLLISION_PENDING"
    receipt["business_mutation_started"] = True
    common.write_private(receipt_path, receipt)

    barrier = threading.Barrier(2)
    results: list[dict[str, Any]] = []
    threads = [threading.Thread(
        target=worker,
        args=(registry, api, ConcurrencyError, args.actor_id, session_keys[index],
              order_ids[index], codes[index], key, barrier, results),
        name=f"s11-key-collision-{index + 1}", daemon=True,
    ) for index in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(THREAD_TIMEOUT_SECONDS + 5)
    if any(thread.is_alive() for thread in threads):
        receipt.update({"phase": "WORKER_TIMEOUT_REQUIRES_READBACK", "worker_results": results})
        common.write_private(receipt_path, receipt)
        raise common.Refusal(f"bounded race timed out; independently read back before retry: {receipt_path}")

    with registry.cursor() as cr:
        cr.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        env = api.Environment(cr, args.actor_id, {})
        after = snapshot(env, order_ids, args.store_id, key)
        cr.rollback()

    outcomes = sorted(row["kind"] for row in results)
    changed = [row for row in after["orders"] if row["package_code"]]
    accepted = next((row for row in results if row["kind"] == "accepted"), {})
    winner = next((row for row in after["orders"]
                   if row["order_id"] == accepted.get("order_id")), {})
    passed = (len(results) == 2 and len({row["backend_pid"] for row in results}) == 2 and
              outcomes == ["accepted", "version_conflict"] and len(changed) == 1 and
              len(after["operations"]) == 1 and
              sum(len(row["code_bound_events"]) for row in after["orders"]) == 1 and
              sum(len(row["code_bound_audits"]) for row in after["orders"]) == 1 and
              winner.get("package_code") == codes[order_ids.index(accepted.get("order_id", -1))] and
              len(winner.get("code_bound_events", [])) == 1 and
              len(winner.get("code_bound_audits", [])) == 1 and
              all(not row["package_code"] and not row["code_bound_events"] and
                  not row["code_bound_audits"] for row in after["orders"] if row != winner))
    receipt.update({
        "phase": "READBACK_COMPLETE", "worker_results": results, "after": after,
        "two_distinct_postgresql_backends": len({row["backend_pid"] for row in results}) == 2,
        "one_code_binding_and_event": len(changed) == 1 and
            sum(len(row["code_bound_events"]) for row in after["orders"]) == 1 and
            sum(len(row["code_bound_audits"]) for row in after["orders"]) == 1,
        "one_operation_row": len(after["operations"]) == 1,
        "outcome": "PASS" if passed else "FAIL",
        "finished_at_utc": dt.datetime.now(dt.UTC).isoformat(),
    })
    common.write_private(receipt_path, receipt)
    print(json.dumps({"receipt": str(receipt_path), "outcome": receipt["outcome"],
                      "worker_outcomes": outcomes,
                      "two_distinct_postgresql_backends": receipt["two_distinct_postgresql_backends"],
                      "one_code_binding_and_event": receipt["one_code_binding_and_event"],
                      "one_operation_row": receipt["one_operation_row"]}, sort_keys=True))
    return 0 if passed else 3


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"S11 lab operation-key collision stopped: {type(error).__name__}: {error}", file=sys.stderr)
        raise SystemExit(2)

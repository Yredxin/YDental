#!/usr/bin/env python3
"""Race two real PostgreSQL requests for one S11 physical laboratory receipt.

This deliberately tests duplicate receipt delivery only. Both ordinary,
store-scoped workers submit the same stable request key and payload against one
already-sent synthetic work order. The guarded lab service should commit one
physical-receipt event and return the persisted result for the duplicate.

Cancellation and put-away cannot validly race on the same initial order:
cancellation accepts draft/sent/processing, while put-away requires received.
This harness does not manufacture an impossible state or race a later action.
It never starts Odoo, installs/upgrades modules, creates stock, or touches old
S10 objects. Evidence is private under the ignored .local/s11/races directory.
"""

from __future__ import annotations

# Operational CLI follows race_package_code.py conventions.
# ruff: noqa: TRY002, TRY003, TRY301, EM101, BLE001, T201
import argparse
import datetime as dt
import hashlib
import json
import os
import secrets
import stat
import sys
import threading
from pathlib import Path
from typing import Any

from psycopg2.errors import SerializationFailure

REPO_ROOT = Path(__file__).resolve().parents[2]
PRIVATE_ROOT = REPO_ROOT / ".local" / "s11"
RACE_ROOT = PRIVATE_ROOT / "races"
ODOO_ROOT = REPO_ROOT.parent
CONFIRMATION = "S11-SYNTHETIC-LAB-RECEIPT-DUPLICATE-RACE-V1"
THREAD_TIMEOUT_SECONDS = 35
STATEMENT_TIMEOUT_SECONDS = 20
LOCK_TIMEOUT_SECONDS = 15
MAX_SERIALIZATION_RETRIES = 3


class Refusal(RuntimeError):
    """A fail-closed preflight or race refusal."""


def utc_now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def require_private_directory(path: Path) -> None:
    if path.exists():
        info = path.lstat()
        if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or
                stat.S_IMODE(info.st_mode) & 0o077):
            raise Refusal("private S11 race evidence directory has unsafe owner or permissions")
    else:
        path.mkdir(mode=0o700, parents=True)
    os.chmod(path, 0o700)


def json_default(value: Any) -> Any:
    if isinstance(value, (dt.datetime, dt.date)):
        return value.isoformat()
    raise TypeError(f"unsupported private S11 receipt value: {type(value).__name__}")


def write_private(path: Path, data: dict[str, Any]) -> None:
    require_private_directory(path.parent)
    temp = path.with_name(path.name + ".tmp-" + secrets.token_hex(6))
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, sort_keys=True, indent=2, default=json_default)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
        os.chmod(path, 0o600)
        directory_fd = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        try:
            temp.unlink()
        except FileNotFoundError:
            pass


def load_admitted_runtime(candidate: str):
    sys.path.insert(0, str(REPO_ROOT / "scripts" / "s11"))
    import launcher  # noqa: PLC0415

    runtime, admission, database, branch, commit = launcher.validate_pair()
    if commit != candidate or branch != launcher.EXPECTED_BRANCH:
        raise Refusal("candidate must equal the clean, currently admitted S11 commit")
    if launcher.ACTIVE.exists():
        raise Refusal("an owned S11 service marker exists; resolve it before direct database work")
    return launcher, runtime, admission, database, branch, commit


def configure_odoo(launcher, database: dict[str, Any]):
    sys.path.insert(0, str(launcher.ODOO_ROOT))
    from odoo import api  # noqa: PLC0415
    from odoo.orm.registry import Registry  # noqa: PLC0415
    from odoo.tools import config  # noqa: PLC0415

    config["addons_path"] = ",".join((str(launcher.ODOO_ROOT / "odoo" / "addons"), str(REPO_ROOT)))
    config["data_dir"] = str(PRIVATE_ROOT / "data")
    config["db_host"] = database["host"]
    config["db_port"] = str(database["port"])
    config["db_user"] = database["user"]
    config["db_password"] = database["password"]
    config["db_name"] = database["name"]
    config["dbfilter"] = "^" + database["name"] + "$"
    config["list_db"] = False
    return api, Registry


def readonly_identity(cr, launcher, database: dict[str, Any]) -> dict[str, Any]:
    cr.execute("SET TRANSACTION READ ONLY")
    cr.execute("""
        SELECT current_database(), d.oid::bigint, current_user,
               r.rolsuper, r.rolcreatedb, r.rolcreaterole,
               r.rolreplication, r.rolbypassrls, r.rolcanlogin,
               pg_get_userbyid(d.datdba),
               EXISTS (SELECT 1 FROM pg_auth_members m
                        WHERE m.member = r.oid OR m.roleid = r.oid),
               (SELECT count(*) FROM pg_database other
                 WHERE other.datname <> d.datname AND other.datdba = r.oid),
               (SELECT count(*) FROM pg_database other
                  CROSS JOIN LATERAL aclexplode(
                      COALESCE(other.datacl, acldefault('d', other.datdba))) acl
                 WHERE other.datname <> d.datname AND acl.grantee = r.oid
                   AND acl.privilege_type IN ('CONNECT', 'CREATE', 'TEMPORARY')),
               (SELECT system_identifier::text FROM pg_control_system())
          FROM pg_database d
          JOIN pg_roles r ON r.rolname = current_user
         WHERE d.datname = current_database()
    """)
    row = cr.fetchone()
    if not row:
        raise Refusal("database identity query returned no row")
    (name, oid, role, is_super, can_createdb, can_createrole, can_replicate,
     can_bypass_rls, can_login, database_owner, has_role_membership,
     other_owned_databases, other_database_grants, cluster_ref) = row
    expected = (launcher.EXPECTED_DATABASE, launcher.EXPECTED_OID,
                launcher.EXPECTED_CLUSTER, database["user"])
    if (name, oid, cluster_ref, role) != expected:
        raise Refusal("live database identity differs from the current S11 admission contract")
    if (is_super or can_createdb or can_createrole or can_replicate or can_bypass_rls or
            not can_login or database_owner != role or has_role_membership or
            other_owned_databases or other_database_grants):
        raise Refusal("database role has privileges or ownership outside its dedicated S11 scratch boundary")
    return {"database_name": name, "database_oid": oid, "cluster_ref": cluster_ref,
            "database_role": role, "role_is_superuser": is_super,
            "role_createdb": can_createdb, "role_createrole": can_createrole,
            "role_replication": can_replicate, "role_bypassrls": can_bypass_rls,
            "role_can_login": can_login, "scratch_is_role_owned_database": database_owner == role,
            "role_membership_absent": not has_role_membership,
            "other_owned_databases": other_owned_databases,
            "other_explicit_database_grants": other_database_grants,
            "public_connect_acl_unchanged": True}


def snapshot(env, order_id: int, store_id: int, *, after_race: bool = False) -> dict[str, Any]:
    order = env["ydental.lab.order"].sudo().browse(order_id).exists()
    if not order or order.ydental_store_id.id != store_id:
        raise Refusal("target synthetic laboratory order is absent or outside the admitted store")
    if not (order.ydental_internal_code or "").startswith("S11-"):
        raise Refusal("receipt race is restricted to an S11-prefixed synthetic work order")
    allowed_states = ("sent", "processing", "received") if after_race else ("sent", "processing")
    if order.state not in allowed_states:
        raise Refusal("target state is outside the bounded duplicate receipt race contract")
    if not order.ydental_lot_id or order.ydental_lot_id.product_id != order.ydental_product_id:
        raise Refusal("target must have a matching prosthesis lot before receipt")
    events = env["ydental.lab.event"].sudo().search_read(
        [("ydental_order_id", "=", order.id)],
        ["id", "ydental_kind", "ydental_inventory_event_id", "ydental_purchase_line_id",
         "ydental_vendor_cost", "ydental_recorded_at", "ydental_actor_id"],
        order="id",
    )
    if not any(row["ydental_kind"] == "sent" for row in events):
        raise Refusal("target needs a committed dispatch event before physical receipt")
    if not after_race and any(row["ydental_kind"] in ("received", "putaway") for row in events):
        raise Refusal("target already has a receipt or put-away event; do not replay it")
    if after_race and (sum(row["ydental_kind"] == "received" for row in events) != 1 or
                       any(row["ydental_kind"] == "putaway" for row in events)):
        raise Refusal("post-race target must have exactly one receipt and no put-away event")
    if not after_race and (order.ydental_inventory_event_id or order.ydental_followup_id):
        raise Refusal("target already links put-away stock or passive follow-up")

    stock_events = env["ydental.inventory.event"].sudo().search_read(
        [("ydental_store_id", "=", store_id),
         ("ydental_source_namespace", "=", "warehouse"),
         ("ydental_source_key", "=", "lab-receipt-%s" % order.id)],
        ["id", "ydental_kind", "ydental_quantity", "ydental_source_key"], order="id",
    )
    quants = env["stock.quant"].sudo().search_read(
        [("product_id", "=", order.ydental_product_id.id),
         ("lot_id", "=", order.ydental_lot_id.id)],
        ["id", "location_id", "quantity", "reserved_quantity"], order="location_id,id",
    )
    followups = env["ydental.followup"].sudo().search_read(
        [("ydental_lab_order_id", "=", order.id)],
        ["id", "state", "ydental_lab_cycle_key"], order="id",
    )
    receipt_audits = env["ydental.access.audit"].sudo().search_read(
        [("ydental_store_id", "=", store_id), ("ydental_event", "=", "lab.received"),
         ("ydental_target_model", "=", "ydental.lab.order"),
         ("ydental_target_id", "=", order.id)], ["id", "ydental_user_id"], order="id",
    )
    if not after_race and (stock_events or followups or receipt_audits):
        raise Refusal("target has pre-existing put-away stock, passive follow-up, or receipt audit; do not replay")
    purchase_line = order.ydental_purchase_line_id.sudo()
    cost = False
    if purchase_line:
        cost = {"line_id": purchase_line.id, "purchase_id": purchase_line.order_id.id,
                "purchase_state": purchase_line.order_id.state,
                "quantity": purchase_line.product_qty, "unit_price": purchase_line.price_unit,
                "subtotal": purchase_line.price_subtotal, "total": purchase_line.price_total,
                "currency_id": purchase_line.order_id.currency_id.id}
    return {
        "order_id": order.id, "store_id": order.ydental_store_id.id,
        "state": order.state, "internal_code": order.ydental_internal_code,
        "parent_order_id": order.ydental_parent_order_id.id or None,
        "rework_no": order.ydental_rework_no, "product_id": order.ydental_product_id.id,
        "lot_id": order.ydental_lot_id.id, "quantity": order.ydental_quantity,
        "receipt_at": order.ydental_receipt_at.isoformat() if order.ydental_receipt_at else None,
        "receipt_actor_id": order.ydental_receipt_actor_id.id or None,
        "inventory_event_id": order.ydental_inventory_event_id.id or None,
        "followup_id": order.ydental_followup_id.id or None,
        "lab_events": events, "inventory_events": stock_events, "stock_quants": quants,
        "followups": followups, "receipt_audits": receipt_audits, "purchase_cost_source": cost,
    }


def validate_actor(env, admission: dict[str, Any], actor_id: int, store_id: int) -> None:
    user = env["res.users"].browse(actor_id).exists()
    if not user or not user._is_internal() or user.share or env.su:
        raise Refusal("actor must be an existing ordinary internal user")
    access = env["ydental.access.service"]
    if access._is_group_manager():
        raise Refusal("use a store-scoped warehouse operator, not a group manager")
    store = env["ydental.access.store"].sudo().browse(store_id).exists()
    membership = access._membership(actor_id, store_id)
    levels = access._levels(membership) if membership else {}
    if (not store or not store.active or not membership or not membership.ydental_employee_id.active or
            levels.get("medical") != "write" or levels.get("warehouse") != "write" or
            store.company_id.id not in user.company_ids.ids or
            store_id not in admission["allowed_store_ids"] or
            store.company_id.id not in admission["allowed_company_ids"]):
        raise Refusal("actor is outside the independently admitted medical/warehouse store scope")


def prepare_session(registry, api, actor_id: int, store_id: int, key: str) -> int:
    with registry.cursor() as cr:
        env = api.Environment(cr, actor_id, {})
        access = env["ydental.access.service"]
        session = access._session_for_key(key)
        access._bind(session)._switch(store_id)
        session_id = session.id
        cr.commit()
    return session_id


def _worker(registry, api, retryable_error, actor_id: int, session_key: str, order_id: int,
            action_key: str, barrier: threading.Barrier, results: list[dict[str, Any]]) -> None:
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
                    raise Refusal("worker session disappeared before the receipt action")
                bound = access._bind(session)
                if attempt == 1:
                    barrier.wait(timeout=THREAD_TIMEOUT_SECONDS)
                try:
                    response = bound.env["ydental.lab.service"]._operate(
                        "receive", {"order_id": order_id}, action_key)
                    outcome = {"kind": response.get("result"), "state": response.get("state"),
                               "order_id": response.get("order_id")}
                except (SerializationFailure, retryable_error):
                    raise
                except BaseException as error:
                    outcome = {"kind": "action_error", "error_type": type(error).__name__}
                cr.commit()
                results.append({"backend_pid": first_pid, "attempts": attempt, **outcome})
                return
        except (SerializationFailure, retryable_error):
            # PostgreSQL or Odoo explicitly marked this request for retry; only
            # these known non-commit outcomes are eligible for bounded retry.
            if attempt == MAX_SERIALIZATION_RETRIES:
                results.append({"backend_pid": first_pid, "attempts": attempt,
                                "kind": "serialization_retry_exhausted"})
        except BaseException as error:
            results.append({"backend_pid": first_pid, "attempts": attempt,
                            "kind": "worker_error", "error_type": type(error).__name__})
            return


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, help="full admitted S11 commit SHA")
    parser.add_argument("--actor-id", type=int, required=True, help="ordinary store-scoped warehouse user ID")
    parser.add_argument("--store-id", type=int, required=True, help="admitted S11 store ID")
    parser.add_argument("--order-id", type=int, required=True, help="sent/processing S11 synthetic order ID")
    parser.add_argument("--confirm", required=True)
    args = parser.parse_args()
    if args.confirm != CONFIRMATION or min(args.actor_id, args.store_id, args.order_id) <= 0:
        raise Refusal("explicit confirmation and positive actor/store/order IDs are required")
    if len(args.candidate) != 40 or any(char not in "0123456789abcdef" for char in args.candidate):
        raise Refusal("candidate must be a full lowercase 40-character commit SHA")

    launcher, runtime, admission, database, branch, commit = load_admitted_runtime(args.candidate)
    api, Registry = configure_odoo(launcher, database)
    from odoo.exceptions import ConcurrencyError  # noqa: PLC0415

    retryable_error = ConcurrencyError
    registry = Registry(database["name"])
    with registry.cursor() as cr:
        identity = readonly_identity(cr, launcher, database)
        env = api.Environment(cr, args.actor_id, {})
        validate_actor(env, admission, args.actor_id, args.store_id)
        module_rows = env["ir.module.module"].sudo().search_read(
            [("name", "in", ["ydental_lab", "ydental_followup"]), ("state", "=", "installed")],
            ["name", "state"],
        )
        if {row["name"] for row in module_rows} != {"ydental_lab", "ydental_followup"}:
            raise Refusal("required S11 lab and follow-up modules must already be installed")
        before = snapshot(env, args.order_id, args.store_id)
        cr.rollback()

    race_id = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(4)
    receipt_path = RACE_ROOT / f"{race_id}-lab-receipt-duplicate.json"
    action_key = "s11-receive-race-" + secrets.token_hex(18)
    session_keys = [secrets.token_urlsafe(32), secrets.token_urlsafe(32)]
    phase: dict[str, Any] = {
        "schema": "YD-S11-LAB-RECEIPT-DUPLICATE-RACE-V1",
        "plan_id": launcher.PLAN_ID, "candidate_commit": commit, "branch": branch,
        "scope_id": runtime["scope"]["id"],
        "scope_expires_at_utc": runtime["scope"]["expires_at_utc"],
        "database_identity": identity, "actor_id": args.actor_id, "store_id": args.store_id,
        "order_id": args.order_id, "session_ids": [],
        "session_key_sha256": [hashlib.sha256(key.encode()).hexdigest() for key in session_keys],
        "action_key_sha256": hashlib.sha256(action_key.encode()).hexdigest(),
        "operation": "receive", "request_payload": {"order_id": args.order_id},
        "before": before, "phase": "READY_BEFORE_RACE", "business_mutation_started": False,
        "started_at_utc": utc_now(),
    }
    write_private(receipt_path, phase)
    for index, session_key in enumerate(session_keys, 1):
        session_id = prepare_session(registry, api, args.actor_id, args.store_id, session_key)
        phase["session_ids"].append(session_id)
        phase["phase"] = "SESSION_SETUP_COMMITTED"
        phase["session_setup_count"] = index
        phase["session_checkpoint_at_utc"] = dt.datetime.now(dt.UTC).isoformat()
        write_private(receipt_path, phase)
    phase["phase"] = "SESSION_SETUP_COMPLETE"
    write_private(receipt_path, phase)
    phase["phase"] = "TWO_CONNECTION_RECEIPT_RACE_PENDING"
    phase["business_mutation_started"] = True
    phase["mutation_started_at_utc"] = utc_now()
    write_private(receipt_path, phase)

    barrier = threading.Barrier(2)
    results: list[dict[str, Any]] = []
    threads = [threading.Thread(
        target=_worker,
        args=(registry, api, retryable_error, args.actor_id, session_keys[index], args.order_id,
              action_key, barrier, results),
        name=f"s11-receipt-race-{index + 1}", daemon=True,
    ) for index in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(THREAD_TIMEOUT_SECONDS + 5)
    if any(thread.is_alive() for thread in threads):
        phase.update({"phase": "WORKER_TIMEOUT_REQUIRES_READBACK", "worker_results": results,
                      "finished_at_utc": utc_now()})
        write_private(receipt_path, phase)
        raise Refusal(f"bounded race timed out; preserve receipt and independently read back before any retry: {receipt_path}")
    phase.update({"phase": "WORKERS_COMPLETE_READBACK_PENDING", "worker_results": results})
    write_private(receipt_path, phase)

    with registry.cursor() as cr:
        cr.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        env = api.Environment(cr, args.actor_id, {})
        after = snapshot(env, args.order_id, args.store_id, after_race=True)
        operations = env["ydental.lab.operation"].sudo().search_read(
            [("ydental_store_id", "=", args.store_id),
             ("ydental_key", "=", action_key)],
            ["id", "ydental_fingerprint", "ydental_result", "ydental_actor_id"])
        audit = after["receipt_audits"]
        cr.rollback()
    phase.update({"phase": "POST_RACE_READBACK_COMPLETE", "after": after,
                  "committed_operation_rows": operations, "matching_audit_rows": audit})
    write_private(receipt_path, phase)

    outcomes = sorted(row.get("kind") for row in results)
    received_events = [row for row in after["lab_events"] if row["ydental_kind"] == "received"]
    expected_ids = {"order_id": args.order_id, "state": "received", "inventory_event_id": False}
    one_receipt_delta = (len(received_events) == 1 and len(after["lab_events"]) == len(before["lab_events"]) + 1 and
                         after["state"] == "received" and after["receipt_at"] and
                         after["receipt_actor_id"] == args.actor_id and
                         received_events[0]["ydental_actor_id"][0] == args.actor_id)
    one_operation = (len(operations) == 1 and
                     operations[0]["ydental_result"] == expected_ids and
                     operations[0]["ydental_actor_id"][0] == args.actor_id and
                     operations[0]["ydental_fingerprint"] == hashlib.sha256(
                         json.dumps(["receive", args.store_id, {"order_id": args.order_id}],
                                    sort_keys=True, ensure_ascii=True).encode()).hexdigest())
    one_audit = len(audit) == 1 and audit[0]["ydental_user_id"][0] == args.actor_id
    pids = [row.get("backend_pid") for row in results]
    passed = (len(results) == 2 and len(set(pids)) == 2 and
              outcomes == ["accepted", "already_accepted"] and one_receipt_delta and
              all(row.get("state") == "received" and row.get("order_id") == args.order_id
                  for row in results) and
              one_operation and one_audit and
              after["inventory_event_id"] is None and after["followup_id"] is None and
              after["stock_quants"] == before["stock_quants"] and
              after["inventory_events"] == before["inventory_events"] and
              after["purchase_cost_source"] == before["purchase_cost_source"])
    phase.update({
        "phase": "READBACK_COMPLETE", "worker_results": results,
        "two_distinct_postgresql_backends": len(set(pids)) == 2,
        "after": after, "committed_operation_rows": operations, "matching_audit_rows": audit,
        "one_physical_receipt_event": one_receipt_delta,
        "one_idempotency_operation": one_operation, "one_matching_audit": one_audit,
        "stock_and_purchase_cost_unchanged": (
            after["stock_quants"] == before["stock_quants"] and
            after["inventory_events"] == before["inventory_events"] and
            after["purchase_cost_source"] == before["purchase_cost_source"]),
        "outcome": "PASS" if passed else "FAIL", "finished_at_utc": utc_now(),
    })
    write_private(receipt_path, phase)
    print(json.dumps({"receipt": str(receipt_path), "outcome": phase["outcome"],
                      "two_distinct_postgresql_backends": phase["two_distinct_postgresql_backends"],
                      "one_physical_receipt_event": one_receipt_delta,
                      "one_idempotency_operation": one_operation,
                      "stock_and_purchase_cost_unchanged": phase["stock_and_purchase_cost_unchanged"]},
                     sort_keys=True))
    return 0 if passed else 3


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"S11 lab receipt duplicate race stopped: {type(error).__name__}: {error}", file=sys.stderr)
        raise SystemExit(2)

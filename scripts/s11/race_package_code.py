#!/usr/bin/env python3
"""Run an explicitly authorized two-connection S11 package-code race.

This harness binds one fresh synthetic package code against two already
committed S11 synthetic work orders. It does not create or alter orders, stock,
purchase costs, patients, clinical events, or follow-ups. Preparation of the two
orders remains a separate normal S11 workflow and their IDs are supplied
explicitly. Every business mutation is an ordinary guarded lab service action.

The harness is opt-in, never starts Odoo, checks the current S11 launcher
admission before opening PostgreSQL, requires an exact committed candidate, and
stores non-secret phase receipts beneath .local/s11/new-target-races.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import secrets
import stat
import sys
import threading
from typing import Any

from race_lab_receipt_duplicate import is_synthetic_internal_code


REPO_ROOT = Path(__file__).resolve().parents[2]
PRIVATE_ROOT = REPO_ROOT / ".local" / "s11"
RACE_ROOT = PRIVATE_ROOT / "new-target-races"
ODOO_ROOT = REPO_ROOT.parent
RUNNER_VERSION = 1
CONFIRMATION = "S11-SYNTHETIC-PACKAGE-CODE-RACE-V1"
SYNTHETIC_CODE_PREFIX = "S11-RACE-"
THREAD_TIMEOUT_SECONDS = 30


class Refusal(RuntimeError):
    """Fail-closed preflight or execution refusal."""


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def require_private_directory(path: Path) -> None:
    if path.exists():
        info = path.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
            raise Refusal(f"private evidence directory has unsafe owner or permissions: {path}")
    else:
        path.mkdir(mode=0o700, parents=True)
    os.chmod(path, 0o700)


def write_receipt(path: Path, data: dict[str, Any]) -> None:
    """Atomically write a mode-0600 JSON checkpoint without secret inputs."""
    require_private_directory(path.parent)
    temp = path.with_name(path.name + ".tmp-" + secrets.token_hex(6))
    descriptor = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(data, stream, indent=2, sort_keys=True)
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


def validate_cli(args: argparse.Namespace) -> None:
    if args.confirm != CONFIRMATION:
        raise Refusal("explicit S11 synthetic-race confirmation is required")
    if not re.fullmatch(r"[0-9a-f]{40}", args.candidate):
        raise Refusal("--candidate must be a full lowercase 40-character commit")
    if args.actor_id <= 0 or args.store_id <= 0 or args.order_a <= 0 or args.order_b <= 0:
        raise Refusal("actor, store, and order IDs must be positive integers")
    if args.order_a == args.order_b:
        raise Refusal("the two race targets must be distinct work orders")


def race_outcome_matches(race_result: dict[str, Any], readback_result: dict[str, Any]) -> bool:
    return bool(
        race_result.get("two_distinct_postgresql_backends") is True
        and race_result.get("expected_outcome_pair") is True
        and race_result.get("exactly_one_action_accepted") is True
        and readback_result.get("stock_facts_unchanged") is True
        and readback_result.get("stock_quantities_unchanged") is True
        and readback_result.get("supplier_cost_sources_unchanged") is True
        and len(readback_result.get("order_snapshot", {}).get("orders", [])) == 2
    )


def actor_has_required_grants(levels: dict[str, Any]) -> bool:
    """The lab service needs medical authority before bind_code checks warehouse authority."""
    return levels.get("medical") == "write" and levels.get("warehouse") == "write"


def load_admitted_runtime(candidate: str):
    sys.path.insert(0, str(REPO_ROOT / "scripts" / "s11"))
    import launcher  # noqa: PLC0415 - admission contract is the existing S11 launcher.

    runtime, admission, database, branch, commit = launcher.validate_pair()
    if commit != candidate:
        raise Refusal("--candidate does not equal the currently admitted committed HEAD")
    if branch != launcher.EXPECTED_BRANCH:
        raise Refusal("the S11 launcher admitted an unexpected branch")
    if launcher.ACTIVE.exists():
        raise Refusal("an S11 owned service marker exists; resolve it before direct-connection race work")
    return launcher, runtime, admission, database, branch, commit


def configure_odoo(launcher, database: dict):
    sys.path.insert(0, str(ODOO_ROOT))
    from odoo import api  # noqa: PLC0415
    from odoo.orm.registry import Registry  # noqa: PLC0415
    from odoo.tools import config  # noqa: PLC0415

    config["addons_path"] = ",".join((str(ODOO_ROOT / "odoo" / "addons"), str(REPO_ROOT)))
    config["data_dir"] = str(launcher.DATA_DIR)
    config["db_host"] = database["host"]
    config["db_port"] = str(database["port"])
    config["db_user"] = database["user"]
    config["db_password"] = database["password"]
    config["db_name"] = database["name"]
    config["dbfilter"] = "^" + database["name"] + "$"
    config["list_db"] = False
    return api, Registry


def _connection(registry):
    return registry.cursor()


def readonly_identity(cr, launcher, database: dict) -> dict[str, Any]:
    cr.execute("SET TRANSACTION READ ONLY")
    cr.execute("""
        SELECT current_database(), d.oid::bigint, current_user,
               r.rolsuper, r.rolcreatedb, r.rolcreaterole,
               (SELECT system_identifier::text FROM pg_control_system())
          FROM pg_database d
          JOIN pg_roles r ON r.rolname = current_user
         WHERE d.datname = current_database()
    """)
    row = cr.fetchone()
    if not row:
        raise Refusal("database identity query returned no row")
    name, oid, role, is_super, can_createdb, can_createrole, cluster_ref = row
    expected = (launcher.EXPECTED_DATABASE, launcher.EXPECTED_OID,
                launcher.EXPECTED_CLUSTER, database["user"])
    if (name, oid, cluster_ref, role) != expected:
        raise Refusal("live database identity differs from the S11 admission contract")
    if is_super or can_createdb or can_createrole:
        raise Refusal("live database role has cluster-wide privileges forbidden by S11 admission")
    return {"database_name": name, "database_oid": oid, "cluster_ref": cluster_ref,
            "database_role": role, "role_is_superuser": is_super,
            "role_createdb": can_createdb, "role_createrole": can_createrole}


def validate_order_sources(orders, store_id: int) -> None:
    for order in orders:
        source = order.ydental_source_event_id
        patient = order.ydental_patient_id
        if (not source or not source.id or not patient or not patient.id or
                source.state != "confirmed" or source.ydental_kind != "treatment" or
                order.ydental_store_id.id != store_id or source.ydental_store_id.id != store_id or
                source.ydental_patient_id != patient):
            raise Refusal("each order must point to its actual confirmed same-store synthetic treatment source")


def _order_snapshot(env, order_ids: tuple[int, int], store_id: int,
                    require_unbound: bool = True) -> dict[str, Any]:
    Order = env["ydental.lab.order"].sudo()
    orders = Order.browse(order_ids).exists()
    if len(orders) != 2 or set(orders.ids) != set(order_ids):
        raise Refusal("both supplied S11 work orders must exist")
    if any(order.ydental_store_id.id != store_id for order in orders):
        raise Refusal("both work orders must belong to the supplied admitted store")
    if any(not is_synthetic_internal_code(order.ydental_internal_code) for order in orders):
        raise Refusal("race targets must be explicitly S11 synthetic work orders (S11- or S11V12- prefix)")
    if any(order.state not in ("draft", "sent", "processing", "received") for order in orders):
        raise Refusal("only active synthetic work orders may be used; completed/cancelled history is protected")
    if require_unbound and any(order.ydental_package_code for order in orders):
        raise Refusal("both synthetic work orders must have no package code before the race")
    validate_order_sources(orders, store_id)

    events = env["ydental.lab.event"].sudo().search([("ydental_order_id", "in", order_ids)])
    audit = env["ydental.access.audit"].sudo().search([
        ("ydental_store_id", "=", store_id), ("ydental_target_model", "=", "ydental.lab.order"),
        ("ydental_target_id", "in", order_ids), ("ydental_event", "=", "lab.code_bound"),
    ])
    stock_event_ids = set(events.mapped("ydental_inventory_event_id").ids)
    for order in orders:
        stock_event_ids.update(order.ydental_inventory_event_id.ids)
        stock_event_ids.update(order.ydental_fit_inventory_event_id.ids)
    purchase_line_ids = [order.ydental_purchase_line_id.id or False for order in orders]
    stock_quants = []
    for order in orders:
        quant_rows = env["stock.quant"].sudo().search([
            ("product_id", "=", order.ydental_product_id.id),
            ("lot_id", "=", order.ydental_lot_id.id or False),
        ], order="location_id, id")
        stock_quants.extend({
            "product_id": row.product_id.id,
            "lot_id": row.lot_id.id or None,
            "location_id": row.location_id.id,
            "quantity": row.quantity,
            "reserved_quantity": row.reserved_quantity,
        } for row in quant_rows)
    if require_unbound and (audit or events.filtered(lambda event: event.ydental_kind == "code_bound")):
        raise Refusal("race targets already have package-code binding history")
    return {
        "orders": [{
            "id": order.id,
            "state": order.state,
            "internal_code": order.ydental_internal_code,
            "package_code": order.ydental_package_code or None,
            "product_id": order.ydental_product_id.id,
            "lot_id": order.ydental_lot_id.id or None,
            "quantity": order.ydental_quantity,
            "purchase_line_id": order.ydental_purchase_line_id.id or None,
            "source_fee_id": order.ydental_source_fee_id.id or None,
            "inventory_event_id": order.ydental_inventory_event_id.id or None,
            "fit_inventory_event_id": order.ydental_fit_inventory_event_id.id or None,
            "followup_id": order.ydental_followup_id.id or None,
            "event_ids": sorted(events.filtered(lambda event: event.ydental_order_id == order).ids),
            "event_costs": [
                {"id": event.id, "kind": event.ydental_kind,
                 "purchase_line_id": event.ydental_purchase_line_id.id or None,
                 "vendor_cost": event.ydental_vendor_cost}
                for event in events.filtered(lambda event: event.ydental_order_id == order)
            ],
        } for order in orders],
        "lab_event_count": len(events),
        "code_bind_audit_count": len(audit),
        "linked_stock_event_ids": sorted(stock_event_ids),
        "stock_quants": sorted(stock_quants, key=lambda row: (
            row["product_id"], row["lot_id"] or 0, row["location_id"],
        )),
        "purchase_line_ids": purchase_line_ids,
    }


def preflight(launcher, admission: dict, registry, api, database: dict,
              args: argparse.Namespace) -> tuple[dict, dict]:
    with _connection(registry) as cr:
        identity = readonly_identity(cr, launcher, database)
        env = api.Environment(cr, args.actor_id, {})
        if not env.user.exists() or not env.user._is_internal() or env.user.share or env.su:
            raise Refusal("the selected actor must be an existing internal user")
        access = env["ydental.access.service"]
        if access._is_group_manager():
            raise Refusal("use a store-scoped warehouse actor, not a group superuser, for this race")
        store = env["ydental.access.store"].sudo().browse(args.store_id).exists()
        if not store or not store.active:
            raise Refusal("the selected store must exist and be active")
        company_ids = env.user.sudo().company_ids.ids
        if store.company_id.id not in company_ids:
            raise Refusal("the selected actor is not authorized for the store company")
        membership = access._membership(args.actor_id, args.store_id)
        if not membership or not membership.ydental_employee_id.active:
            raise Refusal("the selected actor has no active store membership")
        levels = access._levels(membership)
        if not actor_has_required_grants(levels):
            raise Refusal("the selected actor needs medical-write and warehouse-write grants in the store")
        allowed_companies = set(admission["allowed_company_ids"])
        allowed_stores = set(admission["allowed_store_ids"])
        if store.company_id.id not in allowed_companies or store.id not in allowed_stores:
            raise Refusal("store/company is outside the independently admitted S11 scope")
        module_rows = env["ir.module.module"].sudo().search_read(
            [("name", "in", ["ydental_lab", "ydental_followup"]), ("state", "=", "installed")],
            ["name", "state"],
        )
        if {row["name"] for row in module_rows} != {"ydental_lab", "ydental_followup"}:
            raise Refusal("both S11 lab and follow-up modules must already be installed")
        before = _order_snapshot(env, (args.order_a, args.order_b), args.store_id)
        return identity, before


def _prepare_session(registry, api, actor_id: int, store_id: int, key: str) -> dict[str, Any]:
    """Create an ordinary server-bound store session for an existing authorized actor."""
    with _connection(registry) as cr:
        env = api.Environment(cr, actor_id, {})
        access = env["ydental.access.service"]
        session = access._session_for_key(key)
        access._bind(session)._switch(store_id)
        session.invalidate_recordset(["ydental_revision"])
        bound = access._bind(session)
        result = {"session_key": key, "session_id": session.id,
                  "revision": bound.env.context["ydental_binding"].revision}
        cr.commit()
        return result


def _worker(registry, api, actor_id: int, store_id: int, order_id: int,
            key: str, action_key: str, code: str, barrier: threading.Barrier,
            result_box: list[dict[str, Any]]) -> None:
    try:
        with _connection(registry) as cr:
            cr.execute("SET LOCAL statement_timeout = '20s'")
            cr.execute("SET LOCAL lock_timeout = '15s'")
            cr.execute("SELECT pg_backend_pid()")
            backend_pid = cr.fetchone()[0]
            env = api.Environment(cr, actor_id, {})
            access = env["ydental.access.service"]
            session = access._existing_session_for_key(key)
            if not session:
                raise Refusal("worker session was not committed during preflight")
            bound = access._bind(session)
            barrier.wait(timeout=THREAD_TIMEOUT_SECONDS)
            try:
                response = bound.env["ydental.lab.service"]._operate(
                    "bind_code", {"order_id": order_id, "code": code}, action_key)
                outcome = {"kind": "accepted", "order_id": order_id,
                           "state": response.get("code_bound") is True}
            except Exception as error:  # Capture one losing request without logging payloads.
                from odoo.exceptions import UserError  # noqa: PLC0415
                if isinstance(error, UserError) and "code_conflict" in str(error):
                    outcome = {"kind": "code_conflict", "order_id": order_id}
                else:
                    outcome = {"kind": "error", "order_id": order_id,
                               "error_type": type(error).__name__}
            cr.commit()
            result_box.append({"backend_pid": backend_pid, **outcome})
    except BaseException as error:
        result_box.append({"kind": "worker_error", "error_type": type(error).__name__})


def race(registry, api, args: argparse.Namespace, before: dict,
         checkpoint) -> dict[str, Any]:
    race_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(5)
    code = SYNTHETIC_CODE_PREFIX + secrets.token_hex(12).upper()
    action_keys = ["s11-code-race-" + secrets.token_hex(16) for _ in range(2)]
    sessions = [secrets.token_urlsafe(32) for _ in range(2)]
    # Session creation is an explicit, separately committed S11 scope checkpoint.
    session_receipts = []
    for index, session_key in enumerate(sessions, 1):
        session_receipts.append(_prepare_session(registry, api, args.actor_id, args.store_id, session_key))
        checkpoint({
            "phase": "SESSION_SETUP_COMMITTED",
            "session_setup_commits": [{"session_id": item["session_id"], "revision": item["revision"]}
                                       for item in session_receipts],
            "session_setup_count": index,
            "race_id": race_id,
            "synthetic_package_code": code,
        })
    results: list[dict[str, Any]] = []
    barrier = threading.Barrier(2)
    threads = [threading.Thread(
        target=_worker,
        args=(registry, api, args.actor_id, args.store_id, order_id,
              sessions[index], action_keys[index], code, barrier, results),
        name=f"s11-code-race-{index + 1}", daemon=True,
    ) for index, order_id in enumerate((args.order_a, args.order_b))]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(THREAD_TIMEOUT_SECONDS + 5)
    if any(thread.is_alive() for thread in threads):
        raise Refusal("a race worker exceeded its bounded join; preserve evidence and do not retry")
    pids = [result.get("backend_pid") for result in results if result.get("backend_pid")]
    outcomes = [result.get("kind") for result in results]
    return {
        "race_id": race_id,
        "synthetic_package_code": code,
        "order_ids": [args.order_a, args.order_b],
        "worker_backend_pids": sorted(pids),
        "session_ids": [item["session_id"] for item in session_receipts],
        "action_keys_sha256": [__import__("hashlib").sha256(key.encode()).hexdigest()
                               for key in action_keys],
        "outcomes": sorted(results, key=lambda item: item.get("order_id", 0)),
        "two_distinct_postgresql_backends": len(set(pids)) == 2,
        "expected_outcome_pair": sorted(outcomes) == ["accepted", "code_conflict"],
        "exactly_one_action_accepted": sum(result.get("state") is True for result in results) == 1,
        "_action_keys": action_keys,
        "before": before,
    }


def readback(registry, api, args: argparse.Namespace, race_result: dict[str, Any]) -> dict[str, Any]:
    with _connection(registry) as cr:
        cr.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        env = api.Environment(cr, args.actor_id, {})
        after = _order_snapshot(env, (args.order_a, args.order_b), args.store_id,
                                require_unbound=False)
        bound = env["ydental.lab.order"].sudo().search([
            ("ydental_store_id", "=", args.store_id),
            ("ydental_package_code", "=", race_result["synthetic_package_code"]),
        ])
        code_events = env["ydental.lab.event"].sudo().search([
            ("ydental_order_id", "in", [args.order_a, args.order_b]),
            ("ydental_kind", "=", "code_bound"),
        ])
        audits = env["ydental.access.audit"].sudo().search([
            ("ydental_store_id", "=", args.store_id),
            ("ydental_event", "=", "lab.code_bound"),
            ("ydental_target_model", "=", "ydental.lab.order"),
            ("ydental_target_id", "in", [args.order_a, args.order_b]),
        ])
        operations = env["ydental.lab.operation"].sudo().search([
            ("ydental_store_id", "=", args.store_id),
            ("ydental_key", "in", [
                # Only hashes are stored in public output; raw keys are kept in the in-memory closure.
                race_result["_action_keys"][0], race_result["_action_keys"][1],
            ]),
        ])
        if len(bound) != 1 or len(code_events) != 1 or len(audits) != 1 or len(operations) != 1:
            raise Refusal("independent committed readback found non-unique bind/event/audit/operation facts")
        if bound.id != code_events.ydental_order_id.id or bound.id != audits.ydental_target_id:
            raise Refusal("independent readback bind, workflow event, and audit target disagree")
        accepted = [row for row in race_result["outcomes"] if row.get("kind") == "accepted"]
        conflicts = [row for row in race_result["outcomes"] if row.get("kind") == "code_conflict"]
        if (len(accepted) != 1 or len(conflicts) != 1 or
                accepted[0].get("order_id") != bound.id or
                conflicts[0].get("order_id") == bound.id):
            raise Refusal("the race must record one accepted bind and one ordinary code conflict")
        if after["linked_stock_event_ids"] != race_result["before"]["linked_stock_event_ids"]:
            raise Refusal("package-code binding unexpectedly changed linked native stock facts")
        if after["purchase_line_ids"] != race_result["before"]["purchase_line_ids"]:
            raise Refusal("package-code binding unexpectedly changed supplier-cost sources")
        if after["stock_quants"] != race_result["before"]["stock_quants"]:
            raise Refusal("package-code binding unexpectedly changed native stock quantities")
        before_by_id = {row["id"]: row for row in race_result["before"]["orders"]}
        after_by_id = {row["id"]: row for row in after["orders"]}
        if set(before_by_id) != set(after_by_id):
            raise Refusal("independent readback order set changed")
        for order_id, old in before_by_id.items():
            new = after_by_id[order_id]
            if (order_id == bound.id and new["package_code"] != race_result["synthetic_package_code"] or
                    order_id != bound.id and new["package_code"]):
                raise Refusal("only the accepted work order may retain the raced package code")
            for field_name in ("state", "internal_code", "product_id", "lot_id", "quantity",
                               "purchase_line_id", "source_fee_id", "inventory_event_id",
                               "fit_inventory_event_id", "followup_id"):
                if new[field_name] != old[field_name]:
                    raise Refusal("package-code binding changed an unrelated laboratory source field")
            added_event_ids = set(new["event_ids"]) - set(old["event_ids"])
            if order_id == bound.id:
                if len(added_event_ids) != 1 or code_events.id not in added_event_ids:
                    raise Refusal("winner must append exactly its own package-code event")
            elif added_event_ids:
                raise Refusal("losing work order must not receive any workflow event")
            old_costs = {row["id"]: row for row in old["event_costs"]}
            new_costs = {row["id"]: row for row in new["event_costs"]}
            if any(new_costs.get(event_id) != event for event_id, event in old_costs.items()):
                raise Refusal("package-code binding changed an existing vendor-cost event snapshot")
        if after["lab_event_count"] != race_result["before"]["lab_event_count"] + 1:
            raise Refusal("the race did not append exactly one laboratory event")
        if after["code_bind_audit_count"] != 1:
            raise Refusal("the race did not append exactly one matching audit event")
        return {
            "bound_order_id": bound.id,
            "package_code": race_result["synthetic_package_code"],
            "lab_code_bind_event_id": code_events.id,
            "audit_id": audits.id,
            "operation_id": operations.id,
            "order_snapshot": after,
            "stock_facts_unchanged": True,
            "stock_quantities_unchanged": True,
            "supplier_cost_sources_unchanged": True,
        }


def execute(args: argparse.Namespace) -> int:
    validate_cli(args)
    launcher, runtime, admission, database, branch, commit = load_admitted_runtime(args.candidate)
    api, Registry = configure_odoo(launcher, database)
    registry = Registry(database["name"])

    # The complete identity, actor, module and synthetic-target checks are read-only.
    identity, before = preflight(launcher, admission, registry, api, database, args)
    receipt_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(4)
    receipt_path = RACE_ROOT / f"{receipt_id}.json"
    phase = {
        "schema": "YD-S11-PACKAGE-CODE-RACE-V1",
        "runner_version": RUNNER_VERSION,
        "plan_id": launcher.PLAN_ID,
        "candidate_commit": commit,
        "branch": branch,
        "scope_id": runtime["scope"]["id"],
        "scope_expires_at_utc": runtime["scope"]["expires_at_utc"],
        "database_identity": identity,
        "actor_id": args.actor_id,
        "store_id": args.store_id,
        "order_ids": [args.order_a, args.order_b],
        "preflight_at_utc": utc_now(),
        "preflight": "PASS_READ_ONLY",
        "before": before,
        "business_mutation_started": False,
    }
    write_receipt(receipt_path, phase)

    phase["business_mutation_started"] = True
    phase["phase"] = "TWO_SESSION_SETUP_AND_RACE_PENDING"
    phase["mutation_started_at_utc"] = utc_now()
    write_receipt(receipt_path, phase)
    def checkpoint(update: dict[str, Any]) -> None:
        phase.update(update)
        phase["checkpointed_at_utc"] = utc_now()
        write_receipt(receipt_path, phase)

    try:
        race_result = race(registry, api, args, before, checkpoint)
        phase["race"] = {key: value for key, value in race_result.items() if not key.startswith("_")}
        phase["phase"] = "RACE_WORKERS_COMMITTED"
        phase["race_committed_at_utc"] = utc_now()
        write_receipt(receipt_path, phase)
        final = readback(registry, api, args, race_result)
    except Exception as error:
        phase["phase"] = "PARTIAL_READBACK_REQUIRED"
        phase["failure_type"] = type(error).__name__
        phase["failure_summary"] = str(error)[:240]
        phase["stopped_at_utc"] = utc_now()
        write_receipt(receipt_path, phase)
        raise
    action_keys = race_result.pop("_action_keys")
    expected = race_outcome_matches(race_result, final)
    phase.update({
        "phase": "COMPLETE" if expected else "RACE_RESULT_DID_NOT_MATCH_EXPECTATION",
        "completed_at_utc": utc_now(),
        "race": {key: value for key, value in race_result.items() if not key.startswith("_")},
        "independent_readback": final,
        "action_keys_sha256": [__import__("hashlib").sha256(key.encode()).hexdigest()
                               for key in action_keys],
    })
    write_receipt(receipt_path, phase)
    print(f"S11 synthetic package-code race {phase['phase']}: receipt={receipt_path}")
    return 0 if expected else 3


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, help="exact currently admitted full Git commit")
    parser.add_argument("--actor-id", required=True, type=int, help="existing internal user with warehouse write")
    parser.add_argument("--store-id", required=True, type=int, help="store inside the fresh S11 admission")
    parser.add_argument("--order-a", required=True, type=int, help="first committed S11 synthetic work order")
    parser.add_argument("--order-b", required=True, type=int, help="second committed S11 synthetic work order")
    parser.add_argument("--confirm", required=True, help=f"must equal {CONFIRMATION}")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return execute(args)
    except Exception as error:
        print(f"S11 race refused/stopped: {type(error).__name__}: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

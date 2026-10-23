#!/usr/bin/env python3
"""Run a bounded two-connection scan of one committed S11 package code.

The scan is the real transient-model action used by the laboratory menu. It
does not receive, put away, bind, or otherwise mutate a work order. The receipt
keeps only object IDs, result IDs, and a hash of the synthetic package code.
"""

from __future__ import annotations

# Follow the operational CLI conventions in race_package_code.py.
# ruff: noqa: TRY002, TRY301, BLE001, T201
# Operational CLI output and bounded refusal exceptions follow race_package_code.py.
import argparse
import datetime as dt
import hashlib
import json
import os
import secrets
import sys
import threading
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
PRIVATE_ROOT = REPO_ROOT / ".local" / "s11"
RECEIPT_ROOT = PRIVATE_ROOT / "new-target-races"
CONFIRMATION = "S11-SYNTHETIC-LAB-SCAN-RACE-V1"
TIMEOUT_SECONDS = 20


class Refusal(RuntimeError):
    """A preflight or race result failed its fixed S11 contract."""


def write_private(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    temp = path.with_name(path.name + ".tmp-" + secrets.token_hex(6))
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, sort_keys=True, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
        os.chmod(path, 0o600)
    finally:
        try:
            temp.unlink()
        except FileNotFoundError:
            pass


def load_runtime(candidate: str):
    sys.path.insert(0, str(REPO_ROOT / "scripts" / "s11"))
    import launcher  # noqa: PLC0415

    runtime, admission, database, branch, commit = launcher.validate_pair()
    if commit != candidate or branch != launcher.EXPECTED_BRANCH:
        msg = "the exact committed S11 candidate is not currently admitted"
        raise Refusal(msg)
    if launcher.ACTIVE.exists():
        msg = "an owned S11 service marker exists; stop and resolve it first"
        raise Refusal(msg)
    return launcher, runtime, admission, database, branch, commit


def configure(launcher, database: dict[str, Any]):
    sys.path.insert(0, str(launcher.ODOO_ROOT))
    from odoo import api  # noqa: PLC0415
    from odoo.orm.registry import Registry  # noqa: PLC0415
    from odoo.tools import config  # noqa: PLC0415

    config["addons_path"] = ",".join((str(launcher.ODOO_ROOT / "odoo" / "addons"), str(REPO_ROOT)))
    config["data_dir"] = str(launcher.DATA_DIR)
    config["db_host"] = database["host"]
    config["db_port"] = str(database["port"])
    config["db_user"] = database["user"]
    config["db_password"] = database["password"]
    config["db_name"] = database["name"]
    config["dbfilter"] = "^" + database["name"] + "$"
    config["list_db"] = False
    return api, Registry


def snapshot(cr, api, order_id: int, store_id: int) -> dict[str, Any]:
    env = api.Environment(cr, 1, {})
    order = env["ydental.lab.order"].sudo().browse(order_id).exists()
    if not order or order.ydental_store_id.id != store_id:
        msg = "the target S11 synthetic order is missing or belongs to another store"
        raise Refusal(msg)
    if not (order.ydental_internal_code or "").startswith("S11-") or not order.ydental_package_code:
        msg = "the scan target must be an already-bound S11 synthetic package"
        raise Refusal(msg)
    event_rows = env["ydental.lab.event"].sudo().search_read(
        [("ydental_order_id", "=", order.id)],
        ["id", "ydental_kind", "ydental_inventory_event_id", "ydental_purchase_line_id", "ydental_vendor_cost"],
        order="id",
    )
    stock_ids = sorted({row["ydental_inventory_event_id"][0]
                        for row in event_rows if row["ydental_inventory_event_id"]})
    purchase_ids = sorted({row["ydental_purchase_line_id"][0]
                            for row in event_rows if row["ydental_purchase_line_id"]})
    quants = env["stock.quant"].sudo().search_read(
        [("product_id", "=", order.ydental_product_id.id),
         ("lot_id", "=", order.ydental_lot_id.id or False)],
        ["id", "location_id", "quantity", "reserved_quantity"], order="location_id,id",
    )
    return {
        "order_id": order.id,
        "store_id": order.ydental_store_id.id,
        "state": order.state,
        "package_code_sha256": hashlib.sha256(order.ydental_package_code.encode()).hexdigest(),
        "event_rows": event_rows,
        "inventory_event_ids": stock_ids,
        "purchase_line_ids": purchase_ids,
        "stock_quants": quants,
        "followup_id": order.ydental_followup_id.id or None,
    }


def prepare_session(registry, api, actor_id: int, store_id: int) -> str:
    key = secrets.token_urlsafe(32)
    with registry.cursor() as cr:
        env = api.Environment(cr, actor_id, {})
        access = env["ydental.access.service"]
        session = access._session_for_key(key)
        access._bind(session)._switch(store_id)
        cr.commit()
    return key


def main() -> int:  # noqa: TRY002, BLE001, T201
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--actor-id", type=int, required=True)
    parser.add_argument("--store-id", type=int, required=True)
    parser.add_argument("--order-id", type=int, required=True)
    parser.add_argument("--confirm", required=True)
    args = parser.parse_args()
    if args.confirm != CONFIRMATION or min(args.actor_id, args.store_id, args.order_id) <= 0:
        msg = "explicit confirmation and positive IDs are required"
        raise Refusal(msg)

    launcher, _runtime, admission, database, branch, commit = load_runtime(args.candidate)
    api, Registry = configure(launcher, database)
    registry = Registry(database["name"])
    with registry.cursor() as cr:
        cr.execute("SET TRANSACTION READ ONLY")
        env = api.Environment(cr, args.actor_id, {})
        user = env.user
        if not user.exists() or not user._is_internal() or user.share or env.su:
            msg = "scan actor must be an existing ordinary internal user"
            raise Refusal(msg)
        access = env["ydental.access.service"]
        if access._is_group_manager():
            msg = "use a store-scoped warehouse user, not a group manager"
            raise Refusal(msg)
        store = env["ydental.access.store"].sudo().browse(args.store_id).exists()
        membership = access._membership(args.actor_id, args.store_id)
        levels = access._levels(membership) if membership else {}
        if (not store or not store.active or not membership or not membership.ydental_employee_id.active or
                levels.get("warehouse") != "write" or store.company_id.id not in user.company_ids.ids or
                args.store_id not in admission["allowed_store_ids"] or
                store.company_id.id not in admission["allowed_company_ids"]):
            msg = "actor/store is outside the admitted warehouse scope"
            raise Refusal(msg)
        before = snapshot(cr, api, args.order_id, args.store_id)
        order = env["ydental.lab.order"].sudo().browse(args.order_id)
        code = order.ydental_package_code
        cr.rollback()

    session_keys = [prepare_session(registry, api, args.actor_id, args.store_id) for _ in range(2)]
    barrier = threading.Barrier(2)
    results: list[dict[str, Any]] = []

    def worker(index: int) -> None:
        try:
            with registry.cursor() as cr:
                cr.execute("SET LOCAL statement_timeout = '20s'")
                cr.execute("SELECT pg_backend_pid()")
                backend_pid = cr.fetchone()[0]
                env = api.Environment(cr, args.actor_id, {})
                access = env["ydental.access.service"]
                session = access._existing_session_for_key(session_keys[index])
                bound = access._bind(session)
                barrier.wait(timeout=TIMEOUT_SECONDS)
                result = bound.env["ydental.lab.code.scan"].create({"code": code}).action_scan()
                results.append({"backend_pid": backend_pid, "res_model": result.get("res_model"),
                                "res_id": result.get("res_id"), "action_type": result.get("type")})
                cr.commit()
        except Exception as error:
            results.append({"worker_error": type(error).__name__})

    threads = [threading.Thread(target=worker, args=(index,), daemon=True) for index in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(TIMEOUT_SECONDS + 5)
    if any(thread.is_alive() for thread in threads):
        msg = "scan worker exceeded bounded join; preserve state and do not retry"
        raise Refusal(msg)

    with registry.cursor() as cr:
        cr.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        after = snapshot(cr, api, args.order_id, args.store_id)
        cr.rollback()

    pids = [row.get("backend_pid") for row in results]
    passed = (len(results) == 2 and all(row.get("res_model") == "ydental.lab.order" and
                                        row.get("res_id") == args.order_id for row in results) and
              len(set(pids)) == 2 and before == after)
    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    receipt = RECEIPT_ROOT / f"{stamp}-lab-scan-race-{commit[:7]}.json"
    data = {
        "schema": "YD-S11-LAB-SCAN-RACE-V1", "plan_id": launcher.PLAN_ID,
        "candidate_commit": commit, "branch": branch,
        "database": launcher.EXPECTED_DATABASE, "database_oid": launcher.EXPECTED_OID,
        "cluster_ref": launcher.EXPECTED_CLUSTER, "actor_id": args.actor_id,
        "store_id": args.store_id, "order_id": args.order_id,
        "package_code_sha256": before["package_code_sha256"],
        "two_distinct_postgresql_backends": len(set(pids)) == 2,
        "results": results, "before": before, "after": after,
        "business_state_unchanged": before == after,
        "outcome": "PASS" if passed else "FAIL",
        "external_delivery": "NOT_INVOLVED",
        "finished_at_utc": dt.datetime.now(dt.UTC).isoformat(),
    }
    write_private(receipt, data)
    print(json.dumps({"receipt": str(receipt), "outcome": data["outcome"],
                      "two_distinct_postgresql_backends": data["two_distinct_postgresql_backends"],
                      "both_resolved_same_order": all(row.get("res_id") == args.order_id for row in results),
                      "business_state_unchanged": data["business_state_unchanged"]}, sort_keys=True))
    return 0 if passed else 3


if __name__ == "__main__":  # noqa: TRY003, BLE001, T201
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"S11 package scan race refused/stopped: {type(error).__name__}: {error}", file=sys.stderr)
        raise SystemExit(2)

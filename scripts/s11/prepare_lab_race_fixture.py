#!/usr/bin/env python3
"""Create one isolated, auditable S11 source/order chain for the lab race tests.

This is a one-shot test-fixture operation, not a general import tool. It uses
an existing unused confirmed synthetic treatment event, approved vendor,
company-matched service product, prosthesis product and lot. It creates a new
native confirmed purchase and a new laboratory order, then dispatches through
the ordinary store-scoped laboratory service. Every committing phase is
checkpointed privately before the next phase; uncertain phases must be read
back independently and must never be blindly replayed.
"""

from __future__ import annotations

# Operational CLI follows race_package_code.py conventions.
# ruff: noqa: TRY002, TRY003, TRY301, EM101, BLE001, T201
import argparse
import datetime as dt
import hashlib
import json
import math
import os
import re
import secrets
import stat
import sys
from typing import Any

import race_lab_receipt_duplicate as common

CONFIRMATION = "S11-SYNTHETIC-LAB-RACE-FIXTURE-V1"
EXPECTED_SYNTHETIC_SOURCE_EVENT_ID = 187
RECEIPT_ROOT = common.PRIVATE_ROOT / "fixtures"
_S11_TOKEN = re.compile(r"(?<![A-Za-z0-9])S11(?![A-Za-z0-9])", re.IGNORECASE)
_SYNTHETIC_MARKER = re.compile(
    r"(?<![A-Za-z])(?:synthetic|test|fixture)(?![A-Za-z])|合成|测试", re.IGNORECASE,
)


def utc_now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def require_order_actor(env, admission: dict[str, Any], actor_id: int, store_id: int) -> None:
    common.validate_actor(env, admission, actor_id, store_id)
    if not env.user.has_group("purchase.group_purchase_user"):
        raise common.Refusal("fixture setup actor must have native purchase-user rights to attach its own cost line")


def take_one_shot_lock(path, candidate: str, nonce: str, source_event_id: int) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump({"plan_id": "YD-S11-FOLLOWUP-LAB-V1", "candidate": candidate,
                       "source_event_id": source_event_id,
                       "fixture_nonce": nonce, "created_at_utc": utc_now()}, stream,
                      sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        try:
            os.close(fd)
        except OSError:
            pass
        raise


def source_lock_path(source_event_id: int, receipt_root=RECEIPT_ROOT):
    if type(source_event_id) is not int or source_event_id <= 0:
        raise common.Refusal("source event ID must be a positive integer")
    return receipt_root / f"lab-race-fixture-source-{source_event_id}.lock"


def source_receipt_pattern(source_event_id: int) -> str:
    if type(source_event_id) is not int or source_event_id <= 0:
        raise common.Refusal("source event ID must be a positive integer")
    return f"*-source-{source_event_id}-lab-race-fixture.json"


def legacy_lock_blocks_source(source_event_id: int) -> bool:
    return source_event_id == EXPECTED_SYNTHETIC_SOURCE_EVENT_ID


def is_explicit_synthetic_source(patient_name: str, event_source: str, event_reason: str) -> bool:
    """Require S11 and synthetic markers on both the patient and treatment source."""
    patient_marked = bool(_S11_TOKEN.search(patient_name or "")) and bool(
        _SYNTHETIC_MARKER.search(patient_name or ""),
    )
    source_marked = bool(_S11_TOKEN.search(event_source or "")) and bool(
        _SYNTHETIC_MARKER.search(event_reason or ""),
    )
    return patient_marked and source_marked


def has_prior_source_receipt(source_event_id: int, receipt_root=RECEIPT_ROOT) -> bool:
    """Match legacy receipt identity without making it a global one-shot gate."""
    if any(receipt_root.glob(source_receipt_pattern(source_event_id))):
        return True
    for path in receipt_root.glob("*-lab-race-fixture.json"):
        if re.fullmatch(r".*-source-\d+-lab-race-fixture\.json", path.name):
            continue
        try:
            receipt = json.loads(path.read_text(encoding="utf-8"))
            receipt_source_id = receipt["intent"]["source_event_id"]
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise common.Refusal(
                "legacy fixture receipt cannot be safely attributed; do not create another fixture",
            ) from error
        if type(receipt_source_id) is not int or receipt_source_id <= 0:
            raise common.Refusal(
                "legacy fixture receipt has no valid source identity; do not create another fixture",
            )
        if receipt_source_id == source_event_id:
            return True
    return False


def preflight(env, args, admission):
    from odoo import fields  # noqa: PLC0415

    store = env["ydental.access.store"].sudo().browse(args.store_id).exists()
    vendor = env["ydental.lab.vendor"].sudo().browse(args.vendor_id).exists()
    cooperation = env["ydental.lab.cooperation"].sudo().search([
        ("ydental_store_id", "=", args.store_id),
        ("ydental_vendor_id", "=", args.vendor_id), ("active", "=", True),
    ], limit=1)
    event = env["ydental.treatment.event"].sudo().browse(args.source_event_id).exists()
    patient = env["ydental.patient"].sudo().browse(args.patient_id).exists()
    prosthesis = env["product.product"].sudo().browse(args.prosthesis_product_id).exists()
    lot = env["stock.lot"].sudo().browse(args.lot_id).exists()
    service = env["product.product"].sudo().browse(args.service_product_id).exists()
    incoming = env["stock.picking.type"].sudo().browse(args.incoming_type_id).exists()
    if not store or not store.active or store.company_id.id not in admission["allowed_company_ids"]:
        raise common.Refusal("fixture store is absent or outside the admitted company scope")
    require_order_actor(env, admission, args.purchase_actor_id, args.store_id)
    common.validate_actor(env, admission, args.warehouse_actor_id, args.store_id)
    if args.warehouse_actor_id == args.purchase_actor_id:
        raise common.Refusal("use distinct ordinary purchase setup and warehouse action actors")
    if (not vendor or vendor.state != "approved" or
            not vendor.valid_until or vendor.valid_until < fields.Date.context_today(
                env["res.users"].browse(env.uid)) or
            store.company_id not in vendor.company_ids):
        raise common.Refusal("vendor must have current approved qualification for this company")
    if not cooperation or cooperation.ydental_vendor_id != vendor:
        raise common.Refusal("an active cooperation for this vendor and store is required")
    if (not patient or not event or event.state != "confirmed" or event.ydental_kind != "treatment" or
            event.ydental_store_id != store or event.ydental_category != "medical"):
        raise common.Refusal("source must be a confirmed treatment event in this selected store")
    if event.ydental_patient_id != patient:
        raise common.Refusal("source event must belong to the explicitly selected synthetic patient")
    if not is_explicit_synthetic_source(patient.name, event.ydental_source, event.ydental_reason):
        raise common.Refusal("patient and treatment source must carry explicit S11 synthetic markers")
    document = event.ydental_document_id.exists()
    if not document or document.ydental_patient_id != patient:
        raise common.Refusal("source treatment must link its existing same-patient clinical document")
    fee = env["ydental.treatment.fee"].sudo().search([("ydental_event_id", "=", event.id)], limit=2)
    if len(fee) != 1 or fee.ydental_amount <= 0 or fee.ydental_currency_id != store.company_id.currency_id:
        raise common.Refusal("source treatment must have exactly one positive same-company confirmed fee")
    if env["ydental.lab.order"].sudo().search_count([
            ("ydental_source_event_id", "=", event.id), ("ydental_parent_order_id", "=", False)]):
        raise common.Refusal("treatment event already has an initial lab order; do not reuse it")
    if (not prosthesis or not prosthesis.active or prosthesis.ydental_inventory_kind != "prosthesis" or
            (prosthesis.company_id and prosthesis.company_id != store.company_id) or
            not lot or lot.product_id != prosthesis or lot.company_id != store.company_id or
            (lot.expiration_date and lot.expiration_date <= fields.Datetime.now())):
        raise common.Refusal("prosthesis and receiving lot must match the active store company and validity")
    if (not service or not service.active or service.type != "service" or not service.purchase_ok or
            (service.company_id and service.company_id != store.company_id)):
        raise common.Refusal("vendor-cost product must be an active purchasable service in the store company")
    if (not incoming or incoming.code != "incoming" or
            incoming.warehouse_id.company_id != store.company_id):
        raise common.Refusal("native incoming picking type must belong to the store company")
    order_vals = {
        "name": "S11 synthetic concurrent laboratory lifecycle preflight",
        "ydental_source_event_id": event.id,
        "ydental_vendor_id": vendor.id,
        "ydental_product_id": prosthesis.id,
        "ydental_lot_id": lot.id,
        "ydental_quantity": 1.0, "ydental_teeth": [16],
        "ydental_material": "Synthetic race-test material",
        "ydental_instructions": "Synthetic race harness fixture only",
        "ydental_internal_code": "S11-RACE-PREFLIGHT",
        "ydental_responsible_id": args.warehouse_actor_id,
    }
    env["ydental.lab.service"]._order_identity(event.id, order_vals, store)
    return {
        "store_id": store.id, "company_id": store.company_id.id,
        "source_event_id": event.id, "patient_id": patient.id,
        "source_document_id": document.id,
        "source_fee_id": fee.id, "source_fee_amount": fee.ydental_amount,
        "source_fee_currency_id": fee.ydental_currency_id.id,
        "vendor_id": vendor.id, "vendor_partner_id": vendor.partner_id.id,
        "qualification_version": vendor.qualification_version,
        "cooperation_id": cooperation.id, "product_id": prosthesis.id,
        "lot_id": lot.id, "lot_product_id": lot.product_id.id,
        "vendor_service_product_id": service.id,
        "incoming_type_id": incoming.id,
        "quantity": 1.0, "synthetic_purchase_unit_price": args.unit_price,
        "purchase_currency_id": store.company_id.currency_id.id,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, help="full admitted S11 commit SHA")
    parser.add_argument("--purchase-actor-id", type=int, required=True)
    parser.add_argument("--warehouse-actor-id", type=int, required=True)
    parser.add_argument("--store-id", type=int, required=True)
    parser.add_argument("--vendor-id", type=int, required=True)
    parser.add_argument("--patient-id", type=int, required=True,
                        help="explicitly verified S11 synthetic patient ID for the treatment source")
    parser.add_argument("--source-event-id", type=int, required=True)
    parser.add_argument("--prosthesis-product-id", type=int, required=True)
    parser.add_argument("--lot-id", type=int, required=True)
    parser.add_argument("--service-product-id", type=int, required=True)
    parser.add_argument("--incoming-type-id", type=int, required=True)
    parser.add_argument("--unit-price", type=float, required=True)
    parser.add_argument("--confirm", required=True)
    args = parser.parse_args()
    ids = [args.purchase_actor_id, args.warehouse_actor_id, args.store_id, args.vendor_id, args.patient_id,
           args.source_event_id, args.prosthesis_product_id, args.lot_id,
           args.service_product_id, args.incoming_type_id]
    if (args.confirm != CONFIRMATION or min(ids) <= 0 or
            not math.isfinite(args.unit_price) or args.unit_price <= 0):
        raise common.Refusal("explicit confirmation, positive IDs, and nonzero synthetic price are required")
    if (len(args.candidate) != 40 or
            any(char not in "0123456789abcdef" for char in args.candidate)):
        raise common.Refusal("candidate must be a full lowercase 40-character commit SHA")
    common.require_private_directory(RECEIPT_ROOT)
    if has_prior_source_receipt(args.source_event_id):
        raise common.Refusal("a receipt already exists for this treatment source; do not replay it")
    # This historical lock belongs to event187. Preserve it as a permanent
    # stop for that source while permitting independent sources.
    if legacy_lock_blocks_source(args.source_event_id):
        lock_path = RECEIPT_ROOT / "lab-race-fixture-setup.lock"
        if lock_path.exists():
            info = lock_path.lstat()
            if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or
                    stat.S_IMODE(info.st_mode) != 0o600):
                raise common.Refusal("existing event187 fixture lock has an unsafe owner or mode")
            raise common.Refusal("the original event187 one-shot fixture lock exists; do not replay it")
    lock_path = source_lock_path(args.source_event_id)
    if lock_path.exists():
        info = lock_path.lstat()
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or
                stat.S_IMODE(info.st_mode) != 0o600):
            raise common.Refusal("existing source-specific fixture lock has an unsafe owner or mode")
        raise common.Refusal("source-specific fixture lock already exists; read back its checkpoint and do not retry")

    launcher, runtime, admission, database, branch, commit = common.load_admitted_runtime(args.candidate)
    api, Registry = common.configure_odoo(launcher, database)
    from odoo import Command, fields  # noqa: PLC0415

    registry = Registry(database["name"])
    with registry.cursor() as cr:
        identity = common.readonly_identity(cr, launcher, database)
        setup_env = api.Environment(cr, args.purchase_actor_id, {"lang": "en_US"})
        before = preflight(setup_env, args, admission)
        cr.rollback()

    nonce = secrets.token_hex(8).upper()
    take_one_shot_lock(lock_path, commit, nonce, args.source_event_id)
    purchase_key = "S11-RACE-COST-" + nonce
    internal_code = "S11-RACE-" + nonce
    send_action_key = "s11-race-fixture-send-" + nonce.lower()
    receipt_path = RECEIPT_ROOT / (utc_now().replace(":", "") +
                                   f"-source-{args.source_event_id}-lab-race-fixture.json")
    receipt: dict[str, Any] = {
        "schema": "YD-S11-LAB-RACE-FIXTURE-V1", "plan_id": launcher.PLAN_ID,
        "candidate_commit": commit, "branch": branch,
        "scope_id": runtime["scope"]["id"],
        "scope_expires_at_utc": runtime["scope"]["expires_at_utc"],
        "database_identity": identity,
        "actors": {"purchase_setup": args.purchase_actor_id,
                   "warehouse": args.warehouse_actor_id},
        "intent": before, "patient_id": args.patient_id,
        "source_event_id": args.source_event_id, "synthetic_purchase_key": purchase_key,
        "internal_order_code": internal_code,
        "send_action_key_sha256": hashlib.sha256(send_action_key.encode()).hexdigest(),
        "phase": "READY_BEFORE_NATIVE_PURCHASE", "business_mutation_started": False,
        "started_at_utc": utc_now(),
    }
    common.write_private(receipt_path, receipt)

    # Native purchase creation and confirmation are one deliberate transaction.
    # Any exception/uncertain outcome preserves the intent receipt; never retry
    # before an independent read-only search for the synthetic purchase key.
    receipt.update({"phase": "NATIVE_PURCHASE_PENDING", "business_mutation_started": True,
                    "mutation_started_at_utc": utc_now()})
    common.write_private(receipt_path, receipt)
    with registry.cursor() as cr:
        env = api.Environment(cr, args.purchase_actor_id, {"lang": "en_US"})
        store = env["ydental.access.store"].sudo().browse(args.store_id).exists()
        with_company = env["purchase.order"].with_company(store.company_id)
        incoming = env["stock.picking.type"].browse(args.incoming_type_id)
        purchase = with_company.create({
            "partner_id": args.vendor_id and env["ydental.lab.vendor"].sudo().browse(args.vendor_id).partner_id.id,
            "company_id": store.company_id.id, "currency_id": store.company_id.currency_id.id,
            "picking_type_id": incoming.id, "date_order": fields.Datetime.now(),
            "origin": purchase_key,
            "order_line": [Command.create({
                "name": "S11 synthetic race laboratory service cost " + nonce,
                "product_id": args.service_product_id, "product_qty": 1.0,
                "uom_id": env["product.product"].browse(args.service_product_id).uom_id.id,
                "price_unit": args.unit_price,
                "date_planned": fields.Datetime.now() + dt.timedelta(days=1),
            })],
        })
        purchase.button_confirm()
        line = purchase.order_line.ensure_one()
        if purchase.state not in ("purchase", "done") or line.price_subtotal <= 0:
            raise common.Refusal("native purchase did not reach confirmed state with a nonzero line")
        purchase_id, line_id = purchase.id, line.id
        actual_subtotal, actual_total = line.price_subtotal, line.price_total
        purchase_currency_id = purchase.currency_id.id
        cr.commit()
    receipt.update({"phase": "NATIVE_PURCHASE_CONFIRMED", "purchase_id": purchase_id,
                    "purchase_line_id": line_id, "purchase_state": "purchase",
                    "purchase_subtotal": actual_subtotal, "purchase_total": actual_total,
                    "purchase_currency_id": purchase_currency_id,
                    "purchase_committed_at_utc": utc_now()})
    common.write_private(receipt_path, receipt)

    # The ordinary store-scoped manager creates the clinical-source-bound draft.
    create_key = secrets.token_urlsafe(32)
    receipt.update({"phase": "CREATE_SESSION_PENDING",
                    "create_session_key_sha256": hashlib.sha256(create_key.encode()).hexdigest(),
                    "session_creation_started_at_utc": utc_now()})
    common.write_private(receipt_path, receipt)
    create_session_id = common.prepare_session(
        registry, api, args.purchase_actor_id, args.store_id, create_key)
    receipt.update({"phase": "ORDER_CREATE_PENDING", "session_ids": [create_session_id],
                    "session_creation_committed_at_utc": utc_now()})
    common.write_private(receipt_path, receipt)
    with registry.cursor() as cr:
        env = api.Environment(cr, args.purchase_actor_id, {"lang": "en_US"})
        access = env["ydental.access.service"]
        session = access._existing_session_for_key(create_key)
        scoped = access._bind(session)
        order = scoped.env["ydental.lab.order"].create({
            "name": "S11 synthetic concurrent laboratory lifecycle " + nonce,
            "ydental_source_event_id": args.source_event_id,
            "ydental_vendor_id": args.vendor_id,
            "ydental_product_id": args.prosthesis_product_id,
            "ydental_lot_id": args.lot_id,
            "ydental_purchase_line_id": line_id,
            "ydental_quantity": 1.0, "ydental_teeth": [16],
            "ydental_material": "Synthetic race-test material",
            "ydental_instructions": "Synthetic race harness fixture only",
            "ydental_internal_code": internal_code,
            "ydental_responsible_id": args.warehouse_actor_id,
            "ydental_planned_at": fields.Datetime.now(),
        })
        order_id = order.id
        cr.commit()
    receipt.update({"phase": "ORDER_DRAFT_CREATED", "order_id": order_id,
                    "order_committed_at_utc": utc_now()})
    common.write_private(receipt_path, receipt)

    send_key = secrets.token_urlsafe(32)
    receipt.update({"phase": "SEND_SESSION_PENDING", "send_session_key_sha256": hashlib.sha256(
        send_key.encode()).hexdigest(), "session_creation_started_at_utc": utc_now()})
    common.write_private(receipt_path, receipt)
    send_session_id = common.prepare_session(
        registry, api, args.warehouse_actor_id, args.store_id, send_key)
    receipt["session_ids"].append(send_session_id)
    receipt.update({"phase": "SEND_PENDING", "session_creation_committed_at_utc": utc_now(),
                    "send_started_at_utc": utc_now()})
    common.write_private(receipt_path, receipt)
    with registry.cursor() as cr:
        env = api.Environment(cr, args.warehouse_actor_id, {"lang": "en_US"})
        access = env["ydental.access.service"]
        session = access._existing_session_for_key(send_key)
        scoped = access._bind(session)
        result = scoped.env["ydental.lab.service"]._operate(
            "send", {"order_id": order_id}, send_action_key)
        if result.get("state") != "sent" or result.get("order_id") != order_id:
            raise common.Refusal("ordinary dispatch service did not return the expected sent state")
        cr.commit()
    receipt.update({"phase": "DISPATCHED", "dispatch_result": result,
                    "finished_at_utc": utc_now(), "outcome": "CREATED_AND_SENT"})
    common.write_private(receipt_path, receipt)
    print(json.dumps({"receipt": str(receipt_path), "outcome": receipt["outcome"],
                      "purchase_id": purchase_id, "purchase_line_id": line_id,
                      "order_id": order_id, "store_id": args.store_id,
                      "source_event_id": args.source_event_id}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"S11 race fixture setup stopped: {type(error).__name__}: {error}", file=sys.stderr)
        raise SystemExit(2)

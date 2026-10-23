#!/usr/bin/env python3
"""Race two real PostgreSQL requests for one S11 physical laboratory receipt.

This deliberately tests duplicate receipt delivery only. Both ordinary,
store-scoped workers submit the same stable request key and payload against one
already-sent synthetic work order. The guarded lab service should commit one
physical-receipt event and return the persisted result for the duplicate.

Cancellation versus put-away is a separate race starting from received.
This harness only records duplicate physical receipt and preserves an existing
T16 waiting plan; it does not manufacture stock or contact availability.
It never starts Odoo, installs/upgrades modules, creates stock, or touches old
S10 objects. Evidence is private under .local/s11/new-target-races.
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
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
PRIVATE_ROOT = REPO_ROOT / ".local" / "s11"
RACE_ROOT = PRIVATE_ROOT / "new-target-races"
ODOO_ROOT = REPO_ROOT.parent
CONFIRMATION = "S11-SYNTHETIC-LAB-RECEIPT-DUPLICATE-RACE-V1"
THREAD_TIMEOUT_SECONDS = 35
STATEMENT_TIMEOUT_SECONDS = 20
LOCK_TIMEOUT_SECONDS = 15
MAX_SERIALIZATION_RETRIES = 3


class Refusal(RuntimeError):
    """A fail-closed preflight or race refusal."""


def is_synthetic_internal_code(code: object) -> bool:
    return isinstance(code, str) and code.startswith(("S11-", "S11V12-"))


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
    config["data_dir"] = str(launcher.DATA_DIR)
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
    if not is_synthetic_internal_code(order.ydental_internal_code):
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
    if not after_race and order.ydental_inventory_event_id:
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
    if not after_race and (stock_events or receipt_audits):
        raise Refusal("target has pre-existing put-away stock, passive follow-up, or receipt audit; do not replay")
    purchase_line = order.ydental_purchase_line_id.sudo()
    cost = False
    if purchase_line:
        cost = {"line_id": purchase_line.id, "purchase_id": purchase_line.order_id.id,
                "purchase_state": purchase_line.order_id.state,
                "quantity": purchase_line.product_qty, "unit_price": purchase_line.price_unit,
                "subtotal": purchase_line.price_subtotal, "total": purchase_line.price_total,
                "currency_id": purchase_line.order_id.currency_id.id}
    data = {
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
    data.update(support_snapshot(env, order))
    validate_waiting_plan(data)
    return data


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
    # Put-away can schedule a postcommit arrival job. G01 requires no delivery;
    # do not trust a historical admission flag for current transport config.
    policies = env['ydental.followup.policy'].sudo().search([('ydental_store_id', '=', store_id)])
    if any(policy.ydental_enabled and policy.ydental_channel_mode != 'disabled' for policy in policies):
        raise Refusal('G01 requires the target store notification delivery disabled; do not mutate config here')
    if env['ir.mail_server'].sudo().search_count([]):
        raise Refusal('G01 requires no configured SMTP transport')


def prepare_session(registry, api, actor_id: int, store_id: int, key: str) -> int:
    with registry.cursor() as cr:
        env = api.Environment(cr, actor_id, {})
        access = env["ydental.access.service"]
        session = access._session_for_key(key)
        access._bind(session)._switch(store_id)
        session_id = session.id
        cr.commit()
    return session_id


def relation_id(value):
    return value[0] if isinstance(value, (tuple, list)) and value else value or None


def support_snapshot(env, order):
    """Privileged evidence reads only; workers never receive this environment."""
    rows = env['ydental.followup'].sudo().search_read(
        [('ydental_lab_order_id', '=', order.id)],
        ['id', 'state', 'ydental_store_id', 'ydental_lab_order_id', 'ydental_lab_cycle_key',
         'ydental_lab_contact_stage', 'ydental_schedule_version', 'ydental_version',
         'ydental_followup_type', 'ydental_patient_id', 'ydental_source_event_id',
         'ydental_responsible_id', 'ydental_active_notification_request_id',
         'ydental_active_notification_schedule_version'], order='id')
    ids = [row['id'] for row in rows]
    jobs = env['ydental.notification.job'].sudo().search_read(
        [('ydental_followup_id', 'in', ids)],
        ['id', 'ydental_followup_id', 'ydental_event_type', 'ydental_source_version',
         'ydental_state', 'ydental_attempt_count', 'ydental_due_at',
         'ydental_accepted_at', 'ydental_delivered_at'], order='id')
    activities = env['mail.activity'].sudo().with_context(active_test=False).search_read(
        ['|', '&', ('res_model', '=', 'ydental.lab.order'), ('res_id', '=', order.id),
         '&', ('res_model', '=', 'ydental.followup'), ('res_id', 'in', ids)],
        ['id', 'res_model', 'res_id', 'user_id', 'summary', 'note', 'active'], order='id')
    for row in activities:
        note = row.pop('note') or ''
        row['note_sha256'] = hashlib.sha256(note.encode()).hexdigest()
        row['physical_financial_instructions'] = all(word in note for word in (
            'package location', 'vendor cost', 'patient fees', 'native purchase', 'no stock movement'))
        row['communication_instructions'] = (all(word in note for word in (
            'patient communication', 'fee disposition')) and
            ('do not notify' in note or 'No refund or clinical completion' in note))
    fee = order.ydental_source_fee_id.sudo()
    fees = fee.read(['id', 'ydental_event_id', 'ydental_parent_id', 'ydental_price_snapshot_id',
                     'ydental_quantity', 'ydental_unit_price', 'ydental_currency_id', 'ydental_amount'])
    sent = env['ydental.lab.event'].sudo().search_read(
        [('ydental_order_id', '=', order.id), ('ydental_kind', '=', 'sent')],
        ['id', 'ydental_purchase_line_id', 'ydental_purchase_cost_snapshot',
         'ydental_vendor_cost', 'ydental_patient_fee_id', 'ydental_patient_fee_amount',
         'ydental_fee_currency_id', 'ydental_recorded_at'], order='id')
    charges = env['ydental.lab.charge'].sudo().search_read(
        [('ydental_order_id', '=', order.id)],
        ['id', 'state', 'ydental_amount', 'ydental_quantity', 'ydental_unit_price',
         'ydental_price_snapshot_id', 'ydental_settlement_source_id', 'ydental_invoice_id',
         'ydental_invoice_line_id'], order='id')
    return {'followups': rows, 'jobs': jobs, 'activities': activities,
            'economic': {'fee': fees, 'sent_snapshots': sent, 'charges': charges,
                         'native_purchase': env['ydental.lab.service']._purchase_cost_values(
                             order.ydental_purchase_line_id.sudo()) if order.ydental_purchase_line_id else False},
            'patient_id': order.ydental_patient_id.id,
            'source_event_id': order.ydental_source_event_id.id,
            'responsible_id': order.ydental_responsible_id.id}


def passive_identity_is_exact(data, row):
    return (row['id'] == data['followup_id'] and row['ydental_lab_order_id'] == data['order_id'] and
            row['ydental_lab_cycle_key'] == 'order' and
            relation_id(row['ydental_store_id']) == data['store_id'] and
            row['ydental_followup_type'] == 'lab_arrival' and
            relation_id(row['ydental_patient_id']) == data['patient_id'] and
            relation_id(row['ydental_source_event_id']) == data['source_event_id'] and
            relation_id(row['ydental_responsible_id']) == data['responsible_id'])


def validate_waiting_plan(data):
    rows = data['followups']
    if not rows and data['followup_id'] is None:
        return  # genuinely legacy; never manufacture or backfill a waiting plan
    if len(rows) != 1:
        raise Refusal('target must have one exact passive plan, or no legacy plan')
    row = rows[0]
    if not passive_identity_is_exact(data, row) or row['ydental_lab_contact_stage'] not in ('waiting', False):
        raise Refusal('pre-putaway passive plan has an unexpected identity or stage')
    if any(j['ydental_event_type'] == 'lab_arrival' and
           j['ydental_state'] not in ('cancelled', 'not_configured') for j in data['jobs']):
        raise Refusal('pre-putaway target has an arrival notification history; do not replay')


def jobs_preserve_history(before, after, *, cancel_pending):
    old = {row['id']: row for row in before}
    new = {row['id']: row for row in after}
    for key, previous in old.items():
        current = new.get(key)
        if current is None:
            return False
        if previous['ydental_state'] == 'pending' and cancel_pending:
            expected = dict(previous, ydental_state='cancelled')
            if current != expected:
                return False
        elif current != previous:
            return False
    return True


class Journal:
    """Durable metadata, including unknown outcomes; never SQL text or payloads."""
    def __init__(self, path):
        self.path = path
        self.lock = threading.Lock()
        self.rows = []
        require_private_directory(path.parent)
        self.fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)

    def add(self, stage, **values):
        with self.lock:
            row = {'sequence': len(self.rows) + 1, 'stage': stage,
                   'utc': dt.datetime.now(dt.UTC).isoformat(), 'monotonic_ns': time.monotonic_ns(), **values}
            raw = (json.dumps(row, sort_keys=True, default=json_default) + '\n').encode()
            offset = 0
            while offset < len(raw):
                offset += os.write(self.fd, raw[offset:])
            os.fsync(self.fd)
            self.rows.append(row)
            return row

    def close(self):
        os.close(self.fd)


def known_abort(error, concurrency_type, commit_started):
    return not commit_started and (getattr(error, 'pgcode', None) == '40001' or
                                  isinstance(error, concurrency_type))


@contextmanager
def observe_native_locks(cursor_type, journal, local, first_lock_barrier, registry=None):
    original = cursor_type.execute

    def execute(cursor, query, params=None, *args, **kwargs):
        context = getattr(local, 'context', None)
        code = query if isinstance(query, str) else getattr(query, 'code', '')
        observed = context and cursor is getattr(local, 'cursor', None) and 'pg_advisory_xact_lock' in code
        if not observed:
            return original(cursor, query, params, *args, **kwargs)
        # This barrier precedes the real SQL call. No delay or success is added
        # to that measured call and no product lock is replaced.
        lock_ids = [x for x in (params or ()) if type(x) is int]
        if 31911 in lock_ids and context['attempt'] == 1:
            first_lock_barrier.wait(timeout=THREAD_TIMEOUT_SECONDS)
        journal.add('native_lock_call_started', lock_ids=lock_ids, **context)
        try:
            result = original(cursor, query, params, *args, **kwargs)
        except BaseException as error:
            journal.add('native_lock_call_failed', error_type=type(error).__name__,
                        sqlstate=getattr(error, 'pgcode', None), **context)
            raise
        journal.add('native_lock_call_returned', lock_ids=lock_ids, **context)
        if registry is not None and 31911 in lock_ids and context['attempt'] == 1:
            # One real read-only observation after the real acquisition returns.
            # It neither replaces the product lock nor pretends a wait occurred.
            pids = sorted({r['backend_pid'] for r in journal.rows if
                           r['stage'] == 'transaction_open' and r.get('attempt') == 1})
            with registry.cursor() as observer:
                original(observer, 'SET TRANSACTION READ ONLY')
                original(observer, "SELECT pid, granted, mode FROM pg_locks WHERE locktype='advisory' "
                         'AND database=(SELECT oid FROM pg_database WHERE datname=current_database()) '
                         'AND classid=0 AND objid=31911 AND objsubid=1 AND pid=ANY(%s) ORDER BY pid', [pids])
                locks = [{'pid': pid, 'granted': granted, 'mode': mode}
                         for pid, granted, mode in observer.fetchall()]
                observer.rollback()
            journal.add('native_lock_state_observed', locks=locks, **context)
        return result

    cursor_type.execute = execute
    try:
        yield
    finally:
        cursor_type.execute = original


def execute_attempt(registry, api, actor_id, session_key, spec, worker_id, attempt,
                    barrier, journal, local, concurrency_type, user_error_type):
    cr = None
    commit_started = rollback_returned = closed = False
    failure = None
    response = None
    result = {'worker_id': worker_id, 'operation': spec['operation'], 'attempt': attempt}
    context = dict(result, actor_id=actor_id)
    try:
        cr = registry.cursor()
        cr.execute('SET LOCAL statement_timeout = %s', [f'{STATEMENT_TIMEOUT_SECONDS}s'])
        cr.execute('SET LOCAL lock_timeout = %s', [f'{LOCK_TIMEOUT_SECONDS}s'])
        cr.execute("SELECT pg_backend_pid(), current_setting('transaction_isolation'), backend_start::text "
                   "FROM pg_stat_activity WHERE pid=pg_backend_pid()")
        pid, isolation, birth = cr.fetchone()
        result.update(backend_pid=pid, isolation=isolation, backend_start=birth)
        context.update(backend_pid=pid)
        journal.add('transaction_open', isolation=isolation, backend_start=birth, **context)
        env = api.Environment(cr, actor_id, {'lang': 'en_US'})
        access = env['ydental.access.service']
        session = access._existing_session_for_key(session_key)
        if not session:
            raise Refusal('worker session disappeared')
        context['session_id'] = session.id
        bound = access._bind(session)
        if attempt == 1:
            barrier.wait(timeout=THREAD_TIMEOUT_SECONDS)
        local.context = context
        local.cursor = cr
        journal.add('action_started', **context)
        if spec['operation'] == 'scan':
            response = bound.env['ydental.lab.code.scan'].create(spec['payload']).action_scan()
            result.update(kind='resolved', res_model=response.get('res_model'), res_id=response.get('res_id'))
        else:
            response = bound.env['ydental.lab.service']._operate(
                spec['operation'], spec['payload'], spec['key'])
            result.update(kind=response.get('result'), state=response.get('state'),
                          order_id=response.get('order_id'), inventory_event_id=response.get('inventory_event_id'))
        journal.add('action_returned', result_kind=result['kind'], **context)
        journal.add('commit_started', **context)
        commit_started = True
        cr.commit()  # includes native postcommit callbacks; exception means UNKNOWN
        journal.add('commit_returned', **context)
        result['commit_returned'] = True
    except BaseException as error:
        failure = error
        expected = (not commit_started and isinstance(error, user_error_type) and
                    spec.get('expected_error') == str(error))
        result.update(kind='expected_state_conflict' if expected else
                      'unknown_commit' if commit_started else 'aborted',
                      error_type=type(error).__name__, sqlstate=getattr(error, 'pgcode', None))
        journal.add('first_exception', commit_started=commit_started,
                    error_type=type(error).__name__, sqlstate=getattr(error, 'pgcode', None), **context)
    finally:
        local.context = None
        local.cursor = None
        if cr is not None:
            if not result.get('commit_returned'):
                journal.add('rollback_started', **context)
                try:
                    cr.rollback()
                    rollback_returned = True
                    journal.add('rollback_returned', transaction_status=cr._cnx.get_transaction_status(), **context)
                except BaseException as error:
                    result['cleanup_error_type'] = type(error).__name__
                    journal.add('rollback_failed', error_type=type(error).__name__, **context)
            try:
                cr.close()
                closed = bool(cr.closed)
                journal.add('cursor_closed', closed=closed, **context)
            except BaseException as error:
                result['close_error_type'] = type(error).__name__
                journal.add('cursor_close_failed', error_type=type(error).__name__, **context)
    result.update(commit_started=commit_started, rollback_returned=rollback_returned, cursor_closed=closed)
    result['retry_safe'] = bool(failure is not None and known_abort(failure, concurrency_type, commit_started)
                                and rollback_returned and closed and not result.get('cleanup_error_type'))
    return result


def overlap_evidence(events):
    """Compare only actual first-attempt native calls and transaction stages."""
    rows = [row for row in events if row.get('attempt') == 1]
    workers = sorted({row['worker_id'] for row in rows})

    def interval(worker):
        start = next((r['monotonic_ns'] for r in rows if r['worker_id'] == worker and r['stage'] == 'action_started'), None)
        ends = [r['monotonic_ns'] for r in rows if r['worker_id'] == worker and
                r['stage'] in ('commit_returned', 'rollback_returned')]
        return (start, max(ends)) if start is not None and ends else None
    spans = [interval(w) for w in workers]
    overlap = (min(s[1] for s in spans) - max(s[0] for s in spans)
               if len(spans) == 2 and all(spans) else 0)
    # Only actual server pg_locks rows can establish a granted holder and
    # another waiting backend. Native call timing alone does not prove a wait.
    contention = any(
        any(lock['granted'] for lock in row['locks']) and
        any(not lock['granted'] for lock in row['locks']) and
        len({lock['pid'] for lock in row['locks']}) == 2
        for row in rows if row['stage'] == 'native_lock_state_observed')
    return {'first_attempt_action_overlap_ns': max(0, overlap),
            'native_lab_lock_contention_observed': contention,
            'instrumentation_duration_is_not_pure_server_sql_time': True}


def run_pair(registry, api, actor_id, session_keys, specs, receipt_path):
    from odoo.exceptions import ConcurrencyError, UserError  # noqa: PLC0415
    from odoo.sql_db import Cursor  # noqa: PLC0415
    journal = Journal(receipt_path.with_suffix('.stages.jsonl'))
    barrier, lock_barrier = threading.Barrier(2), threading.Barrier(2)
    local = threading.local()
    outcomes = []

    def worker(index):
        attempts = []
        for number in range(1, MAX_SERIALIZATION_RETRIES + 1):
            row = execute_attempt(registry, api, actor_id, session_keys[index], specs[index],
                                  index + 1, number, barrier, journal, local, ConcurrencyError, UserError)
            attempts.append(row)
            if not row['retry_safe'] or number == MAX_SERIALIZATION_RETRIES:
                outcomes.append(dict(row, attempts=attempts))
                return
    try:
        with observe_native_locks(Cursor, journal, local, lock_barrier, registry):
            threads = [threading.Thread(target=worker, args=(i,), daemon=True) for i in range(2)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(THREAD_TIMEOUT_SECONDS + 30)
            if any(thread.is_alive() for thread in threads):
                journal.add('workers_timeout_unknown')
                raise Refusal('worker timeout; durable stages retained; independent readback required, never rerun')
        journal.add('workers_finished')
        metrics = overlap_evidence(journal.rows)
        metrics['stage_file'] = str(journal.path)
        metrics['stage_sha256'] = hashlib.sha256(journal.path.read_bytes()).hexdigest()
        metrics['all_worker_cursors_closed'] = len(outcomes) == 2 and all(r['cursor_closed'] for r in outcomes)
        return outcomes, metrics
    finally:
        # A timed-out daemon may still be recording until process termination;
        # leave its descriptor open rather than fabricate a clean closure.
        if not any(t.is_alive() for t in locals().get('threads', [])):
            journal.close()


def physical_history_preserved(before, after):
    old = {row['id']: row for row in before['lab_events']}
    new = {row['id']: row for row in after['lab_events']}
    return (all(new.get(key) == value for key, value in old.items()) and
            before['economic'] == after['economic'] and
            before['purchase_cost_source'] == after['purchase_cost_source'])


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

    results, race_evidence = run_pair(registry, api, args.actor_id, session_keys,
        [{'operation': 'receive', 'payload': {'order_id': args.order_id}, 'key': action_key}] * 2,
        receipt_path)
    phase['race_evidence'] = race_evidence
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
    pids = [row["attempts"][0].get("backend_pid") for row in results]
    passed = (len(results) == 2 and len(set(pids)) == 2 and
              outcomes == ["accepted", "already_accepted"] and one_receipt_delta and
              all(row.get("state") == "received" and row.get("order_id") == args.order_id
                  for row in results) and
              one_operation and one_audit and
              after["inventory_event_id"] is None and after["followup_id"] == before["followup_id"] and
              after["followups"] == before["followups"] and after["jobs"] == before["jobs"] and
              after["activities"] == before["activities"] and physical_history_preserved(before, after) and
              race_evidence["first_attempt_action_overlap_ns"] > 0 and
              race_evidence["native_lab_lock_contention_observed"] and race_evidence["all_worker_cursors_closed"] and
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

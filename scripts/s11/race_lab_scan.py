#!/usr/bin/env python3
"""Resolve one bound synthetic package through two real ordinary scan actions.

This commits only ordinary workspace/transient technical records. It does not
receive, put away, cancel, bind a code or send a notification. Durable intent
and per-attempt real connection/transaction stages precede action execution.
"""
# Operational CLI: explicit bounded refusal messages and process status output.
# ruff: noqa: EM101, TRY301, BLE001, T201
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import secrets
import sys

import race_lab_receipt_duplicate as common

CONFIRMATION = 'S11-SYNTHETIC-LAB-SCAN-RACE-V1'


def snapshot(env, order_id, store_id):
    order = env['ydental.lab.order'].sudo().browse(order_id).exists()
    if (not order or order.ydental_store_id.id != store_id or
            not common.is_synthetic_internal_code(order.ydental_internal_code) or
            not order.ydental_package_code):
        raise common.Refusal('target must be an existing authorized bound synthetic order')
    events = env['ydental.lab.event'].sudo().search_read(
        [('ydental_order_id', '=', order.id)],
        ['id', 'ydental_kind', 'ydental_before_state', 'ydental_after_state',
         'ydental_inventory_event_id', 'ydental_purchase_line_id', 'ydental_vendor_cost',
         'ydental_actor_id', 'ydental_recorded_at'], order='id')
    quants = env['stock.quant'].sudo().search_read(
        [('product_id', '=', order.ydental_product_id.id), ('lot_id', '=', order.ydental_lot_id.id or False)],
        ['id', 'location_id', 'quantity', 'reserved_quantity'], order='location_id,id')
    data = {'order_id': order.id, 'store_id': store_id, 'state': order.state,
            'version': order.ydental_version,
            'package_code_sha256': hashlib.sha256(order.ydental_package_code.encode()).hexdigest(),
            'followup_id': order.ydental_followup_id.id or None,
            'inventory_event_id': order.ydental_inventory_event_id.id or None,
            'receipt_at': order.ydental_receipt_at, 'receipt_actor_id': order.ydental_receipt_actor_id.id or None,
            'lab_events': events, 'stock_quants': quants}
    data.update(common.support_snapshot(env, order))
    return data


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate', required=True)
    p.add_argument('--actor-id', required=True, type=int)
    p.add_argument('--store-id', required=True, type=int)
    p.add_argument('--order-id', required=True, type=int)
    p.add_argument('--confirm', required=True)
    args = p.parse_args()
    if (args.confirm != CONFIRMATION or min(args.actor_id, args.store_id, args.order_id) <= 0 or
            len(args.candidate) != 40 or any(c not in '0123456789abcdef' for c in args.candidate)):
        raise common.Refusal('exact confirmation, full candidate and positive IDs required')
    launcher, runtime, admission, database, branch, commit = common.load_admitted_runtime(args.candidate)
    api, Registry = common.configure_odoo(launcher, database)
    registry = Registry(database['name'])
    with registry.cursor() as cr:
        identity = common.readonly_identity(cr, launcher, database)
        env = api.Environment(cr, args.actor_id, {})
        common.validate_actor(env, admission, args.actor_id, args.store_id)
        before = snapshot(env, args.order_id, args.store_id)
        code = env['ydental.lab.order'].sudo().browse(args.order_id).ydental_package_code
        cr.rollback()
    race_id = dt.datetime.now(dt.UTC).strftime('%Y%m%dT%H%M%SZ') + '-' + secrets.token_hex(4)
    path = common.RACE_ROOT / (race_id + '-lab-scan.json')
    keys = [secrets.token_urlsafe(32), secrets.token_urlsafe(32)]
    phase = {'schema': 'YD-S11-LAB-SCAN-RACE-V2', 'plan_id': launcher.PLAN_ID,
             'candidate_commit': commit, 'branch': branch, 'database_identity': identity,
             'scope_id': runtime['scope']['id'], 'scope_expires_at_utc': runtime['scope']['expires_at_utc'],
             'actor_id': args.actor_id, 'store_id': args.store_id, 'order_id': args.order_id,
             'session_key_sha256': [hashlib.sha256(k.encode()).hexdigest() for k in keys],
             'session_ids': [], 'before': before, 'phase': 'READY_BEFORE_SCAN',
             'business_mutation_started': False, 'technical_wizard_write_started': False}
    common.write_private(path, phase)
    for key in keys:
        phase['session_ids'].append(common.prepare_session(registry, api, args.actor_id, args.store_id, key))
        phase['phase'] = 'SESSION_SETUP_COMMITTED'
        common.write_private(path, phase)
    phase.update(phase='TWO_CONNECTION_SCAN_PENDING', technical_wizard_write_started=True)
    common.write_private(path, phase)
    outcomes, metrics = common.run_pair(registry, api, args.actor_id, keys,
                                       [{'operation': 'scan', 'payload': {'code': code}}] * 2, path)
    phase.update(phase='WORKERS_COMPLETE_READBACK_PENDING', worker_results=outcomes, race_evidence=metrics)
    common.write_private(path, phase)
    with registry.cursor() as cr:
        cr.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        after = snapshot(api.Environment(cr, args.actor_id, {}), args.order_id, args.store_id)
        cr.rollback()
    pids = [r['attempts'][0].get('backend_pid') for r in outcomes]
    passed = (len(outcomes) == 2 and len(set(pids)) == 2 and None not in pids and
              all(r['kind'] == 'resolved' and r.get('commit_returned') and r['res_model'] == 'ydental.lab.order'
                  and r['res_id'] == args.order_id for r in outcomes) and before == after and
              metrics['first_attempt_action_overlap_ns'] > 0 and metrics['all_worker_cursors_closed'])
    phase.update(phase='READBACK_COMPLETE', after=after,
                 two_distinct_postgresql_backends=len(set(pids)) == 2 and None not in pids,
                 business_state_unchanged=before == after, outcome='PASS' if passed else 'FAIL',
                 external_delivery='NOT_INVOLVED', finished_at_utc=common.utc_now())
    common.write_private(path, phase)
    print(json.dumps({'receipt': str(path), 'outcome': phase['outcome']}))
    return 0 if passed else 3


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f'S11 scan stopped: {type(error).__name__}: {error}', file=sys.stderr)
        raise SystemExit(2)

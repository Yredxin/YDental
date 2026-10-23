#!/usr/bin/env python3
"""Race cancellation against actual put-away from a committed received order.

The historical filename is retained for callers. This V2 contract is explicitly
cancel/putaway, never the obsolete receive/cancel one-winner assertion. No
receipt or fixture is prepared here. Existing legacy absent plans remain absent
on cancellation; new waiting plans stop, preserving all historical facts.
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

import race_lab_putaway_duplicate as putaway
import race_lab_receipt_duplicate as common

CONFIRMATION = 'S11-SYNTHETIC-LAB-CANCEL-PUTAWAY-RACE-V2'


def cancelled_plan_is_exact(before, after):
    if not before['followups']:
        return not after['followups'] and after['followup_id'] is None and not after['jobs']
    if len(before['followups']) != 1 or len(after['followups']) != 1:
        return False
    old, new = before['followups'][0], after['followups'][0]
    return (common.passive_identity_is_exact(after, new) and
            new['id'] == old['id'] == after['followup_id'] and
            new['ydental_lab_contact_stage'] == 'stopped' and
            new['ydental_schedule_version'] == old['ydental_schedule_version'] + 1 and
            new['state'] == (old['state'] if old['state'] in ('done', 'closed') else 'closed') and
            not new['ydental_active_notification_request_id'] and
            new['ydental_active_notification_schedule_version'] == 0 and
            {r['id'] for r in before['jobs']} == {r['id'] for r in after['jobs']} and
            common.jobs_preserve_history(before['jobs'], after['jobs'], cancel_pending=True))


def cancellation_activities_are_real(before, after, actor_id):
    old = {row['id']: row for row in before['activities']}
    new = {row['id']: row for row in after['activities']}
    for key, previous in old.items():
        current = new.get(key)
        if current is None:
            return False
        refreshed_contact = (previous['active'] and previous['res_model'] == 'ydental.followup' and
                             previous['res_id'] == before['followup_id'] and
                             common.relation_id(previous['user_id']) == before['responsible_id'] and
                             previous['summary'] == 'Follow-up contact required')
        if refreshed_contact:
            unchanged_fields = set(previous) - {'note_sha256', 'communication_instructions', 'physical_financial_instructions'}
            if any(current[field] != previous[field] for field in unchanged_fields):
                return False
        elif current != previous:
            return False
    physical = [row for row in new.values() if row['active'] and
                row['res_model'] == 'ydental.lab.order' and row['res_id'] == before['order_id'] and
                common.relation_id(row['user_id']) == actor_id and row['physical_financial_instructions']]
    communication_model = 'ydental.followup' if before['followup_id'] else 'ydental.lab.order'
    communication_id = before['followup_id'] or before['order_id']
    communication = [row for row in new.values() if row['active'] and
                     row['res_model'] == communication_model and row['res_id'] == communication_id and
                     common.relation_id(row['user_id']) == before['responsible_id'] and
                     row['communication_instructions']]
    return bool(physical and communication)


def putaway_winner_is_exact(before, after, inventory_operations, actor_id):
    if len(after['inventory_events']) != 1 or not after['move']:
        return False
    stock, move = after['inventory_events'][0], after['move']
    quantity = before['quantity']
    source_key = before['inventory_key']
    payload = {'lot_id': before['lot_id'], 'quantity': quantity, 'uom_id': before['product_uom_id'],
               'source_key': source_key,
               'reason': 'External laboratory work order %s received and put away' % before['internal_code']}
    fingerprint = hashlib.sha256(json.dumps(['receive', before['store_id'], payload],
                                         sort_keys=True, ensure_ascii=True).encode()).hexdigest()
    return (after['state'] == 'available' and after['inventory_event_id'] == stock['id'] and
            stock['ydental_kind'] == 'receipt' and stock['state'] == 'done' and
            stock['ydental_source_namespace'] == 'warehouse' and stock['ydental_source_key'] == source_key and
            common.relation_id(stock['ydental_product_id']) == before['product_id'] and
            common.relation_id(stock['ydental_lot_id']) == before['lot_id'] and
            common.relation_id(stock['ydental_actor_id']) == actor_id and
            common.relation_id(stock['ydental_from_id']) == before['supplier_location_id'] and
            common.relation_id(stock['ydental_to_id']) == before['target_location_id'] and
            common.relation_id(stock['ydental_move_id']) == move['id'] and
            move['state'] == 'done' and move['product_id'] == before['product_id'] and
            move['location_id'] == before['supplier_location_id'] and
            move['location_dest_id'] == before['target_location_id'] and
            move['company_id'] == before['company_id'] and move['store_id'] == before['store_id'] and
            move['uom_id'] == before['product_uom_id'] and
            abs(stock['ydental_quantity'] - quantity) <= 1e-9 and
            abs(move['product_uom_qty'] - quantity) <= 1e-9 and
            putaway.quant_effect_is_exact(before, after, quantity) and
            putaway.plan_transition_is_exact(before, after) and
            len(inventory_operations) == 1 and
            inventory_operations[0]['ydental_key'] == 'lab-putaway-%s' % before['order_id'] and
            inventory_operations[0]['ydental_fingerprint'] == fingerprint and
            common.relation_id(inventory_operations[0]['ydental_actor_id']) == actor_id and
            inventory_operations[0]['ydental_result'] == {
                'id': stock['id'], 'move_id': move['id'], 'state': 'done', 'result': 'accepted'})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', required=True)
    parser.add_argument('--actor-id', type=int, required=True)
    parser.add_argument('--store-id', type=int, required=True)
    parser.add_argument('--order-id', type=int, required=True)
    parser.add_argument('--prior-race-order-id', type=int, required=True)
    parser.add_argument('--confirm', required=True)
    args = parser.parse_args()
    if (args.confirm != CONFIRMATION or min(args.actor_id, args.store_id, args.order_id,
                                          args.prior_race_order_id) <= 0 or
            args.order_id == args.prior_race_order_id or len(args.candidate) != 40 or
            any(c not in '0123456789abcdef' for c in args.candidate)):
        raise common.Refusal('exact confirmation/candidate and positive distinct target/reference required')
    launcher, runtime, admission, database, branch, commit = common.load_admitted_runtime(args.candidate)
    api, Registry = common.configure_odoo(launcher, database)
    registry = Registry(database['name'])
    with registry.cursor() as cr:
        identity = common.readonly_identity(cr, launcher, database)
        env = api.Environment(cr, args.actor_id, {})
        common.validate_actor(env, admission, args.actor_id, args.store_id)
        previous = env['ydental.lab.order'].sudo().browse(args.prior_race_order_id).exists()
        if (not previous or previous.ydental_store_id.id != args.store_id or
                not common.is_synthetic_internal_code(previous.ydental_internal_code)):
            raise common.Refusal('reference must be an existing distinct synthetic order in this store')
        before = putaway.validate_target(env, args.order_id, args.actor_id, args.store_id)
        cr.rollback()
    inner_key = 'lab-putaway-%s' % args.order_id
    if putaway.prepare_inventory_operation(registry, api, args.actor_id, args.store_id, inner_key):
        raise common.Refusal('target already has an inner putaway operation; never replay')
    race_id = dt.datetime.now(dt.UTC).strftime('%Y%m%dT%H%M%SZ') + '-' + secrets.token_hex(4)
    receipt_path = common.RACE_ROOT / (race_id + '-lab-cancel-putaway.json')
    reason = 'S11 synthetic concurrent cancellation before actual put-away'
    specs = [
        {'operation': 'cancel', 'payload': {'order_id': args.order_id, 'reason': reason},
         'key': 's11-cancel-race-' + secrets.token_hex(18),
         'expected_error': 'Cancellation is allowed only before actual put-away.'},
        {'operation': 'putaway', 'payload': {'order_id': args.order_id},
         'key': 's11-putaway-race-' + secrets.token_hex(18),
         'expected_error': 'Physical receipt and the matching native prosthesis lot are required before put-away.'}]
    session_keys = [secrets.token_urlsafe(32), secrets.token_urlsafe(32)]
    phase = {'schema': 'YD-S11-LAB-CANCEL-PUTAWAY-RACE-V2', 'plan_id': launcher.PLAN_ID,
             'candidate_commit': commit, 'branch': branch, 'database_identity': identity,
             'scope_id': runtime['scope']['id'], 'scope_expires_at_utc': runtime['scope']['expires_at_utc'],
             'actor_id': args.actor_id, 'store_id': args.store_id, 'order_id': args.order_id,
             'prior_race_order_id': args.prior_race_order_id, 'before': before,
             'operation_key_sha256': {s['operation']: hashlib.sha256(s['key'].encode()).hexdigest() for s in specs},
             'session_key_sha256': [hashlib.sha256(k.encode()).hexdigest() for k in session_keys],
             'session_ids': [], 'business_mutation_started': False, 'phase': 'READY_BEFORE_RACE'}
    common.write_private(receipt_path, phase)
    for key in session_keys:
        phase['session_ids'].append(common.prepare_session(registry, api, args.actor_id, args.store_id, key))
        phase['phase'] = 'SESSION_SETUP_COMMITTED'
        common.write_private(receipt_path, phase)
    phase.update(phase='TWO_CONNECTION_CANCEL_PUTAWAY_PENDING', business_mutation_started=True)
    common.write_private(receipt_path, phase)
    outcomes, metrics = common.run_pair(registry, api, args.actor_id, session_keys, specs, receipt_path)
    phase.update(phase='WORKERS_COMPLETE_READBACK_PENDING', worker_results=outcomes, race_evidence=metrics)
    common.write_private(receipt_path, phase)
    with registry.cursor() as cr:
        cr.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        env = api.Environment(cr, args.actor_id, {})
        after = putaway.snapshot(env, args.order_id, args.store_id)
        operations = env['ydental.lab.operation'].sudo().search_read(
            [('ydental_store_id', '=', args.store_id), ('ydental_key', 'in', [s['key'] for s in specs])],
            ['id', 'ydental_key', 'ydental_fingerprint', 'ydental_result', 'ydental_actor_id'], order='id')
        inner = env['ydental.inventory.operation'].sudo().search_read(
            [('ydental_store_id', '=', args.store_id), ('ydental_key', '=', inner_key)],
            ['id', 'ydental_key', 'ydental_fingerprint', 'ydental_result', 'ydental_actor_id'], order='id')
        audits = env['ydental.access.audit'].sudo().search_read(
            [('ydental_store_id', '=', args.store_id), ('ydental_target_model', '=', 'ydental.lab.order'),
             ('ydental_target_id', '=', args.order_id),
             ('ydental_event', 'in', ['lab.putaway', 'lab.cancelled', 'lab.cancellation_review'])],
            ['id', 'ydental_event', 'ydental_user_id'], order='id')
        cr.rollback()
    accepted = [row for row in outcomes if row['kind'] == 'accepted' and row.get('commit_returned')]
    rejected = [row for row in outcomes if row['kind'] == 'expected_state_conflict' and row['rollback_returned']]
    winning = accepted[0]['operation'] if len(accepted) == 1 else None
    spec = next((s for s in specs if s['operation'] == winning), None)
    events = [r for r in after['lab_events'] if r['id'] not in {e['id'] for e in before['lab_events']}]
    event_kind = 'putaway' if winning == 'putaway' else 'cancelled'
    immutable = (common.physical_history_preserved(before, after) and
                 before['receipt_at'] == after['receipt_at'] and
                 before['receipt_actor_id'] == after['receipt_actor_id'])
    one_event = (len(events) == 1 and events[0]['ydental_kind'] == event_kind and
                 events[0]['ydental_before_state'] == 'received' and
                 events[0]['ydental_after_state'] == after['state'] and
                 common.relation_id(events[0]['ydental_actor_id']) == args.actor_id and
                 after['version'] == before['version'] +
                 (2 if winning == 'putaway' and before['followup_id'] is None else 1))
    one_operation = bool(spec and len(operations) == 1 and
                         operations[0]['ydental_key'] == spec['key'] and
                         operations[0]['ydental_fingerprint'] == hashlib.sha256(json.dumps(
                             [winning, args.store_id, spec['payload']], sort_keys=True, ensure_ascii=True).encode()).hexdigest() and
                         common.relation_id(operations[0]['ydental_actor_id']) == args.actor_id and
                         operations[0]['ydental_result'] == {'order_id': args.order_id, 'state': after['state'],
                                                            'inventory_event_id': after['inventory_event_id'] or False})
    if winning == 'cancel':
        terminal = (after['state'] == 'cancelled' and after['inventory_event_id'] is None and not inner and
                    not after['inventory_events'] and not after['move'] and
                    after['stock_quants'] == before['stock_quants'] and
                    cancelled_plan_is_exact(before, after) and
                    cancellation_activities_are_real(before, after, args.actor_id))
        expected_audits = ['lab.cancellation_review', 'lab.cancelled']
    else:
        terminal = winning == 'putaway' and putaway_winner_is_exact(before, after, inner, args.actor_id)
        expected_audits = ['lab.putaway']
    audit_ok = (sorted(r['ydental_event'] for r in audits) == expected_audits and
                all(common.relation_id(r['ydental_user_id']) == args.actor_id for r in audits))
    pids = [row['attempts'][0].get('backend_pid') for row in outcomes]
    passed = (len(outcomes) == 2 and len(set(pids)) == 2 and None not in pids and
              len(accepted) == len(rejected) == 1 and
              {r['operation'] for r in outcomes} == {'cancel', 'putaway'} and
              metrics['first_attempt_action_overlap_ns'] > 0 and
              metrics['native_lab_lock_contention_observed'] and metrics['all_worker_cursors_closed'] and
              immutable and one_event and one_operation and terminal and audit_ok)
    phase.update(phase='READBACK_COMPLETE', after=after, worker_results=outcomes,
                 committed_operation_rows=operations, committed_inventory_operations=inner,
                 matching_audit_rows=audits, immutable_receipt_cost_fee_history=immutable,
                 exactly_one_action_committed=bool(len(accepted) == len(rejected) == 1),
                 one_event=one_event, one_idempotency_operation=one_operation,
                 terminal_effects_exact=terminal, matching_audits=audit_ok,
                 two_distinct_postgresql_backends=len(set(pids)) == 2 and None not in pids,
                 winner=winning, outcome='PASS' if passed else 'FAIL', finished_at_utc=common.utc_now())
    common.write_private(receipt_path, phase)
    print(json.dumps({'receipt': str(receipt_path), 'outcome': phase['outcome'], 'winner': winning}))
    return 0 if passed else 3


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f'S11 cancel/putaway race stopped: {type(error).__name__}: {error}', file=sys.stderr)
        raise SystemExit(2)

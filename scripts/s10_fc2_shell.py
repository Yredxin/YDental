"""FC2 one Odoo shell, two independent ORM cursors, seven planned business commits.

The shell command is dispatched only by s10_fc2_control.py after the #34 checkpoint.
No business action uses another Odoo registry process.
"""

from collections import Counter
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
import threading
import time
from types import SimpleNamespace

from odoo import Command, api
from odoo.exceptions import AccessError, UserError, ValidationError
from psycopg2 import errorcodes
from odoo.addons.ydental_treatment_test.tests.common import bind, key, price
from odoo.addons.ydental_treatment_test.tests.treatment_common import setup, receive, opened_actual, execute_args

RUN = Path(os.environ['YDENTAL_S10_RUN_DIR'])
NAME = 'ydental_s10_test_20261014152000_fc2a7d31'
AUTH = 6171419484
assert RUN.name == NAME and env.cr.dbname == NAME
assert stat.S_IMODE(RUN.stat().st_mode) == 0o700
MARKER = json.loads((RUN / 'database.json').read_text())
assert MARKER['database'] == NAME and MARKER['auth'] == AUTH
assert MARKER['shell_sha256'] == hashlib.sha256(Path('/home/redxin/code/odoo/odoo-sd/code/sd-addons/scripts/s10_fc2_shell.py').read_bytes()).hexdigest()
env.cr.execute('SELECT oid FROM pg_database WHERE datname=%s', [NAME])
assert env.cr.fetchone()[0] == MARKER['oid']
env.cr.execute('SELECT system_identifier::text FROM pg_control_system()')
assert env.cr.fetchone()[0] == MARKER['cluster']

ROOT = api.Environment(env.cr, 1, {})
EVIDENCE = RUN / 'fc2-evidence.jsonl'
LEDGER = RUN / 'fc2-commit-ledger.jsonl'
MAX_COMMITS = 12
commit_count = 0


def append(path, row):
    raw = json.dumps(row, ensure_ascii=True, sort_keys=True, default=str) + '\n'
    with path.open('a', encoding='utf-8') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def event(case, stage, **values):
    append(EVIDENCE, {'utc': datetime.now(timezone.utc).isoformat(), 'case': case,
                      'stage': stage, **values})


def commit(case, purpose):
    global commit_count
    assert commit_count < MAX_COMMITS
    assert purpose in ('fixture', 'A_cancel_first', 'B_done', 'B_unknown_failed',
                       'B_verified_recover_release', 'C_execute_first',
                       'C_same_cashier_close', 'D_cash_history_close',
                       'D_unlock_correct_old_reclose', 'D_actual_wechat_refund',
                       'D_today_wechat_close')
    intents = Counter(str(kind) for _channel, kind, _payload in env.cr.precommit.data.get('bus.bus.values', ()))
    event(case, 'precommit_bus_intents', kinds=dict(intents), total=sum(intents.values()))
    append(LEDGER, {'attempt': commit_count + 1, 'case': case, 'purpose': purpose,
                    'utc': datetime.now(timezone.utc).isoformat(), 'status': 'BEFORE_COMMIT'})
    env.cr.commit()
    commit_count += 1
    append(LEDGER, {'attempt': commit_count, 'case': case, 'purpose': purpose,
                    'utc': datetime.now(timezone.utc).isoformat(), 'status': 'COMMITTED'})
    event(case, 'commit', purpose=purpose, total=commit_count)


def bound(root, actor_id, session_id):
    user = root['res.users'].browse(actor_id)
    access = root['ydental.access.service'].with_user(user)
    session = root['ydental.access.session'].sudo().browse(session_id)
    return access._bind(session).env['ydental.settlement.service']


def session(root, user, store):
    access = root['ydental.access.service'].with_user(user)
    created = access._session_for_key(key())
    access._bind(created)._switch(store.id)
    return created.id


def counts(root):
    names = ('account.move', 'account.payment', 'account.partial.reconcile',
             'ydental.settlement.refund', 'ydental.settlement.close',
             'ydental.access.audit', 'mail.message', 'mail.mail', 'bus.bus')
    return {name: root[name].sudo().search_count([]) for name in names}


def native(root, ids):
    result = {}
    for name, payment_id in ids.items():
        payment = root['ydental.settlement.payment'].sudo().browse(payment_id)
        actual = payment.ydental_payment_id
        result[name] = {'state': actual.state, 'move_state': actual.move_id.state,
                        'amount': payment.ydental_amount, 'channel': payment.ydental_channel,
                        'date': str(payment.ydental_business_date), 'journal_id': actual.journal_id.id,
                        'company_id': actual.company_id.id}
    return result


def refund_state(root, refund_id):
    refund = root['ydental.settlement.refund'].sudo().browse(refund_id)
    outbound = refund.ydental_native_payment_id
    return {'state': refund.ydental_state, 'amount': refund.ydental_amount,
            'requester': refund.ydental_requester_id.id,
            'approver': refund.ydental_approver_id.id,
            'executor': refund.ydental_executor_id.id,
            'actual_date': str(refund.ydental_refund_business_date) if refund.ydental_refund_business_date else None,
            'channel': refund.ydental_refund_channel or None,
            'outbound_id': outbound.id or None, 'outbound_amount': outbound.amount if outbound else 0,
            'outbound_state': outbound.move_id.state if outbound else None,
            'outbound_journal': outbound.journal_id.id if outbound else None,
            'credits': [(x.id, x.state, x.amount_total) for x in refund.ydental_credit_note_ids]}


def initial_fixture():
    # The approved global Settings effect is explicit and scoped to this clone.
    group_user = ROOT.ref('base.group_user')
    for xmlid in ('stock.group_stock_multi_warehouses',
                  'stock.group_stock_multi_locations', 'product.group_product_pricelist'):
        group = ROOT.ref(xmlid)
        if group not in group_user.implied_ids:
            group_user._apply_group(group)
        assert group in group_user.implied_ids
    implied = sorted(group_user.implied_ids.ids)
    f = SimpleNamespace(env=ROOT)
    setup(f)
    store = f.stores[0]
    for role in ('manager', 'frontdesk'):
        f.admin._grant(f.users[role].id, store.id,
                       {'settlement': 'write', 'finance_approval': 'write'})
    f.admin._grant(f.users['doctor'].id, store.id, {'settlement': 'write'})
    company = store.company_id
    root = f.root['base'].with_company(company).env
    income = root['account.account'].search([('account_type', '=', 'income'),
        ('company_ids', 'in', company.id)], limit=1)
    sales = root['account.journal'].search([('type', '=', 'sale'), ('company_id', '=', company.id)], limit=1)
    general = root['account.journal'].search([('type', '=', 'general'), ('company_id', '=', company.id)], limit=1)
    assert income and sales and general
    cfg = {'ydental_store_id': store.id, 'company_id': company.id,
           'ydental_policy': 'demo_confirmation', 'ydental_sales_journal_id': sales.id,
           'ydental_income_account_id': income.id, 'ydental_adjustment_journal_id': general.id}
    for index, channel in enumerate(('cash', 'wechat', 'alipay', 'card'), 1):
        account = root['account.account'].create({'name': 'FC2 synthetic outstanding ' + channel,
            'code': 'Y' + str(store.id).zfill(3) + str(index),
            'account_type': 'asset_current', 'company_ids': [Command.link(company.id)]})
        journal = root['account.journal'].create({'name': 'FC2 synthetic ' + channel,
            'code': 'Y' + str(index) + str(store.id), 'type': 'bank', 'company_id': company.id})
        for line in journal.inbound_payment_method_line_ids | journal.outbound_payment_method_line_ids:
            if line.payment_method_id.code == 'manual':
                line.write({'payment_account_id': account.id})
        cfg['ydental_' + channel + '_journal_id'] = journal.id
    root['ydental.settlement.config']._new(cfg)
    receive(f, 10)
    price(f, 100)
    treatment, _clinical, _queue, _lease, _execution, _document, args = opened_actual(f)
    manager = bind(f, f.users['manager']).env['ydental.settlement.service']
    frontdesk = bind(f, f.users['frontdesk']).env['ydental.settlement.service']
    fees = []
    for _ in range(3):
        actual = treatment._operate('execute', execute_args(f, args), key())
        assert actual['amount'] == 100
        fees.append(actual['fee_id'])
    invoices = [manager._operate('bill', {'fee_ids': [fee], 'discount': 0, 'reason': ''}, key())['invoice_id'] for fee in fees]
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    today = datetime.now(timezone.utc).isoformat()
    pay_ab = manager._operate('pay', {'invoice_ids': [invoices[0]], 'amount': 100,
        'channel': 'card', 'actual_utc': today, 'proof': 'FC2 synthetic offline card receipt AB'}, key())['payment_id']
    pay_c = frontdesk._operate('pay', {'invoice_ids': [invoices[1]], 'amount': 100,
        'channel': 'card', 'actual_utc': yesterday, 'proof': 'FC2 synthetic prior-day card receipt C'}, key())['payment_id']
    pay_d = manager._operate('pay', {'invoice_ids': [invoices[2]], 'amount': 100,
        'channel': 'cash', 'actual_utc': yesterday,
        'proof': 'FC2 synthetic real WeChat receipt mislabeled cash'}, key())['payment_id']

    requests = {}
    for label, payment_id, amount in (
        ('a', pay_ab, 20), ('b', pay_ab, 25), ('u', pay_ab, 20), ('f', pay_ab, 20),
        ('c', pay_c, 30), ('d', pay_d, 40)):
        requests[label] = manager._operate('refund_request', {'payment_id': payment_id,
            'amount': amount, 'reason': 'FC2 synthetic ' + label + ' refund',
            'request_key': key()}, key())['refund_id']
        approved = frontdesk._operate('refund_approve', {'refund_id': requests[label],
            'reason': 'FC2 independent finance approval'}, key())
        assert approved['state'] == 'approved' and approved['actually_refunded'] == 0
    old_day = str(root['ydental.settlement.payment'].browse(pay_c).ydental_business_date)
    current_day = str(root['ydental.settlement.payment'].browse(pay_ab).ydental_business_date)
    assert old_day < current_day
    old_card_close = frontdesk._operate('close', {'business_date': old_day, 'channel': 'card'}, key())
    assert old_card_close['gross'] == 100 and old_card_close['refunded'] == 0
    sessions = {role: session(root, f.users[role], store) for role in ('manager', 'frontdesk', 'doctor')}
    sessions['frontdesk_close'] = session(root, f.users['frontdesk'], store)
    fixture = {'store_id': store.id, 'company_id': company.id,
               'actors': {role: f.users[role].id for role in ('manager', 'frontdesk', 'doctor')} | {
                   'frontdesk_close': f.users['frontdesk'].id},
               'sessions': sessions,
               'payments': {'ab': pay_ab, 'c': pay_c, 'd': pay_d},
               'invoices': invoices, 'refunds': requests, 'old_day': old_day,
               'today': current_day, 'old_card_close': old_card_close['close_id'],
               'journals': {channel: cfg['ydental_' + channel + '_journal_id'] for channel in ('card', 'cash', 'wechat')},
               'groups': implied}
    assert sorted(group_user.implied_ids.ids) == implied
    assert all(x['move_state'] == 'posted' for x in native(root, fixture['payments']).values())
    event('fixture', 'precommit', counts=counts(root), native=native(root, fixture['payments']),
          refunds={name: refund_state(root, rid) for name, rid in requests.items()}, groups=implied)
    commit('fixture', 'fixture')
    return fixture


def race(case, first_role, first_op, second_role, second_op, fixture, purpose):
    """Actor one holds an uncommitted Odoo action while actor two waits on its lock."""
    root = api.Environment(env.cr, 1, {})
    first = bound(root, fixture['actors'][first_role], fixture['sessions'][first_role])
    env.cr.execute('SELECT pg_backend_pid()')
    first_pid = env.cr.fetchone()[0]
    started = threading.Event()
    finished = threading.Event()
    result = {}

    def other():
        with env.registry.cursor() as cr:
            other_root = api.Environment(cr, 1, {})
            cr.execute('SELECT pg_backend_pid()')
            result['backend'] = cr.fetchone()[0]
            second = bound(other_root, fixture['actors'][second_role], fixture['sessions'][second_role])
            result['start_utc'] = datetime.now(timezone.utc).isoformat()
            started.set()
            try:
                value = second._operate(*second_op)
            except (AccessError, UserError, ValidationError) as exc:
                result.update(status='EXPECTED_REJECT', exception=type(exc).__name__, code=str(exc).split(':', 1)[0])
                cr.rollback()
            except Exception as exc:
                result.update(status='ODOO_PASS_ROLLBACK' if getattr(exc, 'pgcode', None) == errorcodes.SERIALIZATION_FAILURE else 'FAIL',
                              exception=type(exc).__name__, sqlstate=getattr(exc, 'pgcode', None))
                cr.rollback()
            else:
                result.update(status='FAIL_UNEXPECTED_SECOND_ACCEPT', value=value)
                cr.rollback()
            result['end_utc'] = datetime.now(timezone.utc).isoformat()
            finished.set()

    event(case, 'first_start', backend=first_pid, role=first_role, operation=first_op[0])
    first_value = first._operate(*first_op)
    event(case, 'first_action_uncommitted', backend=first_pid, value=first_value)
    thread = threading.Thread(target=other, name='fc2-second-backend', daemon=False)
    thread.start()
    assert started.wait(10), 'Second backend did not start'
    assert first_pid != result['backend']
    time.sleep(0.25)
    assert thread.is_alive(), 'Second action did not overlap uncommitted first action'
    event(case, 'overlap', first_backend=first_pid, second_backend=result['backend'],
          second_start_utc=result['start_utc'], second_waiting=True)
    commit(case, purpose)
    assert finished.wait(30), 'Second backend did not finish after first commit'
    thread.join(timeout=2)
    assert not thread.is_alive()
    event(case, 'race_result', first='ODOO_PASS_COMMITTED', second=result)
    assert result['status'] in ('ODOO_PASS_ROLLBACK', 'EXPECTED_REJECT'), result
    return first_value, result


def review(fixture, label):
    root = api.Environment(env.cr, 1, {})
    output = {'counts': counts(root), 'native': native(root, fixture['payments']),
              'refunds': {name: refund_state(root, rid) for name, rid in fixture['refunds'].items()}}
    assert all(x['move_state'] == 'posted' for x in output['native'].values())
    assert sorted(root.ref('base.group_user').implied_ids.ids) == fixture['groups']
    assert output['counts']['mail.mail'] == 0
    event(label, 'fresh_cursor_review', **output)
    return root, output


def reject(case, service, operation, payload, reason):
    before = counts(api.Environment(env.cr, 1, {}))
    with env.cr.savepoint():
        try:
            service._operate(operation, payload, key())
        except (AccessError, UserError, ValidationError) as exc:
            event(case, 'EXPECTED_REJECT', operation=operation, reason=reason,
                  exception=type(exc).__name__, code=str(exc).split(':', 1)[0])
        else:
            raise AssertionError(case + ': forbidden ' + operation + ' accepted')
    after = counts(api.Environment(env.cr, 1, {}))
    for name in ('account.move', 'account.payment', 'account.partial.reconcile',
                 'ydental.access.audit', 'mail.mail'):
        assert after[name] == before[name], (case, operation, name, before[name], after[name])


fixture = initial_fixture()
root, baseline = review(fixture, 'fixture')
assert baseline['counts']['account.payment'] == 3
assert all(x['state'] == 'approved' for x in baseline['refunds'].values())
manager = bound(root, fixture['actors']['manager'], fixture['sessions']['manager'])
assert manager._refund_capacity(root['ydental.settlement.payment'].browse(fixture['payments']['ab'])) == 15

# A: verified-not-paid cancellation is committed before contested execution.
cancel_payload = {'refund_id': fixture['refunds']['a'], 'verified_not_paid': True,
                  'evidence': 'FC2 synthetic offline proof: no payout occurred',
                  'reason': 'FC2 independently verified no payout'}
a_cancel, a_loser = race('A', 'frontdesk', ('refund_cancel', cancel_payload, key()),
    'manager', ('refund_execute', {'refund_id': fixture['refunds']['a'],
    'actual_utc': datetime.now(timezone.utc).isoformat(),
    'proof': 'FC2 contested synthetic payout that must not occur'}, key()),
    fixture, 'A_cancel_first')
root, after_a = review(fixture, 'A')
assert after_a['refunds']['a']['state'] == 'cancelled'
assert after_a['refunds']['a']['outbound_id'] is None and not after_a['refunds']['a']['credits']
assert after_a['counts']['account.payment'] == baseline['counts']['account.payment']
assert after_a['counts']['account.partial.reconcile'] == baseline['counts']['account.partial.reconcile']
manager = bound(root, fixture['actors']['manager'], fixture['sessions']['manager'])
assert manager._refund_capacity(root['ydental.settlement.payment'].browse(fixture['payments']['ab'])) == 35
reject('A', manager, 'refund_execute', {'refund_id': fixture['refunds']['a'],
    'actual_utc': datetime.now(timezone.utc).isoformat(),
    'proof': 'FC2 forbidden new-key execution after cancellation'}, 'new_key_after_cancel')
frontdesk = bound(root, fixture['actors']['frontdesk'], fixture['sessions']['frontdesk'])
reject('A', frontdesk, 'refund_cancel', cancel_payload, 'no_second_capacity_release')
env.cr.rollback()

# B1: a completed refund is immutable under same-key replay and new keys.
root = api.Environment(env.cr, 1, {})
manager = bound(root, fixture['actors']['manager'], fixture['sessions']['manager'])
frontdesk = bound(root, fixture['actors']['frontdesk'], fixture['sessions']['frontdesk'])
actual_b = {'refund_id': fixture['refunds']['b'],
            'actual_utc': datetime.now(timezone.utc).isoformat(),
            'proof': 'FC2 confirmed synthetic offline refund B'}
execute_key = key()
first_b = manager._operate('refund_execute', actual_b, execute_key)
assert first_b['state'] == 'done' and first_b['actually_refunded'] == 25
commit('B', 'B_done')
root, after_b = review(fixture, 'B_done')
assert after_b['refunds']['b']['state'] == 'done'
assert after_b['refunds']['b']['outbound_amount'] == 25
assert after_b['refunds']['b']['outbound_state'] == 'posted'
assert len(after_b['refunds']['b']['credits']) == 1
assert after_b['counts']['account.payment'] == after_a['counts']['account.payment'] + 1
manager = bound(root, fixture['actors']['manager'], fixture['sessions']['manager'])
frontdesk = bound(root, fixture['actors']['frontdesk'], fixture['sessions']['frontdesk'])
pre_replay = counts(root)
replay = manager._operate('refund_execute', actual_b, execute_key)
assert replay['result'] == 'already_accepted' and replay['native_payment_id'] == first_b['native_payment_id']
assert counts(root) == pre_replay
reject('B', manager, 'refund_execute', actual_b, 'different_key_after_done')
reject('B', frontdesk, 'refund_cancel', {'refund_id': fixture['refunds']['b'],
    'verified_not_paid': True, 'evidence': 'FC2 false no-payout claim',
    'reason': 'FC2 forbidden completed cancel'}, 'cancel_after_done')
reject('B', frontdesk, 'refund_recover', {'refund_id': fixture['refunds']['b'],
    'verified_not_paid': True, 'reason': 'FC2 forbidden done recovery'}, 'recover_done_true_rejected')
reject('B', manager, 'refund_uncertain', {'refund_id': fixture['refunds']['b'],
    'outcome': 'unknown', 'reason': 'FC2 forbidden done regression'}, 'unknown_after_done')
event('B', 'done_replay_review', same_key=replay['result'], before=pre_replay, after=counts(root))
env.cr.rollback()

# B2: synthetic unknown/failed means no payout was attempted. The negative
# evidence flag cannot re-arm or release; an independent finance reviewer can.
root = api.Environment(env.cr, 1, {})
manager = bound(root, fixture['actors']['manager'], fixture['sessions']['manager'])
for label, outcome in (('u', 'unknown'), ('f', 'failed')):
    result = manager._operate('refund_uncertain', {'refund_id': fixture['refunds'][label],
        'outcome': outcome, 'reason': 'FC2 synthetic no payout completed'}, key())
    assert result['state'] == outcome and result['actually_refunded'] == 0
commit('B', 'B_unknown_failed')
root, unresolved = review(fixture, 'B_unknown_failed')
assert unresolved['refunds']['u']['state'] == 'unknown'
assert unresolved['refunds']['f']['state'] == 'failed'
assert unresolved['counts']['account.payment'] == after_b['counts']['account.payment']
frontdesk = bound(root, fixture['actors']['frontdesk'], fixture['sessions']['frontdesk'])
for label in ('u', 'f'):
    reject('B', frontdesk, 'refund_recover', {'refund_id': fixture['refunds'][label],
        'verified_not_paid': False, 'reason': 'FC2 no proof'}, label + '_recover_without_verification')
    reject('B', frontdesk, 'refund_cancel', {'refund_id': fixture['refunds'][label],
        'verified_not_paid': False, 'evidence': 'FC2 no proof',
        'reason': 'FC2 no proof'}, label + '_cancel_without_verification')
for label in ('u', 'f'):
    recovered = frontdesk._operate('refund_recover', {'refund_id': fixture['refunds'][label],
        'verified_not_paid': True, 'reason': 'FC2 synthetic manual review confirmed no payout'}, key())
    assert recovered['state'] == 'approved' and recovered['actually_refunded'] == 0
    cancelled = frontdesk._operate('refund_cancel', {'refund_id': fixture['refunds'][label],
        'verified_not_paid': True, 'evidence': 'FC2 synthetic bank/cash review no payment',
        'reason': 'FC2 release after reviewer verification'}, key())
    assert cancelled['state'] == 'cancelled' and cancelled['actually_refunded'] == 0
commit('B', 'B_verified_recover_release')
root, after_recovery = review(fixture, 'B_recovered')
assert after_recovery['refunds']['u']['state'] == 'cancelled'
assert after_recovery['refunds']['f']['state'] == 'cancelled'
assert after_recovery['counts']['account.payment'] == after_b['counts']['account.payment']
manager = bound(root, fixture['actors']['manager'], fixture['sessions']['manager'])
assert manager._refund_capacity(root['ydental.settlement.payment'].browse(fixture['payments']['ab'])) == 75
env.cr.rollback()

# C: actual refund wins against close for the SAME executor/cashier, day/channel.
c_payload = {'refund_id': fixture['refunds']['c'],
    'actual_utc': datetime.now(timezone.utc).isoformat(),
    'proof': 'FC2 actual synthetic card refund same cashier'}
c_done, c_loser = race('C', 'frontdesk', ('refund_execute', c_payload, key()),
    'frontdesk_close', ('close', {'business_date': fixture['today'], 'channel': 'card'}, key()),
    fixture, 'C_execute_first')
root, after_c_race = review(fixture, 'C_race')
assert after_c_race['refunds']['c']['state'] == 'done'
assert after_c_race['refunds']['c']['executor'] == fixture['actors']['frontdesk']
assert after_c_race['refunds']['c']['actual_date'] == fixture['today']
assert after_c_race['refunds']['c']['channel'] == 'card'
assert after_c_race['refunds']['c']['outbound_journal'] == fixture['journals']['card']
assert root['ydental.settlement.close'].sudo().browse(fixture['old_card_close']).ydental_gross == 100
assert root['ydental.settlement.close'].sudo().browse(fixture['old_card_close']).ydental_refunded == 0
assert after_c_race['counts']['ydental.settlement.close'] == 1
env.cr.rollback()
root = api.Environment(env.cr, 1, {})
frontdesk = bound(root, fixture['actors']['frontdesk'], fixture['sessions']['frontdesk_close'])
c_close = frontdesk._operate('close', {'business_date': fixture['today'], 'channel': 'card'}, key())
assert (c_close['gross'], c_close['refunded'], c_close['pending'], c_close['net']) == (0, 30, 0, -30)
commit('C', 'C_same_cashier_close')
root, after_c_close = review(fixture, 'C_close')
assert root['ydental.settlement.close'].sudo().browse(fixture['old_card_close']).ydental_refunded == 0
event('C', 'same_cashier_day_channel', executor=fixture['actors']['frontdesk'],
      business_day=fixture['today'], channel='card', result=c_close)
env.cr.rollback()

# D: the REAL source is WeChat; the old cash label is first locked, then
# corrected by a separate finance reviewer. No arbitrary cross-channel payout.
root = api.Environment(env.cr, 1, {})
manager = bound(root, fixture['actors']['manager'], fixture['sessions']['manager'])
frontdesk = bound(root, fixture['actors']['frontdesk'], fixture['sessions']['frontdesk'])
doctor = bound(root, fixture['actors']['doctor'], fixture['sessions']['doctor'])
old_cash = manager._operate('close', {'business_date': fixture['old_day'], 'channel': 'cash'}, key())
assert old_cash['gross'] == 100 and old_cash['refunded'] == 0
commit('D', 'D_cash_history_close')
root, after_old_cash = review(fixture, 'D_cash_close')
manager = bound(root, fixture['actors']['manager'], fixture['sessions']['manager'])
frontdesk = bound(root, fixture['actors']['frontdesk'], fixture['sessions']['frontdesk'])
doctor = bound(root, fixture['actors']['doctor'], fixture['sessions']['doctor'])
reject('D', doctor, 'unlock', {'close_id': old_cash['close_id'],
    'reason': 'FC2 unauthorized finance unlock'}, 'no_finance_approval')
reject('D', frontdesk, 'reclassify', {'payment_id': fixture['payments']['d'],
    'new_channel': 'wechat', 'reason': 'FC2 real WeChat proof'}, 'locked_cash_day')
assert root['ydental.settlement.correction'].sudo().search_count([
    ('ydental_payment_id', '=', fixture['payments']['d'])]) == 0
env.cr.rollback()
root = api.Environment(env.cr, 1, {})
manager = bound(root, fixture['actors']['manager'], fixture['sessions']['manager'])
frontdesk = bound(root, fixture['actors']['frontdesk'], fixture['sessions']['frontdesk'])
original_cash = root['ydental.settlement.payment'].sudo().browse(fixture['payments']['d']).ydental_payment_id
assert original_cash.journal_id.id == fixture['journals']['cash']
unlocked = frontdesk._operate('unlock', {'close_id': old_cash['close_id'],
    'reason': 'FC2 reviewed actual WeChat receipt proof'}, key())
assert unlocked['state'] == 'unlocked'
correction = frontdesk._operate('reclassify', {'payment_id': fixture['payments']['d'],
    'new_channel': 'wechat', 'reason': 'FC2 verified originally paid by WeChat'}, key())
assert correction['old_channel'] == 'cash' and correction['new_channel'] == 'wechat'
assert root['account.move'].sudo().browse(correction['move_id']).state == 'posted'
old_wechat = manager._operate('close', {'business_date': fixture['old_day'],
    'channel': 'wechat'}, key())
assert old_wechat['gross'] == 100 and old_wechat['refunded'] == 0
commit('D', 'D_unlock_correct_old_reclose')
root, after_correction = review(fixture, 'D_corrected')
assert root['ydental.settlement.close'].sudo().browse(old_cash['close_id']).ydental_gross == 100
assert root['ydental.settlement.close'].sudo().browse(old_cash['close_id']).ydental_state == 'unlocked'
assert root['ydental.settlement.payment'].sudo().browse(fixture['payments']['d']).ydental_payment_id.journal_id.id == fixture['journals']['cash']
manager = bound(root, fixture['actors']['manager'], fixture['sessions']['manager'])
reject('D', manager, 'refund_execute', {'refund_id': fixture['refunds']['d'],
    'actual_utc': (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
    'proof': 'FC2 forbidden backdated payout'}, 'wrong_day_before_request_or_correction')
env.cr.rollback()
root = api.Environment(env.cr, 1, {})
manager = bound(root, fixture['actors']['manager'], fixture['sessions']['manager'])
d_done = manager._operate('refund_execute', {'refund_id': fixture['refunds']['d'],
    'actual_utc': datetime.now(timezone.utc).isoformat(),
    'proof': 'FC2 confirmed actual WeChat offline refund'}, key())
assert d_done['state'] == 'done' and d_done['actually_refunded'] == 40
commit('D', 'D_actual_wechat_refund')
root, after_d_refund = review(fixture, 'D_refund')
assert after_d_refund['refunds']['d']['actual_date'] == fixture['today']
assert after_d_refund['refunds']['d']['channel'] == 'wechat'
assert after_d_refund['refunds']['d']['outbound_journal'] == fixture['journals']['wechat']
assert after_d_refund['refunds']['d']['outbound_state'] == 'posted'
assert after_d_refund['refunds']['d']['outbound_amount'] == 40
assert root['ydental.settlement.close'].sudo().browse(old_wechat['close_id']).ydental_refunded == 0
assert root['ydental.settlement.close'].sudo().browse(old_cash['close_id']).ydental_refunded == 0
env.cr.rollback()
root = api.Environment(env.cr, 1, {})
manager = bound(root, fixture['actors']['manager'], fixture['sessions']['manager'])
d_close = manager._operate('close', {'business_date': fixture['today'], 'channel': 'wechat'}, key())
assert (d_close['gross'], d_close['refunded'], d_close['pending'], d_close['net']) == (0, 40, 0, -40)
commit('D', 'D_today_wechat_close')
root, final = review(fixture, 'final')
assert root['ydental.settlement.close'].sudo().browse(old_cash['close_id']).ydental_gross == 100
assert root['ydental.settlement.close'].sudo().browse(old_wechat['close_id']).ydental_gross == 100
assert final['refunds']['d']['outbound_journal'] != fixture['journals']['cash']
assert commit_count == 11
assert final['counts']['mail.mail'] == 0
env.cr.rollback()
event('FC2', 'COMPLETE', commits=commit_count, status='ODOO_PASS_COMMITTED',
      cases=['A', 'B', 'C', 'D'])
print('S10_FC2_COMPLETE', json.dumps({'commits': commit_count, 'cases': ['A', 'B', 'C', 'D']}), flush=True)

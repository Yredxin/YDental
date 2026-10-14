"""FC1 one Odoo shell, two independent ORM cursors, seven planned business commits.

The shell command is dispatched only by s10_fc1_control.py after the #34 checkpoint.
No business action uses another Odoo registry process.
"""

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
NAME = 'ydental_s10_test_20261014145000_fc1a84d7'
AUTH = 6170892559
assert RUN.name == NAME and env.cr.dbname == NAME
assert stat.S_IMODE(RUN.stat().st_mode) == 0o700
MARKER = json.loads((RUN / 'database.json').read_text())
assert MARKER['database'] == NAME and MARKER['auth'] == AUTH
assert MARKER['shell_sha256'] == hashlib.sha256(Path('/home/redxin/code/odoo/odoo-sd/code/sd-addons/scripts/s10_fc1_shell.py').read_bytes()).hexdigest()
env.cr.execute('SELECT oid FROM pg_database WHERE datname=%s', [NAME])
assert env.cr.fetchone()[0] == MARKER['oid']
env.cr.execute('SELECT system_identifier::text FROM pg_control_system()')
assert env.cr.fetchone()[0] == MARKER['cluster']

ROOT = api.Environment(env.cr, 1, {})
EVIDENCE = RUN / 'fc1-evidence.jsonl'
LEDGER = RUN / 'fc1-commit-ledger.jsonl'
MAX_COMMITS = 8
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
    assert purpose in ('fixture', 'A_approval', 'B_execute', 'C_refund_close',
                       'C_refund_after_close', 'C_reclass_close', 'C_unlock_reclass_reclose')
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
    # The approved global Settings policy is applied explicitly by the synthetic
    # superuser before the second native warehouse. The S07 service never does it.
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
    for role in ('manager', 'frontdesk', 'doctor'):
        f.admin._grant(f.users[role].id, store.id,
                       {'settlement': 'write', 'finance_approval': 'write'})
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
        account = root['account.account'].create({'name': 'FC1 synthetic outstanding ' + channel,
            'code': 'X' + str(store.id).zfill(3) + str(index),
            'account_type': 'asset_current', 'company_ids': [Command.link(company.id)]})
        journal = root['account.journal'].create({'name': 'FC1 synthetic ' + channel,
            'code': 'X' + str(index) + str(store.id), 'type': 'bank', 'company_id': company.id})
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
    pay_a = manager._operate('pay', {'invoice_ids': [invoices[0]], 'amount': 100,
        'channel': 'card', 'actual_utc': today, 'proof': 'FC1 synthetic offline receipt A'}, key())['payment_id']
    pay_c_refund = frontdesk._operate('pay', {'invoice_ids': [invoices[1]], 'amount': 100,
        'channel': 'card', 'actual_utc': yesterday, 'proof': 'FC1 synthetic prior-day receipt C'}, key())['payment_id']
    pay_c_cash = manager._operate('pay', {'invoice_ids': [invoices[2]], 'amount': 100,
        'channel': 'cash', 'actual_utc': yesterday, 'proof': 'FC1 synthetic mislabeled cash'}, key())['payment_id']
    a = manager._operate('refund_request', {'payment_id': pay_a, 'amount': 20,
        'reason': 'FC1 synthetic concurrent approval', 'request_key': key()}, key())['refund_id']
    b = manager._operate('refund_request', {'payment_id': pay_a, 'amount': 25,
        'reason': 'FC1 synthetic actual refund', 'request_key': key()}, key())['refund_id']
    c = frontdesk._operate('refund_request', {'payment_id': pay_c_refund, 'amount': 30,
        'reason': 'FC1 synthetic current-day refund', 'request_key': key()}, key())['refund_id']
    for refund_id, service in ((b, frontdesk), (c, manager)):
        outcome = service._operate('refund_approve', {'refund_id': refund_id,
            'reason': 'FC1 separate finance approval'}, key())
        assert outcome['state'] == 'approved' and outcome['actually_refunded'] == 0
    with env.cr.savepoint():
        try:
            manager._operate('refund_approve', {'refund_id': a, 'reason': 'Forbidden own approval'}, key())
        except AccessError:
            event('A', 'self_approval_expected_reject')
        else:
            raise AssertionError('Requester self-approved')
    sessions = {role: session(root, f.users[role], store) for role in ('manager', 'frontdesk', 'doctor')}
    assert sorted(group_user.implied_ids.ids) == implied
    fixture = {'store_id': store.id, 'company_id': company.id,
               'actors': {role: f.users[role].id for role in sessions}, 'sessions': sessions,
               'payments': {'a': pay_a, 'c_refund': pay_c_refund, 'c_cash': pay_c_cash},
               'invoices': invoices, 'refunds': {'a': a, 'b': b, 'c': c},
               'yesterday': str(root['ydental.settlement.payment'].browse(pay_c_refund).ydental_business_date),
               'today': str(root['ydental.settlement.payment'].browse(pay_a).ydental_business_date),
               'journals': {channel: cfg['ydental_' + channel + '_journal_id'] for channel in ('card', 'cash', 'wechat')},
               'groups': implied}
    assert fixture['yesterday'] != fixture['today']
    assert all(x['move_state'] == 'posted' for x in native(root, fixture['payments']).values())
    event('fixture', 'precommit', counts=counts(root), native=native(root, fixture['payments']),
          refunds={name: refund_state(root, rid) for name, rid in fixture['refunds'].items()},
          groups=implied)
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
    thread = threading.Thread(target=other, name='fc1-second-backend', daemon=False)
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


fixture = initial_fixture()
root, baseline = review(fixture, 'fixture')
assert baseline['refunds']['a']['state'] == 'requested'

# A: two distinct finance reviewers contend for exactly one approval.
approval_key = key()
approved, loser = race('A', 'frontdesk', ('refund_approve',
    {'refund_id': fixture['refunds']['a'], 'reason': 'FC1 first finance reviewer'}, approval_key),
    'doctor', ('refund_approve', {'refund_id': fixture['refunds']['a'],
    'reason': 'FC1 second finance reviewer'}, key()), fixture, 'A_approval')
root, after_a = review(fixture, 'A')
assert after_a['refunds']['a']['state'] == 'approved'
assert after_a['refunds']['a']['approver'] == fixture['actors']['frontdesk']
assert after_a['refunds']['a']['outbound_id'] is None
assert after_a['counts']['account.payment'] == baseline['counts']['account.payment']
same = bound(root, fixture['actors']['frontdesk'], fixture['sessions']['frontdesk'])._operate(
    'refund_approve', {'refund_id': fixture['refunds']['a'], 'reason': 'FC1 first finance reviewer'}, approval_key)
assert same['result'] == 'already_accepted'
env.cr.rollback()
event('A', 'idempotent_replay_rollback', result=same['result'])

# B: actual confirmed offline refund wins; cancellation waits and must roll back.
actual_b = datetime.now(timezone.utc).isoformat()
done_b, loser_b = race('B', 'manager', ('refund_execute',
    {'refund_id': fixture['refunds']['b'], 'actual_utc': actual_b,
     'proof': 'FC1 confirmed synthetic offline payout'}, key()),
    'frontdesk', ('refund_cancel', {'refund_id': fixture['refunds']['b'],
     'verified_not_paid': True, 'evidence': 'FC1 contested no-payout claim',
     'reason': 'FC1 contested cancellation'}, key()), fixture, 'B_execute')
root, after_b = review(fixture, 'B')
assert after_b['refunds']['b']['state'] == 'done'
assert after_b['refunds']['b']['outbound_state'] == 'posted'
assert after_b['refunds']['b']['outbound_amount'] == 25
assert after_b['counts']['account.payment'] == after_a['counts']['account.payment'] + 1
assert len(after_b['refunds']['b']['credits']) == 1
assert after_b['refunds']['b']['credits'][0][1:] == ('posted', 25.0)
env.cr.rollback()

# C1: yesterday's receipt, today's pending approval. The cashier close wins
# before the distinct refund executor; a fresh cursor must see no half payout.
close_card, close_loser = race('C_refund', 'frontdesk', ('close',
    {'business_date': fixture['today'], 'channel': 'card'}, key()),
    'manager', ('refund_execute', {'refund_id': fixture['refunds']['c'],
    'actual_utc': datetime.now(timezone.utc).isoformat(),
    'proof': 'FC1 synthetic today refund after prior-day receipt'}, key()),
    fixture, 'C_refund_close')
root, after_c_close = review(fixture, 'C_refund_close')
assert after_c_close['refunds']['c']['state'] == 'approved'
close = root['ydental.settlement.close'].sudo().browse(close_card['close_id'])
assert close.ydental_refunded == 0 and close.ydental_pending == 30
assert close.ydental_gross == 0
env.cr.rollback()

# The distinct executor's day is not cashier frontdesk's closed day.
root = api.Environment(env.cr, 1, {})
manager = bound(root, fixture['actors']['manager'], fixture['sessions']['manager'])
later = manager._operate('refund_execute', {'refund_id': fixture['refunds']['c'],
    'actual_utc': datetime.now(timezone.utc).isoformat(),
    'proof': 'FC1 confirmed synthetic current-day card payout'}, key())
assert later['state'] == 'done' and later['actually_refunded'] == 30
commit('C_refund', 'C_refund_after_close')
root, after_c_refund = review(fixture, 'C_refund_after_close')
assert after_c_refund['refunds']['c']['actual_date'] == fixture['today']
assert after_c_refund['refunds']['c']['outbound_journal'] == fixture['journals']['card']
assert root['ydental.settlement.close'].sudo().browse(close_card['close_id']).ydental_refunded == 0
env.cr.rollback()

# C2: a different operator tries to correct old cash to WeChat while that
# cashier confirms the old cash day. After its rollback, finance unlocks,
# correction posts a balanced native entry, then cashier closes WeChat.
cash_close, cash_loser = race('C_reclass', 'manager', ('close',
    {'business_date': fixture['yesterday'], 'channel': 'cash'}, key()),
    'frontdesk', ('reclassify', {'payment_id': fixture['payments']['c_cash'],
    'new_channel': 'wechat', 'reason': 'FC1 synthetic reviewed WeChat source'}, key()),
    fixture, 'C_reclass_close')
root, after_cash_close = review(fixture, 'C_reclass_close')
cash = root['ydental.settlement.close'].sudo().browse(cash_close['close_id'])
assert cash.ydental_gross == 100 and cash.ydental_refunded == 0
assert root['ydental.settlement.correction'].sudo().search_count([
    ('ydental_payment_id', '=', fixture['payments']['c_cash'])]) == 0
frontdesk = bound(root, fixture['actors']['frontdesk'], fixture['sessions']['frontdesk'])
manager = bound(root, fixture['actors']['manager'], fixture['sessions']['manager'])
unlocked = frontdesk._operate('unlock', {'close_id': cash.id,
    'reason': 'FC1 reviewed original proof'}, key())
assert unlocked['state'] == 'unlocked'
correction = frontdesk._operate('reclassify', {'payment_id': fixture['payments']['c_cash'],
    'new_channel': 'wechat', 'reason': 'FC1 synthetic reviewed WeChat source'}, key())
assert correction['old_channel'] == 'cash' and correction['new_channel'] == 'wechat'
reclosed = manager._operate('close', {'business_date': fixture['yesterday'],
    'channel': 'wechat'}, key())
assert reclosed['gross'] == 100 and reclosed['refunded'] == 0
commit('C_reclass', 'C_unlock_reclass_reclose')
root, final = review(fixture, 'final')
assert root['account.move'].sudo().browse(correction['move_id']).state == 'posted'
assert root['ydental.settlement.close'].sudo().browse(cash_close['close_id']).ydental_gross == 100
assert root['ydental.settlement.close'].sudo().browse(cash_close['close_id']).ydental_state == 'unlocked'
assert final['refunds']['c']['outbound_journal'] == fixture['journals']['card']
assert commit_count == 7
env.cr.rollback()
event('FC1', 'COMPLETE', commits=commit_count, status='ODOO_PASS_COMMITTED',
      cases=['A', 'B', 'C_refund', 'C_reclass'])
print('S10_FC1_COMPLETE', json.dumps({'commits': commit_count, 'cases': ['A', 'B', 'C_refund', 'C_reclass']}), flush=True)

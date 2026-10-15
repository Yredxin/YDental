"""UI1 one-commit synthetic fixture, executed by the bounded Odoo shell."""

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

from odoo.addons.ydental_settlement_test import pre_init_hook

SCRIPTS = Path('/home/redxin/code/odoo/odoo-sd/code/sd-addons/scripts')
sys.path.insert(0, str(SCRIPTS))
from s10_ui1_r2_contract import validate_marker

RUN = Path(os.environ['YDENTAL_S10_RUN_DIR'])
NAME = 'ydental_s10_test_20261015014500_c72e6f91'
AUTH = 6182293301
assert RUN.name == NAME and env.cr.dbname == NAME
MARKER = json.loads((RUN / 'database.json').read_text())
env.cr.execute('SELECT oid FROM pg_database WHERE datname=%s', [NAME])
real_oid = env.cr.fetchone()[0]
env.cr.execute('SELECT system_identifier::text FROM pg_control_system()')
real_cluster = env.cr.fetchone()[0]
actual_core = subprocess.check_output(['git', '-C', str(SCRIPTS.parent.parent), 'rev-parse', 'HEAD'], text=True).strip()
validate_marker(marker=MARKER, database=NAME, oid=real_oid, cluster=real_cluster,
    actual_core=actual_core, config=RUN / 'odoo.conf', run=RUN,
    auth=AUTH, base='d59f15d364c3d00641fdb7a155fcbb35236838a5', port=18271,
    source='ydental_s10_test_20261014044700_4f6a8d2c', source_oid=2100080,
    policy=RUN / 'network-policy/sitecustomize.py',
    prepare=SCRIPTS / 's10_ui1_r2_prepare.py',
    control=SCRIPTS / 's10_ui1_r2_control.py',
    browser=SCRIPTS / 's10_ui1_r2_browser.py',
    contract=SCRIPTS / 's10_ui1_r2_contract.py')
# This fixed adapter guard is deliberately run before any group, store, patient,
# price, inventory, fee or settlement preparation.
pre_init_hook(env)

from odoo import Command, api
from odoo.addons.ydental_treatment_test.tests.common import key, price
from odoo.addons.ydental_treatment_test.tests.treatment_common import setup, receive, opened_actual, execute_args

ROOT = api.Environment(env.cr, 1, {})
assert ROOT['ydental.access.store'].search_count([]) == 0
assert ROOT['account.move'].search_count([]) == 0

# The Settings administrator explicitly enables the approved native global groups
# in this isolated clone before the second store's warehouse is initialized.
group_user = ROOT.ref('base.group_user')
for xmlid in ('stock.group_stock_multi_warehouses',
              'stock.group_stock_multi_locations', 'product.group_product_pricelist'):
    group = ROOT.ref(xmlid)
    if group not in group_user.implied_ids:
        group_user._apply_group(group)
    assert group in group_user.implied_ids
implied = sorted(group_user.implied_ids.ids)

fixture = SimpleNamespace(env=ROOT)
setup(fixture)
store = fixture.stores[0]
other_store = fixture.stores[1]
fixture.admin._grant(fixture.users['manager'].id, store.id,
                     {'settlement': 'write', 'finance_approval': 'write'})
fixture.admin._grant(fixture.users['frontdesk'].id, store.id,
                     {'settlement': 'write', 'finance_approval': 'write', 'export': 'write'})
fixture.admin._grant(fixture.users['reader'].id, store.id, {'settlement': 'read'})
fixture.admin._grant(fixture.users['manager'].id, other_store.id,
                     {'settlement': 'write', 'finance_approval': 'write'})
assert group_user.implied_ids.ids and sorted(group_user.implied_ids.ids) == implied

company = store.company_id
root = fixture.root['base'].with_company(company).env
income = root['account.account'].search([('account_type', '=', 'income'),
    ('company_ids', 'in', company.id)], limit=1)
sales = root['account.journal'].search([('type', '=', 'sale'), ('company_id', '=', company.id)], limit=1)
general = root['account.journal'].search([('type', '=', 'general'), ('company_id', '=', company.id)], limit=1)
assert income and sales and general
cfg = {'ydental_store_id': store.id, 'company_id': company.id,
       'ydental_policy': 'demo_confirmation', 'ydental_sales_journal_id': sales.id,
       'ydental_income_account_id': income.id, 'ydental_adjustment_journal_id': general.id}
for index, channel in enumerate(('cash', 'wechat', 'alipay', 'card'), 1):
    account = root['account.account'].create({'name': 'UI1 synthetic outstanding ' + channel,
        'code': 'U' + str(store.id).zfill(3) + str(index),
        'account_type': 'asset_current', 'company_ids': [Command.link(company.id)]})
    journal = root['account.journal'].create({'name': 'UI1 synthetic ' + channel,
        'code': 'U' + str(index) + str(store.id), 'type': 'bank', 'company_id': company.id})
    for line in journal.inbound_payment_method_line_ids | journal.outbound_payment_method_line_ids:
        if line.payment_method_id.code == 'manual':
            line.write({'payment_account_id': account.id})
    cfg['ydental_' + channel + '_journal_id'] = journal.id
root['ydental.settlement.config']._new(cfg)

receive(fixture, 10)
price(fixture, 100)
treatment, _clinical, _queue, _lease, _execution, _document, args = opened_actual(fixture)
fees = []
for _ in range(2):
    actual = treatment._operate('execute', execute_args(fixture, args), key())
    assert actual['amount'] == 100
    fees.append(actual['fee_id'])
fee_records = root['ydental.treatment.fee'].browse(fees)
assert len(fee_records.mapped('ydental_patient_id')) == 1
assert all(x.ydental_price_snapshot_id or x.ydental_price_review_id for x in fee_records)
assert root['account.move'].search_count([]) == 0

snapshot = {'db': NAME, 'oid': MARKER['oid'], 'store_id': store.id,
            'other_store_id': other_store.id, 'company_id': company.id,
            'patient_id': fee_records[0].ydental_patient_id.id,
            'fees': fees, 'actors': {role: fixture.users[role].id
                for role in ('manager', 'frontdesk', 'reader', 'none')},
            'journals': {channel: cfg['ydental_' + channel + '_journal_id']
                for channel in ('cash', 'wechat', 'alipay', 'card')},
            'global_groups': implied, 'prepared_at': datetime.now(timezone.utc).isoformat()}
counts = {name: root[name].sudo().search_count([]) for name in
          ('ydental.access.audit', 'mail.message', 'mail.mail', 'bus.bus',
           'ydental.settlement.receipt', 'ydental.treatment.fee', 'account.move')}
bus = Counter(str(kind) for _channel, kind, _payload in env.cr.precommit.data.get('bus.bus.values', ()))
with (RUN / 'fixture-before-commit.json').open('x') as stream:
    json.dump({'purpose': 'fixture', 'counts': counts, 'bus_precommit_intents': dict(bus)}, stream, indent=2)
    stream.write('\n')
env.cr.commit()
with (RUN / 'fixture.json').open('x') as stream:
    json.dump(snapshot, stream, indent=2)
    stream.write('\n')
with (RUN / 'ui1-commit-ledger.jsonl').open('x') as stream:
    stream.write(json.dumps({'number': 1, 'name': 'fixture', 'status': 'COMMITTED',
        'utc': datetime.now(timezone.utc).isoformat()}) + '\n')
print('UI1_PREPARED', json.dumps({'oid': MARKER['oid'], 'stores': 2, 'fees': 2, 'business_commits': 1}), flush=True)

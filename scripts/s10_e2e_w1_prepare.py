"""Prepare legal synthetic masters only; every fee, stock issue and payment is Web owned."""

from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

from odoo import Command, api, fields
from odoo.addons.ydental_settlement_test import pre_init_hook

SCRIPTS = Path('/home/redxin/code/odoo/odoo-sd/code/sd-addons/scripts')
sys.path.insert(0, str(SCRIPTS))
from s10_e2e_w1_contract import validate_marker
from s10_e2e_w1_control import AUTH, BASE, BROWSER, CLUSTER, CONTRACT, CONTROL, NAME, POLICY, PORT, RUN, SHELL, SOURCE

assert Path(os.environ['YDENTAL_S10_RUN_DIR']) == RUN and env.cr.dbname == NAME
marker = json.loads((RUN / 'database.json').read_text())
env.cr.execute('SELECT oid FROM pg_database WHERE datname=%s', [NAME])
oid = env.cr.fetchone()[0]
env.cr.execute('SELECT system_identifier::text FROM pg_control_system()')
cluster = env.cr.fetchone()[0]
core = subprocess.check_output(['git', '-C', str(SCRIPTS.parent.parent), 'rev-parse', 'HEAD'], text=True).strip()
validate_marker(marker=marker, database=NAME, oid=oid, cluster=cluster,
                actual_core=core, config=RUN / 'odoo.conf', run=RUN,
                auth=AUTH, base=BASE, port=PORT, source=SOURCE, source_oid=2100080,
                policy=RUN / 'network-policy/sitecustomize.py', prepare=SHELL,
                control=CONTROL, browser=BROWSER, contract=CONTRACT)
pre_init_hook(env)

from odoo.addons.ydental_treatment_test.tests.common import key, price, patient
from odoo.addons.ydental_treatment_test.tests.treatment_common import setup, receive

root = api.Environment(env.cr, 1, {})
assert root['ydental.access.store'].search_count([]) == 0
assert root['account.move'].search_count([]) == 0
assert root['ydental.treatment.fee'].search_count([]) == 0
group_user = root.ref('base.group_user')
for xmlid in ('stock.group_stock_multi_warehouses', 'stock.group_stock_multi_locations',
              'product.group_product_pricelist'):
    group = root.ref(xmlid)
    if group not in group_user.implied_ids:
        group_user._apply_group(group)
    assert group in group_user.implied_ids

fixture = SimpleNamespace(env=root)
setup(fixture)
store = fixture.stores[0]
fixture.admin._grant(fixture.users['manager'].id, store.id,
                     {'settlement': 'write', 'finance_approval': 'write', 'exam': 'write'})
fixture.admin._grant(fixture.users['frontdesk'].id, store.id,
                     {'settlement': 'write'})
fixture.admin._grant(fixture.users['reader'].id, store.id,
                     {'settlement': 'read'})
fixture.admin._grant(fixture.second.id, store.id, {'exam': 'write'})

# The helper's first care slot has seconds and a five minute lifetime. Build a
# minute-aligned slot on its existing second care chair, with explicit coverage.
# Browser HTML datetime-local can then express the exact published interval.
supply = fixture.group.env['ydental.supply.service']
slot_start = fields.Datetime.now().replace(second=0, microsecond=0) + timedelta(minutes=20)
slot_end = slot_start + timedelta(hours=3)
slot_result = supply._operate('slot', {
    'station_id': fixture.other_station.id,
    'start': fields.Datetime.to_string(slot_start),
    'end': fields.Datetime.to_string(slot_end), 'total': 12,
    'capability_ids': fixture.capabilities[0].ids,
    'reason': 'W1 minute-aligned synthetic Web qualification'}, key())
slot = fixture.root['ydental.supply.slot'].browse(slot_result['id'])
supply._operate('publish', {'id': slot.id, 'version': slot.ydental_version,
                           'user_ids': [fixture.users['manager'].id],
                           'reason': 'W1 explicit synthetic staff coverage'}, key())
assert slot.ydental_start == slot_start and slot.ydental_end == slot_end and slot.state == 'published'

company = store.company_id
account_env = fixture.root['base'].with_company(company).env
income = account_env['account.account'].search([('account_type', '=', 'income'),
                                                 ('company_ids', 'in', company.id)], limit=1)
sales = account_env['account.journal'].search([('type', '=', 'sale'), ('company_id', '=', company.id)], limit=1)
general = account_env['account.journal'].search([('type', '=', 'general'), ('company_id', '=', company.id)], limit=1)
assert income and sales and general
config = {'ydental_store_id': store.id, 'company_id': company.id,
          'ydental_policy': 'demo_confirmation', 'ydental_sales_journal_id': sales.id,
          'ydental_income_account_id': income.id, 'ydental_adjustment_journal_id': general.id}
for index, channel in enumerate(('cash', 'wechat', 'alipay', 'card'), 1):
    account = account_env['account.account'].create({
        'name': 'W1 synthetic offline ' + channel + ' outstanding',
        'code': 'W' + str(store.id).zfill(3) + str(index),
        'account_type': 'asset_current', 'company_ids': [Command.link(company.id)]})
    journal = account_env['account.journal'].create({
        'name': 'W1 synthetic offline ' + channel, 'code': 'W' + str(index) + str(store.id),
        'type': 'bank', 'company_id': company.id})
    for line in journal.inbound_payment_method_line_ids | journal.outbound_payment_method_line_ids:
        if line.payment_method_id.code == 'manual':
            line.write({'payment_account_id': account.id})
    config['ydental_' + channel + '_journal_id'] = journal.id
account_env['ydental.settlement.config']._new(config)

receive(fixture, 20, 'material')
receive(fixture, 20, 'medicine')
price(fixture, 600)
price(fixture, 80, catalog=fixture.catalogs[2])
price(fixture, 10, catalog=fixture.drug_catalog)
reviewer = fixture.group.env['ydental.exam.service']
reviewer._operate('review_capability', {'capability_id': fixture.catalogs[2].ydental_capability_id.id,
                                         'family': 'panorama', 'reason': 'W1 synthetic capability review'}, key())
reviewer._operate('bind_template', {'catalog_id': fixture.catalogs[2].id,
                                    'code': 'panorama-demo-1',
                                    'reason': 'W1 synthetic approved template'}, key())
patient_id = patient(fixture)

counts = {name: account_env[name].sudo().search_count([]) for name in (
    'ydental.treatment.event', 'ydental.treatment.fee', 'ydental.exam.result',
    'ydental.settlement.source', 'ydental.settlement.receipt', 'ydental.settlement.payment',
    'ydental.settlement.refund', 'account.move', 'account.payment', 'account.partial.reconcile')}
assert all(count == 0 for count in counts.values()), counts
fixture_data = {'database': NAME, 'oid': oid, 'store': store.id,
                'patient': patient_id, 'company': company.id,
                'care_station': fixture.other_station.id,
                'exam_station': fixture.stations[0][2].id,
                'pharmacy_station': fixture.pharmacy_station.id,
                'care_mapping': fixture.mappings[0][0].id,
                'exam_mapping': fixture.mappings[0][2].id,
                'pharmacy_mapping': fixture.drug_mapping.id,
                'care_catalog': fixture.catalogs[0].id,
                'medicine_product': fixture.products['medicine'],
                'material_lot': fixture.lots['material'],
                'medicine_lot': fixture.lots['medicine'],
                'slot_start': fields.Datetime.to_string(slot_start),
                'slot_end': fields.Datetime.to_string(slot_end),
                'roles': {role: user.login for role, user in fixture.users.items()},
                'exam_login': fixture.second.login, 'pharmacy_login': fixture.pharmacist.login,
                'pre_economic_counts': counts}
with (RUN / 'fixture.json').open('x') as stream:
    json.dump(fixture_data, stream, indent=2)
    stream.write('\n')
env.cr.commit()
print('W1_ORM_PREP_ONLY', json.dumps({'oid': oid, 'patient_id': patient_id,
                                    'financial_counts': counts}), flush=True)

from datetime import timedelta

from odoo import fields
from odoo.tests import new_test_user

from .common import setup as clinical_setup, bind, key, opened, save_args, queue_bind, lease_args


def setup(cls):
    clinical_setup(cls)
    for store in cls.stores:
        store.write({'name': 'S08B Synthetic ' + key()})
    cls.root['ir.config_parameter'].set_str('ydental_queue.timeout_seconds', '600')
    cls.admin._grant(cls.users['manager'].id, cls.stores[0].id, {'warehouse': 'write'})
    cls.stock = bind(cls, cls.users['manager']).env['ydental.inventory.service']
    cls.stock._operate('setup', {'code': 'B' + str(cls.stores[0].id)}, key())
    cls.products, cls.lots = {}, {}
    for kind in ('medicine', 'material'):
        result = cls.stock._operate('product', {'code': 'S08B-' + key(), 'name': 'S08B Synthetic ' + kind,
            'kind': kind, 'stock_uom_id': cls.uom.id, 'issue_uom_id': cls.uom.id, 'step': 1,
            'specification': 'Synthetic review only'}, key())
        cls.products[kind] = result['id']
        cls.lots[kind] = cls.stock._operate('lot', {'product_id': result['id'], 'name': 'S08B-' + key(),
            'expiration': fields.Datetime.to_string(fields.Datetime.now() + timedelta(days=45))}, key())['id']
    cls.pharmacist = new_test_user(cls.root, name='S08B Synthetic Pharmacist', login='s08b_pharm_' + key(),
        password='s08b-synthetic-password', groups='ydental_base.ydental_base_group_user')
    cls.admin._join(cls.pharmacist.id, cls.stores[0].id)
    cls.admin._grant(cls.pharmacist.id, cls.stores[0].id, {'pharmacy': 'write'})
    cls.pharmacist.write({'ydental_capability_ids': [fields.Command.set(cls.capabilities[0].ids)]})
    original = cls.stations[0][0]
    cls.pharmacy_area = cls.root['ydental.space.area'].create({'name': 'S08B Pharmacy', 'ydental_store_id': cls.stores[0].id,
        'ydental_floor_id': original.ydental_floor_id.id, 'ydental_reporting': True, 'ydental_missed_limit': 2, 'ydental_purpose': 'pharmacy'})
    cls.pharmacy_station = cls.root['ydental.space.station'].create({'name': 'S08B Dispensing station',
        'ydental_store_id': cls.stores[0].id, 'ydental_floor_id': original.ydental_floor_id.id,
        'ydental_area_id': cls.pharmacy_area.id, 'ydental_kind': 'pharmacy', 'ydental_add_capability_ids': [fields.Command.set(cls.capabilities[0].ids)]})
    cls.group.env['ydental.supply.service']._operate('business', {'area_id': cls.pharmacy_area.id, 'state': 'open', 'reason': 'S08B synthetic open'}, key())
    catalog = cls.group._operate('catalog', {'code': 'S08B-drug-' + key(), 'name': 'S08B Take-away synthetic medicine',
        'kind': 'medicine', 'capability_id': cls.capabilities[0].id, 'uom_id': cls.uom.id}, key())
    cls.drug_catalog = cls.root['ydental.intake.catalog'].browse(catalog['id'])
    mapping = cls.group._operate('mapping', {'catalog_id': cls.drug_catalog.id, 'area_id': cls.pharmacy_area.id,
        'execution_area_id': cls.pharmacy_area.id}, key())
    cls.drug_mapping = cls.root['ydental.intake.mapping'].browse(mapping['id'])


def receive(cls, quantity=20, kind='material'):
    return cls.stock._operate('receive', {'lot_id': cls.lots[kind], 'quantity': quantity, 'uom_id': cls.uom.id,
        'source_key': key(), 'reason': 'S08B evidenced physical receipt'}, key())


def opened_actual(cls):
    clinical, queue, lease, execution, data = opened(cls)
    data.update(clinical._operate('save', save_args(data)))
    args = {'execution_id': execution.id, 'lease_id': lease['lease_id'], 'lease_token': lease['token'],
        'document_id': data['document_id'], 'document_version': data['version']}
    return queue.env['ydental.treatment.service'], clinical, queue, lease, execution, data, args


def execute_args(cls, args, actual=False):
    return args | {'catalog_id': cls.catalogs[0].id, 'quantity': 1, 'source': key(),
        'reason': 'Synthetic physically verified project', 'materials': [{'lot_id': cls.lots['material'],
            'quantity': 1, 'uom_id': cls.uom.id, 'kind': 'treatment'}], 'teeth': [{'tooth': 16, 'state': 'present', 'surfaces': ['O']}],
        'already_performed': actual, 'policy': 'demo_confirmation'}


def prescription(cls, service, args):
    lines = [{'mapping_id': cls.drug_mapping.id, 'quantity': 6, 'uom_id': cls.uom.id, 'product_id': cls.products['medicine'],
        'specification': 'Synthetic specification', 'usage': 'Synthetic explicit usage', 'frequency': 'Synthetic frequency', 'course': 'Synthetic course'}]
    draft = service._operate('order', args | {'kind': 'prescription', 'purpose': 'Synthetic take-away demonstration', 'lines': lines}, key())
    issued = service._operate('issue', args | {'order_id': draft['order_id'], 'version': draft['version']}, key())
    return issued


def pharmacy_start(cls, issued, task_id=None):
    task = cls.root['ydental.intake.task'].browse(task_id or issued['task_ids'][0])
    cls.front._operate('arrive', {'patient_id': task.ydental_patient_id.id}, key())
    cls.front._operate('report', {'task_id': task.id, 'version': task.ydental_version}, key())
    queue = queue_bind(cls, cls.pharmacist)
    lease = queue._operate('enter', {'station_id': cls.pharmacy_station.id})
    call = queue._operate('call', lease_args(lease))
    assert call['task_id'] == task.id
    actual = queue._operate('start', lease_args(lease) | {'entry_id': call['entry_id']})
    return queue.env['ydental.treatment.service'], {'execution_id': actual['execution_id'], 'lease_id': lease['lease_id'],
        'lease_token': lease['token'], 'order_id': issued['order_id'], 'order_version': issued['version']}

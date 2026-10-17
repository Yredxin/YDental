from datetime import timedelta
import secrets

from odoo import fields
from odoo.tests import new_test_user


def key():
    return secrets.token_hex(12)


def bind(cls, user, store=None, session_key=None):
    access = cls.root['ydental.access.service'].with_user(user)
    session = access._session_for_key(session_key or key())
    access = access._bind(session)
    access._switch((store or cls.stores[0]).id)
    return access._bind(session).env['ydental.intake.service']


def setup(cls):
    cls.root = cls.env['base'].env
    root = cls.root
    offset = 12 - fields.Datetime.now().hour
    timezone = 'Etc/GMT%+d' % -offset if offset else 'UTC'
    cls.stores = root['ydental.access.store'].create([
        {'name': 'P020-B Synthetic A ' + key(), 'company_id': root.company.id, 'ydental_timezone': timezone},
        {'name': 'P020-B Synthetic B ' + key(), 'company_id': root.company.id, 'ydental_timezone': timezone}])
    cls.users = {}
    for role in ('manager', 'frontdesk', 'doctor', 'reader', 'price', 'none', 'catalog'):
        groups = 'ydental_base.ydental_base_group_user'
        if role in ('manager', 'catalog'):
            groups += ',ydental_access.ydental_group_manager'
        cls.users[role] = new_test_user(root, name='P020-B Synthetic ' + role,
            login='s06a_' + role + '_' + key()[:8], password='s05-test-password', groups=groups)
    access = root['ydental.access.service'].with_user(cls.users['manager'])
    cls.admin = access._bind(access._session_for_key(key()))
    for user in cls.users.values():
        for store in cls.stores:
            cls.admin._join(user.id, store.id)
    for store in cls.stores:
        cls.admin._grant(cls.users['manager'].id, store.id, dict.fromkeys(('frontdesk', 'patient', 'price', 'medical', 'capacity', 'space', 'export'), 'write'))
        cls.admin._grant(cls.users['frontdesk'].id, store.id, {'frontdesk': 'write'})
        cls.admin._grant(cls.users['doctor'].id, store.id, {'medical': 'write'})
        cls.admin._grant(cls.users['reader'].id, store.id, {'frontdesk': 'read', 'price': 'read'})
        cls.admin._grant(cls.users['price'].id, store.id, {'price': 'write'})
    cls.group = bind(cls, cls.users['manager'])
    cls.front = bind(cls, cls.users['frontdesk'])
    cls.doctor = bind(cls, cls.users['doctor'])
    cls.reader = bind(cls, cls.users['reader'])
    cls.pricer = bind(cls, cls.users['price'])
    cls.capabilities = root['ydental.access.capability'].create([
        {'name': 'P020-B Cleaning', 'ydental_code': 's06a_clean_' + key()},
        {'name': 'P020-B Implant', 'ydental_code': 's06a_implant_' + key()},
        {'name': 'P020-B Panorama', 'ydental_code': 's06a_pan_' + key()},
        {'name': 'P020-B CBCT', 'ydental_code': 's06a_cbct_' + key()}])
    cls.users['manager'].write({'ydental_capability_ids': [fields.Command.set(cls.capabilities.ids)]})
    cls.areas, cls.stations, cls.mappings, cls.slots = [], [], [], []
    cls.start = fields.Datetime.now().replace(microsecond=0) + timedelta(minutes=5)
    cls.end = cls.start + timedelta(minutes=5)
    cls.uom = root.ref('uom.product_uom_unit')
    cls.catalogs = []
    for i, cap in enumerate(cls.capabilities):
        result = cls.group._operate('catalog', {'code': 's06a_service_' + key(), 'name': cap.name,
            'kind': 'care' if i < 2 else 'exam', 'capability_id': cap.id, 'uom_id': cls.uom.id}, key())
        cls.catalogs.append(root['ydental.intake.catalog'].browse(result['id']))
    for store in cls.stores:
        manager = bind(cls, cls.users['manager'], store)
        supply = manager.env['ydental.supply.service']
        floor = root['ydental.space.floor'].create({'name': 'P020-B Floor', 'ydental_store_id': store.id})
        supply._operate('policy', {'name': 'P020-B synthetic demo 1:2', 'mode': 'demo', 'rounding': 'floor',
            'phone_pool': 'reservation', 'cutoff_minutes': 0, 'reason': 'Synthetic validation only'}, key())
        areas, stations, mappings, slots = [], [], [], []
        for i, cap in enumerate(cls.capabilities):
            area = root['ydental.space.area'].create({'name': cap.name + ' area', 'ydental_store_id': store.id,
                'ydental_floor_id': floor.id, 'ydental_reporting': True, 'ydental_missed_limit': 2, 'ydental_purpose': 'care' if i < 2 else 'exam'})
            station = root['ydental.space.station'].create({'name': cap.name + ' station', 'ydental_store_id': store.id,
                'ydental_floor_id': floor.id, 'ydental_area_id': area.id,
                'ydental_kind': 'care' if i < 2 else 'exam',
                'ydental_add_capability_ids': [fields.Command.set(cap.ids)]})
            supply._operate('business', {'area_id': area.id, 'state': 'open', 'reason': 'Synthetic local day open'}, key())
            result = manager._operate('mapping', {'catalog_id': cls.catalogs[i].id, 'area_id': area.id, 'execution_area_id': area.id}, key())
            mappings.append(root['ydental.intake.mapping'].browse(result['id']))
            slots.append(make_slot(cls, manager, station, cls.start, cls.end))
            areas.append(area); stations.append(station)
        cls.areas.append(areas); cls.stations.append(stations); cls.mappings.append(mappings); cls.slots.append(slots)
    cls.currency = root.company.currency_id
    root['ir.config_parameter'].set_str('ydental_queue.heartbeat_seconds', '2')
    root['ir.config_parameter'].set_str('ydental_queue.timeout_seconds', '20')
    for role in ('doctor', 'manager'):
        cls.users[role].write({'ydental_capability_ids': [fields.Command.set(cls.capabilities.ids)]})
    cls.admin._grant(cls.users['doctor'].id, cls.stores[0].id, {'exam': 'write'})
    cls.second = new_test_user(root, name='P020-B Synthetic Second', login='s06a_second_' + key(),
        password='s06a-test-password', groups='ydental_base.ydental_base_group_user')
    cls.admin._join(cls.second.id, cls.stores[0].id)
    cls.admin._grant(cls.second.id, cls.stores[0].id, {'medical': 'write', 'exam': 'write'})
    cls.second.write({'ydental_capability_ids': [fields.Command.set(cls.capabilities.ids)]})
    original = cls.stations[0][0]
    cls.other_station = root['ydental.space.station'].create({'name': 'P020-B Second Cleaning Chair',
        'ydental_store_id': original.ydental_store_id.id, 'ydental_floor_id': original.ydental_floor_id.id,
        'ydental_area_id': original.ydental_area_id.id, 'ydental_add_capability_ids': [fields.Command.set(cls.capabilities[0].ids)]})



def make_slot(cls, service, station, start, end, total=12):
    supply = service.env['ydental.supply.service']
    result = supply._operate('slot', {'station_id': station.id, 'start': fields.Datetime.to_string(start),
        'end': fields.Datetime.to_string(end), 'total': total, 'capability_ids': station.ydental_capability_ids.ids,
        'reason': 'P020-B synthetic capacity'}, key())
    slot = cls.root['ydental.supply.slot'].browse(result['id'])
    supply._operate('publish', {'id': slot.id, 'version': slot.ydental_version, 'user_ids': [cls.users['manager'].id],
        'reason': 'P020-B synthetic verified coverage'}, key())
    return slot


def patient(cls, service=None):
    return (cls.front if service is None else service).env['ydental.patient.service']._operate('create', {'values': {'name': 'P020-B Synthetic Person'}}, key())['id']


def qualify(cls, patient_id=None, mapping=None, service=None, channel='reservation', start=None, end=None):
    service = cls.front if service is None else service
    return service._operate('reserve' if channel != 'walkin' else 'register', dict(
        {'patient_id': patient_id or patient(cls), 'mapping_id': (mapping or cls.mappings[0][0]).id,
         'start': fields.Datetime.to_string(start or cls.start), 'end': fields.Datetime.to_string(end or cls.end)},
        **({'channel': channel} if channel != 'walkin' else {})), key())


def arrive_report(cls, q, service=None):
    service = cls.front if service is None else service
    task = cls.root['ydental.intake.task'].browse(q['task_id'])
    service._operate('arrive', {'patient_id': task.ydental_patient_id.id}, key())
    return service._operate('report', {'task_id': task.id, 'version': task.ydental_version}, key())


def price(cls, amount=600, service=None, catalog=None, start=None, end=None, replace=None):
    service = cls.group if service is None else service
    record = service._operate('price', {'catalog_id': (catalog or cls.catalogs[0]).id,
        'currency_id': cls.currency.id, 'unit_price': amount,
        'start': fields.Datetime.to_string(start or fields.Datetime.now() - timedelta(days=1)),
        'end': fields.Datetime.to_string(end or fields.Datetime.now() + timedelta(days=30)), 'reason': 'P020-B synthetic price'}, key())
    record = service._operate('review', {'record_id': record['id'], 'version': record['version'], 'reason': 'P020-B review'}, key())
    args = {'record_id': record['id'], 'version': record['version'], 'reason': 'P020-B publish'}
    if replace:
        args.update(replace_id=replace.id, replace_version=replace.ydental_version)
    published = service._operate('publish', args, key())
    if hasattr(cls, 'drug_catalog') and catalog == cls.drug_catalog:
        controlled = service.env['ydental.queue.service']._bind_connection(key() + key()).env['ydental.treatment.service']
        if not controlled._medicine_link(cls.stores[0], product=cls.root['product.product'].browse(cls.products['medicine']), required=False):
            controlled._operate('publish_medicine', {'catalog_id': cls.drug_catalog.id,
                'product_id': cls.products['medicine'], 'uom_id': cls.uom.id,
                'evidence': 'Explicit synthetic SKU to reviewed service price association', 'policy': 'demo_confirmation'}, key())
    return published



def queue_bind(cls, user=None, session_key=None, connection=None):
    return bind(cls, user or cls.users['doctor'], session_key=session_key).env['ydental.queue.service']._bind_connection(connection or key() + key())


def enter(cls, service=None, station=None):
    service = service if service is not None else queue_bind(cls)
    return service, service._operate('enter', {'station_id': (station or cls.stations[0][0]).id})


def lease_args(lease):
    return {'lease_id': lease['lease_id'], 'token': lease['token']}


def accepted(cls, mapping=None):
    q = qualify(cls, mapping=mapping)
    arrive_report(cls, q)
    return cls.root['ydental.intake.task'].browse(q['task_id'])


def serving(cls, user=None, station=None, task=None):
    task = task if task is not None else accepted(cls)
    queue = queue_bind(cls, user=user)
    lease = queue._operate('enter', {'station_id': (station or cls.stations[0][0]).id})
    call = queue._operate('call', lease_args(lease))
    assert call['task_id'] == task.id
    actual = queue._operate('start', dict(lease_args(lease), entry_id=call['entry_id']))
    return queue, lease, cls.root['ydental.queue.execution'].browse(actual['execution_id'])


def opened(cls):
    queue, lease, execution = serving(cls)
    service = queue.env['ydental.clinical.service']
    data = service._operate('open', {'execution_id': execution.id, 'lease_id': lease['lease_id'], 'lease_token': lease['token']})
    return service, queue, lease, execution, data


def save_args(data, text='Synthetic complaint'):
    content = dict(data['content'], chief_complaint=text)
    return {'document_id': data['document_id'], 'editor_token': data['editor_token'],
        'expected_version': data['version'], 'content': content, 'key': key()}


def handover_args(data, lease, text='Synthetic complaint'):
    return save_args(data, text) | {'lease_id': lease['lease_id'], 'lease_token': lease['token']}

clinical_setup=setup
from datetime import timedelta

from odoo import fields
from odoo.tests import new_test_user



def setup(cls):
    clinical_setup(cls)
    for store in cls.stores:
        store.write({'name': 'P020-B Synthetic ' + key()})
    cls.root['ir.config_parameter'].set_str('ydental_queue.timeout_seconds', '600')
    cls.admin._grant(cls.users['manager'].id, cls.stores[0].id, {'warehouse': 'write'})
    cls.stock = bind(cls, cls.users['manager']).env['ydental.inventory.service']
    cls.stock._operate('setup', {'code': 'B' + str(cls.stores[0].id)}, key())
    cls.products, cls.lots = {}, {}
    for kind in ('medicine', 'material'):
        result = cls.stock._operate('product', {'code': 'S08B-' + key(), 'name': 'P020-B Synthetic ' + kind,
            'kind': kind, 'stock_uom_id': cls.uom.id, 'issue_uom_id': cls.uom.id, 'step': 1,
            'specification': 'Synthetic review only'}, key())
        cls.products[kind] = result['id']
        cls.lots[kind] = cls.stock._operate('lot', {'product_id': result['id'], 'name': 'S08B-' + key(),
            'expiration': fields.Datetime.to_string(fields.Datetime.now() + timedelta(days=45))}, key())['id']
    cls.pharmacist = new_test_user(cls.root, name='P020-B Synthetic Pharmacist', login='s08b_pharm_' + key(),
        password='s08b-synthetic-password', groups='ydental_base.ydental_base_group_user')
    cls.admin._join(cls.pharmacist.id, cls.stores[0].id)
    cls.admin._grant(cls.pharmacist.id, cls.stores[0].id, {'pharmacy': 'write'})
    cls.pharmacist.write({'ydental_capability_ids': [fields.Command.set(cls.capabilities[0].ids)]})
    original = cls.stations[0][0]
    cls.pharmacy_area = cls.root['ydental.space.area'].create({'name': 'P020-B Pharmacy', 'ydental_store_id': cls.stores[0].id,
        'ydental_floor_id': original.ydental_floor_id.id, 'ydental_reporting': True, 'ydental_missed_limit': 2, 'ydental_purpose': 'pharmacy'})
    cls.pharmacy_station = cls.root['ydental.space.station'].create({'name': 'P020-B Dispensing station',
        'ydental_store_id': cls.stores[0].id, 'ydental_floor_id': original.ydental_floor_id.id,
        'ydental_area_id': cls.pharmacy_area.id, 'ydental_kind': 'pharmacy', 'ydental_add_capability_ids': [fields.Command.set(cls.capabilities[0].ids)]})
    cls.group.env['ydental.supply.service']._operate('business', {'area_id': cls.pharmacy_area.id, 'state': 'open', 'reason': 'P020-B synthetic open'}, key())
    catalog = cls.group._operate('catalog', {'code': 'S08B-drug-' + key(), 'name': 'P020-B Take-away synthetic medicine',
        'kind': 'medicine', 'capability_id': cls.capabilities[0].id, 'uom_id': cls.uom.id}, key())
    cls.drug_catalog = cls.root['ydental.intake.catalog'].browse(catalog['id'])
    mapping = cls.group._operate('mapping', {'catalog_id': cls.drug_catalog.id, 'area_id': cls.pharmacy_area.id,
        'execution_area_id': cls.pharmacy_area.id}, key())
    cls.drug_mapping = cls.root['ydental.intake.mapping'].browse(mapping['id'])


def receive(cls, quantity=20, kind='material'):
    return cls.stock._operate('receive', {'lot_id': cls.lots[kind], 'quantity': quantity, 'uom_id': cls.uom.id,
        'source_key': key(), 'reason': 'P020-B evidenced physical receipt'}, key())


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

def cross_legal_target(cls, total=12):
    """A real B company, approved service, business day and published capacity."""
    from .common import make_slot
    company = cls.root['res.company'].create({'name': 'Synthetic target legal entity ' + key()})
    store = cls.root['ydental.access.store'].create({'name': 'Synthetic cross-legal store ' + key(),
        'company_id': company.id, 'ydental_timezone': cls.stores[0].ydental_timezone})
    for user in (cls.users['manager'], cls.users['frontdesk']):
        user.write({'company_ids': [fields.Command.link(company.id)]})
        cls.admin._join(user.id, store.id)
    cls.admin._grant(cls.users['manager'].id, store.id, dict.fromkeys(('space','capacity','price','frontdesk'), 'write'))
    cls.admin._grant(cls.users['frontdesk'].id, store.id, {'frontdesk': 'write'})
    manager = bind(cls, cls.users['manager'], store)
    floor = cls.root['ydental.space.floor'].create({'name': 'Synthetic target floor', 'ydental_store_id': store.id})
    area = cls.root['ydental.space.area'].create({'name': 'Synthetic cross-legal care area',
        'ydental_store_id': store.id, 'ydental_floor_id': floor.id, 'ydental_reporting': True, 'ydental_purpose': 'care'})
    station = cls.root['ydental.space.station'].create({'name': 'Synthetic cross-legal chair',
        'ydental_store_id': store.id, 'ydental_floor_id': floor.id, 'ydental_area_id': area.id,
        'ydental_add_capability_ids': [fields.Command.set(cls.capabilities[0].ids)]})
    supply = manager.env['ydental.supply.service']
    supply._operate('policy', {'name': 'Synthetic cross-legal 1:2', 'mode': 'demo', 'rounding': 'floor',
        'phone_pool': 'reservation', 'cutoff_minutes': 0, 'reason': 'Synthetic published capacity policy'}, key())
    supply._operate('business', {'area_id': area.id, 'state': 'open', 'reason': 'Explicit target business day'}, key())
    mapping = manager._operate('mapping', {'catalog_id': cls.catalogs[0].id, 'area_id': area.id, 'execution_area_id': area.id}, key())
    slot = make_slot(cls, manager, station, cls.start, cls.end, total=total)
    return store, cls.root['ydental.intake.mapping'].browse(mapping['id']), slot

def publish_medicine_link(cls, product, catalog):
    service = bind(cls, cls.users['price']).env['ydental.queue.service']._bind_connection(key()+key()).env['ydental.treatment.service']
    return service._operate('publish_medicine', {'catalog_id': catalog.id, 'product_id': product,
        'uom_id': cls.uom.id, 'evidence': 'Explicit synthetic SKU and service price review', 'policy': 'demo_confirmation'}, key())


def distinct_medicine(cls, amount=27, publish=True):
    product = cls.stock._operate('product', {'code': 'R-' + key(), 'name': 'Distinct synthetic medicine ' + key()[:6],
        'kind': 'medicine', 'stock_uom_id': cls.uom.id, 'issue_uom_id': cls.uom.id, 'step': 1,
        'specification': 'Synthetic distinct specification'}, key())['id']
    lot = cls.stock._operate('lot', {'product_id': product, 'name': 'R-' + key(),
        'expiration': str(fields.Datetime.now() + timedelta(days=45))}, key())['id']
    cls.stock._operate('receive', {'lot_id': lot, 'quantity': 20, 'uom_id': cls.uom.id,
        'source_key': key(), 'reason': 'Synthetic distinct physical receipt'}, key())
    catalog = cls.group._operate('catalog', {'code': 'R-' + key(), 'name': 'Exact distinct medicine fee ' + str(amount),
        'kind': 'medicine', 'capability_id': cls.capabilities[0].id, 'uom_id': cls.uom.id}, key())['id']
    catalog = cls.root['ydental.intake.catalog'].browse(catalog)
    cls.group._operate('mapping', {'catalog_id': catalog.id, 'area_id': cls.pharmacy_area.id,
        'execution_area_id': cls.pharmacy_area.id}, key())
    from .common import price
    price(cls, catalog=catalog, amount=amount)
    if publish:
        publish_medicine_link(cls, product, catalog)
    return product, lot, catalog

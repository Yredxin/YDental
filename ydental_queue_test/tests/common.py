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
    cls.root = cls.env['base'].sudo().env
    root = cls.root
    cls.stores = root['ydental.access.store'].create([
        {'name': 'S06A Synthetic A', 'company_id': root.company.id, 'ydental_timezone': 'UTC'},
        {'name': 'S06A Synthetic B', 'company_id': root.company.id, 'ydental_timezone': 'UTC'}])
    cls.users = {}
    for role in ('manager', 'frontdesk', 'doctor', 'reader', 'price', 'none', 'catalog'):
        groups = 'ydental_base.ydental_base_group_user'
        if role in ('manager', 'catalog'):
            groups += ',ydental_access.ydental_group_manager'
        cls.users[role] = new_test_user(root, name='S06A Synthetic ' + role,
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
        {'name': 'S06A Cleaning', 'ydental_code': 's06a_clean_' + key()},
        {'name': 'S06A Implant', 'ydental_code': 's06a_implant_' + key()},
        {'name': 'S06A Panorama', 'ydental_code': 's06a_pan_' + key()},
        {'name': 'S06A CBCT', 'ydental_code': 's06a_cbct_' + key()}])
    cls.users['manager'].write({'ydental_capability_ids': [fields.Command.set(cls.capabilities.ids)]})
    cls.areas, cls.stations, cls.mappings, cls.slots = [], [], [], []
    cls.start = fields.Datetime.now().replace(microsecond=0) + timedelta(hours=1)
    cls.end = cls.start + timedelta(hours=1)
    cls.uom = root.ref('uom.product_uom_unit')
    cls.catalogs = []
    for i, cap in enumerate(cls.capabilities):
        result = cls.group._operate('catalog', {'code': 's06a_service_' + key(), 'name': cap.name,
            'kind': 'care' if i < 2 else 'exam', 'capability_id': cap.id, 'uom_id': cls.uom.id}, key())
        cls.catalogs.append(root['ydental.intake.catalog'].browse(result['id']))
    for store in cls.stores:
        manager = bind(cls, cls.users['manager'], store)
        supply = manager.env['ydental.supply.service']
        floor = root['ydental.space.floor'].create({'name': 'S06A Floor', 'ydental_store_id': store.id})
        supply._operate('policy', {'name': 'S06A synthetic demo 1:2', 'mode': 'demo', 'rounding': 'floor',
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
    cls.second = new_test_user(root, name='S06A Synthetic Second', login='s06a_second_' + key(),
        password='s06a-test-password', groups='ydental_base.ydental_base_group_user')
    cls.admin._join(cls.second.id, cls.stores[0].id)
    cls.admin._grant(cls.second.id, cls.stores[0].id, {'medical': 'write', 'exam': 'write'})
    cls.second.write({'ydental_capability_ids': [fields.Command.set(cls.capabilities.ids)]})
    original = cls.stations[0][0]
    cls.other_station = root['ydental.space.station'].create({'name': 'S06A Second Cleaning Chair',
        'ydental_store_id': original.ydental_store_id.id, 'ydental_floor_id': original.ydental_floor_id.id,
        'ydental_area_id': original.ydental_area_id.id, 'ydental_add_capability_ids': [fields.Command.set(cls.capabilities[0].ids)]})



def make_slot(cls, service, station, start, end, total=12):
    supply = service.env['ydental.supply.service']
    result = supply._operate('slot', {'station_id': station.id, 'start': fields.Datetime.to_string(start),
        'end': fields.Datetime.to_string(end), 'total': total, 'capability_ids': station.ydental_capability_ids.ids,
        'reason': 'S06A synthetic capacity'}, key())
    slot = cls.root['ydental.supply.slot'].browse(result['id'])
    supply._operate('publish', {'id': slot.id, 'version': slot.ydental_version, 'user_ids': [cls.users['manager'].id],
        'reason': 'S06A synthetic verified coverage'}, key())
    return slot


def patient(cls, service=None):
    return (cls.front if service is None else service).env['ydental.patient.service']._operate('create', {'values': {'name': 'S06A Synthetic Person'}}, key())['id']


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
        'end': fields.Datetime.to_string(end or fields.Datetime.now() + timedelta(days=30)), 'reason': 'S06A synthetic price'}, key())
    record = service._operate('review', {'record_id': record['id'], 'version': record['version'], 'reason': 'S06A review'}, key())
    args = {'record_id': record['id'], 'version': record['version'], 'reason': 'S06A publish'}
    if replace:
        args.update(replace_id=replace.id, replace_version=replace.ydental_version)
    return service._operate('publish', args, key())



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

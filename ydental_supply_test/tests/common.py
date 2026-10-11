from datetime import timedelta
import secrets

from odoo import fields
from odoo.tests import new_test_user


def setup_supply(cls):
    cls.root = cls.env['base'].sudo().env
    root = cls.root
    suffix = secrets.token_hex(4)
    cls.suffix = suffix
    cls.stores = root['ydental.access.store'].create([
        {'name': 'S03 Synthetic A', 'company_id': root.company.id, 'ydental_timezone': 'UTC'},
        {'name': 'S03 Synthetic B', 'company_id': root.company.id, 'ydental_timezone': 'UTC'}])
    cls.writer = new_test_user(root, name='S03 Synthetic Writer', login='s03_writer_' + suffix, password='s03-test-password', groups='ydental_base.ydental_base_group_user')
    cls.reader = new_test_user(root, name='S03 Synthetic Reader', login='s03_reader_' + suffix, password='s03-test-password', groups='ydental_base.ydental_base_group_user')
    cls.staff = new_test_user(root, name='S03 Synthetic Staff', login='s03_staff_' + suffix, password='s03-test-password', groups='ydental_base.ydental_base_group_user')
    cls.replacement = new_test_user(root, name='S03 Synthetic Replacement', login='s03_replacement_' + suffix, groups='ydental_base.ydental_base_group_user')
    cls.manager = new_test_user(root, name='S03 Synthetic Manager', login='s03_manager_' + suffix, groups='ydental_base.ydental_base_group_user,ydental_access.ydental_group_manager')
    access = root['ydental.access.service'].with_user(cls.manager)
    cls.admin = access._bind(access._session_for_key('s03-admin-' + suffix))
    for user in (cls.writer, cls.reader, cls.staff, cls.replacement, cls.manager):
        for store in cls.stores:
            cls.admin._join(user.id, store.id)
    for store in cls.stores:
        cls.admin._grant(cls.manager.id, store.id, {'personnel': 'write', 'capacity': 'write', 'space': 'write'})
        cls.admin._grant(cls.writer.id, store.id, {'capacity': 'write', 'space': 'write'})
        cls.admin._grant(cls.reader.id, store.id, {'capacity': 'read'})
    cls.capabilities = root['ydental.access.capability'].create([
        {'name': 'S03 Cleaning', 'ydental_code': 's03_clean_' + suffix}, {'name': 'S03 Filling', 'ydental_code': 's03_fill_' + suffix}])
    for user in (cls.staff, cls.replacement, cls.writer):
        user.write({'ydental_capability_ids': [fields.Command.set(cls.capabilities.ids)]})
    cls.floor = root['ydental.space.floor'].create({'name': 'S03 Floor', 'ydental_store_id': cls.stores[0].id})
    cls.area = root['ydental.space.area'].create({'name': 'S03 Area', 'ydental_store_id': cls.stores[0].id,
        'ydental_floor_id': cls.floor.id, 'ydental_reporting': True})
    values = {'ydental_store_id': cls.stores[0].id, 'ydental_floor_id': cls.floor.id, 'ydental_area_id': cls.area.id}
    cls.stations = root['ydental.space.station'].create([
        dict(values, name='S03 Chair 1', ydental_add_capability_ids=[fields.Command.set(cls.capabilities[:1].ids)]),
        dict(values, name='S03 Chair 2', ydental_add_capability_ids=[fields.Command.set(cls.capabilities.ids)])])
    cls.service = bind(cls, cls.writer, 's03-writer')
    cls.start = (fields.Datetime.now() + timedelta(days=2)).replace(hour=9, minute=0, second=0)
    cls.end = cls.start + timedelta(hours=1)
    cls.policy = cls.service._operate('policy', {'name': 'S03 explicit demo 1:2', 'mode': 'demo',
        'rounding': 'floor', 'phone_pool': 'reservation', 'cutoff_minutes': 0, 'reason': 'Synthetic validation only'}, 'policy')


def bind(cls, user, key, store=None):
    access = cls.root['ydental.access.service'].with_user(user)
    session = access._session_for_key(key + '-' + cls.suffix)
    access = access._bind(session)
    access._switch((store or cls.stores[0]).id)
    return cls.root['ydental.access.service'].with_user(user)._bind(session).env['ydental.supply.service']


def slot(cls, station=None, total=6, start=None, end=None, key='slot'):
    station = station or cls.stations[1]
    start, end = start or cls.start, end or cls.end
    result = cls.service._operate('slot', {'station_id': station.id, 'start': fields.Datetime.to_string(start),
        'end': fields.Datetime.to_string(end), 'total': total, 'capability_ids': station.ydental_capability_ids.ids,
        'reason': 'Synthetic capacity'}, key)
    record = cls.root['ydental.supply.slot'].browse(result['id'])
    cls.service._operate('publish', {'id': record.id, 'version': record.ydental_version,
        'user_ids': [cls.staff.id], 'reason': 'Synthetic verified coverage'}, key + '-publish')
    return record


def acquire_args(cls, record, key='source', channel='reservation', capability=None):
    return {'area_id': record.ydental_area_id.id, 'capability_id': (capability or cls.capabilities[0]).id,
        'start': fields.Datetime.to_string(record.ydental_start), 'end': fields.Datetime.to_string(record.ydental_end),
        'channel': channel, 'source': 's03_synthetic', 'source_key': key}


def acquire(cls, record, key='source', channel='reservation', capability=None):
    result = cls.service._capacity_action('acquire', acquire_args(cls, record, key, channel, capability), 'acquire-' + key)
    return cls.root['ydental.supply.claim'].browse(result['id'])

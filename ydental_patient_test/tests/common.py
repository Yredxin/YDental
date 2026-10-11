import secrets

from odoo.tests import new_test_user


def bind(cls, user, key, store=None):
    access = cls.root['ydental.access.service'].with_user(user)
    session = access._session_for_key(key + cls.suffix)
    access = access._bind(session)
    access._switch((store or cls.stores[0]).id)
    return access._bind(session).env['ydental.patient.service']


def setup_patient(cls):
    cls.root = cls.env['base'].sudo().env
    root = cls.root
    cls.suffix = secrets.token_hex(4)
    cls.stores = root['ydental.access.store'].create([
        {'name': 'S04 Synthetic A', 'company_id': root.company.id, 'ydental_timezone': 'Asia/Shanghai'},
        {'name': 'S04 Synthetic B', 'company_id': root.company.id, 'ydental_timezone': 'UTC'},
        {'name': 'S04 Synthetic C', 'company_id': root.company.id, 'ydental_timezone': 'UTC'}])
    cls.users = {}
    for role in ('manager', 'frontdesk', 'doctor', 'reader', 'none'):
        groups = 'ydental_base.ydental_base_group_user'
        if role == 'manager':
            groups += ',ydental_access.ydental_group_manager'
        cls.users[role] = new_test_user(root, name='S04 Synthetic ' + role,
            login='s04_' + role + '_' + cls.suffix, password='s04-test-password', groups=groups)
    cls.manager = cls.users['manager']
    access = root['ydental.access.service'].with_user(cls.manager)
    cls.admin = access._bind(access._session_for_key('s04-admin-' + cls.suffix))
    for user in cls.users.values():
        cls.admin._join(user.id, cls.stores[0].id)
    for store in cls.stores:
        cls.admin._join(cls.manager.id, store.id)
        cls.admin._grant(cls.manager.id, store.id, {'patient': 'write', 'medical': 'write', 'export': 'write'})
    cls.admin._grant(cls.users['frontdesk'].id, cls.stores[0].id, {'frontdesk': 'write', 'export': 'write'})
    cls.admin._grant(cls.users['doctor'].id, cls.stores[0].id, {'medical': 'write', 'export': 'write'})
    cls.admin._grant(cls.users['reader'].id, cls.stores[0].id, {'patient': 'read'})
    cls.service = bind(cls, cls.users['frontdesk'], 'frontdesk')
    cls.group = bind(cls, cls.manager, 'group')
    cls.doctor = bind(cls, cls.users['doctor'], 'doctor')
    cls.reader = bind(cls, cls.users['reader'], 'reader')


def create(cls, name='Synthetic Person', service=None, key=None, **values):
    return (service or cls.service)._operate('create', {'values': dict(values, name=name)}, key or secrets.token_hex(8))


def merge(cls, source, target, service=None):
    return (service or cls.service)._operate('request_merge', {'source_id': source, 'target_id': target,
        'reason': 'Synthetic identity verification request'}, secrets.token_hex(8))


def clinical(cls, patient_id, store=None, text='S04 SYNTHETIC CLINICAL ONLY'):
    service = cls.doctor if store is None else bind(cls, cls.manager, 'clinical-' + str(store.id), store)
    return service._operate('clinical', {'patient_id': patient_id, 'values': {'allergies': text}}, secrets.token_hex(8))

from odoo import fields
from odoo.tests import new_test_user


SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100"><rect width="80" height="80" fill="#123456"/></svg>'


def setup_space(cls):
    root = cls.env['base'].sudo().env
    cls.root = root
    cls.stores = root['ydental.access.store'].create([
        {'name': 'S02 Synthetic A', 'company_id': root.company.id, 'ydental_timezone': 'UTC'},
        {'name': 'S02 Synthetic B', 'company_id': root.company.id, 'ydental_timezone': 'UTC'},
    ])
    cls.writer = new_test_user(root, login='s02_writer', password='s02-test-password',
        groups='ydental_base.ydental_base_group_user')
    cls.reader = new_test_user(root, login='s02_reader', password='s02-test-password',
        groups='ydental_base.ydental_base_group_user')
    cls.manager = new_test_user(root, login='s02_group',
        groups='ydental_base.ydental_base_group_user,ydental_access.ydental_group_manager')
    service = root['ydental.access.service'].with_user(cls.manager)
    cls.admin = service._bind(service._session_for_key('s02-setup'))
    for user in (cls.writer, cls.reader, cls.manager):
        for store in cls.stores:
            cls.admin._join(user.id, store.id)
    for store in cls.stores:
        cls.admin._grant(cls.manager.id, store.id, {'space': 'write', 'personnel': 'write'})
    cls.admin._grant(cls.writer.id, cls.stores[0].id, {'space': 'write'})
    cls.admin._grant(cls.writer.id, cls.stores[1].id, {'space': 'read'})
    cls.admin._grant(cls.reader.id, cls.stores[0].id, {'space': 'read'})
    cls.capabilities = root['ydental.access.capability'].create([
        {'name': label, 'ydental_code': 's02_' + code}
        for code, label in [('clean', 'Cleaning'), ('fill', 'Filling'), ('panorama', 'Panorama'), ('cbct', 'CBCT')]
    ])
    cls.floor = root['ydental.space.floor'].create({'name': 'S02 Second floor', 'ydental_store_id': cls.stores[0].id})
    values = {'ydental_store_id': cls.stores[0].id, 'ydental_floor_id': cls.floor.id}
    cls.area = root['ydental.space.area'].create(dict(values, name='S02 Treatment', ydental_reporting=True))
    cls.child = root['ydental.space.area'].create(dict(values, name='S02 Room A', parent_id=cls.area.id))
    cls.station = root['ydental.space.station'].create(dict(values, name='S02 Chair 1', ydental_area_id=cls.child.id))
    cls.resource = root['ydental.space.resource'].create({'name': 'S02 Private chair', 'ydental_kind': 'chair',
        'ydental_store_id': cls.stores[0].id, 'ydental_svg': SVG,
        'ydental_capability_ids': [fields.Command.set(cls.capabilities[:1].ids)]})
    cls.item = root['ydental.space.item'].create(dict(values, name='S02 Chair art', ydental_resource_id=cls.resource.id,
        ydental_station_id=cls.station.id))


def bound(cls, user, key, store=None):
    service = cls.root['ydental.access.service'].with_user(user)
    session = service._session_for_key(key)
    service = service._bind(session)
    service._switch((store or cls.stores[0]).id)
    return cls.root['ydental.access.service'].with_user(user)._bind(session)

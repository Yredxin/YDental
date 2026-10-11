"""Seed only the runner-created S02 database with synthetic floor-plan fixtures."""
import json
import os
from pathlib import Path
import re
import secrets

from odoo import api, fields


run = Path(os.environ['YDENTAL_S02_RUN_DIR'])
metadata = json.loads((run / 'database.json').read_text())
assert re.fullmatch(r'ydental_s02_test_[0-9]{14}_[a-f0-9]{8}', metadata['database'])
assert env.cr.dbname == metadata['database']
assert not (run / 'access.json').exists(), 'Preview already seeded'

with env.registry.cursor() as cr:
    seed = api.Environment(cr, api.SUPERUSER_ID, {})
    company = seed['res.company'].create({'name': 'S02 Synthetic Clinic Company'})
    stores = seed['ydental.access.store'].create([
        {'name': 'S02 Synthetic Store A', 'company_id': company.id, 'ydental_timezone': 'Asia/Shanghai'},
        {'name': 'S02 Synthetic Store B', 'company_id': company.id, 'ydental_timezone': 'UTC'},
    ])
    access = {}
    for role in ('group', 'writer', 'reader', 'group_only'):
        login = 's02_' + role + '_' + secrets.token_hex(4) + '@example.invalid'
        password = secrets.token_urlsafe(24)
        groups = ['ydental_base.ydental_base_group_user']
        if role in ('group', 'group_only'):
            groups.append('ydental_access.ydental_group_manager')
        user = seed['res.users'].with_context(no_reset_password=True).create({
            'name': 'S02 Synthetic ' + role.title(), 'login': login, 'email': login, 'password': password,
            'lang': 'zh_CN', 'company_id': company.id, 'company_ids': [fields.Command.set(company.ids)],
            'group_ids': [fields.Command.set([seed.ref(group).id for group in groups])],
        })
        access[role] = {'id': user.id, 'login': login, 'password': password}
    service = seed['ydental.access.service'].with_user(access['group']['id'])
    service = service._bind(service._session_for_key('s02-private-seed'))
    for role in access:
        if role == 'group_only':
            continue
        for store in stores:
            service._join(access[role]['id'], store.id)
            service._grant(access[role]['id'], store.id, {'space': 'write' if role == 'group' or role == 'writer' and store == stores[0] else 'read'})
    capabilities = seed['ydental.access.capability'].create([
        {'name': name, 'ydental_code': code} for name, code in [('Cleaning', 's02_cleaning'),
            ('Filling', 's02_filling'), ('Panorama', 's02_panorama'), ('CBCT', 's02_cbct')]
    ])
    floor = seed['ydental.space.floor'].create({'name': 'S02 Synthetic Second Floor', 'ydental_store_id': stores[0].id})
    defaults = {'ydental_floor_id': floor.id, 'ydental_store_id': stores[0].id}
    areas = seed['ydental.space.area'].create([
        dict(defaults, name='Treatment', ydental_reporting=True, ydental_x=20, ydental_y=30, ydental_width=430, ydental_height=300),
        dict(defaults, name='Imaging', ydental_purpose='exam', ydental_reporting=True, ydental_x=490, ydental_y=30, ydental_width=450, ydental_height=300),
        dict(defaults, name='Pharmacy', ydental_purpose='pharmacy', ydental_reporting=True, ydental_x=20, ydental_y=380, ydental_width=280, ydental_height=240),
        dict(defaults, name='Settlement', ydental_purpose='settlement', ydental_x=340, ydental_y=380, ydental_width=280, ydental_height=240),
        dict(defaults, name='Waiting', ydental_purpose='waiting', ydental_x=670, ydental_y=380, ydental_width=270, ydental_height=240),
    ])
    room = seed['ydental.space.area'].create(dict(defaults, name='Room A', parent_id=areas[0].id,
        ydental_x=45, ydental_y=70, ydental_width=375, ydental_height=220))
    resources = {kind: seed.ref('ydental_space.ydental_space_resource_' + kind) for kind in ('chair', 'imaging', 'pharmacy', 'settlement', 'waiting', 'door', 'wall')}
    stations = seed['ydental.space.station'].create([
        dict(defaults, name='Chair 1', ydental_area_id=room.id, ydental_x=70, ydental_y=110,
            ydental_add_capability_ids=[fields.Command.set(capabilities[:1].ids)]),
        dict(defaults, name='Chair 2', ydental_area_id=room.id, ydental_x=260, ydental_y=110,
            ydental_add_capability_ids=[fields.Command.set(capabilities[:2].ids)]),
        dict(defaults, name='Panorama', ydental_area_id=areas[1].id, ydental_kind='exam', ydental_x=540, ydental_y=110,
            ydental_add_capability_ids=[fields.Command.set(capabilities[2:3].ids)]),
        dict(defaults, name='CBCT', ydental_area_id=areas[1].id, ydental_kind='exam', ydental_x=750, ydental_y=110,
            ydental_add_capability_ids=[fields.Command.set(capabilities[3:].ids)]),
        dict(defaults, name='Pharmacy desk', ydental_area_id=areas[2].id, ydental_kind='pharmacy', ydental_x=80, ydental_y=440),
        dict(defaults, name='Settlement desk', ydental_area_id=areas[3].id, ydental_kind='settlement',
            ydental_callable=False, ydental_x=400, ydental_y=440),
    ])
    items = seed['ydental.space.item'].create([
        dict(defaults, name=station.name, ydental_station_id=station.id,
             ydental_resource_id=resources[kind].id, ydental_x=station.ydental_x + 10,
             ydental_y=station.ydental_y + 25, ydental_width=65, ydental_height=55)
        for station, kind in zip(stations, ('chair', 'chair', 'imaging', 'imaging', 'pharmacy', 'settlement'))
    ])
    private = seed['ydental.space.resource'].create({'name': 'A Private marker', 'ydental_kind': 'waiting',
        'ydental_store_id': stores[0].id, 'ydental_svg': resources['waiting'].ydental_svg})
    action = seed.ref('ydental_space.ydental_space_plan_action')
    summary = {'database': cr.dbname, 'stores': stores.ids, 'floor_id': floor.id, 'area_ids': areas.ids,
               'station_ids': stations.ids, 'item_ids': items.ids, 'private_resource_id': private.id,
               'plan_action_id': action.id, 'synthetic_only': True,
               'group_only_without_membership_or_grants': not seed['ydental.access.membership'].search_count([
                   ('ydental_user_id', '=', access['group_only']['id'])]) and not seed['ydental.access.grant'].search_count([
                   ('ydental_membership_id.ydental_user_id', '=', access['group_only']['id'])])}
    cr.commit()  # Own cursor, committing fixtures only in the guarded new S02 DB.

with os.fdopen(os.open(run / 'access.json', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as handle:
    json.dump(access, handle)
(run / 'preview.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary))

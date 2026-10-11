"""Seed only the recorded, fresh S01 database with synthetic preview users.

Passwords stay in the run's private 0600 access.json. This script never prints
them, sends invitations, publishes policy values or adopts another database.
"""
import json
import os
from pathlib import Path
import re
import secrets

from odoo import api, fields


run = Path(os.environ['YDENTAL_S01_RUN_DIR'])
metadata = json.loads((run / 'database.json').read_text())
assert re.fullmatch(r'ydental_s01_test_[0-9]{14}_[a-f0-9]{8}', metadata['database'])
assert env.cr.dbname == metadata['database']  # supplied by the guarded shell adapter
assert not (run / 'access.json').exists(), 'Preview already seeded; do not overwrite credentials'

# An explicitly opened cursor owns this synthetic seed transaction. The shell's
# original cursor remains unchanged; no production endpoint or existing DB is used.
with env.registry.cursor() as cr:
    seed = api.Environment(cr, api.SUPERUSER_ID, {})
    companies = seed['res.company'].create([{'name': 'S01 Synthetic Company A'}, {'name': 'S01 Synthetic Company C'}])
    stores = seed['ydental.access.store'].create([
        {'name': 'S01 Synthetic Store A', 'company_id': companies[0].id, 'ydental_timezone': 'Asia/Shanghai'},
        {'name': 'S01 Synthetic Store B', 'company_id': companies[0].id, 'ydental_timezone': 'Asia/Shanghai'},
        {'name': 'S01 Synthetic Store C', 'company_id': companies[1].id, 'ydental_timezone': 'UTC'},
    ])
    access = {}
    group_names = {
        'group': ['ydental_base.ydental_base_group_user', 'ydental_access.ydental_group_manager'],
        'manager': ['ydental_base.ydental_base_group_user'],
        'operator': ['ydental_base.ydental_base_group_user'],
        'personnel': ['ydental_base.ydental_base_group_user'],
        'portal': ['base.group_portal'],
    }
    for role, groups in group_names.items():
        login = 's01_' + role + '_' + secrets.token_hex(4) + '@example.invalid'
        password = secrets.token_urlsafe(24)
        user = seed['res.users'].with_context(no_reset_password=True).create({
            'name': 'S01 Synthetic ' + role.title(), 'login': login, 'email': login, 'password': password,
            'lang': 'zh_CN', 'company_id': companies[0].id,
            'company_ids': [fields.Command.set(companies.ids)],
            'group_ids': [fields.Command.set([seed.ref(g).id for g in groups])],
        })
        access[role] = {'id': user.id, 'login': login, 'password': password}
    service = seed['ydental.access.service'].with_user(access['group']['id'])
    session = service._session_for_key('s01-private-seed-scope')
    service = service._bind(session)
    for role in ('group', 'operator', 'personnel'):
        for store in stores:
            service._join(access[role]['id'], store.id)
    service._join(access['manager']['id'], stores[0].id)
    # Fixed synthetic test role only; no production appointment policy approval.
    service._membership(access['manager']['id'], stores[0].id).write({'ydental_is_manager': True})
    service._grant(access['operator']['id'], stores[0].id, {'space': 'write', 'medical': 'read'})
    service._grant(access['operator']['id'], stores[1].id, {'space': 'read'})
    service._grant(access['personnel']['id'], stores[0].id, {'personnel': 'write', 'space': 'read'})
    for store in stores:
        service._grant(access['group']['id'], store.id, {'personnel': 'write', 'space': 'write'})
    records = seed['ydental.access.test.record'].create([
        {'name': 'Synthetic source ' + str(store.id), 'ydental_store_id': store.id,
         'ydental_category': category, 'ydental_text': 'SYNTHETIC_' + category.upper()}
        for store in stores for category in ('space', 'medical', 'settlement')
    ])
    template = seed['ydental.access.template'].create({'name': 'S01 Synthetic Front Desk', 'ydental_levels': {'frontdesk': 'read'}})
    source_a = records.filtered(lambda r: r.ydental_store_id == stores[0] and r.ydental_category == 'space')
    attachment = seed['ir.attachment'].create({'name': 'S01 synthetic attachment', 'raw': b'SYNTHETIC_ATTACHMENT',
                                               'res_model': source_a._name, 'res_id': source_a.id})
    summary = {'database': cr.dbname, 'stores': stores.ids, 'roles': {r: a['id'] for r, a in access.items()},
               'template_id': template.id, 'source_a_id': source_a.id, 'attachment_id': attachment.id,
               'policy': 'not published; fixture manager assignment only', 'synthetic_only': True}
    cr.commit()  # Commit only the cursor opened above, for the isolated preview.

with os.fdopen(os.open(run / 'access.json', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as handle:
    json.dump(access, handle)
(run / 'preview.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary))

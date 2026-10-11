"""Synthetic native-API probes, executed only through s00_b.py after identity checks."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import json
import os
from pathlib import Path
import re
import secrets
import threading

from odoo import api, Command, fields, SUPERUSER_ID
from odoo.tools import config


run = Path(os.environ['YDENTAL_S00B_RUN_DIR'])
repo = Path(__file__).resolve().parents[1]
if (not re.fullmatch(r'ydental_s00b_test_[0-9]{14}_[a-f0-9]{8}', run.name)
        or run.is_symlink() or run.parent.resolve() != (repo / '.local').resolve()
        or env.cr.dbname != run.name):
    raise RuntimeError('Probe requires a guarded S00-B database')
marker = json.loads((run / 'database.json').read_text())
endpoint = {key: str(config['db_' + key]) for key in ('host', 'port', 'user')}
if marker['database'] != run.name or endpoint != {'host': '127.0.0.1', 'port': '5432', 'user': 'odoo'}:
    raise RuntimeError('Probe endpoint or database mismatch')
env.cr.execute('SELECT oid FROM pg_database WHERE datname = current_database()')
if env.cr.fetchone()[0] != marker['oid']:
    raise RuntimeError('Probe OID mismatch')
env.cr.execute('SELECT system_identifier::text FROM pg_control_system()')
if env.cr.fetchone()[0] != '7694897083368259627':
    raise RuntimeError('Probe cluster mismatch')
access_file = run / 'access.json'
if not access_file.exists():
    access = {}
    group = env.ref('ydental_base.ydental_base_group_user')
    for role, groups, lang in (
        ('authorized_zh', [group.id], 'zh_CN'),
        ('authorized_en', [group.id], 'en_US'),
        ('unauthorized', [env.ref('base.group_user').id], 'zh_CN'),
        ('portal', [env.ref('base.group_portal').id], 'zh_CN'),
    ):
        login = 's00b_%s@example.invalid' % role
        password = secrets.token_urlsafe(24)
        user = env['res.users'].with_context(no_reset_password=True).create({
            'name': 'S00-B Synthetic ' + role,
            'login': login, 'email': login, 'password': password,
            'lang': lang, 'group_ids': [Command.set(groups)],
        })
        access[role] = {'login': login, 'password': password, 'id': user.id}
    # The disposable preview never uses the installation default admin password.
    env.ref('base.user_admin').write({'password': secrets.token_urlsafe(32)})
    with os.fdopen(os.open(access_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as output:
        json.dump(access, output)
    env['ir.config_parameter'].set_str('web.base.url', 'http://127.0.0.1:%s' % marker['port'])
    env['ir.config_parameter'].set_str('report.url', 'http://127.0.0.1:%s' % marker['port'])
    # Administrative test-fixture transaction in a new disposable database, not addon logic.
    env.cr.commit()
else:
    access = json.loads(access_file.read_text())

utc = datetime(2026, 10, 10, 16, 30)
local_model = env['res.users'].with_context(tz='Asia/Shanghai')
day = fields.Date.context_today(local_model, timestamp=utc)
assert str(day) == '2026-10-11'
assert str(fields.Date.context_today(env['res.users'].with_context(tz='UTC'), timestamp=utc)) == '2026-10-10'
assert str(fields.Datetime.context_timestamp(local_model, utc)) == '2026-10-11 00:30:00+08:00'
state = run / 'native-before.json'
if not state.exists():
    sequence = env['ir.sequence'].create({
        'name': 'S00-B Synthetic Native Sequence', 'code': 'ydental.s00b.synthetic',
        'implementation': 'standard', 'prefix': 'S00B/%(year)s/%(month)s/%(day)s/',
        'padding': 5, 'use_date_range': True, 'company_id': False,
    })
    first = sequence.next_by_id(sequence_date=day)
    # Publish only synthetic sequence fixture so separate real connections can exercise nextval.
    env.cr.commit()
    barrier = threading.Barrier(4)
    def allocate(_worker):
        with env.registry.cursor() as cursor:
            worker_env = api.Environment(cursor, SUPERUSER_ID, {'tz': 'Asia/Shanghai'})
            worker_sequence = worker_env['ir.sequence'].browse(sequence.id)
            barrier.wait(timeout=20)
            values = [worker_sequence.next_by_id(sequence_date=day) for _ in range(25)]
            cursor.commit()
            return values
    with ThreadPoolExecutor(max_workers=4) as pool:
        values = [value for batch in pool.map(allocate, range(4)) for value in batch]
    assert len(values) == 100 and len(set(values + [first])) == 101
    assert all(value.startswith('S00B/2026/10/11/') for value in values + [first])
    sequence_ids = {'sequence_id': sequence.id, 'first_number': first, 'numbers': values,
                    'threads': 4, 'connections': 4, 'allocations': 100,
                    'utc_timestamp': str(utc), 'synthetic_timezone': 'Asia/Shanghai', 'local_day': str(day),
                    'stable_codes': ['ydental.s00b.synthetic', 'access_denied'],
                    'menu_id': env.ref('ydental_base.ydental_base_menu_root').id,
                    'action_id': env.ref('ydental_base.ydental_base_action').id}
    state.write_text(json.dumps(sequence_ids, indent=2) + '\n')
    output = {'stage': 'before_upgrade', 'native': sequence_ids}
else:
    before = json.loads(state.read_text())
    sequence = env['ir.sequence'].browse(before['sequence_id'])
    assert sequence.exists() and sequence.code == before['stable_codes'][0]
    assert env.ref('ydental_base.ydental_base_menu_root').id == before['menu_id']
    assert env.ref('ydental_base.ydental_base_action').id == before['action_id']
    new_number = sequence.next_by_id(sequence_date=day)
    assert new_number not in before['numbers'] + [before['first_number']]
    actions = [json.loads(line) for line in (run / 'actions.jsonl').read_text().splitlines()]
    upgraded = any(a['action'] == 'upgrade' and a['exit_code'] == 0 and a.get('verification_exit', 0) == 0 for a in actions)
    if upgraded:
        assert json.loads(env['ir.config_parameter'].get_str('ydental.s00b.number_snapshot')) == before
    output = {'stage': 'after_upgrade' if upgraded else 'before_upgrade',
              'old_numbers_unchanged': True, 'new_number': new_number,
              'old_numbers_sha256': __import__('hashlib').sha256(state.read_bytes()).hexdigest()}

if output['stage'] == 'before_upgrade':
    env['ir.config_parameter'].set_str('ydental.s00b.number_snapshot', state.read_text())

translations = []
for role, expected in (('authorized_zh', '牙科'), ('authorized_en', 'Dental')):
    user = env['res.users'].browse(access[role]['id'])
    # Native action records are administrator-readable; ordinary-user labels are tested over HTTP.
    action = env.ref('ydental_base.ydental_base_action').with_context(lang=user.lang)
    assert action.name == expected
    translations.append({'role': role, 'lang': user.lang, 'action_label': action.name})
output['translations'] = translations
output['assertions'] = 'PASS'
# Commit only this run's synthetic fixtures; no production business record is accessed.
env.cr.commit()
(run / ('probe-' + output['stage'] + '.json')).write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(output, ensure_ascii=False))

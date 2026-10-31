import json
import os
from pathlib import Path

from odoo.exceptions import AccessError
from odoo.tools import config


def pre_init_hook(env):
    run = Path(os.environ.get('YDENTAL_S08B_RUN_DIR', '/nonexistent'))
    target = ('ydental_s08b_test_20261031035600_ef48a021', 60467, '7702674877825777694')
    if env.cr.dbname != target[0] or run.name != env.cr.dbname or not (run / 'database.json').is_file():
        raise AccessError('Examination integration verification requires its isolated test database.')
    marker = json.loads((run / 'database.json').read_text())
    env.cr.execute('SELECT current_database(), (SELECT oid FROM pg_database WHERE datname=current_database()), (pg_control_system()).system_identifier::text')
    if env.cr.fetchone() != target or (marker['database'], marker['oid'], marker['cluster']) != target:
        raise AccessError('Examination integration test database identity changed.')


if config['test_enable']:
    from . import tests

import json
import os
from pathlib import Path
import re

from odoo.exceptions import AccessError
from odoo.tools import config


def pre_init_hook(env):
    run = Path(os.environ.get('YDENTAL_S09_RUN_DIR', '/nonexistent'))
    if not re.fullmatch(r'ydental_s09_test_[0-9]{14}_[a-f0-9]{8}', env.cr.dbname) or (
            run.name != env.cr.dbname or not (run / 'database.json').is_file()):
        raise AccessError('S09 verification requires its own guarded synthetic database.')
    metadata = json.loads((run / 'database.json').read_text())
    env.cr.execute('SELECT oid FROM pg_database WHERE datname = %s', [env.cr.dbname])
    if metadata['database'] != env.cr.dbname or metadata['oid'] != env.cr.fetchone()[0] or (
            metadata['cluster'] != '7694897083368259627'):
        raise AccessError('S09 verification database identity changed.')


if config['test_enable']:
    from . import tests

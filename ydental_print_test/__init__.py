import os
import re
from pathlib import Path
from odoo.exceptions import AccessError
from odoo.tools import config


def pre_init_hook(env):
    run = Path(os.environ.get('YDENTAL_S08C_RUN_DIR', '/nonexistent'))
    if not re.fullmatch(r'ydental_s08c_test_[0-9]{14}_[a-f0-9]{8}', env.cr.dbname) or run.name != env.cr.dbname or not (run / 'database.json').is_file():
        raise AccessError('PDF synthetic verification requires a new guarded S08-C database.')


if config['test_enable']:
    from . import tests

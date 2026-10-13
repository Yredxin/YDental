import os
import re
from pathlib import Path

from odoo.exceptions import AccessError
from odoo.tools import config


def pre_init_hook(env):
    stage = 'S08C' if os.environ.get('YDENTAL_S08C_RUN_DIR') else 'S08B'
    run = Path(os.environ.get('YDENTAL_' + stage + '_RUN_DIR', '/nonexistent'))
    if not re.fullmatch(r'ydental_' + stage.lower() + r'_test_[0-9]{14}_[a-f0-9]{8}', env.cr.dbname) or run.name != env.cr.dbname or not (run / 'database.json').is_file():
        raise AccessError('Clinical synthetic verification requires a new guarded S08-B database.')


from . import models


if config['test_enable']:
    from . import tests

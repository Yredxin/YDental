import os
from pathlib import Path
import re

from odoo.exceptions import AccessError

from . import models


def pre_init_hook(env):
    run = os.environ.get('YDENTAL_S04_RUN_DIR', '')
    if not re.fullmatch(r'ydental_s04_test_[0-9]{14}_[a-f0-9]{8}', env.cr.dbname) or not run or (
        Path(run).name != env.cr.dbname or not Path(run, 'database.json').is_file()
    ):
        raise AccessError('Synthetic patient verification requires a newly recorded isolated S04 database.')

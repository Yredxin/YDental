import os
import re

from odoo.exceptions import AccessError


def pre_init_hook(env):
    if not re.fullmatch(r'ydental_s05_test_[0-9]{14}_[a-f0-9]{8}', env.cr.dbname) or not os.environ.get('YDENTAL_S05_RUN_DIR'):
        raise AccessError('S05 verification refused outside a newly isolated S05 database.')


from . import models
from . import tests

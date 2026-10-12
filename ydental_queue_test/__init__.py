import os
import re

from odoo.exceptions import AccessError


def pre_init_hook(env):
    if not re.fullmatch(r'ydental_s06[abc]_test_[0-9]{14}_[a-f0-9]{8}', env.cr.dbname) or not os.environ.get('YDENTAL_S06' + env.cr.dbname[len('ydental_s06')].upper() + '_RUN_DIR'):
        raise AccessError('S06-A verification refused outside a newly isolated S06-A database.')


from . import models
from . import tests

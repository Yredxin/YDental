from odoo.exceptions import AccessError
from odoo.tools import config

from . import models


def pre_init_hook(env):
    if env.cr.dbname != 'ydental_s11_synth_20261023_01':
        raise AccessError('S12 synthetic verification is restricted to its existing authorized target.')
    env.cr.execute("""SELECT db.oid, (pg_control_system()).system_identifier::text,
        current_user FROM pg_database db WHERE db.datname=current_database()""")
    if env.cr.fetchone() != (2171423, '7694897083368259627', 'ydental_s11_synth_20261023_01'):
        raise AccessError('S12 synthetic verification target identity changed.')


if config['test_enable']:
    from . import tests

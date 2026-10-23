from odoo.exceptions import AccessError


def pre_init_hook(env):
    from .models.clock import EXPECTED_CLUSTER, EXPECTED_DB, EXPECTED_OID
    if env.cr.dbname != EXPECTED_DB:
        raise AccessError('S11 clock test support is restricted to the authorized scratch database.')
    env.cr.execute('''
        SELECT d.oid, c.system_identifier::text
          FROM pg_database d CROSS JOIN pg_control_system() c
         WHERE d.datname = current_database()
    ''')
    identity = env.cr.fetchone()
    if not identity or identity != (EXPECTED_OID, EXPECTED_CLUSTER):
        raise AccessError('S11 clock test support is restricted to the exact admitted database identity.')


from . import models
from . import controllers

from odoo.exceptions import AccessError


def pre_init_hook(env):
    from .models.clock import guard
    if env.cr.dbname != 'ydental_s10_test_20261017105432_ce6dcbf8':
        raise AccessError('S11 clock test support is restricted to the authorized scratch database.')
    guard(env)


from . import models
from . import controllers

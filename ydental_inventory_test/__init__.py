from . import models
from odoo.tools import config

if config['test_enable']:
    from . import tests


def pre_init_hook(env):
    from .models.adapter import guard
    guard(env)

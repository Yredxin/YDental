from . import models
from . import controllers

from odoo.tools import config

if config['test_enable']:
    from . import tests

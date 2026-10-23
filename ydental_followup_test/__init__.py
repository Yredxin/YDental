from odoo.tools import config

from . import models

if config['test_enable']:
    from . import tests

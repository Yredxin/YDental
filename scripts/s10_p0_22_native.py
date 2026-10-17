"""Load only verified clone registry. Scenario owns its cursor; no idle outer cursor."""
import os
import sys
import s10_p0_22_contract as c
c.gate(business=True)
assert os.environ['YDENTAL_S10_RUN_DIR'] == str(c.RUN)
sys.path.insert(0, str(c.CORE_ROOT))
import odoo.init
from odoo.tools import config
config.parse_config(['-c', str(c.RUN / 'odoo.conf'), '--no-http'], setup_logging=True)
assert config['db_name'] == [c.NAME] and not config['update'] and not config['init']
from odoo.orm.registry import Registry
from odoo.orm.environments import Environment
from s10_p0_22_runtime import verify_loaded
from s10_p0_22_cases import run
registry = Registry(c.NAME)
with registry.cursor() as cr:
    c.capture(cr)  # Bound database/OID/cluster before any ORM business operation.
    verify_loaded(Environment(cr, 1, {}))
    cr.rollback()
run(registry, sys.argv[1])

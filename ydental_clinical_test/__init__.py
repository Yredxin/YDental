import importlib.util
import os
import re
from pathlib import Path

from odoo.exceptions import AccessError
from odoo.tools import config


def pre_init_hook(env):
    if env.cr.dbname == 'ydental_s10_test_20261017105432_ce6dcbf8':
        repo_root = Path(__file__).resolve().parents[1]
        launcher_path = repo_root / 'scripts' / 's11' / 'launcher.py'
        spec = importlib.util.spec_from_file_location('ydental_s11_test_launcher', launcher_path)
        if not spec or not spec.loader:
            raise AccessError('S11 clinical verification requires a valid private scratch admission.')
        launcher = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(launcher)
        try:
            launcher.validate_connected_database(env)
        except launcher.Refusal as error:
            raise AccessError('S11 clinical verification requires a valid private scratch admission.') from error
        return

    s09 = Path(os.environ.get('YDENTAL_S09_RUN_DIR', '/nonexistent'))
    if re.fullmatch(r'ydental_s09_test_[0-9]{14}_[a-f0-9]{8}', env.cr.dbname) and s09.name == env.cr.dbname and (s09 / 'database.json').is_file():
        import json
        marker = json.loads((s09 / 'database.json').read_text())
        env.cr.execute('SELECT oid FROM pg_database WHERE datname=%s', [env.cr.dbname])
        if marker['database'] == env.cr.dbname and marker['oid'] == env.cr.fetchone()[0] and marker['cluster'] == '7694897083368259627':
            return
    run = Path(os.environ.get('YDENTAL_S08A_RUN_DIR', '/nonexistent'))
    if not re.fullmatch(r'ydental_s08a_test_[0-9]{14}_[a-f0-9]{8}', env.cr.dbname) or run.name != env.cr.dbname or not (run / 'database.json').is_file():
        raise AccessError('Clinical synthetic verification requires a new guarded S08-A database.')


from . import models


if config['test_enable']:
    from . import tests

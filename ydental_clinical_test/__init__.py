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
            runtime, admission, database, branch, candidate = launcher.validate_pair()
            admitted_server_addr = launcher.parse_server_address(
                admission.get('database_server_addr'), 'database_server_addr')
        except launcher.Refusal as error:
            raise AccessError('S11 clinical verification requires a valid private scratch admission.') from error
        env.cr.execute('''SELECT db.oid, current_user, inet_server_addr()::text, inet_server_port()
            FROM pg_database db WHERE db.datname=current_database()''')
        row = env.cr.fetchone()
        try:
            connected_server_addr = launcher.parse_server_address(row[2], 'connected server address') if row else None
        except launcher.Refusal as error:
            raise AccessError('S11 clinical verification requires a valid connected database endpoint.') from error
        if (branch == 'codex/s11-followup-lab-r1' and candidate == admission['candidate_commit'] and
                database['name'] == env.cr.dbname and admission['database_oid'] == 2144130 and
                admission['cluster_ref'] == '7694897083368259627' and row and row[0] == 2144130 and
                row[1] == database['user'] and connected_server_addr == admitted_server_addr and
                row[3] == database['port'] and
                runtime['database']['expected_cluster_ref'] == admission['cluster_ref']):
            return
        raise AccessError('S11 clinical verification target does not match the authorized scratch database.')

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

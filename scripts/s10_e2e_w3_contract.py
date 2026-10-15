"""W3 isolated database marker and unchanged adapter contract."""

import ast
import hashlib
import json
import os
from pathlib import Path
import re

CORE_SHA = 'f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_marker(*, database, oid, cluster, actual_core, config, run, auth, base,
                 port, source, source_oid, policy, prepare, control, browser, contract):
    if actual_core != CORE_SHA or type(oid) is not int or oid <= 0:
        raise ValueError('Core or real database OID does not match the locked W3 identity.')
    run = Path(run)
    if run.is_symlink() or run.name != database:
        raise ValueError('Run directory must match the isolated database.')
    return {
        'database': database, 'oid': oid, 'cluster': cluster, 'core': actual_core,
        'config_sha256': digest(config), 'source': source, 'source_oid': source_oid,
        'auth': auth, 'base': base, 'port': port,
        'policy_sha256': digest(policy), 'shell_sha256': digest(prepare),
        'control_sha256': digest(control), 'browser_sha256': digest(browser),
        'contract_sha256': digest(contract),
    }


def validate_marker(*, marker, database, oid, cluster, actual_core, config, run,
                    auth, base, port, source, source_oid, policy, prepare, control, browser,
                    contract):
    expected = build_marker(database=database, oid=oid, cluster=cluster,
        actual_core=actual_core, config=config, run=run, auth=auth, base=base,
        port=port, source=source, source_oid=source_oid, policy=policy,
        prepare=prepare, control=control, browser=browser, contract=contract)
    if marker != expected:
        raise ValueError('W3 marker does not match the complete producer and consumer contract.')
    if Path(config).is_symlink() or Path(run).is_symlink():
        raise ValueError('Private config and run directory must not be symlinks.')
    return True


def check_fixed_adapter(*, adapter_source, run, database, oid):
    """Execute the unchanged adapter's real pre_init_hook AST with a fake cursor."""
    tree = ast.parse(Path(adapter_source).read_text(), filename=str(adapter_source))
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                 and node.name == 'pre_init_hook']
    if len(functions) != 1:
        raise ValueError('The fixed adapter hook is missing or ambiguous.')

    class AdapterAccessError(Exception):
        pass

    namespace = {'hashlib': hashlib, 'json': json, 'os': os, 'Path': Path,
                 're': re, 'AccessError': AdapterAccessError}
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(adapter_source), 'exec'), namespace)

    class FakeCursor:
        dbname = database

        def execute(self, query, params):
            if query != 'SELECT oid FROM pg_database WHERE datname=%s' or params != [database]:
                raise ValueError('The adapter requested an unexpected SQL contract.')

        def fetchone(self):
            return (oid,)

    class FakeEnv:
        cr = FakeCursor()

    previous = os.environ.get('YDENTAL_S10_RUN_DIR')
    os.environ['YDENTAL_S10_RUN_DIR'] = str(run)
    try:
        namespace['pre_init_hook'](FakeEnv())
    finally:
        if previous is None:
            os.environ.pop('YDENTAL_S10_RUN_DIR', None)
        else:
            os.environ['YDENTAL_S10_RUN_DIR'] = previous
    return True


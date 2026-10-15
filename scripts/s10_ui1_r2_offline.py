"""No Odoo process or database: exercise the real marker builder and fixed hook AST."""

import hashlib
import importlib
import json
from pathlib import Path
import sys
import tempfile

from s10_ui1_r2_contract import (CORE_SHA, build_marker, check_fixed_adapter,
                                 classify_baseline, validate_marker)

ROOT = Path(__file__).resolve().parents[1]
CONTROL = importlib.import_module('s10_ui1_r2_control')
ADAPTER = ROOT / 'ydental_settlement_test/__init__.py'
PREPARE = ROOT / 'scripts/s10_ui1_r2_prepare.py'
BROWSER = ROOT / 'scripts/s10_ui1_r2_browser.py'
POLICY = ROOT / 'scripts/s08c_network_policy.py'
assert CONTROL.NAME == 'ydental_s10_test_20261015014500_c72e6f91'
assert CONTROL.PORT == 18271 and CONTROL.AUTH == 6182293301
assert CONTROL.BASE == 'd59f15d364c3d00641fdb7a155fcbb35236838a5'
assert CONTROL.core_head() == CORE_SHA
assert 'core' not in json.loads((ROOT / '.local/ydental_s10_test_20261015011000_a91c4d70/database.json').read_text())

checks = []


def check(name, function):
    function()
    checks.append(name)


def reject(name, function):
    try:
        function()
    except Exception as error:
        assert type(error).__name__ in ('ValueError', 'AdapterAccessError'), (name, error)
        checks.append(name + ':REJECTED:' + type(error).__name__)
        return
    raise AssertionError(name + ' was accepted')


with tempfile.TemporaryDirectory(prefix='ui1-r1-offline-') as temp:
    run = Path(temp) / CONTROL.NAME
    run.mkdir()
    config = run / 'odoo.conf'
    config.write_text('[options]\ndb_name = synthetic-offline\n')
    policy = run / 'sitecustomize.py'
    policy.write_bytes(POLICY.read_bytes())
    args = dict(database=CONTROL.NAME, oid=123456789, cluster=CONTROL.CLUSTER,
                actual_core=CONTROL.core_head(), config=config, run=run,
                auth=CONTROL.AUTH, base=CONTROL.BASE, port=CONTROL.PORT,
                source=CONTROL.SOURCE, source_oid=2100080, policy=policy,
                prepare=PREPARE, control=ROOT / 'scripts/s10_ui1_r2_control.py',
                browser=BROWSER, contract=ROOT / 'scripts/s10_ui1_r2_contract.py')
    marker = build_marker(**args)
    (run / 'database.json').write_text(json.dumps(marker))
    check('complete_builder_validator', lambda: validate_marker(marker=marker, **args))
    check('complete_real_adapter_ast', lambda: check_fixed_adapter(
        adapter_source=ADAPTER, run=run, database=CONTROL.NAME, oid=args['oid']))

    for label, changed in (
            ('missing_core', {'core': None}), ('wrong_core', {'core': 'wrong'}),
            ('wrong_database', {'database': 'wrong'}), ('wrong_oid', {'oid': 1}),
            ('wrong_cluster', {'cluster': 'wrong'}),
            ('wrong_config_hash', {'config_sha256': '0' * 64})):
        bad = dict(marker)
        bad.update(changed)
        if label == 'missing_core':
            bad.pop('core')
        (run / 'database.json').write_text(json.dumps(bad))
        reject(label + '_controller', lambda bad=bad: validate_marker(marker=bad, **args))
        reject(label + '_real_adapter_ast', lambda: check_fixed_adapter(
            adapter_source=ADAPTER, run=run, database=CONTROL.NAME, oid=args['oid']))
    (run / 'database.json').write_text(json.dumps(marker))
    config.write_text(config.read_text() + 'dbfilter = wrong\n')
    reject('changed_config_controller', lambda: validate_marker(marker=marker, **args))
    reject('changed_config_real_adapter_ast', lambda: check_fixed_adapter(
        adapter_source=ADAPTER, run=run, database=CONTROL.NAME, oid=args['oid']))
    config.write_text('[options]\ndb_name = synthetic-offline\n')
    bad = dict(marker, auth=0)
    reject('wrong_auth_controller', lambda: validate_marker(marker=bad, **args))
    bad = dict(marker, browser_sha256='0' * 64)
    reject('wrong_browser_hash_controller', lambda: validate_marker(marker=bad, **args))
    bad = dict(marker, contract_sha256='0' * 64)
    reject('wrong_contract_hash_controller', lambda: validate_marker(marker=bad, **args))

for entry in ('preflight', 'create', 'verify-target', 'prepare', 'serve-before', 'wait-http',
              'stop-before', 'upgrade', 'serve-after', 'stop-after'):
    check('cli_' + entry, lambda entry=entry: CONTROL.COMMANDS[entry])
for label, data, expected in (
    ('json_navigation', dict(status=200, content_type='application/json; charset=utf-8',
        location=None, page_path='/ydental/settlement/action', has_workbench=False),
        'REPRODUCED_JSON_NAVIGATION'),
    ('html_workbench', dict(status=200, content_type='text/html; charset=utf-8',
        location=None, page_path='/ydental/settlement', has_workbench=True),
        'NOT_REPRODUCED_WORKBENCH'),
    ('303_workbench', dict(status=303, content_type='text/html; charset=utf-8',
        location='/ydental/settlement', page_path='/ydental/settlement', has_workbench=True),
        'NOT_REPRODUCED_WORKBENCH'),
    ('303_redirect', dict(status=303, content_type='text/html',
        location='/ydental/settlement', page_path='/ydental/settlement/action', has_workbench=False),
        'UNCLASSIFIED_STOP'),
    ('403_json', dict(status=403, content_type='application/json',
        location=None, page_path='/ydental/settlement/action', has_workbench=False),
        'UNCLASSIFIED_STOP')):
    check('classification_' + label, lambda data=data, expected=expected:
          (classify_baseline(**data) == expected) or (_ for _ in ()).throw(AssertionError(label)))

result = {'status': 'SIMULATED_PASS', 'checks': len(checks), 'check_names': checks,
          'real_adapter_source_sha256': hashlib.sha256(ADAPTER.read_bytes()).hexdigest(),
          'producer': 's10_ui1_r2_contract.build_marker',
          'consumer': 'fixed ydental_settlement_test.pre_init_hook AST',
          'oid_used': 'SIMULATED_123456789_NOT_A_DATABASE',
          'new_database_created': False, 'odoo_processes': 0, 'browser_processes': 0}
print(json.dumps(result, ensure_ascii=True, sort_keys=True))

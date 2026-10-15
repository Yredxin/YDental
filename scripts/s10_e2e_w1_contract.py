"""Pure UI1-R2 marker and baseline response contracts used by the real runners."""

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
        raise ValueError('Core or real database OID does not match the locked UI1-R2 identity.')
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
        raise ValueError('UI1-R2 marker does not match the complete producer and consumer contract.')
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


def classify_baseline(*, status, content_type, location, page_path, has_workbench):
    """Classify actual browser navigation before any response body decoding."""
    media_type = (content_type or '').split(';', 1)[0].strip().lower()
    if status == 200 and media_type == 'application/json' and (
            page_path == '/ydental/settlement/action' and not has_workbench):
        return 'REPRODUCED_JSON_NAVIGATION'
    if status in (200, 302, 303) and has_workbench and page_path == '/ydental/settlement':
        return 'NOT_REPRODUCED_WORKBENCH'
    # A Location header alone does not prove the browser reached an operable desk.
    return 'UNCLASSIFIED_STOP'


def baseline_record(details, *, oid, parsed_json=None):
    """Validate the actual browser observation before writing a continuation proof."""
    if details['request_url'] != '/ydental/settlement/action':
        raise ValueError('Unexpected form endpoint')
    if not (details['request_content_type'] or '').startswith('application/x-www-form-urlencoded'):
        raise ValueError('Browser did not submit an ordinary HTML form')
    classification = classify_baseline(status=details['status'],
        content_type=details['response_content_type'], location=details['location'],
        page_path=details['page_path'], has_workbench=details['has_workbench'])
    if classification == 'UNCLASSIFIED_STOP':
        raise ValueError('Unclassified browser landing page')
    before = details['before']['counts']
    after = details['after']['counts']
    if after['ydental_settlement_receipt'] != before['ydental_settlement_receipt'] + 1:
        raise ValueError('Baseline receipt was not committed exactly once')
    if after['account_move'] <= before['account_move']:
        raise ValueError('Baseline native accounting move absent')
    reproduced = classification == 'REPRODUCED_JSON_NAVIGATION'
    if reproduced and (not isinstance(parsed_json, dict)
                       or parsed_json.get('result') != 'accepted'
                       or parsed_json.get('amount') != 100):
        raise ValueError('JSON navigation lacks accepted finance receipt')
    if not reproduced and parsed_json is not None:
        raise ValueError('HTML response must not be decoded as JSON')
    return {
        'complete': True, 'oid': oid, 'classification': classification,
        'reproduced': reproduced, 'finance_verified': True,
        'request_content_type': details['request_content_type'],
        'content_type': details['response_content_type'],
        'status': details['status'], 'page_path': details['page_path'],
        'has_workbench': details['has_workbench'], 'location': details['location'],
        'invoice_id': parsed_json.get('invoice_id') if parsed_json else None,
        'state': details['after'],
    }

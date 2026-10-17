"""R1.2 owned-target initial RO admission; never opens a protected source."""
import argparse
import hashlib
from pathlib import Path

from s10_lc2_evidence import collect_selection, runtime_gate, save_once
from s10_lc2_logging import strict_loads
from s10_lc2_targets import EXEC_ROOT, LEGACY_EXEC_ROOT, RUN_ROOT, SOURCE_CAPTURE, PackageBudget, credentials, verify_clone

TARGETS = {'main': ('ydental_s10_test_20261017105432_810a7d9c', 2144129),
           'scratch': ('ydental_s10_test_20261017105432_ce6dcbf8', 2144130)}


def observe(mode, *, approval, product_commit, test_commit):
    dispatch = runtime_gate(approval, product_commit=product_commit, test_commit=test_commit)
    if (mode not in TARGETS or 'reentry-' + mode not in dispatch.get('allowed_actions', [])
            or set(dispatch.get('allowed_target_names', [])) != {name for name, oid in TARGETS.values()}):
        raise RuntimeError('R12_REENTRY_NOT_DISPATCHED')
    database, oid = TARGETS[mode]
    run = RUN_ROOT / database
    marker_bytes = (run / 'database.json').read_bytes()
    directory = EXEC_ROOT / ('reentry-' + mode)
    if mode == 'main':
        selections = strict_loads((LEGACY_EXEC_ROOT / 'admission-r11-final/admission-selection.json').read_bytes())['tables']
        if len(selections) != 316:
            raise RuntimeError('R12_MAIN_SELECTION_DRIFT')
        max_rows, max_bytes = 10000, 16 * 1024 * 1024
    else:
        selections = [{'table': 'ir_module_module', 'order': ['id']}]
        max_rows, max_bytes = 1024, 4 * 1024 * 1024
    import psycopg2
    collect_selection(psycopg2.connect, credentials(), database=database, expected_oid=oid,
                      selections=selections, directory=directory, budget=PackageBudget(EXEC_ROOT),
                      allowed_target_names=[name for name, value in TARGETS.values()],
                      target_directory=run, config_path=run / 'odoo.conf', collect_metadata=True,
                      max_rows=max_rows, max_bytes=max_bytes)
    if (run / 'database.json').read_bytes() != marker_bytes:
        raise RuntimeError('R12_REENTRY_MARKER_CHANGED')
    if mode == 'main':
        result = verify_clone(SOURCE_CAPTURE, directory, run=run)
        result.update(admission_ready=True, purpose='main historical A/B/C and E-MAIN only',
                      current_editor_release_claimed=False)
    else:
        rows = [strict_loads(strict_loads(line)['server_json_text'])
                for line in (directory / 'ir_module_module.rows.jsonl').read_bytes().splitlines()]
        installed = [{key: row[key] for key in ['id', 'name', 'state', 'latest_version']}
                     for row in rows if row['state'] == 'installed']
        pending = [row['name'] for row in rows if row['state'] in {'to install', 'to upgrade', 'to remove'}]
        schema = strict_loads((directory / 'schema.json').read_bytes())
        business_tables = [name for name in schema if name.startswith(('ydental_', 'account_', 'stock_'))]
        result = {'purpose': 'normal Odoo install reentry then independent synthetic D and E-D',
                  'installed_modules': installed, 'pending_module_names': pending,
                  'public_physical_table_count': len(schema), 'business_tables_present': business_tables,
                  'business_scope_absence_proven_by_actual_schema': not business_tables,
                  'module_catalog_rows': len(rows), 'whole_database_empty_claimed': False,
                  'whole_database_rollback_claimed': False,
                  'admission_ready': ({row['name'] for row in installed} == {'base'}
                                      and not pending and not business_tables)}
    result.update(database=database, oid=oid, marker_unchanged=True,
                  marker_sha256=hashlib.sha256(marker_bytes).hexdigest(),
                  independent_connection_closed_before_review=True)
    return save_once(directory / 'reentry-decision.json', result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=TARGETS)
    parser.add_argument('--approval', required=True)
    parser.add_argument('--product-commit', required=True)
    parser.add_argument('--test-commit', required=True)
    args = parser.parse_args()
    print(observe(args.mode, approval=args.approval, product_commit=args.product_commit,
                  test_commit=args.test_commit)['path'])


if __name__ == '__main__':
    main()

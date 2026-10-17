"""Dispatch-gated LC2 clone/scratch creation and independent preservation checks."""
import argparse
import configparser
from datetime import datetime, timezone
import hashlib
from itertools import zip_longest
import json
from pathlib import Path
import secrets
import time

from s10_lc2_admission import verify_admission
from s10_lc2_evidence import ACCIDENT, Budget, RAW_LIMIT, collect_selection, runtime_gate, save_once
from s10_lc2_logging import strict_loads
from s10_lc2_runtime import create_targets, prepare_target, source_filestore_inventory
from s10_lc2_supervisor import safe_plain
from s10_lc2_framework_caller import FAILURE_NAME, framework_failure_facts

ROOT = Path(__file__).resolve().parents[1]
LEGACY_EXEC_ROOT = ROOT / '.local/s10-lc2-exec-20261017'
EXEC_ROOT = ROOT / '.local/s10-lc2-r12-20261017'
RUN_ROOT = ROOT / '.local/s10-lc2/20261017-lc2-exec01'
PLAN = LEGACY_EXEC_ROOT / 'target-plan.json'
SOURCE_CAPTURE = LEGACY_EXEC_ROOT / 'admission-r11-final/capture'
# Parent coordinator ownership is process-local. Framework HttpCase requests
# use their separate exact-launch grant and the same cumulative ledger.
_DISPATCH_OWNER = None
_DISPATCH_FAILURE = None


def freeze_dispatch(failure):
    global _DISPATCH_FAILURE
    if _DISPATCH_FAILURE is None:
        _DISPATCH_FAILURE = dict(failure)


def require_dispatch_unfrozen():
    if _DISPATCH_FAILURE is None and (EXEC_ROOT / FAILURE_NAME).exists():
        freeze_dispatch(framework_failure_facts(EXEC_ROOT))
    if _DISPATCH_FAILURE is not None:
        raise RuntimeError('APPLICATION_DISPATCH_FROZEN_' + _DISPATCH_FAILURE['reason'])


def bind_dispatch_owner(owner):
    global _DISPATCH_OWNER
    require_dispatch_unfrozen()
    if _DISPATCH_OWNER is not None:
        raise RuntimeError('ANOTHER_APPLICATION_DISPATCH_OWNER_ACTIVE')
    _DISPATCH_OWNER = owner


def release_dispatch_owner(owner):
    global _DISPATCH_OWNER
    if _DISPATCH_OWNER is owner:
        _DISPATCH_OWNER = None


class PackageBudget(Budget):
    """R1.2 cumulative resources; both evidence windows plus shared owned files."""
    def consume(self, kind):
        require_dispatch_unfrozen()
        if kind in {'accident_ro', 'maintenance', 'create'}:
            raise RuntimeError('R12_NO_PROTECTED_SOURCE_OR_CREATE_DISPATCH')
        if kind in {'http', 'original_get'}:
            if _DISPATCH_OWNER is None:
                raise RuntimeError('NO_ACTIVE_APPLICATION_DISPATCH_GUARD')
            _DISPATCH_OWNER.check()
        return super().consume(kind)

    def check_storage(self):
        if self.path.exists() and time.time() - strict_loads(self.path.read_bytes())['started_epoch'] > 8 * 3600:
            raise RuntimeError('RUN_WINDOW_EXHAUSTED')
        size = sum(path.stat().st_size for base in (LEGACY_EXEC_ROOT, EXEC_ROOT, RUN_ROOT) if base.exists()
                   for path in base.rglob('*') if path.is_file() and not path.is_symlink())
        if size >= RAW_LIMIT * .9:
            raise RuntimeError('GLOBAL_RAW_STORAGE_PAUSE_AT_90_PERCENT')
        if size >= RAW_LIMIT * .8:
            safe_plain(EXEC_ROOT / 'global-storage-warning.tsv', ['80_PERCENT', size])
        return size


def prepare_plan():
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
    targets = [{'role': role, 'database': 'ydental_s10_test_' + timestamp + '_' + secrets.token_hex(4),
                'port': port} for role, port in [('main', 18410), ('scratch', 18411)]]
    value = {'targets': targets, 'run_root': str(RUN_ROOT),
             'baseline': str(SOURCE_CAPTURE / 'admission-decision.json'),
             'baseline_sha256': hashlib.sha256((SOURCE_CAPTURE / 'admission-decision.json').read_bytes()).hexdigest(),
             'raw_roots': [str(EXEC_ROOT), str(RUN_ROOT)],
             'single_maintenance': True, 'create_limit': 2}
    save_once(PLAN, value)
    return value


def credentials():
    config = configparser.ConfigParser(interpolation=None)
    config.read(ROOT.parent / 'odoo.conf')
    opt = config['options']
    return {'host': opt['db_host'], 'port': opt['db_port'], 'user': opt['db_user'],
            'password': opt['db_password'], 'application_name': 'ydental_s10_lc2_owned_targets'}


def verify_clone(source, target, *, run):
    source, target, run = Path(source), Path(target), Path(run)
    source_index = strict_loads((source / 'sealed-index.json').read_bytes())['files']
    target_index = strict_loads((target / 'sealed-index.json').read_bytes())['files']
    if {item['path'] for item in source_index} != {item['path'] for item in target_index}:
        raise AssertionError('CLONE_SELECTION_SET_DRIFT')
    metadata_files = ['schema.json', 'native-access.json', 'installed-modules.json', 'queue-settings.json']
    for name in metadata_files:
        if strict_loads((source / name).read_bytes()) != strict_loads((target / name).read_bytes()):
            raise AssertionError('CLONE_SCHEMA_SECURITY_OR_MODULE_METADATA_DRIFT')
    compared_rows = 0
    for item in source_index:
        with (source / item['path']).open('rb') as left, (target / item['path']).open('rb') as right:
            for source_raw, target_raw in zip_longest(left, right):
                if source_raw is None or target_raw is None:
                    raise AssertionError('CLONE_ROW_COUNT_DRIFT')
                a, b = strict_loads(source_raw), strict_loads(target_raw)
                if a['physical_table'] != b['physical_table'] or a['server_json_text'] != b['server_json_text']:
                    raise AssertionError('CLONE_PHYSICAL_OR_STORED_ROW_DRIFT')
                compared_rows += 1
    files = strict_loads((run / 'initial-filestore-index.json').read_bytes())['files']
    database = run.name
    for item in files:
        path = run / 'data/filestore' / database / item['path']
        if path.is_symlink() or path.stat().st_size != item['bytes'] or hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            raise AssertionError('CLONE_FILESTORE_BYTES_DRIFT')
    result = {'stored_rows_equal': True, 'compared_rows': compared_rows,
              'filestore_files_equal': len(files), 'copied_not_new_measurement': False,
              'schema_security_modules_and_queue_settings_equal': True,
              'independent_target_RO_measurement': True, 'old_source_business_writes': 0}
    save_once(target / 'clone-verification.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['prepare', 'create', 'verify-source', 'verify-target'])
    parser.add_argument('--approval')
    parser.add_argument('--product-commit')
    parser.add_argument('--test-commit')
    args = parser.parse_args()
    if args.mode == 'prepare':
        value = prepare_plan()
        print(json.dumps({'targets': value['targets'], 'database_connections': 0}))
        return
    dispatch = runtime_gate(args.approval, product_commit=args.product_commit, test_commit=args.test_commit)
    plan = strict_loads(PLAN.read_bytes())
    if (args.mode not in dispatch.get('allowed_actions', [])
            or set(dispatch.get('allowed_target_names', [])) != {item['database'] for item in plan['targets']}):
        raise RuntimeError('TARGET_ACTION_NOT_DISPATCHED')
    budget = PackageBudget(EXEC_ROOT)
    baseline = Path(plan['baseline'])
    if hashlib.sha256(baseline.read_bytes()).hexdigest() != plan['baseline_sha256']:
        raise RuntimeError('COPY_BASELINE_ARTIFACT_DRIFT')
    admission = strict_loads(baseline.read_bytes())
    if admission['copy_admission'] is not True:
        raise RuntimeError('COPY_NOT_ADMITTED')
    import psycopg2
    if args.mode == 'create':
        save_once(EXEC_ROOT / 'source-filestore-precopy.json', source_filestore_inventory())
        created = create_targets(psycopg2.connect, credentials(), targets=plan['targets'],
                                 directory=EXEC_ROOT / 'create-window', budget=budget, main_admission=admission)
        markers = []
        for item in created:
            budget.check_storage()
            markers.append(prepare_target(item, run_root=RUN_ROOT, port=item['port'],
                                          product_commit=args.product_commit, test_commit=args.test_commit,
                                          budget=budget))
        save_once(EXEC_ROOT / 'owned-target-markers.json', {'markers': markers})
        print(json.dumps({'created': markers, 'odoo_started': 0}, ensure_ascii=True))
    else:
        selections = strict_loads((LEGACY_EXEC_ROOT / 'admission-r11-final/admission-selection.json').read_bytes())['tables']
        if args.mode == 'verify-source':
            directory = EXEC_ROOT / 'source-after-copy'
            collect_selection(psycopg2.connect, credentials(), database=ACCIDENT, expected_oid=2144127,
                              selections=selections, directory=directory, budget=budget)
            result = verify_admission(directory)
        else:
            marker = next(item for item in strict_loads((EXEC_ROOT / 'owned-target-markers.json').read_bytes())['markers']
                          if item['role'] == 'main')
            run = RUN_ROOT / marker['database']
            directory = EXEC_ROOT / 'main-after-copy'
            collect_selection(psycopg2.connect, credentials(), database=marker['database'], expected_oid=marker['oid'],
                              selections=selections, directory=directory, budget=budget,
                              allowed_target_names=[item['database'] for item in plan['targets']],
                              target_directory=run, config_path=run / 'odoo.conf', collect_metadata=True)
            result = verify_clone(SOURCE_CAPTURE, directory, run=run)
        print(json.dumps(result, ensure_ascii=True))


if __name__ == '__main__':
    main()

"""Dispatch-gated LC2 clone/scratch creation and independent preservation checks."""
import argparse
import configparser
from datetime import datetime, timezone
import hashlib
from itertools import zip_longest
import json
import os
from pathlib import Path
import secrets
import sys
import time

from s10_lc2_admission import verify_admission
from s10_lc2_evidence import ACCIDENT, Budget, RAW_LIMIT, collect_selection, runtime_gate, save_once
from s10_lc2_logging import strict_loads
from s10_lc2_runtime import create_targets, prepare_target, source_filestore_inventory
from s10_lc2_supervisor import safe_plain
from s10_lc2_framework_caller import FAILURE_NAME, framework_failure_facts
from s10_lc2_task_profile import CURRENT_PLAN, TaskProfile

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
_PROFILE_FAILURES = {}


def freeze_dispatch(failure, profile=None):
    global _DISPATCH_FAILURE
    if profile is not None:
        _PROFILE_FAILURES.setdefault(profile.message_id, dict(failure))
        return
    if _DISPATCH_FAILURE is None:
        _DISPATCH_FAILURE = dict(failure)


def _current_c_renderer_incident_read_only(profile):
    """Only the preserved C renderer exit-one incident permits its one RO observer."""
    if profile.message_id != CURRENT_PLAN:
        return False
    scope = profile.current_scope()
    incident = scope.get('incident_read_only', {})
    if (set(scope['action_reviews']) != {'target-ro'}
            or incident.get('incident') != 'C_RENDERER_EXIT_ONE'
            or incident.get('stop_sha256') != 'c32c0944ec6eb0fa543082d6ecfb928d1cc33bf943c54d47ebf0afc06619eae6'
            or incident.get('event_log_sha256') != 'd92f47b506b77767439e31baeac85b5b69d8ff121528d7aedc841506bd16763c'):
        return False
    stop_path = profile.root / 'HARD-STOP.json'
    if stop_path.is_symlink() or not stop_path.is_file() or stop_path.stat().st_uid != os.getuid():
        return False
    stop_raw = stop_path.read_bytes()
    if hashlib.sha256(stop_raw).hexdigest() != incident['stop_sha256']:
        return False
    stopped = strict_loads(stop_raw)
    if stopped != {'pid': 1829480, 'primary_event_id': '6208b49b9433427bb9ca2d4020f7c775',
            'reason': 'RENDERER_NONZERO_REQUIRES_VERIFICATION', 'root_event_id': None,
            'ts_utc': '2026-10-18T08:19:09.431668+00:00'}:
        return False
    def verified_reference(name):
        path = ROOT / incident[name + '_ref']
        if (path.is_symlink() or not path.resolve().is_relative_to(profile.root)
                or path.stat().st_uid != os.getuid()):
            raise RuntimeError('C_INCIDENT_RO_REFERENCE_INVALID')
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != incident[name + '_sha256']:
            raise RuntimeError('C_INCIDENT_RO_REFERENCE_BYTES_CHANGED')
        return path.resolve(), raw
    event_path, event_raw = verified_reference('event_log')
    expected_log = profile.run_root / profile.database / 'diagnostics/events-1829480-bc23047e96cd45a29feb546b90ce42bb-000.jsonl'
    if event_path != expected_log or profile.database != 'ydental_s10_test_20261017105432_810a7d9c':
        return False
    events = [strict_loads(line) for line in event_raw.splitlines()]
    matches = [row for row in events if row.get('event_id') == stopped['primary_event_id']]
    if len(matches) != 1 or any(matches[0].get(key) != value for key, value in {
            'event': 'renderer.exit', 'pid': 1829480, 'renderer_exit_code': 1,
            'renderer_signal': None, 'outcome': 'NONZERO_NOT_NATIVE', 'actor_id': 59,
            'effective_uid': 59, 'su_flag': False, 'case_id': 'C-ATTACHMENT',
            'run_id': profile.run_id, 'scope_revision': 1}.items()):
        return False
    approval = strict_loads((profile.root / 'runtime-approval.json').read_bytes())
    if (approval.get('allowed_actions') != [] or approval.get('allowed_target_names') != [profile.database]
            or approval.get('authority_sha256') != profile.authority_sha256
            or approval.get('runtime_dispatched') is not True):
        return False
    entries = []
    for name in ('observer', 'wrapper'):
        path, _ = verified_reference(name)
        if approval.get('frozen_files', {}).get(incident[name + '_ref']) != incident[name + '_sha256']:
            return False
        entries.append(path)
    return len(set(entries)) == 2 and Path(sys.argv[0]).resolve() in entries


def require_dispatch_unfrozen(profile=None, *, read_only=False):
    if type(read_only) is not bool:
        raise ValueError('DISPATCH_READ_ONLY_FLAG_INVALID')
    if profile is not None:
        profile.verify()
        if (profile.root / FAILURE_NAME).exists():
            freeze_dispatch(framework_failure_facts(profile.root), profile)
        if ((profile.root / 'HARD-STOP.json').exists() and read_only
                and profile.message_id not in _PROFILE_FAILURES
                and _current_c_renderer_incident_read_only(profile)):
            return
        if (profile.root / 'HARD-STOP.json').exists() or profile.message_id in _PROFILE_FAILURES:
            raise RuntimeError('FRAMEWORK6_DISPATCH_FROZEN')
        return
    if _DISPATCH_FAILURE is None and (EXEC_ROOT / FAILURE_NAME).exists():
        freeze_dispatch(framework_failure_facts(EXEC_ROOT))
    if _DISPATCH_FAILURE is not None:
        raise RuntimeError('APPLICATION_DISPATCH_FROZEN_' + _DISPATCH_FAILURE['reason'])


def bind_dispatch_owner(owner, profile=None):
    global _DISPATCH_OWNER
    require_dispatch_unfrozen(profile)
    if _DISPATCH_OWNER is not None:
        raise RuntimeError('ANOTHER_APPLICATION_DISPATCH_OWNER_ACTIVE')
    _DISPATCH_OWNER = owner


def release_dispatch_owner(owner):
    global _DISPATCH_OWNER
    if _DISPATCH_OWNER is owner:
        _DISPATCH_OWNER = None


class PackageBudget(Budget):
    """R1.2 cumulative resources; both evidence windows plus shared owned files."""
    def __init__(self, directory, *, profile=None, **kwargs):
        if profile is not None:
            kwargs.update(create=False, profile=profile)
        super().__init__(directory, **kwargs)

    def consume(self, kind, *, firefox_purpose=None):
        require_dispatch_unfrozen(self.profile, read_only=kind == 'target_ro')
        if self.profile is not None and kind not in self.profile.local_limits:
            raise RuntimeError('FRAMEWORK6_RESOURCE_NOT_AUTHORIZED')
        if kind in {'accident_ro', 'maintenance', 'create'}:
            raise RuntimeError('R12_NO_PROTECTED_SOURCE_OR_CREATE_DISPATCH')
        if kind in {'http', 'original_get'}:
            if _DISPATCH_OWNER is None:
                raise RuntimeError('NO_ACTIVE_APPLICATION_DISPATCH_GUARD')
            owner_profile = getattr(_DISPATCH_OWNER, 'profile', None)
            if (self.profile is not None and owner_profile != self.profile
                    or self.profile is None and type(owner_profile) is TaskProfile):
                raise RuntimeError('APPLICATION_TASK_PROFILE_MISMATCH')
            _DISPATCH_OWNER.check()
        return super().consume(kind, firefox_purpose=firefox_purpose)

    def check_storage(self):
        if self.profile is not None:
            self.profile.verify()
            current_bytes = sum(p.stat().st_size for p in self.profile.root.rglob('*') if p.is_file() and not p.is_symlink())
            raw_limit = (384 if self.profile.message_id == CURRENT_PLAN else 256) * 1024 ** 2
            maximum = (.9 if self.profile.message_id == CURRENT_PLAN else 1) * raw_limit
            if current_bytes >= maximum:
                raise RuntimeError('FRAMEWORK6_RAW_STORAGE_BOUND')
            if self.profile.message_id == CURRENT_PLAN and current_bytes >= .8 * raw_limit:
                safe_plain(self.profile.root / 'storage-warning.tsv', ['80_PERCENT', current_bytes])
        elif self.path.exists() and time.time() - strict_loads(self.path.read_bytes())['started_epoch'] > 8 * 3600:
            raise RuntimeError('RUN_WINDOW_EXHAUSTED')
        roots = (LEGACY_EXEC_ROOT, EXEC_ROOT, RUN_ROOT)
        if self.profile is not None:
            # The complete retained LC2 package; metadata only, no old contents.
            roots = tuple(ROOT / '.local' / name for name in (
                's10-lc2-safety-triage-20261017-01', 's10-lc2-framework6-20261017-01',
                's10-lc2-r12-20261017', 's10-lc2-caller-adapter-20261017-02',
                's10-lc2-plan-20261017', 's10-lc2-code-rework-20261017-01',
                's10-lc2', 's10-lc2-main-a-20261018-01', 's10-lc2-exec-20261017',
                's10-lc2-main-a-20261018-02', 's10-lc2-main-a-20261018-03',
                's10-lc2-main-a-20261018-04',
            )) + (self.profile.root,)
        roots = tuple(dict.fromkeys(roots))
        size = sum(path.stat().st_size for base in roots if base.exists()
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

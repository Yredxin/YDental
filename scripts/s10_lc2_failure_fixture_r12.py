"""Generate a new offline-only failure-search package for independent review.

The producer knows the synthetic injection. The consumer receives only the
index/manifest, evidence bytes and retrieval contract. No answer key is exported.
No database, Odoo, browser, socket, existing fixture or old evidence is changed.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import logging
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch
import uuid

from s10_lc2_evidence import CORE, save_once
from s10_lc2_supervisor import launch


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_ROOT = ROOT / '.local/s10-lc2-r12-20261017'
SOURCES = ('scripts/s10_lc2_failure_fixture_r12.py', 'ydental_access/diagnostics.py',
           'scripts/s10_lc2_supervisor.py', 'scripts/s10_lc2_evidence.py',
           'scripts/s10_lc2_logging.py')


def _inventory_sources():
    return {name: {'bytes': (ROOT / name).stat().st_size,
                   'sha256': hashlib.sha256((ROOT / name).read_bytes()).hexdigest()} for name in SOURCES}


def _storage_gate():
    roots = (PRIVATE_ROOT, ROOT / '.local/s10-lc2-exec-20261017',
             ROOT / '.local/s10-lc2/20261017-lc2-exec01')
    size = sum(path.stat().st_size for base in roots if base.exists()
               for path in base.rglob('*') if path.is_file() and not path.is_symlink())
    if size >= 1024 ** 3 * .9:
        raise RuntimeError('GLOBAL_RAW_STORAGE_PAUSE_AT_90_PERCENT')


def _first_stage():
    raise LookupError('synthetic-sensitive-origin-never-export-this-text')


def _middle_stage():
    try:
        _first_stage()
    except LookupError:
        raise ValueError('synthetic-sensitive-middle-never-export-this-text')


def _outer_stage():
    try:
        _middle_stage()
    except ValueError as cause:
        raise RuntimeError('synthetic-sensitive-outer-never-export-this-text') from cause


def child(directory, checkpoint_name):
    spec = importlib.util.spec_from_file_location('_lc2_r12_locator_diagnostics', ROOT / 'ydental_access/diagnostics.py')
    diagnostics = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(diagnostics)
    if not diagnostics.configure_once(str(directory)):
        raise RuntimeError('DIAGNOSTICS_CONFIGURATION_FAILED')
    token = diagnostics.bind_context(
        run_id=os.environ['YDENTAL_RUN_ID'], task_id='S10-LOG-AND-CLOSEOUT-v2',
        case_id='L11', attempt=1, trace_id=uuid.uuid4().hex,
        request_id=uuid.uuid4().hex, operation_ref=uuid.uuid4().hex,
        transaction_phase='NO_DATABASE_SYNTHETIC_FIXTURE')
    try:
        checkpoint = directory.parent / checkpoint_name
        if not checkpoint.is_file() or checkpoint.is_symlink():
            raise RuntimeError('FIXTURE_CHECKPOINT_UNAVAILABLE')
        diagnostics.emit_event('fixture.checkpoint', checkpoint_ref=checkpoint_name,
                               outcome='completed', commit_observation='NOT_OBSERVED')
        actual_open = os.open

        def bounded_synthetic_save_fault(path, *args, **kwargs):
            # A real caught OSError at the product's stack-save boundary. This
            # is deliberately injected tool behavior, never a real disk fault.
            if Path(path).name.startswith('stack-'):
                raise OSError('synthetic-secondary-save-fault-never-export-this-text')
            return actual_open(path, *args, **kwargs)

        try:
            _outer_stage()
        except RuntimeError as error:
            with patch.object(diagnostics.os, 'open', side_effect=bounded_synthetic_save_fault):
                diagnostics.record_exception(error, component='offline_fixture', stage='evidence.capture')
        diagnostics.emit_event('fixture.boundary', outcome='stopped', commit_observation='UNKNOWN',
                               transaction_phase='NO_DATABASE_SYNTHETIC_FIXTURE')
    finally:
        diagnostics.reset_context(token)
        # Exercise the same native logging shutdown entry as the application;
        # the diagnostic handler emits one run.end before its segment is sealed.
        logging.shutdown()
    return 1


def build(directory):
    _storage_gate()
    directory = Path(directory)
    if (not directory.is_absolute() or directory.resolve() != directory
            or not directory.is_relative_to(PRIVATE_ROOT) or directory == PRIVATE_ROOT):
        raise ValueError('R12_NEW_PRIVATE_DIRECTORY_REQUIRED')
    directory.mkdir(mode=0o700, parents=False, exist_ok=False)
    events = directory / 'events'
    events.mkdir(mode=0o700)
    checkpoint_name = 'checkpoint-' + uuid.uuid4().hex + '.json'
    save_once(directory / checkpoint_name, {'kind': 'LOCAL_SYNTHETIC_PREPARATION',
        'created_at': datetime.now(timezone.utc).isoformat(), 'prepared': True,
        'database_commit_observation': 'NOT_OBSERVED', 'real_business_commits': 0})
    sources = _inventory_sources()
    head = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
    product = subprocess.check_output(['git', '-C', str(ROOT), 'log', '-1', '--format=%H', '--',
                                       'ydental_access/diagnostics.py'], text=True).strip()
    save_once(directory / 'source-before.json', {'head': head, 'files': sources})
    env = dict(os.environ, PYTHONPATH=str(ROOT / 'scripts'), PYTHONDONTWRITEBYTECODE='1',
               YDENTAL_RUN_ID='lc2-r12-locator-' + uuid.uuid4().hex,
               YDENTAL_TASK_ID='S10-LOG-AND-CLOSEOUT-v2', YDENTAL_PRODUCT_COMMIT=product,
               YDENTAL_TEST_COMMIT=head, YDENTAL_CORE_COMMIT=CORE)
    result = launch([sys.executable, str(Path(__file__).resolve()), 'child',
                     '--directory', str(events), '--checkpoint', checkpoint_name],
                    directory / 'process', timeout=20, attempt=1,
                    last_checkpoint=checkpoint_name, env=env, cwd=ROOT)
    after = _inventory_sources()
    save_once(directory / 'source-after.json', {'files': after, 'source_unchanged': sources == after})
    if sources != after or not result['parent_evidence_complete']:
        raise RuntimeError('FIXTURE_SOURCE_OR_EXIT_EVIDENCE_INCOMPLETE')
    files = []
    for path in sorted(directory.rglob('*')):
        if path.is_file():
            raw = path.read_bytes()
            files.append({'path': str(path.relative_to(directory)), 'bytes': len(raw),
                          'sha256': hashlib.sha256(raw).hexdigest()})
    if sum(item['bytes'] for item in files) > 1024 * 1024:
        raise RuntimeError('SYNTHETIC_PACKAGE_SIZE_EXCEEDED')
    save_once(directory / 'manifest.json', {
        'schema_version': '1.0', 'task_id': 'S10-LOG-AND-CLOSEOUT-v2',
        'evidence_layer': 'OFFLINE_SYNTHETIC_FIXTURE',
        'database_connections': 0, 'odoo_starts': 0, 'real_http': 0, 'browser_starts': 0,
        'real_business_commits': 0, 'files': files,
        'retrieval_contract': 'Read immutable evidence; distinguish local preparation from database commit. No runtime actions.',
    })
    save_once(directory / 'index.json', {
        'manifest': 'manifest.json', 'event_files': [str(path.relative_to(directory))
            for path in sorted(events.glob('events-*.jsonl'))],
        'process_exit': 'process/parent-exit.tsv', 'raw_stdout': 'process/stdout.log',
        'raw_stderr': 'process/stderr-faulthandler.log',
        'evidence_layer': 'OFFLINE_SYNTHETIC_FIXTURE',
        'retrieval_tool': 'scripts/s10_lc2_logging.py',
        'acceptance_contract': 'Locate primary and first visible cause with frame relationships; distinguish secondary evidence failure, last reliable checkpoint, actual process exit and unknown boundary. Report elapsed time and evidence references. No database/network/application actions.',
    })
    _storage_gate()
    return directory / 'index.json'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('build', 'child'))
    parser.add_argument('--directory', required=True)
    parser.add_argument('--checkpoint')
    args = parser.parse_args()
    os.umask(0o077)
    if args.mode == 'child':
        return child(Path(args.directory), args.checkpoint)
    print(build(args.directory))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

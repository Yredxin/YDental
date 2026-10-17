"""Build a synthetic-only independent locator package without Odoo or database use."""
import argparse
import hashlib
import importlib.util
import json
import logging
from pathlib import Path
import sys

from s10_lc2_evidence import save_once
from s10_lc2_supervisor import launch

ROOT = Path(__file__).resolve().parents[1]


def child(directory):
    spec = importlib.util.spec_from_file_location('_lc2_locator_diagnostics', ROOT / 'ydental_access/diagnostics.py')
    diagnostics = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(diagnostics)
    diagnostics.configure_once(str(directory))
    token = diagnostics.bind_context(run_id='synthetic-locator-run', task_id='S10-LOG-AND-CLOSEOUT-v2',
                                     case_id='L11', attempt=1, trace_id='synthetic-locator-trace',
                                     request_id='synthetic-locator-request', component='synthetic_observer')
    try:
        diagnostics.emit_event('run.start', transaction_phase='NO_DATABASE_SYNTHETIC_FIXTURE')
        diagnostics.emit_event('fixture.checkpoint', checkpoint_ref='fixture-ready',
                               commit_observation='NOT_OBSERVED', outcome='completed')
        try:
            raise LookupError('synthetic fixture failure')
        except LookupError as error:
            primary = diagnostics.record_exception(error, component='synthetic_adapter', stage='evidence.capture')
        diagnostics.emit_event('evidence.secondary', component='synthetic_writer', stage='evidence.persist',
                               error_class='EVIDENCE_ERROR', error_code='DIAGNOSTIC_FAILURE',
                               exception_type='OSError', root_event_id=primary,
                               commit_observation='UNKNOWN', severity='ERROR')
        diagnostics.emit_event('run.end', outcome='failed', commit_observation='UNKNOWN')
    finally:
        diagnostics.reset_context(token)
        logging.shutdown()
    return 1


def build(directory):
    directory = Path(directory).resolve()
    directory.mkdir(mode=0o700, parents=True, exist_ok=False)
    events = directory / 'events'
    events.mkdir(mode=0o700)
    result = launch([sys.executable, str(Path(__file__).resolve()), 'child', '--directory', str(events)],
                    directory / 'process', timeout=15, attempt=1, last_checkpoint='fixture-ready')
    manifest = {'task_id': 'S10-LOG-AND-CLOSEOUT-v2', 'case_id': 'L11',
                'evidence_layer': 'SYNTHETIC_FIXTURE', 'database_connections': 0,
                'odoo_starts': 0, 'browser_starts': 0, 'real_business_commits': 0,
                'purpose': 'Independent failure localization using standard entry only',
                'process_result': result,
                'log_query': 'python3 scripts/s10_lc2_logging.py <event files> --case-id L11',
                'files': []}
    for path in sorted(directory.rglob('*')):
        if path.is_file():
            raw = path.read_bytes()
            manifest['files'].append({'path': str(path.relative_to(directory)), 'bytes': len(raw),
                                      'sha256': hashlib.sha256(raw).hexdigest()})
    save_once(directory / 'manifest.json', manifest)
    save_once(directory / 'index.json', {'manifest': 'manifest.json', 'event_files': [
        str(path.relative_to(directory)) for path in sorted(events.glob('events-*.jsonl'))],
        'process_exit': 'process/parent-exit.tsv', 'raw_stdout': 'process/stdout.log',
        'raw_stderr': 'process/stderr-faulthandler.log',
        'evidence_layer': 'SYNTHETIC_FIXTURE',
        'acceptance_task': 'Locate first exception, secondary chain, last reliable step and actual unknown boundary; record elapsed time. No runtime/database actions.'})
    return directory / 'index.json'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['build', 'child'])
    parser.add_argument('--directory', required=True)
    args = parser.parse_args()
    if args.mode == 'child':
        return child(Path(args.directory))
    print(build(args.directory))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

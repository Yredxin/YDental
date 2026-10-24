#!/usr/bin/env python3
"""S12 bindings for the existing owned Odoo foreground supervisor.

Reuse its process ownership, exit receipts, bounded logs, loopback configuration
and live read-only target check. S12 gets a new runtime, scope, admission and run
history. The SAME target retains its existing filestore; it is never copied.
No S11 clock can be enabled through this entry.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
BASE_SOURCE = ROOT / 'scripts/s11/launcher.py'
spec = importlib.util.spec_from_file_location('ydental_s12_supervisor_engine', BASE_SOURCE)
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)

engine.PLAN_ID = 'YD-S12-DOCUMENTS-REPORTS-V1'
engine.EXPECTED_BRANCH = 'codex/s12-documents-reports-r1'
engine.PRIVATE_ROOT = ROOT / '.local/s12'
engine.RUNTIME_CONFIG = engine.PRIVATE_ROOT / 'runtime.json'
engine.ADMISSION = engine.PRIVATE_ROOT / 'admission.json'
engine.RUNS = engine.PRIVATE_ROOT / 'runs'
engine.ACTIVE = engine.PRIVATE_ROOT / 'active.json'
engine.DATA_DIR = ROOT / '.local/s11/new-target-data'
engine.SCRIPT_PATH = Path(__file__).resolve()
engine.DOC_ONLY_CANDIDATE_PATHS = (
    'CURRENT_TASK.md', 'docs/reports/s12/', 'scripts/s12/README.md',
)

_base_validate_pair = engine.validate_pair


def validate_pair():
    runtime, admission, database, branch, candidate = _base_validate_pair()
    if admission.get('base_launcher_sha256') != engine.file_sha256(BASE_SOURCE):
        raise engine.Refusal('S12 admission must bind the exact reused supervisor implementation.')
    if runtime.get('data_dir') != str(engine.DATA_DIR):
        raise engine.Refusal('S12 must preserve the existing target filestore without copying it.')
    if (ROOT / '.local/s11/new-target-active.json').exists():
        raise engine.Refusal('The same target has an S11 owner record; preserve and resolve it before S12.')
    return runtime, admission, database, branch, candidate


def no_legacy_clock(_branch, _candidate, gdb_capture):
    if any(name.startswith('YDENTAL_S11_CLOCK_') for name in os.environ):
        raise engine.Refusal('S12 does not enable the S11 synthetic session clock.')
    return None


engine.validate_pair = validate_pair
engine.validate_s11_clock_debug = no_legacy_clock


def __getattr__(name):
    """Expose the verified existing helpers to the bounded S12 tools."""
    return getattr(engine, name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('start', 'status', 'stop'))
    parser.add_argument('--gdb', action='store_true', help='explicit optional native-crash capture')
    args = parser.parse_args()
    try:
        if args.command == 'start':
            return engine.start_service(gdb_capture=args.gdb, s11_clock=False)
        if args.gdb:
            raise engine.Refusal('--gdb is valid only with start.')
        return engine.status_service() if args.command == 'status' else engine.stop_service()
    except engine.Refusal as error:
        print(f'S12 launcher refused: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

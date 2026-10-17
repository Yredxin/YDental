"""One candidate's pure rework checks, with external dispatch actively forbidden."""
import argparse
import builtins
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
import importlib.abc
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
BLOCKED_IMPORTS = {'odoo', 'psycopg', 'psycopg2', 'playwright', 'requests', 'selenium', 'lxml'}
PROTECTED = [ROOT / '.local' / name for name in (
    's10-lc2-exec-20261017', 's10-lc2-r12-20261017', 's10-lc2')]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output')
    parser.add_argument('--product-commit', required=True)
    parser.add_argument('--test-commit', required=True)
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    sources = sorted([*ROOT.glob('scripts/s10_lc2*.py'), ROOT / 'ydental_access/diagnostics.py',
                      ROOT / 'ydental_settlement_test/tests/test_log_closeout.py',
                      *ROOT.glob('ydental_settlement/models/*.py')])

    def manifest():
        return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}

    def save(name, value):
        raw = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()
        with os.fdopen(os.open(output / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'wb') as stream:
            stream.write(raw)

    before = manifest()
    save('source-before.json', before)
    attempts = []

    def deny(label):
        def blocked(*a, **kw):
            attempts.append(label)
            raise RuntimeError('PURE_REWORK_FORBIDDEN_' + label)
        return blocked

    class Imports(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path=None, target=None):
            if fullname.split('.')[0] in BLOCKED_IMPORTS:
                attempts.append('import:' + fullname)
                raise ImportError('PURE_REWORK_FORBIDDEN_IMPORT')

    def confined_opener(original):
        def open_allowed(file, *a, **kw):
            if isinstance(file, (str, bytes, os.PathLike)):
                path = Path(os.fsdecode(file)).resolve()
                if any(path.is_relative_to(base) for base in PROTECTED):
                    attempts.append('protected_material_access')
                    raise RuntimeError('PURE_REWORK_PROTECTED_MATERIAL_ACCESS')
            return original(file, *a, **kw)
        return open_allowed

    started = datetime.now(timezone.utc).isoformat()
    finder = Imports()
    sys.meta_path.insert(0, finder)
    try:
        with ExitStack() as scope:
            for owner, name in ((subprocess, 'Popen'), (subprocess, 'run'),
                                (socket, 'create_connection'), (socket.socket, 'connect'),
                                (socket.socket, 'connect_ex'), (socket.socket, 'bind')):
                scope.enter_context(patch.object(owner, name, deny(name)))
            for owner, name in ((builtins, 'open'), (io, 'open'), (os, 'open')):
                scope.enter_context(patch.object(owner, name, confined_opener(getattr(owner, name))))
            # Parent sticky-state checks must never inspect the real stopped run.
            import s10_lc2_targets
            synthetic_shared = output / 'synthetic-shared-state'
            synthetic_shared.mkdir(mode=0o700)
            scope.enter_context(patch.object(s10_lc2_targets, 'EXEC_ROOT', synthetic_shared))
            suite = unittest.TestSuite()
            for module in ('s10_lc2_test_process_guard', 's10_lc2_test_browser',
                           's10_lc2_test_http', 's10_lc2_test_renderer',
                           's10_lc2_test_framework_caller'):
                suite.addTests(unittest.defaultTestLoader.loadTestsFromName(module))
            # No preflight subprocess, signal injection, accounts, cases import,
            # real framework, or broad discovery of unrelated application tests.
            from s10_lc2_test_launch import LaunchCase
            from s10_lc2_test_tools import DiagnosticsCase, RendererSchemaCase, ToolCase
            for name in unittest.defaultTestLoader.getTestCaseNames(LaunchCase):
                if name != 'test_actual_child_metadata_and_import_under_exact_application_environment':
                    suite.addTest(LaunchCase(name))
            for name in unittest.defaultTestLoader.getTestCaseNames(DiagnosticsCase):
                if name != 'test_real_emit_and_explicit_shutdown_have_bounded_join':
                    suite.addTest(DiagnosticsCase(name))
            suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(RendererSchemaCase))
            for name in ('test_valid_query_and_unknown_is_not_commit',
                         'test_bad_lines_cannot_hide_good_or_mark_run_valid',
                         'test_sequence_and_event_replay_detected',
                         'test_missing_end_and_empty_never_valid',
                         'test_process_end_does_not_hide_same_run_other_pid_gap',
                         'test_primary_secondary_and_checkpoint_independent'):
                suite.addTest(ToolCase(name))
            selected = []

            def collect(node):
                if isinstance(node, unittest.TestSuite):
                    for child in node:
                        collect(child)
                else:
                    selected.append(node.id())

            collect(suite)
            save('selected-tests.json', selected)
            with os.fdopen(os.open(output / 'unittest.txt', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as stream:
                result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    finally:
        sys.meta_path.remove(finder)
    after = manifest()
    save('source-after.json', after)
    record = {'scope': 'SOURCE_AND_PURE_OFFLINE_ONLY', 'execution_role': 'CONTROLLER_REWORK_SELF_TEST',
              'product_commit': args.product_commit, 'test_commit': args.test_commit,
              'started_at_utc': started, 'finished_at_utc': datetime.now(timezone.utc).isoformat(),
              'pid': os.getpid(), 'tests': result.testsRun, 'failures': len(result.failures),
              'errors': len(result.errors), 'skips': len(result.skipped), 'forbidden_attempts': attempts,
              'source_before_after_equal': before == after, 'source_files': len(before),
              'cases_module_imported': 's10_lc2_cases' in sys.modules,
              'odoo_imported': any(name == 'odoo' or name.startswith('odoo.') for name in sys.modules),
              'independent_tester_or_application_pass_claimed': False}
    save('result.json', record)
    print(json.dumps(record))
    return 0 if (result.wasSuccessful() and not result.skipped and not attempts
                 and before == after and not record['cases_module_imported'] and not record['odoo_imported']) else 1


if __name__ == '__main__':
    raise SystemExit(main())

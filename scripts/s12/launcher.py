#!/usr/bin/env python3
"""S12 bindings for the existing owned Odoo foreground supervisor.

Reuse its process ownership, exit receipts, bounded logs, loopback configuration
and live read-only target check. S12 gets a new runtime, scope, admission and run
history. The SAME target retains its existing filestore; it is never copied.
No S11 clock can be enabled through this entry.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from email.parser import Parser
import hashlib
import importlib.util
import os
from pathlib import Path
import stat
import subprocess
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
PDF_DIRECTORY = ROOT / '.local/s12/pdf-deps'
PDF_DISTRIBUTION = 'rl-renderPM'
PDF_VERSION = '4.0.3'
PDF_FILES = frozenset((
    '_rl_renderPM.cpython-312-x86_64-linux-gnu.so',
    'rl_renderPM.libs/libbz2-a273e504.so.1.0.6',
    'rl_renderPM.libs/libpng15-ce838cd1.so.15.13.0',
    'rl_renderPM.libs/libfreetype-c0e61f0c.so.6.14.0',
    'rl_renderPM-4.0.3.dist-info/REQUESTED',
    'rl_renderPM-4.0.3.dist-info/INSTALLER',
    'rl_renderPM-4.0.3.dist-info/RECORD',
    'rl_renderPM-4.0.3.dist-info/top_level.txt',
    'rl_renderPM-4.0.3.dist-info/METADATA',
    'rl_renderPM-4.0.3.dist-info/WHEEL',
))


def _owned_regular(path):
    try:
        info = path.lstat()
    except OSError as error:
        raise engine.Refusal('A bound S12 runtime environment file is unavailable.') from error
    if not stat.S_ISREG(info.st_mode) or path.is_symlink() or info.st_uid != os.getuid():
        raise engine.Refusal('S12 runtime files must be owned regular files without symlinks.')


def runtime_child_environment(runtime, parent_environment=None):
    """Validate only the explicit S12 font and one project wheel; return env.

    No DB, package installation or code import from the extra path occurs here.
    The inherited environment stays intact except the two bound child variables.
    T07 observation flags are never enabled by this helper.
    """
    font = runtime.get('fontconfig') or {}
    expected_font = ROOT / 'ydental_settlement/static/fonts/NotoSansCJKsc-Regular.otf'
    expected_config = ROOT / '.local/s12/fontconfig/fonts.conf'
    if (font.get('family') != 'Noto Sans CJK SC' or font.get('font_file') != str(expected_font)
            or font.get('fontconfig_file') != str(expected_config)):
        raise engine.Refusal('The actual S12 Chinese font/configuration paths must be explicitly bound.')
    for path, field in ((expected_font, 'font_sha256'), (expected_config, 'fontconfig_sha256')):
        _owned_regular(path)
        if engine.file_sha256(path) != font.get(field):
            raise engine.Refusal('The bound S12 font/configuration SHA does not match its actual bytes.')
    extension = runtime.get('pdf_python') or {}
    files = extension.get('files')
    if (extension.get('directory') != str(PDF_DIRECTORY)
            or extension.get('distribution') != PDF_DISTRIBUTION
            or extension.get('version') != PDF_VERSION or not isinstance(files, dict)
            or set(files) != PDF_FILES):
        raise engine.Refusal('Bind only the exact S12 private rl-renderPM 4.0.3 wheel file manifest.')
    try:
        directory_info = PDF_DIRECTORY.lstat()
    except OSError as error:
        raise engine.Refusal('The explicit S12 private PDF dependency directory is unavailable.') from error
    private_info = engine.PRIVATE_ROOT.lstat()
    if (not stat.S_ISDIR(private_info.st_mode) or engine.PRIVATE_ROOT.is_symlink()
            or private_info.st_uid != os.getuid() or stat.S_IMODE(private_info.st_mode) != 0o700
            or not stat.S_ISDIR(directory_info.st_mode) or PDF_DIRECTORY.is_symlink()
            or directory_info.st_uid != os.getuid()):
        raise engine.Refusal('The S12 PDF dependency must remain below the owned private project root.')
    actual_files = set()
    for path in PDF_DIRECTORY.rglob('*'):
        info = path.lstat()
        if path.is_symlink() or info.st_uid != os.getuid():
            raise engine.Refusal('The S12 PDF wheel contains an unsafe filesystem entry.')
        if stat.S_ISREG(info.st_mode):
            relative = path.relative_to(PDF_DIRECTORY).as_posix()
            # uv's existing empty installer lock is not importable payload.
            if relative == '.lock' and info.st_size == 0:
                continue
            actual_files.add(relative)
        elif not stat.S_ISDIR(info.st_mode):
            raise engine.Refusal('The S12 PDF wheel contains an unsupported filesystem entry.')
    if actual_files != PDF_FILES:
        raise engine.Refusal('The S12 PDF dependency directory differs from the exact wheel manifest.')
    for relative, expected_sha in files.items():
        path = PDF_DIRECTORY / relative
        _owned_regular(path)
        if engine.file_sha256(path) != expected_sha:
            raise engine.Refusal('A bound S12 PDF wheel file SHA does not match its actual bytes.')
    metadata = Parser().parsestr((PDF_DIRECTORY / 'rl_renderPM-4.0.3.dist-info/METADATA').read_text())
    if metadata.get('Name') != PDF_DISTRIBUTION or metadata.get('Version') != PDF_VERSION:
        raise engine.Refusal('The installed S12 PDF native distribution name/version differs.')
    environment = dict(os.environ if parent_environment is None else parent_environment)
    inherited_path = environment.get('PYTHONPATH', '')
    # Preserve inherited entries and their order. Only this admitted extra
    # wheel directory is prepended; existing copies of it need not be repeated.
    inherited_entries = [entry for entry in inherited_path.split(os.pathsep) if entry != str(PDF_DIRECTORY)] if inherited_path else []
    environment['PYTHONPATH'] = os.pathsep.join([str(PDF_DIRECTORY), *inherited_entries])
    environment['FONTCONFIG_FILE'] = str(expected_config)
    try:
        matched = subprocess.run(['fc-match', '-f', '%{family}\n%{file}', 'Noto Sans CJK SC'],
            env=environment, capture_output=True, text=True, timeout=5, check=True)
    except (OSError, subprocess.SubprocessError) as error:
        raise engine.Refusal('The explicit S12 child environment cannot resolve the verified font.') from error
    observed = matched.stdout.splitlines()
    if len(observed) != 2 or 'Noto Sans CJK SC' not in observed[0] or observed[1] != str(expected_font):
        raise engine.Refusal('The S12 child font lookup does not resolve the bound actual font file.')
    proof = {'font_family_observed': observed[0], 'font_file': str(expected_font),
        'font_sha256': font['font_sha256'], 'fontconfig_file': str(expected_config),
        'fontconfig_sha256': font['fontconfig_sha256'], 'pdf_python': extension,
        'inherited_pythonpath_preserved': True,
        'inherited_pythonpath_sha256': hashlib.sha256(inherited_path.encode()).hexdigest(),
        'child_pythonpath_sha256': hashlib.sha256(environment['PYTHONPATH'].encode()).hexdigest(),
        't07_flags_automatically_enabled': False}
    return environment, proof


@contextmanager
def _child_environment(environment):
    """Set only this launcher process's child inheritance, then restore it."""
    keys = ('FONTCONFIG_FILE', 'PYTHONPATH')
    prior = {key: os.environ.get(key) for key in keys}
    try:
        os.environ.update({key: environment[key] for key in keys})
        yield
    finally:
        for key, value in prior.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


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
            runtime, _admission, _database, _branch, _candidate = validate_pair()
            environment, _proof = runtime_child_environment(runtime)
            with _child_environment(environment):
                return engine.start_service(gdb_capture=args.gdb, s11_clock=False)
        if args.gdb:
            raise engine.Refusal('--gdb is valid only with start.')
        return engine.status_service() if args.command == 'status' else engine.stop_service()
    except engine.Refusal as error:
        print(f'S12 launcher refused: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

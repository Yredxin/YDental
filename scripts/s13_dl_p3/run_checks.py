#!/usr/bin/env python3
"""One explicitly frozen S13 native module upgrade or affected test run.

Requires the actual complete immediate pre snapshot. It never creates a DB,
cleans business data, retries an operation or kills a timed-out child. Unknown
outcomes retain the exact child identity and require readback before any replay.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess

from admission_probe import PRIVATE, ROOT, TARGET, git, write_receipt
import launcher
from protected_snapshot import ALLOWED_MODULES, private_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=('upgrade', 'suite'), required=True)
    parser.add_argument('--candidate', required=True)
    parser.add_argument('--modules', required=True)
    parser.add_argument('--install', default='')
    parser.add_argument('--freeze', type=Path, required=True)
    parser.add_argument('--pre', type=Path, required=True)
    parser.add_argument('--label', required=True)
    args = parser.parse_args()
    if not re.fullmatch('[A-Za-z0-9_-]{1,60}', args.label):
        raise RuntimeError('Use a bounded explicit run label.')
    modules = set(args.modules.split(','))
    installs = set(args.install.split(',')) if args.install else set()
    if not modules or not modules <= ALLOWED_MODULES or not installs <= modules:
        raise RuntimeError('Only explicit affected S13 modules and a subset to install are supported.')
    runtime, admission, database, branch, candidate = launcher.validate_pair()
    if args.candidate != candidate or candidate != git('rev-parse', 'HEAD'):
        raise RuntimeError('Freeze, runtime and actual clean candidate must agree.')
    freeze = private_json(args.freeze.resolve())
    pre = private_json(args.pre.resolve())
    if (freeze.get('writers_quiescent') is not True or freeze.get('candidate_commit') != candidate
            or freeze.get('database') != TARGET or freeze.get('database_oid') != 2171423
            or set(freeze.get('modules', [])) != modules):
        raise RuntimeError('The actual explicit freeze does not match this execution.')
    if (pre.get('status') != 'READONLY_PROTECTED_UPGRADE_SNAPSHOT_COMPLETE' or pre.get('phase') != 'pre'
            or pre.get('candidate_commit') != candidate or pre.get('database') != TARGET
            or pre.get('database_oid') != 2171423 or pre.get('cluster') != launcher.EXPECTED_CLUSTER
            or set(pre.get('modules', [])) != modules
            or pre.get('freeze_receipt_sha256') != launcher.file_sha256(args.freeze)
            or pre.get('rollback_idle') is not True or pre.get('connection_closed') is not True
            or not pre.get('business') or not pre.get('technical_metadata') or 'attachments' not in pre
            or not {'ir_act_report_xml', 'report_paperformat', 'ir_act_url', 'res_lang'} <= set(pre['technical_metadata'])):
        raise RuntimeError('A complete matching immediate pre snapshot is required; no upgrade is authorized.')
    if not pre.get('committed_business_anchors_verified'):
        raise RuntimeError('The protected committed source anchors were not verified.')
    if (PRIVATE / 'active.json').exists() or (ROOT / '.local/s11/new-target-active.json').exists() or (ROOT / '.local/s12/active.json').exists() or (ROOT / '.local/s13/active.json').exists() or (ROOT / '.local/dl-p1/active.json', '.local/dl-p2/active.json').exists():
        raise RuntimeError('The shared target still has an active owner record.')
    for port in (18411, 18412):
        with socket.socket() as sock:
            sock.settimeout(.5)
            if sock.connect_ex(('127.0.0.1', port)) == 0:
                raise RuntimeError('A shared test port is occupied; coordinate the owner before execution.')
    launcher.validate_live_database(database, admission)
    child_environment, environment_proof = launcher.runtime_child_environment(runtime)
    font = runtime['fontconfig']
    directory = PRIVATE / 'checks' / (args.label + '-' + args.phase)
    directory.mkdir(mode=0o700, parents=True)
    os.chmod(directory.parent, 0o700)
    config = launcher.render_odoo_config(database, directory)
    command = [str(launcher.PYTHON), str(launcher.ODOO_BIN), '-c', str(config),
               '--stop-after-init', '--without-demo=all']
    if args.phase == 'upgrade':
        command += ['--no-http']
        if modules - installs:
            command += ['-u', ','.join(sorted(modules - installs))]
        if installs:
            command += ['-i', ','.join(sorted(installs))]
    else:
        if installs or 'ydental_s12_test' not in modules:
            raise RuntimeError('Tests require an already installed S13 test addon; never combine installation and test evidence.')
        command += ['-u', 'ydental_s12_test', '--test-enable', '--test-tags', '/ydental_s12_test']
    operation = {'plan_id': launcher.PLAN_ID, 'candidate': candidate, 'branch': branch,
        'core': launcher.EXPECTED_CORE_COMMIT, 'database': TARGET, 'oid': 2171423,
        'cluster': launcher.EXPECTED_CLUSTER, 'phase': args.phase, 'modules': sorted(modules),
        'install_modules': sorted(installs), 'command': command,
        'started_at_utc': dt.datetime.now(dt.UTC).isoformat(),
        'pre_sha256': launcher.file_sha256(args.pre), 'freeze_sha256': launcher.file_sha256(args.freeze),
        'tool_sha256': launcher.file_sha256(Path(__file__)),
        'fontconfig_sha256': font['fontconfig_sha256'], 'font_sha256': font['font_sha256'],
        'font_family_observed': environment_proof['font_family_observed'],
        'runtime_environment': environment_proof,
        'test_tag': '/ydental_s12_test' if args.phase == 'suite' else None,
        'test_transactions_are_not_durable_business_evidence': args.phase == 'suite',
        'no_automatic_retry': True, 'timeout_child_preserved': True}
    write_receipt(directory / 'operation.json', operation)
    timeout = 1200 if args.phase == 'suite' else 300
    logfile = directory / 'odoo.log'
    with logfile.open('xb') as stream:
        os.chmod(logfile, 0o600)
        child = subprocess.Popen(command, cwd=ROOT, env=child_environment, stdin=subprocess.DEVNULL,
            stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
        write_receipt(directory / 'child.json', {'pid': child.pid, 'start_ticks': launcher.proc_start_ticks(child.pid),
                                               'owner': os.geteuid()})
        try:
            exit_code = child.wait(timeout=timeout)
            outcome = 'EXITED_REQUIRES_INDEPENDENT_POST_READBACK'
        except subprocess.TimeoutExpired:
            exit_code, outcome = None, 'TIMEOUT_CHILD_PRESERVED_UNKNOWN_NO_REPLAY'
        stream.flush()
        os.fsync(stream.fileno())
    if exit_code is not None:
        config.unlink()
    raw = logfile.read_bytes()
    lines = raw.decode(errors='replace').splitlines()
    result = dict(operation, finished_at_utc=dt.datetime.now(dt.UTC).isoformat(), exit_code=exit_code,
        outcome=outcome, log_sha256=hashlib.sha256(raw).hexdigest(), log_bytes=len(raw),
        error_line_count=sum(' ERROR ' in line or ' CRITICAL ' in line for line in lines),
        native_signal=exit_code in (-11, 139) or any('Segmentation fault' in line for line in lines),
        official_summary_lines=[line for line in lines if 'failed, ' in line or 'post-tests in' in line],
        temporary_secret_config_removed=exit_code is not None)
    digest = write_receipt(directory / 'result.json', result)
    print(json.dumps({'outcome': outcome, 'exit_code': exit_code,
        'error_line_count': result['error_line_count'], 'native_signal': result['native_signal'],
        'result': str((directory / 'result.json').relative_to(ROOT)), 'sha256': digest,
        'official_summary_lines': result['official_summary_lines']}))
    return 0 if exit_code == 0 and not result['error_line_count'] else 2


if __name__ == '__main__':
    raise SystemExit(main())

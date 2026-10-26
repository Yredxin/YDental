#!/usr/bin/env python3
"""Run one bounded P9 browser client and retain exact executed sources and exit.

No service is started, no account is created and no retry occurs. The child
checks the normal stage-owned service before authentication. Raw evidence stays
in the ignored stage directory and excludes credential/request body values.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
PRIVATE = ROOT / '.local/dl-p9'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', required=True)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--engine', choices=('chromium', 'webkit'), required=True)
    parser.add_argument('--stage', choices=('before', 'after'), required=True)
    parser.add_argument('--mode', choices=('narrow', 'busy', 'others-bypass', 'before', 'main', 'zoom', 'nojs', 'fixtures', 'bypass', 'files', 'permissions', 'spacing', 'stress'), default='main')
    parser.add_argument('--sample-file', default='.local/dl-p9/testing/sample.json')
    parser.add_argument('--timeout', type=int, default=600)
    parser.add_argument('--fixture-file')
    parser.add_argument('--before-result')
    parser.add_argument('--role', default='doctor')
    args = parser.parse_args()
    assert re.fullmatch(r'[A-Za-z0-9_-]{1,60}', args.label)
    assert 0 < args.timeout <= 1200
    out = PRIVATE / 'testing' / 'evidence' / ('process-' + args.label)
    out.mkdir(mode=0o700, parents=True)
    source = Path(__file__).with_suffix('.cjs')
    node = ROOT / '.local/s11/operations/clock-operator-users-ui-c981cd0-attempt15-runtime-snapshot/playwright/driver/node'
    command = [str(node), str(source)]
    for name in ('label', 'run_id', 'engine', 'stage', 'mode', 'sample_file', 'role'):
        command.extend(['--' + name.replace('_', '-'), getattr(args, name)])

    def save(name, value):
        raw = json.dumps(value, indent=2).encode()
        fd = os.open(out / name, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw)
        return hashlib.sha256(raw).hexdigest()

    if args.before_result:
        command.extend(['--before-result', args.before_result])
    if args.fixture_file:
        command.extend(['--fixture-file', args.fixture_file])
    dependencies = [Path(__file__), source,
                    ROOT / 'scripts/s13/browser_client.py', ROOT / 'scripts/s13_dl_p9/http_client.py', ROOT / 'scripts/s13_dl_p9/admission_probe.py', ROOT / 'scripts/s13_dl_p9/launcher.py',
                    ROOT / '.local/dl-p3/tools/webkit_finite_zoom_bridge.cjs',
                    ROOT / '.local/dl-p3/verification/webkit_plugins_environment.cjs']
    for index, item in enumerate(dependencies):
        destination = out / ('executed-%s-%s' % (index, item.name))
        destination.write_bytes(item.read_bytes())
        destination.chmod(0o400)
    with (out / 'native.log').open('xb') as log:
        os.chmod(log.name, 0o600)
        child = subprocess.Popen(command, cwd=ROOT, stdout=log,
                                 stderr=subprocess.STDOUT, start_new_session=True)
        facts = {'candidate': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                 'command': command, 'parent_pid': os.getpid(), 'child_pid': child.pid,
                 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                 'started_at_utc': dt.datetime.now(dt.UTC).isoformat(), 'automatic_retry': False}
        save('start.json', facts)
        try:
            code = child.wait(timeout=args.timeout)
            facts.update(outcome='EXITED', actual_child_returncode=code,
                         signal_number=-code if code < 0 else None)
        except subprocess.TimeoutExpired:
            code = None
            facts.update(outcome='TIMEOUT_CHILD_PRESERVED_UNKNOWN_NO_REPLAY',
                         actual_child_returncode=None, signal_number=None)
    facts.update(finished_at_utc=dt.datetime.now(dt.UTC).isoformat(),
                 log_sha256=hashlib.sha256((out / 'native.log').read_bytes()).hexdigest())
    digest = save('result.json', facts)
    print(json.dumps({'outcome': facts['outcome'], 'actual_child_returncode': code,
                      'signal_number': facts['signal_number'], 'receipt_sha256': digest,
                      'result': str((out / 'result.json').relative_to(ROOT))}))
    return 0 if code == 0 else 2


if __name__ == '__main__':
    raise SystemExit(main())

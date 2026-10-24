#!/usr/bin/env python3
"""Prepare S12 project resource records from the authorized DB provider.

No DB connection, admission, service or business action is performed. A scope
is a scheduling record, not an assertion that platform permissions are granted.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import uuid

from admission_probe import BRANCH, CORE, OID, PLAN, PRIVATE, ROOT, TARGET, git, read_provider, write_receipt

RUNTIME = PRIVATE / 'runtime.json'
ANCHOR = 'e100e098dea5b919f3c9ca09454d239189e69ad1'


def check_candidate(candidate):
    if candidate != git('rev-parse', 'HEAD') or git('branch', '--show-current') != BRANCH:
        raise RuntimeError('Candidate must be the current full S12 HEAD.')
    if git('-C', str(ROOT.parent), 'rev-parse', 'HEAD') != CORE:
        raise RuntimeError('The locked Odoo core changed.')
    git('merge-base', '--is-ancestor', ANCHOR, candidate)


def create(candidate, hours, operator):
    check_candidate(candidate)
    if not 0 < hours <= 24:
        raise RuntimeError('The project resource scope must be within 24 hours.')
    database = read_provider(ROOT / '.local/s11/new-target-runtime.json')
    now = dt.datetime.now(dt.UTC)
    value = {'plan_id': PLAN, 'branch': BRANCH, 'candidate_commit': candidate, 'core_commit': CORE,
             'database': database, 'data_dir': str(ROOT / '.local/s11/new-target-data'),
             'scope': {'plan_id': PLAN, 'id': 's12-' + now.strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:12],
                       'issued_at_utc': now.isoformat(), 'expires_at_utc': (now + dt.timedelta(hours=hours)).isoformat(),
                       'issued_by': operator, 'purpose': 'S12 authorized synthetic software implementation and verification',
                       'platform_permission_claimed': False},
             'application': {'host': '127.0.0.1', 'port': 18411, 'workers': 0, 'max_cron_threads': 0,
                             'db_maxconn': 16, 'dbfilter': '^' + TARGET + '$', 'list_db': False}}
    digest = write_receipt(RUNTIME, value)
    print(json.dumps({'status': 'S12_PROJECT_RUNTIME_CREATED_NOT_ADMITTED',
                      'output': str(RUNTIME.relative_to(ROOT)), 'candidate': candidate,
                      'scope_id': value['scope']['id'], 'expires_at_utc': value['scope']['expires_at_utc'],
                      'runtime_sha256': digest, 'database_oid': OID, 'database_write_performed': False}))


def rebind(candidate, operator):
    check_candidate(candidate)
    read_provider(RUNTIME)
    raw = RUNTIME.read_bytes()
    value = json.loads(raw)
    if (value.get('plan_id') != PLAN or value.get('branch') != BRANCH or
            value.get('scope', {}).get('plan_id') != PLAN):
        raise RuntimeError('Only an existing actual S12 resource scope can be rebound.')
    now = dt.datetime.now(dt.UTC)
    expiry = dt.datetime.fromisoformat(value['scope']['expires_at_utc'])
    if now >= expiry:
        raise RuntimeError('An expired project scope cannot be rebound or silently extended.')
    if (PRIVATE / 'active.json').exists():
        raise RuntimeError('Stop the exact owned service before candidate rebinding.')
    value['candidate_commit'] = candidate
    value['candidate_rebound_by'] = operator
    value['candidate_rebound_at_utc'] = now.isoformat()
    archive = PRIVATE / 'runtime-history' / ('runtime-before-' + now.strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8] + '.json')
    archive.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(archive, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    temporary = PRIVATE / ('runtime-next-' + uuid.uuid4().hex + '.json')
    digest = write_receipt(temporary, value)
    os.replace(temporary, RUNTIME)
    print(json.dumps({'status': 'S12_CANDIDATE_REBOUND_NOT_ADMITTED', 'candidate': candidate,
                      'scope_id': value['scope']['id'], 'scope_expiry_unchanged': value['scope']['expires_at_utc'],
                      'runtime_sha256': digest, 'prior_bytes_archive': str(archive.relative_to(ROOT)),
                      'prior_bytes_sha256': hashlib.sha256(raw).hexdigest(), 'database_write_performed': False}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('create', 'rebind'))
    parser.add_argument('--candidate', required=True)
    parser.add_argument('--operator', required=True)
    parser.add_argument('--hours', type=float, default=8)
    args = parser.parse_args()
    create(args.candidate, args.hours, args.operator) if args.command == 'create' else rebind(args.candidate, args.operator)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

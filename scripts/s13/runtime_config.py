#!/usr/bin/env python3
"""Create or rebind S13 resource metadata for the same existing synthetic target.

No DB connection, service start or admission is performed. Stage expiry is new;
older runtime/scope records are never modified. Existing PDF dependency metadata
is validated against its actual files before it is copied into the new record.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import stat
import uuid

from admission_probe import BRANCH, CORE, OID, PLAN, PRIVATE, ROOT, TARGET, git, read_provider, write_receipt
import launcher

RUNTIME = PRIVATE / 'runtime.json'
ANCHOR = 'a437464351220605bf14b8f50181132266272d65'


def check_candidate(candidate):
    if candidate != git('rev-parse', 'HEAD') or git('branch', '--show-current') != BRANCH:
        raise RuntimeError('Candidate must equal the full current S13 HEAD.')
    if git('-C', str(ROOT.parent), 'rev-parse', 'HEAD') != CORE:
        raise RuntimeError('Locked core mismatch.')
    git('merge-base', '--is-ancestor', ANCHOR, candidate)


def read_private(path):
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or path.is_symlink() or info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != 0o600:
        raise RuntimeError('The explicit provider must be private, owned and regular.')
    return json.loads(path.read_text())


def create(candidate, hours, operator):
    check_candidate(candidate)
    if not 0 < hours <= 24:
        raise RuntimeError('Use a new project resource duration within 24 hours.')
    database = read_provider(ROOT / '.local/s11/new-target-runtime.json')
    prior = read_private(ROOT / '.local/s12/runtime.json')
    PRIVATE.mkdir(mode=0o700, exist_ok=True)
    launcher.runtime_child_environment(prior)
    now = dt.datetime.now(dt.UTC)
    value = {'plan_id': PLAN, 'branch': BRANCH, 'candidate_commit': candidate, 'core_commit': CORE,
             'database': database, 'data_dir': str(ROOT / '.local/s11/new-target-data'),
             'fontconfig': prior['fontconfig'], 'pdf_python': prior['pdf_python'],
             'scope': {'plan_id': PLAN, 'id': 's13-ux-' + now.strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:12],
                       'issued_at_utc': now.isoformat(), 'expires_at_utc': (now + dt.timedelta(hours=hours)).isoformat(),
                       'issued_by': operator, 'purpose': 'Authorized S13 UX documents limited synthetic software implementation and verification',
                       'platform_permission_claimed': False},
             'application': {'host': '127.0.0.1', 'port': 18411, 'workers': 0, 'max_cron_threads': 0,
                             'db_maxconn': 16, 'dbfilter': '^' + TARGET + '$', 'list_db': False}}
    digest = write_receipt(RUNTIME, value)
    print(json.dumps({'status':'S13_RESOURCE_CREATED_NOT_ADMITTED','candidate':candidate,
                      'runtime_sha256':digest,'scope_id':value['scope']['id'],'expires_at_utc':value['scope']['expires_at_utc'],
                      'old_scope_modified':False,'database_write_performed':False}))


def rebind(candidate, operator):
    check_candidate(candidate)
    read_provider(RUNTIME)
    raw=RUNTIME.read_bytes();value=json.loads(raw)
    if value.get('plan_id') != PLAN or value.get('branch') != BRANCH or value.get('scope',{}).get('plan_id') != PLAN:
        raise RuntimeError('Only the existing S13 resource record may be rebound.')
    now=dt.datetime.now(dt.UTC)
    if now >= dt.datetime.fromisoformat(value['scope']['expires_at_utc']):
        raise RuntimeError('An expired scope cannot be silently rebound or extended.')
    if any(path.exists() for path in (PRIVATE/'active.json',ROOT/'.local/s12/active.json',ROOT/'.local/s11/new-target-active.json')):
        raise RuntimeError('Resolve the exact existing service lifecycle before rebinding.')
    value.update(candidate_commit=candidate,candidate_rebound_by=operator,candidate_rebound_at_utc=now.isoformat())
    archive=PRIVATE/'runtime-history'/('runtime-before-'+now.strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]+'.json')
    archive.parent.mkdir(mode=0o700,exist_ok=True)
    fd=os.open(archive,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'wb') as stream:
        stream.write(raw);stream.flush();os.fsync(stream.fileno())
    temporary=PRIVATE/('runtime-next-'+uuid.uuid4().hex+'.json')
    digest=write_receipt(temporary,value);os.replace(temporary,RUNTIME)
    print(json.dumps({'status':'S13_CANDIDATE_REBOUND_NOT_ADMITTED','candidate':candidate,'runtime_sha256':digest,
                      'scope_expiry_unchanged':value['scope']['expires_at_utc'],'prior_bytes_sha256':hashlib.sha256(raw).hexdigest(),
                      'prior_archive':str(archive.relative_to(ROOT)),'database_write_performed':False}))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('create','rebind'));parser.add_argument('--candidate',required=True)
    parser.add_argument('--operator',required=True);parser.add_argument('--hours',type=float,default=8)
    args=parser.parse_args()
    create(args.candidate,args.hours,args.operator) if args.command=='create' else rebind(args.candidate,args.operator)


if __name__=='__main__':
    main()

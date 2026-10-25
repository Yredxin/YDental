"""Small normal-login client for the single owned S13 loopback service.

Never records passwords, cookies, CSRF values, connection/editor tokens or full
request bodies. It performs no automatic retries, including after a timeout.
"""

from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path
import stat
import subprocess
import time
from urllib.parse import urlsplit

from lxml import html
import requests

from admission_probe import PLAN, PRIVATE, ROOT, TARGET, git, write_receipt
import launcher

BASE = 'http://127.0.0.1:18411'
ROLE_PROVIDER = ROOT / '.local/s11/new-target-tests/roles.json'


def private_json(path):
    path = path.absolute()
    if path != ROLE_PROVIDER and PRIVATE not in path.parents:
        raise RuntimeError('Only S13 records or the explicitly authorized normal-role provider are allowed.')
    info = path.lstat()
    if (not stat.S_ISREG(info.st_mode) or path.is_symlink() or info.st_uid != os.geteuid()
            or stat.S_IMODE(info.st_mode) != 0o600):
        raise RuntimeError('Private input must be an owned regular mode-0600 file.')
    fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
    with os.fdopen(fd) as stream:
        return json.load(stream)


def execution_dirty_paths():
    """Preserve porcelain status bytes, including a leading unchanged index.

    A rename/copy contributes both paths so moving an execution file into a
    report directory cannot hide it behind the report-only allowance.
    """
    raw = subprocess.check_output(
        ['git', 'status', '--porcelain=v1', '--untracked-files=all', '-z'], cwd=ROOT)
    entries = iter(raw.split(b'\0')[:-1])
    paths = []
    for entry in entries:
        if len(entry) < 4 or entry[2:3] != b' ':
            raise RuntimeError('Unrecognized native worktree status; retain the frozen execution candidate.')
        paths.append(os.fsdecode(entry[3:]))
        if b'R' in entry[:2] or b'C' in entry[:2]:
            try:
                paths.append(os.fsdecode(next(entries)))
            except StopIteration as error:
                raise RuntimeError('Incomplete native rename status; retain the frozen execution candidate.') from error
    return paths


def owned_service(run_id):
    marker = private_json(PRIVATE / 'active.json')
    if (marker.get('plan_id') != PLAN or marker.get('run_id') != run_id or
            marker.get('database_name') != TARGET or marker.get('database_oid') != 2171423 or
            marker.get('cluster_ref') != '7694897083368259627' or marker.get('s11_session_clock')):
        raise RuntimeError('The exact owned S13 service/target is not established.')
    if not launcher.own_process_matches(marker['supervisor_pid'], marker['supervisor_start_ticks'], expected_script=True):
        raise RuntimeError('The S13 supervisor process birth/script identity is stale.')
    if launcher.proc_start_ticks(marker['child_pid']) != marker['child_start_ticks']:
        raise RuntimeError('The owned child process birth identity is stale.')
    if dt.datetime.now(dt.UTC) >= dt.datetime.fromisoformat(marker['scope_expires_at_utc'].replace('Z', '+00:00')):
        raise RuntimeError('The S13 project resource scope expired.')
    launcher.candidate_report_delta(marker['candidate_commit'], git('rev-parse', 'HEAD'))
    dirty = execution_dirty_paths()
    if any(path != 'CURRENT_TASK.md' and not path.startswith('docs/reports/s13-dl-p6/') for path in dirty):
        raise RuntimeError('Execution code differs from the frozen running candidate.')
    return {key: marker[key] for key in ('plan_id', 'run_id', 'candidate_commit', 'core_commit',
                                        'database_name', 'database_oid', 'cluster_ref', 'scope_id')}


class HttpActor:
    def __init__(self, alias, record_dir):
        roles = private_json(ROLE_PROVIDER)['users']
        if alias not in roles:
            raise RuntimeError('Unknown authorized normal-role alias.')
        self.alias = alias
        self.account = roles[alias]
        self.directory = record_dir
        self.session = requests.Session()
        self.session.trust_env = False
        self.events = []
        self.csrf = None
        self.revision = None

    def request(self, method, path, **kwargs):
        parsed = urlsplit(path)
        if parsed.scheme or parsed.netloc or not path.startswith('/') or path.startswith('//'):
            raise RuntimeError('HTTP requests must use an explicit relative loopback path.')
        operation = kwargs.pop('record_operation', None)
        timeout = kwargs.pop('timeout', 60)
        event = {'method': method, 'path': parsed.path, 'operation': operation, 'actor_alias': self.alias,
                 'started_at_utc': dt.datetime.now(dt.UTC).isoformat(),
                 'request_body_or_credentials_recorded': False, 'automatic_retry': False,
                 'independent_commit_verified': False}
        started = time.monotonic()
        try:
            response = self.session.request(method, BASE + path, timeout=timeout, allow_redirects=False, **kwargs)
            event.update(status=response.status_code, elapsed_seconds=time.monotonic() - started,
                         response_content_type=response.headers.get('Content-Type'))
            if response.is_redirect:
                location = urlsplit(response.headers.get('Location', ''))
                if location.netloc and location.netloc != '127.0.0.1:18411':
                    raise RuntimeError('The normal local request attempted an external redirect.')
                event['redirect_path'] = location.path
            return response
        except requests.RequestException as error:
            event.update(status=None, error_class=type(error).__name__, persistent_result='UNKNOWN_REQUIRES_READBACK_NO_RETRY')
            raise
        finally:
            event['finished_at_utc'] = dt.datetime.now(dt.UTC).isoformat()
            self.events.append(event)
            write_receipt(self.directory / ('http-%03d.json' % len(self.events)), event)

    def login(self, store_id):
        response = self.request('GET', '/web/login?db=' + TARGET)
        if response.status_code != 200:
            raise RuntimeError('The normal login form was unavailable.')
        tree = html.fromstring(response.content)
        csrf = tree.xpath('//form[contains(@class,"oe_login_form")]//input[@name="csrf_token"]/@value')
        if len(csrf) != 1:
            raise RuntimeError('The normal login form has no unique CSRF value.')
        response = self.request('POST', '/web/login', data={'login': self.account['login'],
            'password': self.account['password'], 'csrf_token': csrf[0], 'db': TARGET,
            'redirect': '/ydental/access'})
        if response.status_code not in (302, 303):
            raise RuntimeError('Normal-role authentication did not complete.')
        identity = self.request('POST', '/web/session/get_session_info', json={
            'jsonrpc': '2.0', 'method': 'call', 'params': {}, 'id': 1}).json().get('result', {})
        if identity.get('uid') != self.account['id']:
            raise RuntimeError('The authenticated actor differs from its normal-role provider.')
        response = self.request('GET', '/ydental/access')
        if response.status_code != 200:
            raise RuntimeError('The normal access workbench is unavailable.')
        tree = html.fromstring(response.content)
        csrf = tree.xpath('//input[@name="csrf_token"]/@value')
        revision = tree.xpath('//input[@name="revision"]/@value')
        if not csrf or not revision:
            raise RuntimeError('The normal store form has no revision/CSRF state.')
        self.csrf, self.revision = csrf[0], int(revision[0])
        response = self.action('/ydental/access/action', 'switch', {'store_id': store_id}, output='json')
        if response.status_code != 200:
            raise RuntimeError('The authorized normal-role store selection failed.')
        self.revision = response.json()['revision']
        self.account = {'id': self.account['id']}
        return {'actor_alias': self.alias, 'actual_uid': identity['uid'], 'store_id': store_id,
                'status': 'NORMAL_LOGIN_AND_STORE_SELECTED', 'credential_values_recorded': False}

    def action(self, path, operation, payload, **form):
        if self.csrf is None or self.revision is None:
            raise RuntimeError('A normal authenticated store form is required.')
        return self.request('POST', path, record_operation=operation, data={
            'csrf_token': self.csrf, 'revision': self.revision, 'operation': operation,
            'payload': json.dumps(payload), **form})

    def close(self):
        self.session.close()

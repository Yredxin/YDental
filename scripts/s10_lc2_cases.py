"""R1.2 serial owned-target A/B/C/D/E runner, with RAM-only authentication."""
import argparse
import ast
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
from html.parser import HTMLParser
import io
import json
import os
from pathlib import Path
import select
import time
import uuid
import re
import threading
from contextlib import contextmanager
from urllib.parse import urlencode

from s10_lc2_evidence import collect_selection, runtime_gate, save_once
from s10_lc2_http import Client, OutcomeUnknown, RequestNotSent, csrf_from
from s10_lc2_launch import ACTION_ROLES, OwnedApplication, ROOT, stop
from s10_lc2_logging import strict_loads, validate_jsonl
from s10_lc2_targets import (EXEC_ROOT, LEGACY_EXEC_ROOT, PLAN, RUN_ROOT, PackageBudget,
                            credentials, require_dispatch_unfrozen)

ORIGINAL_SHA = '05928780e7d97a06cf29019634f64b010eb4994c2f1c5032d561008a50b059b4'
NAMES = {'main': 'ydental_s10_test_20261017105432_810a7d9c', 'scratch': 'ydental_s10_test_20261017105432_ce6dcbf8'}
OIDS = {'main': 2144129, 'scratch': 2144130}
BASES = {'main': 'http://127.0.0.1:18410', 'scratch': 'http://127.0.0.1:18411'}


class PageFacts(HTMLParser):
    def __init__(self, body):
        super().__init__()
        self.revisions, self.main = set(), {}
        self.feed(body.decode('utf-8', errors='strict'))

    def handle_starttag(self, tag, values):
        attrs = dict(values)
        if tag == 'input' and attrs.get('name') == 'revision':
            self.revisions.add(int(attrs['value']))
        if tag == 'main':
            self.main.update(attrs)


class Facts:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=False)

    def save(self, name, value):
        return save_once(self.directory / (name + '.json'), value)


class Actor:
    def __init__(self, role, name, uid, login, password, *, budget, directory):
        self.role, self.uid, self.login_name, self.password = role, uid, login, password
        self.client = Client(BASES[role], database=NAMES[role], owned_targets={NAMES[role]: BASES[role]},
                             target_role=role, budget=budget, directory=directory)
        self.connection = uuid.uuid4().hex
        self.revision, self.csrf = None, None

    def login(self, store_id):
        response = self.client.login(self.login_name, self.password)
        response.require_status(302, 303)
        self.refresh()
        self.switch(store_id)
        return self

    def refresh(self):
        page = self.client.request('GET', '/ydental/access', case_id='L02')
        page.require_status(200)
        self.csrf = csrf_from(page)
        revisions = PageFacts(page.body).revisions
        if len(revisions) != 1:
            raise RuntimeError('ACCESS_PAGE_REVISION_NOT_UNIQUE')
        self.revision = revisions.pop()
        return self.revision

    def switch(self, store_id):
        value = self.action('access', 'switch', {'store_id': store_id}, case='C-SCOPE')
        self.revision = value['revision']
        return self.revision

    def action(self, endpoint, operation, payload, *, case, key=None, expect=(200,), discard=False,
               retry=False, operation_ref=None, attempt=1):
        form = {'operation': operation, 'revision': self.revision, 'csrf_token': self.csrf}
        if endpoint == 'settlement':
            form.update(payload)
            form['key'] = key or uuid.uuid4().hex
        else:
            form.update(payload=json.dumps(payload, separators=(',', ':')), output='json')
            if endpoint != 'access':
                form['key'] = key or uuid.uuid4().hex
            if endpoint in {'clinical', 'queue', 'treatment'}:
                form['connection'] = self.connection
        if endpoint in {'clinical', 'queue'}:
            form.pop('key', None)
        if endpoint in {'clinical', 'queue', 'treatment'}:
            form.pop('output', None)
        response = self.client.request('POST', '/ydental/' + endpoint + '/action', form=form,
                                       case_id=case, attempt=attempt, operation_ref=operation_ref or operation,
                                       discard_response=discard, retry_manifest=retry)
        if discard:
            if response.commit_observation != 'UNKNOWN':
                raise RuntimeError('REFUND_LOSS_NOT_UNKNOWN')
            return response
        response.require_status(*expect)
        value = response.json()
        if response.status == 200 and 'error' in value:
            raise AssertionError('APPLICATION_RETURNED_ERROR_AT_SUCCESS_STATUS')
        return value

    def rpc(self, model, method, args, *, case='C-SCOPE', attempt=1, kwargs=None):
        parameters = {'context': {'ydental_revision': self.revision, 'lang': 'en_US'}}
        parameters.update(kwargs or {})
        response = self.client.rpc(model, method, args, kwargs=parameters,
                                   case_id=case, attempt=attempt, operation_ref=(model + '.' + method)[:96])
        response.require_status(200)
        return response, response.json()

    def rpc_observed(self, model, method, args, *, operation_ref, attempt=1):
        """Observe one B request without assertions or automatic replay.

        INTENT_READY is a local boundary, never proof that Odoo received bytes.
        No exception messages, arbitrary response bodies or credentials escape.
        """
        dispatch = {}
        observed = {'started_utc': datetime.now(timezone.utc).isoformat(),
                    'dispatch_state': 'NOT_SENT', 'request_id': None,
                    'http_status': None, 'native_error_name': None,
                    'native_public_arguments_exact_expected': False}
        try:
            response = self.client.rpc(model, method, args,
                kwargs={'context': {'ydental_revision': self.revision, 'lang': 'en_US'}},
                case_id='B-RPC-6', attempt=attempt, operation_ref=operation_ref,
                dispatch_observer=dispatch.update)
        except Exception as error:
            observed.update(dispatch_state='NOT_SENT' if not dispatch or isinstance(error, RequestNotSent) else 'UNKNOWN',
                            request_id=dispatch.get('request_id'), local_exception_type=type(error).__name__)
        else:
            observed.update(request_id=response.request_id, http_status=response.status,
                            dispatch_state='RESPONSE_RECEIVED' if response.transport_outcome == 'RETURNED' else 'UNKNOWN')
            if observed['dispatch_state'] == 'RESPONSE_RECEIVED':
                try:
                    result = response.json()
                    valid = (type(result) is dict and result.get('jsonrpc') == '2.0'
                             and 'id' in result and ('error' in result) != ('result' in result))
                    observed['response_format_valid'] = valid
                    if not valid:
                        raise ValueError('B_RPC_RESPONSE_SHAPE_INVALID')
                    data = result.get('error', {}).get('data', {})
                    name = data.get('name')
                    allowed = {'odoo.exceptions.AccessError', 'odoo.exceptions.AccessDenied',
                               'odoo.exceptions.UserError', 'odoo.exceptions.ValidationError',
                               'odoo.http.SessionExpiredException', 'builtins.TypeError', 'builtins.ValueError'}
                    observed.update(native_error_name=name if name in allowed else 'OTHER',
                        result_present='result' in result,
                        native_public_arguments_exact_expected=data.get('arguments') == [_b_message(model, method)])
                except (ValueError, TypeError, AttributeError):
                    observed['response_format_valid'] = False
        observed['ended_utc'] = datetime.now(timezone.utc).isoformat()
        return observed


def existing_main_accounts():
    # Static data read only: never import, execute or reuse the old runner/session.
    chain = strict_loads((ROOT / '.local/ydental_s10_test_20261017050000_21b0cafe/b-chain.json').read_bytes())
    candidates = set()
    for path in sorted((ROOT / 'scripts').glob('s10*browser*.py')):
        source = ast.parse(path.read_bytes())
        for node in ast.walk(source):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'fill'
                    and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)
                    and isinstance(node.func.value, ast.Call) and node.func.value.args
                    and isinstance(node.func.value.args[0], ast.Constant)
                    and node.func.value.args[0].value == '[name=password]'):
                candidates.add(node.args[0].value)
    records = {row['id']: row for row in stored_rows(EXEC_ROOT / 'reentry-main', 'res_users')}
    from passlib.context import CryptContext
    verifier = CryptContext(schemes=['pbkdf2_sha512'])
    passwords = {}
    for uid in [5, 6, 7, 14, 41]:
        matches = [password for password in sorted(candidates) if verifier.verify(password, records[uid]['password'])]
        if len(matches) != 1:
            raise RuntimeError('EXISTING_SYNTHETIC_ACCOUNT_PASSWORD_NOT_VERIFIED_OFFLINE')
        passwords[uid] = matches[0]
    users = {uid: row['login'] for uid, row in records.items()}
    return {'manager': {'uid': chain['manager_id'], 'login': chain['manager_login'], 'password': passwords[chain['manager_id']]},
            'doctor': {'uid': chain['doctor_id'], 'login': chain['doctor_login'], 'password': passwords[chain['doctor_id']]},
            'ordinary': {'uid': chain['frontdesk_id'], 'login': users[chain['frontdesk_id']], 'password': passwords[chain['frontdesk_id']]},
            'cross_store': {'uid': 14, 'login': users[14], 'password': passwords[14]},
            'cross_company': {'uid': 41, 'login': users[41], 'password': passwords[41]}}


def marker(role):
    return next(item for item in strict_loads((LEGACY_EXEC_ROOT / 'owned-target-markers.json').read_bytes())['markers'] if item['role'] == role)


def reader_levels(fixture, store=1):
    return dict(dict(fixture['initial_levels'])[store])


def run_fixture(role, *, approval, product_commit, test_commit):
    input_read, input_write = os.pipe()
    output_read, output_write = os.pipe()
    app = OwnedApplication(marker(role), approval=approval, product_commit=product_commit,
                           test_commit=test_commit, action=role + '-fixture')
    app.env.update(YDENTAL_LC2_INPUT_FD=str(input_read), YDENTAL_LC2_OUTPUT_FD=str(output_write))
    request = json.dumps({'mode': 'main-prepare' if role == 'main' else 'scratch-bootstrap'}).encode()
    data = bytearray()
    deadline = time.monotonic() + 600
    exited_at = None
    try:
        app.start([], pass_fds=(input_read, output_write), stdin_path=ROOT / 'scripts/s10_lc2_fixture_process.py')
        os.close(input_read); input_read = None
        os.close(output_write); output_write = None
        os.write(input_write, request)
        os.close(input_write); input_write = None
        while True:
            app.budget.check_storage()
            if time.monotonic() >= deadline:
                raise TimeoutError('FIXTURE_RAM_PIPE_TOTAL_DEADLINE')
            if (EXEC_ROOT / 'HARD-STOP.json').exists():
                raise RuntimeError('FIXTURE_HARD_STOP')
            ready, _, _ = select.select([output_read], [], [], .1)
            if ready:
                chunk = os.read(output_read, 8192)
                if not chunk:
                    break
                data.extend(chunk)
                if len(data) > 65536:
                    raise RuntimeError('FIXTURE_RAM_OUTPUT_BOUND_EXCEEDED')
            if app.process.poll() is None:
                app.check()
            else:
                exited_at = exited_at or time.monotonic()
                if time.monotonic() - exited_at > 2:
                    raise TimeoutError('FIXTURE_CHILD_EXITED_WITHOUT_PIPE_EOF')
        code = app.wait(600)
        if code:
            raise RuntimeError('FIXTURE_PROCESS_FAILED_WITH_PRESERVED_STATE')
        result = strict_loads(data)
        save_once(app.directory / 'safe-result.json', result['safe'])
        closed_log_report(app)
        return result
    except BaseException:
        app.close(primary={'event_id': None})
        raise
    finally:
        for fd in [input_read, input_write, output_read, output_write]:
            if fd is not None:
                os.close(fd)


def capture(role, label, *, selections=None, metadata=False, max_rows=100000):
    run = RUN_ROOT / NAMES[role]
    if selections is None:
        selections = strict_loads((LEGACY_EXEC_ROOT / 'admission-r11-final/admission-selection.json').read_bytes())['tables']
    directory = EXEC_ROOT / ('capture-' + role + '-' + label)
    import psycopg2
    collect_selection(psycopg2.connect, credentials(), database=NAMES[role], expected_oid=OIDS[role],
                      selections=selections, directory=directory, budget=PackageBudget(EXEC_ROOT),
                      allowed_target_names=list(NAMES.values()), target_directory=run, config_path=run / 'odoo.conf',
                      collect_metadata=metadata, max_bytes=64 * 1024 * 1024, max_rows=max_rows)
    return directory


def stored_rows(directory, table):
    path = Path(directory) / (table + '.rows.jsonl')
    return [strict_loads(strict_loads(line)['server_json_text'], parse_float=Decimal) for line in path.read_bytes().splitlines()]


def assert_main_preserved(before, after, *, document_editor_allowed=False):
    tables = strict_loads((Path(before) / 'sealed-index.json').read_bytes())['files']
    changed = []
    for item in tables:
        table = item['path'].removesuffix('.rows.jsonl')
        economic = table.startswith(('account_', 'stock_', 'ydental_inventory_', 'ydental_treatment_', 'ydental_exam_', 'ydental_settlement_'))
        economic = economic and 'mutex' not in table
        queue = table.startswith('ydental_queue_')
        if economic or queue or table == 'ydental_clinical_version':
            if stored_rows(before, table) != stored_rows(after, table):
                changed.append(table)
    old_doc = next(row for row in stored_rows(before, 'ydental_clinical_document') if row['id'] == 1)
    new_doc = next(row for row in stored_rows(after, 'ydental_clinical_document') if row['id'] == 1)
    for row in [old_doc, new_doc]:
        if row['ydental_version'] != 4 or row['state'] != 'confirmed' or row['write_uid'] != 7:
            raise RuntimeError('MAIN_DOCUMENT_V4_INTEGRITY_FAILURE')
    allowed = {'write_date', 'write_uid'} | {key for key in old_doc if key.startswith('ydental_editor_')}
    if any(new_doc[key] != value for key, value in old_doc.items() if key not in allowed):
        changed.append('ydental_clinical_document:noneditor')
    if changed:
        stop('MAIN_ECONOMIC_OR_VERSION_INTEGRITY_FAILURE', tables=changed)
        raise RuntimeError('MAIN_PRESERVATION_FAILURE')
    return {'all_economic_tables_unchanged': True, 'all_old_queue_rows_unchanged': True, 'version_ancestry_unchanged': True,
            'document_v4_confirmed': True, 'editor_fields_changed': [key for key in old_doc if old_doc[key] != new_doc[key]]}


def main_a(manager, doctor, facts):
    page = doctor.client.request('GET', '/ydental/clinical?document_id=1', case_id='A-EDITOR')
    page.require_status(200)
    state = PageFacts(page.body).main
    if state.get('data-version') != '4' or state.get('data-state') != 'confirmed':
        raise RuntimeError('MAIN_A_ACTUAL_PAGE_BASELINE_MISMATCH')
    acquired = doctor.action('clinical', 'acquire', {'document_id': 1}, case='A-EDITOR', operation_ref='main-legal-editor-acquire')
    token = acquired['editor_token']
    released = doctor.action('clinical', 'release', {'document_id': 1, 'editor_token': token}, case='A-EDITOR', operation_ref='main-legal-editor-release')
    facts.save('A-editor-http', {'actor_id': doctor.uid, 'acquire_http_200': True, 'release_http_200': True,
                                'response_token_retained': False, 'v4_before': True,
                                'release_result_keys': sorted(released), 'independent_verification': 'PENDING'})


B_TARGET_FIELDS = {
    'ydental.settlement.source': 'ydental_original_amount',
    'ydental.settlement.payment': 'ydental_amount',
    'ydental.access.audit': 'ydental_reason',
}


def _b_ref(value):
    return type(value) is str and bool(re.fullmatch(r'[A-Za-z0-9_./:-]{1,240}', value)) and '..' not in value.split('/')


def _b_sha(value):
    return type(value) is str and bool(re.fullmatch(r'[a-f0-9]{64}', value))


def _b_message(model, method):
    if model == 'ydental.access.audit':
        return 'Audit events cannot be changed.' if method == 'write' else 'Audit events cannot be deleted.'
    return ('history_immutable: Settlement evidence cannot be overwritten.' if method == 'write'
            else 'history_immutable: Settlement evidence cannot be deleted.')


def validate_b_inputs(manifest, provider_ref):
    """Validate non-secret inputs only; their referenced measurements remain external.

    This never opens a provider or manufactures current identities/targets. A
    future authorized caller must supply independently observed source receipts.
    """
    if (type(manifest) is not dict or set(manifest) != {'schema', 'identity', 'actor', 'store_id', 'targets', 'source_ref'}
            or manifest['schema'] != 'LC2_B_MANIFEST_1'
            or manifest['identity'] != {'database': NAMES['main'], 'oid': OIDS['main'], 'cluster': '7694897083368259627'}
            or not _b_ref(manifest['source_ref'])):
        raise ValueError('B_CURRENT_MANIFEST_REQUIRED')
    actor = manifest['actor']
    if (type(actor) is not dict or set(actor) != {'uid', 'active', 'internal', 'application_user', 'su', 'is_admin', 'is_system', 'metadata_ref'}
            or type(actor['uid']) is not int or actor['uid'] <= 1 or actor['uid'] == 7
            or any(actor[key] is not True for key in ('active', 'internal', 'application_user'))
            or actor['su'] is not False or actor['is_admin'] is not False or actor['is_system'] is not False
            or not _b_ref(actor['metadata_ref'])
            or type(manifest['store_id']) is not int or manifest['store_id'] <= 0):
        raise ValueError('B_ORDINARY_CURRENT_IDENTITY_REQUIRED')
    if (type(provider_ref) is not dict or set(provider_ref) != {'ref', 'actor_id'}
            or provider_ref['actor_id'] != actor['uid'] or not _b_ref(provider_ref['ref'])
            or not provider_ref['ref'].startswith('.local/')):
        raise ValueError('B_EXPLICIT_PRIVATE_PROVIDER_REFERENCE_REQUIRED')
    targets = manifest['targets']
    if (type(targets) is not list or len(targets) != 3
            or any(type(item) is not dict for item in targets)
            or {item.get('model') for item in targets} != set(B_TARGET_FIELDS)):
        raise ValueError('B_EXACT_CURRENT_TARGETS_REQUIRED')
    for item in targets:
        column = B_TARGET_FIELDS[item['model']]
        expected = 'LC2 denied tampering' if column == 'ydental_reason' else 1
        if (set(item) != {'model', 'id', 'values', 'source_ref'} or type(item['id']) is not int or item['id'] <= 0
                or type(item['values']) is not dict or item['values'] != {column: expected}
                or type(item['values'][column]) is not type(expected) or not _b_ref(item['source_ref'])):
            raise ValueError('B_NONEMPTY_TARGET_AND_VALID_WRITE_REQUIRED')
    return manifest


def _b_time(value):
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError('B_TIMEZONE_REQUIRED')
    return parsed.timestamp()


def _b_snapshot_valid(value, manifest, target, *, check_id, phase, point):
    """Consume a narrow independent-RO receipt, not a whole database snapshot."""
    if type(value) is not dict:
        return False
    try:
        _b_time(value['captured_utc'])
    except (KeyError, ValueError, TypeError):
        return False
    return (value.get('check_id') == check_id and value.get('phase') == phase and value.get('point') == point
            and value.get('baseline_ref') == manifest['source_ref']
            and value.get('transaction') == {'read_only': True, 'closed': True, 'outcome': 'ROLLBACK'}
            and value.get('layer') == 'INDEPENDENT_RO' and value.get('independent') is True
            and _b_ref(value.get('ref')) and _b_ref(value.get('connection_ref'))
            and value.get('identity') == manifest['identity']
            and value.get('actor') == manifest['actor']
            and value.get('source_ref') == target['source_ref']
            and value.get('model') == target['model'] and type(value.get('id')) is int and value.get('id') == target['id']
            and all(_b_sha(value.get(key)) for key in ('row_sha256', 'old_audit_sha256', 'protected_sha256'))
            and value.get('editor') == {'document_id': 1, 'state': 'confirmed', 'version': 4,
                                      'author_id': 7, 'responsible_id': 7,
                'ydental_editor_id': None, 'ydental_session_id': None, 'ydental_session_revision': 0,
                'ydental_connection_hash_is_null': True, 'ydental_editor_hash_is_null': True,
                'ydental_editor_expires': None, 'ydental_editor_lease_id': None})


def _b_preserved(before, after, manifest, target, *, check_id, phase, point='after', observation=None):
    if not (_b_snapshot_valid(before, manifest, target, check_id=check_id, phase=phase, point='before')
            and _b_snapshot_valid(after, manifest, target, check_id=check_id, phase=phase, point=point)
            and before['ref'] != after['ref']
            and before['connection_ref'] != after['connection_ref']
            and all(before[key] == after[key] for key in ('row_sha256', 'old_audit_sha256', 'protected_sha256'))):
        return False
    try:
        before_time, after_time = _b_time(before['captured_utc']), _b_time(after['captured_utc'])
        if not 0 <= after_time - before_time <= 300:
            return False
        if observation is not None:
            started, ended = _b_time(observation['started_utc']), _b_time(observation['ended_utc'])
            if not before_time <= started <= ended <= after_time or ended - started > 120:
                return False
    except (KeyError, ValueError, TypeError):
        return False
    return True


def _b_model_complete(model, manifest):
    """A producer summary flag cannot substitute for the six native observations."""
    if (type(model) is not dict or model.get('identity') != manifest['identity'] | {'core': 'f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb'}
            or model.get('actor_id') != manifest['actor']['uid']
            or type(model.get('checks')) is not list or len(model['checks']) != 6):
        return False
    uid = manifest['actor']['uid']
    try:
        batch_end = max(_b_time(row['ended_utc']) for row in model['checks'])
    except (KeyError, ValueError, TypeError):
        return False
    for index, (row, (target, method)) in enumerate(zip(model['checks'], [
            (target, method) for target in manifest['targets'] for method in ('write', 'unlink')])):
        check_id = 'B-MODEL-%d-%s' % (index // 2 + 1, method)
        if (type(row) is not dict or row.get('check_id') != check_id or row.get('phase') != 'B-model'
                or row.get('layer') != 'MODEL' or row.get('model') != target['model']
                or row.get('id') != target['id'] or row.get('operation') != method
                or any(type(row.get(key)) is not int for key in ('actor_id', 'effective_uid', 'default_env_uid'))
                or row.get('actor_id') != uid or row.get('effective_uid') != uid
                or row.get('default_env_uid') != uid or row.get('su_flag') is not False
                or row.get('default_env_su') is not False or row.get('is_admin') is not False
                or row.get('is_system') is not False or row.get('rollback_observed') is not True
                or row.get('exception_name') != 'odoo.exceptions.AccessError'
                or row.get('native_public_arguments') != [_b_message(target['model'], method)]
                or row.get('native_public_arguments_exact_expected') is not True or row.get('denied') is not True):
            return False
        before, after, terminal = (row.get(key) for key in ('before', 'after', 'terminal'))
        if (not _b_preserved(before, after, manifest, target, check_id=check_id, phase='B-model', observation=row)
                or not _b_preserved(before, terminal, manifest, target, check_id=check_id, phase='B-model', point='terminal', observation=row)
                or terminal['ref'] == after['ref']
                or _b_time(terminal['captured_utc']) < batch_end
                or row.get('existing_target_sha256') != before['row_sha256']
                or row.get('after_sha256') != before['row_sha256']):
            return False
    return True


def correlate_b_server(intent, observation, events):
    """Use existing producer fields; server/client request UUIDs are independent.

    check_id and phase are encoded in the bounded operation label, since the
    existing server producer has no separate fields with those names.
    """
    if type(events) is not list or observation.get('dispatch_state') == 'NOT_SENT':
        return None
    try:
        lower = _b_time(observation['started_utc'])
        upper = _b_time(observation['ended_utc'])
        if not 0 <= upper - lower <= 120:
            return None
    except (KeyError, ValueError, TypeError):
        return None
    matches = []
    for event in events:
        if type(event) is not dict:
            continue
        try:
            timestamp = _b_time(event['ts_utc'])
        except (KeyError, ValueError, TypeError):
            continue
        if (event.get('event') == 'request.received' and event.get('case_id') == 'B-RPC-6'
                and event.get('operation_ref') == intent['operation_ref_sha256']
                and event.get('attempt') == intent['attempt'] and lower - 1 <= timestamp <= upper + 1
                and _b_ref(event.get('request_id')) and _b_ref(event.get('trace_id'))
                and _b_ref(event.get('evidence_ref'))):
            matches.append(event)
    if len(matches) != 1:
        return None
    event = matches[0]
    return {key: event.get(key) for key in ('request_id', 'trace_id', 'actor_id', 'effective_uid',
                                           'su_flag', 'evidence_ref')}


def main_b(ordinary, facts, *, manifest=None, provider_ref=None, observe=None,
           server_events=None, terminal=None, phase='B-pre'):
    """Six explicit B calls with save-first evidence and no retry on uncertainty.

    Callbacks are supplied by the caller; this function never starts services,
    reads credentials, queries a database, or interprets a receipt as authority.
    """
    validate_b_inputs(manifest, provider_ref)
    if (ordinary.uid != manifest['actor']['uid'] or getattr(ordinary, 'role', None) != 'main'
            or type(ordinary.revision) is not int or ordinary.revision < 0
            or not re.fullmatch(r'[A-Za-z0-9_-]{1,24}', phase)):
        raise ValueError('B_ACTOR_OR_REVISION_MISMATCH')
    results, baselines, halted = [], [], False
    for index, target in enumerate(manifest['targets'], 1):
        for method in ('write', 'unlink'):
            check_id = 'B-RPC-%d-%s' % (index, method)
            binding = json.dumps({'phase': phase, 'check_id': check_id, 'model': target['model'],
                'target_id': target['id'], 'actor_id': ordinary.uid, 'baseline_ref': manifest['source_ref']},
                sort_keys=True, separators=(',', ':'))
            operation_ref = phase + '.' + check_id + '.' + hashlib.sha256(binding.encode()).hexdigest()[:24]
            intent = {'layer': 'HTTP_RPC', 'case_id': 'B-RPC-6', 'check_id': check_id, 'phase': phase,
                'created_utc': datetime.now(timezone.utc).isoformat(),
                'attempt': 1, 'model': target['model'], 'method': method, 'target_existing_id': target['id'],
                'args': [[target['id']], target['values']] if method == 'write' else [[target['id']]],
                'context': {'ydental_revision': ordinary.revision, 'lang': 'en_US'},
                'intended_actor_id': ordinary.uid, 'source_ref': target['source_ref'],
                'operation_ref': operation_ref,
                'operation_ref_sha256': hashlib.sha256(('ydental-client-operation:' + operation_ref).encode()).hexdigest()}
            facts.save(check_id + '-intent', intent)
            row = intent | {'classification': 'NOT_SENT', 'preservation': 'PENDING',
                            'server_identity': 'PENDING', 'before_ref': None, 'after_ref': None,
                            'evidence_gaps': []}
            try:
                before = observe('before', check_id, target) if observe else None
            except Exception:
                before = None
                row['evidence_gaps'].append('BEFORE_OBSERVER_FAILED')
            baseline_valid = _b_snapshot_valid(before, manifest, target, check_id=check_id, phase=phase, point='before')
            if baseline_valid:
                baseline_valid = (_b_time(intent['created_utc']) - 1 <= _b_time(before['captured_utc'])
                                  <= datetime.now(timezone.utc).timestamp() + 1)
            if not baseline_valid:
                row['reason'] = 'MISSING_CURRENT_INDEPENDENT_BASELINE'
                facts.save(check_id + '-observation', row)
                results.append(row)
                halted = True
                break
            baselines.append((target, before))
            row['before_ref'] = before['ref']
            try:
                observation = ordinary.rpc_observed(target['model'], method, intent['args'],
                                                    operation_ref=operation_ref, attempt=1)
            except Exception:
                observation = {'dispatch_state': 'UNKNOWN', 'request_id': None, 'http_status': None}
                row['evidence_gaps'].append('RPC_OBSERVER_FAILED_OUTCOME_UNKNOWN')

            # Save the available transport observation before interpreting it.
            facts.save(check_id + '-transport', observation)
            row.update(observation)
            row['classification'] = observation['dispatch_state']
            if observation['dispatch_state'] == 'RESPONSE_RECEIVED':
                if (observation.get('http_status') == 200 and observation.get('native_error_name') == 'odoo.exceptions.AccessError'
                        and observation.get('native_public_arguments_exact_expected') is True
                        and observation.get('result_present') is False and observation.get('response_format_valid') is True):
                    row['classification'] = 'EXPECTED_MODEL_DENIAL'
                else:
                    if observation.get('http_status') in {301, 302, 303, 307, 308, 401, 403} or observation.get('native_error_name') in {
                            'odoo.exceptions.AccessDenied', 'odoo.http.SessionExpiredException'}:
                        row['classification'] = 'AUTHENTICATION_OR_AUTHORIZATION_PRECONDITION'
                    elif observation.get('response_format_valid') is not True or observation.get('native_error_name') in {'builtins.TypeError', 'builtins.ValueError'}:
                        row['classification'] = 'FORMAT_PRECONDITION'
                    else:
                        row['classification'] = 'OTHER_NATIVE_RESULT_OR_REJECTION'
            try:
                events = server_events(intent, observation) if server_events else []
            except Exception:
                events = []
                row['evidence_gaps'].append('SERVER_EVENT_OBSERVER_FAILED')
            server = correlate_b_server(intent, observation, events)
            if server:
                row['server'] = server
                row['server_identity'] = ('VERIFIED' if server['actor_id'] == ordinary.uid
                    and server['effective_uid'] == ordinary.uid and server['su_flag'] is False else 'MISMATCH')
            try:
                after = observe('after', check_id, target) if observe else None
            except Exception:
                after = None
                row['evidence_gaps'].append('AFTER_OBSERVER_FAILED')
            row['after_ref'] = after.get('ref') if type(after) is dict else None
            if _b_preserved(before, after, manifest, target, check_id=check_id, phase=phase, observation=observation):
                row['preservation'] = 'VERIFIED'
            facts.save(check_id + '-observation', row)
            results.append(row)
            if (row['classification'] != 'EXPECTED_MODEL_DENIAL' or row['server_identity'] != 'VERIFIED'
                    or row['preservation'] != 'VERIFIED'):
                halted = True
                break
        if halted:
            break
    try:
        final = terminal(manifest) if terminal else None
    except Exception:
        final = None
    # Raw receipts stay at their explicit private references. Persist only the
    # check-bound safe source refs and validation result here.
    terminal_ok = (bool(baselines) and type(final) is list and len(final) == len(baselines)
                  and all(_b_preserved(before, end, manifest, target, check_id=results[index]['check_id'],
                                       phase=phase, point='terminal', observation=results[index])
                          and end['ref'] != results[index]['after_ref']
                          and all(_b_time(end['captured_utc']) >= _b_time(item['ended_utc'])
                                  for item in results if item.get('ended_utc'))
                          for index, ((target, before), end) in enumerate(zip(baselines, final))))
    summary = {'checks': results, 'terminal_preservation': 'VERIFIED' if terminal_ok else 'PENDING',
        'terminal_refs': [item['ref'] for item in final] if terminal_ok else [],
        'status': 'PASS' if len(results) == 6 and terminal_ok and all(
            item['classification'] == 'EXPECTED_MODEL_DENIAL' and item['server_identity'] == 'VERIFIED'
            and item['preservation'] == 'VERIFIED' for item in results) else 'PENDING',
        'layer': 'HTTP_RPC', 'native_runtime_claimed': False}
    facts.save('B-six-real-RPC', summary)
    return summary


def run_b_only(*, manifest, provider_ref, approval, product_commit, test_commit, facts,
               model_probe, actor_factory, observe, server_events, terminal):
    """Future B-only composition; current profiles do not grant this dispatch.

    The unchanged native admission gate runs before any injected dependency.
    No CLI shortcut, profile grant or provider loader is introduced here.
    """
    validate_b_inputs(manifest, provider_ref)
    runtime_gate(approval, product_commit=product_commit, test_commit=test_commit)
    require_dispatch_unfrozen()
    if (EXEC_ROOT / 'HARD-STOP.json').exists():
        raise RuntimeError('B_EXISTING_HARD_STOP')
    # No existing profile integrates B. Offline source approval cannot open it.
    raise RuntimeError('B_RUNTIME_PROFILE_INTEGRATION_PENDING')


def _run_b_only_checks(*, manifest, provider_ref, facts, model_probe, actor_factory,
                       observe, server_events, terminal):
    """Pure composition seam: all effects must be explicit caller dependencies.

    It neither grants admission nor supplies a live launcher/provider/observer.
    Only the future runtime integration may connect it to real dependencies.
    """
    validate_b_inputs(manifest, provider_ref)
    model = model_probe(manifest)
    facts.save('B-model-observation', model)
    if not _b_model_complete(model, manifest):
        return {'status': 'PENDING', 'model': model, 'rpc': 'NOT_RUN'}
    ordinary = actor_factory(provider_ref, manifest)
    rpc = main_b(ordinary, facts, manifest=manifest, provider_ref=provider_ref,
                 observe=observe, server_events=server_events, terminal=terminal)
    return {'status': rpc['status'], 'model': model, 'rpc': rpc}


def main_c(manager, reader, token, placeholder, facts, attachment_id, scope_actors, *, dynamic_pdf_admitted=False):
    from PIL import Image
    results = []
    # Genuine limited token was verified in an owned ordinary fixture cursor.
    # Tokens stay only in request memory; access transport logging is suppressed.
    for state, value in [('none', None), ('invalid', 'lc2-invalid-synthetic-token'), ('valid', token)]:
        query = '?' + urlencode({'access_token': value}) if value is not None else ''
        for route in ['content', 'image']:
            for download in [False, True]:
                suffix = query + ('&' if query else '?') + 'download=true' if download else query
                response = reader.client.request('GET', '/web/' + route + '/' + str(attachment_id) + suffix,
                    case_id='C-TOKEN', artifact_kind='image' if route == 'image' else 'pdf', operation_ref='native-' + route + '-' + state)
                row = {'route': route, 'download': download, 'token_state': state, 'request_id': response.request_id,
                       'status': response.status, 'bytes': len(response.body or b''),
                       'sha256': hashlib.sha256(response.body or b'').hexdigest()}
                if response.body and response.body.startswith(b'%PDF'):
                    stop('UNAUTHORIZED_ORIGINAL_BINARY_LEAK', request_id=response.request_id)
                    raise RuntimeError('NATIVE_ATTACHMENT_RETURNED_PROTECTED_PDF')
                if response.status == 200 and route == 'image':
                    with Image.open(io.BytesIO(response.body)) as actual, Image.open(io.BytesIO(placeholder)) as expected:
                        actual.load(); expected.load()
                        same = actual.size == expected.size and actual.convert('RGBA').tobytes() == expected.convert('RGBA').tobytes()
                        row.update(image_size=list(actual.size), expected_placeholder_pixels_equal=same)
                    if not same:
                        stop('NATIVE_IMAGE_UNEXPECTED_CONTENT', request_id=response.request_id)
                        raise RuntimeError('IMAGE_200_NOT_VERIFIED_PLACEHOLDER')
                elif response.status not in {403, 404}:
                    raise AssertionError('NATIVE_PROTECTED_ATTACHMENT_NOT_DENIED')
                results.append(row)
    for model, method, args in [
        ('ydental.settlement.bill.original', 'read', [[1], ['id', 'pdf_sha256']]),
        ('ir.attachment', 'read', [[attachment_id], ['raw']]),
        ('ir.attachment', 'export_data', [[attachment_id], ['raw']]),
        ('ydental.settlement.service', '_bill_original_bytes', [1]),
        ('ydental.settlement.source', 'read', [[1, 5], ['id', 'ydental_patient_id']]),
        ('ydental.settlement.bill.original', 'search_read', [[['id', '=', 1]], ['id', 'pdf_sha256']]),
        ('ydental.settlement.bill.original', 'web_read', [[1], {'id': {}, 'pdf_sha256': {}}]),
        ('ydental.settlement.bill.original', 'export_data', [[1], ['id', 'pdf_sha256']]),
        ('ir.attachment', 'search_read', [[['id', '=', attachment_id]], ['id', 'raw']]),
        ('ir.attachment', 'web_read', [[attachment_id], {'id': {}, 'raw': {}}]),
    ]:
        response, result = reader.rpc(model, method, args)
        if method == 'search_read' and result.get('result') == []:
            results.append({'model': model, 'method': method, 'layer': 'REAL_RPC_FILTERED_EMPTY',
                            'request_id': response.request_id, 'existing_target_independently_proven': True})
            continue
        if 'result' in result:
            stop('PROTECTED_SOURCE_RPC_UNEXPECTED_RESULT', model=model, method=method)
            raise RuntimeError('C_NATIVE_SOURCE_RPC_NOT_DENIED')
        error = result.get('error', {}).get('data', {})
        if error.get('name') not in {'odoo.exceptions.AccessError', 'odoo.exceptions.UserError'}:
            raise RuntimeError('C_NATIVE_RPC_UNEXPECTED_ERROR_TYPE')
        results.append({'model': model, 'method': method, 'layer': 'REAL_RPC_GUARD', 'request_id': response.request_id,
                        'native_error_name': error['name'], 'cross_patient_service_branch_claimed': False})
    # Read/export split uses the NEW reader alone. All other baseline categories
    # are restored by the family helper/browser callbacks after their tests.
    for label, levels in [('read-no-export', {'settlement': 'read', 'export': 'none'}),
                          ('export-no-read', {'settlement': 'none', 'export': 'write'}),
                          ('neither', {'settlement': 'none', 'export': 'none'})]:
        manager.action('access', 'grant', {'user_id': reader.uid, 'store_id': 1, 'levels': levels}, case='C-SCOPE')
        reader.refresh()
        page = reader.client.request('GET', '/ydental/settlement?patient_id=1', case_id='C-SCOPE')
        if label == 'read-no-export':
            page.require_status(200)
            if b'name="settled-bills"' not in page.body or b'/ydental/settlement/bill-original/' in page.body or b'/ydental/settlement/pdf/' in page.body:
                raise RuntimeError('READ_ONLY_WORKBENCH_EXPORT_OR_MISSING_SETTLED_SECTION')
            # Invoice 1 is a real pre-existing settled invoice; parse the table's
            # numeric cell rather than treating a generic HTTP 200 as visibility.
            section = page.body.split(b'name="settled-bills"', 1)[1].split(b'</section>', 1)[0]
            if not __import__('re').search(rb'<td[^>]*>\s*1\s*</td>', section):
                raise RuntimeError('READ_ONLY_WORKBENCH_EXISTING_INVOICE_NOT_VISIBLE')
        else:
            page.require_status(403)
        results.append({'permission': label, 'route': 'workbench', 'status': page.status,
                        'request_id': page.request_id, 'existing_invoice_visible': label == 'read-no-export',
                        'export_link_absent': True})
        for kind, target in [('bill', 1), ('receipt', 1), ('refund', 1)]:
            denied = reader.client.request('GET', '/ydental/settlement/pdf/%s/%s' % (kind, target), case_id='C-SCOPE')
            denied.require_status(403)
            results.append({'permission': label, 'route': 'dynamic-' + kind, 'status': denied.status, 'request_id': denied.request_id})
        response = reader.client.request('GET', '/ydental/settlement/bill-original/1', case_id='C-SCOPE')
        response.require_status(403)
        if response.body.startswith(b'%PDF'):
            stop('READER_SCOPE_ORIGINAL_LEAK')
            raise RuntimeError('C_SCOPE_LEAK')
        results.append({'permission': label, 'request_id': response.request_id, 'status': response.status})
    manager.action('access', 'grant', {'user_id': reader.uid, 'store_id': 1,
                                      'levels': {'settlement': 'read', 'export': 'write'}}, case='C-SCOPE')
    reader.refresh()
    for kind, target in ([('bill', 1), ('receipt', 1), ('refund', 1)] if dynamic_pdf_admitted else []):
        response = manager.client.request('GET', '/ydental/settlement/pdf/%s/%s' % (kind, target),
            case_id='C-ATTACHMENT', artifact_kind='pdf')
        response.require_status(200)
        if not response.body.startswith(b'%PDF-'):
            raise RuntimeError('AUTHORIZED_DYNAMIC_PDF_NOT_ACTUAL_PDF')
        results.append({'route': 'dynamic-' + kind, 'source_existing_id': target, 'status': 200,
                        'request_id': response.request_id, 'sha256': hashlib.sha256(response.body).hexdigest(),
                        'stored_original_regenerated': False})
    for route in ['content', 'image']:
        response = reader.client.request('GET', '/web/%s/ir.attachment/%s/raw' % (route, attachment_id),
            case_id='C-ATTACHMENT', artifact_kind='image' if route == 'image' else 'pdf')
        if response.body.startswith(b'%PDF'):
            stop('NATIVE_MODEL_FIELD_BINARY_LEAK')
            raise RuntimeError('NATIVE_MODEL_FIELD_BINARY_LEAK')
        if response.status == 200 and route == 'image':
            with Image.open(io.BytesIO(response.body)) as actual, Image.open(io.BytesIO(placeholder)) as expected:
                actual.load(); expected.load()
                if actual.size != expected.size or actual.convert('RGBA').tobytes() != expected.convert('RGBA').tobytes():
                    raise RuntimeError('MODEL_FIELD_IMAGE_NOT_PLACEHOLDER')
        elif response.status not in {403, 404}:
            raise RuntimeError('MODEL_FIELD_CONTENT_NOT_DENIED')
        results.append({'route': 'model-field-' + route, 'status': response.status, 'request_id': response.request_id,
                        'actual_content_semantics': 'VERIFIED_PLACEHOLDER' if response.status == 200 else 'DENIED'})
    # Actual existing authorized principals in another store/company; no grants
    # or membership of any historical user are changed for these checks.
    for actor, store, own_patient in scope_actors:
        path = '/ydental/settlement' + ('?patient_id=' + str(own_patient) if own_patient else '')
        page = actor.client.request('GET', path, case_id='C-SCOPE')
        page.require_status(200)
        denied_page = actor.client.request('GET', '/ydental/settlement?patient_id=1', case_id='C-SCOPE')
        denied_page.require_status(403)
        response = actor.client.request('GET', '/ydental/settlement/bill-original/1', case_id='C-SCOPE')
        response.require_status(403)
        results.append({'actor_id': actor.uid, 'store_id': store, 'original_id': 1,
                        'own_patient_workbench_status': page.status, 'foreign_patient_workbench_status': denied_page.status,
                        'request_id': response.request_id, 'status': response.status})
    facts.save('C-actual-matrix', {'cells': results, 'valid_limited_signature_used': True,
                                 'dynamic_pdf_positive_admission': 'ADMITTED' if dynamic_pdf_admitted else 'NOT_RUN_INTERNAL_HTTP_ACCOUNTING_GATE',
                                 'source_financial_family_nonempty_positive': 'NOT_RUN_NO_NEW_LEGITIMATE_FINANCIAL_FAMILY_SOURCE'})


def d_selection(schema=None):
    if schema is None:
        schema = strict_loads((EXEC_ROOT / 'capture-scratch-framework-state/schema.json').read_bytes())
    initial = strict_loads((LEGACY_EXEC_ROOT / 'admission-r11-final/admission-selection.json').read_bytes())['tables']
    return [item for item in initial if item['table'] in schema]


def d_observe(label):
    return capture('scratch', label, selections=d_selection(), metadata=True)


def verify_d(directory, source, *, state, actual_refund):
    payments = stored_rows(directory, 'ydental_settlement_payment')
    refunds = stored_rows(directory, 'ydental_settlement_refund')
    native = stored_rows(directory, 'account_payment')
    payment = next(row for row in payments if row['id'] == source['payment_id'])
    inbound = next(row for row in native if row['id'] == payment['ydental_payment_id'])
    invoice = next(row for row in stored_rows(directory, 'account_move') if row['id'] == source['invoice_id'])
    fees = stored_rows(directory, 'ydental_treatment_fee')
    if (len(payments) != 1 or len(fees) != 1 or payment['ydental_amount'] != 6
            or inbound['amount'] != 6 or inbound['payment_type'] != 'inbound'
            or not inbound['is_reconciled'] or inbound['state'] != 'reconciled'
            or invoice['state'] != 'posted' or invoice['amount_total'] != 6 or invoice['amount_residual'] != 0):
        stop('D_PAYMENT_INTEGRITY_FAILURE')
        raise RuntimeError('D_UNIQUE_SIX_NOT_INDEPENDENTLY_VERIFIED')
    parts = stored_rows(directory, 'account_partial_reconcile')
    for row, label in [(invoice, 'invoice'), (inbound, 'inbound')]:
        if row.get('company_id') != source['company_id'] or row.get('currency_id') != source['currency_id']:
            stop('D_CURRENCY_COMPANY_MISMATCH', layer=label)
            raise RuntimeError('D_CURRENCY_COMPANY_MISMATCH')
    if payment['ydental_store_id'] != source['store_id'] or payment['ydental_currency_id'] != source['currency_id']:
        raise RuntimeError('D_STORE_MISMATCH')
    if not parts or sum((row['amount'] for row in parts), Decimal(0)) != Decimal(6 + actual_refund):
        stop('D_PARTIAL_RECONCILIATION_MISMATCH')
        raise RuntimeError('D_NATIVE_PARTIAL_TOTAL_MISMATCH')
    if any(row['company_id'] != source['company_id'] or row['debit_currency_id'] != source['currency_id']
           or row['credit_currency_id'] != source['currency_id'] for row in parts):
        raise RuntimeError('D_PARTIAL_COMPANY_CURRENCY_MISMATCH')
    refund = next((row for row in refunds if row['id'] == source.get('refund_id')), None)
    outbound = [row for row in native if row['payment_type'] == 'outbound']
    credits = [row for row in stored_rows(directory, 'account_move') if row['move_type'] == 'out_refund']
    if state is None:
        if refunds or outbound or credits:
            raise RuntimeError('D_PRE_REFUND_UNEXPECTED_FINANCIAL_ROWS')
    else:
        if not refund or refund['ydental_state'] != state or refund['ydental_amount'] != 2:
            raise RuntimeError('D_REFUND_STATE_NOT_VERIFIED')
        if (refund['ydental_currency_id'] != source['currency_id'] or refund['ydental_payment_id'] != payment['id']):
            raise RuntimeError('D_REFUND_SCOPE_MISMATCH')
        if actual_refund:
            receipts = [row for row in stored_rows(directory, 'ydental_settlement_receipt')
                        if row['ydental_operation'] == 'refund_execute' and row['ydental_key'] == source['execute_key']]
            audits = [row for row in stored_rows(directory, 'ydental_access_audit')
                      if row['ydental_event'] == 'settlement.refund.execute' and row['ydental_target_id'] == refund['id']]
            if (len(outbound) != 1 or outbound[0]['amount'] != 2 or len(credits) != 1
                    or credits[0]['amount_total'] != 2 or credits[0]['state'] != 'posted'
                    or refund['ydental_native_payment_id'] != outbound[0]['id']
                    or refund['ydental_credit_note_id'] != credits[0]['id']
                    or len(receipts) != 1 or len(audits) != 1
                    or refund['ydental_requester_id'] == refund['ydental_approver_id']):
                stop('D_UNIQUE_REFUND_COMMIT_NOT_VERIFIED')
                raise RuntimeError('D_REFUND_UNKNOWN_NO_RETRY_ALLOWED')
            if any(row.get('company_id') != source['company_id'] or row.get('currency_id') != source['currency_id']
                   for row in outbound + credits):
                raise RuntimeError('D_OUTBOUND_CURRENCY_COMPANY_MISMATCH')
            if not outbound[0]['is_reconciled'] or outbound[0]['state'] != 'reconciled' or credits[0]['amount_residual'] != 0:
                raise RuntimeError('D_OUTBOUND_NOT_NATIVE_RECONCILED')
        elif outbound or credits or refund['ydental_native_payment_id'] or refund['ydental_credit_note_id']:
            stop('D_PRE_EXECUTION_UNEXPECTED_OUTBOUND')
            raise RuntimeError('D_FAILED_RECOVERY_ALREADY_PAID')
    return {'layer': 'INDEPENDENT_RO_NATIVE_COMMITTED', 'received': 6, 'actually_refunded': actual_refund,
            'net_received': 6 - actual_refund, 'refund_state': state,
            'native_inbound_count': 1, 'native_outbound_count': len(outbound),
            'native_credit_count': len(credits), 'source_fee_count': 1,
            'company_id': source['company_id'], 'currency_id': source['currency_id'], 'store_id': source['store_id'],
            'real_gateway_claimed': False, 'synthetic_offline_fixture': True}


def d_flow(manager, front, doctor, fixture, facts):
    now = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)
    fmt = lambda value: value.strftime('%Y-%m-%d %H:%M:%S')
    catalog = manager.action('intake', 'catalog', {'code': 'lc2-six-' + uuid.uuid4().hex, 'name': 'LC2 independent six-unit care',
        'kind': 'care', 'capability_id': fixture['capability_id'], 'uom_id': fixture['uom_id']}, case='D-ADMIT')
    mapping = manager.action('intake', 'mapping', {'catalog_id': catalog['id'], 'area_id': fixture['area_id'], 'execution_area_id': fixture['area_id']}, case='D-ADMIT')
    price = manager.action('intake', 'price', {'catalog_id': catalog['id'], 'currency_id': fixture['currency_id'], 'unit_price': 6,
        'start': fmt(now - timedelta(minutes=1)), 'end': fmt(now + timedelta(days=1)), 'reason': 'LC2 explicit synthetic six-unit policy'}, case='D-ADMIT')
    review = manager.action('intake', 'review', {'record_id': price['id'], 'version': price['version'], 'reason': 'LC2 reviewed synthetic price'}, case='D-ADMIT')
    manager.action('intake', 'publish', {'record_id': review['id'], 'version': review['version'], 'reason': 'LC2 published synthetic price'}, case='D-ADMIT')
    start, end = now + timedelta(minutes=5), now + timedelta(minutes=10)
    slot = manager.action('supply', 'slot', {'station_id': fixture['station_id'], 'start': fmt(start), 'end': fmt(end), 'total': 3,
        'capability_ids': [fixture['capability_id']], 'reason': 'LC2 independent synthetic capacity'}, case='D-ADMIT')
    manager.action('supply', 'publish', {'id': slot['id'], 'version': 1, 'user_ids': [manager.uid], 'reason': 'LC2 qualified synthetic coverage'}, case='D-ADMIT')
    patient = front.action('patients', 'create', {'values': {'name': 'LC2 independent synthetic D patient'}}, case='D-ADMIT')
    qualification = front.action('intake', 'reserve', {'patient_id': patient['id'], 'mapping_id': mapping['id'], 'start': fmt(start), 'end': fmt(end), 'channel': 'reservation'}, case='D-ADMIT')
    front.action('intake', 'arrive', {'patient_id': patient['id']}, case='D-ADMIT')
    front.action('intake', 'report', {'task_id': qualification['task_id'], 'version': qualification['task_version']}, case='D-ADMIT')
    lease = doctor.action('queue', 'enter', {'station_id': fixture['station_id']}, case='D-ADMIT')
    held = {'lease_id': lease['lease_id'], 'token': lease['token']}
    called = doctor.action('queue', 'call', held, case='D-ADMIT')
    if called['task_id'] != qualification['task_id']:
        raise RuntimeError('D_QUEUE_SELECTED_UNEXPECTED_TASK')
    execution = doctor.action('queue', 'start', held | {'entry_id': called['entry_id']}, case='D-ADMIT')
    document = doctor.action('clinical', 'open', {'execution_id': execution['execution_id'], 'lease_id': lease['lease_id'], 'lease_token': lease['token']}, case='D-ADMIT')
    content = document['content'] | {'chief_complaint': 'LC2 independent synthetic six-unit source'}
    saved = doctor.action('clinical', 'save', {'document_id': document['document_id'], 'editor_token': document['editor_token'],
        'expected_version': document['version'], 'content': content, 'key': uuid.uuid4().hex}, case='D-ADMIT')
    event = doctor.action('treatment', 'execute', {'execution_id': execution['execution_id'], 'lease_id': lease['lease_id'], 'lease_token': lease['token'],
        'document_id': document['document_id'], 'document_version': saved['version'], 'catalog_id': catalog['id'], 'quantity': 1,
        'source': 'LC2 independent ' + uuid.uuid4().hex, 'reason': 'LC2 one newly performed synthetic care', 'materials': [], 'teeth': [],
        'already_performed': False, 'policy': 'demo_confirmation'}, case='D-NORMAL-6')
    if event['amount'] != 6:
        raise RuntimeError('D_SOURCE_FEE_NOT_SIX')
    doctor.action('clinical', 'handover', {'document_id': document['document_id'], 'editor_token': document['editor_token'], 'expected_version': saved['version'],
        'content': content, 'key': uuid.uuid4().hex, 'lease_id': lease['lease_id'], 'lease_token': lease['token']}, case='D-ADMIT')
    bill = manager.action('settlement', 'bill', {'fee_ids': [event['fee_id']], 'discount': 0, 'reason': ''}, case='D-NORMAL-6')
    payment = manager.action('settlement', 'pay', {'invoice_ids': [bill['invoice_id']], 'amount': 6, 'channel': 'cash',
        'actual_utc': datetime.now(timezone.utc).isoformat(), 'proof': 'LC2 synthetic offline six received'}, case='D-NORMAL-6')
    source = {'patient_id': patient['id'], 'event_id': event['event_id'], 'fee_id': event['fee_id'], 'invoice_id': bill['invoice_id'], 'payment_id': payment['payment_id'],
              'company_id': fixture['company_id'], 'currency_id': fixture['currency_id'], 'store_id': fixture['store_id'],
              'manager_id': manager.uid, 'approver_id': front.uid}
    state = d_observe('normal-six')
    facts.save('D-normal-independent', verify_d(state, source, state=None, actual_refund=0) | source)
    request = manager.action('settlement', 'refund_request', {'payment_id': source['payment_id'], 'amount': 2, 'reason': 'LC2 synthetic two-unit refund'}, case='D-FAILED-2')
    source['refund_id'] = request['refund_id']
    front.action('settlement', 'refund_approve', {'refund_id': source['refund_id'], 'reason': 'LC2 independent authorized approval'}, case='D-FAILED-2')
    manager.action('settlement', 'refund_uncertain', {'refund_id': source['refund_id'], 'outcome': 'failed', 'reason': 'LC2 synthetic verified unpaid before offline execution'}, case='D-FAILED-2')
    facts.save('D-failed-independent', verify_d(d_observe('failed-two'), source, state='failed', actual_refund=0))
    front.action('settlement', 'refund_recover', {'refund_id': source['refund_id'], 'verified_not_paid': '1', 'reason': 'LC2 independent verified unpaid synthetic fact'}, case='D-RECOVER-2')
    facts.save('D-recover-independent', verify_d(d_observe('recovered-two'), source, state='approved', actual_refund=0))
    source['execute_key'] = uuid.uuid4().hex
    payload = {'refund_id': source['refund_id'], 'actual_utc': datetime.now(timezone.utc).isoformat(), 'proof': 'LC2 synthetic offline two actually returned'}
    loss = manager.action('settlement', 'refund_execute', payload, key=source['execute_key'], case='D-LOST-REFUND-2',
                          operation_ref='lc2-unique-refund-execute', discard=True, retry=True)
    facts.save('D-loss-observation', {'request_id': loss.request_id, 'outcome': 'UNKNOWN', 'automatic_retry': False})
    # The transport may return headers just before COMMIT. Bounded independent
    # observers can wait for visibility; they never re-dispatch the refund.
    verified = None
    for attempt in range(3):
        directory = d_observe('lost-independent-' + str(attempt + 1))
        refund = next(row for row in stored_rows(directory, 'ydental_settlement_refund') if row['id'] == source['refund_id'])
        if refund['ydental_state'] == 'done':
            verified = verify_d(directory, source, state='done', actual_refund=2)
            break
        time.sleep(.2)
    if verified is None:
        stop('REFUND_COMMIT_UNKNOWN_NO_RETRY')
        raise OutcomeUnknown('REFUND_NOT_VERIFIED_STOP_NO_RETRY')
    facts.save('D-lost-verified-before-retry', verified)
    retry_result = manager.action('settlement', 'refund_execute', payload, key=source['execute_key'], case='D-VERIFY-RETRY',
                                 operation_ref='lc2-unique-refund-execute', attempt=2, retry=True)
    if retry_result.get('result') != 'already_accepted':
        raise RuntimeError('D_RETRY_DID_NOT_RETURN_PRIOR_RECEIPT')
    facts.save('D-idempotent-retry-independent', verify_d(d_observe('retry-unique'), source, state='done', actual_refund=2))
    safe_source = {key: value for key, value in source.items() if key != 'execute_key'}
    facts.save('D-unique-source-identities', safe_source)
    return source


def closed_log_report(app):
    paths = sorted((app.run / 'diagnostics').glob('events-' + str(app.process.pid) + '-*.jsonl'))
    validation = validate_jsonl(paths)
    if validation['status'] != 'VALID':
        save_once(app.directory / 'strict-log-defects.json', {'defects': validation['defects']})
        raise RuntimeError('ACTUAL_PROCESS_LOG_NOT_COMPLETE_AND_VALID')
    report = {'pid': app.process.pid, 'returncode': app.process.returncode,
              'strict_jsonl': 'VALID', 'records': validation['record_count'],
              'run_end_is_transaction_commit': False, 'paths': [str(path) for path in paths]}
    save_once(app.directory / 'strict-log-report.json', report)
    return validation


def run_framework(*, approval, product_commit, test_commit):
    app = OwnedApplication(marker('scratch'), approval=approval, product_commit=product_commit,
                           test_commit=test_commit, action='scratch-tests')
    app.start(['--stop-after-init', '--load-language=zh_CN', '-i', 'ydental_settlement_test',
               '--test-enable', '--test-tags=s10_lc2'])
    if app.wait(1200) != 0:
        raise RuntimeError('FRAMEWORK_INSTALL_FAILED_PRESERVE_PARTIAL_STATE')
    logs = b''.join(path.read_bytes() for path in [app.native_logfile, app.directory / 'stdout.log'] if path.exists())
    source = ast.parse((ROOT / 'ydental_settlement_test/tests/test_log_closeout.py').read_bytes())
    expected = [node.name for node in ast.walk(source) if isinstance(node, ast.FunctionDef) and node.name.startswith('test_')]
    if len(expected) != 6 or any(not re.search(rb'Starting [^\n]*\b' + name.encode() + rb'\b', logs) for name in expected):
        raise RuntimeError('FRAMEWORK_SIX_CASES_NOT_ACTUALLY_STARTED')
    if not re.search(rb'0 failed, 0 error\(s\) of [1-9][0-9]* tests', logs) or re.search(rb'[1-9][0-9]* (?:failed|error\(s\))', logs):
        raise RuntimeError('FRAMEWORK_ACTUAL_RESULTS_NOT_ZERO_FAILURE')
    closed_log_report(app)
    directory = capture('scratch', 'framework-state', selections=[{'table': 'ir_module_module', 'order': ['id']}],
                        metadata=True, max_rows=1024)
    modules = stored_rows(directory, 'ir_module_module')
    target = next(row for row in modules if row['name'] == 'ydental_settlement_test')
    if target['state'] != 'installed' or any(row['state'] in {'to install', 'to upgrade', 'to remove'} for row in modules):
        raise RuntimeError('FRAMEWORK_INSTALL_NOT_INDEPENDENTLY_COMPLETE')
    save_once(EXEC_ROOT / 'framework-accepted-prerequisite.json', {
        'product_commit': product_commit, 'test_commit': test_commit, 'application_directory': str(app.directory),
        'six_actual_cases': expected, 'child_exit': 0, 'independent_module_state': 'installed',
        'gpr_ui_acceptance_claimed': False})


@contextmanager
def service(role, *, approval, product_commit, test_commit):
    with OwnedApplication(marker(role), approval=approval, product_commit=product_commit,
                          test_commit=test_commit, action=role + '-service') as app:
        app.start([])
        app.wait_ready()
        yield app
    closed_log_report(app)


def file_inventory(role):
    base = RUN_ROOT / NAMES[role] / 'data/filestore' / NAMES[role]
    output = {}
    if base.exists():
        for path in sorted(base.rglob('*')):
            if path.is_symlink():
                raise RuntimeError('OWNED_FILESTORE_SYMLINK_REFUSED')
            if path.is_file():
                output[str(path.relative_to(base))] = {'bytes': path.stat().st_size,
                    'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    return output


def e_selections(role):
    initial = strict_loads((LEGACY_EXEC_ROOT / 'admission-r11-final/admission-selection.json').read_bytes())['tables']
    schema = strict_loads((EXEC_ROOT / ('reentry-main/schema.json' if role == 'main' else 'capture-scratch-framework-state/schema.json')).read_bytes())
    tables = {item['table']: item for item in initial if item['table'] in schema}
    for table in ['ir_ui_view', 'ir_model_data', 'ir_module_module']:
        if table not in schema:
            raise RuntimeError('E_EXPECTED_TECHNICAL_TABLE_MISSING')
        tables[table] = {'table': table, 'order': ['id']}
    safe_fixture = strict_loads((EXEC_ROOT / 'actual-cases' / ('fixture-' + role + '-safe.json')).read_bytes())
    ids = [item['id'] for item in safe_fixture['report_parameters']]
    if len(ids) != 3 or len(set(ids)) != 3:
        raise RuntimeError('E_REPORT_CONFIGURATION_SCOPE_INVALID')
    tables['ir_config_parameter'] = {'table': 'ir_config_parameter', 'ids': ids, 'order': ['id']}
    return list(tables.values())


def verify_upgrade(before, after, *, role, files_before, files_after):
    """Every business row stays exact; only reviewed S10 loader metadata may vary."""
    before, after = Path(before), Path(after)
    index = strict_loads((before / 'sealed-index.json').read_bytes())['files']
    changed = []
    technical = []
    refs = stored_rows(before, 'ir_model_data')
    allowed_refs = {row['id'] for row in refs if row['module'] == 'ydental_settlement'}
    allowed_views = {row['res_id'] for row in refs if row['module'] == 'ydental_settlement' and row['model'] == 'ir.ui.view'}
    for item in index:
        table = item['path'].removesuffix('.rows.jsonl')
        old, new = stored_rows(before, table), stored_rows(after, table)
        if old == new:
            continue
        if table not in {'ir_ui_view', 'ir_model_data', 'ir_module_module'}:
            changed.append(table)
            continue
        a, b = {row['id']: row for row in old}, {row['id']: row for row in new}
        for identifier in set(a) | set(b):
            if a.get(identifier) == b.get(identifier):
                continue
            left, right = a.get(identifier), b.get(identifier)
            fields = sorted(key for key in set(left or {}) | set(right or {}) if (left or {}).get(key) != (right or {}).get(key))
            own = (identifier in allowed_refs if table == 'ir_model_data' else identifier in allowed_views if table == 'ir_ui_view'
                   else bool(left and right and left['name'] == right['name'] == 'ydental_settlement'))
            if not own or left is None or right is None or not set(fields) <= {'write_date', 'write_uid'}:
                changed.append(table + ':' + str(identifier))
            technical.append({'table': table, 'id': identifier, 'changed_fields': fields, 's10_owned': own})
    for filename in ['schema.json', 'native-access.json', 'queue-settings.json']:
        if (before / filename).read_bytes() != (after / filename).read_bytes():
            changed.append(filename)
    if files_before != files_after:
        changed.append('actual-filestore-bytes')
    if changed:
        stop('E_UPGRADE_PRESERVATION_DIFFERENCE', role=role, changed=changed)
        raise RuntimeError('E_UPGRADE_DIFFERENCE_REQUIRES_INDEPENDENT_REVIEW')
    return {'role': role, 'business_rows_exact': True, 'schema_security_queue_exact': True,
            'filestore_bytes_exact': True, 'technical_changes': technical,
            'upgrade_scope': 'ydental_settlement_only', 'rebuild_or_rollback_performed': False}


def upgrade(role, facts, *, approval, product_commit, test_commit):
    before = capture(role, 'E-before', selections=e_selections(role), metadata=True)
    files_before = file_inventory(role)
    facts.save('E-' + role + '-files-before', files_before)
    app = OwnedApplication(marker(role), approval=approval, product_commit=product_commit,
                           test_commit=test_commit, action=role + '-upgrade')
    app.start(['--stop-after-init', '--load-language=zh_CN', '-u', 'ydental_settlement'])
    if app.wait(1200):
        raise RuntimeError('E_UPGRADE_FAILED_KEEP_PARTIAL_TARGET_AND_FILES')
    closed_log_report(app)
    after = capture(role, 'E-after', selections=e_selections(role), metadata=True)
    files_after = file_inventory(role)
    facts.save('E-' + role + '-files-after', files_after)
    facts.save('E-' + role + '-independent', verify_upgrade(before, after, role=role,
               files_before=files_before, files_after=files_after))
    return after


def process_tree():
    """Read only PID/PPID/birth/executable basenames; no process arguments."""
    rows = {}
    for path in Path('/proc').iterdir():
        if not path.name.isdecimal():
            continue
        try:
            raw = (path / 'stat').read_text()
            tail = raw[raw.rfind(')') + 2:].split()
            rows[int(path.name)] = {'pid': int(path.name), 'parent_pid': int(tail[1]),
                                    'birth_ticks': int(tail[19]), 'exe_basename': Path(os.readlink(path / 'exe')).name}
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
    return rows


async def browser_phase(phase, manager, reader, doctor, reader_fixture, facts):
    from s10_lc2_browser import Credentials, run_browser
    directory = EXEC_ROOT / ('browser-' + phase)
    baseline = process_tree()
    observed, finished = {}, threading.Event()
    parent = os.getpid()

    def watch():
        while not finished.wait(.05):
            rows = process_tree()
            descendants = {parent}
            while True:
                expanded = descendants | {pid for pid, row in rows.items() if row['parent_pid'] in descendants}
                if expanded == descendants:
                    break
                descendants = expanded
            for pid in descendants - {parent} - set(baseline):
                row = rows[pid]
                if row['exe_basename'] in {'firefox', 'firefox-bin', 'node', 'plugin-container', 'RDD Process', 'Web Content', 'Socket Process'}:
                    observed[pid] = row

    thread = threading.Thread(target=watch, daemon=True)
    thread.start()
    async def grant(levels):
        return await asyncio.to_thread(manager.action, 'access', 'grant',
            {'user_id': reader.uid, 'store_id': 1, 'levels': levels}, case='C-REVOKED-PAGE')
    async def revoke():
        return await grant({'settlement': 'none', 'export': 'none'})
    async def restore():
        return await grant(reader_levels(reader_fixture))
    try:
        result = await run_browser(base_url=BASES['main'], database=NAMES['main'],
            owned_targets={NAMES['main']: BASES['main']}, budget=PackageBudget(EXEC_ROOT), directory=directory,
            phase=phase, manager_credentials=Credentials(manager.login_name, manager.password),
            reader_credentials=Credentials(reader.login_name, reader.password),
            doctor_credentials=Credentials(doctor.login_name, doctor.password), store_id=1,
            invoice_id=1, original_id=1, original_sha256=ORIGINAL_SHA, patient_id=1,
            audit_id=228, document_id=1, revoke_reader=revoke, restore_reader=restore,
            maximum_seconds=600)
    finally:
        finished.set(); thread.join(timeout=2)
        current = process_tree()
        survivors = [row for pid, row in observed.items() if pid in current and current[pid]['birth_ticks'] == row['birth_ticks']]
        save_once(directory / 'independent-process-closure.json', {'observer_pid': parent,
            'observed_owned_descendants': list(observed.values()), 'surviving_owned_descendants': survivors,
            'pid_reuse_checked_by_birth': True, 'browser_api_close_is_only_exit_evidence': False,
            'debug_scope': 'pw:browser_only', 'debug_window_seconds_max': 600,
            'exit_code_evidence': 'OUTER_PARENT_CAPTURED_PW_BROWSER_STDERR'})
        if survivors:
            stop('OWNED_BROWSER_DESCENDANT_STILL_LIVE', pids=[row['pid'] for row in survivors])
            raise RuntimeError('OWNED_BROWSER_CLEANUP_UNCONFIRMED')
    if not any(row['exe_basename'].startswith('firefox') for row in observed.values()):
        raise RuntimeError('ACTUAL_FIREFOX_PID_NOT_INDEPENDENTLY_OBSERVED')
    facts.save('browser-' + phase, result)


def post_c(manager, reader, cross_company, facts):
    manager.action('access', 'grant', {'user_id': reader.uid, 'store_id': 1,
                   'levels': {'settlement': 'read', 'export': 'none'}}, case='E-AFFECTED-REGRESSION')
    denied = reader.client.request('GET', '/ydental/settlement/bill-original/1', case_id='E-AFFECTED-REGRESSION')
    denied.require_status(403)
    other = cross_company.client.request('GET', '/ydental/settlement/bill-original/1', case_id='E-AFFECTED-REGRESSION')
    other.require_status(403)
    manager.action('access', 'grant', {'user_id': reader.uid, 'store_id': 1,
                   'levels': {'settlement': 'read', 'export': 'write'}}, case='E-AFFECTED-REGRESSION')
    facts.save('E-C-critical-real-HTTP', {'read_without_export': denied.status, 'cross_company': other.status,
               'request_ids': [denied.request_id, other.request_id]})


def run_closeout(*, approval, product_commit, test_commit):
    prerequisite = strict_loads((EXEC_ROOT / 'framework-accepted-prerequisite.json').read_bytes())
    if prerequisite['product_commit'] != product_commit or prerequisite['test_commit'] != test_commit:
        raise RuntimeError('ACTUAL_FRAMEWORK_PREREQUISITE_CANDIDATE_DRIFT')
    facts = Facts(EXEC_ROOT / 'actual-cases')
    facts.save('resource-plan', {'original_get_pre': 7, 'original_get_post': 4, 'original_get_repair_reserved': 1,
                              'firefox_pre_post': 2, 'firefox_repair_reserved': 1, 'dynamic_pdf_admitted': False})
    baseline = EXEC_ROOT / 'reentry-main'
    main_fixture = run_fixture('main', approval=approval, product_commit=product_commit, test_commit=test_commit)
    facts.save('fixture-main-safe', main_fixture['safe'])
    scratch_fixture = run_fixture('scratch', approval=approval, product_commit=product_commit, test_commit=test_commit)
    facts.save('fixture-scratch-safe', scratch_fixture['safe'])
    reader_ram = main_fixture['ram']['reader']
    accounts = existing_main_accounts()
    budget = PackageBudget(EXEC_ROOT)
    counter = 0
    def actor(role, name, values, store):
        nonlocal counter
        counter += 1
        uid = values.get('uid', values.get('user_id'))
        return Actor(role, name, uid, values['login'], values['password'], budget=budget,
                     directory=EXEC_ROOT / ('http-' + str(counter) + '-' + name)).login(store)
    with service('main', approval=approval, product_commit=product_commit, test_commit=test_commit) as app:
        manager = actor('main', 'manager-pre', accounts['manager'], 1)
        doctor = actor('main', 'doctor-pre', accounts['doctor'], 1)
        ordinary = actor('main', 'ordinary-pre', accounts['ordinary'], 1)
        reader = actor('main', 'new-reader-pre', reader_ram, 1)
        other_store = actor('main', 'other-store-pre', accounts['cross_store'], 3)
        other_company = actor('main', 'other-company-pre', accounts['cross_company'], 11)
        main_a(manager, doctor, facts)
        main_b(ordinary, facts)
        main_c(manager, reader, main_fixture['ram']['limited_token'],
               bytes.fromhex(main_fixture['ram']['expected_placeholder_hex']), facts,
               main_fixture['safe']['attachment_id'], [(other_store, 3, 2), (other_company, 11, None)])
        from s10_lc2_family import run_family
        def grant(levels):
            result = manager.action('access', 'grant', {'user_id': reader.uid, 'store_id': 1, 'levels': levels}, case='C-SCOPE')
            reader.refresh()
            return result
        def restore():
            return grant(reader_levels(reader_ram))
        family = run_family(reader, manager, grant, restore, directory=EXEC_ROOT / 'C-family', protected_patient_ids=(1, 2, 3, 4))
        facts.save('C-family-identities', family)
        asyncio.run(browser_phase('pre', manager, reader, doctor, reader_ram, facts))
        app.check()
    main_pre = capture('main', 'post-ABC', metadata=True)
    facts.save('main-old-preservation-pre-E', assert_main_preserved(baseline, main_pre))
    sf = scratch_fixture['ram']
    with service('scratch', approval=approval, product_commit=product_commit, test_commit=test_commit) as app:
        dm = actor('scratch', 'D-manager', sf['manager'], sf['store_id'])
        df = actor('scratch', 'D-approver', sf['frontdesk'], sf['store_id'])
        dd = actor('scratch', 'D-doctor', sf['doctor'], sf['store_id'])
        source = d_flow(dm, df, dd, sf, facts)
        app.check()
    upgrade('main', facts, approval=approval, product_commit=product_commit, test_commit=test_commit)
    upgrade('scratch', facts, approval=approval, product_commit=product_commit, test_commit=test_commit)
    with service('main', approval=approval, product_commit=product_commit, test_commit=test_commit) as app:
        manager = actor('main', 'manager-post', accounts['manager'], 1)
        doctor = actor('main', 'doctor-post', accounts['doctor'], 1)
        ordinary = actor('main', 'ordinary-post', accounts['ordinary'], 1)
        reader = actor('main', 'new-reader-post', reader_ram, 1)
        other_company = actor('main', 'other-company-post', accounts['cross_company'], 11)
        post_facts = Facts(EXEC_ROOT / 'actual-post-E')
        main_b(ordinary, post_facts)
        post_c(manager, reader, other_company, post_facts)
        asyncio.run(browser_phase('post', manager, reader, doctor, reader_ram, post_facts))
        app.check()
    final_main = capture('main', 'final', metadata=True)
    facts.save('final-main-old-preservation', assert_main_preserved(baseline, final_main))
    facts.save('final-D-after-E', verify_d(d_observe('final-after-E'), source, state='done', actual_refund=2))
    facts.save('runtime-finished', {'business_pass_claimed': 'PENDING_INDEPENDENT_ACCEPTANCE',
        'source_connections_R12': 0, 'main_economic_actions': 0, 'scratch_new_received': 6,
        'scratch_new_refund': 2, 'net': 4, 'old_funds_replayed': False,
        'dynamic_pdf_positive': 'NOT_RUN_INTERNAL_HTTP_ACCOUNTING_GATE',
        'nonempty_financial_family': 'NOT_RUN_NO_LEGITIMATE_NEW_SOURCE',
        'native_root_cause': 'UNKNOWN'})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['framework', 'closeout'])
    parser.add_argument('--approval', required=True)
    parser.add_argument('--product-commit', required=True)
    parser.add_argument('--test-commit', required=True)
    args = parser.parse_args()
    dispatch = runtime_gate(args.approval, product_commit=args.product_commit, test_commit=args.test_commit)
    required = {'scratch-tests'} if args.stage == 'framework' else {
        'main-fixture', 'scratch-fixture', 'main-service', 'scratch-service', 'main-upgrade', 'scratch-upgrade'}
    if not required <= set(dispatch.get('allowed_actions', [])):
        raise RuntimeError('PACKAGE_STAGE_NOT_DISPATCHED')
    operation = run_framework if args.stage == 'framework' else run_closeout
    operation(approval=args.approval, product_commit=args.product_commit, test_commit=args.test_commit)


if __name__ == '__main__':
    main()

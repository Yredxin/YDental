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
from urllib.parse import parse_qs, urlencode, urljoin, urlsplit

from s10_lc2_evidence import (collect_b_source, collect_selection, parse_b_server_events,
                             read_b_source, runtime_gate, save_once, verify_b_log_prefixes)
from s10_lc2_http import Client, OutcomeUnknown, RequestNotSent, csrf_from
from s10_lc2_launch import ACTION_ROLES, OwnedApplication, ROOT, stop
from s10_lc2_logging import strict_loads, validate_jsonl
from s10_lc2_targets import (EXEC_ROOT, LEGACY_EXEC_ROOT, PLAN, RUN_ROOT, PackageBudget,
                            credentials, require_dispatch_unfrozen)
from s10_lc2_task_profile import CURRENT_PLAN

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
        self.store_id, self.scope_request_id = None, None

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
        if type(value.get('revision')) is not int or value['revision'] < 0:
            raise RuntimeError('ACCESS_SWITCH_REVISION_INVALID')
        self.revision = value['revision']
        self.store_id = store_id
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
        if endpoint == 'access' and operation == 'switch':
            self.scope_request_id = response.request_id
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

    def session_metadata(self, *, binding):
        """Normal authenticated native metadata, with no SID/token export."""
        started = datetime.now(timezone.utc).isoformat()
        response = self.client.request('POST', '/web/session/get_session_info',
            json_body={'jsonrpc': '2.0', 'id': uuid.uuid4().hex, 'method': 'call', 'params': {}},
            case_id='B-RPC-6', operation_ref='B-session-metadata')
        response.require_status(200)
        info = response.json()['result']
        safe = {key: info.get(key) for key in ('uid', 'db', 'is_admin', 'is_system', 'is_internal_user', 'ydental_store_name')}
        safe['user_context'] = {'ydental_revision': info.get('user_context', {}).get('ydental_revision')}
        safe['user_companies'] = {'allowed_companies': {str(key): {'id': value['id']}
            for key, value in info.get('user_companies', {}).get('allowed_companies', {}).items()}}
        safe['source'] = {'binding': binding, 'request_id': response.request_id,
                          'started_utc': started, 'ended_utc': datetime.now(timezone.utc).isoformat(),
                          'switch_request_id': self.scope_request_id, 'requested_store_id': self.store_id,
                          'switch_revision': self.revision}
        return safe


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


def marker(role, profile=None):
    if profile is not None:
        if role != profile.target_role:
            raise RuntimeError('CURRENT_PLAN_FIXTURE_TARGET_MISMATCH')
        return strict_loads((profile.run_root / profile.database / 'database.json').read_bytes())
    return next(item for item in strict_loads((LEGACY_EXEC_ROOT / 'owned-target-markers.json').read_bytes())['markers'] if item['role'] == role)



def reader_levels(fixture, store=1):
    return dict(dict(fixture['initial_levels'])[store])


def run_fixture(role, *, approval, product_commit, test_commit, mode=None, manifest=None,
                provider_ref=None, observe=None, terminal=None, evidence_factory=None, profile=None):
    mode = mode or ('main-prepare' if role == 'main' else 'scratch-bootstrap')
    b_only = mode == 'main-b-only'
    log_off = mode == 'log-rollback-only' and manifest is not None and manifest.get('diagnostics') == 'OFF'
    if b_only:
        validate_b_inputs(manifest, provider_ref)
        if role != 'main' or ((observe is None or terminal is None) and evidence_factory is None):
            raise ValueError('B_FIXTURE_PARENT_DEPENDENCIES_REQUIRED')
    input_read, input_write = os.pipe()
    output_read, output_write = os.pipe()
    app = None
    try:
        app = OwnedApplication(marker(role, profile), approval=approval, product_commit=product_commit,
                               test_commit=test_commit, action=role + '-fixture',
                               **({'diagnostics_off': True} if log_off else {}),
                               **({'profile': profile} if profile is not None else {}))
        if b_only and evidence_factory is not None:
            callbacks = evidence_factory(app)
            observe, terminal = callbacks['observe'], callbacks['terminal']
    except BaseException as error:
        try:
            if app is not None:
                try:
                    save_once(app.directory / 'b-parent-setup-failure.json', {'failure_type': type(error).__name__,
                              'status': 'NOT_SENT', 'application_started': False})
                finally:
                    app.close(primary={'event_id': None})
        finally:
            for fd in (input_read, input_write, output_read, output_write):
                os.close(fd)
        if b_only:
            raise RuntimeError('B_FIXTURE_SETUP_FAILED_NOT_SENT') from None
        raise
    app.env.update(YDENTAL_LC2_INPUT_FD=str(input_read), YDENTAL_LC2_OUTPUT_FD=str(output_write))
    request = json.dumps({'mode': mode, **({'manifest': manifest} if manifest is not None else {})}).encode()
    data = bytearray()
    b_result, checkpoints, checkpoint_index = None, {}, 0
    expected = [(point, 'B-MODEL-%d-%s' % (index, method), target)
                for index, target in enumerate(manifest['targets'], 1)
                for method in ('write', 'unlink') for point in ('before', 'after')] if b_only else []
    def partial_b_failure(error_type):
        partial = []
        for _, check_id, _ in expected[::2]:
            path = app.run / 'diagnostics' / (check_id + '-observation.json')
            if path.is_file() and not path.is_symlink() and path.stat().st_size <= 16384:
                row = strict_loads(path.read_bytes())
                partial.append(row | checkpoints.get(check_id, {}))
        return {'safe': {'mode': mode, 'status': 'PENDING', 'failure_type': error_type,
            'fixture_commits': 0, 'model_checks': {'checks': partial, 'producer_status': 'FAILED',
            'actor_id': manifest['actor']['uid'], 'identity': manifest['identity'] | {'core': 'f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb'},
            'independent_preservation': 'PENDING'}}, 'ram': {}}
    deadline = time.monotonic() + 600
    exited_at = None
    try:
        app.start([], pass_fds=(input_read, output_write), stdin_path=ROOT / 'scripts/s10_lc2_fixture_process.py')
        os.close(input_read); input_read = None
        os.close(output_write); output_write = None
        os.write(input_write, request + (b'\n' if b_only else b''))
        if not b_only:
            os.close(input_write); input_write = None
        while True:
            app.budget.check_storage()
            if time.monotonic() >= deadline:
                raise TimeoutError('FIXTURE_RAM_PIPE_TOTAL_DEADLINE')
            if app.stop_path.exists():
                raise RuntimeError('FIXTURE_HARD_STOP')
            ready, _, _ = select.select([output_read], [], [], .1)
            if ready:
                chunk = os.read(output_read, 8192)
                if not chunk:
                    break
                data.extend(chunk)
                if len(data) > 65536:
                    raise RuntimeError('FIXTURE_RAM_OUTPUT_BOUND_EXCEEDED')
                while b_only and b'\n' in data:
                    line, _, tail = data.partition(b'\n')
                    data = bytearray(tail)
                    message = strict_loads(line)
                    if message.get('event') == 'b.checkpoint':
                        triple = (message.get('point'), message.get('check_id'), message.get('target'))
                        if checkpoint_index >= len(expected) or triple != expected[checkpoint_index]:
                            raise RuntimeError('B_FIXTURE_CHECKPOINT_ORDER_DRIFT')
                        point, check_id, target = triple
                        observer_error_type = None
                        try:
                            receipt = observe(point, check_id, target)
                        except Exception as error:
                            receipt = None
                            observer_error_type = type(error).__name__
                        accepted = _b_snapshot_valid(receipt, manifest, target,
                            check_id=check_id, phase='B-model', point=point)
                        checkpoints.setdefault(check_id, {})[point] = receipt if accepted else None
                        save_once(app.directory / (check_id + '-' + point + '.json'),
                            {'receipt': receipt if accepted else None, 'accepted': accepted,
                             'observer_error_type': observer_error_type})
                        os.write(input_write, json.dumps({'accepted': accepted, 'check_id': check_id, 'point': point}).encode() + b'\n')
                        checkpoint_index += 1
                    elif message.get('event') in {'b.result', 'b.failure'} and b_result is None:
                        b_result = message
                    else:
                        raise RuntimeError('B_FIXTURE_PIPE_EVENT_INVALID')
            if app.process.poll() is None:
                # A finite shell may have emitted run.end while its interpreter
                # is still closing. No further HTTP dispatch is requested here.
                app.check_evidence_markers()
                app.observe_events(allow_starting=time.monotonic() - app.started < 60)
            else:
                app.observe_native_exit(app.process.returncode)
                exited_at = exited_at or time.monotonic()
                if time.monotonic() - exited_at > 2:
                    raise TimeoutError('FIXTURE_CHILD_EXITED_WITHOUT_PIPE_EOF')
        code = app.wait(600)
        if code and not b_only:
            raise RuntimeError('FIXTURE_PROCESS_FAILED_WITH_PRESERVED_STATE')
        if b_only:
            if data or b_result is None:
                raise RuntimeError('B_FIXTURE_RESULT_INCOMPLETE')
            result = {key: b_result[key] for key in ('safe', 'ram')}
            model = result['safe'].get('model_checks')
            if model is None:
                result = partial_b_failure(result['safe'].get('failure_type', 'ChildFailure'))
                model = result['safe']['model_checks']
            model['producer_status'] = 'SUCCESS' if b_result['event'] == 'b.result' and not code else 'FAILED'
            try:
                final = terminal(manifest)
            except Exception as error:
                final = []
                result['safe']['terminal_error_type'] = type(error).__name__
            for index, row in enumerate(model['checks']):
                row.update(checkpoints.get(row['check_id'], {}))
                row['terminal'] = final[index] if type(final) is list and index < len(final) else None
            model['independent_preservation'] = 'VERIFIED' if _b_model_complete(model, manifest) else 'PENDING'
        else:
            result = strict_loads(data)
        if mode == 'log-rollback-only':
            result['safe'].update(owned_process_pid=app.process.pid,
                application_directory=str(app.directory.relative_to(ROOT)),
                native_exit_code=app.process.returncode)
        save_once(app.directory / 'safe-result.json', result['safe'])
        if code:
            raise RuntimeError('FIXTURE_PROCESS_FAILED_WITH_PRESERVED_STATE')
        if log_off:
            app.observe_events(final=True)
            if result['safe'].get('rollback_returned') is not True or result['safe'].get('cursor_close_returned') is not True:
                raise RuntimeError('LOG_OFF_REAL_MODEL_ROLLBACK_OR_CURSOR_CLOSE_MISSING')
            save_once(app.directory / 'optional-json-absence.json', {
                'status': 'EXPECTED_OPTIONAL_JSON_ABSENT', 'pid': app.process.pid,
                'native_exit_code': app.process.returncode, 'json_integrity_pass_claimed': False,
                'native_parent_exit_observed': True, 'rollback_returned': True, 'cursor_close_returned': True})
        else:
            closed_log_report(app)
        return result
    except BaseException as error:
        if b_only:
            path = app.directory / 'b-parent-failure.json'
            if not path.exists():
                save_once(path, partial_b_failure(type(error).__name__)['safe'])
        ended = app.directory / 'parent-exit.tsv'
        still_live = app.process is not None and app.process.poll() is None
        if (still_live or not ended.exists() or not any(
                line.startswith(b'parent.end\t') for line in ended.read_bytes().splitlines())):
            app.close(primary={'event_id': None})
        raise
    finally:
        for fd in [input_read, input_write, output_read, output_write]:
            if fd is not None:
                os.close(fd)


def capture(role, label, *, selections=None, metadata=False, max_rows=100000, profile=None):
    if profile is not None:
        profile.require_action('target-ro')
        profile.validate_target(NAMES[role], OIDS[role])
    run = (profile.run_root if profile is not None else RUN_ROOT) / NAMES[role]
    if selections is None:
        selections = strict_loads((LEGACY_EXEC_ROOT / 'admission-r11-final/admission-selection.json').read_bytes())['tables']
    directory = (profile.root if profile is not None else EXEC_ROOT) / ('capture-' + role + '-' + label)
    import psycopg2
    collect_selection(psycopg2.connect, credentials(), database=NAMES[role], expected_oid=OIDS[role],
                      selections=selections, directory=directory, budget=PackageBudget(profile.root, profile=profile) if profile is not None else PackageBudget(EXEC_ROOT),
                      allowed_target_names=[profile.database] if profile is not None else list(NAMES.values()), target_directory=run, config_path=run / 'odoo.conf',
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


def b_selections(requested, *, old_audit_ids=None):
    """Only the explicit B targets, native relationships and protected old rows."""
    keys = {'uid', 'store_id', 'patient_id', 'source_id', 'payment_id', 'audit_id',
            'invoice_id', 'line_id', 'native_payment_id'}
    if (type(requested) is not dict or set(requested) != keys
            or any(type(value) is not int or value <= 0 for value in requested.values())
            or requested['uid'] in {1, 7}):
        raise ValueError('B_EXPLICIT_RELATION_TARGETS_REQUIRED')
    def item(table, columns, *, ids=None, equals=None, digest=False, nulls=None, order=None):
        return {'table': table, 'columns': columns, 'row_digest': digest,
            **({'ids': ids} if ids is not None else {}), **({'equals': equals} if equals else {}),
            **({'null_columns': nulls} if nulls else {}), **({'order': order} if order else {})}
    return [
        item('res_users', ['id', 'active', 'company_id'], ids=[requested['uid']]),
        item('res_groups_users_rel', ['uid', 'gid'], equals={'uid': requested['uid']}, order=['uid', 'gid']),
        item('res_groups_implied_rel', ['gid', 'hid'], order=['gid', 'hid']),
        item('ir_model_data', ['id', 'module', 'name', 'model', 'res_id']) | {'xmlids': [
            'base.group_user', 'base.group_system', 'base.group_erp_manager', 'ydental_base.ydental_base_group_user']},
        item('ydental_access_store', ['id', 'name', 'active', 'company_id'], ids=[requested['store_id']]),
        item('ydental_access_membership', ['id', 'active', 'ydental_user_id', 'ydental_store_id', 'ydental_employee_id'],
             equals={'ydental_user_id': requested['uid'], 'ydental_store_id': requested['store_id']}),
        item('hr_employee', ['id', 'active', 'user_id', 'company_id'], equals={'user_id': requested['uid']}),
        item('ydental_access_session', ['ydental_user_id', 'ydental_store_id', 'ydental_revision'],
             equals={'ydental_user_id': requested['uid']}),
        item('ydental_settlement_source', ['id', 'ydental_store_id', 'ydental_patient_id', 'ydental_invoice_id', 'ydental_line_id'],
             ids=[requested['source_id']], digest=True),
        item('ydental_settlement_payment', ['id', 'ydental_store_id', 'ydental_patient_id', 'ydental_payment_id'],
             ids=[requested['payment_id']], digest=True),
        item('ydental_settlement_payment_invoice_rel', ['settlement_payment_id', 'invoice_id'],
             equals={'settlement_payment_id': requested['payment_id']}, digest=True,
             order=['settlement_payment_id', 'invoice_id']),
        item('ydental_access_audit', ['id', 'ydental_user_id', 'ydental_store_id', 'ydental_target_model', 'ydental_target_id'],
             ids=old_audit_ids, digest=True),
        item('ydental_patient', ['id', 'ydental_partner_id'], ids=[requested['patient_id']]),
        item('account_move', ['id', 'company_id', 'partner_id'], ids=[requested['invoice_id']], digest=True),
        item('account_move_line', ['id', 'move_id'], ids=[requested['line_id']], digest=True),
        item('account_payment', ['id', 'company_id'], ids=[requested['native_payment_id']], digest=True),
        item('ydental_clinical_document', ['id', 'state', 'ydental_version', 'ydental_author_id', 'ydental_responsible_id',
             'ydental_editor_id', 'ydental_session_id', 'ydental_session_revision', 'ydental_editor_expires', 'ydental_editor_lease_id'],
             ids=[1], digest=True, nulls=['ydental_connection_hash', 'ydental_editor_hash']),
        item('ydental_clinical_version', ['id'], equals={'ydental_document_id': 1}, digest=True),
    ]


def _b_one(rows, table, record_id):
    found = [row for row in rows.get(table, []) if row.get('id') == record_id]
    if len(found) != 1:
        raise ValueError('B_SOURCE_TARGET_MISSING_OR_AMBIGUOUS')
    return found[0]


def _b_relations(source, info, requested):
    """Native session info is only read in RAM; return its small safe projection."""
    rows, uid = source['rows'], requested['uid']
    user = _b_one(rows, 'res_users', uid)
    store = _b_one(rows, 'ydental_access_store', requested['store_id'])
    context = info.get('user_context', {})
    revision = context.get('ydental_revision')
    allowed = info.get('user_companies', {}).get('allowed_companies', {})
    provenance = info.get('source', {})
    try:
        started, ended = (_b_time(provenance[key]) for key in ('started_utc', 'ended_utc'))
        collected = _b_time(source['started_utc'])
        fresh = 0 <= ended - started <= 30 and 0 <= collected - ended <= 120
    except (KeyError, ValueError, TypeError):
        fresh = False
    if (info.get('uid') != uid or info.get('db') != source['binding']['identity']['database']
            or info.get('is_admin') is not False or info.get('is_system') is not False
            or info.get('is_internal_user') is not True or user.get('active') is not True
            or store.get('active') is not True or info.get('ydental_store_name') != store.get('name')
            or type(revision) is not int or revision < 0
            or str(store['company_id']) not in {str(key) for key in allowed}
            or provenance.get('binding') != source['binding'] or not _b_ref(provenance.get('request_id')) or not fresh):
        raise ValueError('B_NORMAL_SESSION_IDENTITY_OR_STORE_DRIFT')
    if (provenance.get('requested_store_id') != store['id'] or provenance.get('switch_revision') != revision
            or not _b_ref(provenance.get('switch_request_id'))):
        raise ValueError('B_NORMAL_SWITCH_PROVENANCE_REQUIRED')
    xmlids = {row['module'] + '.' + row['name']: row['res_id'] for row in rows.get('ir_model_data', [])
              if row.get('model') == 'res.groups'}
    needed = {'base.group_user', 'base.group_system', 'base.group_erp_manager', 'ydental_base.ydental_base_group_user'}
    if set(xmlids) != needed:
        raise ValueError('B_NATIVE_GROUP_METADATA_MISSING')
    groups = {row['gid'] for row in rows.get('res_groups_users_rel', []) if row['uid'] == uid}
    while True:
        expanded = groups | {row['hid'] for row in rows.get('res_groups_implied_rel', []) if row['gid'] in groups}
        if expanded == groups:
            break
        groups = expanded
    if (not {xmlids['base.group_user'], xmlids['ydental_base.ydental_base_group_user']} <= groups
            or groups & {xmlids['base.group_system'], xmlids['base.group_erp_manager']}):
        raise ValueError('B_CURRENT_NONADMIN_APPLICATION_GROUP_REQUIRED')
    members = [row for row in rows.get('ydental_access_membership', [])
               if row.get('active') is True and row.get('ydental_user_id') == uid
               and row.get('ydental_store_id') == store['id']]
    if len(members) != 1:
        raise ValueError('B_CURRENT_MEMBERSHIP_REQUIRED')
    employee = _b_one(rows, 'hr_employee', members[0]['ydental_employee_id'])
    if employee.get('active') is not True or employee.get('user_id') != uid or employee.get('company_id') != store['company_id']:
        raise ValueError('B_EMPLOYEE_COMPANY_RELATION_DRIFT')
    sessions = rows.get('ydental_access_session', [])
    expected_scope = {'ydental_user_id': uid, 'ydental_store_id': store['id'], 'ydental_revision': revision}
    # Current native metadata proves the current business scope. Several normal
    # sessions may witness the same tuple; none may contradict that scope.
    current_plan = source['binding'].get('run_id') == 's10-technical-closeout-v1'
    valid_scope = (bool(sessions) and all(row == expected_scope for row in sessions)
                   if current_plan else sum(row == expected_scope for row in sessions) == 1)
    if not valid_scope:
        raise ValueError('B_NORMAL_SESSION_SCOPE_NOT_OBSERVED')
    fee = _b_one(rows, 'ydental_settlement_source', requested['source_id'])
    payment = _b_one(rows, 'ydental_settlement_payment', requested['payment_id'])
    audit = _b_one(rows, 'ydental_access_audit', requested['audit_id'])
    invoice = _b_one(rows, 'account_move', requested['invoice_id'])
    line = _b_one(rows, 'account_move_line', requested['line_id'])
    native_payment = _b_one(rows, 'account_payment', requested['native_payment_id'])
    patient = _b_one(rows, 'ydental_patient', requested['patient_id'])
    if (any(row.get('ydental_store_id') != store['id'] for row in (fee, payment, audit))
            or fee.get('ydental_patient_id') != patient['id'] or payment.get('ydental_patient_id') != patient['id']
            or fee.get('ydental_invoice_id') != invoice['id'] or fee.get('ydental_line_id') != line['id']
            or line.get('move_id') != invoice['id'] or invoice.get('partner_id') != patient['ydental_partner_id']
            or payment.get('ydental_payment_id') != native_payment['id']
            or invoice.get('company_id') != store['company_id'] or native_payment.get('company_id') != store['company_id']
            or not any(row['settlement_payment_id'] == payment['id'] and row['invoice_id'] == invoice['id']
                       for row in rows.get('ydental_settlement_payment_invoice_rel', []))):
        raise ValueError('B_TARGET_PATIENT_INVOICE_COMPANY_RELATION_DRIFT')
    return {'uid': uid, 'store_id': store['id'], 'company_id': store['company_id'], 'revision': revision}


def manifest_from_b_source(reference, *, binding, session_info, provider_ref, requested):
    source = read_b_source(reference, binding=binding)
    if source['point'] != 'manifest' or source['selections'] != b_selections(requested):
        raise ValueError('B_MANIFEST_SOURCE_SELECTION_DRIFT')
    scope = _b_relations(source, session_info, requested)
    ref = 'b-source:' + reference['sha256']
    actor = {'uid': scope['uid'], 'active': True, 'internal': True, 'application_user': True,
             'su': False, 'is_admin': False, 'is_system': False, 'metadata_ref': ref}
    targets = [{'model': model, 'id': requested[key], 'values': {column: 'LC2 denied tampering' if column == 'ydental_reason' else 1},
                'source_ref': ref} for model, key, column in (
        ('ydental.settlement.source', 'source_id', 'ydental_original_amount'),
        ('ydental.settlement.payment', 'payment_id', 'ydental_amount'),
        ('ydental.access.audit', 'audit_id', 'ydental_reason'))]
    manifest = {'schema': 'LC2_B_MANIFEST_1', 'identity': binding['identity'], 'actor': actor,
                'store_id': scope['store_id'], 'targets': targets, 'source_ref': ref}
    validate_b_inputs(manifest, provider_ref)
    return manifest


def receipt_from_b_source(reference, *, binding, manifest, requested, session_info,
                          check_id, phase, point, target, old_audit_ids, used):
    if (manifest['identity'] != binding['identity'] or manifest['actor']['uid'] != requested['uid']
            or manifest['store_id'] != requested['store_id'] or target not in manifest['targets']):
        raise ValueError('B_RECEIPT_MANIFEST_RELATION_DRIFT')
    source = read_b_source(reference, binding=binding, used=used)
    if (source['point'], source['check_id'], source['phase']) != (point, check_id, phase):
        raise ValueError('B_RECEIPT_CHECKPOINT_DRIFT')
    if source['selections'] != b_selections(requested, old_audit_ids=old_audit_ids):
        raise ValueError('B_RECEIPT_PROTECTION_SELECTION_DRIFT')
    _b_relations(source, session_info, requested)
    rows = source['rows']
    row = _b_one(rows, target['model'].replace('.', '_'), target['id'])
    doc = _b_one(rows, 'ydental_clinical_document', 1)
    editor = {key: doc[key] for key in ('ydental_editor_id', 'ydental_session_id', 'ydental_session_revision',
        'ydental_connection_hash_is_null', 'ydental_editor_hash_is_null', 'ydental_editor_expires', 'ydental_editor_lease_id')}
    editor.update(document_id=doc['id'], state=doc['state'], version=doc['ydental_version'],
                  author_id=doc['ydental_author_id'], responsible_id=doc['ydental_responsible_id'])
    def digest(tables):
        values = {table: rows[table] for table in tables}
        return hashlib.sha256(json.dumps(values, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    audit_ids = [item['id'] for item in rows['ydental_access_audit']]
    if sorted(audit_ids) != sorted(old_audit_ids):
        raise ValueError('B_OLD_AUDIT_SELECTION_DRIFT')
    receipt = {'layer': 'INDEPENDENT_RO', 'independent': True, 'check_id': check_id, 'phase': phase,
        'point': point, 'baseline_ref': manifest['source_ref'], 'ref': 'b-source:' + reference['sha256'],
        'source_reference': reference,
        'connection_ref': source['connection_ref'], 'identity': binding['identity'], 'actor': manifest['actor'],
        'source_ref': target['source_ref'], 'model': target['model'], 'id': target['id'],
        'captured_utc': source['captured_utc'], 'transaction': {'read_only': True, 'closed': True, 'outcome': 'ROLLBACK'},
        'row_sha256': row['__row_sha256'], 'old_audit_sha256': digest(['ydental_access_audit']),
        'protected_sha256': digest(['ydental_settlement_source', 'ydental_settlement_payment',
            'ydental_settlement_payment_invoice_rel', 'account_move', 'account_move_line', 'account_payment',
            'ydental_clinical_document', 'ydental_clinical_version', 'res_users', 'res_groups_users_rel',
            'res_groups_implied_rel', 'ir_model_data', 'ydental_access_store', 'ydental_access_membership',
            'hr_employee', 'ydental_patient']), 'editor': editor}
    if not _b_snapshot_valid(receipt, manifest, target, check_id=check_id, phase=phase, point=point):
        raise ValueError('B_PROTECTION_RECEIPT_INVALID')
    return receipt


def b_evidence_callbacks(*, binding, manifest, requested, manifest_reference, session_info,
                         collect_step, log_source, close_owned_service, phase='B-pre'):
    """Connect existing producers/parsers to R1 consumers, with no live defaults.

    collect_step receives the exact projection and checkpoint and must call the
    existing collector. It returns a file reference, never a fabricated receipt.
    log_source is the owned app/target/PID argument set for the existing parser.
    The runtime entry remains closed; these are explicit composition dependencies.
    """
    baseline = read_b_source(manifest_reference, binding=binding)
    if manifest['source_ref'] != 'b-source:' + manifest_reference['sha256']:
        raise ValueError('B_CALLBACK_BASELINE_REFERENCE_DRIFT')
    if (manifest['actor']['uid'] != requested['uid'] or manifest['store_id'] != requested['store_id']
            or manifest['identity'] != binding['identity']):
        raise ValueError('B_CALLBACK_MANIFEST_RELATION_DRIFT')
    old_ids = [row['id'] for row in baseline['rows']['ydental_access_audit']]
    observed, used, prefixes, terminal_done = [], {baseline['measurement_id']}, [], False
    last_info = session_info if not callable(session_info) else None

    def observe(point, check_id, target):
        nonlocal last_info
        if point == 'before':
            last_info = session_info() if callable(session_info) else session_info
        current_info = last_info
        reference = collect_step(point=point, check_id=check_id, phase=phase,
                                 selections=b_selections(requested, old_audit_ids=old_ids))
        receipt = receipt_from_b_source(reference, binding=binding, manifest=manifest, requested=requested,
            session_info=current_info, check_id=check_id, phase=phase, point=point,
            target=target, old_audit_ids=old_ids, used=used)
        if point == 'before':
            observed.append((check_id, target))
        return receipt

    def server_events(intent, observation):
        options = log_source() if callable(log_source) else log_source
        parsed = parse_b_server_events(binding=binding, **options, final=False)
        durable = save_once(Path(options['app_directory']) / ('b-log-live-%02d.json' % len(prefixes)),
            {**{key: parsed[key] for key in ('binding', 'locations', 'prefixes', 'launch_refs', 'final')},
             'manifest_source_reference': manifest_reference})
        prefixes.append(parsed)
        return [event | {'source_reference': durable} for event in parsed['events']]

    def terminal(current_manifest):
        nonlocal terminal_done, last_info
        if terminal_done or current_manifest != manifest:
            raise ValueError('B_TERMINAL_REPLAY_OR_MANIFEST_DRIFT')
        terminal_done = True
        # Reuse the last bounded normal metadata observation. In particular,
        # UNKNOWN never causes another HTTP request merely to collect evidence.
        # No fabricated run.end: close the one owned service, then check seals.
        close_owned_service()
        options = log_source() if callable(log_source) else log_source
        final = parse_b_server_events(binding=binding, **options, final=True)
        verify_b_log_prefixes(prefixes, final)
        durable = save_once(Path(options['app_directory']) / 'b-log-final.json', {
            **{key: final[key] for key in ('binding', 'locations', 'prefixes', 'launch_refs', 'final')},
            'live_prefixes_verified': True, 'manifest_source_reference': manifest_reference})
        receipts = [observe('terminal', check_id, target) for check_id, target in observed]
        for receipt in receipts:
            receipt['sealed_log_sources'] = final['launch_refs'] + final['prefixes']
            receipt['sealed_log_reference'] = durable
        return receipts

    return {'observe': observe, 'server_events': server_events, 'terminal': terminal}


def b_collect_step(*, binding, connect, connection_args, directory, budget, target_directory, config_path):
    """Bind existing collector I/O once; each checkpoint gets a new measurement."""
    def collect(*, point, check_id, phase, selections):
        output = Path(directory) / (phase + '-' + check_id + '-' + point + '-' + uuid.uuid4().hex[:8])
        return collect_b_source(connect, connection_args, binding=binding, point=point,
            check_id=check_id, phase=phase, selections=selections, directory=output, budget=budget,
            target_directory=target_directory, config_path=config_path)
    return collect


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
    if (type(model) is not dict or model.get('producer_status') == 'FAILED'
            or model.get('identity') != manifest['identity'] | {'core': 'f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb'}
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
                                           'su_flag', 'evidence_ref', 'source_reference')}


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
            row['before_source'] = before.get('source_reference')
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
            row['after_source'] = after.get('source_reference') if type(after) is dict else None
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
        'terminal_sources': [{'source_reference': item.get('source_reference'),
                              'sealed_log_reference': item.get('sealed_log_reference')}
                             for item in final] if terminal_ok else [],
        'status': 'PASS' if len(results) == 6 and terminal_ok and all(
            item['classification'] == 'EXPECTED_MODEL_DENIAL' and item['server_identity'] == 'VERIFIED'
            and item['preservation'] == 'VERIFIED' for item in results) else 'PENDING',
        'layer': 'HTTP_RPC', 'native_runtime_claimed': False}
    facts.save('B-six-real-RPC', summary)
    return summary


def run_b_only(*, manifest, provider_ref, approval, product_commit, test_commit, facts,
               model_probe, actor_factory, observe, server_events, terminal, profile=None):
    """Current-plan B composition; historical profiles remain ineligible."""
    validate_b_inputs(manifest, provider_ref)
    extra = {'profile': profile} if profile is not None else {}
    runtime_gate(approval, product_commit=product_commit, test_commit=test_commit, **extra)
    require_dispatch_unfrozen(**extra)
    stop_path = profile.root / 'HARD-STOP.json' if profile is not None else EXEC_ROOT / 'HARD-STOP.json'
    if stop_path.exists():
        raise RuntimeError('B_EXISTING_HARD_STOP')
    if profile is None or profile.message_id != CURRENT_PLAN:
        raise RuntimeError('B_RUNTIME_PROFILE_INTEGRATION_PENDING')
    profile.require_action('B-MODEL-6')
    profile.require_action('B-RPC-6')
    return _run_b_only_checks(manifest=manifest, provider_ref=provider_ref, facts=facts,
        model_probe=model_probe, actor_factory=actor_factory, observe=observe,
        server_events=server_events, terminal=terminal)


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


def main_c(manager, reader, token, placeholder, facts, attachment_id, scope_actors, *, dynamic_pdf_admitted=False,
           profile=None, verify_permission=None, token_applicability=None, tail_only=False):
    from PIL import Image
    results = []
    def record(value):
        # Persist each completed predicate before any subsequent request.
        facts.save('C-cell-%03d' % (len(results) + 1), value)
        results.append(value)
    if tail_only and (profile is None or not dynamic_pdf_admitted):
        raise RuntimeError('C_TAIL_CURRENT_PROFILE_AND_DYNAMIC_ADMISSION_REQUIRED')
    if not tail_only:
        # A legal producer may supply a token in RAM; current plan records N/A only
        # when source and the independently observed attachment relationship agree.
        token_cases = [('none', None), ('invalid', 'lc2-invalid-synthetic-token')]
        if token is not None:
            token_cases.append(('valid', token))
        elif profile is not None and (not token_applicability or token_applicability.get('valid_token') != 'NOT_APPLICABLE_NO_CURRENT_LEGAL_ISSUER'):
            raise ValueError('C_TOKEN_APPLICABILITY_EVIDENCE_REQUIRED')
        for state, value in token_cases:
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
                        stop('UNAUTHORIZED_ORIGINAL_BINARY_LEAK', profile=profile, request_id=response.request_id)
                        raise RuntimeError('NATIVE_ATTACHMENT_RETURNED_PROTECTED_PDF')
                    if response.status == 200 and route == 'image':
                        with Image.open(io.BytesIO(response.body)) as actual, Image.open(io.BytesIO(placeholder)) as expected:
                            actual.load(); expected.load()
                            same = actual.size == expected.size and actual.convert('RGBA').tobytes() == expected.convert('RGBA').tobytes()
                            row.update(image_size=list(actual.size), expected_placeholder_pixels_equal=same)
                        if not same:
                            stop('NATIVE_IMAGE_UNEXPECTED_CONTENT', profile=profile, request_id=response.request_id)
                            raise RuntimeError('IMAGE_200_NOT_VERIFIED_PLACEHOLDER')
                    elif response.status not in {403, 404}:
                        raise AssertionError('NATIVE_PROTECTED_ATTACHMENT_NOT_DENIED')
                    record(row)
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
                record({'model': model, 'method': method, 'layer': 'REAL_RPC_FILTERED_EMPTY',
                                'request_id': response.request_id, 'existing_target_independently_proven': True})
                continue
            if 'result' in result:
                stop('PROTECTED_SOURCE_RPC_UNEXPECTED_RESULT', profile=profile, model=model, method=method)
                raise RuntimeError('C_NATIVE_SOURCE_RPC_NOT_DENIED')
            error = result.get('error', {}).get('data', {})
            if error.get('name') not in {'odoo.exceptions.AccessError', 'odoo.exceptions.UserError'}:
                raise RuntimeError('C_NATIVE_RPC_UNEXPECTED_ERROR_TYPE')
            record({'model': model, 'method': method, 'layer': 'REAL_RPC_GUARD', 'request_id': response.request_id,
                            'native_error_name': error['name'], 'cross_patient_service_branch_claimed': False})
        # Read/export split uses the NEW reader alone. All other baseline categories
        # are restored by the family helper/browser callbacks after their tests.
        for label, levels in [('read-no-export', {'settlement': 'read', 'export': 'none'}),
                              ('export-no-read', {'settlement': 'none', 'export': 'write'}),
                              ('neither', {'settlement': 'none', 'export': 'none'})]:
            manager.action('access', 'grant', {'user_id': reader.uid, 'store_id': 1, 'levels': levels}, case='C-SCOPE')
            if verify_permission is not None:
                verify_permission(label, levels)
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
            record({'permission': label, 'route': 'workbench', 'status': page.status,
                            'request_id': page.request_id, 'existing_invoice_visible': label == 'read-no-export',
                            'export_link_absent': True})
            for kind, target in [('bill', 1), ('receipt', 1), ('refund', 1)]:
                denied = reader.client.request('GET', '/ydental/settlement/pdf/%s/%s' % (kind, target), case_id='C-SCOPE')
                denied.require_status(403)
                record({'permission': label, 'route': 'dynamic-' + kind, 'status': denied.status, 'request_id': denied.request_id})
            response = reader.client.request('GET', '/ydental/settlement/bill-original/1', case_id='C-SCOPE')
            response.require_status(403)
            if response.body.startswith(b'%PDF'):
                stop('READER_SCOPE_ORIGINAL_LEAK', profile=profile)
                raise RuntimeError('C_SCOPE_LEAK')
            record({'permission': label, 'request_id': response.request_id, 'status': response.status})
        manager.action('access', 'grant', {'user_id': reader.uid, 'store_id': 1,
                                          'levels': {'settlement': 'read', 'export': 'write'}}, case='C-SCOPE')
        if verify_permission is not None:
            verify_permission('read-and-export', {'settlement': 'read', 'export': 'write'})
        reader.refresh()
        if profile is not None:
            positive = reader.client.request('GET', '/ydental/settlement?patient_id=1', case_id='C-SCOPE')
            positive.require_status(200)
            if b'href="/ydental/settlement/bill-original/1"' not in positive.body:
                raise RuntimeError('C_BOTH_PERMISSIONS_EXISTING_ORIGINAL_LINK_MISSING')
            original = reader.client.request('GET', '/ydental/settlement/bill-original/1',
                case_id='C-ATTACHMENT', artifact_kind='pdf')
            original.require_status(200)
            if not original.body.startswith(b'%PDF-') or hashlib.sha256(original.body).hexdigest() != ORIGINAL_SHA:
                raise RuntimeError('C_BOTH_PERMISSIONS_EXISTING_ORIGINAL_CHANGED')
            record({'permission': 'read-and-export', 'route': 'controlled-original',
                'workbench_request_id': positive.request_id, 'request_id': original.request_id,
                'status': 200, 'sha256': ORIGINAL_SHA, 'nonempty_existing_original': True})
    else:
        # Two HTML predicates were not durable in the failed first C run. These
        # do not repeat its token/RPC denials, four-way route matrix or original GET.
        from lxml import html
        for label, levels in [('tail-read-no-export', {'settlement': 'read', 'export': 'none'}),
                              ('tail-read-and-export', {'settlement': 'read', 'export': 'write'})]:
            facts.save(label + '-grant-intent', {'actor_id': reader.uid, 'store_id': 1, 'levels': levels})
            manager.action('access', 'grant', {'user_id': reader.uid, 'store_id': 1, 'levels': levels}, case='C-SCOPE')
            if verify_permission is None:
                raise RuntimeError('C_TAIL_INDEPENDENT_PERMISSION_OBSERVER_REQUIRED')
            verify_permission(label, levels)
            reader.refresh()
            page = reader.client.request('GET', '/ydental/settlement?patient_id=1', case_id='C-SCOPE')
            page.require_status(200)
            tree = html.fromstring(page.body)
            invoices = sorted(int(value.strip()) for value in tree.xpath(
                '//section[@name="settled-bills"]//tbody/tr/td[1]/text()') if value.strip())
            exports = [value for value in tree.xpath('//a/@href') if value.startswith(
                ('/ydental/settlement/bill-original/', '/ydental/settlement/pdf/'))]
            original_link = '/ydental/settlement/bill-original/1' in exports
            if (1 not in invoices or (levels['export'] == 'none' and exports)
                    or (levels['export'] == 'write' and not original_link)):
                raise RuntimeError('C_TAIL_HTML_READ_EXPORT_PREDICATE_FAILED')
            record({'permission': label, 'actor_id': reader.uid, 'store_id': 1,
                'request_id': page.request_id, 'status': 200, 'settled_invoice_ids': invoices,
                'existing_invoice1_visible': True, 'original1_link_present': original_link,
                'export_link_count': len(exports), 'body_sha256': hashlib.sha256(page.body).hexdigest(),
                'raw_body_retained': False, 'controlled_original_download_repeated': False})
    for kind, target in ([('bill', 1), ('receipt', 1), ('refund', 1)] if dynamic_pdf_admitted else []):
        report_actor = reader if profile is not None else manager
        facts.save('dynamic-' + kind + '-intent', {'actor_id': report_actor.uid,
            'kind': kind, 'source_existing_id': target, 'stored_original_regenerated': False})
        response = report_actor.client.request('GET', '/ydental/settlement/pdf/%s/%s' % (kind, target),
            case_id='C-ATTACHMENT', artifact_kind='pdf')
        response.require_status(200)
        if not response.body.startswith(b'%PDF-'):
            raise RuntimeError('AUTHORIZED_DYNAMIC_PDF_NOT_ACTUAL_PDF')
        record({'route': 'dynamic-' + kind, 'source_existing_id': target, 'status': 200,
                        'actor_id': report_actor.uid,
                        'request_id': response.request_id, 'sha256': hashlib.sha256(response.body).hexdigest(),
                        'stored_original_regenerated': False})
    for route in ['content', 'image']:
        response = reader.client.request('GET', '/web/%s/ir.attachment/%s/raw' % (route, attachment_id),
            case_id='C-ATTACHMENT', artifact_kind='image' if route == 'image' else 'pdf')
        if response.body.startswith(b'%PDF'):
            stop('NATIVE_MODEL_FIELD_BINARY_LEAK', profile=profile)
            raise RuntimeError('NATIVE_MODEL_FIELD_BINARY_LEAK')
        if response.status == 200 and route == 'image':
            with Image.open(io.BytesIO(response.body)) as actual, Image.open(io.BytesIO(placeholder)) as expected:
                actual.load(); expected.load()
                if actual.size != expected.size or actual.convert('RGBA').tobytes() != expected.convert('RGBA').tobytes():
                    raise RuntimeError('MODEL_FIELD_IMAGE_NOT_PLACEHOLDER')
        elif response.status not in {403, 404}:
            raise RuntimeError('MODEL_FIELD_CONTENT_NOT_DENIED')
        record({'route': 'model-field-' + route, 'status': response.status, 'request_id': response.request_id,
                        'actual_content_semantics': 'VERIFIED_PLACEHOLDER' if response.status == 200 else 'DENIED'})
    # Actual existing authorized principals in another store/company; no grants
    # or membership of any historical user are changed for these checks.
    for scope_actor in scope_actors:
        actor, store, own_patient = scope_actor[:3]
        scope = scope_actor[3] if len(scope_actor) == 4 else {}
        path = '/ydental/settlement' + ('?patient_id=' + str(own_patient) if own_patient else '')
        page = actor.client.request('GET', path, case_id='C-SCOPE')
        page.require_status(200)
        own_invoice = scope.get('own_invoice_id')
        if own_invoice and ('href="/ydental/settlement/pdf/bill/%d"' % own_invoice).encode() not in page.body:
            raise RuntimeError('C_FOREIGN_STORE_NONEMPTY_OWN_INVOICE_NOT_VISIBLE')
        record({'route': 'foreign-own-workbench', 'actor_id': actor.uid, 'store_id': store,
            'request_id': page.request_id, 'status': page.status, 'own_invoice_id': own_invoice,
            'nonempty_positive_proven': bool(own_invoice), 'body_sha256': hashlib.sha256(page.body).hexdigest(),
            'raw_body_retained': False})
        denied_page = actor.client.request('GET', '/ydental/settlement?patient_id=1', case_id='C-SCOPE')
        denied_page.require_status(200 if scope.get('patient1_related') else 403)
        if denied_page.status == 200 and any(value in denied_page.body for value in (
                b'/ydental/settlement/bill-original/1"', b'/ydental/settlement/pdf/bill/1"')):
            stop('C_FOREIGN_STORE_PROTECTED_INVOICE_LINK_LEAK', profile=profile)
            raise RuntimeError('C_FOREIGN_STORE_PROTECTED_INVOICE_LINK_LEAK')
        visible_financial = None
        if denied_page.status == 200:
            from lxml import html
            tree = html.fromstring(denied_page.body)
            visible_financial = {kind: set() for kind in ('invoice', 'payment', 'refund', 'fee', 'event', 'close')}
            for link in tree.xpath('//a/@href'):
                match = re.fullmatch(r'/ydental/settlement/pdf/(bill|receipt|refund)/(\d+)', link)
                if match:
                    kind = {'bill': 'invoice', 'receipt': 'payment', 'refund': 'refund'}[match[1]]
                    visible_financial[kind].add(int(match[2]))
            visible_financial['invoice'].update(int(value.strip()) for value in tree.xpath(
                '//section[@name="settled-bills"]//tbody/tr/td[1]/text()') if value.strip())
            for paragraph in tree.xpath('//section[h2[text()="线下付款与退款"]]/div/p'):
                label = ''.join(paragraph.itertext()).strip()
                kind = 'payment' if label.startswith('付款') else 'refund' if label.startswith('退款') else None
                identifiers = paragraph.xpath('./span[1]/text()')
                if kind and identifiers:
                    visible_financial[kind].add(int(identifiers[0].strip()))
            for heading, kind in (('今日未出账费用', 'fee'), ('历史未出账费用', 'fee'), ('待核对，禁止出账', 'event')):
                visible_financial[kind].update(int(value.strip()) for value in tree.xpath(
                    '//section[h2[text()=$heading]]//tbody/tr/td[1]/text()', heading=heading) if value.strip())
            visible_financial['close'].update(int(value.strip()) for value in tree.xpath(
                '//section[h2[text()="收费员日结"]]/div/p/span[1]/text()') if value.strip())
            expected_invoices = {row['id']: row for row in scope.get('patient1_visible_invoices', [])}
            for section, settled in (('//section[h2[text()="已出账未付清"]]', False),
                                     ('//section[@name="settled-bills"]', True)):
                for tr in tree.xpath(section + '//tbody/tr'):
                    links = [match for value in tr.xpath('.//a/@href') if (match := re.fullmatch(
                        r'/ydental/settlement/pdf/bill/(\d+)', value))]
                    cells = [''.join(cell.itertext()).strip() for cell in tr.xpath('./td')]
                    identifier = int(cells[0]) if settled and cells else int(links[0][1]) if len(links) == 1 else None
                    expected = expected_invoices.get(identifier)
                    offset = 1 if settled else 0
                    if (len(links) != 1 or not expected or len(cells) < offset + 4
                            or cells[offset] != expected['name']
                            or Decimal(cells[offset + 2].replace(',', '')) != Decimal(str(expected['amount_total']))
                            or Decimal(cells[offset + 3].replace(',', '')) != Decimal(str(expected['amount_residual']))):
                        stop('C_FOREIGN_FINANCIAL_ROW_NOT_CORRELATED', profile=profile)
                        raise RuntimeError('C_FOREIGN_FINANCIAL_ROW_NOT_CORRELATED')
            if (1 in visible_financial['invoice'] or any(not identifiers <= set(scope.get(
                    ('store_visible_close_ids' if kind == 'close' else 'patient1_visible_' + kind + '_ids'), []))
                    for kind, identifiers in visible_financial.items())):
                stop('C_FOREIGN_STORE_FINANCIAL_BODY_SCOPE_LEAK', profile=profile)
                raise RuntimeError('C_FOREIGN_STORE_FINANCIAL_BODY_SCOPE_LEAK')
            visible_financial = {key: sorted(value) for key, value in visible_financial.items()}
        record({'route': 'foreign-patient-workbench', 'actor_id': actor.uid, 'store_id': store,
            'request_id': denied_page.request_id, 'status': denied_page.status,
            'patient1_related': bool(scope.get('patient1_related')),
            'allowed_financial_body_ids': visible_financial,
            'body_sha256': hashlib.sha256(denied_page.body).hexdigest(), 'raw_body_retained': False})
        summary = actor.client.request('GET', '/ydental/settlement/other-stores/' + str(own_patient), case_id='C-SCOPE')
        summary.require_status(200)
        summary_rows = summary.json()
        if (type(summary_rows) is not list or any(type(row) is not dict or set(row) != {
                'store', 'store_id', 'company', 'currency', 'residual'} for row in summary_rows)):
            stop('C_OTHER_STORE_SUMMARY_FULL_CONTENT_OR_SHAPE_LEAK', profile=profile)
            raise RuntimeError('C_OTHER_STORE_SUMMARY_FULL_CONTENT_OR_SHAPE_LEAK')
        record({'route': 'foreign-other-store-summary', 'actor_id': actor.uid, 'store_id': store,
            'request_id': summary.request_id, 'status': summary.status,
            'summary_fields_only': True, 'summary_count': len(summary_rows),
            'body_sha256': hashlib.sha256(summary.body).hexdigest(), 'raw_body_retained': False,
            'summary_nonempty_status': 'NONEMPTY_SOURCE_SHAPE_VERIFIED' if summary_rows else 'EMPTY_ONLY_PENDING_NONEMPTY_SCRATCH'})
        response = actor.client.request('GET', '/ydental/settlement/bill-original/1', case_id='C-SCOPE')
        response.require_status(403)
        record({'route': 'foreign-controlled-original-denial', 'actor_id': actor.uid, 'store_id': store,
            'request_id': response.request_id, 'original_id': 1, 'status': 403})
        dynamic_denials = []
        for kind in ('bill', 'receipt', 'refund'):
            denied = actor.client.request('GET', '/ydental/settlement/pdf/' + kind + '/1', case_id='C-SCOPE')
            denied.require_status(403)
            record({'route': 'foreign-dynamic-' + kind + '-denial', 'actor_id': actor.uid,
                'store_id': store, 'existing_source_id': 1, 'request_id': denied.request_id, 'status': 403})
            dynamic_denials.append({'kind': kind, 'existing_source_id': 1, 'request_id': denied.request_id, 'status': 403})
        record({'actor_id': actor.uid, 'store_id': store, 'original_id': 1,
                        'own_patient_workbench_status': page.status, 'foreign_patient_workbench_status': denied_page.status,
                        'own_invoice_id': own_invoice, 'nonempty_positive_proven': bool(own_invoice),
                        'summary_request_id': summary.request_id, 'summary_count': len(summary_rows),
                        'summary_fields_only': True,
                        'summary_nonempty_status': 'NONEMPTY_SOURCE_SHAPE_VERIFIED' if summary_rows else 'EMPTY_ONLY_PENDING_NONEMPTY_SCRATCH',
                        'foreign_patient_financial_body_ids': visible_financial,
                        'dynamic_source_denials': dynamic_denials,
                        'request_id': response.request_id, 'status': response.status})
    facts.save('C-tail-actual-matrix' if tail_only else 'C-actual-matrix', {'cells': results, 'prefix_replayed': False if tail_only else None, 'valid_limited_signature_used': token is not None,
                                 'token_applicability': token_applicability,
                                 'dynamic_pdf_positive_admission': 'ADMITTED' if dynamic_pdf_admitted else 'NOT_RUN_INTERNAL_HTTP_ACCOUNTING_GATE',
                                 'source_financial_family_nonempty_positive': 'NOT_RUN_NO_NEW_LEGITIMATE_FINANCIAL_FAMILY_SOURCE'})



class CRecordedActor:
    """Retain each C-only persistent intent before its actual native HTTP call."""

    def __init__(self, actor, facts, label, fixture):
        if not re.fullmatch(r'[a-z][a-z0-9-]{0,35}', label):
            raise ValueError('C_SYNTHETIC_STEP_LABEL_INVALID')
        self.actor, self.facts, self.label, self.fixture = actor, facts, label, fixture
        self.uid, self.step = actor.uid, 0

    def __getattr__(self, name):
        return getattr(self.actor, name)

    def action(self, endpoint, operation, payload, **options):
        self.step += 1
        name = 'C-%s-%02d-%s' % (self.label, self.step, operation)
        options.setdefault('case', 'C-SCOPE')
        options.setdefault('operation_ref', name)
        if endpoint not in {'access', 'queue', 'clinical'}:
            options.setdefault('key', uuid.uuid4().hex)
        # Only the fixed new-fixture IDs/amounts leave this in-memory call.
        # Authentication, lease/editor tokens and synthetic text remain RAM-only.
        identifiers = {key: value for key, value in payload.items()
                       if (key.endswith('_id') and type(value) is int)
                       or (key.endswith('_ids') and type(value) is list
                           and all(type(item) is int for item in value))
                       or key in {'quantity', 'discount', 'unit_price', 'amount'}}
        self.facts.save(name + '-intent', {
            'stage': 'BEFORE_DISPATCH', 'actor_id': self.uid,
            'store_id': self.fixture['store_id'], 'company_id': self.fixture['company_id'],
            'endpoint': endpoint, 'operation': operation, 'business_ids': identifiers,
            'key': options.get('key'), 'operation_ref': options['operation_ref'],
            'case': options['case'], 'automatic_retry': False})
        try:
            result = self.actor.action(endpoint, operation, payload, **options)
        except BaseException as error:
            self.facts.save(name + '-unconfirmed', {
                'outcome': 'UNCONFIRMED_REQUIRES_INDEPENDENT_RO',
                'error_type': type(error).__name__, 'automatic_retry': False})
            raise
        safe = {key: value for key, value in result.items()
                if (type(value) in (int, float, bool) or value is None)
                and key not in {'password', 'content', 'token', 'editor_token', 'lease_token'}}
        self.facts.save(name + '-returned', {
            'business_ids': safe, 'commit_claimed': False, 'automatic_retry': False})
        return result


def new_c_confirmed_fee(manager, doctor, fixture, facts, *, label, amount, d_source,
                        patient_id=None, schedule_offset=0):
    """Normal S05→S06→S07→S08 path for one independent uncollected C fee.

    All actors must already be switched to this new C clinic. The caller must
    exclude the committed D patient, source, fee and bill from every fixture.
    This helper never bills, collects, refunds, merges or touches the D chain.
    """
    if (not re.fullmatch(r'[a-z][a-z0-9-]{0,24}', label)
            or Decimal(str(amount)) <= 0 or Decimal(str(amount)) > 100
            or type(schedule_offset) is not int or not 0 <= schedule_offset <= 40
            or any(type(d_source.get(key)) is not int or d_source[key] <= 0
                   for key in ('patient_id', 'event_id', 'fee_id', 'invoice_id'))
            or patient_id is not None and (type(patient_id) is not int or patient_id <= 0
                                           or patient_id == d_source['patient_id'])):
        raise ValueError('C_NEW_UPSTREAM_PARAMETERS_INVALID')
    facts.save('C-' + label + '-upstream-in-flight', {
        'store_id': fixture['store_id'], 'company_id': fixture['company_id'],
        'existing_new_c_patient_id': patient_id, 'amount': str(amount),
        'manager_id': manager.uid, 'doctor_id': doctor.uid,
        'd_patient_allowed': False, 'automatic_retry': False})
    manager = CRecordedActor(manager, facts, label + '-manager', fixture)
    doctor = CRecordedActor(doctor, facts, label + '-doctor', fixture)
    now = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)
    fmt = lambda value: value.strftime('%Y-%m-%d %H:%M:%S')
    catalog = manager.action('intake', 'catalog', {
        'code': 'current-c-' + uuid.uuid4().hex, 'name': 'S10 independent C synthetic care',
        'kind': 'care', 'capability_id': fixture['capability_id'], 'uom_id': fixture['uom_id']})
    mapping = manager.action('intake', 'mapping', {
        'catalog_id': catalog['id'], 'area_id': fixture['area_id'],
        'execution_area_id': fixture['area_id']})
    price = manager.action('intake', 'price', {
        'catalog_id': catalog['id'], 'currency_id': fixture['currency_id'],
        'unit_price': amount, 'start': fmt(now - timedelta(minutes=1)),
        'end': fmt(now + timedelta(days=1)), 'reason': 'S10 separate C frozen synthetic price'})
    reviewed = manager.action('intake', 'review', {
        'record_id': price['id'], 'version': price['version'],
        'reason': 'S10 C synthetic price review'})
    manager.action('intake', 'publish', {
        'record_id': reviewed['id'], 'version': reviewed['version'],
        'reason': 'S10 C synthetic price publication'})
    start = now + timedelta(minutes=5 + schedule_offset)
    end = start + timedelta(minutes=4)
    slot = manager.action('supply', 'slot', {
        'station_id': fixture['station_id'], 'start': fmt(start), 'end': fmt(end), 'total': 3,
        'capability_ids': [fixture['capability_id']], 'reason': 'S10 separate C real capacity'})
    manager.action('supply', 'publish', {
        'id': slot['id'], 'version': 1, 'user_ids': [doctor.uid],
        'reason': 'S10 actual qualified C doctor coverage'})
    if patient_id is None:
        patient_id = manager.action('patients', 'create', {
            'values': {'name': 'S10 independent C synthetic ' + label}})['id']
    if patient_id == d_source['patient_id']:
        raise RuntimeError('C_NEW_PATIENT_UNEXPECTEDLY_EQUALS_PROTECTED_D_PATIENT')
    qualified = manager.action('intake', 'reserve', {
        'patient_id': patient_id, 'mapping_id': mapping['id'],
        'start': fmt(start), 'end': fmt(end), 'channel': 'reservation'})
    manager.action('intake', 'arrive', {'patient_id': patient_id})
    manager.action('intake', 'report', {
        'task_id': qualified['task_id'], 'version': qualified['task_version']})
    lease = doctor.action('queue', 'enter', {'station_id': fixture['station_id']})
    held = {'lease_id': lease['lease_id'], 'token': lease['token']}
    called = doctor.action('queue', 'call', held)
    if called['task_id'] != qualified['task_id']:
        raise RuntimeError('C_QUEUE_SELECTED_UNEXPECTED_TASK_NO_SUBSTITUTION')
    execution = doctor.action('queue', 'start', held | {'entry_id': called['entry_id']})
    document = doctor.action('clinical', 'open', {
        'execution_id': execution['execution_id'], 'lease_id': lease['lease_id'],
        'lease_token': lease['token']})
    content = document['content'] | {'chief_complaint': 'S10 separate C synthetic care'}
    saved = doctor.action('clinical', 'save', {
        'document_id': document['document_id'], 'editor_token': document['editor_token'],
        'expected_version': document['version'], 'content': content, 'key': uuid.uuid4().hex})
    event = doctor.action('treatment', 'execute', {
        'execution_id': execution['execution_id'], 'lease_id': lease['lease_id'],
        'lease_token': lease['token'], 'document_id': document['document_id'],
        'document_version': saved['version'], 'catalog_id': catalog['id'], 'quantity': 1,
        'source': 'S10 C independent ' + uuid.uuid4().hex,
        'reason': 'S10 independently performed C synthetic care',
        'materials': [], 'teeth': [], 'already_performed': False, 'policy': 'demo_confirmation'})
    facts.save('C-' + label + '-event-returned', {
        'patient_id': patient_id, 'event_id': event['event_id'], 'fee_id': event['fee_id'],
        'expected_amount': str(amount), 'actual_amount': str(event['amount']),
        'independent_commit_verification_required': True})
    if (Decimal(str(event['amount'])) != Decimal(str(amount))
            or event['fee_id'] == d_source['fee_id'] or event['event_id'] == d_source['event_id']):
        raise RuntimeError('C_FROZEN_SOURCE_AMOUNT_MISMATCH')
    doctor.action('clinical', 'handover', {
        'document_id': document['document_id'], 'editor_token': document['editor_token'],
        'expected_version': saved['version'], 'content': content, 'key': uuid.uuid4().hex,
        'lease_id': lease['lease_id'], 'lease_token': lease['token']})
    doctor.action('queue', 'exit', held)
    source = {key: fixture[key] for key in ('store_id', 'company_id', 'currency_id')}
    source.update(patient_id=patient_id, event_id=event['event_id'], fee_id=event['fee_id'],
        catalog_id=catalog['id'], price_id=price['id'], amount=str(amount),
        task_id=qualified['task_id'], execution_id=execution['execution_id'],
        document_id=document['document_id'], doctor_id=doctor.uid, lease_id=lease['lease_id'])
    facts.save('C-' + label + '-upstream-returned', source | {
        'fund_dispatches': 0, 'billed': False, 'independent_commit_verification_required': True})
    return source


def run_new_c_fixture_flow(manager, doctor, clinics, facts, d_source, *, observe,
                           new_c_confirmed_fee, recorded_actor, store_original):
    """Create separate C sources, never a second persistent funds chain.

    Independent observe(label, source_rows) must preserve the exact D graph and
    prove every C source's patient/event/snapshot/fee/invoice and no extra funds.
    It returns the actual-current manifest for subsequent normal reader cells.
    """
    if ([item['label'] for item in clinics] != ['local', 'same-company', 'other-company']
            or clinics[0]['company_id'] != clinics[1]['company_id']
            or clinics[0]['company_id'] == clinics[2]['company_id']
            or any(item['store_id'] == d_source['store_id'] for item in clinics)):
        raise RuntimeError('C_THREE_NEW_INDEPENDENT_CLINICS_REQUIRED')
    facts.save('C-SCRATCH-SOURCES-IN-FLIGHT', {
        'd_patient_id': d_source['patient_id'], 'd_fee_id': d_source['fee_id'],
        'd_invoice_id': d_source['invoice_id'], 'clinics': clinics,
        'fund_actions_allowed': False, 'automatic_retry': False})
    switch_step = 0
    def switch(actor, clinic):
        nonlocal switch_step
        switch_step += 1
        name = 'C-scope-switch-%02d' % switch_step
        facts.save(name + '-intent', {'actor_id': actor.uid, 'store_id': clinic['store_id'],
            'previous_store_id': actor.store_id, 'revision_before': actor.revision,
            'operation_ref': 'switch', 'automatic_retry': False})
        actor.refresh()
        revision = actor.switch(clinic['store_id'])
        facts.save(name + '-returned', {'actor_id': actor.uid, 'store_id': actor.store_id,
            'revision': revision, 'request_id': actor.scope_request_id})
    local, same_company, other_company = clinics
    switch(manager, local)
    switch(doctor, local)
    fee_a = new_c_confirmed_fee(manager, doctor, local, facts, label='family-source',
        amount=7, d_source=d_source, schedule_offset=0)
    fee_b = new_c_confirmed_fee(manager, doctor, local, facts, label='family-target',
        amount=11, d_source=d_source, schedule_offset=6)
    rows = [fee_a, fee_b]
    observe('two-separate-unbilled-patients', rows)
    local_manager = recorded_actor(manager, facts, 'local-post-care', local)
    # Valid nonempty same-store fees, different current patients and no prior
    # source: native _same_patient guard must be the actual refusal.
    mixed_key = uuid.uuid4().hex
    mixed = local_manager.action('settlement', 'bill', {
        'fee_ids': [fee_a['fee_id'], fee_b['fee_id']], 'discount': 0, 'reason': ''},
        key=mixed_key, expect=(403,), operation_ref='current-C-mixed-new-patients')
    facts.save('C-mixed-patient-bill-refusal', {
        'actor_id': manager.uid, 'store_id': local['store_id'],
        'fee_ids': [fee_a['fee_id'], fee_b['fee_id']], 'stable_key': mixed_key,
        'expected_native_message_match': mixed.get('error') ==
            'access_denied: Mixed patient fees cannot be billed.',
        'operation_ref': 'current-C-mixed-new-patients',
        'denial_layer_claimed': 'REAL_HTTP_PRODUCT_SCOPE_GUARD_PENDING_NATIVE_CORRELATION'})
    if mixed.get('error') != 'access_denied: Mixed patient fees cannot be billed.':
        raise RuntimeError('C_MIXED_FEES_DID_NOT_HIT_NATIVE_SAME_PATIENT_GUARD')
    observe('mixed-refused-no-C-invoice-or-source', rows)
    for label, source in [('source', fee_a), ('target', fee_b)]:
        billed = local_manager.action('settlement', 'bill', {
            'fee_ids': [source['fee_id']], 'discount': 0, 'reason': ''},
            operation_ref='current-C-family-' + label + '-bill')
        source['invoice_id'] = billed['invoice_id']
        facts.save('C-family-' + label + '-bill-returned', {
            **source, 'no_payment_or_refund_dispatched': True,
            'independent_commit_verification_required': True})
        observe('family-' + label + '-unpaid-invoice', rows)
        if label == 'source':
            # Normal native original creation before the synthetic merge gives
            # a real nonempty immutable file whose old identity/bytes must be
            # retained when the new target family subsequently reads it.
            source['original_expected'] = True
            original = store_original(manager, source, label='family-source-before-merge')
            source.update(original)
            facts.save('C-family-source-original-committed', {
                'invoice_id': source['invoice_id'], **original,
                'original_patient_id': source['patient_id'], 'new_render_after_merge_allowed': False})
            observe('new-C-original-before-family-merge', rows)
    requested = local_manager.action('patients', 'request_merge', {
        'source_id': fee_a['patient_id'], 'target_id': fee_b['patient_id'],
        'reason': 'S10 explicit verification of two independent synthetic C identities'},
        operation_ref='current-C-new-patients-family-request')
    merged = local_manager.action('patients', 'confirm', {
        'request_id': requested['id'], 'version': requested['version'],
        'reason': 'S10 verified synthetic C family only; no D identity or funds'},
        operation_ref='current-C-new-patients-family-confirm')
    facts.save('C-new-family-confirmed-returned', {
        'merge_id': requested['id'], 'source_patient_id': fee_a['patient_id'],
        'target_patient_id': fee_b['patient_id'], 'result_patient_id': merged.get('patient_id'),
        'state_is_accepted': merged.get('result') == 'accepted',
        'expected_source_invoice_id': fee_a['invoice_id'],
        'expected_target_invoice_id': fee_b['invoice_id'],
        'old_D_patient_excluded': True, 'independent_commit_verification_required': True})
    if merged.get('result') != 'accepted' or merged.get('patient_id') != fee_b['patient_id']:
        raise RuntimeError('C_NEW_SYNTHETIC_FAMILY_MERGE_NOT_CONFIRMED')
    observe('new-family-source-financial-ownership-preserved', rows)
    unrelated = new_c_confirmed_fee(manager, doctor, local, facts, label='unrelated',
        amount=13, d_source=d_source, schedule_offset=12)
    rows.append(unrelated)
    billed = local_manager.action('settlement', 'bill', {
        'fee_ids': [unrelated['fee_id']], 'discount': 0, 'reason': ''},
        operation_ref='current-C-unrelated-nonempty-bill')
    unrelated['invoice_id'] = billed['invoice_id']
    observe('unrelated-new-C-patient-unpaid-invoice', rows)
    log_fee = new_c_confirmed_fee(manager, doctor, local, facts, label='log-unbilled',
        amount=17, d_source=d_source, patient_id=fee_b['patient_id'], schedule_offset=18)
    rows.append(log_fee)
    observe('new-C-log-unbilled-fee', rows)
    for clinic, amount, label in [(same_company, 19, 'same-company'),
                                   (other_company, 23, 'other-company')]:
        switch(manager, clinic)
        switch(doctor, clinic)
        source = new_c_confirmed_fee(manager, doctor, clinic, facts, label=label,
            amount=amount, d_source=d_source, patient_id=fee_b['patient_id'])
        rows.append(source)
        actor = recorded_actor(manager, facts, label + '-post-care', clinic)
        billed = actor.action('settlement', 'bill', {
            'fee_ids': [source['fee_id']], 'discount': 0, 'reason': ''},
            operation_ref='current-C-' + label + '-nonempty-unpaid-bill')
        source['invoice_id'] = billed['invoice_id']
        facts.save('C-' + label + '-bill-returned', {
            **source, 'no_payment_or_refund_dispatched': True,
            'independent_commit_verification_required': True})
        observe('new-C-' + label + '-native-unpaid-bill', rows)
        if label == 'other-company':
            source['original_expected'] = True
            original = store_original(manager, source, label='other-company-own-positive')
            source.update(original)
            facts.save('C-other-company-original-committed', {
                'invoice_id': source['invoice_id'], **original,
                'company_id': source['company_id'], 'ordinary_actor_id': manager.uid})
            observe('new-C-other-company-original-own-positive', rows)
    switch(manager, local)
    mixed_manager = recorded_actor(manager, facts, 'cross-scope-mixed', local)
    for label, foreign in [('same-company', rows[-2]), ('other-company', rows[-1])]:
        rejected = mixed_manager.action('settlement', 'bill', {
            'fee_ids': [log_fee['fee_id'], foreign['fee_id']], 'discount': 0, 'reason': ''},
            expect=(403,), operation_ref='current-C-mixed-store-' + label)
        exact = rejected.get('error') == 'access_denied: Select a confirmed fee in this store.'
        facts.save('C-mixed-store-' + label + '-refusal', {
            'actor_id': manager.uid, 'selected_store_id': local['store_id'],
            'local_unbilled_fee_id': log_fee['fee_id'], 'foreign_fee_id': foreign['fee_id'],
            'foreign_store_id': foreign['store_id'], 'foreign_company_id': foreign['company_id'],
            'ordinary_actor_legally_assigned_both_stores': True,
            'expected_native_message_match': exact,
            'operation_ref': 'current-C-mixed-store-' + label,
            'denial_layer_claimed': 'REAL_HTTP_PRODUCT_SCOPE_GUARD_PENDING_NATIVE_CORRELATION'})
        if not exact:
            raise RuntimeError('C_MIXED_FOREIGN_FEE_DID_NOT_HIT_NATIVE_CURRENT_STORE_GUARD')
        observe('mixed-store-' + label + '-refused-no-economic-change', rows)
    final = observe('C-independent-new-financial-sources-complete', rows)
    facts.save('C-SCRATCH-SOURCES-RETURNED', {
        'sources': rows, 'family_source_patient_id': fee_a['patient_id'],
        'family_target_patient_id': fee_b['patient_id'], 'unrelated_patient_id': unrelated['patient_id'],
        'unbilled_log_fee_id': log_fee['fee_id'], 'fund_dispatches': 0,
        'd_patient_id': d_source['patient_id'], 'd_fee_id': d_source['fee_id'],
        'normal_sources_independent_verification_complete': bool(final)})
    return rows, final


def c_source_selections(schema, *, d_selection, profile):
    selected = d_selection(schema, profile=profile)
    for entry in selected:
        if entry['table'] == 'account_move':
            if 'create_uid' not in {row['column'] for row in schema['account_move']}:
                raise RuntimeError('C_CURRENT_NATIVE_INVOICE_CREATOR_SCHEMA_REQUIRED')
            entry['columns'].append('create_uid')
        if entry['table'] in {'ydental_treatment_fee', 'ydental_treatment_event',
                              'ydental_intake_snapshot', 'ydental_settlement_source'}:
            entry.update(columns=[row['column'] for row in schema[entry['table']]], row_digest=True)
    additions = {
        'ydental_patient': 'id active ydental_merged_into_id ydental_partner_id ydental_store_id ydental_version',
        'ydental_patient_relation': 'id ydental_patient_id ydental_store_id ydental_superseded_by_id',
        'res_partner': 'id company_id ydental_patient_owner_id',
        'ydental_access_store': 'id name company_id ydental_timezone',
        'res_company': 'id name currency_id chart_template',
        'res_currency': 'id name',
        'ydental_access_session': 'id ydental_user_id ydental_store_id ydental_revision',
        'ydental_settlement_bill_original': 'id invoice_id patient_id store_id company_id currency_id actor_id version previous_id source_sha256 template_sha256 pdf_sha256 attachment_id',
        'ir_attachment': 'id res_model res_id company_id public mimetype file_size checksum',
    }
    for table, fields in additions.items():
        columns = fields.split()
        if table not in schema or not set(columns) <= {row['column'] for row in schema[table]}:
            raise RuntimeError('C_CURRENT_INDEPENDENT_PROJECTION_SCHEMA_MISSING')
        entry = {'table': table, 'columns': columns, 'order': ['id'], 'row_digest': True}
        if table == 'ir_attachment':
            entry['null_columns'] = ['access_token']
            entry['row_digest'] = False
        if table == 'ydental_access_session':
            entry['row_digest'] = False
        selected.append(entry)
    if (not {'attachment_id', 'message_id'} <= {
            row['column'] for row in schema.get('message_attachment_rel', [])}):
        raise RuntimeError('C_CURRENT_LEGAL_TOKEN_RELATION_SCHEMA_MISSING')
    selected.append({'table': 'message_attachment_rel', 'columns': ['attachment_id', 'message_id'],
                     'order': ['attachment_id', 'message_id']})
    return selected


def verify_c_sources(directory, rows, d_source, *, stored_rows, verify_d, profile,
                     immutable_billed=None):
    """Use actual rows/edges and globally unique D funds, never a passed-ID waiver."""
    protection = verify_d(directory, d_source, state='done', actual_refund=2, profile=profile,
        additional_unpaid_fee_ids=tuple(row['fee_id'] for row in rows))
    tables = {name: {row['id']: row for row in stored_rows(directory, name)} for name in (
        'ydental_treatment_fee', 'ydental_treatment_event', 'ydental_intake_snapshot',
        'ydental_settlement_source', 'account_move', 'account_move_line',
        'ydental_patient', 'res_partner', 'ydental_settlement_bill_original', 'ir_attachment')}
    fees = tables['ydental_treatment_fee']
    sources = tables['ydental_settlement_source']
    actual_originals, actual_rows = [], []
    immutable_billed = immutable_billed if immutable_billed is not None else {}
    expected_original_invoice_ids = set()
    for claimed in rows:
        fee = fees.get(claimed['fee_id'])
        event = tables['ydental_treatment_event'].get(claimed['event_id'])
        if (not fee or not event or fee['ydental_event_id'] != event['id']
                or event['state'] != 'confirmed' or fee['ydental_patient_id'] != claimed['patient_id']
                or event['ydental_patient_id'] != claimed['patient_id']
                or event['ydental_catalog_id'] != claimed['catalog_id']
                or fee['ydental_store_id'] != claimed['store_id']
                or event['ydental_store_id'] != claimed['store_id']
                or fee['ydental_currency_id'] != claimed['currency_id']
                or Decimal(str(fee['ydental_amount'])) != Decimal(claimed['amount'])
                or fee['ydental_quantity'] != 1 or fee['ydental_unit_price'] != fee['ydental_amount']
                or claimed['patient_id'] == d_source['patient_id']
                or claimed['event_id'] == d_source['event_id'] or claimed['fee_id'] == d_source['fee_id']):
            raise RuntimeError('C_NORMAL_EVENT_PATIENT_FEE_RELATION_OR_D_SEPARATION_NOT_PROVEN')
        snapshot = tables['ydental_intake_snapshot'].get(fee['ydental_price_snapshot_id'])
        if (not snapshot or event['ydental_price_snapshot_id'] != snapshot['id']
                or snapshot['ydental_price_id'] != claimed['price_id']
                or snapshot['ydental_catalog_id'] != claimed['catalog_id']
                or snapshot['ydental_currency_id'] != claimed['currency_id']
                or Decimal(str(snapshot['ydental_amount'])) != Decimal(claimed['amount'])
                or snapshot['ydental_unit_price'] != snapshot['ydental_amount']
                or snapshot['ydental_quantity'] != 1):
            raise RuntimeError('C_NORMAL_FROZEN_PRICE_SOURCE_NOT_PROVEN')
        linked = [row for row in sources.values() if row['ydental_fee_id'] == fee['id']]
        invoice = None
        if 'invoice_id' not in claimed:
            if linked:
                raise RuntimeError('C_EXPLICIT_UNBILLED_FEE_ALREADY_HAS_SOURCE')
        else:
            invoice = tables['account_move'].get(claimed['invoice_id'])
            patient = tables['ydental_patient'].get(claimed['patient_id'])
            partner = tables['res_partner'].get(patient['ydental_partner_id']) if patient else None
            if (len(linked) != 1 or not invoice or not partner
                    or invoice['id'] == d_source['invoice_id']
                    or invoice['company_id'] != claimed['company_id']
                    or invoice['currency_id'] != claimed['currency_id']
                    or invoice['partner_id'] != partner['id']
                    or partner['ydental_patient_owner_id'] != claimed['patient_id']
                    or invoice['state'] != 'posted' or invoice['move_type'] != 'out_invoice'
                    or Decimal(str(invoice['amount_total'])) != Decimal(claimed['amount'])
                    or invoice['amount_residual'] != invoice['amount_total']
                    or linked[0]['ydental_invoice_id'] != invoice['id']
                    or linked[0]['ydental_store_id'] != claimed['store_id']
                    or linked[0]['ydental_patient_id'] != claimed['patient_id']
                    or linked[0]['ydental_original_amount'] != fee['ydental_amount']
                    or linked[0]['ydental_discount'] != 0
                    or linked[0]['ydental_currency_id'] != claimed['currency_id']
                    or linked[0]['ydental_price_version'] != 'S05:' + str(claimed['price_id'])):
                raise RuntimeError('C_EXPLICIT_NATIVE_UNPAID_BILL_OR_ORIGINAL_FINANCIAL_OWNER_NOT_PROVEN')
            line = tables['account_move_line'].get(linked[0]['ydental_line_id'])
            if (not line or line['move_id'] != invoice['id'] or line['quantity'] != 1
                    or line['price_subtotal'] != fee['ydental_amount']):
                raise RuntimeError('C_EXPLICIT_NATIVE_INVOICE_FEE_LINE_NOT_PROVEN')
            # Each old billed source stays byte-for-byte the same through later
            # C family merge, scope changes, reads and new independent C bills.
            digest = {name: record['__row_sha256'] for name, record in (
                ('fee', fee), ('event', event), ('snapshot', snapshot),
                ('source', linked[0]), ('invoice', invoice), ('partner', partner))}
            previous = immutable_billed.setdefault(fee['id'], digest)
            if previous != digest:
                raise RuntimeError('C_BILLED_SOURCE_OR_FINANCIAL_OWNER_MUTATED_BY_LATER_C_ACTION')
        originals = [row for row in tables['ydental_settlement_bill_original'].values()
                     if row['invoice_id'] == claimed.get('invoice_id')]
        if claimed.get('original_expected') is True:
            expected_original_invoice_ids.add(claimed['invoice_id'])
        if bool(originals) != bool(claimed.get('original_expected')):
            raise RuntimeError('C_EXPLICIT_ORIGINAL_CREATION_EXPECTATION_MISMATCH')
        if originals:
            if len(originals) != 1:
                raise RuntimeError('C_NEW_SYNTHETIC_ORIGINAL_NOT_UNIQUE')
            original = originals[0]
            attachment = tables['ir_attachment'].get(original['attachment_id'])
            if (original['version'] != 1 or original['previous_id'] is not None
                    or original['patient_id'] != claimed['patient_id']
                    or original['store_id'] != claimed['store_id']
                    or original['company_id'] != claimed['company_id']
                    or original['currency_id'] != claimed['currency_id']
                    or not attachment or attachment['res_model'] != 'ydental.settlement.bill.original'
                    or attachment['res_id'] != original['id'] or attachment['public']
                    or attachment['company_id'] != claimed['company_id']
                    or not attachment['access_token_is_null'] or attachment['mimetype'] != 'application/pdf'
                    or any(link['attachment_id'] == attachment['id'] for link in stored_rows(
                        directory, 'message_attachment_rel'))):
                raise RuntimeError('C_NEW_ORIGINAL_ATTACHMENT_OR_LEGAL_TOKEN_RELATION_INVALID')
            if ('original_id' in claimed and (original['id'] != claimed['original_id']
                    or original['pdf_sha256'] != claimed['pdf_sha256']
                    or original['attachment_id'] != claimed['attachment_id'])):
                raise RuntimeError('C_PREMERGE_ORIGINAL_ID_OR_BYTES_CHANGED')
            original_digest = {'original': original['__row_sha256'],
                               'attachment_metadata': hashlib.sha256(json.dumps(
                                   attachment, sort_keys=True, ensure_ascii=True).encode()).hexdigest()}
            previous = immutable_billed.setdefault(('original', original['id']), original_digest)
            if previous != original_digest:
                raise RuntimeError('C_PREMERGE_ORIGINAL_OR_ATTACHMENT_MUTATED')
            actual_originals.append(original)
        invoice_safe = None if not invoice else {
            key: (str(value) if key in {'amount_total', 'amount_residual'} else value)
            for key, value in invoice.items()}
        actual_rows.append(dict(claimed, **({'source_id': linked[0]['id'], 'invoice': invoice_safe} if invoice else {})))
    if {row['invoice_id'] for row in tables['ydental_settlement_bill_original'].values()} != expected_original_invoice_ids:
        raise RuntimeError('C_UNEXPLAINED_SYNTHETIC_ORIGINAL_OUTSIDE_EXPLICIT_NEW_BILLS')
    return {'validation_status': 'CURRENT_C_NORMAL_SOURCES_AND_UNIQUE_D_FUNDS_INDEPENDENTLY_OBSERVED',
        'source_rows': actual_rows, 'originals': actual_originals,
        'D_native_accounting': protection, 'evidence_layer': 'INDEPENDENT_COMMITTED_RO',
        'no_new_C_funds': True, 'scope_manifest_requires_actual_patient_relations': True}


def check_c_nonempty_workbench(reader, facts, label, expected, *, stop):
    """Record minimal nonsecret facts BEFORE any disclosure assertion can stop."""
    from lxml import etree, html
    response = reader.client.request('GET', '/ydental/settlement?patient_id=%d' % expected['patient_id'],
        case_id='C-SCOPE', operation_ref='C-' + label + '-workbench')
    row = {'actor_id': reader.uid, 'store_id': expected['store_id'],
        'company_id': expected['company_id'], 'patient_id': expected['patient_id'],
        'request_id': response.request_id, 'http_status': response.status,
        'body_sha256': hashlib.sha256(response.body).hexdigest(), 'raw_body_retained': False,
        'expected_invoice_ids': sorted(item['id'] for item in expected['invoices']),
        'expected_fee_ids': sorted(expected['unbilled_fee_ids']),
        'actual_ids': {}, 'financial_rows_match': False}
    invoices = {item['id']: item for item in expected['invoices']}
    actual = {kind: set() for kind in ('invoice', 'fee', 'event', 'payment', 'refund', 'close')}
    matched = []
    parse_failure = None
    try:
        tree = html.fromstring(response.body)
        for heading in ('今日未出账费用', '历史未出账费用'):
            actual['fee'].update(int(value.strip()) for value in tree.xpath(
                '//section[h2[text()=$heading]]//tbody/tr/td[1]/text()', heading=heading) if value.strip())
        actual['event'].update(int(value.strip()) for value in tree.xpath(
            '//section[h2[text()="待核对，禁止出账"]]//tbody/tr/td[1]/text()') if value.strip())
        # All these isolated C bills remain unpaid; a settled row is unexpected.
        settled = tree.xpath('//section[@name="settled-bills"]//tbody/tr')
        for tr in tree.xpath('//section[h2[text()="已出账未付清"]]//tbody/tr'):
            links = [match for value in tr.xpath('.//a/@href') if (match := re.fullmatch(
                r'/ydental/settlement/pdf/bill/(\d+)', value))]
            cells = [''.join(cell.itertext()).strip() for cell in tr.xpath('./td')]
            identifier = int(links[0][1]) if len(links) == 1 else None
            if identifier is not None:
                actual['invoice'].add(identifier)
            selected = invoices.get(identifier)
            matched.append(bool(selected and len(cells) >= 4 and cells[0] == selected['name']
                and Decimal(cells[2].replace(',', '')) == Decimal(str(selected['amount_total']))
                and Decimal(cells[3].replace(',', '')) == Decimal(str(selected['amount_residual']))))
        for href in tree.xpath('//a/@href'):
            match = re.fullmatch(r'/ydental/settlement/pdf/(receipt|refund)/(\d+)', href)
            if match:
                actual['payment' if match[1] == 'receipt' else 'refund'].add(int(match[2]))
        for paragraph in tree.xpath('//section[h2[text()="线下付款与退款"]]/div/p'):
            text = ''.join(paragraph.itertext()).strip()
            kind = 'payment' if text.startswith('付款') else 'refund' if text.startswith('退款') else None
            identifiers = paragraph.xpath('./span[1]/text()')
            if kind and identifiers:
                actual[kind].add(int(identifiers[0].strip()))
        actual['close'].update(int(value.strip()) for value in tree.xpath(
            '//section[h2[text()="收费员日结"]]/div/p/span[1]/text()') if value.strip())
        row.update(actual_ids={key: sorted(value) for key, value in actual.items()},
                   financial_rows_match=bool(matched) and all(matched),
                   settled_row_count=len(settled), invoice_row_count=len(matched))
    except (ValueError, TypeError, ArithmeticError, etree.ParserError, etree.XMLSyntaxError) as error:
        parse_failure = type(error).__name__
        row.update(parse_failure=parse_failure, actual_ids={key: sorted(value) for key, value in actual.items()})
    facts.save('C-' + label + '-workbench-minimal', row)
    if (response.status != 200 or parse_failure or row.get('settled_row_count') != 0
            or not row['financial_rows_match'] or len(matched) != len(invoices)
            or actual['invoice'] != set(invoices)
            or actual['fee'] != set(expected['unbilled_fee_ids'])
            or any(actual[key] for key in ('event', 'payment', 'refund', 'close'))):
        stop('C_SYNTHETIC_WORKBENCH_SCOPE_OR_CONTENT_MISMATCH',
             request_id=response.request_id, evidence='C-' + label + '-workbench-minimal.json')
        raise RuntimeError('C_SYNTHETIC_WORKBENCH_SCOPE_OR_CONTENT_MISMATCH')
    return row


def check_c_nonempty_summary(reader, facts, label, expected, *, stop):
    response = reader.client.request('GET', '/ydental/settlement/other-stores/%d' % expected['patient_id'],
        case_id='C-SCOPE', operation_ref='C-' + label + '-summary')
    allowed_keys = {'store', 'store_id', 'company', 'currency', 'residual'}
    body = None
    parse_failure = None
    try:
        body = response.json()
    except (ValueError, TypeError) as error:
        parse_failure = type(error).__name__
    shape_ok = type(body) is list and all(type(item) is dict and set(item) == allowed_keys for item in body)
    actual_ids = [item.get('store_id') if type(item.get('store_id')) is int else 'INVALID_TYPE'
                  for item in body if type(item) is dict] if type(body) is list else []
    actual_fields = [sorted(item) for item in body if type(item) is dict] if type(body) is list else []
    totals_ok = False
    if shape_ok and len(actual_ids) == len(set(actual_ids)) and 'INVALID_TYPE' not in actual_ids:
        try:
            totals_ok = ({item['store_id']: Decimal(str(item['residual'])) for item in body}
                         == {int(key): Decimal(str(value)) for key, value in expected['summary_residuals'].items()})
        except (ValueError, TypeError, ArithmeticError) as error:
            parse_failure = type(error).__name__
    metadata_ok = bool(shape_ok) and all(
        all(item.get(key) == value for key, value in expected.get('summary_metadata', {}).get(str(item['store_id']), {}).items())
        and str(item['store_id']) in expected.get('summary_metadata', {}) for item in body)
    row = {'actor_id': reader.uid, 'store_id': expected['store_id'],
        'company_id': expected['company_id'], 'request_id': response.request_id,
        'http_status': response.status, 'body_sha256': hashlib.sha256(response.body).hexdigest(),
        'raw_body_retained': False, 'actual_store_ids': actual_ids,
        'expected_store_ids': sorted(int(key) for key in expected['summary_residuals']),
        'actual_field_sets': actual_fields, 'strict_summary_shape': shape_ok,
        'synthetic_expected_totals_match': totals_ok, 'actual_store_company_currency_labels_match': metadata_ok,
        'parse_failure': parse_failure}
    facts.save('C-' + label + '-summary-minimal', row)
    if (response.status != 200 or not shape_ok or not totals_ok or not metadata_ok or not actual_ids):
        stop('C_SYNTHETIC_NONEMPTY_SUMMARY_SCOPE_OR_SHAPE_MISMATCH',
             request_id=response.request_id, evidence='C-' + label + '-summary-minimal.json')
        raise RuntimeError('C_SYNTHETIC_NONEMPTY_SUMMARY_SCOPE_OR_SHAPE_MISMATCH')
    return row


def check_c_foreign_target_denied(reader, facts, label, *, path, kind, target_id, stop):
    """The caller has independently proven this target and a valid own scope."""
    response = reader.client.request('GET', path, case_id='C-SCOPE',
        operation_ref='C-' + label + '-foreign-' + kind)
    row = {'actor_id': reader.uid, 'request_id': response.request_id,
        'foreign_target_id': target_id, 'route_kind': kind, 'http_status': response.status,
        'body_sha256': hashlib.sha256(response.body).hexdigest(),
        'protected_pdf_returned': response.body.startswith(b'%PDF-'), 'raw_body_retained': False}
    facts.save('C-' + label + '-foreign-' + kind + '-minimal', row)
    if response.status != 403 or row['protected_pdf_returned']:
        stop('C_SYNTHETIC_FOREIGN_TARGET_NOT_DENIED', request_id=response.request_id,
             evidence='C-' + label + '-foreign-' + kind + '-minimal.json')
        raise RuntimeError('C_SYNTHETIC_FOREIGN_TARGET_NOT_DENIED')
    return row


def current_c_read_manifest(directory, source_rows, clinics):
    """Project real committed C relationships into the expected read-only cells."""
    patients = {row['id']: row for row in stored_rows(directory, 'ydental_patient')}
    stores = {row['id']: row for row in stored_rows(directory, 'ydental_access_store')}
    companies = {row['id']: row for row in stored_rows(directory, 'res_company')}
    currencies = {row['id']: row for row in stored_rows(directory, 'res_currency')}
    links = stored_rows(directory, 'ydental_settlement_source')
    moves = {row['id']: row for row in stored_rows(directory, 'account_move')}
    relations = stored_rows(directory, 'ydental_patient_relation')
    original_source, target_source, unrelated, log_fee = source_rows[:4]
    source_patient, target = original_source['patient_id'], target_source['patient_id']
    if (len(source_rows) != 6 or patients[source_patient]['active']
            or patients[source_patient]['ydental_merged_into_id'] != target
            or not patients[target]['active'] or patients[target]['ydental_merged_into_id'] is not None
            or log_fee['patient_id'] != target):
        raise RuntimeError('C_ACTUAL_NEW_FAMILY_MERGE_RELATION_NOT_PROVEN')
    family = {source_patient, target}
    family_bills = {}
    for link in links:
        if link['ydental_patient_id'] in family:
            family_bills.setdefault(link['ydental_store_id'], set()).add(link['ydental_invoice_id'])
    cells = []
    for clinic in clinics:
        store_id = clinic['store_id']
        store = stores[store_id]
        if (store['company_id'] != clinic['company_id']
                or not any(row['ydental_patient_id'] == target and row['ydental_store_id'] == store_id
                           and row['ydental_superseded_by_id'] is None for row in relations)):
            raise RuntimeError('C_ACTUAL_CANONICAL_PATIENT_CURRENT_STORE_RELATION_NOT_PROVEN')
        own = [moves[identifier] for identifier in sorted(family_bills.get(store_id, set()))]
        if not own:
            raise RuntimeError('C_NONEMPTY_OWN_FAMILY_INVOICE_CONTROL_MISSING')
        residuals, metadata = {}, {}
        for other, identifiers in family_bills.items():
            if other == store_id:
                continue
            other_store = stores[other]
            company = companies[other_store['company_id']]
            residuals[str(other)] = str(sum((moves[identifier]['amount_residual'] for identifier in identifiers), Decimal(0)))
            metadata[str(other)] = {'store': other_store['name'], 'company': company['name'],
                                   'currency': currencies[company['currency_id']]['name']}
        cells.append({'label': clinic['label'], 'store_id': store_id, 'store_name': store['name'],
            'company_id': clinic['company_id'], 'patient_id': target,
            'invoices': [{key: (str(value) if key in {'amount_total', 'amount_residual'} else value)
                          for key, value in move.items()} for move in own],
            'unbilled_fee_ids': [log_fee['fee_id']] if clinic['label'] == 'local' else [],
            'summary_residuals': residuals, 'summary_metadata': metadata})
    foreign = source_rows[-1]
    if any(key not in original_source or key not in foreign for key in ('original_id', 'attachment_id', 'pdf_sha256')):
        raise RuntimeError('C_REAL_LOCAL_AND_OTHER_COMPANY_ORIGINAL_CONTROLS_REQUIRED')
    unrelated_invoice = moves[unrelated['invoice_id']]
    unrelated_cell = {'store_id': clinics[0]['store_id'], 'company_id': clinics[0]['company_id'],
        'patient_id': unrelated['patient_id'], 'unbilled_fee_ids': [],
        'invoices': [{key: (str(value) if key in {'amount_total', 'amount_residual'} else value)
                      for key, value in unrelated_invoice.items()}]}
    return {'cells': cells, 'family_ids': sorted(family), 'canonical_patient_id': target,
        'unrelated': unrelated_cell, 'local_original': original_source,
        'other_company_original': foreign, 'all_C_fee_ids': [row['fee_id'] for row in source_rows],
        'valid_token': 'N/A_NO_LEGAL_ISSUER_FOR_TYPED_SETTLEMENT_ORIGINAL',
        'legal_issuer_basis': 'actual access_token NULL + no mail attachment relationship; no portal.mixin producer'}


def run_current_c_read_cells(reader, facts, manifest, d_source, *, profile, stop, source_ref, source_sha256):
    """Real nonempty family, other-store/company, summary and attachment reads."""
    def halt(reason, **metadata):
        return stop(reason, profile=profile, **metadata)
    def authorized_pdf(label, source, *, original):
        path = ('/ydental/settlement/bill-original/%d' % source['original_id'] if original else
                '/ydental/settlement/pdf/bill/%d' % source['invoice_id'])
        facts.save('C-' + label + '-authorized-pdf-intent', {
            'actor_id': reader.uid, 'store_id': reader.store_id,
            'invoice_id': source['invoice_id'], 'original_id': source.get('original_id') if original else None,
            'stored_original_regeneration': False, 'automatic_retry': False})
        response = reader.client.request('GET', path, case_id='C-ATTACHMENT',
            artifact_kind='pdf', operation_ref='C-' + label + '-authorized-pdf')
        digest = hashlib.sha256(response.body).hexdigest()
        result = {'actor_id': reader.uid, 'store_id': reader.store_id,
            'request_id': response.request_id, 'status': response.status,
            'bytes': len(response.body), 'pdf_magic': response.body.startswith(b'%PDF-'),
            'pdf_content_type': response.headers.get('content-type', '').split(';')[0] == 'application/pdf',
            'sha256': digest, 'artifact_ref': response.metadata.get('artifact_ref'),
            'same_original_bytes': digest == source['pdf_sha256'] if original else None,
            'every_page_review': 'PENDING_INDEPENDENT_REVIEW', 'stored_original_regenerated': False}
        facts.save('C-' + label + '-authorized-pdf-returned', result)
        if (response.status != 200 or not result['pdf_magic'] or not result['pdf_content_type']
                or original and not result['same_original_bytes']):
            halt('C_AUTHORIZED_ORIGINAL_OR_DYNAMIC_REPORT_FAILED', request_id=response.request_id)
            raise RuntimeError('C_AUTHORIZED_ORIGINAL_OR_DYNAMIC_REPORT_FAILED')
        return result
    for cell in manifest['cells']:
        label = cell['label']
        facts.save('C-' + label + '-reader-switch-intent', {
            'actor_id': reader.uid, 'store_id': cell['store_id'], 'automatic_retry': False})
        reader.refresh()
        reader.switch(cell['store_id'])
        info_response = reader.client.request('POST', '/web/session/get_session_info',
            json_body={'jsonrpc': '2.0', 'id': uuid.uuid4().hex, 'method': 'call', 'params': {}},
            case_id='C-SCOPE', operation_ref='C-' + label + '-native-session')
        info_response.require_status(200)
        info = info_response.json()['result']
        identity = {key: info.get(key) for key in ('uid', 'db', 'is_admin', 'is_system', 'is_internal_user')}
        identity.update(request_id=info_response.request_id, switch_request_id=reader.scope_request_id,
            revision=info.get('user_context', {}).get('ydental_revision'),
            store_name_matches_independent_source=info.get('ydental_store_name') == cell['store_name'],
            selected_store_id=cell['store_id'])
        facts.save('C-' + label + '-native-session', identity)
        if (identity['uid'] != reader.uid or identity['db'] != profile.database
                or identity['is_admin'] is not False or identity['is_system'] is not False
                or identity['is_internal_user'] is not True or identity['revision'] != reader.revision
                or not identity['store_name_matches_independent_source']):
            raise RuntimeError('C_NATIVE_CURRENT_SESSION_IDENTITY_SCOPE_NOT_PROVEN')
        check_c_nonempty_workbench(reader, facts, label + '-family', cell, stop=halt)
        check_c_nonempty_summary(reader, facts, label, cell, stop=halt)
        local = manifest['local_original']
        foreign = manifest['other_company_original']
        if label == 'local':
            check_c_nonempty_workbench(reader, facts, 'unrelated-local-positive', manifest['unrelated'], stop=halt)
            authorized_pdf('family-premerge-original', local, original=True)
            target = foreign
        elif label == 'other-company':
            authorized_pdf('other-company-own-original', foreign, original=True)
            authorized_pdf('other-company-own-dynamic', foreign, original=False)
            target = local
        else:
            target = local
        check_c_foreign_target_denied(reader, facts, label,
            path='/ydental/settlement/bill-original/%d' % target['original_id'],
            kind='original', target_id=target['original_id'], stop=halt)
        check_c_foreign_target_denied(reader, facts, label,
            path='/ydental/settlement/pdf/bill/%d' % target['invoice_id'],
            kind='bill', target_id=target['invoice_id'], stop=halt)
        # Nonempty receipt/refund controls exist only on the one D chain. These
        # are read-only valid foreign-scope denials, never another fund fixture.
        for kind, identifier in [('receipt', d_source['payment_id']), ('refund', d_source['refund_id'])]:
            check_c_foreign_target_denied(reader, facts, label,
                path='/ydental/settlement/pdf/%s/%d' % (kind, identifier),
                kind=kind, target_id=identifier, stop=halt)
        if label == 'other-company':
            # The native report route must independently reject a real foreign
            # invoice even when JSON supplies plausible report context/options.
            # An opaque in-process SettlementPdfScope cannot be issued by JSON.
            with reader.client.current_c_target(source_ref=source_ref, source_sha256=source_sha256,
                    invoice_id=local['invoice_id'], actor_id=reader.uid, active_store_id=cell['store_id']):
                probes = [('native-html', 'html', {}), ('native-pdf', 'pdf', {}),
                    ('native-pdf-context', 'pdf', {'context': json.dumps(
                        {'ydental_settlement_pdf_scope': {}}, separators=(',', ':'))}),
                    ('native-pdf-options', 'pdf', {'options': json.dumps(
                        {'kind': 'bill', 'source_id': local['invoice_id']}, separators=(',', ':'))})]
                for purpose, converter, query in probes:
                    path = '/report/%s/ydental_settlement.ydental_settlement_pdf/%d' % (converter, local['invoice_id'])
                    if query:
                        path += '?' + urlencode(query)
                    check_c_foreign_target_denied(reader, facts, label, path=path,
                        kind=purpose, target_id=local['invoice_id'], stop=halt)
            from PIL import Image
            placeholder = ROOT.parent / 'addons/web/static/img/placeholder.png'
            for route, suffix in [('content', str(local['attachment_id'])),
                                  ('image', str(local['attachment_id'])),
                                  ('content', 'ir.attachment/%d/raw' % local['attachment_id']),
                                  ('image', 'ir.attachment/%d/raw' % local['attachment_id'])]:
                purpose = 'C-cross-company-native-' + route + ('-model-field' if '/' in suffix else '-id')
                response = reader.client.request('GET', '/web/' + route + '/' + suffix,
                    case_id='C-ATTACHMENT', operation_ref=purpose)
                record = {'actor_id': reader.uid, 'store_id': cell['store_id'],
                    'foreign_attachment_id': local['attachment_id'], 'request_id': response.request_id,
                    'http_status': response.status, 'sha256': hashlib.sha256(response.body).hexdigest(),
                    'pdf_returned': response.body.startswith(b'%PDF-'), 'raw_body_retained': False}
                facts.save(purpose + '-response-minimal', record)
                if record['pdf_returned']:
                    halt('C_CROSS_COMPANY_NATIVE_ATTACHMENT_PDF_LEAK', request_id=response.request_id)
                    raise RuntimeError('C_CROSS_COMPANY_NATIVE_ATTACHMENT_PDF_LEAK')
                same_placeholder = False
                if route == 'image' and response.status == 200:
                    with Image.open(io.BytesIO(response.body)) as image, Image.open(placeholder) as expected:
                        image.load(); expected.load()
                        same_placeholder = image.size == expected.size and image.convert('RGBA').tobytes() == expected.convert('RGBA').tobytes()
                    facts.save(purpose + '-content-semantics', {
                        'request_id': response.request_id, 'actual_placeholder_pixels_match': same_placeholder})
                if response.status not in {403, 404} and not same_placeholder:
                    halt('C_CROSS_COMPANY_NATIVE_ATTACHMENT_NOT_DENIED', request_id=response.request_id)
                    raise RuntimeError('C_CROSS_COMPANY_NATIVE_ATTACHMENT_NOT_DENIED')
    facts.save('C-scratch-read-cells-returned', {
        'scope_cases': [cell['label'] for cell in manifest['cells']],
        'family_ids': manifest['family_ids'], 'canonical_patient_id': manifest['canonical_patient_id'],
        'all_positive_controls_nonempty': True, 'all_C_fund_dispatches': 0,
        'valid_token': manifest['valid_token'], 'independent_acceptance': 'PENDING'})



def run_current_c_error303(manager, facts, observe, rows, *, profile, stop):
    """A valid new manager's empty normal bill form: native error -> 303 notice."""
    from lxml import etree, html
    profile.require_action('LOG-03')
    before = observe('LOG03-before-empty-bill-form', rows)
    page = manager.client.request('GET', '/ydental/settlement', case_id='LOG-03',
        operation_ref='LOG03-valid-manager-bill-form')
    revisions = PageFacts(page.body).revisions if page.status == 200 else set()
    facts.save('LOG03-empty-bill-form-page', {
        'actor_id': manager.uid, 'store_id': manager.store_id,
        'request_id': page.request_id, 'http_status': page.status,
        'body_sha256': hashlib.sha256(page.body).hexdigest(),
        'actual_page_revision_matches_bound_actor': revisions == {manager.revision},
        'raw_body_retained': False})
    page.require_status(200)
    if revisions != {manager.revision}:
        raise RuntimeError('LOG03_NORMAL_FORM_CURRENT_SCOPE_NOT_PROVEN')
    key = uuid.uuid4().hex
    facts.save('LOG03-empty-bill-form-intent', {
        'actor_id': manager.uid, 'store_id': manager.store_id,
        'operation': 'bill', 'selected_fee_count': 0, 'output': 'html',
        'stable_key': key, 'automatic_retry': False,
        'expected_native_exception': 'odoo.exceptions.ValidationError',
        'expected_native_message': 'Select distinct confirmed fee sources.'})
    denied = manager.client.request('POST', '/ydental/settlement/action',
        form={'operation': 'bill', 'revision': manager.revision,
              'csrf_token': csrf_from(page), 'key': key, 'output': 'html',
              'discount': '0', 'reason': ''},
        case_id='LOG-03', operation_ref='LOG03-empty-normal-bill-html')
    location = denied.headers.get('location', '')
    resolved = urlsplit(urljoin(manager.client.base_url + denied.request_path, location))
    query = parse_qs(resolved.query, keep_blank_values=True)
    location_ok = (bool(location) and resolved.scheme + '://' + resolved.netloc == manager.client.base_url
        and resolved.path == '/ydental/settlement' and not resolved.fragment
        and set(query) == {'notice'} and len(query['notice']) == 1 and bool(query['notice'][0]))
    facts.save('LOG03-empty-bill-form-303', {
        'actor_id': manager.uid, 'store_id': manager.store_id,
        'request_id': denied.request_id, 'http_status': denied.status,
        'body_sha256': hashlib.sha256(denied.body).hexdigest(),
        'same_origin_settlement_location': location_ok,
        'location_path': resolved.path, 'location_query_keys': sorted(query),
        'notice_token_present_not_retained': bool(query.get('notice')),
        'product_exception_requires_native_correlation': True})
    if denied.status != 303 or not location_ok:
        stop('LOG03_NORMAL_FORM_ERROR_303_NOT_OBSERVED', profile=profile, request_id=denied.request_id)
        raise RuntimeError('LOG03_NORMAL_FORM_ERROR_303_NOT_OBSERVED')
    notice = manager.client.follow(denied, case_id='LOG-03', operation_ref='LOG03-native-denied-notice')
    messages, parse_failure = [], None
    try:
        tree = html.fromstring(notice.body)
        messages = [''.join(element.itertext()).strip()
                    for element in tree.xpath('//p[@data-ui1-feedback="1"]')]
    except (ValueError, TypeError, etree.ParserError, etree.XMLSyntaxError) as error:
        parse_failure = type(error).__name__
    expected = '请求未完成，请核对权限、门店或输入后重试。'
    notice_ok = messages == [expected]
    facts.save('LOG03-empty-bill-form-denied-notice', {
        'actor_id': manager.uid, 'store_id': manager.store_id,
        'request_id': notice.request_id, 'http_status': notice.status,
        'body_sha256': hashlib.sha256(notice.body).hexdigest(),
        'actual_denied_notice_match': notice_ok, 'message_count': len(messages),
        'parse_failure': parse_failure, 'raw_body_or_notice_token_retained': False})
    after = observe('LOG03-after-empty-bill-form-denial', rows)
    unchanged = before == after
    facts.save('LOG03-empty-bill-form-independent-preservation', {
        'independent_same_committed_C_sources_and_unique_D_funds': unchanged,
        'native_request_id': denied.request_id, 'http_status': denied.status,
        'mandatory_rejected_business_audit_claimed': False,
        'native_rejection_and_normal_view_audits': 'REQUIRES_INDEPENDENT_LOG_AUDIT_CORRELATION'})
    if notice.status != 200 or parse_failure or not notice_ok or not unchanged:
        stop('LOG03_DENIED_NOTICE_OR_NO_BILL_PRESERVATION_FAILED', profile=profile, request_id=notice.request_id)
        raise RuntimeError('LOG03_DENIED_NOTICE_OR_NO_BILL_PRESERVATION_FAILED')


def d_selection(schema=None, *, profile=None):
    if profile is not None:
        if schema is None:
            raise ValueError('CURRENT_D_OBSERVER_SCHEMA_REQUIRED')
        # Actual current schema, restricted to this new synthetic graph. No
        # historical package manifest is used to choose the current columns.
        names = {'ydental_treatment_event', 'ydental_treatment_fee', 'ydental_intake_snapshot',
                 'ydental_settlement_source', 'ydental_settlement_payment', 'ydental_settlement_refund',
                 'ydental_settlement_receipt', 'ydental_settlement_payment_invoice_rel',
                 'ydental_settlement_refund_credit_rel', 'ydental_access_audit',
                 'account_move', 'account_move_line', 'account_payment', 'account_partial_reconcile',
                 'account_full_reconcile', 'account_move__account_payment', 'ydental_queue_execution',
                 'ydental_queue_lease', 'ydental_supply_slot'}
        if not names <= set(schema):
            raise RuntimeError('CURRENT_D_NATIVE_GRAPH_SCHEMA_MISSING')
        projections = {
            'account_move': 'id name state move_type amount_total amount_residual payment_state company_id currency_id partner_id journal_id invoice_date date',
            'account_payment': 'id name amount payment_type is_reconciled state company_id currency_id partner_id journal_id move_id',
            'ydental_queue_lease': 'id ydental_actor_id ydental_store_id ydental_station_id ydental_active ydental_release_reason',
        }
        selected = []
        for name in sorted(names):
            columns = [item['column'] for item in schema[name]]
            entry = {'table': name, 'order': ['id'] if 'id' in columns else sorted(columns)}
            if name in projections:
                entry['columns'] = projections[name].split()
                entry['row_digest'] = True
                if not set(entry['columns']) <= set(columns):
                    raise RuntimeError('CURRENT_D_NATIVE_PROJECTION_SCHEMA_DRIFT')
            selected.append(entry)
        return selected
    if schema is None:
        schema = strict_loads((EXEC_ROOT / 'capture-scratch-framework-state/schema.json').read_bytes())
    initial = strict_loads((LEGACY_EXEC_ROOT / 'admission-r11-final/admission-selection.json').read_bytes())['tables']
    return [item for item in initial if item['table'] in schema]


def d_observe(label, *, profile=None, schema=None):
    if profile is not None and schema is None:
        raise ValueError('CURRENT_D_OBSERVER_SCHEMA_REQUIRED')
    return capture('scratch', label, selections=d_selection(schema, profile=profile), metadata=profile is None,
                   max_rows=2000 if profile is not None else 100000, profile=profile)



def verify_d(directory, source, *, state, actual_refund, profile=None, additional_unpaid_fee_ids=()):
    payments = stored_rows(directory, 'ydental_settlement_payment')
    refunds = stored_rows(directory, 'ydental_settlement_refund')
    native = stored_rows(directory, 'account_payment')
    payment = next(row for row in payments if row['id'] == source['payment_id'])
    inbound = next(row for row in native if row['id'] == payment['ydental_payment_id'])
    invoice = next(row for row in stored_rows(directory, 'account_move') if row['id'] == source['invoice_id'])
    fees = stored_rows(directory, 'ydental_treatment_fee')
    sources = stored_rows(directory, 'ydental_settlement_source')
    d_fees = [row for row in fees if row['id'] == source['fee_id'] and row['ydental_event_id'] == source['event_id']]
    d_sources = [row for row in sources if row['ydental_fee_id'] == source['fee_id']]
    if (len(d_fees) != 1 or d_fees[0]['ydental_amount'] != 6
            or d_fees[0]['ydental_currency_id'] != source['currency_id']
            or len(d_sources) != 1 or d_sources[0]['ydental_invoice_id'] != source['invoice_id']
            or d_sources[0]['ydental_original_amount'] != 6
            or d_sources[0]['ydental_patient_id'] != source['patient_id']
            or d_sources[0]['ydental_store_id'] != source['store_id']
            or {row['id'] for row in fees} != {source['fee_id']} | set(additional_unpaid_fee_ids)):
        stop('D_EVENT_FEE_SOURCE_RELATION_NOT_UNIQUE', profile=profile)
        raise RuntimeError('D_EVENT_FEE_SOURCE_RELATION_NOT_UNIQUE')
    allocation_links = stored_rows(directory, 'ydental_settlement_payment_invoice_rel')
    if allocation_links != [{'invoice_id': source['invoice_id'], 'settlement_payment_id': payment['id']}]:
        raise RuntimeError('D_EXACT_SELECTED_INVOICE_PAYMENT_RELATION_MISMATCH')
    events = [row for row in stored_rows(directory, 'ydental_treatment_event') if row['id'] == source['event_id']]
    snapshots = [row for row in stored_rows(directory, 'ydental_intake_snapshot')
                 if row['id'] == d_fees[0]['ydental_price_snapshot_id']]
    invoice_lines = [row for row in stored_rows(directory, 'account_move_line')
                     if row['id'] == d_sources[0]['ydental_line_id']]
    if (len(events) != 1 or events[0]['state'] != 'confirmed'
            or events[0]['ydental_patient_id'] != source['patient_id']
            or events[0]['ydental_store_id'] != source['store_id']
            or events[0]['ydental_catalog_id'] != source['catalog_id']
            or len(snapshots) != 1 or snapshots[0]['ydental_price_id'] != source['price_id']
            or snapshots[0]['ydental_amount'] != 6 or snapshots[0]['ydental_unit_price'] != 6
            or snapshots[0]['ydental_quantity'] != 1
            or events[0]['ydental_price_snapshot_id'] != snapshots[0]['id']
            or d_sources[0]['ydental_price_version'] != 'S05:' + str(source['price_id'])
            or len(invoice_lines) != 1 or invoice_lines[0]['move_id'] != source['invoice_id']
            or invoice_lines[0]['quantity'] != 1 or invoice_lines[0]['price_subtotal'] != 6):
        raise RuntimeError('D_CONFIRMED_EVENT_FROZEN_PRICE_NATIVE_LINE_RELATION_MISMATCH')
    executions = [row for row in stored_rows(directory, 'ydental_queue_execution') if row['id'] == source['execution_id']]
    leases = [row for row in stored_rows(directory, 'ydental_queue_lease') if row['id'] == source['lease_id']]
    slots = [row for row in stored_rows(directory, 'ydental_supply_slot') if row['id'] == source['slot_id']]
    if (len(executions) != 1 or executions[0]['ydental_task_id'] != source['task_id']
            or executions[0]['ydental_patient_id'] != source['patient_id']
            or executions[0]['ydental_lease_id'] != source['lease_id'] or executions[0]['state'] != 'handover'
            or events[0]['ydental_execution_id'] != source['execution_id']
            or events[0]['ydental_document_id'] != source['document_id']
            or events[0]['ydental_document_version'] != source['document_version']
            or events[0]['ydental_actor_id'] != source['doctor_id']
            or len(leases) != 1 or leases[0]['ydental_actor_id'] != source['doctor_id']
            or leases[0]['ydental_station_id'] != source['station_id'] or leases[0]['ydental_active']
            or leases[0]['ydental_release_reason'] != 'holder_exit'
            or len(slots) != 1 or slots[0]['state'] != 'published'
            or slots[0]['ydental_coverage'].get('user_ids') != [source['doctor_id']]):
        raise RuntimeError('D_REAL_PUBLISHED_DOCTOR_EXECUTION_RELATION_NOT_PROVEN')
    # C controls may create only the explicitly listed unpaid sources. They are
    # kept separate, and never exempt any extra payment/refund or native funds.
    c_sources = [row for row in sources if row['ydental_fee_id'] != source['fee_id']]
    c_moves = {row['ydental_invoice_id'] for row in c_sources}
    moves = stored_rows(directory, 'account_move')
    if (any(row['ydental_fee_id'] not in additional_unpaid_fee_ids for row in c_sources)
            or any(row['move_type'] != 'out_invoice' or row['state'] != 'posted'
                   or row['amount_total'] <= 0 or row['amount_residual'] != row['amount_total']
                   for row in moves if row['id'] in c_moves)):
        raise RuntimeError('D_C_CONTROL_NOT_EXPLICIT_UNPAID_SOURCE')
    if (len(payments) != 1 or len(native) != 1 + bool(actual_refund) or payment['ydental_amount'] != 6
            or inbound['amount'] != 6 or inbound['payment_type'] != 'inbound'
            or not inbound['is_reconciled'] or inbound['state'] != 'reconciled'
            or invoice['state'] != 'posted' or invoice['amount_total'] != 6 or invoice['amount_residual'] != 0):
        stop('D_PAYMENT_INTEGRITY_FAILURE', profile=profile)
        raise RuntimeError('D_UNIQUE_SIX_NOT_INDEPENDENTLY_VERIFIED')
    parts = stored_rows(directory, 'account_partial_reconcile')
    for row, label in [(invoice, 'invoice'), (inbound, 'inbound')]:
        if row.get('company_id') != source['company_id'] or row.get('currency_id') != source['currency_id']:
            stop('D_CURRENCY_COMPANY_MISMATCH', profile=profile, layer=label)
            raise RuntimeError('D_CURRENCY_COMPANY_MISMATCH')
    if payment['ydental_store_id'] != source['store_id'] or payment['ydental_currency_id'] != source['currency_id']:
        raise RuntimeError('D_STORE_MISMATCH')
    if not parts or sum((row['amount'] for row in parts), Decimal(0)) != Decimal(6 + actual_refund):
        stop('D_PARTIAL_RECONCILIATION_MISMATCH', profile=profile)
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
        if len(refunds) != 1 or not refund or refund['ydental_state'] != state or refund['ydental_amount'] != 2:
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
                stop('D_UNIQUE_REFUND_COMMIT_NOT_VERIFIED', profile=profile)
                raise RuntimeError('D_REFUND_UNKNOWN_NO_RETRY_ALLOWED')
            if any(row.get('company_id') != source['company_id'] or row.get('currency_id') != source['currency_id']
                   for row in outbound + credits):
                raise RuntimeError('D_OUTBOUND_CURRENCY_COMPANY_MISMATCH')
            if not outbound[0]['is_reconciled'] or outbound[0]['state'] != 'reconciled' or credits[0]['amount_residual'] != 0:
                raise RuntimeError('D_OUTBOUND_NOT_NATIVE_RECONCILED')
        elif outbound or credits or refund['ydental_native_payment_id'] or refund['ydental_credit_note_id']:
            stop('D_PRE_EXECUTION_UNEXPECTED_OUTBOUND', profile=profile)
            raise RuntimeError('D_FAILED_RECOVERY_ALREADY_PAID')
    expected_moves = {source['invoice_id'], inbound['move_id']} | c_moves
    if actual_refund:
        expected_moves |= {outbound[0]['move_id'], credits[0]['id']}
    if {row['id'] for row in moves} != expected_moves:
        raise RuntimeError('D_UNEXPLAINED_NATIVE_MOVE_OUTSIDE_D_OR_EXPLICIT_UNPAID_C')
    native_lines = stored_rows(directory, 'account_move_line')
    move_for_line = {row['id']: row['move_id'] for row in native_lines}
    actual_partial_edges = {(move_for_line.get(row['debit_move_id']), move_for_line.get(row['credit_move_id']), row['amount']) for row in parts}
    expected_partial_edges = {(source['invoice_id'], inbound['move_id'], Decimal(6))}
    credit_links = stored_rows(directory, 'ydental_settlement_refund_credit_rel')
    if actual_refund:
        expected_partial_edges.add((outbound[0]['move_id'], credits[0]['id'], Decimal(2)))
        if credit_links != [{'move_id': credits[0]['id'], 'refund_id': refund['id']}]:
            raise RuntimeError('D_EXACT_REFUND_CREDIT_RELATION_MISMATCH')
    elif credit_links:
        raise RuntimeError('D_PRE_EXECUTION_UNEXPECTED_CREDIT_RELATION')
    if actual_partial_edges != expected_partial_edges or len(parts) != len(expected_partial_edges):
        raise RuntimeError('D_NATIVE_PARTIAL_RECONCILIATION_MOVE_EDGES_MISMATCH')
    if any(sum((row['balance'] for row in native_lines if row['move_id'] == move_id), Decimal(0)) != 0
           for move_id in expected_moves):
        raise RuntimeError('D_NATIVE_JOURNAL_MOVE_NOT_BALANCED')
    reserved = sum((row['ydental_amount'] for row in refunds if row['ydental_state'] in {
        'requested', 'approved', 'failed', 'unknown'}), Decimal(0))
    completed = sum((row['ydental_amount'] for row in refunds if row['ydental_state'] == 'done'), Decimal(0))
    if completed != actual_refund or reserved != (Decimal(2) if state and not actual_refund else Decimal(0)):
        raise RuntimeError('D_APPROVED_INFLIGHT_OR_ACTUAL_REFUND_TOTAL_MISMATCH')
    return {'layer': 'INDEPENDENT_RO_NATIVE_COMMITTED', 'received': 6, 'actually_refunded': actual_refund,
            'approved_or_protected_inflight': float(reserved), 'refund_capacity_remaining': float(6 - completed - reserved),
            'net_received': 6 - actual_refund, 'refund_state': state,
            'native_inbound_count': 1, 'native_outbound_count': len(outbound),
            'native_credit_count': len(credits), 'source_fee_count': 1,
            'additional_explicit_unpaid_control_fee_ids': list(additional_unpaid_fee_ids),
            'company_id': source['company_id'], 'currency_id': source['currency_id'], 'store_id': source['store_id'],
            'real_gateway_claimed': False, 'synthetic_offline_fixture': True}



def d_flow(manager, front, doctor, fixture, facts, *, profile=None, observe=None, server_pid=None):
    if profile is not None:
        profile.require_action('D-ADMIT')
        save_once(profile.root / 'D-CHAIN-IN-FLIGHT.json', {
            'stage': 'BEFORE_NEW_SYNTHETIC_UPSTREAM_DISPATCH', 'target': profile.database,
            'facts': str(facts.directory.relative_to(ROOT)), 'manager_id': manager.uid,
            'approver_id': front.uid, 'doctor_id': doctor.uid, 'automatic_retry': False})
        if observe is None:
            raise ValueError('CURRENT_D_INDEPENDENT_OBSERVER_REQUIRED')
    observe = observe or d_observe
    if profile is not None:
        step = 0
        def safe_ids(value):
            if type(value) in (int, float, bool) or value is None:
                return value
            if type(value) is list:
                return [safe_ids(item) for item in value]
            if type(value) is dict:
                return {name: safe_ids(item) for name, item in value.items()
                        if name not in {'token', 'editor_token', 'lease_token', 'connection',
                                        'csrf_token', 'password', 'login', 'content'}
                        and (type(item) is not str or name in {'state', 'result', 'channel', 'actual_utc'})}
            return None
        class RecordedActor:
            def __init__(self, actor, label):
                self.actual, self.uid, self.label = actor, actor.uid, label
            def __getattr__(self, name):
                return getattr(self.actual, name)
            def action(self, endpoint, operation, payload, **options):
                nonlocal step
                step += 1
                name = 'D-step-%02d-%s-%s' % (step, self.label, operation)
                if endpoint not in {'access', 'queue', 'clinical'}:
                    options['key'] = options.get('key') or uuid.uuid4().hex
                options['operation_ref'] = options.get('operation_ref') or name
                facts.save(name + '-intent', {'actor_id': self.uid, 'store_id': fixture['store_id'],
                    'endpoint': endpoint, 'operation': operation, 'key': options.get('key'),
                    'operation_ref': options['operation_ref'], 'case': options['case'],
                    'business_ids': safe_ids(payload), 'private_runtime_tokens_retained': False,
                    'automatic_retry': False, 'stage': 'BEFORE_DISPATCH'})
                try:
                    result = self.actual.action(endpoint, operation, payload, **options)
                except BaseException as error:
                    facts.save(name + '-uncertain', {'outcome': 'UNCONFIRMED_REQUIRES_INDEPENDENT_RO',
                        'error_type': type(error).__name__, 'automatic_retry': False})
                    raise
                facts.save(name + '-returned', {'result': safe_ids(result) if type(result) is dict else {
                    'request_id': result.request_id, 'outcome': 'UNKNOWN'},
                    'commit_claimed': False, 'automatic_retry': False})
                return result
        manager, front, doctor = (RecordedActor(actor, label) for actor, label in (
            (manager, 'manager'), (front, 'approver'), (doctor, 'doctor')))
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
    manager.action('supply', 'publish', {'id': slot['id'], 'version': 1, 'user_ids': [doctor.uid], 'reason': 'LC2 actual qualified synthetic doctor coverage'}, case='D-ADMIT')
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
    if profile is not None:
        doctor.action('queue', 'exit', held, case='D-ADMIT')
    bill = manager.action('settlement', 'bill', {'fee_ids': [event['fee_id']], 'discount': 0, 'reason': ''}, case='D-NORMAL-6')
    source = {'patient_id': patient['id'], 'event_id': event['event_id'], 'fee_id': event['fee_id'],
              'invoice_id': bill['invoice_id'], 'catalog_id': catalog['id'], 'price_id': price['id'],
              'slot_id': slot['id'], 'task_id': qualification['task_id'], 'execution_id': execution['execution_id'],
              'document_id': document['document_id'], 'document_version': saved['version'],
              'doctor_id': doctor.uid, 'lease_id': lease['lease_id'], 'station_id': fixture['station_id'],
              'company_id': fixture['company_id'], 'currency_id': fixture['currency_id'], 'store_id': fixture['store_id'],
              'manager_id': manager.uid, 'approver_id': front.uid,
              'pay_key': uuid.uuid4().hex, 'execute_key': uuid.uuid4().hex,
              'pay_operation_ref': 'current-D-unique-receive-six',
              'execute_operation_ref': 'current-D-unique-return-two'}
    pay_payload = {'invoice_ids': [bill['invoice_id']], 'amount': 6, 'channel': 'cash',
                   'actual_utc': datetime.now(timezone.utc).isoformat(), 'proof': 'LC2 synthetic offline six received'}
    facts.save('D-pay-before-dispatch', {'source': source, 'payload': pay_payload,
        'stage': 'NOT_SENT', 'automatic_retry': False, 'actor_id': manager.uid})
    payment = manager.action('settlement', 'pay', pay_payload, key=source['pay_key'],
        operation_ref=source['pay_operation_ref'], case='D-NORMAL-6')
    source['payment_id'] = payment['payment_id']
    facts.save('D-pay-response-before-independent-check', source)
    state = observe('normal-six')
    facts.save('D-normal-independent', verify_d(state, source, state=None, actual_refund=0, profile=profile) | source)
    request = manager.action('settlement', 'refund_request', {'payment_id': source['payment_id'], 'amount': 2, 'reason': 'LC2 synthetic two-unit refund'}, case='D-FAILED-2')
    source['refund_id'] = request['refund_id']
    facts.save('D-requested-independent', verify_d(observe('requested-two'), source,
        state='requested', actual_refund=0, profile=profile))
    self_approval = manager.action('settlement', 'refund_approve', {
        'refund_id': source['refund_id'], 'reason': 'LC2 requester cannot approve own refund'},
        case='D-FAILED-2', expect=(403, 409))
    expected_separation = 'access_denied: A different finance approver must approve a pending request.'
    if self_approval.get('error') != expected_separation:
        raise RuntimeError('D_SELF_APPROVAL_DID_NOT_HIT_NATIVE_SEPARATION_GUARD')
    facts.save('D-self-approval-refused-independent', verify_d(observe('self-approval-denied-two'), source,
        state='requested', actual_refund=0, profile=profile) | {
            'requester_approval_permission': fixture['manager_levels']['finance_approval'],
            'native_separation_message_sha256': hashlib.sha256(expected_separation.encode()).hexdigest()})
    front.action('settlement', 'refund_approve', {'refund_id': source['refund_id'], 'reason': 'LC2 independent authorized approval'}, case='D-FAILED-2')
    facts.save('D-approved-before-failed-independent', verify_d(observe('approved-two'), source,
        state='approved', actual_refund=0, profile=profile) | {'approved_in_flight': 2, 'actually_refunded': 0})
    manager.action('settlement', 'refund_uncertain', {'refund_id': source['refund_id'], 'outcome': 'failed', 'reason': 'LC2 synthetic verified unpaid before offline execution'}, case='D-FAILED-2')
    facts.save('D-failed-independent', verify_d(observe('failed-two'), source, state='failed', actual_refund=0, profile=profile))
    unverified = front.action('settlement', 'refund_recover', {
        'refund_id': source['refund_id'], 'verified_not_paid': '0',
        'reason': 'LC2 missing independent no-payment verification must refuse'},
        case='D-RECOVER-2', expect=(409,))
    expected_recovery = 'refund_recovery_required: Verify the external offline transfer before re-arming.'
    if unverified.get('error') != expected_recovery:
        raise RuntimeError('D_UNVERIFIED_RECOVERY_DID_NOT_HIT_NATIVE_RECOVERY_REQUIRED')
    facts.save('D-unverified-recovery-refused-independent', verify_d(observe('unverified-recovery-denied-two'),
        source, state='failed', actual_refund=0, profile=profile) | {
            'qualified_approver_id': front.uid, 'http_status': 409,
            'native_recovery_message_sha256': hashlib.sha256(expected_recovery.encode()).hexdigest()})
    front.action('settlement', 'refund_recover', {'refund_id': source['refund_id'], 'verified_not_paid': '1', 'reason': 'LC2 independent verified unpaid synthetic fact'}, case='D-RECOVER-2')
    facts.save('D-recover-independent', verify_d(observe('recovered-two'), source, state='approved', actual_refund=0, profile=profile))
    payload = {'refund_id': source['refund_id'], 'actual_utc': datetime.now(timezone.utc).isoformat(), 'proof': 'LC2 synthetic offline two actually returned'}
    facts.save('D-refund-execute-before-dispatch', {'source': source, 'payload': payload,
        'stage': 'NOT_SENT', 'automatic_retry': False, 'actor_id': manager.uid})
    loss = manager.action('settlement', 'refund_execute', payload, key=source['execute_key'], case='D-LOST-REFUND-2',
                          operation_ref=source['execute_operation_ref'], discard=True, retry=True)
    facts.save('D-loss-observation', {'request_id': loss.request_id, 'outcome': 'UNKNOWN', 'automatic_retry': False})
    # The transport may return headers just before COMMIT. Bounded independent
    # observers can wait for visibility; they never re-dispatch the refund.
    verified = None
    for attempt in range(3):
        directory = observe('lost-independent-' + str(attempt + 1))
        refund = next(row for row in stored_rows(directory, 'ydental_settlement_refund') if row['id'] == source['refund_id'])
        if refund['ydental_state'] == 'done':
            verified = verify_d(directory, source, state='done', actual_refund=2, profile=profile)
            break
        time.sleep(.2)
    if verified is None:
        stop('REFUND_COMMIT_UNKNOWN_NO_RETRY', profile=profile)
        raise OutcomeUnknown('REFUND_NOT_VERIFIED_STOP_NO_RETRY')
    facts.save('D-lost-verified-before-retry', verified)
    retry_result = manager.action('settlement', 'refund_execute', payload, key=source['execute_key'], case='D-VERIFY-RETRY',
                                 operation_ref=source['execute_operation_ref'], attempt=2, retry=True)
    if retry_result.get('result') != 'already_accepted':
        raise RuntimeError('D_RETRY_DID_NOT_RETURN_PRIOR_RECEIPT')
    facts.save('D-idempotent-retry-independent', verify_d(observe('retry-unique'), source, state='done', actual_refund=2, profile=profile))
    if profile is None:
        receipt = manager.client.request('GET', '/ydental/settlement/pdf/refund/' + str(source['refund_id']),
            case_id='D-VERIFY-RETRY', artifact_kind='pdf', operation_ref='current-D-final-two-refund-receipt')
    else:
        from concurrent.futures import ThreadPoolExecutor
        import threading
        from lxml import html
        profile.require_action('LOG-02')
        if (type(server_pid) is not int or server_pid <= 0 or manager.uid == front.uid
                or manager.client.cookies is front.client.cookies):
            raise RuntimeError('LOG02_REAL_OWNED_SERVER_AND_TWO_ACTORS_REQUIRED')
        receipt_operation = 'current-D-final-two-refund-receipt'
        front_operation = 'LOG-02-current-D-front-workbench'
        facts.save('LOG02-final-D-read-pair-intent', {'actors': [manager.uid, front.uid],
            'server_pid': server_pid, 'refund_id': source['refund_id'], 'patient_id': source['patient_id'],
            'additional_pdf_requests': 0, 'financial_concurrency_claimed': False})
        barrier = threading.Barrier(2)
        def fetch_receipt():
            barrier.wait(timeout=10)
            return manager.client.request('GET', '/ydental/settlement/pdf/refund/' + str(source['refund_id']),
                case_id='D-VERIFY-RETRY', artifact_kind='pdf', operation_ref=receipt_operation)
        def fetch_workbench():
            barrier.wait(timeout=10)
            return front.client.request('GET', '/ydental/settlement?patient_id=' + str(source['patient_id']),
                case_id='LOG-02', operation_ref=front_operation)
        with ThreadPoolExecutor(max_workers=2) as executor:
            receipt_future = executor.submit(fetch_receipt)
            workbench_future = executor.submit(fetch_workbench)
            receipt = receipt_future.result()
            workbench = workbench_future.result()
        workbench.require_status(200)
        tree = html.fromstring(workbench.body)
        invoice_ids = sorted(int(value.strip()) for value in tree.xpath(
            '//section[@name="settled-bills"]//tbody/tr/td[1]/text()') if value.strip())
        if source['invoice_id'] not in invoice_ids:
            raise RuntimeError('LOG02_FRONT_NONEMPTY_D_WORKBENCH_NOT_PROVEN')
        intervals = []
        for operation, actor_id in ((receipt_operation, manager.uid), (front_operation, front.uid)):
            operation_hash = hashlib.sha256(('ydental-client-operation:' + operation).encode()).hexdigest()
            rows = []
            for path in (profile.run_root / profile.database / 'diagnostics').glob('events-' + str(server_pid) + '-*.jsonl'):
                rows.extend(row for line in path.read_bytes().splitlines() if (
                    row := strict_loads(line)).get('operation_ref') == operation_hash)
            received = [row for row in rows if row.get('event') == 'request.received']
            returned = [row for row in rows if row.get('event') == 'request.returned']
            if len(received) != 1 or len(returned) != 1:
                raise RuntimeError('LOG02_NATIVE_REQUEST_INTERVAL_NOT_UNIQUE')
            first, last = received[0], returned[0]
            if (first.get('actor_id') != actor_id or last.get('actor_id') != actor_id
                    or first.get('request_id') != last.get('request_id')
                    or first.get('trace_id') != last.get('trace_id')
                    or not first.get('request_id') or not first.get('trace_id')
                    or any(row.get('request_id') != first['request_id'] or row.get('trace_id') != first['trace_id']
                           or row.get('actor_id') != actor_id for row in rows)):
                raise RuntimeError('LOG02_ACTOR_REQUEST_TRACE_ISOLATION_FAILED')
            intervals.append({'actor_id': actor_id, 'request_id': first['request_id'], 'trace_id': first['trace_id'],
                'start_ns': first['monotonic_ns'], 'end_ns': last['monotonic_ns'],
                'received_event_id': first['event_id'], 'returned_event_id': last['event_id'],
                'operation_ref_sha256': operation_hash, 'associated_event_count': len(rows)})
        if (intervals[0]['request_id'] == intervals[1]['request_id']
                or intervals[0]['trace_id'] == intervals[1]['trace_id']):
            raise RuntimeError('LOG02_DIFFERENT_REQUEST_CONTEXTS_COLLIDED')
        overlap = max(row['start_ns'] for row in intervals) < min(row['end_ns'] for row in intervals)
        facts.save('LOG02-two-real-identity-request-isolation', {'server_pid': server_pid, 'intervals': intervals,
            'server_intervals_overlap': overlap, 'status': 'PASS' if overlap else 'NOT_PROVEN_NO_SERVER_OVERLAP',
            'client_request_ids': [receipt.request_id, workbench.request_id],
            'workbench_invoice_ids': invoice_ids, 'workbench_body_sha256': hashlib.sha256(workbench.body).hexdigest(),
            'two_distinct_cookie_jars': manager.client.cookies is not front.client.cookies,
            'financial_competition_claimed': False, 'extra_pdf_download_for_logs': False})
    receipt.require_status(200)
    if not receipt.body or not receipt.body.startswith(b'%PDF-'):
        raise RuntimeError('D_FINAL_REFUND_RECEIPT_NOT_PDF')
    facts.save('D-final-refund-receipt', {'request_id': receipt.request_id, 'actor_id': manager.uid,
        'refund_id': source['refund_id'], 'sha256': hashlib.sha256(receipt.body).hexdigest(),
        'bytes': len(receipt.body), 'artifact_ref': receipt.metadata.get('artifact_ref'),
        'client_directory': str(manager.client.directory.relative_to(ROOT)),
        'page_review': 'PENDING_INDEPENDENT_EVERY_PAGE_REVIEW'})
    safe_source = {key: value for key, value in source.items() if key not in {'execute_key', 'pay_key'}}
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

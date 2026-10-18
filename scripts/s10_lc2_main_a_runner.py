"""Reviewable MAIN-A normal-login/service and stored-original UI orchestration.

No network, provider read or application launch occurs at import. The controller
contract is access._execute: switch returns only ``revision``. Clinical._operate
adds ``result=accepted`` to acquire/release. Native authenticated session_info
supplies the actual uid and source session's store name and revision.
"""
import argparse
import asyncio
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import stat
import uuid

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_SHA = '05928780e7d97a06cf29019634f64b010eb4994c2f1c5032d561008a50b059b4'


class ContractError(RuntimeError):
    """A fixed reason code, never response text or secret values."""


class DashboardRevision(HTMLParser):
    def __init__(self, raw):
        super().__init__()
        self.revisions = set()
        self.feed(raw.decode('utf-8'))

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'input' and attrs.get('name') == 'revision':
            self.revisions.add(int(attrs['value']))

    def unique(self):
        if len(self.revisions) != 1:
            raise ContractError('ACCESS_DASHBOARD_REVISION_NOT_UNIQUE')
        return valid_revision(next(iter(self.revisions)))


def valid_revision(value):
    if type(value) is not int or value < 0:
        raise ContractError('INVALID_SERVER_REVISION')
    return value


def switch_revision(response):
    if response.status != 200:
        raise ContractError('SWITCH_REJECTED_NO_EDITOR_DISPATCH')
    value = response.json()
    if type(value) is not dict or set(value) != {'revision'}:
        raise ContractError('SWITCH_CONTROLLER_CONTRACT_MISMATCH')
    return valid_revision(value['revision'])


def authenticated_scope(response, *, revision, expected_store_name):
    if response.status != 200:
        raise ContractError('NATIVE_SESSION_METADATA_REJECTED')
    envelope = response.json()
    info = envelope.get('result') if type(envelope) is dict else None
    if (type(info) is not dict or info.get('uid') != 7
            or type(info.get('uid')) is not int
            or type(info.get('user_context')) is not dict
            or info['user_context'].get('ydental_revision') != revision
            or type(info['user_context'].get('ydental_revision')) is not int
            or info.get('ydental_store_name') != expected_store_name):
        raise ContractError('ACTUAL_SESSION_USER_STORE_OR_REVISION_MISMATCH')
    return {'actual_uid': 7, 'server_revision': revision,
            'source_session_store_name_matches_observed_store1': True}


def provider(user_id):
    if user_id not in (5, 7):
        raise ContractError('PROVIDER_USER_OUT_OF_SCOPE')
    directory = ROOT / '.local/s10-lc2-main-a-20261018-02/credentials'
    path = directory / ('user-%d.json' % user_id)
    if (directory.is_symlink() or path.is_symlink()
            or stat.S_IMODE(directory.stat().st_mode) != 0o700
            or stat.S_IMODE(path.stat().st_mode) != 0o600):
        raise ContractError('PRIVATE_PROVIDER_MODE_INVALID')
    value = json.loads(path.read_bytes())
    if set(value) != {'user_id', 'login', 'password'} or value['user_id'] != user_id:
        raise ContractError('PRIVATE_PROVIDER_IDENTITY_INVALID')
    return value


def run_editor(client, credential, *, gate, emit):
    """One normal login, scope validation, acquire and matching-token release.

    ``emit`` persists only primitive metadata. A failed/unknown operation is not
    retried here; the controller first obtains independent committed state.
    """
    from s10_lc2_http import csrf_from
    if not (gate.get('identity_valid') is True and gate.get('clinical_user7_eligible') is True
            and gate.get('no_other_valid_editor') is True
            and type(gate.get('store1_name')) is str and gate['store1_name']):
        raise ContractError('FRESH_EDITOR_PRECONDITION_NOT_ESTABLISHED')
    if gate.get('editor_already_legally_released') is True:
        emit('editor-result', {'status': 'ALREADY_RELEASED_VERIFIED_NO_REPEAT'})
        return
    login = client.login(credential['login'], credential['password'], case_id='A-EDITOR')
    if login.status not in (302, 303):
        raise ContractError('NORMAL_LOGIN_FORM_REJECTED')
    page = client.request('GET', '/ydental/access', case_id='A-EDITOR')
    if page.status != 200:
        raise ContractError('ACCESS_DASHBOARD_REJECTED')
    revision = DashboardRevision(page.body).unique()
    csrf = csrf_from(page)
    switched = client.request('POST', '/ydental/access/action', form={
        'operation': 'switch', 'revision': revision, 'csrf_token': csrf,
        'payload': json.dumps({'store_id': 1}), 'output': 'json'},
        case_id='A-EDITOR', operation_ref='normal-store-switch')
    revision = switch_revision(switched)
    refreshed = client.request('GET', '/ydental/access', case_id='A-EDITOR')
    if refreshed.status != 200 or DashboardRevision(refreshed.body).unique() != revision:
        raise ContractError('FRESH_ACCESS_PAGE_REVISION_MISMATCH')
    csrf = csrf_from(refreshed)
    metadata = client.request('POST', '/web/session/get_session_info',
        json_body={'jsonrpc': '2.0', 'method': 'call', 'params': {}, 'id': 1},
        case_id='A-EDITOR', operation_ref='native-authenticated-session-metadata')
    scope = authenticated_scope(metadata, revision=revision, expected_store_name=gate['store1_name'])
    emit('editor-login-scope', scope | {'normal_login_post': login.status,
         'switch_http': switched.status, 'evidence_kind': 'REAL_HTTP_NORMAL_LOGIN_AND_SERVICE',
         'cookies': 'SERVER_SET_COOKIE_ONLY_RAM_COOKIEJAR', 'browser_ui_claimed': False})
    connection = uuid.uuid4().hex

    def clinical(operation, payload):
        emit('editor-' + operation + '-intent', {'actor_id': 7, 'document_id': 1,
             'revision': revision, 'commit_observation': 'NOT_OBSERVED'})
        return client.request('POST', '/ydental/clinical/action', form={
            'operation': operation, 'revision': revision, 'csrf_token': csrf,
            'connection': connection, 'payload': json.dumps(payload)}, case_id='A-EDITOR',
            operation_ref='main-legal-editor-' + operation)

    acquired = clinical('acquire', {'document_id': 1})
    if acquired.status != 200:
        raise ContractError('EDITOR_ACQUIRE_REJECTED_OR_UNKNOWN_NO_RETRY')
    value = acquired.json()
    if (type(value) is not dict or value.get('result') != 'accepted' or value.get('document_id') != 1
            or value.get('version') != 4 or value.get('state') != 'confirmed'
            or value.get('responsible_id') != 7
            or type(value.get('editor_token')) is not str or not value['editor_token']):
        raise ContractError('EDITOR_ACQUIRE_CONTRACT_OR_INTEGRITY_MISMATCH_NO_RETRY')
    token = value['editor_token']
    emit('editor-acquire-returned', {'http': 200, 'actor_id': 7, 'document_id': 1,
         'version': 4, 'state': 'confirmed', 'token_retention': 'RAM_ONLY_NOT_EXPORTED',
         'commit_observation': 'HTTP_RETURNED_INDEPENDENT_OBSERVATION_PENDING'})
    released = clinical('release', {'document_id': 1, 'editor_token': token})
    if released.status != 200 or released.json() != {'document_id': 1, 'result': 'accepted'}:
        raise ContractError('EDITOR_RELEASE_REJECTED_OR_UNKNOWN_NO_RETRY')
    emit('editor-result', {'status': 'HTTP_ACQUIRE_RELEASE_RETURNED', 'actor_id': 7,
         'document_id': 1, 'acquire_http': 200, 'release_http': 200,
         'new_connection_and_returned_token_used': True, 'token_retention': 'RAM_ONLY_NOT_EXPORTED',
         'forbidden_text_or_economic_operations': 0,
         'independent_committed_observation': 'PENDING'})


async def run_original(*, budget, directory):
    from s10_lc2_browser import Credentials, run_main_a_browser
    value = provider(5)
    credentials = Credentials(value['login'], value['password'])
    del value
    return await run_main_a_browser(base_url='http://127.0.0.1:18410', database=budget.profile.database,
        owned_targets={budget.profile.database: 'http://127.0.0.1:18410'}, budget=budget,
        directory=directory, credentials=credentials, store_id=1, invoice_id=1, original_id=1,
        original_sha256=ORIGINAL_SHA, patient_id=1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', choices=('editor', 'original', 'both'), default='both')
    args = parser.parse_args()
    from s10_lc2_task_profile import main_a_engineering_profile
    from s10_lc2_launch import OwnedApplication
    from s10_lc2_http import Client
    from s10_lc2_evidence import save_once
    from s10_lc2_browser import _DRIVER_ENV_KEYS
    profile = main_a_engineering_profile()
    directory = profile.root
    approval = directory / 'runtime-approval.json'
    authority = json.loads(approval.read_bytes())
    gate = json.loads((directory / 'fresh-editor-gate.json').read_bytes())
    marker = json.loads((profile.run_root / profile.database / 'database.json').read_bytes())
    if args.phase in ('both', 'editor') and (directory / 'editor-result.json').exists():
        raise ContractError('EDITOR_ALREADY_EXECUTED_NO_REPEAT')
    attempt = uuid.uuid4().hex[:8]

    def emit(name, value):
        save_once(directory / (name + '.json'), value)

    try:
        with OwnedApplication(marker, approval=approval, product_commit=authority['product_commit'],
                              test_commit=authority['test_commit'], action='main-service', profile=profile) as app:
            app.start([])
            app.wait_ready(60)
            if args.phase in ('both', 'editor'):
                client = Client('http://127.0.0.1:18410', database=profile.database,
                    owned_targets={profile.database: 'http://127.0.0.1:18410'}, budget=app.budget,
                    directory=directory / ('editor-http-' + attempt), target_role='main')
                credential = provider(7)
                try:
                    run_editor(client, credential, gate=gate, emit=emit)
                finally:
                    del credential
            if args.phase in ('both', 'original'):
                readiness = json.loads((directory / 'browser-readiness.json').read_bytes())
                if readiness.get('blank_page_pass') is not True:
                    emit('original-result', {'status': 'NOT_RUN_BROWSER_DIAGNOSTIC_NOT_ADMITTED'})
                else:
                    ambient = dict(os.environ)
                    clean = {key: value for key, value in ambient.items() if key in _DRIVER_ENV_KEYS}
                    try:
                        os.environ.clear()
                        os.environ.update(clean)
                        result = asyncio.run(run_original(budget=app.budget,
                                              directory=directory / ('browser-ui-' + attempt)))
                        emit('original-result', result)
                    finally:
                        os.environ.clear()
                        os.environ.update(ambient)
            app.check()
            application_directory = app.directory
        save_once(directory / ('runner-' + attempt + '-result.json'), {
            'status': 'FINISHED_INDEPENDENT_TERMINAL_OBSERVATION_PENDING', 'phase': args.phase,
            'application_directory': str(application_directory.relative_to(ROOT))})
        print(json.dumps({'phase': args.phase, 'status': 'FINISHED_INDEPENDENT_OBSERVATION_PENDING'}))
    except BaseException as error:
        save_once(directory / ('runner-' + attempt + '-failure.json'), {
            'phase': args.phase, 'exception_type': type(error).__name__,
            'reason': str(error) if type(error) is ContractError else 'THIRD_PARTY_TEXT_NOT_EXPORTED',
            'commit_observation': 'INDEPENDENT_OBSERVATION_REQUIRED_BEFORE_ANY_RETRY'})
        print(json.dumps({'phase': args.phase, 'status': 'FAILED_STOP', 'exception_type': type(error).__name__}))
        raise SystemExit(1) from None


if __name__ == '__main__':
    main()

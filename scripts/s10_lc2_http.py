"""Owned-target HTTP observations; no redirects, retries or inferred commits.

Importing this module does not open a socket. Tests can supply an opener whose
open(Request, timeout=...) returns a file-like response or raises an exception.
Credentials/tokens/full payloads remain in memory, never in diagnostic files.
Explicit approved binary artifacts and minimal D retry facts are separate.
"""
from dataclasses import dataclass, field
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
from http.client import HTTPException
from http.cookiejar import CookieJar
import json
import os
from pathlib import Path
import re
import stat
import time
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, unquote, urlencode, urljoin, urlsplit
from urllib.request import build_opener, HTTPCookieProcessor, HTTPRedirectHandler, ProxyHandler, Request
import uuid

from s10_lc2_evidence import PROTECTED, save_once
from s10_lc2_logging import strict_loads
from s10_lc2_supervisor import save_primary
from s10_lc2_task_profile import MAIN_A_PROFILES, MAIN


_DATABASE = re.compile(r'ydental_s10_test_[0-9]{14}_[a-f0-9]{8}\Z')
_SCRATCH_DATABASE = 'ydental_s10_test_20261017105432_ce6dcbf8'
_MAIN_DATABASE = 'ydental_s10_test_20261017105432_810a7d9c'
FAMILY_PATIENT_VALUES = ({'name': 'LC2 C FAMILY ALIAS', 'sex': 'unknown', 'phone': '', 'email': ''},
                         {'name': 'LC2 C FAMILY CANONICAL', 'sex': 'unknown', 'phone': '', 'email': ''})
FAMILY_CLINICAL_VALUES = ({'allergies': 'LC2_SYNTHETIC_ALIAS_ALLERGY',
                           'prior_history': 'LC2_SYNTHETIC_ALIAS_HISTORY', 'medication': 'LC2_SYNTHETIC_ALIAS_MEDICATION'},
                          {'allergies': 'LC2_SYNTHETIC_CANONICAL_ALLERGY',
                           'prior_history': 'LC2_SYNTHETIC_CANONICAL_HISTORY', 'medication': 'LC2_SYNTHETIC_CANONICAL_MEDICATION'})
FAMILY_REQUEST_REASON = 'LC2 synthetic identity duplicate verified for isolated C family'
FAMILY_CONFIRM_REASON = 'LC2 manager verified only the two new synthetic identities'
_MODEL = re.compile(r'[a-z][a-z0-9_.]{0,99}\Z')
_METHOD = re.compile(r'[a-z_][a-z0-9_]{0,99}\Z')
_LABEL = re.compile(r'[A-Za-z0-9_.:-]{1,96}\Z')
_ORIGINAL = re.compile(r'/ydental/settlement/bill-original/[0-9]+/?\Z')
_REDIRECTS = {301, 302, 303, 307, 308}
_OPERATIONS = frozenset({'bill', 'pay', 'refund_request', 'refund_approve', 'refund_reject',
                         'refund_execute', 'refund_uncertain', 'refund_recover', 'refund_cancel',
                         'close', 'unlock', 'reclassify', 'waive', 'trade',
                         'acquire', 'release', 'heartbeat', 'open', 'save', 'confirm', 'correct',
                         'create', 'clinical', 'request_merge'})
_MIMES = frozenset({'application/pdf', 'application/json', 'application/octet-stream',
                    'text/html', 'text/plain', 'text/css', 'application/javascript',
                    'image/png', 'image/jpeg', 'image/gif', 'image/svg+xml', 'image/webp'})
_NATIVE_ERRORS = frozenset({'odoo.exceptions.AccessError', 'odoo.exceptions.UserError',
                            'odoo.exceptions.ValidationError', 'odoo.exceptions.AccessDenied'})
_CASES = frozenset({
    *(('L%02d' % number) for number in range(1, 13)),
    *(('LOG-%02d' % number) for number in range(1, 13)),
    'A-STATE', 'A-EDITOR', 'A-ORIGINAL', 'B-MODEL-6', 'B-RPC-6',
    'C-SCOPE', 'C-ATTACHMENT', 'C-TOKEN', 'C-REVOKED-PAGE',
    'D-ADMIT', 'D-NORMAL-6', 'D-FAILED-2', 'D-RECOVER-2',
    'D-LOST-REFUND-2', 'D-VERIFY-RETRY', 'E-PREBASELINE',
    'E-UPGRADE-S10-ONLY', 'E-PRESERVE', 'E-AFFECTED-REGRESSION',
})


def main_a_request_boundary(method, path, *, form=None, json_body=None):
    """MAIN-A permits normal login, store 1, document 1 and stored original 1.

    This gate only narrows the existing transport guard. It never supplies
    credentials, a session, an editor token or an authorization decision.
    """
    parsed = urlsplit(path)
    route = parsed.path
    query = parse_qs(parsed.query, keep_blank_values=True)
    if method == 'GET':
        allowed = route in {'/web/login', '/ydental/access', '/ydental/clinical',
                            '/ydental/settlement', '/ydental/settlement/bill-original/1',
                            '/web/binary/company_logo', '/logo.png', '/web/manifest.webmanifest',
                            '/ydental_clinical/static/src/document/document.js',
                            '/ydental_clinical/static/src/document/document.css'}
        allowed = allowed or route.startswith(('/web/assets/', '/web/static/'))
        allowed = allowed or bool(re.fullmatch(r'/web/image/res\.company/[1-9][0-9]*/logo', route))
        if not allowed or route == '/ydental/clinical' and query != {'document_id': ['1']}:
            raise ValueError('MAIN_A_GET_ROUTE_OR_DOCUMENT_FORBIDDEN')
        if route == '/ydental/settlement' and query not in ({}, {'patient_id': ['1']}):
            raise ValueError('MAIN_A_PATIENT_QUERY_FORBIDDEN')
        return
    if method != 'POST' or type(form) is not dict or json_body is not None:
        raise ValueError('MAIN_A_POST_SHAPE_FORBIDDEN')
    if route == '/web/login':
        if (set(form) - {'db', 'login', 'password', 'csrf_token', 'redirect', 'type'}
                or form.get('db', MAIN) != MAIN
                or form.get('redirect', '/ydental/settlement') not in {'/ydental/settlement', '/ydental/access'}):
            raise ValueError('MAIN_A_LOGIN_SHAPE_FORBIDDEN')
        return
    if route == '/ydental/access/action' and form.get('operation') == 'switch':
        if 'payload' in form:
            payload = strict_loads(form['payload'])
            valid = payload == {'store_id': 1}
            allowed_fields = {'operation', 'revision', 'payload', 'output', 'csrf_token'}
        else:
            valid = form.get('store_id') in (1, '1')
            allowed_fields = {'operation', 'revision', 'store_id', 'csrf_token'}
        if valid and not set(form) - allowed_fields:
            return
    if route == '/ydental/clinical/action':
        operation = form.get('operation')
        payload = strict_loads(form.get('payload', 'null'))
        if (set(form) <= {'operation', 'revision', 'connection', 'csrf_token', 'payload'}
                and type(payload) is dict and payload.get('document_id') == 1
                and type(payload.get('document_id')) is int):
            if operation == 'acquire' and set(payload) == {'document_id'}:
                return
            if (operation == 'release' and set(payload) == {'document_id', 'editor_token'}
                    and type(payload['editor_token']) is str and 0 < len(payload['editor_token']) <= 128):
                return
    raise ValueError('MAIN_A_ACTION_FORBIDDEN')


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        return None


class HttpEvidenceError(RuntimeError):
    """Evidence/parse failure; says nothing about transaction outcome."""


class OutcomeUnknown(RuntimeError):
    """Caller must independently verify before any repeat economic request."""


class _FamilyWriteScope:
    """One bounded C fixture sequence; this is tool admission, not Odoo auth."""
    def __init__(self, reader, manager, *, reader_uid, manager_uid, existing_patients, existing_merges,
                 protected_patient_ids):
        for client in (reader, manager):
            if (client.target_role != 'main' or client.database != _MAIN_DATABASE
                    or client.base_url != 'http://127.0.0.1:18410'):
                raise ValueError('FAMILY_TARGET_IDENTITY_MISMATCH')
        if type(reader_uid) is not int or reader_uid <= 7 or manager_uid != 5 or reader is manager:
            raise ValueError('FAMILY_ACTOR_IDENTITY_MISMATCH')
        for values in (existing_patients, existing_merges, protected_patient_ids):
            if type(values) not in (list, tuple) or len(values) > 1000 or any(type(item) is not int or item <= 0 for item in values):
                raise ValueError('FAMILY_BASELINE_IDS_INVALID')
        if not {1, 2, 3, 4} <= set(protected_patient_ids):
            raise ValueError('FAMILY_PROTECTED_PATIENT_BASELINE_MISSING')
        self.reader, self.manager = reader, manager
        self.existing_patients = set(existing_patients) | set(protected_patient_ids)
        self.existing_merges = set(existing_merges)
        self.patient_ids, self.clinical_ids = [], []
        self.merge_id = self.merge_version = None
        self.step = 0
        self.dispatched = False

    def expected(self):
        if self.step in (0, 2):
            return self.reader, 'create', {'values': dict(FAMILY_PATIENT_VALUES[self.step // 2])}
        if self.step in (1, 3):
            index = self.step // 2
            return self.reader, 'clinical', {'patient_id': self.patient_ids[index],
                'values': dict(FAMILY_CLINICAL_VALUES[index])}
        if self.step == 4:
            return self.reader, 'request_merge', {'source_id': self.patient_ids[0],
                'target_id': self.patient_ids[1], 'reason': FAMILY_REQUEST_REASON}
        if self.step == 5:
            return self.manager, 'confirm', {'request_id': self.merge_id,
                'version': self.merge_version, 'reason': FAMILY_CONFIRM_REASON}
        raise ValueError('FAMILY_SCOPE_COMPLETE_NO_MORE_WRITES')

    def permit(self, client, operation, payload):
        expected_client, expected_operation, expected_payload = self.expected()
        if self.dispatched or client is not expected_client or (operation, payload) != (expected_operation, expected_payload):
            raise ValueError('FAMILY_WRITE_OUTSIDE_EXACT_NEW_FIXTURE_SEQUENCE')

    def consume_form(self, client, form):
        if (type(form) is not dict or set(form) != {'operation', 'revision', 'csrf_token', 'payload', 'output', 'key'}
                or form.get('output') != 'json' or type(form.get('key')) is not str
                or not re.fullmatch(r'[a-f0-9]{32}', form['key'])
                or type(form.get('payload')) is not str):
            raise ValueError('FAMILY_FORM_SHAPE_NOT_APPROVED')
        payload = strict_loads(form['payload'])
        self.permit(client, form['operation'], payload)
        self.dispatched = True  # An unknown outcome cannot silently be retried.

    def accept(self, operation, result):
        _, expected_operation, _ = self.expected()
        if not self.dispatched or operation != expected_operation or type(result) is not dict or result.get('result') != 'accepted':
            raise OutcomeUnknown('FAMILY_ACTION_RESULT_REQUIRES_INDEPENDENT_VERIFICATION')
        identity, version = result.get('id'), result.get('version')
        if type(identity) is not int or identity <= 0 or type(version) is not int or version <= 0:
            raise OutcomeUnknown('FAMILY_ACTION_IDENTITY_NOT_OBSERVED')
        if operation == 'create':
            if identity in self.existing_patients or identity in self.patient_ids or identity <= 4:
                raise OutcomeUnknown('FAMILY_CREATE_RETURNED_PREEXISTING_PATIENT_STOP')
            self.patient_ids.append(identity)
        elif operation == 'clinical':
            self.clinical_ids.append(identity)
        elif operation == 'request_merge':
            if identity in self.existing_merges:
                raise OutcomeUnknown('FAMILY_MERGE_RETURNED_PREEXISTING_REQUEST_STOP')
            self.merge_id, self.merge_version = identity, version
        elif result.get('patient_id') != self.patient_ids[1]:
            raise OutcomeUnknown('FAMILY_CONFIRM_CANONICAL_IDENTITY_MISMATCH')
        self.step += 1
        self.dispatched = False


class _CsrfParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.values = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'input':
            values = dict(attrs)
            if values.get('name') == 'csrf_token' and isinstance(values.get('value'), str):
                self.values.append(values['value'])


def csrf_from(observation):
    """Parse a previously saved response; never fetch an extra page implicitly."""
    if observation.body is None:
        raise OutcomeUnknown('CSRF_RESPONSE_NOT_OBSERVED')
    try:
        parser = _CsrfParser()
        parser.feed(observation.body.decode('utf-8', errors='strict'))
        values = set(parser.values)
        if len(values) != 1:
            raise ValueError('CSRF_NOT_UNIQUE')
        return values.pop()
    except (ValueError, UnicodeError) as error:
        raise HttpEvidenceError('CSRF_PARSE_FAILED_AFTER_RESPONSE_SAVE') from error


@dataclass(frozen=True)
class Observation:
    request_id: str
    status: int | None
    transport_outcome: str
    commit_observation: str
    metadata: dict
    body: bytes | None = field(repr=False)
    headers: dict = field(repr=False)
    request_path: str = field(repr=False)
    request_method: str = field(repr=False)

    def require_status(self, *allowed):
        if self.transport_outcome != 'RETURNED':
            raise OutcomeUnknown('HTTP_OUTCOME_REQUIRES_INDEPENDENT_VERIFICATION')
        if self.status not in allowed:
            raise AssertionError('HTTP_STATUS_ASSERTION_AFTER_BODY_SAVE')
        return self

    def json(self):
        if self.body is None or self.transport_outcome != 'RETURNED':
            raise OutcomeUnknown('HTTP_BODY_NOT_OBSERVED')
        try:
            return strict_loads(self.body.decode('utf-8', errors='strict'))
        except (ValueError, UnicodeError) as error:
            raise HttpEvidenceError('JSON_PARSE_FAILED_AFTER_RESPONSE_SAVE') from error


def _private_directory(directory):
    directory = Path(directory)
    directory.mkdir(mode=0o700, parents=False, exist_ok=True)
    info = directory.lstat()
    if (not directory.is_absolute() or directory.resolve() != directory
            or not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid()
            or stat.S_IMODE(info.st_mode) != 0o700):
        raise ValueError('HTTP_EVIDENCE_DIRECTORY_NOT_PRIVATE')
    return directory


def _save_bytes(path, raw):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        raise


def _mime(headers):
    actual = headers.get('content-type', '').split(';')[0].strip().lower()
    return actual if actual in _MIMES else 'other'


def _redacted_json(body):
    """Do not preserve arbitrary keys, text, exception messages or nested payloads."""
    result = {'retention': 'REDACTED_SUMMARY_ONLY'}
    try:
        value = strict_loads(body.decode('utf-8', errors='strict'))
    except (ValueError, UnicodeError):
        return result | {'format': 'NON_JSON'}
    if type(value) is not dict:
        return result | {'format': 'JSON', 'top_level': type(value).__name__}
    result['format'] = 'JSON'
    states = {'accepted', 'already_accepted', 'draft', 'confirmed', 'requested', 'approved',
              'failed', 'unknown', 'done', 'cancelled', 'rejected', 'pending'}
    numeric_fields = {'document_id', 'execution_id', 'version', 'refund_id', 'payment_id',
                      'invoice_id', 'original_id', 'actually_refunded', 'reserved',
                      'available', 'released', 'amount', 'residual'}

    def selected(source):
        if type(source) is not dict:
            return {}
        output = {}
        for name in numeric_fields:
            item = source.get(name)
            if type(item) in (int, float) and -1e15 < item < 1e15:
                output[name] = item
        for name in ('result', 'state'):
            item = source.get(name)
            if type(item) is str and item in states:
                output[name] = item
        return output

    result['business_summary'] = selected(value)
    if 'result' in value and type(value['result']) is dict:
        result['rpc_result_summary'] = selected(value['result'])
    if 'error' in value:
        result['error_present'] = True
        error = value['error']
        data = error.get('data') if type(error) is dict else None
        if type(data) is dict:
            name = data.get('name')
            result['native_exception_name'] = name if type(name) is str and name in _NATIVE_ERRORS else 'OTHER_EXCEPTION'
            arguments = data.get('arguments')
            if type(arguments) in (list, tuple):
                result['argument_count'] = len(arguments)
                # The fixed-byte fingerprint can prove expected-message equality
                # without saving arbitrary translated/error text or tokens.
                try:
                    result['arguments_sha256'] = hashlib.sha256(json.dumps(
                        arguments, ensure_ascii=True, allow_nan=False, separators=(',', ':')).encode()).hexdigest()
                except (ValueError, TypeError):
                    result['arguments_hash_status'] = 'UNAVAILABLE'
    return result


def _binary_kind(body):
    if body.startswith(b'%PDF'):
        return 'pdf'
    if (body.startswith((b'\x89PNG\r\n\x1a\n', b'\xff\xd8\xff', b'GIF87a', b'GIF89a'))
            or body.startswith(b'RIFF') and body[8:12] == b'WEBP'):
        return 'image'
    return None


class Client:
    def __init__(self, base_url, *, database, owned_targets, budget, directory,
                 opener=None, timeout=15, max_response_bytes=16 * 1024 * 1024,
                 target_role='main'):
        parsed = urlsplit(base_url)
        if (parsed.scheme != 'http' or parsed.hostname != '127.0.0.1'
                or parsed.port not in range(18410, 18420) or parsed.username is not None
                or parsed.password is not None or parsed.path not in ('', '/')
                or parsed.query or parsed.fragment):
            raise ValueError('HTTP_BASE_NOT_APPROVED')
        base_url = 'http://127.0.0.1:%s' % parsed.port
        if (database in PROTECTED or not _DATABASE.fullmatch(database)
                or type(owned_targets) is not dict or type(owned_targets.get(database)) is not str
                or owned_targets[database].rstrip('/') != base_url):
            raise ValueError('HTTP_DATABASE_NOT_OWNED')
        if not 0 < timeout <= 30 or not 1 <= max_response_bytes <= 32 * 1024 * 1024:
            raise ValueError('HTTP_OBSERVATION_BOUND_NOT_APPROVED')
        if target_role not in {'main', 'scratch'} or (
                target_role == 'scratch' and (database != _SCRATCH_DATABASE or parsed.port != 18411)):
            raise ValueError('HTTP_TARGET_ROLE_IDENTITY_MISMATCH')
        self.base_url = base_url
        self.database = database
        self.target_role = target_role
        self._family_ticket = None
        self.budget = budget
        self.task_profile = getattr(budget, 'profile', None)
        if self.task_profile is not None and self.task_profile.message_id in MAIN_A_PROFILES:
            self.task_profile.validate_target(database, 2144129, parsed.port)
            if target_role != 'main' or set(owned_targets) != {MAIN}:
                raise ValueError('MAIN_A_HTTP_TARGET_SCOPE_INVALID')
        self.directory = _private_directory(directory)
        self.timeout = timeout
        self.max_response_bytes = max_response_bytes
        self.cookies = CookieJar()
        if opener is not None and any(isinstance(handler, HTTPRedirectHandler)
                                      and not isinstance(handler, _NoRedirect)
                                      for handler in getattr(opener, 'handlers', ())):
            raise ValueError('CUSTOM_OPENER_AUTO_REDIRECT_FORBIDDEN')
        self.opener = opener if opener is not None else build_opener(
            ProxyHandler({}), _NoRedirect(), HTTPCookieProcessor(self.cookies))

    def _path(self, path):
        if not isinstance(path, str) or not path.startswith('/') or path.startswith('//'):
            raise ValueError('HTTP_RELATIVE_PATH_REQUIRED')
        parsed = urlsplit(path)
        decoded = unquote(parsed.path)
        if (parsed.scheme or parsed.netloc or parsed.fragment
                or any(ord(character) < 32 for character in path + decoded)
                or not re.fullmatch(r'/[A-Za-z0-9_./-]*', decoded)
                or any(part in {'.', '..'} for part in decoded.split('/'))
                or not decoded.startswith(('/ydental/', '/web/'))):
            raise ValueError('HTTP_PATH_NOT_APPROVED')
        if decoded.startswith('/web/') and not (
                decoded in {'/web/login', '/web/session/authenticate', '/web/session/get_session_info',
                            '/web/content', '/web/image'}
                or decoded.startswith(('/web/dataset/call_kw', '/web/content/', '/web/image/',
                                       '/web/assets/', '/web/static/', '/web/webclient/translations'))):
            raise ValueError('HTTP_NATIVE_ADMIN_PATH_FORBIDDEN')
        if decoded.startswith('/ydental/settlement/bill-original/create/'):
            raise ValueError('ORIGINAL_REGENERATION_FORBIDDEN')
        if decoded.startswith('/ydental/'):
            main_path = (decoded in {'/ydental/access', '/ydental/access/action',
                                    '/ydental/clinical', '/ydental/clinical/action',
                                    '/ydental/settlement', '/ydental/settlement/action',
                                    '/ydental/patients'}
                         or bool(re.fullmatch(r'/ydental/settlement/(?:bill-original|other-stores)/[1-9][0-9]*', decoded))
                         or bool(re.fullmatch(r'/ydental/settlement/pdf/(?:bill|receipt|refund)/[1-9][0-9]*', decoded))
                         or bool(re.fullmatch(r'/ydental/patients/[1-9][0-9]*(?:/clinical)?', decoded)))
            scratch_path = self.target_role == 'scratch' and decoded in {
                '/ydental/patients/action', '/ydental/intake', '/ydental/intake/action',
                '/ydental/supply', '/ydental/supply/action', '/ydental/queue', '/ydental/queue/action',
                '/ydental/treatment', '/ydental/treatment/action',
            }
            family_path = decoded == '/ydental/patients/action' and self._family_ticket is not None
            if not (main_path or scratch_path or family_path):
                raise ValueError('HTTP_APPLICATION_ROUTE_NOT_APPROVED_FOR_TARGET_ROLE')
        if any(value != self.database for value in parse_qs(parsed.query, keep_blank_values=True).get('db', [])):
            raise ValueError('HTTP_DATABASE_QUERY_DRIFT')
        return path, decoded

    @contextmanager
    def _family_request(self, scope, operation, payload):
        if not isinstance(scope, _FamilyWriteScope) or self._family_ticket is not None:
            raise ValueError('FAMILY_SCOPE_TICKET_INVALID_OR_NESTED')
        scope.permit(self, operation, payload)
        self._family_ticket = scope
        try:
            yield
        finally:
            self._family_ticket = None

    @staticmethod
    def _route(decoded):
        # Metadata never contains query, object IDs, tokens or arbitrary suffixes.
        if _ORIGINAL.fullmatch(decoded):
            return 'settlement.original'
        for prefix, name in (
            ('/web/dataset/call_kw', 'native.rpc'), ('/web/login', 'native.login'),
            ('/web/content', 'native.content'), ('/web/image', 'native.image'),
            ('/web/assets', 'native.asset'), ('/web/static', 'native.static'),
            ('/ydental/settlement', 'settlement'), ('/ydental/clinical', 'clinical'),
            ('/ydental/access', 'access'), ('/ydental/queue', 'queue'),
        ):
            if decoded.startswith(prefix):
                return name
        return 'owned.application'

    def _save_body(self, request_id, body, artifact_kind):
        fingerprint = {'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest()}
        save_once(self.directory / (request_id + '-body-fingerprint.json'), fingerprint)
        try:
            summary = _redacted_json(body)
        except Exception:
            summary = {'retention': 'REDACTED_SUMMARY_ONLY', 'redaction_status': 'UNAVAILABLE'}
        save_once(self.directory / (request_id + '-body.redacted.json'), summary | fingerprint)
        actual_kind = _binary_kind(body)
        if artifact_kind is not None and actual_kind is not None:
            target = _private_directory(self.directory / 'binary-artifacts')
            filename = request_id + '-' + actual_kind + '.bin'
            _save_bytes(target / filename, body)
            return {'binary_artifact_status': 'SAVED_SEPARATELY',
                    'artifact_ref': 'binary-artifacts/' + filename,
                    'requested_binary_kind': artifact_kind, 'actual_binary_kind': actual_kind}
        return {'binary_artifact_status': 'NOT_REQUESTED' if artifact_kind is None else 'NOT_BINARY'}

    def request(self, method, path, *, form=None, json_body=None, case_id=None,
                attempt=1, operation_ref=None, discard_response=False,
                artifact_kind=None, retry_manifest=False):
        method = method.upper()
        if method not in {'GET', 'POST'} or form is not None and json_body is not None:
            raise ValueError('HTTP_REQUEST_SHAPE_NOT_APPROVED')
        if (form is not None and type(form) is not dict
                or json_body is not None and type(json_body) is not dict
                or type(discard_response) is not bool or type(retry_manifest) is not bool):
            raise ValueError('HTTP_REQUEST_CONTAINER_OR_FLAGS_INVALID')
        path, decoded = self._path(path)
        if self.task_profile is not None and self.task_profile.message_id in MAIN_A_PROFILES:
            self.task_profile.verify()
            main_a_request_boundary(method, path, form=form, json_body=json_body)
            if (case_id not in {'A-STATE', 'A-EDITOR', 'A-ORIGINAL'}
                    or discard_response or retry_manifest):
                raise ValueError('MAIN_A_CASE_OR_REPLAY_FORBIDDEN')
        if self.target_role == 'main' and decoded == '/ydental/patients/action':
            if method != 'POST' or self._family_ticket is None:
                raise ValueError('FAMILY_MAIN_PATIENT_WRITE_REQUIRES_EXACT_TICKET')
            self._family_ticket.consume_form(self, form)
        if (self.target_role == 'main' and decoded == '/ydental/clinical/action'
                and (method != 'POST' or type(form) is not dict
                     or form.get('operation') not in {'acquire', 'release', 'heartbeat'})):
            raise ValueError('HTTP_MAIN_CLINICAL_REPLAY_FORBIDDEN')
        if method == 'POST' and re.fullmatch(r'/ydental/patients(?:/[1-9][0-9]*(?:/clinical)?)?', decoded):
            raise ValueError('HTTP_PATIENT_READ_ROUTE_IS_GET_ONLY')
        if method == 'GET' and (form is not None or json_body is not None):
            raise ValueError('HTTP_GET_BODY_FORBIDDEN')
        if type(form) is dict and 'db' in form and form['db'] != self.database:
            raise ValueError('HTTP_FORM_DATABASE_DRIFT')
        if decoded == '/web/session/authenticate' and (
                type(json_body) is not dict or type(json_body.get('params')) is not dict
                or json_body['params'].get('db') != self.database):
            raise ValueError('HTTP_AUTH_DATABASE_DRIFT')
        if (discard_response and not (method == 'POST' and decoded == '/ydental/settlement/action'
                                     and type(form) is dict and form.get('operation') == 'refund_execute'
                                     and isinstance(form.get('key'), str) and form['key'])):
            raise ValueError('RESPONSE_DISCARD_ONLY_FOR_APPROVED_REFUND_EXECUTE')
        if case_id is not None and case_id not in _CASES:
            raise ValueError('HTTP_CASE_NOT_IN_FROZEN_MATRIX')
        if type(attempt) is not int or not 1 <= attempt <= 9999:
            raise ValueError('HTTP_ATTEMPT_INVALID')
        if operation_ref is not None and (type(operation_ref) is not str or not _LABEL.fullmatch(operation_ref)):
            raise ValueError('HTTP_OPERATION_LABEL_INVALID')
        if artifact_kind not in (None, 'pdf', 'image'):
            raise ValueError('HTTP_BINARY_ARTIFACT_KIND_INVALID')
        if artifact_kind is not None:
            binary_path = (_ORIGINAL.fullmatch(decoded) or re.fullmatch(
                r'/ydental/settlement/pdf/(?:bill|receipt|refund)/[0-9]+/?', decoded)
                or decoded in {'/web/content', '/web/image'}
                or decoded.startswith(('/web/content/', '/web/image/')))
            if (method != 'GET' or not binary_path or case_id not in {
                    'A-ORIGINAL', 'C-SCOPE', 'C-ATTACHMENT', 'C-TOKEN',
                    'E-AFFECTED-REGRESSION', 'D-VERIFY-RETRY', 'L12', 'LOG-12'}):
                raise ValueError('HTTP_BINARY_ARTIFACT_OUTSIDE_APPROVED_CASE')
        if retry_manifest and not (method == 'POST' and decoded == '/ydental/settlement/action'
                                   and type(form) is dict and form.get('operation') == 'refund_execute'
                                   and case_id in {'D-LOST-REFUND-2', 'D-VERIFY-RETRY'}):
            raise ValueError('HTTP_RETRY_MANIFEST_OUTSIDE_APPROVED_D')
        headers = {'X-YDental-Attempt': str(attempt)}
        if case_id is not None:
            headers['X-YDental-Case-ID'] = case_id
        if operation_ref is not None:
            headers['X-YDental-Operation-Ref'] = operation_ref
        data = None
        if form is not None:
            data = urlencode(form, doseq=True).encode('utf-8')
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
        elif json_body is not None:
            data = json.dumps(json_body, ensure_ascii=True, allow_nan=False).encode('utf-8')
            headers['Content-Type'] = 'application/json'
        if data is not None and len(data) > 100000:
            raise ValueError('HTTP_BODY_BOUND_EXCEEDED')
        request_id = uuid.uuid4().hex
        safe = {'request_id': request_id, 'observation_ref': request_id, 'database_ref': 'owned.target',
                'method': method, 'route': self._route(decoded), 'case_id': case_id,
                'attempt': attempt, 'operation_ref': hashlib.sha256(
                    ('ydental-client-operation:' + operation_ref).encode()).hexdigest() if operation_ref else None,
                'ts_utc': datetime.now(timezone.utc).isoformat(), 'commit_observation': 'NOT_OBSERVED',
                'trace_id': None, 'server_request_id': None,
                'correlation_basis': 'CASE_OPERATION_HINT_AND_TIME_WINDOW'}
        # Each budget intent is durable BEFORE any opener can send bytes.
        self.budget.consume('http')
        if method == 'GET' and _ORIGINAL.fullmatch(decoded):
            self.budget.consume('original_get')
        operation = form.get('operation') if type(form) is dict else None
        request_summary = {
            'request_id': request_id, 'method': method, 'route': safe['route'],
            'operation': operation if type(operation) is str and operation in _OPERATIONS else None,
            'operation_ref': safe['operation_ref'], 'body_bytes': len(data) if data is not None else 0,
            'form_field_count': len(form) if type(form) is dict else None,
            'json_body_present': json_body is not None, 'discard_response': discard_response,
            'credentials_tokens_and_payload': 'MEMORY_ONLY',
        }
        save_once(self.directory / (request_id + '-request.redacted.json'), request_summary)
        if retry_manifest:
            # This controlled business retry fact is NOT a diagnostic log.
            # Auth/session/CSRF/editor/connection tokens are never included.
            fields = ('operation', 'revision', 'key', 'refund_id', 'actual_utc', 'proof')
            if not all(name in form for name in fields):
                raise ValueError('D_EXACT_RETRY_FACT_INCOMPLETE')
            if (type(form['key']) is not str or not 1 <= len(form['key']) <= 120
                    or type(form['proof']) is not str or not 1 <= len(form['proof']) <= 300
                    or type(form['actual_utc']) is not str):
                raise ValueError('D_RETRY_FACT_TYPE_INVALID')
            for name in ('revision', 'refund_id'):
                item = form[name]
                if not (type(item) is int and item > 0 or type(item) is str
                        and item.isascii() and item.isdecimal() and len(item) <= 12 and int(item) > 0):
                    raise ValueError('D_RETRY_FACT_ID_INVALID')
            try:
                actual_time = datetime.fromisoformat(form['actual_utc'])
                if actual_time.tzinfo is None:
                    raise ValueError('D_RETRY_TIMEZONE_REQUIRED')
            except ValueError as error:
                raise ValueError('D_RETRY_FACT_TIME_INVALID') from error
            target = _private_directory(self.directory / 'business-retry-facts')
            save_once(target / (request_id + '.json'), {
                'kind': 'APPROVED_D_EXACT_RETRY_FACT_NOT_LOG', 'request_id': request_id,
                'operation_ref': safe['operation_ref'], 'payload': {name: form[name] for name in fields},
                'commit_observation': 'NOT_OBSERVED',
            })
        save_once(self.directory / (request_id + '-intent.public.json'), safe | {'event': 'http.dispatch.intent'})
        request = Request(self.base_url + path, data=data, headers=headers, method=method)
        response = None
        status = None
        actual_headers = {}
        stage = 'transport.open'
        started = time.monotonic_ns()
        try:
            try:
                response = self.opener.open(request, timeout=self.timeout)
            except HTTPError as error:
                # HTTP rejection and explicit redirect are actual responses, not transport failure.
                response = error
            status = response.status if hasattr(response, 'status') else response.getcode()
            actual_headers = {name.lower(): value for name, value in response.headers.items()}
            stage = 'evidence.headers'
            save_once(self.directory / (request_id + '-headers.redacted.json'), {
                'status': status, 'mime': _mime(actual_headers),
                'no_store': 'no-store' in actual_headers.get('cache-control', '').lower(),
                'redirect_present': 'location' in actual_headers,
                'auth_and_arbitrary_headers': 'MEMORY_ONLY',
            })
            if discard_response:
                # Deliberately do not read this body or infer commit from headers.
                safe.update(status=status, transport_outcome='DISCARDED', commit_observation='UNKNOWN',
                            body_observation='NOT_OBSERVED', mime=None, bytes=None, sha256=None)
                body = None
            else:
                stage = 'transport.read'
                body = response.read(self.max_response_bytes + 1)
                # Preserve safe evidence before assertions; full auth/clinical
                # bodies stay in memory even when the run directory is private.
                stage = 'evidence.body'
                body_evidence = self._save_body(request_id, body, artifact_kind)
                mime = _mime(actual_headers)
                safe.update(status=status, transport_outcome='RETURNED',
                            body_observation='OBSERVED', mime=mime,
                            bytes=len(body), sha256=hashlib.sha256(body).hexdigest(), **body_evidence)
                if len(body) > self.max_response_bytes:
                    safe.update(body_observation='TRUNCATED_AT_BOUND', transport_outcome='INCOMPLETE',
                                commit_observation='UNKNOWN')
            safe['duration_ms'] = (time.monotonic_ns() - started) / 1000000
            stage = 'evidence.outcome'
            save_once(self.directory / (request_id + '-outcome.public.json'), safe | {'event': 'http.observation'})
            return Observation(request_id, status, safe['transport_outcome'], safe['commit_observation'],
                               dict(safe), body, actual_headers, path, method)
        except (OSError, URLError, HTTPException) as error:
            if not stage.startswith('transport.'):
                save_primary(self.directory, error, stage=stage)
                raise HttpEvidenceError('HTTP_EVIDENCE_SAVE_FAILED_COMMIT_NOT_OBSERVED') from error
            # Never print transport error strings: they may include a sensitive URL.
            partial = getattr(error, 'partial', None)
            partial = partial[:self.max_response_bytes + 1] if type(partial) is bytes else None
            if partial is not None:
                try:
                    self._save_body(request_id, partial, artifact_kind)
                except Exception as saving_error:
                    save_primary(self.directory, saving_error, stage='evidence.partial_body')
                    raise HttpEvidenceError('HTTP_PARTIAL_BODY_EVIDENCE_SAVE_FAILED') from saving_error
            safe.update(status=status, transport_outcome='DISCONNECTED', commit_observation='UNKNOWN',
                        body_observation='NOT_OBSERVED', error_type=type(error).__name__,
                        duration_ms=(time.monotonic_ns() - started) / 1000000)
            if partial is not None:
                safe.update(body_observation='PARTIAL', bytes=len(partial), sha256=hashlib.sha256(partial).hexdigest())
            try:
                save_once(self.directory / (request_id + '-outcome.public.json'), safe | {'event': 'http.observation'})
            except Exception as saving_error:
                save_primary(self.directory, saving_error, stage='evidence.transport_outcome')
                raise HttpEvidenceError('HTTP_UNKNOWN_OUTCOME_EVIDENCE_SAVE_FAILED') from saving_error
            return Observation(request_id, status, 'DISCONNECTED', 'UNKNOWN', dict(safe), partial, actual_headers, path, method)
        finally:
            if response is not None:
                try:
                    response.close()
                except Exception as close_error:
                    save_primary(self.directory, close_error, stage='transport.response_close.secondary')

    def follow(self, observation, *, case_id=None, attempt=1, operation_ref=None):
        """One explicit redirect; preserving a POST on307/308 requires caller review."""
        if observation.transport_outcome != 'RETURNED' or observation.status not in _REDIRECTS:
            raise ValueError('HTTP_REDIRECT_NOT_OBSERVED')
        if observation.status in {307, 308} and observation.request_method != 'GET':
            raise OutcomeUnknown('POST_REDIRECT_REQUIRES_EXPLICIT_REVIEW_NO_AUTO_REPLAY')
        location = observation.headers.get('location')
        if not location:
            raise HttpEvidenceError('HTTP_REDIRECT_LOCATION_MISSING')
        resolved = urlsplit(urljoin(self.base_url + observation.request_path, location))
        if resolved.scheme + '://' + resolved.netloc != self.base_url:
            raise ValueError('HTTP_REDIRECT_ESCAPES_OWNED_TARGET')
        return self.request('GET', resolved.path + ('?' + resolved.query if resolved.query else ''),
                            case_id=case_id, attempt=attempt, operation_ref=operation_ref)

    def login(self, login, password, *, case_id='L02'):
        page = self.request('GET', '/web/login?' + urlencode({'db': self.database}), case_id=case_id)
        page.require_status(200)
        token = csrf_from(page)
        return self.request('POST', '/web/login', form={
            'db': self.database, 'login': login, 'password': password,
            'csrf_token': token, 'redirect': '/ydental/settlement',
        }, case_id=case_id)

    def rpc(self, model, method, args, *, kwargs=None, case_id=None, attempt=1, operation_ref=None):
        if not _MODEL.fullmatch(model) or not _METHOD.fullmatch(method):
            raise ValueError('RPC_MODEL_OR_METHOD_SHAPE_INVALID')
        body = {'jsonrpc': '2.0', 'method': 'call', 'id': uuid.uuid4().hex,
                'params': {'model': model, 'method': method, 'args': args, 'kwargs': kwargs or {}}}
        return self.request('POST', '/web/dataset/call_kw/' + model + '.' + method,
                            json_body=body, case_id=case_id, attempt=attempt, operation_ref=operation_ref)

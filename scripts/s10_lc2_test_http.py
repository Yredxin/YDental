"""Offline fake-transport tests for the actual LC2 HTTP observer, no sockets."""
from http.client import IncompleteRead
import json
from pathlib import Path
import tempfile
import unittest
from urllib.error import URLError
from urllib.parse import parse_qs

from s10_lc2_http import Client, HttpEvidenceError, OutcomeUnknown, csrf_from

DATABASE = 'ydental_s10_test_20261017120000_1234abcd'
BASE = 'http://127.0.0.1:18410'


class FakeBudget:
    def __init__(self):
        self.intents = []

    def consume(self, kind):
        self.intents.append(kind)


class FakeResponse:
    def __init__(self, body=b'{}', status=200, headers=None, read_error=None):
        self.body, self.status = body, status
        self.headers = headers or {'Content-Type': 'application/json'}
        self.read_error = read_error
        self.read_count = 0
        self.closed = False

    def read(self, bound):
        self.read_count += 1
        if self.read_error is not None:
            raise self.read_error
        return self.body[:bound]

    def close(self):
        self.closed = True


class FakeOpener:
    handlers = ()

    def __init__(self, responses, budget, directory):
        self.responses = list(responses)
        self.budget, self.directory = budget, directory
        self.requests = []

    def open(self, request, timeout):
        if len([item for item in self.budget.intents if item == 'http']) != len(self.requests) + 1:
            raise AssertionError('budget was not consumed before dispatch')
        if len(list(self.directory.glob('*-intent.public.json'))) != len(self.requests) + 1:
            raise AssertionError('intent was not saved before dispatch')
        self.requests.append(request)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class HttpObserverCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='lc2-http-offline-')
        self.directory = Path(self.temporary.name)
        self.addCleanup(self.temporary.cleanup)
        self.budget = FakeBudget()

    def client(self, responses, **kwargs):
        opener = FakeOpener(responses, self.budget, self.directory)
        return Client(BASE, database=DATABASE, owned_targets={DATABASE: BASE}, budget=self.budget,
                      directory=self.directory, opener=opener, **kwargs), opener

    def test_body_saved_before_status_assertion_and_parse(self):
        client, opener = self.client([FakeResponse(b'not-json', status=409)])
        observed = client.request('GET', '/ydental/settlement', case_id='L03')
        fingerprint = json.loads((self.directory / (observed.request_id + '-body-fingerprint.json')).read_bytes())
        self.assertEqual(fingerprint['bytes'], len(b'not-json'))
        self.assertEqual(observed.body, b'not-json')
        self.assertFalse(list(self.directory.glob('*-body.private.bin')))
        with self.assertRaises(AssertionError):
            observed.require_status(200)
        with self.assertRaises(HttpEvidenceError):
            observed.json()
        self.assertEqual(observed.commit_observation, 'NOT_OBSERVED')
        self.assertEqual(len(opener.requests), 1)

    def test_redirect_never_hidden_and_each_explicit_hop_counted(self):
        client, opener = self.client([FakeResponse(b'', 303, {'Location': '/ydental/settlement'}), FakeResponse()])
        redirect = client.request('POST', '/ydental/access/action', form={'operation': 'switch'}, case_id='L02')
        self.assertEqual(len(opener.requests), 1)
        client.follow(redirect, case_id='L02')
        self.assertEqual(len(opener.requests), 2)
        self.assertEqual(self.budget.intents, ['http', 'http'])

    def test_login_uses_existing_saved_csrf_and_no_implicit_follow(self):
        csrf = '<form><input name="csrf_token" value="synthetic-private-csrf"></form>'
        client, opener = self.client([FakeResponse(csrf.encode(), headers={'Content-Type': 'text/html'}),
                                      FakeResponse(b'', 303, {'Location': '/ydental/settlement'})])
        result = client.login('synthetic-user', 'synthetic-password')
        self.assertEqual(len(opener.requests), 2)
        form = parse_qs(opener.requests[1].data.decode())
        self.assertEqual(form['csrf_token'], ['synthetic-private-csrf'])
        self.assertEqual(form['db'], [DATABASE])
        self.assertEqual(result.status, 303)
        for path in self.directory.iterdir():
            raw = path.read_text()
            self.assertNotIn('synthetic-password', raw)
            self.assertNotIn('synthetic-private-csrf', raw)
            self.assertNotIn('synthetic-user', raw)

    def test_actual_rpc_params_preserved_and_native_error_observed_as_body(self):
        response = {'error': {'data': {'name': 'odoo.exceptions.AccessError', 'arguments': ['synthetic denial']}}}
        client, opener = self.client([FakeResponse(json.dumps(response).encode())])
        result = client.rpc('ydental.access.audit', 'write', [[123], {'ydental_reason': 'synthetic'}], case_id='B-RPC-6')
        params = json.loads(opener.requests[0].data)['params']
        self.assertEqual(params, {'model': 'ydental.access.audit', 'method': 'write',
                                  'args': [[123], {'ydental_reason': 'synthetic'}], 'kwargs': {}})
        self.assertEqual(result.json()['error']['data']['name'], 'odoo.exceptions.AccessError')
        self.assertEqual(result.commit_observation, 'NOT_OBSERVED')

    def test_disconnect_is_unknown_and_never_retried_or_secret_printed(self):
        client, opener = self.client([URLError('synthetic-token-secret')])
        result = client.request('POST', '/ydental/settlement/action', form={'operation': 'pay'}, case_id='D-NORMAL-6')
        self.assertEqual(result.transport_outcome, 'DISCONNECTED')
        self.assertEqual(result.commit_observation, 'UNKNOWN')
        self.assertEqual(len(opener.requests), 1)
        with self.assertRaises(OutcomeUnknown):
            result.json()
        for path in self.directory.iterdir():
            self.assertNotIn(b'synthetic-token-secret', path.read_bytes())

    def test_only_refund_execute_can_deliberately_discard_and_body_is_unread(self):
        response = FakeResponse(read_error=AssertionError('must not read discarded response'))
        client, opener = self.client([response])
        with self.assertRaisesRegex(ValueError, 'RESPONSE_DISCARD_ONLY'):
            client.request('POST', '/ydental/settlement/action', form={'operation': 'pay', 'key': 'synthetic'},
                           discard_response=True, case_id='D-NORMAL-6')
        self.assertEqual(self.budget.intents, [])
        result = client.request('POST', '/ydental/settlement/action',
                                form={'operation': 'refund_execute', 'key': 'synthetic'},
                                discard_response=True, case_id='D-LOST-REFUND-2', operation_ref='synthetic-refund')
        self.assertEqual(response.read_count, 0)
        self.assertTrue(response.closed)
        self.assertEqual(result.commit_observation, 'UNKNOWN')
        self.assertEqual(result.transport_outcome, 'DISCARDED')
        self.assertEqual(len(opener.requests), 1)

    def test_partial_body_preserved_and_all_files_private(self):
        client, opener = self.client([FakeResponse(read_error=IncompleteRead(b'synthetic-partial'))])
        result = client.request('GET', '/web/content/123?download=true', case_id='C-ATTACHMENT')
        self.assertEqual(result.commit_observation, 'UNKNOWN')
        self.assertEqual(result.body, b'synthetic-partial')
        fingerprint = json.loads((self.directory / (result.request_id + '-body-fingerprint.json')).read_bytes())
        self.assertEqual(fingerprint['bytes'], len(b'synthetic-partial'))
        self.assertFalse(list(self.directory.glob('*-body.private.bin')))
        for path in self.directory.iterdir():
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_original_get_budget_and_zero_generation(self):
        client, opener = self.client([FakeResponse(b'%PDF-synthetic', headers={'Content-Type': 'application/pdf'})])
        observed = client.request('GET', '/ydental/settlement/bill-original/1', case_id='A-ORIGINAL', artifact_kind='pdf')
        artifact = self.directory / observed.metadata['artifact_ref']
        self.assertEqual(artifact.read_bytes(), b'%PDF-synthetic')
        self.assertEqual(self.budget.intents, ['http', 'original_get'])
        with self.assertRaisesRegex(ValueError, 'ORIGINAL_REGENERATION_FORBIDDEN'):
            client.request('POST', '/ydental/settlement/bill-original/create/1', form={}, case_id='A-ORIGINAL')
        self.assertEqual(len(opener.requests), 1)

    def test_owned_database_and_endpoint_guards_before_dispatch(self):
        client, opener = self.client([])
        for path in ['/web/database/list', '//example.com/steal', '/web/login?db=other', '/web/../database']:
            with self.assertRaises(ValueError):
                client.request('GET', path, case_id='L09')
        self.assertEqual(self.budget.intents, [])
        self.assertEqual(opener.requests, [])

    def test_clinical_auth_fulltext_and_cookie_sentinels_never_reach_disk(self):
        sentinels = ['SECRET_EDITOR_SENTINEL', 'SECRET_SESSION_SENTINEL', 'SECRET_CSRF_SENTINEL',
                     'SECRET_CASE_TEXT_SENTINEL', 'SECRET_ACCESS_SENTINEL']
        response_body = json.dumps({'result': {'editor_token': sentinels[0], 'access_token': sentinels[4],
                                               'content': {'chief_complaint': sentinels[3]}}}).encode()
        client, opener = self.client([FakeResponse(response_body, headers={
            'Content-Type': 'application/json', 'Set-Cookie': 'session_id=' + sentinels[1]})])
        observed = client.request('POST', '/ydental/clinical/action',
                                  form={'operation': 'acquire', 'csrf_token': sentinels[2],
                                        'payload': json.dumps({'document_id': 1, 'editor_token': sentinels[0],
                                                               'content': sentinels[3]})}, case_id='A-EDITOR')
        self.assertEqual(observed.body, response_body)
        for path in self.directory.rglob('*'):
            if path.is_file():
                raw = path.read_bytes()
                for sentinel in sentinels:
                    self.assertNotIn(sentinel.encode(), raw)

    def test_explicit_d_retry_manifest_excludes_auth_and_is_separate(self):
        client, opener = self.client([FakeResponse()])
        form = {'operation': 'refund_execute', 'revision': '1', 'key': 'synthetic-private-retry-key',
                'refund_id': '123', 'actual_utc': '2026-10-17T10:00:00+00:00',
                'proof': 'synthetic offline test', 'csrf_token': 'SECRET_CSRF_RETRY_SENTINEL'}
        client.request('POST', '/ydental/settlement/action', form=form, case_id='D-LOST-REFUND-2',
                       retry_manifest=True, discard_response=True)
        facts = list((self.directory / 'business-retry-facts').glob('*.json'))
        self.assertEqual(len(facts), 1)
        retained = json.loads(facts[0].read_bytes())
        self.assertEqual(set(retained['payload']), {'operation', 'revision', 'key', 'refund_id', 'actual_utc', 'proof'})
        self.assertEqual(retained['payload']['key'], form['key'])
        for path in self.directory.rglob('*'):
            if path.is_file():
                self.assertNotIn(b'SECRET_CSRF_RETRY_SENTINEL', path.read_bytes())


if __name__ == '__main__':
    unittest.main(verbosity=2)

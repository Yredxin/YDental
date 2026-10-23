"""Mocked transport boundaries; these checks do not establish real HTTP delivery."""
import json
import socket
from http.client import IncompleteRead, RemoteDisconnected
from types import SimpleNamespace
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged

from odoo.addons.ydental_followup.models.ydental_followup_service import YDentalFollowupService
from odoo.addons.ydental_followup_test.models import local_sink


@tagged('post_install', '-at_install')
class TestFollowupLocalSink(TransactionCase):

    def setUp(self):
        super().setUp()
        self.service = self.env['ydental.followup.service']
        self.job = SimpleNamespace(
            id=71, ydental_store_id=SimpleNamespace(id=32),
            ydental_request_id='synthetic-stable-request',
            ydental_event_type='followup_contact', ydental_source_res_id=84,
        )
        self.parameters = self.env['ir.config_parameter'].sudo()
        self.parameters.set_str(local_sink.ENABLE_PARAMETER, '1')
        self.parent = self.enterContext(patch.object(
            YDentalFollowupService, '_send_transport', return_value='native-accepted'))
        self.http = self.enterContext(patch.object(local_sink, 'HTTPConnection'))
        self.connection = self.http.return_value
        self.response = self.connection.getresponse.return_value
        self.response.status = 200
        self.response.read.return_value = b'{"outcome":"accepted"}'
        self.enterContext(patch.object(local_sink, 'EXPECTED_DB', self.env.cr.dbname))
        policy = SimpleNamespace(ydental_channel_mode='controlled_test_sink')
        self.policy_search = self.enterContext(patch.object(
            type(self.env['ydental.followup.policy']), 'search', return_value=policy))

    def test_disabled_configuration_uses_native_transport_without_http(self):
        for value in ('', '0', 'true'):
            with self.subTest(value=value):
                self.parameters.set_str(local_sink.ENABLE_PARAMETER, value)
                self.assertEqual(self.service._send_transport(self.job), 'native-accepted')
        self.http.assert_not_called()

    def test_other_database_never_opens_http(self):
        with patch.object(local_sink, 'EXPECTED_DB', self.env.cr.dbname + '_different'):
            self.assertEqual(self.service._send_transport(self.job), 'native-accepted')
        self.http.assert_not_called()
        self.policy_search.assert_not_called()

    def test_non_test_policy_never_opens_http(self):
        self.policy_search.return_value = SimpleNamespace(ydental_channel_mode='disabled')
        self.assertEqual(self.service._send_transport(self.job), 'native-accepted')
        self.http.assert_not_called()

    def test_explicit_acceptance_posts_identifiers_once_then_uses_native_semantics(self):
        self.assertEqual(self.service._send_transport(self.job), 'native-accepted')
        self.http.assert_called_once_with('127.0.0.1', 18412, timeout=0.5)
        self.connection.request.assert_called_once()
        args, kwargs = self.connection.request.call_args
        self.assertEqual(args, ('POST', '/notifications'))
        self.assertEqual(json.loads(kwargs['body']), {
            'request_id': 'synthetic-stable-request', 'job_id': 71,
            'event_type': 'followup_contact', 'source_id': 84,
        })
        self.assertEqual(kwargs['headers'], {'Content-Type': 'application/json'})
        self.response.read.assert_called_once_with(4097)
        self.parent.assert_called_once_with(self.job)
        self.connection.close.assert_called_once()

    def test_timeout_remains_unknown_without_native_acceptance_or_retry(self):
        self.connection.getresponse.side_effect = socket.timeout('synthetic delayed response')
        with self.assertRaises(TimeoutError):
            self.service._send_transport(self.job)
        self.connection.request.assert_called_once()
        self.parent.assert_not_called()
        self.connection.close.assert_called_once()

    def test_explicit_failures_never_record_native_acceptance(self):
        for status, body in ((503, b''), (200, b'{"outcome":"failed"}')):
            with self.subTest(status=status, body_size=len(body)):
                self.connection.reset_mock()
                self.response.status = status
                self.response.read.return_value = body
                with self.assertRaises(RuntimeError):
                    self.service._send_transport(self.job)
                self.connection.request.assert_called_once()
                self.connection.close.assert_called_once()
        self.parent.assert_not_called()

    def test_indeterminate_success_responses_require_same_request_reconciliation(self):
        for body in (b'not-json', b'x' * 4097, b'', b'{"outcome":"unknown"}', b'{}'):
            with self.subTest(body_size=len(body)):
                self.connection.reset_mock()
                self.response.read.return_value = body
                with self.assertRaises(TimeoutError):
                    self.service._send_transport(self.job)
                self.connection.request.assert_called_once()
                self.connection.close.assert_called_once()
        self.parent.assert_not_called()

    def test_connection_and_protocol_failures_remain_unknown_without_retry(self):
        for method, error in ((self.connection.request, ConnectionResetError('synthetic reset')),
                              (self.connection.getresponse, RemoteDisconnected('synthetic disconnect')),
                              (self.response.read, IncompleteRead(b'{"outcome":'))):
            with self.subTest(error=type(error).__name__):
                self.connection.reset_mock()
                with patch.object(method, 'side_effect', error), self.assertRaises(TimeoutError):
                    self.service._send_transport(self.job)
                self.connection.request.assert_called_once()
                self.connection.close.assert_called_once()
        self.parent.assert_not_called()

import hashlib
import hmac
import json
import secrets

from odoo import fields
from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestFollowupNotificationHTTP(HttpCase):
    """Exercise signed provider callbacks through the public HTTP route."""

    def setUp(self):
        super().setUp()
        self.secret = 's11-http-callback-' + secrets.token_hex(16)
        self.env['ir.config_parameter'].sudo().set_str(
            'ydental_followup.callback_secret', self.secret,
        )
        store = self.env['ydental.access.store'].sudo().create({
            'name': 'S11 HTTP synthetic callback store',
            'company_id': self.env.company.id,
            'ydental_timezone': 'UTC',
        })
        self.job = self.env['ydental.notification.job'].sudo()._new({
            'name': 'S11 HTTP synthetic callback job',
            'ydental_store_id': store.id,
            'ydental_category': 'followup',
            'ydental_source_model': 'ydental.followup',
            'ydental_source_res_id': 999999,
            'ydental_event_type': 'followup_contact',
            'ydental_source_version': 1,
            'ydental_channel_key': 'patient',
            'ydental_due_at': fields.Datetime.now(),
        })
        self.job._save({'ydental_state': 'unknown', 'ydental_request_id': 's11-http-' + secrets.token_hex(12)})

    def _post_callback(self, event_id, status, signature_secret=None):
        body = json.dumps({
            'request_id': self.job.ydental_request_id,
            'event_id': event_id,
            'status': status,
        }, separators=(',', ':')).encode()
        secret = signature_secret or self.secret
        signature = 'sha256=' + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        return self.url_open(
            '/ydental/followups/provider-callback',
            data=body,
            headers={
                'Content-Type': 'application/json',
                'X-YDental-Signature': signature,
            },
        )

    def test_signed_callback_route_accepts_deduplicates_and_rejects_invalid_signature(self):
        accepted = self._post_callback('s11-http-event-delivered', 'delivered')
        self.assertEqual(accepted.status_code, 200, accepted.text)
        self.assertEqual(accepted.json(), {'result': 'accepted', 'state': 'delivered'})
        self.assertIn('no-store', accepted.headers.get('Cache-Control', ''))

        duplicate = self._post_callback('s11-http-event-delivered', 'delivered')
        self.assertEqual(duplicate.status_code, 200, duplicate.text)
        self.assertEqual(duplicate.json(), {'result': 'duplicate', 'state': 'delivered'})

        invalid = self._post_callback(
            's11-http-event-invalid-signature', 'delivered',
            signature_secret='wrong-test-only-secret',
        )
        self.assertEqual(invalid.status_code, 403, invalid.text)
        self.assertIn('error', invalid.json())

        self.job.invalidate_recordset()
        self.assertEqual(self.job.ydental_state, 'delivered')
        receipts = self.env['ydental.notification.callback'].sudo().search([
            ('ydental_job_id', '=', self.job.id),
        ])
        self.assertEqual(len(receipts), 1)
        self.assertEqual(receipts.ydental_provider_event_id, 's11-http-event-delivered')

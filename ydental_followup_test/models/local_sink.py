"""Opt-in loopback transport for committed S11 synthetic notification checks."""
import json
import socket
from http.client import HTTPConnection, HTTPException

from odoo import models


EXPECTED_DB = 'ydental_s11_synth_20261023_01'
ENABLE_PARAMETER = 'ydental_followup_test.local_sink_enabled'


class FollowupLocalSink(models.AbstractModel):
    _inherit = 'ydental.followup.service'

    def _send_transport(self, job):
        if self.env.cr.dbname != EXPECTED_DB:
            return super()._send_transport(job)
        if self.env['ir.config_parameter'].sudo().get_str(ENABLE_PARAMETER) != '1':
            return super()._send_transport(job)
        policy = self.env['ydental.followup.policy'].sudo().search([
            ('ydental_store_id', '=', job.ydental_store_id.id),
        ], limit=1)
        if not policy or policy.ydental_channel_mode != 'controlled_test_sink':
            return super()._send_transport(job)

        payload = {
            'request_id': job.ydental_request_id,
            'job_id': job.id,
            'event_type': job.ydental_event_type,
            'source_id': job.ydental_source_res_id,
        }
        connection = None
        try:
            connection = HTTPConnection('127.0.0.1', 18412, timeout=0.5)
            connection.request('POST', '/notifications',
                               body=json.dumps(payload, separators=(',', ':')).encode(),
                               headers={'Content-Type': 'application/json'})
            response = connection.getresponse()
            if not 200 <= response.status < 300:
                raise RuntimeError('S11 local sink explicitly rejected the notification.')
            body = response.read(4097)
            if len(body) > 4096:
                raise TimeoutError('S11 local sink result is oversized; query the existing request.')
            try:
                result = json.loads(body)
            except (ValueError, UnicodeDecodeError) as error:
                raise TimeoutError('S11 local sink result is invalid; query the existing request.') from error
            if result == {'outcome': 'failed'}:
                raise RuntimeError('S11 local sink explicitly failed the notification.')
            if result != {'outcome': 'accepted'}:
                raise TimeoutError('S11 local sink outcome is indeterminate; query the existing request.')
        except socket.timeout as error:
            raise TimeoutError('S11 local sink outcome is unknown; query the existing request.') from error
        except (OSError, HTTPException) as error:
            raise TimeoutError('S11 local sink connection outcome is unknown; query the existing request.') from error
        finally:
            if connection is not None:
                connection.close()
        # Preserve the native internal acceptance/contact history only after
        # explicit loopback acceptance. This never asserts patient delivery.
        return super()._send_transport(job)

import json

from odoo.tests import tagged

from .common import accepted
from .test_http import TestQueueHTTP


@tagged('post_install', '-at_install')
class TestQueueDayHTTP(TestQueueHTTP):
    def test_http_business_drain_close_and_permission(self):
        task = accepted(self)
        self.select('frontdesk')
        b = self.group.env['ydental.supply.service']._business_record(self.stores[0], self.areas[0][0].id)
        payload = {'area_id': self.areas[0][0].id, 'state': 'draining', 'reason': 'C HTTP stop', 'version': b.ydental_version}
        self.assertEqual(self.action('business', payload).status_code, 403)
        self.select('manager');self.assertEqual(self.action('business', payload).status_code, 200)
        self.assertIn('draining', self.url_open('/ydental/queue').text)
        payload.update(state='closed', version=b.ydental_version)
        self.assertEqual(self.action('business', payload).status_code, 409)
        self.assertEqual(task.state, 'accepted')

    def test_http_screen_token_readonly_revocation_and_rpc(self):
        accepted(self);self.select('manager')
        created = self.action('screen_create', {'area_id': self.areas[0][0].id})
        self.assertEqual(created.status_code, 200, created.text)
        token = created.json()['token']
        headers = {'Authorization': 'Bearer ' + token}
        response = self.url_open('/ydental/queue/screen/data', headers=headers)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(set(response.json()['rows'][0]), {'number', 'name', 'state', 'station'})
        self.assertNotIn(token, self.url_open('/ydental/queue/screen').text)
        self.assertEqual(self.url_open('/ydental/queue/screen/data').status_code, 403)
        self.assertIn('error', self.rpc('ydental.queue.screen.token', 'read', [[created.json()['credential_id']], ['ydental_token_hash']]))
        self.assertEqual(self.action('screen_revoke', {'credential_id': created.json()['credential_id']}).status_code, 200)
        self.assertEqual(self.url_open('/ydental/queue/screen/data', headers=headers).status_code, 403)
        self.assertEqual(self.url_open('/ydental/queue/screen/data?last_id=0', headers=headers).status_code, 403)

    def test_http_screen_actual_call_and_fault_snapshot(self):
        task=accepted(self);self.select();args=self.lease()
        call=self.action('call',args).json()
        created=self.group.env['ydental.queue.service']._operate('screen_create',{'area_id':self.areas[0][0].id})
        headers={'Authorization':'Bearer '+created['token']}
        first=self.url_open('/ydental/queue/screen/data',headers=headers).json()
        self.assertEqual(first['rows'][0]['station'],self.stations[0][0].name)
        self.assertEqual(self.action('missed',dict(args,entry_id=call['entry_id'])).status_code,200)
        second=self.url_open('/ydental/queue/screen/data',headers=headers).json()
        self.assertGreater(second['version'],first['version']);self.assertEqual(second['rows'][0]['state'],'waiting')
        self.assertEqual(second['rows'][0]['station'],'')

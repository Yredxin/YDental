import json
import re

from odoo.tests import HttpCase, tagged

from odoo.addons.ydental_treatment_test.tests.common import key
from odoo.addons.ydental_treatment_test.tests.treatment_common import setup


@tagged('post_install', '-at_install')
class TestExaminationHTTP(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup(cls)
        cls.admin._grant(cls.users['reader'].id, cls.stores[0].id,
                         {'medical': 'read', 'exam': 'read'})

    def _select(self, role):
        self.authenticate(self.users[role].login, 's05-test-password')
        page = self.url_open('/ydental/access')
        csrf = re.search(r'name="csrf_token" value="([^"]+)"', page.text).group(1)
        revision = int(re.search(r'name="revision" value="([0-9]+)"', page.text).group(1))
        response = self.url_open('/ydental/access/action', data={'csrf_token': csrf,
            'revision': revision, 'operation': 'switch',
            'payload': json.dumps({'store_id': self.stores[0].id}), 'output': 'json'})
        self.assertEqual(response.status_code, 200, response.text)
        return csrf, response.json()['revision'], key() + key()

    def _action(self, csrf, revision, connection, operation, payload):
        return self.url_open('/ydental/exam/action', data={'csrf_token': csrf,
            'revision': revision, 'connection': connection, 'operation': operation,
            'payload': json.dumps(payload), 'key': key()})

    def _rpc(self, model, method, args):
        return self.url_open('/web/dataset/call_kw/' + model + '/' + method,
            data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'call',
                'params': {'model': model, 'method': method, 'args': args,
                           'kwargs': {'context': {}}}}),
            headers={'Content-Type': 'application/json'}).json()

    def test_workbench_permission_csrf_and_untrusted_rpc(self):
        csrf, revision, connection = self._select('doctor')
        page = self.url_open('/ydental/exam')
        self.assertEqual(page.status_code, 200, page.text)
        self.assertIn('检查工作台', page.text)
        invalid = self._action(csrf, revision, connection, 'invented', {})
        self.assertEqual(invalid.status_code, 409)
        missing_csrf = self.url_open('/ydental/exam/action', data={'revision': revision,
            'connection': connection, 'operation': 'draft', 'payload': '{}', 'key': key()})
        self.assertEqual(missing_csrf.status_code, 400)
        forged = self._rpc('ydental.exam.result', 'create', [{'name': 'forged'}])
        self.assertIn('error', forged)
        hidden = self._rpc('ydental.exam.service', '_operate', ['perform', {}, key()])
        self.assertIn('error', hidden)
        csrf, revision, connection = self._select('reader')
        self.assertEqual(self.url_open('/ydental/exam').status_code, 200)
        denied = self._action(csrf, revision, connection, 'draft', {
            'line_id': 1, 'execution_id': 1, 'lease_id': 1, 'lease_token': 'invalid',
            'inline': False, 'version': 0, 'findings': '', 'measurements': {}, 'conclusion': ''})
        self.assertEqual(denied.status_code, 403)
        self._select('none')
        self.assertEqual(self.url_open('/ydental/exam').status_code, 403)

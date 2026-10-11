import json
from unittest.mock import patch

from lxml import html
from odoo.tests import HttpCase
from odoo.tests.common import Opener
from odoo.tools import mute_logger

from .test_s01 import TestS01


class IndependentOpener(Opener):
    """Independent native login cookies, preserving Odoo's test-cursor guard."""
    def request(self, *args, **kwargs):
        with patch.object(self.test_case, 'opener', self):
            return super().request(*args, **kwargs)


class TestS01HTTP(HttpCase, TestS01):

    def login_session(self, user):
        self.env.flush_all()
        client = IndependentOpener(self)
        response = client.post(self.base_url() + '/web/session/authenticate', json={
            'jsonrpc': '2.0', 'method': 'call',
            'params': {'db': self.env.cr.dbname, 'login': user.login, 'password': user.login},
        }, timeout=20)
        self.assertEqual(response.json().get('result', {}).get('uid'), user.id)
        return client

    def page_scope(self, client):
        response = client.get(self.base_url() + '/ydental/access', timeout=20)
        self.assertEqual(response.status_code, 200)
        page = html.fromstring(response.content)
        return page.xpath('//input[@name="csrf_token"]/@value')[0], int(page.xpath('//input[@name="revision"]/@value')[0])

    def action_http(self, client, operation, payload, old_revision=None):
        csrf, revision = self.page_scope(client)
        return client.post(self.base_url() + '/ydental/access/action', data={
            'csrf_token': csrf, 'revision': revision if old_revision is None else old_revision,
            'operation': operation, 'payload': json.dumps(payload), 'output': 'json',
        }, timeout=20)

    def rpc(self, client, model, method, ids, kwargs=None):
        return client.post(self.base_url() + '/web/dataset/call_kw', json={
            'jsonrpc': '2.0', 'method': 'call',
            'params': {'model': model, 'method': method, 'args': [ids], 'kwargs': kwargs or {}},
        }, timeout=20).json()

    def test_http_two_real_logins_and_stale_page(self):
        first = self.login_session(self.operator)
        second = self.login_session(self.operator)
        self.assertEqual(self.action_http(first, 'switch', {'store_id': self.a.id}).status_code, 200)
        self.assertEqual(self.action_http(second, 'switch', {'store_id': self.b.id}).status_code, 200)
        csrf, old = self.page_scope(first)
        source = self.records.filtered(lambda r: r.ydental_store_id == self.a and r.ydental_category == 'space')
        self.assertIn(source.ydental_text, first.get(self.base_url() + '/ydental/s01-synthetic').text)
        self.assertEqual(self.action_http(first, 'switch', {'store_id': self.b.id}).status_code, 200)
        response = first.post(self.base_url() + '/ydental/s01-synthetic/write', data={
            'csrf_token': csrf, 'revision': old, 'record_id': source.id, 'name': 'Stale synthetic update',
        }, timeout=20)
        self.assertEqual(response.status_code, 409)
        self.assertIn('version_conflict', response.text)
        self.assertNotEqual(source.name, 'Stale synthetic update')
        self.assertEqual(self.action_http(second, 'switch', {'store_id': self.c.id}).status_code, 200)
        self.assertIn(self.b.name, first.get(self.base_url() + '/ydental/access').text)

    def test_http_rpc_native_export_report_and_revoked_download(self):
        client = self.login_session(self.operator)
        self.action_http(client, 'switch', {'store_id': self.a.id})
        record = self.records.filtered(lambda r: r.ydental_store_id == self.a and r.ydental_category == 'space')
        self.assertIn('result', self.rpc(client, record._name, 'read', record.ids, {'fields': ['name']}))
        with mute_logger('odoo.http'):
            self.assertIn('error', self.rpc(client, record._name, 'write', record.ids, {'vals': {'name': 'No revision'}}))
            self.assertIn('error', self.rpc(client, record._name, 'export_data', record.ids, {'fields_to_export': ['name']}))
        self.admin._grant(self.operator.id, self.a.id, {'export': 'write'})
        self.env.flush_all()
        self.assertTrue(self.rpc(client, record._name, 'export_data', record.ids, {'fields_to_export': ['name']})['result']['datas'])
        params = {'model': record._name, 'fields': [{'name': 'name', 'label': 'Name'}],
                  'ids': record.ids, 'domain': [], 'import_compat': False, 'context': {}}
        csrf, _revision = self.page_scope(client)
        response = client.post(self.base_url() + '/web/export/csv', data={'data': json.dumps(params), 'csrf_token': csrf}, timeout=20)
        self.assertEqual(response.status_code, 200)
        self.assertIn(record.name, response.text)
        response = client.get(self.base_url() + '/report/html/ydental_access_test.ydental_synthetic_report/' + str(record.id), timeout=20)
        self.assertEqual(response.status_code, 200)
        self.assertIn(record.name, response.text)
        attachment = self.env['ir.attachment'].create({'name': 'S01 synthetic download', 'raw': b'SYNTHETIC_DOWNLOAD',
                                                       'res_model': record._name, 'res_id': record.id, 'public': True})
        self.env.flush_all()
        path = self.base_url() + '/web/content/' + str(attachment.id)
        self.assertEqual(client.get(path, timeout=20).content, b'SYNTHETIC_DOWNLOAD')
        self.admin._grant(self.operator.id, self.a.id, {'space': 'none', 'export': 'none'})
        self.env.flush_all()
        with mute_logger('odoo.http'):
            self.assertNotEqual(client.get(path, timeout=20).status_code, 200)
            self.assertIn('error', self.rpc(client, record._name, 'read', record.ids, {'fields': ['name']}))
            self.assertNotEqual(client.post(self.base_url() + '/web/export/csv', data={'data': json.dumps(params), 'csrf_token': csrf}, timeout=20).status_code, 200)
        self.assertIn('result', self.rpc(client, self.a._name, 'read', self.a.ids, {'fields': ['name']}))

    def test_http_template_preview_confirmation_and_portal_denial(self):
        manager = self.login_session(self.manager)
        self.action_http(manager, 'switch', {'store_id': self.a.id})
        template = self.env['ydental.access.template'].create({'name': 'Synthetic HTML template', 'ydental_levels': {'frontdesk': 'read'}})
        self.env.flush_all()
        csrf, revision = self.page_scope(manager)
        response = manager.post(self.base_url() + '/ydental/access/action', data={
            'operation': 'preview', 'revision': revision, 'csrf_token': csrf,
            'user_id': self.operator.id, 'template_id': template.id,
        }, timeout=20)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Confirm template changes', response.text)
        self.assertEqual(self.admin._levels(self.admin._membership(self.operator.id, self.a.id))['space'], 'write')
        form = html.fromstring(response.content)
        data = dict(zip(form.xpath('//input/@name'), form.xpath('//input/@value')))
        response = manager.post(self.base_url() + '/ydental/access/action', data=data, timeout=20)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.admin._levels(self.admin._membership(self.operator.id, self.a.id))['space'], 'none')
        with mute_logger('odoo.http'):
            anonymous = IndependentOpener(self)
            response = anonymous.get(self.base_url() + '/ydental/access', allow_redirects=False, timeout=20)
        self.assertEqual(response.status_code, 303)

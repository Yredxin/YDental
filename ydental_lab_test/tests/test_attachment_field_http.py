import base64
import json
import re
import secrets

from odoo import fields
from odoo.tests import HttpCase, new_test_user, tagged


def _key():
    return secrets.token_hex(12)


@tagged('post_install', '-at_install')
class TestLaboratoryAttachmentFieldHTTP(HttpCase):
    """Field-level attachment access must survive direct attachment URLs."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.root = cls.env['base'].sudo().env
        cls.store = cls.root['ydental.access.store'].create({
            'name': 'S11 synthetic attachment access store',
            'company_id': cls.root.company.id,
            'ydental_timezone': 'UTC',
        })
        password = 's11-attachment-http-test-password'
        suffix = _key()
        cls.manager = new_test_user(
            cls.root,
            name='S11 synthetic attachment manager',
            login='s11_attachment_manager_' + suffix,
            password=password,
            groups='ydental_base.ydental_base_group_user,ydental_access.ydental_group_manager',
            company_id=cls.root.company.id,
            company_ids=[fields.Command.set([cls.root.company.id])],
        )
        cls.warehouse = new_test_user(
            cls.root,
            name='S11 synthetic attachment warehouse user',
            login='s11_attachment_warehouse_' + suffix,
            password=password,
            groups='ydental_base.ydental_base_group_user',
            company_id=cls.root.company.id,
            company_ids=[fields.Command.set([cls.root.company.id])],
        )
        cls.password = password

        access = cls.root['ydental.access.service'].with_user(cls.manager)
        access = access._bind(access._session_for_key('s11-attachment-setup-' + suffix))
        access._join(cls.manager.id, cls.store.id)
        access._join(cls.warehouse.id, cls.store.id)
        access._grant(cls.manager.id, cls.store.id, {
            'medical': 'write', 'warehouse': 'write', 'followup': 'write',
        })
        access._grant(cls.warehouse.id, cls.store.id, {
            'medical': 'write', 'warehouse': 'write',
        })

        cls.marker = ('S11_SYNTHETIC_VENDOR_QUALIFICATION_' + suffix).encode()
        cls.vendor_name = 'S11 synthetic laboratory vendor ' + suffix
        partner = cls.root['res.partner'].create({'name': cls.vendor_name})
        vendor = access.env['ydental.lab.vendor'].create({
            'partner_id': partner.id,
            'company_ids': [fields.Command.set([cls.root.company.id])],
            'category': 'crown',
            'qualification_reference': 'S11 synthetic qualification ' + suffix,
            'valid_until': '2099-12-31',
            'qualification_evidence': base64.b64encode(cls.marker).decode(),
            'qualification_evidence_name': 'synthetic-qualification.txt',
        })
        cls.vendor_id = vendor.id
        attachment = access.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'ydental.lab.vendor'),
            ('res_id', '=', vendor.id),
            ('res_field', '=', 'qualification_evidence'),
        ], limit=1)
        assert attachment, 'synthetic manager-only evidence attachment must be created'
        cls.attachment_id = attachment.id

    def select_store(self, user):
        self.authenticate(user.login, self.password)
        page = self.url_open('/ydental/access')
        self.assertEqual(page.status_code, 200, page.text)
        csrf = re.search(r'name="csrf_token" value="([^"]+)"', page.text)
        revision = re.search(r'name="revision" value="([0-9]+)"', page.text)
        self.assertTrue(csrf)
        self.assertTrue(revision)
        response = self.url_open('/ydental/access/action', data={
            'csrf_token': csrf.group(1),
            'revision': int(revision.group(1)),
            'operation': 'switch',
            'payload': json.dumps({'store_id': self.store.id}),
            'output': 'json',
        })
        self.assertEqual(response.status_code, 200, response.text)
        self.revision = response.json()['revision']

    def rpc(self, model, method, args):
        response = self.url_open(
            '/web/dataset/call_kw/' + model + '/' + method,
            data=json.dumps({
                'jsonrpc': '2.0', 'id': 1, 'method': 'call',
                'params': {
                    'model': model,
                    'method': method,
                    'args': args,
                    'kwargs': {'context': {'ydental_revision': self.revision}},
                },
            }),
            headers={'Content-Type': 'application/json'},
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_manager_only_vendor_evidence_denied_by_field_and_direct_attachment_url(self):
        self.select_store(self.manager)
        manager_download = self.url_open('/web/content/%s?download=true' % self.attachment_id)
        self.assertEqual(manager_download.status_code, 200, manager_download.text)
        self.assertIn(self.marker, manager_download.content)

        self.select_store(self.warehouse)
        metadata = self.rpc('ydental.lab.vendor', 'read', [[self.vendor_id], ['name']])
        self.assertIn('result', metadata)
        self.assertEqual(metadata['result'][0]['name'], self.vendor_name)

        field_read = self.rpc('ydental.lab.vendor', 'read', [[self.vendor_id], ['qualification_evidence']])
        self.assertIn('error', field_read)
        self.assertNotIn(self.marker.decode(), json.dumps(field_read))

        denied_download = self.url_open('/web/content/%s?download=true' % self.attachment_id)
        self.assertIn(denied_download.status_code, (403, 404), denied_download.text)
        self.assertNotIn(self.marker, denied_download.content)

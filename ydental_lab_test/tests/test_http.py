import json
import secrets

from odoo import fields
from odoo.tests import HttpCase, new_test_user, tagged


def _key():
    return secrets.token_hex(16)


@tagged('post_install', '-at_install')
class TestLaboratoryHTTP(HttpCase):
    """Check normal authenticated backend RPC and guarded write boundaries."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.root = cls.env['base'].sudo().env
        cls.store = cls.root['ydental.access.store'].create({
            'name': 'S11 HTTP synthetic laboratory store',
            'company_id': cls.root.company.id,
            'ydental_timezone': 'UTC',
        })
        cls.users = {}
        for role, groups in (
            ('warehouse', 'ydental_base.ydental_base_group_user'),
            ('no_grant', 'ydental_base.ydental_base_group_user'),
        ):
            cls.users[role] = new_test_user(
                cls.root,
                name='S11 HTTP synthetic laboratory ' + role,
                login='s11_lab_http_' + role + '_' + _key()[:10],
                password='s11-lab-http-test-password',
                groups=groups,
                company_id=cls.root.company.id,
                company_ids=[fields.Command.set([cls.root.company.id])],
            )
        manager = new_test_user(
            cls.root,
            name='S11 HTTP synthetic laboratory manager',
            login='s11_lab_http_manager_' + _key()[:10],
            password='s11-lab-http-test-password',
            groups='ydental_base.ydental_base_group_user,ydental_access.ydental_group_manager',
            company_id=cls.root.company.id,
            company_ids=[fields.Command.set([cls.root.company.id])],
        )
        access = cls.root['ydental.access.service'].with_user(manager)
        access = access._bind(access._session_for_key('s11-lab-http-setup-' + _key()))
        for user in list(cls.users.values()) + [manager]:
            access._join(user.id, cls.store.id)
        access._grant(manager.id, cls.store.id, {
            'medical': 'write', 'warehouse': 'write', 'followup': 'write',
        })
        access._grant(cls.users['warehouse'].id, cls.store.id, {
            'medical': 'write', 'warehouse': 'write',
        })
        cls.manager = manager

    def login(self, role='warehouse'):
        user = self.users[role]
        self.authenticate(user.login, 's11-lab-http-test-password')

    def rpc(self, model, method, args, context=None):
        response = self.url_open(
            '/web/dataset/call_kw/' + model + '/' + method,
            data=json.dumps({
                'jsonrpc': '2.0', 'id': 1, 'method': 'call',
                'params': {
                    'model': model, 'method': method, 'args': args,
                    'kwargs': {'context': context or {}},
                },
            }),
            headers={'Content-Type': 'application/json'},
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_http_authenticated_backend_and_read_only_vendor_lookup(self):
        self.login()
        page = self.url_open('/web')
        self.assertEqual(page.status_code, 200, page.text)
        response = self.rpc('ydental.lab.vendor', 'search_read', [[], ['name', 'category', 'state']])
        self.assertIn('result', response)
        self.assertIsInstance(response['result'], list)

    def test_http_native_order_create_cannot_forge_clinical_source(self):
        self.login()
        response = self.rpc('ydental.lab.order', 'create', [{
            'name': 'Forged S11 HTTP laboratory order',
            'ydental_source_event_id': 999999991,
            'ydental_product_id': 999999992,
            'ydental_vendor_id': 999999993,
            'ydental_material': 'synthetic',
            'ydental_instructions': 'synthetic test payload',
            'ydental_internal_code': 'S11-HTTP-' + _key(),
            'ydental_teeth': [16],
        }])
        self.assertIn('error', response)
        self.assertNotIn('patient name', json.dumps(response).lower())
        self.assertNotIn('contact details', json.dumps(response).lower())

    def test_http_unknown_package_scan_does_not_return_patient_content(self):
        self.login()
        transient = self.rpc('ydental.lab.code.scan', 'create', [{
            'code': 'S11-UNKNOWN-PACKAGE-' + _key(),
        }])
        self.assertIn('result', transient)
        scan_id = transient['result']
        response = self.rpc('ydental.lab.code.scan', 'action_scan', [[scan_id]])
        self.assertIn('error', response)
        serialized = json.dumps(response).lower()
        for prohibited in ('ydental_patient_id', 'ydental_source_event_id', 'phone', 'email'):
            self.assertNotIn(prohibited, serialized)

    def test_http_model_read_is_limited_by_native_access_control(self):
        self.login('no_grant')
        # The model's read ACL is intentionally available to internal staff;
        # workflow writes still require a live server-bound store scope.
        response = self.rpc('ydental.lab.order', 'search_read', [[], ['name', 'state']])
        self.assertIn('result', response)
        self.assertIsInstance(response['result'], list)
        denied = self.rpc('ydental.lab.vendor', 'create', [{
            'qualification_reference': 'S11 HTTP unauthorized vendor',
            'valid_until': '2099-12-31',
        }])
        self.assertIn('error', denied)
        self.assertNotIn('patient', json.dumps(denied).lower())

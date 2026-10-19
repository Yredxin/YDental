import json
import re
import secrets

from odoo import fields
from odoo.tests import HttpCase, new_test_user, tagged


def _key():
    return secrets.token_hex(16)


@tagged('post_install', '-at_install')
class TestFollowupHTTP(HttpCase):
    """Exercise the authenticated follow-up HTTP boundary with synthetic identities."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.root = cls.env['base'].sudo().env
        cls.stores = cls.root['ydental.access.store'].create([
            {'name': 'S11 HTTP synthetic follow-up store A',
             'company_id': cls.root.company.id, 'ydental_timezone': 'UTC'},
            {'name': 'S11 HTTP synthetic follow-up store B',
             'company_id': cls.root.company.id, 'ydental_timezone': 'UTC'},
        ])
        cls.users = {}
        for role, groups in (
            ('manager', 'ydental_base.ydental_base_group_user,ydental_access.ydental_group_manager'),
            ('desk', 'ydental_base.ydental_base_group_user'),
            ('none', 'ydental_base.ydental_base_group_user'),
        ):
            cls.users[role] = new_test_user(
                cls.root,
                name='S11 HTTP synthetic ' + role,
                login='s11_http_' + role + '_' + _key()[:10],
                password='s11-http-test-password',
                groups=groups,
                company_id=cls.root.company.id,
                company_ids=[fields.Command.set([cls.root.company.id])],
            )

        admin = cls.root['ydental.access.service'].with_user(cls.users['manager'])
        admin_session = admin._session_for_key('s11-http-setup-' + _key())
        admin = admin._bind(admin_session)
        for store in cls.stores:
            for user in cls.users.values():
                admin._join(user.id, store.id)
            admin._grant(cls.users['manager'].id, store.id, {
                'patient': 'write', 'frontdesk': 'write', 'followup': 'write',
                'medical': 'read', 'warehouse': 'write',
            })
            admin._grant(cls.users['desk'].id, store.id, {
                'patient': 'write', 'frontdesk': 'write', 'followup': 'write', 'medical': 'read',
            })

        # The route action uses a current store patient relation. Establish this
        # through the patient service, not by hand-writing patient ORM records.
        admin._switch(cls.stores[0].id)
        patient_service = admin._bind(admin_session).env['ydental.patient.service']
        cls.patient_id = patient_service._operate('create', {
            'values': {'name': 'S11 HTTP Synthetic Follow-up Patient'},
        }, _key())['id']

    def select(self, role='desk'):
        user = self.users[role]
        self.authenticate(user.login, 's11-http-test-password')
        page = self.url_open('/ydental/access')
        self.assertEqual(page.status_code, 200, page.text)
        csrf = re.search(r'name="csrf_token" value="([^"]+)"', page.text)
        revision = re.search(r'name="revision" value="([0-9]+)"', page.text)
        self.assertTrue(csrf, 'access page must expose its request CSRF token')
        self.assertTrue(revision, 'access page must expose its current revision')
        self.csrf = csrf.group(1)
        response = self.url_open('/ydental/access/action', data={
            'csrf_token': self.csrf,
            'revision': int(revision.group(1)),
            'operation': 'switch',
            'payload': json.dumps({'store_id': self.stores[0].id}),
            'output': 'json',
        })
        self.assertEqual(response.status_code, 200, response.text)
        self.revision = response.json()['revision']

    def action(self, operation, payload, revision=None):
        return self.url_open('/ydental/followups/action', data={
            'csrf_token': self.csrf,
            'revision': self.revision if revision is None else revision,
            'operation': operation,
            'payload': json.dumps(payload),
        })

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

    def test_http_followup_preference_action_and_workbench(self):
        self.select('desk')
        response = self.action('set_preference', {
            'patient_id': self.patient_id,
            'opt_out': True,
            'preferred_channel': 'manual',
        })
        self.assertEqual(response.status_code, 200, response.text)
        page = self.url_open('/ydental/followups')
        self.assertEqual(page.status_code, 200, page.text)
        self.assertIn('Cache-Control', page.headers)
        self.assertIn('no-store', page.headers['Cache-Control'])

    def test_http_followup_denies_missing_business_grant_without_patient_disclosure(self):
        self.select('none')
        page = self.url_open('/ydental/followups')
        self.assertEqual(page.status_code, 403, page.text)
        denied = self.action('set_preference', {
            'patient_id': self.patient_id,
            'opt_out': False,
            'preferred_channel': 'email',
        })
        self.assertEqual(denied.status_code, 403, denied.text)
        self.assertNotIn('S11 HTTP Synthetic Follow-up Patient', denied.text)

    def test_http_followup_native_model_mutation_is_not_a_public_workflow(self):
        self.select('desk')
        result = self.rpc('ydental.followup', 'create', [[{'name': 'Forged S11 follow-up'}]])
        self.assertIn('error', result)
        self.assertNotIn('S11 HTTP Synthetic Follow-up Patient', json.dumps(result))
        result = self.rpc('ydental.followup.preference', 'create', [[{
            'name': 'Forged preference',
            'ydental_patient_id': self.patient_id,
        }]])
        self.assertIn('error', result)

    def test_http_followup_rejects_stale_store_revision(self):
        self.select('desk')
        stale = self.revision
        switch = self.url_open('/ydental/access/action', data={
            'csrf_token': self.csrf,
            'revision': self.revision,
            'operation': 'switch',
            'payload': json.dumps({'store_id': self.stores[1].id}),
            'output': 'json',
        })
        self.assertEqual(switch.status_code, 200, switch.text)
        response = self.action('set_preference', {
            'patient_id': self.patient_id,
            'opt_out': True,
            'preferred_channel': 'manual',
        }, revision=stale)
        self.assertEqual(response.status_code, 409, response.text)

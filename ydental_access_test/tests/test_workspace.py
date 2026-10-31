from odoo import fields

from .test_s01_http import TestS01HTTP


class TestWorkspace(TestS01HTTP):
    def test_workspace_current_store_and_revocation(self):
        self.operator.sudo().write({'company_ids': [fields.Command.link(self.company_a.id)]})
        self.admin._grant(self.operator.id, self.a.id, {'frontdesk': 'read'})
        client = self.login_session(self.operator)
        self.assertEqual(self.action_http(client, 'switch', {'store_id': self.a.id}).status_code, 200)
        self.env.flush_all()
        response = client.get(self.base_url() + '/ydental', timeout=20)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.a.name, response.text)
        self.assertIn('前台', response.text)
        self.assertIn('只读', response.text)
        self.assertNotIn('S01 Synthetic B', response.text)

        self.admin._grant(self.operator.id, self.a.id, {'frontdesk': 'none'})
        self.env.flush_all()
        response = client.get(self.base_url() + '/ydental', timeout=20)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('前台', response.text)
        self.assertNotIn('/ydental/intake', response.text)

        self.admin._grant(self.operator.id, self.a.id, {'price': 'read'})
        self.env.flush_all()
        response = client.get(self.base_url() + '/ydental', timeout=20)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('href="/ydental/intake"', response.text)
        if 'ydental.intake.service' in self.env.registry:
            self.assertIn('href="/ydental/intake/prices"', response.text)

    def test_workspace_without_store(self):
        client = self.login_session(self.operator)
        response = client.get(self.base_url() + '/ydental', timeout=20)
        self.assertEqual(response.status_code, 200)
        self.assertIn('尚未选择可用门店', response.text)
        self.assertNotIn(self.a.name, response.text)

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

        self.admin._grant(self.operator.id, self.a.id, {'frontdesk': 'none', 'space': 'none',
                                                        'medical': 'none', 'pharmacy': 'none'})
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
        if 'ydental.treatment.service' in self.env.registry:
            self.assertIn('href="/ydental/treatment?prices=1"', response.text)
        self.assertNotIn('/odoo/action-ydental_space.ydental_space_area_action', response.text)
        self.admin._grant(self.operator.id, self.a.id, {'price': 'none'})
        self.env.flush_all()
        response = client.get(self.base_url() + '/ydental', timeout=20)
        self.assertNotIn('href="/ydental/treatment?prices=1"', response.text)

    def test_workspace_space_and_price_entries_follow_current_grants(self):
        self.operator.sudo().write({'company_ids': [fields.Command.link(self.company_a.id)]})
        self.admin._grant(self.operator.id, self.a.id, {'price': 'read', 'space': 'read'})
        client = self.login_session(self.operator)
        self.assertEqual(self.action_http(client, 'switch', {'store_id': self.a.id}).status_code, 200)
        response = client.get(self.base_url() + '/ydental', timeout=20)
        if 'ydental.space.area' in self.env.registry:
            self.assertIn('/odoo/action-ydental_space.ydental_space_area_action', response.text)
            self.assertIn('/odoo/action-ydental_space.ydental_space_floor_action', response.text)
            self.assertIn('/odoo/action-ydental_space.ydental_space_station_action', response.text)
        if 'ydental.treatment.service' in self.env.registry:
            self.assertIn('href="/ydental/treatment?prices=1"', response.text)
        self.admin._grant(self.operator.id, self.a.id, {'space': 'write'})
        self.env.flush_all()
        response = client.get(self.base_url() + '/ydental', timeout=20)
        if 'ydental.space.area' in self.env.registry:
            self.assertIn('/odoo/action-ydental_space.ydental_space_area_action', response.text)
        self.admin._grant(self.operator.id, self.a.id, {'price': 'none', 'space': 'none'})
        self.env.flush_all()
        response = client.get(self.base_url() + '/ydental', timeout=20)
        self.assertNotIn('/odoo/action-ydental_space.ydental_space_area_action', response.text)
        self.assertNotIn('href="/ydental/treatment?prices=1"', response.text)

    def test_workspace_without_store(self):
        client = self.login_session(self.operator)
        response = client.get(self.base_url() + '/ydental', timeout=20)
        self.assertEqual(response.status_code, 200)
        self.assertIn('尚未选择可用门店', response.text)
        self.assertNotIn(self.a.name, response.text)

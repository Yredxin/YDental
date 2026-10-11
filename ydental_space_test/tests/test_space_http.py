import json
import re

from odoo.tests import HttpCase

from .common import setup_space


class TestSpaceHTTP(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup_space(cls)

    def rpc(self, model, method, args, context=None):
        response = self.url_open('/web/dataset/call_kw', data=json.dumps({
            'jsonrpc': '2.0', 'method': 'call', 'params': {'model': model, 'method': method,
                'args': args, 'kwargs': {'context': context or {'ydental_revision': self.page_revision}}}, 'id': 1,
        }), headers={'Content-Type': 'application/json'})
        return response.json()

    def select_store(self):
        page = self.url_open('/ydental/access')
        token = re.search(r'name="csrf_token" value="([^"]+)"', page.text).group(1)
        revision = int(re.search(r'name="revision" value="([0-9]+)"', page.text).group(1))
        response = self.url_open('/ydental/access/action', data={
            'csrf_token': token, 'operation': 'switch', 'revision': str(revision),
            'payload': json.dumps({'store_id': self.stores[0].id}), 'output': 'json',
        })
        self.assertEqual(response.status_code, 200)
        self.page_revision = response.json()['revision']

    def test_http_private_svg_and_forged_context(self):
        self.authenticate('s02_writer', 's02-test-password')
        self.select_store()
        # Login defaults to an authorized first store; no client-selected source bypass.
        svg = self.url_open('/ydental/space/resource/%s.svg' % self.resource.id)
        self.assertEqual(svg.status_code, 200)
        self.assertIn("sandbox", svg.headers['Content-Security-Policy'])
        foreign = self.root['ydental.space.resource'].create({'name': 'B private', 'ydental_kind': 'chair',
            'ydental_store_id': self.stores[1].id, 'ydental_svg': self.resource.ydental_svg})
        self.assertEqual(self.url_open('/ydental/space/resource/%s.svg' % foreign.id).status_code, 403)
        result = self.rpc('ydental.space.floor', 'write', [[self.floor.id], {'name': 'Forged',
            'ydental_version': self.floor.ydental_version}], {'ydental_revision': 999, 'ydental_binding': {'user_id': self.writer.id}})
        self.assertIn('error', result)
        self.assertEqual(self.floor.name, 'S02 Second floor')

    def test_http_readonly_rpc_and_source_attachment(self):
        self.authenticate('s02_reader', 's02-test-password')
        self.select_store()
        result = self.rpc('ydental.space.station', 'write', [[self.station.id], {'name': 'Denied',
            'ydental_version': self.station.ydental_version}])
        self.assertIn('error', result)
        result = self.rpc('ydental.space.resource', 'create', [{'name': 'Forged shared',
            'ydental_kind': 'chair', 'ydental_svg': self.resource.ydental_svg}])
        self.assertIn('error', result)
        self.assertEqual(self.station.name, 'S02 Chair 1')

    def test_http_rework_group_common_without_membership_or_space_grants(self):
        self.authenticate('s02_group_only', 's02-test-password')
        page = self.url_open('/ydental/access')
        self.page_revision = int(re.search(r'name="revision" value="([0-9]+)"', page.text).group(1))
        self.assertFalse(self.root['ydental.access.membership'].search([
            ('ydental_user_id', '=', self.group_only.id)]))
        self.assertFalse(self.root['ydental.access.grant'].search([
            ('ydental_membership_id.ydental_user_id', '=', self.group_only.id)]))
        values = {'name': 'HTTP group-only common', 'ydental_kind': 'chair', 'ydental_svg': self.resource.ydental_svg}
        created = self.rpc('ydental.space.resource', 'create', [[values]])
        self.assertNotIn('error', created)
        identifier = created['result'][0]
        self.assertIn('result', self.rpc('ydental.space.resource', 'write', [[identifier],
            {'name': 'HTTP independent group', 'ydental_version': 1}]))
        self.assertEqual(self.url_open('/ydental/space/resource/%s.svg' % identifier).status_code, 200)
        self.assertIn('result', self.rpc('ydental.space.resource', 'action_archive', [[identifier]]))
        self.assertIn('result', self.rpc('ydental.space.resource', 'action_unarchive', [[identifier]]))
        self.assertIn('error', self.rpc('ydental.space.resource', 'write', [[self.resource.id],
            {'name': 'Denied private', 'ydental_version': self.resource.ydental_version}]))
        self.assertIn('error', self.rpc('ydental.space.resource', 'create', [[values]],
            {'ydental_revision': self.page_revision, 'default_ydental_store_id': self.stores[1].id}))
        self.assertIn('error', self.rpc('ydental.space.resource', 'create', [[values]],
            {'ydental_revision': 999, 'ydental_binding': {'user_id': self.group_only.id}}))
        self.authenticate('s02_writer', 's02-test-password')
        self.select_store()
        self.assertIn('error', self.rpc('ydental.space.resource', 'write', [[identifier],
            {'name': 'Denied common', 'ydental_version': 4}]))
        self.authenticate('s02_reader', 's02-test-password')
        self.select_store()
        self.assertIn('result', self.rpc('ydental.space.resource', 'read', [[identifier], ['ydental_svg']]))
        self.authenticate('s02_portal', 's02-test-password')
        self.assertEqual(self.url_open('/ydental/space/resource/%s.svg' % identifier).status_code, 403)
        self.assertIn('error', self.rpc('ydental.space.resource', 'create', [[values]]))

    def test_http_rework_unarchive_requires_active_parent(self):
        self.authenticate('s02_writer', 's02-test-password')
        self.select_store()
        self.assertIn('result', self.rpc('ydental.space.station', 'action_archive', [[self.station.id]]))
        self.assertIn('result', self.rpc('ydental.space.area', 'action_archive', [[self.child.id]]))
        self.assertIn('error', self.rpc('ydental.space.station', 'action_unarchive', [[self.station.id]]))
        self.station.invalidate_recordset()
        self.assertFalse(self.station.active)
        self.assertEqual(self.item.ydental_station_id.id, self.station.id)
        # Direct write is subject to the same invariant as action_unarchive.
        self.assertIn('error', self.rpc('ydental.space.station', 'write', [[self.station.id],
            {'active': True, 'ydental_version': self.station.ydental_version}]))
        self.assertIn('result', self.rpc('ydental.space.area', 'action_unarchive', [[self.child.id]]))
        self.assertIn('result', self.rpc('ydental.space.station', 'action_unarchive', [[self.station.id]]))
        self.station.invalidate_recordset()
        self.assertTrue(self.station.active)

    def test_http_rework_rect_json_and_shape_switch(self):
        self.authenticate('s02_writer', 's02-test-password')
        self.select_store()
        for points in ([[[0, 0]]] * 10001, {'nested': {'text': 'x' * 65536}}, 'invalid'):
            self.child.invalidate_recordset()
            self.assertIn('error', self.rpc('ydental.space.area', 'write', [[self.child.id],
                {'ydental_points': points, 'ydental_version': self.child.ydental_version}]))
            self.floor.invalidate_recordset()
            self.assertIn('error', self.rpc('ydental.space.floor', 'action_save_geometry', [[self.floor.id],
                self.floor.ydental_version, [{'kind': 'area', 'id': self.child.id, 'values': {'ydental_points': points}}]]))
        self.child.invalidate_recordset()
        self.assertIn('result', self.rpc('ydental.space.area', 'write', [[self.child.id],
            {'ydental_shape': 'polygon', 'ydental_points': [[0, 0], [100, 0], [50, 80]],
             'ydental_version': self.child.ydental_version}]))
        self.child.invalidate_recordset()
        self.assertIn('result', self.rpc('ydental.space.area', 'write', [[self.child.id],
            {'ydental_shape': 'rect', 'ydental_version': self.child.ydental_version}]))
        snapshot = self.rpc('ydental.space.floor', 'action_snapshot', [[self.floor.id]])['result']
        area = next(area for area in snapshot['areas'] if area['id'] == self.child.id)
        self.assertEqual(area['ydental_shape'], 'rect')
        self.assertFalse(area['ydental_points'])

    def test_http_rework_inactive_capability_new_links_denied(self):
        self.authenticate('s02_writer', 's02-test-password')
        self.select_store()
        inactive = self.capabilities[3]
        inactive.sudo().write({'active': False})
        cases = [(self.resource, 'ydental_capability_ids'), (self.station, 'ydental_add_capability_ids'),
                 (self.station, 'ydental_remove_capability_ids')]
        for record, field in cases:
            for command in ([4, inactive.id, 0], [6, 0, [inactive.id]]):
                record.invalidate_recordset()
                self.assertIn('error', self.rpc(record._name, 'write', [[record.id],
                    {field: [command], 'ydental_version': record.ydental_version}]))
        historical = self.capabilities[0]
        historical.sudo().write({'active': False})
        self.assertIn('result', self.rpc(self.resource._name, 'write', [[self.resource.id],
            {'ydental_capability_ids': [[6, 0, [historical.id, self.capabilities[1].id]]],
             'ydental_version': self.resource.ydental_version}]))
        self.resource.invalidate_recordset()
        self.assertIn('result', self.rpc(self.resource._name, 'write', [[self.resource.id],
            {'ydental_capability_ids': [[3, historical.id, 0]], 'ydental_version': self.resource.ydental_version}]))
        self.resource.invalidate_recordset()
        self.assertIn('error', self.rpc(self.resource._name, 'write', [[self.resource.id],
            {'ydental_capability_ids': [[4, historical.id, 0]], 'ydental_version': self.resource.ydental_version}]))

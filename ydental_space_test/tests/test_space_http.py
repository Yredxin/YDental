import json

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
                'args': args, 'kwargs': {'context': context or {'ydental_revision': 1}}}, 'id': 1,
        }), headers={'Content-Type': 'application/json'})
        return response.json()

    def test_http_private_svg_and_forged_context(self):
        self.authenticate('s02_writer', 's02-test-password')
        page = self.url_open('/ydental/access')
        self.assertEqual(page.status_code, 200)
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
        self.url_open('/ydental/access')
        result = self.rpc('ydental.space.station', 'write', [[self.station.id], {'name': 'Denied',
            'ydental_version': self.station.ydental_version}])
        self.assertIn('error', result)
        result = self.rpc('ydental.space.resource', 'create', [{'name': 'Forged shared',
            'ydental_kind': 'chair', 'ydental_svg': self.resource.ydental_svg}])
        self.assertIn('error', result)
        self.assertEqual(self.station.name, 'S02 Chair 1')

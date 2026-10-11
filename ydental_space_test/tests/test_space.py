import base64

from odoo import fields
from odoo.addons.base.tests.common import BaseCommon
from odoo.exceptions import AccessError, UserError, ValidationError

from .common import SVG, bound, setup_space


class TestSpace(BaseCommon):
    # Every authorization assertion uses an explicitly bound independent role.
    # Keep BaseCommon from rebinding those recordsets to its unrelated default user.
    _test_user_groups = ()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup_space(cls)

    def setUp(self):
        super().setUp()
        self.service = bound(self, self.writer, self._testMethodName)
        self.floor = self.floor.with_env(self.service.env)
        self.station = self.station.with_env(self.service.env)
        self.area = self.area.with_env(self.service.env)
        self.child = self.child.with_env(self.service.env)
        self.item = self.item.with_env(self.service.env)
        self.resource = self.resource.with_env(self.service.env)

    def test_t01_tree_and_stable_identity(self):
        snapshot = self.floor.action_snapshot()
        self.assertEqual(snapshot['floor']['id'], self.floor.id)
        self.assertEqual(len(snapshot['stations']), 1)
        self.assertEqual(self.child.parent_id, self.area)
        self.assertEqual(self.station.ydental_queue_area_id, self.area)
        self.assertEqual(self.station.ydental_capability_ids.ids, self.capabilities[:1].ids)

    def test_t02_rename_move_preserves_reference(self):
        identifier = self.station.id
        art_x = self.item.ydental_x
        station_x = self.station.ydental_x
        self.station.write({'name': 'Renamed chair', 'ydental_x': 315, 'ydental_version': self.station.ydental_version})
        self.station.invalidate_recordset()
        self.assertEqual(self.station.id, identifier)
        self.assertEqual(self.item.ydental_station_id.id, identifier)
        self.assertEqual(self.station.ydental_x, 315)
        self.assertEqual(self.item.ydental_x, art_x + 315 - station_x)
        event = self.root['ydental.access.audit'].search([
            ('ydental_target_model', '=', self.station._name), ('ydental_target_id', '=', identifier),
            ('ydental_event', '=', 'space.modify')], limit=1)
        self.assertEqual(event.ydental_before['name'], 'S02 Chair 1')
        self.assertEqual(event.ydental_after['name'], 'Renamed chair')

    def test_t03_capability_union_add_remove(self):
        self.station.write({'ydental_add_capability_ids': [fields.Command.set(self.capabilities[1:3].ids)],
            'ydental_remove_capability_ids': [fields.Command.set(self.capabilities[:1].ids)],
            'ydental_version': self.station.ydental_version})
        self.assertEqual(set(self.station.ydental_capability_ids.ids), set(self.capabilities[1:3].ids))
        other = self.service.env['ydental.space.station'].create({'name': 'CBCT only',
            'ydental_store_id': self.stores[0].id, 'ydental_floor_id': self.floor.id,
            'ydental_area_id': self.child.id, 'ydental_kind': 'exam',
            'ydental_add_capability_ids': [fields.Command.set(self.capabilities[3:].ids)]})
        self.assertEqual(other.ydental_capability_ids.ids, self.capabilities[3:].ids)
        self.assertEqual(set(self.area.ydental_capability_ids.ids), set(self.capabilities[1:].ids))

    def test_t04_readonly_other_store_and_attachment(self):
        reader = bound(self, self.reader, 'reader')
        with self.assertRaises(AccessError):
            self.floor.with_env(reader.env).write({'name': 'Denied', 'ydental_version': self.floor.ydental_version})
        other = bound(self, self.writer, 'other', self.stores[1])
        with self.assertRaises(AccessError):
            self.resource.with_env(other.env).read(['ydental_svg'])
        attachment = self.root['ir.attachment'].create({'name': 'Synthetic source attachment', 'raw': b'SYNTHETIC',
            'res_model': self.floor._name, 'res_id': self.floor.id, 'public': True})
        with self.assertRaises(AccessError):
            attachment.with_env(other.env)._can_return_content('raw', 'forged')
        with self.assertRaises(AccessError):
            self.floor.with_user(self.writer).with_context(ydental_binding={}).search([])
        with self.assertRaises(AccessError):
            self.service.env['ydental.space.floor'].create({'name': 'Other category',
                'ydental_store_id': self.stores[0].id, 'ydental_category': 'medical'})

    def test_t05_svg_attack_matrix(self):
        attacks = [SVG.replace('<rect', '<script/> <rect'), SVG.replace('<rect', '<foreignObject/> <rect'),
            SVG.replace('<rect', '<image href="https://example.invalid/a"/> <rect'),
            SVG.replace('fill="#123456"', 'fill="url(https://example.invalid/a)"'),
            SVG.replace('<rect', '<rect onload="alert(1)"'), '<svg broken',
            '<!DOCTYPE svg [<!ENTITY e SYSTEM "file:///etc/passwd">]>' + SVG,
            SVG.replace('width="100"', 'width="inf"'), SVG.replace('viewBox="0 0 100 100"', ''),
            SVG + (' ' * 1048576), SVG.replace('<rect', '<use href="#a"/> <rect')]
        for attack in attacks:
            with self.subTest(attack_length=len(attack)), self.assertRaises(ValidationError), self.cr.savepoint():
                self.resource.write({'ydental_svg': attack, 'ydental_version': self.resource.ydental_version})
        self.assertIn('viewBox', self.resource.ydental_svg)
        self.assertNotIn('script', self.resource.ydental_svg)

    def test_t06_stale_versions_and_atomic_geometry(self):
        version = self.floor.ydental_version
        old = self.station.ydental_version
        self.station.write({'name': 'Editor A', 'ydental_version': old})
        with self.assertRaises(UserError):
            self.station.write({'name': 'Editor B', 'ydental_version': old})
        with self.assertRaises(UserError):
            self.floor.action_save_geometry(version, [{'kind': 'station', 'id': self.station.id, 'values': {'ydental_x': 400}}])
        self.assertEqual(self.station.name, 'Editor A')
        original = self.station.ydental_x
        with self.assertRaises(ValidationError):
            self.floor.action_save_geometry(self.floor.ydental_version, [
                {'kind': 'station', 'id': self.station.id, 'values': {'ydental_x': 450}},
                {'kind': 'station', 'id': self.station.id, 'values': {'ydental_width': -1}}])
        self.assertEqual(self.station.ydental_x, original)

    def test_t07_archive_and_cross_floor_guards(self):
        with self.assertRaises(AccessError):
            self.station.unlink()
        self.station.action_archive()
        self.assertFalse(self.station.active)
        self.assertEqual(self.item.ydental_station_id.id, self.station.id)
        with self.assertRaises(AccessError):
            self.station.write({'ydental_store_id': self.stores[1].id, 'ydental_version': self.station.ydental_version})
        with self.assertRaises((ValidationError, AccessError)), self.cr.savepoint():
            self.service.env['ydental.space.area'].create({'name': 'Wrong store', 'ydental_store_id': self.stores[1].id,
                'ydental_floor_id': self.floor.id})

    def test_t08_installed_dependencies_and_schema(self):
        module = self.root['ir.module.module'].search([('name', '=', 'ydental_space')])
        self.assertIn(module.state, ('installed', 'to upgrade', 'to install'))
        self.assertEqual(set(module.dependencies_id.mapped('name')), {'ydental_access', 'web'})
        self.assertEqual(self.floor.ydental_category, 'space')
        self.assertTrue(self.root.ref('ydental_space.ydental_space_resource_door'))

    def test_t09_reporting_ancestor_and_in_use_hook(self):
        self.station.sudo().write({'ydental_test_in_use': True, 'ydental_version': self.station.ydental_version})
        with self.assertRaises(UserError):
            self.child.write({'ydental_reporting': True, 'ydental_version': self.child.ydental_version})
        self.assertFalse(self.child.ydental_reporting)
        self.assertEqual(self.station.ydental_queue_area_id, self.area)
        self.station.sudo().write({'ydental_test_in_use': False, 'ydental_version': self.station.ydental_version})
        self.child.write({'ydental_reporting': True, 'ydental_version': self.child.ydental_version})
        self.assertEqual(self.station.ydental_queue_area_id, self.child)
        self.child.write({'ydental_prefix': 'SYN', 'ydental_missed_limit': 3,
                          'ydental_version': self.child.ydental_version})
        event = self.root['ydental.access.audit'].search([
            ('ydental_target_model', '=', self.child._name), ('ydental_target_id', '=', self.child.id),
            ('ydental_event', '=', 'space.modify')], order='id desc', limit=1)
        self.assertEqual(event.ydental_before['ydental_missed_limit'], 0)
        self.assertEqual(event.ydental_after['ydental_prefix'], 'SYN')
        self.assertEqual(event.ydental_after['ydental_missed_limit'], 3)
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.area.write({'parent_id': self.child.id, 'ydental_version': self.area.ydental_version})

    def test_t10_public_private_resources_and_runtime(self):
        public = self.root.ref('ydental_space.ydental_space_resource_chair').with_env(self.service.env)
        self.assertTrue(public.read(['ydental_svg']))
        with self.assertRaises(AccessError):
            public.write({'name': 'No group right', 'ydental_version': public.ydental_version})
        manager = bound(self, self.manager, 'manager')
        public = public.with_env(manager.env)
        public.write({'name': 'Group maintained', 'ydental_version': public.ydental_version})
        self.assertEqual(self.station._get_runtime_states()[0]['state'], 'not_connected')
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.station.write({'ydental_kind': 'settlement', 'ydental_version': self.station.ydental_version})

    def test_capability_commands_cannot_edit_dictionary(self):
        original = self.capabilities[0].name
        with self.assertRaises(ValidationError):
            self.station.write({'ydental_add_capability_ids': [(1, self.capabilities[0].id, {'name': 'Attack'})],
                'ydental_version': self.station.ydental_version})
        self.assertEqual(self.capabilities[0].name, original)
        for field, value in [('ydental_capability_ids', [fields.Command.set(self.capabilities.ids)]),
                             ('ydental_queue_area_id', self.child.id), ('write_uid', self.reader.id)]:
            with self.assertRaises(AccessError):
                self.station.write({field: value, 'ydental_version': self.station.ydental_version})

    def test_polygon_and_finite_geometry(self):
        values = {'name': 'Polygon', 'ydental_store_id': self.stores[0].id, 'ydental_floor_id': self.floor.id,
                  'ydental_shape': 'polygon', 'ydental_points': [[0, 0], [100, 0], [50, 80]]}
        polygon = self.service.env['ydental.space.area'].create(values)
        self.assertEqual(len(polygon.ydental_points), 3)
        for invalid in (float('nan'), float('inf'), 100001):
            with self.assertRaises(ValidationError), self.cr.savepoint():
                polygon.write({'ydental_x': invalid, 'ydental_version': polygon.ydental_version})

    def test_binary_upload_is_sanitized_and_bounded(self):
        self.resource.write({'ydental_upload': {'filename': 'synthetic.svg', 'content': base64.b64encode(SVG.encode()).decode()},
                             'ydental_version': self.resource.ydental_version})
        self.assertFalse(self.resource.ydental_upload)
        self.assertIn('viewBox', self.resource.ydental_svg)
        for raw in (b'not-valid-base64!', base64.b64encode(b'<!DOCTYPE svg>' + SVG.encode()), b'a' * 1500000):
            with self.assertRaises(ValidationError), self.cr.savepoint():
                self.resource.write({'ydental_upload': raw, 'ydental_version': self.resource.ydental_version})

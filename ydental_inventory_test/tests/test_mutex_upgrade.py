from odoo.tests import TransactionCase, tagged
from odoo.tools.convert import convert_file


@tagged('post_install', '-at_install')
class TestInventoryMutexUpgrade(TransactionCase):
    def test_update_preserves_existing_legacy_mutex_and_fence(self):
        env = self.env.sudo()
        mutex = env.ref('ydental_inventory.ydental_inventory_mutex')
        xmlid = env['ir.model.data'].search([
            ('module', '=', 'ydental_inventory'), ('name', '=', 'ydental_inventory_mutex')], limit=1)
        self.assertTrue(xmlid)
        # Exercise the real XML update reader with the legacy XMLID flag.
        xmlid.write({'noupdate': False})
        mutex.write({'ydental_revision': 41})
        convert_file(env, 'ydental_inventory', 'data/ydental_inventory_data.xml', {}, mode='update')
        mutex.invalidate_recordset(['ydental_revision'])
        self.assertEqual(mutex.ydental_revision, 41)
        env['ydental.inventory.service']._lock()
        mutex.invalidate_recordset(['ydental_revision'])
        self.assertEqual(mutex.ydental_revision, 42)
        convert_file(env, 'ydental_inventory', 'data/ydental_inventory_data.xml', {}, mode='update')
        mutex.invalidate_recordset(['ydental_revision'])
        self.assertEqual(mutex.ydental_revision, 42)

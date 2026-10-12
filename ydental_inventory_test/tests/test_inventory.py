from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase, tagged

from .common import bind, issue, key, op, quantity, receive, setup
from ..models.adapter import SyntheticSource


@tagged('post_install', '-at_install')
class TestInventory(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup(cls)

    def test_t01_f1_native_receipt_issue_retry(self):
        r = receive(self)
        k, source = key(), key()
        issued = issue(self, request_key=k, source_key=source)
        retry = issue(self, request_key=k, source_key=source)
        self.assertEqual(issued['id'], retry['id']); self.assertEqual(retry['result'], 'already_accepted')
        self.assertEqual(quantity(self), 7)
        self.assertEqual(self.root['stock.move'].browse(issued['move_id']).state, 'done')
        self.assertEqual(self.root['stock.move.line'].search_count([('move_id', '=', issued['move_id'])]), 1)
        self.assertEqual(issue(self, source_key=source)['id'], issued['id'])
        self.assertEqual(quantity(self), 7)

    def test_t01_key_collision_rolls_back(self):
        receive(self); k = key(); issue(self, request_key=k)
        before = self.root['ydental.inventory.event'].search_count([])
        with self.assertRaises(UserError): issue(self, quantity=1, request_key=k)
        self.assertEqual(quantity(self), 7); self.assertEqual(self.root['ydental.inventory.event'].search_count([]), before)

    def test_t02_shortage_has_no_half_move_or_audit(self):
        receive(self, 1)
        before = [self.root[m].search_count([]) for m in ('stock.move', 'stock.move.line', 'ydental.inventory.event', 'ydental.access.audit')]
        with self.assertRaises(UserError): issue(self, 2)
        self.assertEqual(quantity(self), 1)
        self.assertEqual(before, [self.root[m].search_count([]) for m in ('stock.move', 'stock.move.line', 'ydental.inventory.event', 'ydental.access.audit')])

    def test_t03_expired_disabled_product_and_forged_batch(self):
        receive(self)
        lot = self.stock._lot(self.lots['medicine'], self.stores[0])
        with patch.object(type(self.stock), '_now', return_value=lot.expiration_date):
            with self.assertRaisesRegex(UserError, 'lot_expired'): issue(self)
        op(self, 'lot_edit', lot_id=lot.id, enabled=False, reason='Synthetic batch stop')
        with self.assertRaisesRegex(UserError, 'lot_disabled'): issue(self)
        op(self, 'lot_edit', lot_id=lot.id, enabled=True, reason='Synthetic batch reopen')
        op(self, 'product_edit', service=self.group, product_id=self.products['medicine'], name='Inactive synthetic', active=False)
        with self.assertRaises(UserError): issue(self)
        with self.assertRaises(AccessError): issue(self, lot=99999999)
        self.assertEqual(quantity(self), 10)

    def test_t04_pack_and_small_quantity_conserve(self):
        op(self, 'receive', lot_id=self.lots['medicine'], quantity=1, uom_id=self.pack.id, source_key=key(), reason='One pack of ten')
        op(self, 'issue', lot_id=self.lots['medicine'], quantity=0.001, uom_id=self.pack.id, source_key=key(), reason='Actual 0.01 stock units')
        self.assertAlmostEqual(quantity(self), 9.99)
        event = self.root['ydental.inventory.event'].search([('ydental_kind', '=', 'replenishment')], order='id desc', limit=1)
        self.assertAlmostEqual(event.ydental_quantity, 0.01); self.assertEqual(event.ydental_unit_snapshot['input_factor'], 10)

    def test_t04_reject_silent_rounding_invalid_unit_nonfinite(self):
        receive(self)
        for q in (0.001, -1, float('inf'), float('nan'), True):
            with self.assertRaises(ValidationError): issue(self, q)
        with self.assertRaises(ValidationError):
            op(self, 'issue', lot_id=self.lots['medicine'], quantity=1, uom_id=self.root.ref('uom.product_uom_hour').id, source_key=key(), reason='Bad unit')
        self.assertEqual(quantity(self), 10)

    def test_t05_f1_return_quarantine_verify_refund(self):
        receive(self); issued = issue(self)
        returned = op(self, 'return', event_id=issued['id'], quantity=1, uom_id=self.uom.id, source_key=key(), reason='Physical package returned')
        self.assertEqual(quantity(self), 7); self.assertEqual(quantity(self, quarantine=True), 1)
        with self.assertRaises(AccessError): op(self, 'refund', event_id=issued['id'])
        self.assertEqual(quantity(self), 7)
        op(self, 'verify', event_id=returned['id'], quantity=1, uom_id=self.uom.id, disposition='release', source_key=key(), reason='Verified intact suitable batch')
        self.assertEqual(quantity(self), 8); self.assertEqual(quantity(self, quarantine=True), 0)

    def test_t05_return_limit_discard_and_consumption_no_automatic_restock(self):
        receive(self); issued = issue(self, 1)
        with self.assertRaises(UserError): op(self, 'return', event_id=issued['id'], quantity=2, uom_id=self.uom.id, source_key=key(), reason='Too much')
        returned = op(self, 'return', event_id=issued['id'], quantity=1, uom_id=self.uom.id, source_key=key(), reason='Physical damaged return')
        op(self, 'verify', event_id=returned['id'], quantity=1, uom_id=self.uom.id, disposition='discard', source_key=key(), reason='Actual damaged loss')
        self.assertEqual(quantity(self), 9); self.assertEqual(quantity(self, quarantine=True), 0)
        with self.assertRaises(UserError): op(self, 'verify', event_id=returned['id'], quantity=1, uom_id=self.uom.id, disposition='release', source_key=key(), reason='Double verification')

    def test_t06_f3_actual_pending_correction_original_price_recovery(self):
        doctor = bind(self, self.users['doctor'])
        source = SyntheticSource(self.users['doctor'].id, self.stores[0].id, key(), 'treatment', self.lots['material'], 2, self.uom.id, already_performed=True)
        pending = doctor._source_action(source)
        event = self.root['ydental.inventory.event'].browse(pending['id'])
        self.assertEqual(event.state, 'pending'); self.assertFalse(event.ydental_move_id)
        snapshot = dict(event.ydental_price_snapshot); reference = event.ydental_fee_reference
        self.assertEqual(doctor._source_action(source)['id'], event.id)
        with self.assertRaises(UserError): op(self, 'recover', event_id=event.id, reason='Still insufficient')
        receive(self, 5, self.lots['material'])
        with patch.object(type(self.stock), '_now', return_value=fields.Datetime.now()+timedelta(seconds=1)):
            op(self, 'recover', event_id=event.id, reason='Original event after evidence receipt')
        op(self, 'recover', event_id=event.id, reason='Recovery retry')
        self.assertEqual(event.state, 'done'); self.assertEqual(quantity(self, self.lots['material']), 3)
        self.assertEqual(event.ydental_price_snapshot, snapshot); self.assertEqual(event.ydental_fee_reference, reference)
        self.assertEqual(doctor._source_action(source)['id'], event.id)
        self.assertEqual(self.root['stock.move'].search_count([('origin', '=', 'YDental inventory event %s' % event.id)]), 1)
        self.assertTrue(event.ydental_synthetic)

    def test_t06_source_kind_unique_chairside_no_duplicate_prescription(self):
        receive(self)
        doctor = bind(self, self.users['doctor']); pharmacy = bind(self, self.users['pharmacy'])
        source_key = key()
        source = SyntheticSource(self.users['doctor'].id, self.stores[0].id, source_key, 'chairside', self.lots['medicine'], 2, self.uom.id)
        doctor._source_action(source)
        with self.assertRaises(UserError):
            pharmacy._source_action(SyntheticSource(self.users['pharmacy'].id, self.stores[0].id, source_key, 'prescription', self.lots['medicine'], 2, self.uom.id))
        self.assertEqual(quantity(self), 8)

    def test_t06_untrusted_dict_context_and_actor_failclosed(self):
        doctor = bind(self, self.users['doctor'])
        with self.assertRaises(AccessError): doctor._source_action({'kind': 'treatment', 'already_performed': True})
        with self.assertRaises(AccessError): doctor.with_context(ydental_inventory_source=True)._source_action({})
        with self.assertRaises(AccessError): doctor._source_action(SyntheticSource(self.users['stock'].id, self.stores[0].id, key(), 'treatment', self.lots['material'], 1, self.uom.id))

    def test_t07_cross_store_company_native_crud_export(self):
        receive(self)
        for store in self.stores[1:]:
            with self.assertRaises(AccessError): issue(self, service=bind(self, store=store))
        for model, ids in [('stock.lot', [self.lots['medicine']]), ('product.product', [self.products['medicine']]),
                ('stock.warehouse', [self.stock._config(self.stores[0]).ydental_warehouse_id.id])]:
            with self.assertRaises(AccessError): self.stock.env[model].browse(ids).read(['id'])
            with self.assertRaises(AccessError): self.stock.env[model].browse(ids).write({'name': 'Forged'})
            with self.assertRaises(AccessError): self.stock.env[model].browse(ids).export_data(['id'])
        with self.assertRaises(AccessError): self.stock.env['ydental.inventory.event'].search([]).unlink()
        with self.assertRaises(AccessError): self.stock.env['ydental.inventory.event'].create({'name': 'Forged'})

    def test_t07_native_stock_manager_cannot_bypass(self):
        receive(self); s = bind(self, self.users['stock2'])
        with self.assertRaises(AccessError): s.env['stock.quant'].search([]).write({'quantity': 999})
        with self.assertRaises(AccessError): s.env['stock.move'].create({'product_id': self.products['medicine']})
        with self.assertRaises(AccessError): s.env['stock.lot'].browse(self.lots['medicine']).read(['quant_ids', 'product_qty'])
        with self.assertRaises(AccessError): s.env['stock.quant'].search([])

    def test_t07_patient_and_public_attachment_denied(self):
        attachment = self.root['ir.attachment'].create({'name': 'Synthetic forbidden clinical attachment', 'res_model': 'stock.lot',
            'res_id': self.lots['medicine'], 'type': 'binary', 'raw': b'SYNTHETIC', 'public': True})
        with self.assertRaises(AccessError): attachment.with_env(self.stock.env).read(['raw'])
        with self.assertRaises(AccessError): attachment.with_env(self.stock.env)._can_return_content('raw')
        self.assertFalse(self.stock.env['ydental.patient.clinical'].search([]))

    def test_t07_revoke_next_request_old_tab(self):
        receive(self)
        self.admin._grant(self.users['stock'].id, self.stores[0].id, {'warehouse': 'none'})
        with self.assertRaises(AccessError): issue(self)
        with self.assertRaises(AccessError): self.stock._dashboard()
        with self.assertRaises(AccessError): self.stock.env['ydental.inventory.event'].search([])

    def test_t08_inventory_count_transfer_no_crosslegal(self):
        receive(self)
        op(self, 'inventory', lot_id=self.lots['medicine'], counted=8, uom_id=self.uom.id, source_key=key(), reason='Real counted evidence eight')
        self.assertEqual(quantity(self), 8)
        op(self, 'transfer', lot_id=self.lots['medicine'], quantity=3, uom_id=self.uom.id, target_store_id=self.stores[1].id, source_key=key(), reason='Physical same company handoff')
        self.assertEqual(quantity(self), 5); self.assertEqual(quantity(self, store=self.stores[1]), 3)
        with self.assertRaises(AccessError): op(self, 'transfer', lot_id=self.lots['medicine'], quantity=1, uom_id=self.uom.id, target_store_id=self.stores[2].id, source_key=key(), reason='Cross legal denied')
        self.assertEqual(quantity(self), 5)
        # Target lifecycle is independent; native manufacturer lot identity stays.
        target = bind(self, store=self.stores[1]); op(self, 'lot_edit', service=target, lot_id=self.lots['medicine'], enabled=False, reason='Target only stop')
        issue(self, 1)
        with self.assertRaises(UserError): issue(self, 1, service=target)

    def test_t08_target_grant_required_even_same_company(self):
        receive(self)
        self.admin._grant(self.users['stock'].id, self.stores[1].id, {'warehouse': 'read'})
        with self.assertRaises(AccessError): op(self, 'transfer', lot_id=self.lots['medicine'], quantity=1, uom_id=self.uom.id, target_store_id=self.stores[1].id, source_key=key(), reason='Target permission missing')
        self.assertEqual(quantity(self), 10)

    def test_t09_roles_master_price_warehouse_split(self):
        for role in ('stock', 'price', 'doctor', 'pharmacy', 'reader'):
            with self.assertRaises(AccessError): op(self, 'product', service=bind(self, self.users[role]))
        for role in ('price', 'catalog', 'doctor', 'pharmacy', 'none', 'reader'):
            with self.assertRaises(AccessError): receive_args = issue(self, service=bind(self, self.users[role]))
        catalog = bind(self, self.users['catalog'])._dashboard(catalog=True)
        self.assertTrue(catalog['products']); self.assertFalse(catalog['lots']); self.assertFalse(catalog['events'])
        with self.assertRaises(AccessError): self.stock.env['ydental.intake.service']._operate('price', {}, key())

    def test_t09_categories_dates_policy_scan_and_audit(self):
        self.assertFalse(self.stock._config(self.stores[0]).ydental_policy_configured)
        for lot in self.lots.values(): receive(self, 2, lot)
        op(self, 'policy', near_days=60, wait_days=0, low_quantity=3, reason='Synthetic alert policy only')
        dashboard = self.stock._dashboard()
        for row in dashboard['lots']:
            self.assertIn('near', row['flags']); self.assertIn('low', row['flags']); self.assertTrue(row['received_at'])
            if row['kind'] == 'prosthesis': self.assertIn('collection', row['flags'])
        self.assertEqual(self.stock._scan('UNSUPPORTED-OUTSOURCE'), {'result': 'unsupported_source', 'received': False})
        self.assertGreater(self.root['ydental.access.audit'].search_count([('ydental_event', 'like', 'inventory.%')]), 0)
        config = self.stock._config(self.stores[0])
        self.assertEqual(len({config.ydental_medicine_id.id, config.ydental_material_id.id, config.ydental_prosthesis_id.id, config.ydental_quarantine_id.id}), 4)

    def test_t09_lifecycle_and_direct_balance_guard(self):
        receive(self)
        for m in ('stock.quant', 'stock.move', 'stock.lot'):
            rec = self.root[m].search([('ydental_store_id', '=', self.stores[0].id)], limit=1)
            with self.assertRaises(AccessError): rec.write({'ydental_store_id': self.stores[1].id})
            with self.assertRaises(AccessError): rec.unlink()
        with self.assertRaises(AccessError): self.stock._config(self.stores[0]).write({'ydental_low_quantity': 0})

    def test_t06_real_s05_repricing_keeps_original_demo_snapshot(self):
        intake=self.group.env['ydental.intake.service'];now=fields.Datetime.now()
        capability=self.root['ydental.access.capability'].create({'name':'S07 synthetic treatment price','ydental_code':'s07_'+key()})
        catalog=intake._operate('catalog',{'code':key(),'name':'S07 demo treatment catalog','kind':'care','capability_id':capability.id,'uom_id':self.uom.id},key())['id']
        def publish(amount,previous=None):
            p=intake._operate('price',{'catalog_id':catalog,'currency_id':self.root.company.currency_id.id,'unit_price':amount,
                'start':fields.Datetime.to_string(now+timedelta(minutes=1) if previous else now-timedelta(days=1)),'end':fields.Datetime.to_string(now+timedelta(days=30)),'reason':'S07 synthetic actual S05 price'},key())
            p=intake._operate('review',{'record_id':p['id'],'version':p['version'],'reason':'S07 review'},key())
            args={'record_id':p['id'],'version':p['version'],'reason':'S07 publish'}
            if previous:
                old=self.root['ydental.intake.price'].browse(previous);args.update(replace_id=old.id,replace_version=old.ydental_version)
            return intake._operate('publish',args,key())['id']
        first=publish(20)
        snap=intake._operate('snapshot',{'catalog_id':catalog,'currency_id':self.root.company.currency_id.id,'quantity':2,'source':'S07-original-'+key(),'policy':'demo_confirmation'},key())['id']
        doctor=bind(self,self.users['doctor'])
        source=SyntheticSource(self.users['doctor'].id,self.stores[0].id,key(),'treatment',self.lots['material'],2,self.uom.id,already_performed=True,snapshot_id=snap)
        event=self.root['ydental.inventory.event'].browse(doctor._source_action(source)['id'])
        second=publish(99,first);self.assertNotEqual(second,first)
        version, quote=intake._quote(self.stores[0],catalog,self.root.company.currency_id.id,2,instant=now+timedelta(minutes=2))
        self.assertEqual(quote['ydental_unit_price'],99)
        receive(self,5,self.lots['material'])
        with patch.object(type(self.stock),'_now',return_value=now+timedelta(minutes=2)):
            op(self,'recover',event_id=event.id,reason='Real correction after actual S05 reprice')
        self.assertEqual(event.ydental_price_snapshot['unit_price'],20);self.assertEqual(event.ydental_price_snapshot['version'],str(first));self.assertEqual(event.ydental_price_snapshot['snapshot_id'],snap)
        self.assertEqual(doctor._source_action(source)['id'],event.id);self.assertEqual(quantity(self,self.lots['material']),3)

    def test_t08_zero_delta_count_retains_source_and_retry(self):
        receive(self,2);source=key()
        args={'lot_id':self.lots['medicine'],'counted':2,'uom_id':self.uom.id,'source_key':source,'reason':'Physical count matches current stock'}
        first=op(self,'inventory',args);retry=op(self,'inventory',args)
        self.assertEqual(first['id'],retry['id']);event=self.root['ydental.inventory.event'].browse(first['id'])
        self.assertEqual(event.state,'observed');self.assertFalse(event.ydental_move_id);self.assertEqual(quantity(self),2)

    def test_t04_used_unit_conversion_and_unrelated_issue_unit_rejected(self):
        with self.assertRaises(AccessError):self.pack.write({'relative_factor':12})
        with self.assertRaises(ValidationError):op(self,'product',service=self.group,code=key(),name='Invalid dimensions',kind='medicine',stock_uom_id=self.uom.id,issue_uom_id=self.root.ref('uom.product_uom_hour').id,step=0.01,specification='Synthetic invalid unit')

    def test_t06_already_performed_disabled_batch_keeps_pending_fact(self):
        receive(self,2,self.lots['material'])
        op(self,'lot_edit',lot_id=self.lots['material'],enabled=False,reason='Actual stop after performance')
        doctor=bind(self,self.users['doctor']);source=SyntheticSource(self.users['doctor'].id,self.stores[0].id,key(),'treatment',self.lots['material'],1,self.uom.id,already_performed=True)
        event=doctor._source_action(source);self.assertEqual(event['state'],'pending');self.assertFalse(event['move_id'])
        self.assertEqual(quantity(self,self.lots['material']),2)

    def test_t05_consumed_chairside_source_cannot_be_returned_as_unused(self):
        receive(self,2)
        doctor=bind(self,self.users['doctor'])
        source=SyntheticSource(self.users['doctor'].id,self.stores[0].id,key(),'chairside',self.lots['medicine'],1,self.uom.id)
        e=doctor._source_action(source)
        with self.assertRaises(UserError):op(self,'return',event_id=e['id'],quantity=1,uom_id=self.uom.id,source_key=key(),reason='Consumed medicine cannot reappear')
        self.assertEqual(quantity(self),1)

    def test_t09_product_low_alert_sums_usable_batches(self):
        receive(self,2)
        second=op(self,'lot',product_id=self.products['medicine'],name='S07-'+key(),expiration=fields.Datetime.to_string(fields.Datetime.now()+timedelta(days=30)))['id']
        receive(self,2,second)
        op(self,'policy',near_days=60,wait_days=0,low_quantity=3,reason='Synthetic aggregate threshold')
        rows=[r for r in self.stock._dashboard()['lots'] if r['product_id']==self.products['medicine']]
        self.assertTrue(all('low' not in r['flags'] for r in rows))
        op(self,'lot_edit',lot_id=second,enabled=False,reason='Store stops second lot')
        rows=[r for r in self.stock._dashboard()['lots'] if r['product_id']==self.products['medicine']]
        self.assertTrue(all('low' in r['flags'] for r in rows))
        stopped=next(r for r in rows if r['id']==second);self.assertEqual(stopped['quantity'],0);self.assertEqual(stopped['on_hand'],2)

    def test_t09_product_hook_default_failclosed(self):
        from odoo.addons.ydental_inventory.models.ydental_inventory_service import YDentalInventoryService
        with self.assertRaises(AccessError):YDentalInventoryService._authorize_source(self.stock,{'kind':'treatment'})

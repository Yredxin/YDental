"""Real service regressions for GPT-REVIEW 6135903692, before product fixes."""
from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

from .common import handover_args, key, price
from .treatment_common import opened_actual, pharmacy_start, receive, setup


@tagged('post_install', '-at_install')
class TestReworkBoundaries(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup(cls)

    def chairside(self, args, rows, quantity=2, actual=False):
        return args | {'catalog_id': self.drug_catalog.id, 'quantity': quantity,
            'source': key(), 'reason': 'Explicit synthetic chairside fact',
            'materials': rows, 'teeth': [], 'already_performed': actual, 'policy': 'demo_confirmation'}

    def line(self, **values):
        return dict(mapping_id=self.drug_mapping.id, quantity=6, uom_id=self.uom.id,
            product_id=self.products['medicine'], specification='Synthetic specification',
            usage='Synthetic usage', frequency='Synthetic frequency', course='Synthetic course', **values)

    def test_rework_chairside_empty_batch_must_not_confirm_fee(self):
        price(self, catalog=self.drug_catalog, amount=10)
        s,c,q,l,e,d,a = opened_actual(self)
        with self.assertRaises(UserError):
            s._operate('execute', self.chairside(a, []), key())
        self.assertFalse(s._model('event').search_count([('ydental_execution_id', '=', e.id)]))

    def test_rework_chairside_quantity_mismatch_must_not_confirm_fee(self):
        receive(self, 20, 'medicine'); price(self, catalog=self.drug_catalog, amount=10)
        s,c,q,l,e,d,a = opened_actual(self)
        row = {'lot_id': self.lots['medicine'], 'quantity': 1, 'uom_id': self.uom.id, 'kind': 'chairside'}
        with self.assertRaises(UserError):
            s._operate('execute', self.chairside(a, [row], quantity=2), key())
        self.assertFalse(s._model('event').search_count([('ydental_execution_id', '=', e.id)]))

    def test_rework_incomplete_rx_draft_allowed_but_issue_rejected(self):
        s,c,q,l,e,d,a = opened_actual(self)
        line = self.line(); line.update(specification='', usage='  ', frequency='', course='')
        draft = s._operate('order', a | {'kind': 'prescription', 'purpose': 'Incomplete synthetic draft', 'lines': [line]}, key())
        with self.assertRaises(UserError):
            s._operate('issue', a | {'order_id': draft['order_id'], 'version': draft['version']}, key())
        self.assertEqual(s._model('order').browse(draft['order_id']).state, 'draft')
        self.assertFalse(s._model('segment').search_count([('ydental_order_id', '=', draft['order_id'])]))

    def test_rework_second_sku_cannot_borrow_generic_service_price(self):
        product = self.stock._operate('product', {'code': 'R-' + key(), 'name': 'Distinct synthetic medicine B',
            'kind': 'medicine', 'stock_uom_id': self.uom.id, 'issue_uom_id': self.uom.id, 'step': 1,
            'specification': 'Distinct SKU specification'}, key())['id']
        lot = self.stock._operate('lot', {'product_id': product, 'name': 'R-' + key(),
            'expiration': str(fields.Datetime.now() + timedelta(days=45))}, key())['id']
        self.stock._operate('receive', {'lot_id': lot, 'quantity': 20, 'uom_id': self.uom.id,
            'source_key': key(), 'reason': 'Physical synthetic medicine B'}, key())
        price(self, catalog=self.drug_catalog, amount=10)
        s,c,q,l,e,d,a = opened_actual(self)
        line = self.line(); line['product_id'] = product
        draft = s._operate('order', a | {'kind': 'prescription', 'purpose': 'Unproven SKU fee source', 'lines': [line]}, key())
        issued = s._operate('issue', a | {'order_id': draft['order_id'], 'version': draft['version']}, key())
        c._operate('handover', handover_args(d,l))
        p,args = pharmacy_start(self, issued)
        with self.assertRaises(UserError):
            p._operate('dispense', args | {'line_id': issued['line_ids'][0], 'lot_id': lot,
                'quantity': 4, 'source': key(), 'reason': 'No authorized SKU price link', 'policy': 'demo_confirmation'}, key())
        self.assertEqual(p._remaining(p._model('line').browse(issued['line_ids'][0])), 6)

    def test_rework_source_only_company_can_initiate_controlled_cross_legal_referral(self):
        s,c,q,l,e,d,a = opened_actual(self)
        company = self.root['res.company'].create({'name': 'Rework synthetic target legal entity'})
        store = self.root['ydental.access.store'].create({'name': 'Rework target ' + key(), 'company_id': company.id, 'ydental_timezone': 'UTC'})
        floor = self.root['ydental.space.floor'].create({'name': 'Rework floor', 'ydental_store_id': store.id})
        area = self.root['ydental.space.area'].create({'name': 'Rework care', 'ydental_store_id': store.id,
            'ydental_floor_id': floor.id, 'ydental_purpose': 'care', 'ydental_reporting': True})
        self.root['ydental.space.station'].create({'name': 'Rework target chair', 'ydental_store_id': store.id,
            'ydental_floor_id': floor.id, 'ydental_area_id': area.id, 'ydental_add_capability_ids': [fields.Command.set(self.capabilities[0].ids)]})
        mapping = self.root['ydental.intake.mapping']._new({'name': 'Rework cross legal target',
            'ydental_store_id': store.id, 'ydental_category': 'frontdesk', 'ydental_catalog_id': self.catalogs[0].id,
            'ydental_area_id': area.id, 'ydental_execution_area_id': area.id})
        self.assertNotIn(company, self.users['doctor'].company_ids)
        result = s._operate('refer', a | {'mode': 'untimed', 'mapping_id': mapping.id,
            'reason': 'S05 trusted source, no arbitrary target write', 'valid_until': str(fields.Datetime.now() + timedelta(days=1)), 'source': key()}, key())
        self.assertEqual(result['target_qualification'], 'not_acquired')
        self.assertEqual(e.state, 'serving')

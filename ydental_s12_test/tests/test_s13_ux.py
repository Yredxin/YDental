"""S13 affected MODEL checks on independent rollback-only synthetic sources.

No historical object or committed economic chain is replayed. Browser, durable
state, page appearance and QR decoding require their own separate evidence.
"""
import copy
import hashlib
from unittest.mock import patch

from odoo import Command
from odoo.addons.base.tests.common import DISABLED_MAIL_CREATE_CONTEXT
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, tagged

from odoo.addons.ydental_treatment_test.tests.common import bind, key, save_args
from odoo.addons.ydental_treatment_test.tests.treatment_common import opened_actual, setup


@tagged('post_install', '-at_install', 's13_ux')
class TestS13UX(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env['base'].with_context(**DISABLED_MAIL_CREATE_CONTEXT).env
        synthetic_supply = patch.object(type(cls.env['ydental.supply.service']), '_allow_demo_supply', return_value=True)
        synthetic_supply.start()
        cls.addClassCleanup(synthetic_supply.stop)
        root = cls.env['base'].sudo().env
        root.ref('base.group_user').write({'implied_ids': [
            Command.link(root.ref('stock.group_stock_multi_warehouses').id),
            Command.link(root.ref('stock.group_stock_multi_locations').id),
        ]})
        setup(cls)

    def _patient(self, name, service=None):
        actor = self.front if service is None else service
        ident = actor.env['ydental.patient.service']._operate('create', {
            'values': {'name': name, 'phone': '', 'email': ''}}, key())['id']
        return self.root['ydental.patient'].browse(ident)

    def test_settlement_patient_search_is_paged_minimal_and_current_store_only(self):
        term = 'S13 same-name ' + key()
        patients = self.root['ydental.patient']
        for _index in range(31):
            patients |= self._patient(term)
        outside = self._patient(term, bind(self, self.users['frontdesk'], self.stores[1]))
        self.admin._grant(self.users['reader'].id, self.stores[0].id, {'settlement': 'read', 'frontdesk': 'none'})
        settlement = bind(self, self.users['reader']).env['ydental.settlement.service']
        first = settlement._patient_options(term)
        second = settlement._patient_options(term, page=2)
        self.assertEqual((len(first['rows']), len(second['rows'])), (30, 1))
        self.assertTrue(first['has_more'])
        self.assertFalse(second['has_more'])
        rows = first['rows'] + second['rows']
        self.assertEqual({row['id'] for row in rows}, set(patients.ids))
        self.assertNotIn(outside.id, {row['id'] for row in rows})
        self.assertTrue(all(set(row) == {'id', 'name', 'number'} for row in rows))
        self.assertEqual(len({row['number'] for row in rows}), 31)
        exact = settlement._patient_options(patients[0].ydental_number)
        self.assertEqual([row['id'] for row in exact['rows']], patients[0].ids)
        self.assertFalse(settlement._patient_options('not-found-' + key())['rows'])
        self.admin._grant(self.users['reader'].id, self.stores[0].id, {'settlement': 'none'})
        with self.assertRaises(AccessError):
            settlement._patient_options(term)

    def test_patient_and_inventory_search_reject_invalid_pages_before_reading(self):
        self.admin._grant(self.users['reader'].id, self.stores[0].id, {'settlement': 'read'})
        settlement = bind(self, self.users['reader']).env['ydental.settlement.service']
        for arguments in ({'term': 'x' * 101}, {'page': 0}, {'page': True}, {'page': 10001}):
            with self.subTest(arguments=arguments), self.assertRaises(ValidationError):
                settlement._patient_options(**arguments)
            with self.subTest(inventory_arguments=arguments), self.assertRaises(ValidationError):
                self.stock._dashboard(**arguments)

    def test_inventory_search_pages_sources_and_never_projects_clinical_identifiers(self):
        lot = self.root['stock.lot'].browse(self.lots['material'])
        identifiers = set()
        for _index in range(31):
            result = self.stock._operate('receive', {'lot_id': lot.id, 'quantity': 1,
                'uom_id': self.uom.id, 'source_key': key(), 'reason': 'S13 rollback source search fixture'}, key())
            identifiers.add(result['id'])
        first = self.stock._dashboard(term=lot.name)
        second = self.stock._dashboard(term=lot.name, page=2)
        self.assertEqual((len(first['events']), len(second['events'])), (30, 1))
        self.assertTrue(first['has_more_events'])
        self.assertFalse(second['has_more_events'])
        self.assertEqual({row['id'] for row in first['events'] + second['events']}, identifiers)
        self.assertTrue(all(row['name'] == lot.name for row in first['visible_lots']))
        self.assertTrue(all(not ({'patient_id', 'clinical_document_id', 'attachments'} & set(row))
                            for row in first['events'] + second['events']))
        self.assertFalse(self.stock._dashboard(term='not-found-' + key())['events'])
        self.assertFalse(self.stock._dashboard(event_id=max(identifiers) + 999999)['events'])
        with self.assertRaises(AccessError):
            bind(self, self.users['none']).env['ydental.inventory.service']._dashboard(term=lot.name)

    def test_report_options_recheck_source_permissions_without_broadening_store_scope(self):
        self.admin._grant(self.users['doctor'].id, self.stores[0].id, {'settlement': 'read'})
        report = bind(self, self.users['doctor']).env['ydental.reporting.service']
        options = report._selection_options('collections')
        self.assertEqual({row['id'] for row in options['stores']}, {self.stores[0].id})
        self.assertEqual({row['id'] for row in options['companies']}, {self.stores[0].company_id.id})
        self.assertTrue(options['money'])
        self.assertFalse(report._selection_options('arrivals')['money'])
        with self.assertRaises(ValidationError):
            report._selection_options('collections', state='done')
        with self.assertRaises(ValidationError):
            report._selection_options('not-a-metric')
        self.admin._grant(self.users['doctor'].id, self.stores[0].id, {'settlement': 'none', 'export': 'write'})
        self.assertFalse(report._selection_options('collections')['stores'])

    def test_report_presentation_preserves_machine_results_and_domain_specific_state(self):
        self._patient('S13 report source ' + key())
        report = bind(self, self.users['doctor']).env['ydental.reporting.service'].with_context(lang='zh_CN')
        today = self.group.env['ydental.supply.service']._date(self.stores[0])
        result = report._query('arrivals', str(today), str(today))
        before = copy.deepcopy(result)
        shown = report._display_time('2026-10-24 04:05:06.123456', self.stores[0])
        self.assertIn('2026-', shown)
        self.assertIn(self.stores[0].ydental_timezone, shown)
        self.assertEqual(shown, report._display_time('2026-10-24 04:05:06', self.stores[0]))
        display = report._presentation(result)
        self.assertEqual(result, before)
        self.assertIn('title', display)
        self.assertIn('scope', display)
        self.assertNotEqual(report._state_label('done', 'refunds'), report._state_label('done', 'consumption'))
        self.assertNotEqual(report._state_label('sent', 'lab_pending'), report._state_label('received', 'lab_pending'))

    def test_new_document_layout_paper_scope_and_immutable_published_templates(self):
        printing = bind(self, self.users['manager']).env['ydental.print.service']
        arguments = {'name': 'S13 compact synthetic label', 'kind': 'lab_label', 'version': key(),
                     'body': 'Synthetic demonstration only', 'applicability': 'S13 software label only',
                     'paper': 'label100x70', 'synthetic': True}
        result = printing._original_operate('template_create', arguments)
        for action in ('review', 'publish'):
            printing._original_operate('template_review', {'template_id': result['template_id'], 'action': action})
        template, facts, checksum = printing._original_template_facts('lab_label', result['template_id'])
        self.assertEqual(facts['paper'], 'label100x70')
        self.assertEqual(facts['paperformat']['page_width'], 100)
        self.assertEqual(facts['paperformat']['page_height'], 70)
        self.assertTrue(facts.get('layout_version'))
        before = template.read(['body', 'paper', 'version', 'state'])
        with self.assertRaises((AccessError, ValidationError)):
            template.write({'paper': 'a4'})
        self.assertEqual(template.read(['body', 'paper', 'version', 'state']), before)
        with self.assertRaises(ValidationError):
            printing._original_operate('template_create', dict(arguments, kind='clinical', version=key()))
        with self.assertRaises(AccessError):
            bind(self, self.users['none']).env['ydental.print.service']._original_operate('template_create', dict(arguments, version=key()))

    def test_document_patient_search_preserves_saved_original_bytes_and_scope(self):
        treatment, clinical, queue, lease, execution, document, arguments = opened_actual(self)
        document.update(clinical._operate('confirm', save_args(document, 'S13 synthetic document search source')))
        printing = clinical.env['ydental.print.service'].with_context(lang='zh_CN')
        selection = {'kind': 'clinical', 'source_id': document['document_id'], 'version': document['version']}
        preview = printing._original_operate('preview', selection)
        generated = printing._original_operate('generate', dict(selection, expected_digest=preview['source_digest'], key=key()))
        old_bytes, old_checksum = printing._original_operate('download', {'original_id': generated['original_id']})
        patient = execution.ydental_patient_id
        exact = printing._original_workbench(term=patient.ydental_number, page=999)
        self.assertEqual([row['id'] for row in exact['originals']], [generated['original_id']])
        self.assertEqual(exact['pagination']['page'], 1)
        self.assertEqual(exact['pagination']['total'], 1)
        self.assertTrue(all(choice['patient_number'] == patient.ydental_number for choice in exact['choices']))
        missing = printing._original_workbench(term='not-found-' + key())
        self.assertFalse(missing['originals'])
        self.assertFalse(missing['choices'])
        other = bind(self, self.users['doctor'], self.stores[1]).env['ydental.print.service']
        self.assertFalse(other._original_workbench(term=patient.ydental_number)['originals'])
        with self.assertRaises(AccessError):
            other._original_operate('download', {'original_id': generated['original_id']})
        returned, checksum = printing._original_operate('download', {'original_id': generated['original_id']})
        self.assertEqual(returned, old_bytes)
        self.assertEqual(checksum, old_checksum)
        self.assertEqual(hashlib.sha256(returned).hexdigest(), generated['sha256'])
        for arguments in ({'term': 'x' * 101}, {'page': 0}, {'page': True}):
            with self.assertRaises(ValidationError):
                printing._original_workbench(**arguments)

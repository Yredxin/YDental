import base64
from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase, tagged

from odoo.addons.ydental_treatment_test.tests.common import (
    key, price, queue_bind, lease_args, handover_args, make_slot, serving, save_args,
)
from odoo.addons.ydental_treatment_test.tests.treatment_common import setup, opened_actual


@tagged('post_install', '-at_install')
class TestExamination(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup(cls)

    def _bind_templates(self):
        service = self.doctor.env['ydental.exam.service']
        for catalog, code in ((self.catalogs[2], 'panorama-demo-1'),
                              (self.catalogs[3], 'cbct-demo-1')):
            service._operate('bind_template', {'catalog_id': catalog.id, 'code': code,
                'reason': 'Synthetic reviewed template association'}, key())

    def _order(self, treatment, args, indexes=(2, 3)):
        def row(index):
            return {'mapping_id': self.mappings[0][index].id, 'quantity': 1,
                'uom_id': self.uom.id, 'product_id': False, 'specification': '',
                'usage': '', 'frequency': '', 'course': ''}
        created = treatment._operate('order', args | {'kind': 'exam',
            'purpose': 'Synthetic independent examination', 'lines': [row(i) for i in indexes]}, key())
        return treatment._operate('issue', args | {'order_id': created['order_id'],
            'version': created['version']}, key())

    def _external_start(self, issued, index=0, user=None):
        task = self.root['ydental.intake.task'].browse(issued['task_ids'][index])
        self.front._operate('report', {'task_id': task.id, 'version': task.ydental_version}, key())
        examiner = queue_bind(self, user or self.second)
        lease = examiner._operate('enter', {'station_id': self.stations[0][2 + index].id})
        called = examiner._operate('call', lease_args(lease))
        self.assertEqual(called['task_id'], task.id)
        started = examiner._operate('start', lease_args(lease) | {'entry_id': called['entry_id']})
        args = {'line_id': issued['line_ids'][index], 'execution_id': started['execution_id'],
            'lease_id': lease['lease_id'], 'lease_token': lease['token'], 'inline': False}
        return examiner.env['ydental.exam.service'], args

    def _complete_external(self, service, action):
        draft = service._operate('draft', action | {'version': 0,
            'findings': '合成影像所见待人工复核', 'measurements': {}, 'conclusion': ''}, key())
        actual = service._operate('perform', action | {'reason': '真实合成检查实施', 'materials': []}, key())
        confirmed = service._operate('confirm', {'line_id': action['line_id'],
            'version': draft['version'], 'reason': '人工确认所见'}, key())
        service._operate('finish', action | {'reason': '真实检查段结束'}, key())
        return actual, confirmed

    def test_f1_exact_catalog_price_result_and_pdf(self):
        self._bind_templates()
        price(self, 80, catalog=self.catalogs[2])
        with patch.object(type(self.group.env['ydental.supply.service']), '_allow_demo_supply', return_value=True):
            treatment, clinical, queue, lease, medical, document, args = opened_actual(self)
        issued = self._order(treatment, args)
        clinical._operate('handover', handover_args(document, lease))
        service, action = self._external_start(issued)
        draft = service._operate('draft', action | {'version': 0,
            'findings': '合成全景所见待人工复核', 'measurements': {}, 'conclusion': ''}, key())
        perform_args = action | {'reason': '实际完成合成全景', 'materials': []}
        perform_key = key()
        actual = service._operate('perform', perform_args, perform_key)
        replay = service._operate('perform', perform_args, perform_key)
        self.assertEqual((replay['result'], replay['event_id']), ('already_accepted', actual['event_id']))
        event = self.root['ydental.treatment.event'].browse(actual['event_id'])
        fee = self.root['ydental.treatment.fee'].browse(actual['fee_id'])
        self.assertEqual((actual['state'], actual['event_state'], event.state), ('confirmed', 'confirmed', 'confirmed'))
        self.assertEqual((actual['result_document_state'], actual['order_line_state'], actual['fee_source_state']),
                         ('pending', 'done', 'recorded'))
        self.assertEqual((actual['amount'], fee.ydental_amount, fee.ydental_unit_price), (80, 80, 80))
        self.assertEqual(event.ydental_price_snapshot_id.ydental_price_id.ydental_catalog_id, self.catalogs[2])
        self.assertFalse(actual['inventory_event_ids'])
        self.assertEqual(self.root['ydental.treatment.line'].browse(issued['line_ids'][1]).state, 'issued')
        confirmed = service._operate('confirm', {'line_id': action['line_id'], 'version': draft['version'],
            'reason': '人工复核合成结果'}, key())
        with self.assertRaises(AccessError):
            service._pdf(action['line_id'], confirmed['version'])
        self.admin._grant(self.second.id, self.stores[0].id, {'export': 'write'})
        pdf, _digest = service._pdf(action['line_id'], confirmed['version'])
        self.assertTrue(pdf.startswith(b'%PDF-'))
        service._operate('finish', {k: action[k] for k in ('line_id', 'execution_id', 'lease_id', 'lease_token')} |
            {'reason': '检查段完成'}, key())
        self.assertEqual(self.root['ydental.treatment.fee'].search_count([('ydental_event_id', '=', event.id)]), 1)

    def test_inline_examination_keeps_medical_execution(self):
        self._bind_templates()
        price(self, 80, catalog=self.catalogs[2])
        original = self.stations[0][0]
        station = self.root['ydental.space.station'].create({'name': 'Synthetic inline qualified chair',
            'ydental_store_id': self.stores[0].id, 'ydental_floor_id': original.ydental_floor_id.id,
            'ydental_area_id': original.ydental_area_id.id, 'ydental_kind': 'care',
            'ydental_add_capability_ids': [fields.Command.set(self.capabilities[0].ids + self.capabilities[2].ids)]})
        make_slot(self, self.group, station, self.start, self.end)
        with patch.object(type(self.group.env['ydental.supply.service']), '_allow_demo_supply', return_value=True):
            queue, lease, medical = serving(self, station=station)
        clinical = queue.env['ydental.clinical.service']
        document = clinical._operate('open', {'execution_id': medical.id,
            'lease_id': lease['lease_id'], 'lease_token': lease['token']})
        document.update(clinical._operate('save', save_args(document)))
        treatment = queue.env['ydental.treatment.service']
        args = {'execution_id': medical.id, 'lease_id': lease['lease_id'], 'lease_token': lease['token'],
            'document_id': document['document_id'], 'document_version': document['version']}
        issued = self._order(treatment, args, indexes=(2,))
        service = queue.env['ydental.exam.service']
        action = {'line_id': issued['line_ids'][0], 'execution_id': medical.id,
            'lease_id': lease['lease_id'], 'lease_token': lease['token'], 'inline': True}
        service._operate('draft', action | {'version': 0, 'findings': '合成内嵌所见',
            'measurements': {}, 'conclusion': ''}, key())
        actual = service._operate('perform', action | {'reason': '内嵌真实检查', 'materials': []}, key())
        self.assertEqual(actual['event_state'], 'confirmed')
        resolved = service._operate('finish', action | {'reason': '内嵌检查完成'}, key())
        self.assertEqual(resolved['state'], 'medical_continues')
        self.assertEqual(medical.state, 'serving')
        self.assertFalse(self.root['ydental.queue.execution'].search_count([
            ('ydental_task_id', '=', issued['task_ids'][0])]))

    def test_template_and_unperformed_abort_fail_closed(self):
        with patch.object(type(self.group.env['ydental.supply.service']), '_allow_demo_supply', return_value=True):
            treatment, clinical, queue, lease, _medical, document, args = opened_actual(self)
        issued = self._order(treatment, args, indexes=(2,))
        clinical._operate('handover', handover_args(document, lease))
        service, action = self._external_start(issued)
        with self.assertRaises(UserError):
            service._operate('draft', action | {'version': 0, 'findings': 'synthetic',
                'measurements': {}, 'conclusion': ''}, key())
        self._bind_templates()
        aborted = service._operate('abort', action | {'reason': '实际开始后中止'}, key())
        self.assertEqual(aborted['state'], 'aborted')
        self.assertFalse(self.root['ydental.treatment.event'].search_count([
            ('ydental_order_line_id', '=', action['line_id'])]))
        service._operate('finish', action | {'reason': '中止后释放工位'}, key())

    def test_draft_no_fee_and_template_measurement_rejection(self):
        self._bind_templates()
        with patch.object(type(self.group.env['ydental.supply.service']), '_allow_demo_supply', return_value=True):
            treatment, clinical, queue, lease, _medical, document, args = opened_actual(self)
        issued = self._order(treatment, args, indexes=(2,))
        clinical._operate('handover', handover_args(document, lease))
        service, action = self._external_start(issued)
        with self.assertRaises(ValidationError):
            service._operate('draft', action | {'version': 0, 'findings': 'synthetic',
                'measurements': {'unknown': {'status': 'known', 'value': 1, 'unit': 'mm'}},
                'conclusion': ''}, key())
        service._operate('draft', action | {'version': 0, 'findings': '未判断',
            'measurements': {'length_mm': {'status': 'unknown', 'value': None, 'unit': 'mm'}},
            'conclusion': ''}, key())
        self.assertFalse(self.root['ydental.treatment.event'].search_count([
            ('ydental_order_line_id', '=', action['line_id'])]))
        self.assertFalse(self.root['ydental.treatment.fee'].search_count([
            ('ydental_store_id', '=', self.stores[0].id)]))

    def test_f2_partial_result_return_restores_only_on_confirmation(self):
        self._bind_templates()
        price(self, 80, catalog=self.catalogs[2])
        with patch.object(type(self.group.env['ydental.supply.service']), '_allow_demo_supply', return_value=True):
            treatment, clinical, queue, lease, medical, _document, args = opened_actual(self)
        issued = self._order(treatment, args)
        hold = queue._operate('reserve', lease_args(lease) | {'execution_id': medical.id,
            'target_task_id': issued['task_ids'][0]})
        service, action = self._external_start(issued)
        actual, _confirmed = self._complete_external(service, action)
        cbct_task = self.root['ydental.intake.task'].browse(issued['task_ids'][1])
        self.front._operate('report', {'task_id': cbct_task.id, 'version': cbct_task.ydental_version}, key())
        cbct_queue = queue_bind(self, self.second)
        cbct_lease = cbct_queue._operate('enter', {'station_id': self.stations[0][3].id})
        called = cbct_queue._operate('call', lease_args(cbct_lease))
        before = cbct_queue._model('entry').browse(called['entry_id']).state
        hint = self.front.env['ydental.queue.service']._operate('query_return',
            {'patient_id': medical.ydental_patient_id.id})
        self.assertEqual(hint['state'], 'holding')
        self.assertEqual(cbct_queue._model('entry').browse(called['entry_id']).state, before)
        restored = queue._operate('restore', lease_args(lease) | {'hold_id': hold['hold_id'],
            'confirmed': True})
        self.assertEqual(restored['state'], 'serving')
        self.assertEqual(cbct_queue._model('entry').browse(called['entry_id']).state, 'void')
        self.assertEqual(cbct_task.state, 'pending')
        self.assertEqual(self.root['ydental.treatment.line'].browse(issued['line_ids'][1]).state, 'issued')
        self.assertEqual(self.root['ydental.treatment.fee'].search_count([
            ('ydental_event_id', '=', actual['event_id'])]), 1)

    def test_f3_handover_to_new_doctor_sees_only_completed_result(self):
        self._bind_templates()
        price(self, 80, catalog=self.catalogs[2])
        with patch.object(type(self.group.env['ydental.supply.service']), '_allow_demo_supply', return_value=True):
            treatment, clinical, queue, lease, medical, document, args = opened_actual(self)
        issued = self._order(treatment, args)
        handed = clinical._operate('handover', handover_args(document, lease))
        service, action = self._external_start(issued)
        actual, confirmed = self._complete_external(service, action)
        continuation = self.root['ydental.intake.task'].browse(handed['continuation_task_id'])
        self.assertEqual(continuation.ydental_mapping_id, self.mappings[0][0])
        self.assertEqual(continuation.ydental_continuation_snapshot['capability_id'], self.capabilities[0].id)
        self.front._operate('report', {'task_id': continuation.id, 'version': continuation.ydental_version}, key())
        other, other_lease, new_execution = serving(self, user=self.second,
            station=self.other_station, task=continuation)
        self.assertNotEqual(new_execution.id, medical.id)
        self.assertEqual(new_execution.ydental_patient_id, medical.ydental_patient_id)
        self.assertEqual(self.root['ydental.treatment.line'].browse(issued['line_ids'][1]).state, 'issued')
        view = other.env['ydental.exam.service']._view(action['line_id'])
        self.assertEqual((view['result_state'], view['version']), ('confirmed', confirmed['version']))
        self.assertEqual(self.root['ydental.treatment.order'].browse(issued['order_id']).ydental_actor_id,
                         self.users['doctor'])
        self.assertEqual(self.root['ydental.treatment.fee'].search_count([
            ('ydental_event_id', '=', actual['event_id'])]), 1)
        self.assertEqual(self.root['ydental.intake.task'].search_count([
            ('ydental_source_execution_id', '=', medical.id), ('ydental_source_kind', '=', 'continuation')]), 1)

    def test_f4_next_day_requires_doctor_revalidation_and_preserves_done_line(self):
        self._bind_templates()
        price(self, 80, catalog=self.catalogs[2])
        price(self, 120, catalog=self.catalogs[3])
        self.admin._grant(self.users['manager'].id, self.stores[0].id, {'exam': 'write'})
        with patch.object(type(self.group.env['ydental.supply.service']), '_allow_demo_supply', return_value=True):
            treatment, clinical, queue, lease, medical, document, args = opened_actual(self)
        issued = self._order(treatment, args)
        handed = clinical._operate('handover', handover_args(document, lease))
        service, action = self._external_start(issued)
        panorama, _confirmed = self._complete_external(service, action)
        cbct_task = self.root['ydental.intake.task'].browse(issued['task_ids'][1])
        self.front._operate('report', {'task_id': cbct_task.id, 'version': cbct_task.ydental_version}, key())
        yesterday = self.group.env['ydental.supply.service']._date(self.stores[0])
        tomorrow = fields.Datetime.now() + timedelta(days=1)
        with patch.object(fields.Datetime, 'now', return_value=tomorrow):
            cleanup = self.front.env['ydental.queue.service']._cleanup_day(self.stores[0], yesterday)
            self.assertIn(cbct_task.id, self.root['ydental.queue.entry'].browse(cleanup['ended']).ydental_task_id.ids)
            self.assertEqual(cbct_task.state, 'pending')
            self.assertEqual(self.root['ydental.treatment.line'].browse(issued['line_ids'][0]).state, 'done')
            supply = self.group.env['ydental.supply.service']
            for area in (self.areas[0][0], self.areas[0][3]):
                supply._operate('business', {'area_id': area.id, 'state': 'open',
                    'reason': 'Explicit synthetic next-day opening'}, key())
            self.front._operate('arrive', {'patient_id': medical.ydental_patient_id.id}, key())
            with self.assertRaises(UserError):
                self.front._operate('report', {'task_id': cbct_task.id,
                    'version': cbct_task.ydental_version}, key())
            continuation = self.root['ydental.intake.task'].browse(handed['continuation_task_id'])
            self.front._operate('report', {'task_id': continuation.id,
                'version': continuation.ydental_version}, key())
            doctor, doctor_lease, current = serving(self, user=self.second,
                station=self.other_station, task=continuation)
            current_clinical = doctor.env['ydental.clinical.service']
            current_document = current_clinical._operate('open', {'execution_id': current.id,
                'lease_id': doctor_lease['lease_id'], 'lease_token': doctor_lease['token']})
            current_document.update(current_clinical._operate('save', save_args(current_document)))
            validated = doctor.env['ydental.exam.service']._operate('revalidate', {
                'line_id': issued['line_ids'][1], 'execution_id': current.id,
                'lease_id': doctor_lease['lease_id'], 'lease_token': doctor_lease['token'],
                'document_id': current_document['document_id'],
                'document_version': current_document['version'], 'reason': '今日仍需CBCT'}, key())
            self.assertNotEqual(validated['validated_date'], str(yesterday))
            current_clinical._operate('handover', handover_args(current_document, doctor_lease))
            today_report = self.front._operate('report', {'task_id': cbct_task.id,
                'version': cbct_task.ydental_version}, key())
            self.assertEqual(today_report['task_id'], cbct_task.id)
            cbct_service, cbct_action = self._external_start(issued, index=1, user=self.users['manager'])
            cbct, _result = self._complete_external(cbct_service, cbct_action)
            self.assertEqual((cbct['event_state'], cbct['amount']), ('confirmed', 120))
            self.assertEqual(self.root['ydental.treatment.fee'].browse(panorama['fee_id']).ydental_amount, 80)
            self.assertEqual(self.root['ydental.treatment.fee'].search_count([
                ('ydental_event_id', '=', panorama['event_id'])]), 1)

    def test_result_takeover_requires_release_and_preserves_original_author_fee(self):
        self._bind_templates()
        price(self, 80, catalog=self.catalogs[2])
        self.admin._grant(self.users['manager'].id, self.stores[0].id, {'exam': 'write'})
        with patch.object(type(self.group.env['ydental.supply.service']), '_allow_demo_supply', return_value=True):
            treatment, clinical, queue, lease, _medical, document, args = opened_actual(self)
        issued = self._order(treatment, args, indexes=(2,))
        clinical._operate('handover', handover_args(document, lease))
        service, action = self._external_start(issued)
        actual, confirmed = self._complete_external(service, action)
        manager = queue_bind(self, self.users['manager']).env['ydental.exam.service']
        takeover = {'line_id': action['line_id'], 'version': confirmed['version'],
            'reason': '原技师交接合成结果责任'}
        with self.assertRaises(AccessError):
            manager._operate('takeover', takeover, key())
        service._operate('release_editor', {'line_id': action['line_id'],
            'version': confirmed['version']}, key())
        manager._operate('takeover', takeover, key())
        corrected = manager._operate('correct', {'line_id': action['line_id'],
            'version': confirmed['version'], 'findings': '人工更正合成所见',
            'measurements': {}, 'conclusion': '', 'reason': '核对原始合成影像'}, key())
        result = self.root['ydental.exam.result'].search([('ydental_line_id', '=', action['line_id'])])
        self.assertEqual((result.ydental_original_author_id, result.ydental_responsible_id),
                         (self.second, self.users['manager']))
        self.assertEqual(corrected['version'], confirmed['version'] + 1)
        self.assertEqual(self.root['ydental.treatment.fee'].search_count([
            ('ydental_event_id', '=', actual['event_id'])]), 1)

    def test_actual_missing_price_keeps_original_pending_without_fake_fee(self):
        self._bind_templates()
        with patch.object(type(self.group.env['ydental.supply.service']), '_allow_demo_supply', return_value=True):
            treatment, clinical, queue, lease, _medical, document, args = opened_actual(self)
        issued = self._order(treatment, args, indexes=(2,))
        clinical._operate('handover', handover_args(document, lease))
        service, action = self._external_start(issued)
        service._operate('draft', action | {'version': 0, 'findings': '实际合成检查后待核对',
            'measurements': {}, 'conclusion': ''}, key())
        actual = service._operate('perform', action | {'reason': '已发生但原价未知',
            'materials': []}, key())
        event = self.root['ydental.treatment.event'].browse(actual['event_id'])
        self.assertEqual((actual['event_state'], actual['result_document_state'], actual['fee_source_state']),
                         ('pending', 'pending', 'absent'))
        self.assertEqual(actual['pending_reason'], 'missing_price')
        self.assertFalse(actual['fee_id'])
        self.assertIsNone(actual['amount'])
        self.assertFalse(event.ydental_price_snapshot_id)
        departed = service._operate('finish', action | {'reason': '临床离场，原价待核对责任继续保留'}, key())
        self.assertEqual(departed['state'], 'completed_pending_reconciliation')
        self.assertEqual(event.state, 'pending')
        self.assertEqual(self.root['ydental.queue.execution'].browse(action['execution_id']).state, 'completed')
        self.assertFalse(self.root['ydental.queue.lease'].browse(action['lease_id']).ydental_active)
        price(self, 999, catalog=self.catalogs[2])
        retry = service._operate('reconcile', {'line_id': action['line_id'],
            'reason': '后价不能替代原价'}, key())
        self.assertEqual((retry['state'], retry['pending_reason'], retry['fee_id']),
                         ('pending', 'missing_price', False))

    def test_wrong_template_type_cannot_bind_to_other_capability(self):
        service = self.doctor.env['ydental.exam.service']
        with self.assertRaises(ValidationError):
            service._operate('bind_template', {'catalog_id': self.catalogs[2].id,
                'code': 'cbct-demo-1', 'reason': 'Synthetic wrong capability must be rejected'}, key())
        self.assertFalse(self.root['ydental.exam.template'].search([
            ('ydental_catalog_id', '=', self.catalogs[2].id)]))
        with self.assertRaises(ValidationError):
            service._operate('bind_template', {'catalog_id': self.catalogs[3].id,
                'code': 'panorama-demo-1', 'reason': 'Synthetic reverse mismatch must be rejected'}, key())

    def test_text_only_save_does_not_clear_known_measurement(self):
        self._bind_templates()
        with patch.object(type(self.group.env['ydental.supply.service']), '_allow_demo_supply', return_value=True):
            treatment, clinical, _queue, lease, _medical, document, args = opened_actual(self)
        issued = self._order(treatment, args, indexes=(2,))
        clinical._operate('handover', handover_args(document, lease))
        service, action = self._external_start(issued)
        known = {'length_mm': {'status': 'known', 'value': 12, 'unit': 'mm'}}
        draft = service._operate('draft', action | {'version': 0, 'findings': '初次所见',
            'measurements': known, 'conclusion': ''}, key())
        saved = service._operate('draft', action | {'version': draft['version'],
            'findings': '仅修改所见', 'measurements': {}, 'conclusion': ''}, key())
        self.assertEqual(saved['version'], draft['version'] + 1)
        self.assertEqual(service._view(action['line_id'])['measurements'], known)

    def test_panorama_task_cannot_be_called_from_idle_cbct_station(self):
        self._bind_templates()
        with patch.object(type(self.group.env['ydental.supply.service']), '_allow_demo_supply', return_value=True):
            treatment, clinical, queue, lease, _medical, document, args = opened_actual(self)
        issued = self._order(treatment, args)
        clinical._operate('handover', handover_args(document, lease))
        task = self.root['ydental.intake.task'].browse(issued['task_ids'][0])
        self.front._operate('report', {'task_id': task.id, 'version': task.ydental_version}, key())
        wrong = queue_bind(self, self.second)
        wrong_lease = wrong._operate('enter', {'station_id': self.stations[0][3].id})
        with self.assertRaises(UserError):
            wrong._operate('call', lease_args(wrong_lease))
        wrong._operate('exit', lease_args(wrong_lease))
        right = queue_bind(self, self.second)
        right_lease = right._operate('enter', {'station_id': self.stations[0][2].id})
        called = right._operate('call', lease_args(right_lease))
        self.assertEqual(called['task_id'], task.id)
        self.assertEqual(self.root['ydental.treatment.line'].browse(issued['line_ids'][1]).state, 'issued')

    def test_unperformed_cancel_blocks_reporting_and_frozen_order_edit(self):
        with patch.object(type(self.group.env['ydental.supply.service']), '_allow_demo_supply', return_value=True):
            treatment, _clinical, _queue, _lease, _medical, _document, args = opened_actual(self)
        issued = self._order(treatment, args, indexes=(2,))
        row = {'mapping_id': self.mappings[0][3].id, 'quantity': 1, 'uom_id': self.uom.id,
               'product_id': False, 'specification': '', 'usage': '', 'frequency': '', 'course': ''}
        with self.assertRaises(UserError):
            treatment._operate('edit_order', args | {'order_id': issued['order_id'],
                'version': issued['version'], 'purpose': 'Illegal addition', 'lines': [row]}, key())
        cancelled = treatment._operate('cancel_exam', args | {'line_id': issued['line_ids'][0],
            'order_version': issued['version'], 'reason': 'Doctor cancelled unperformed synthetic exam'}, key())
        self.assertEqual(cancelled['state'], 'cancelled')
        task = self.root['ydental.intake.task'].browse(issued['task_ids'][0])
        self.assertEqual(task.state, 'cancelled')
        with self.assertRaises((AccessError, UserError)):
            self.front._operate('report', {'task_id': task.id, 'version': task.ydental_version}, key())
        self.assertFalse(self.root['ydental.treatment.event'].search_count([
            ('ydental_order_line_id', '=', issued['line_ids'][0])]))
        other = self._order(treatment, args, indexes=(3,))
        self.assertNotEqual(other['order_id'], issued['order_id'])
        self.assertEqual(self.root['ydental.treatment.order'].browse(other['order_id']).ydental_actor_id,
                         self.users['doctor'])

    def test_started_inline_exam_cannot_be_cancelled_as_unperformed(self):
        self._bind_templates()
        price(self, 80, catalog=self.catalogs[2])
        original = self.stations[0][0]
        station = self.root['ydental.space.station'].create({'name': 'Synthetic cancel guard chair',
            'ydental_store_id': self.stores[0].id, 'ydental_floor_id': original.ydental_floor_id.id,
            'ydental_area_id': original.ydental_area_id.id, 'ydental_kind': 'care',
            'ydental_add_capability_ids': [fields.Command.set(self.capabilities[0].ids + self.capabilities[2].ids)]})
        make_slot(self, self.group, station, self.start, self.end)
        with patch.object(type(self.group.env['ydental.supply.service']), '_allow_demo_supply', return_value=True):
            queue, lease, medical = serving(self, station=station)
        clinical = queue.env['ydental.clinical.service']
        document = clinical._operate('open', {'execution_id': medical.id,
            'lease_id': lease['lease_id'], 'lease_token': lease['token']})
        document.update(clinical._operate('save', save_args(document)))
        treatment = queue.env['ydental.treatment.service']
        args = {'execution_id': medical.id, 'lease_id': lease['lease_id'], 'lease_token': lease['token'],
            'document_id': document['document_id'], 'document_version': document['version']}
        issued = self._order(treatment, args, indexes=(2,))
        action = {'line_id': issued['line_ids'][0], 'execution_id': medical.id,
            'lease_id': lease['lease_id'], 'lease_token': lease['token'], 'inline': True}
        exam = queue.env['ydental.exam.service']
        exam._operate('draft', action | {'version': 0, 'findings': '合成内嵌检查',
            'measurements': {}, 'conclusion': ''}, key())
        actual = exam._operate('perform', action | {'reason': '内嵌实际发生', 'materials': []}, key())
        with self.assertRaises(UserError):
            treatment._operate('cancel_exam', args | {'line_id': issued['line_ids'][0],
                'order_version': issued['version'], 'reason': 'Cannot erase actual exam'}, key())
        self.assertEqual(self.root['ydental.treatment.fee'].browse(actual['fee_id']).ydental_amount, 80)

    def test_attachment_requires_current_editor_source_and_export_for_download(self):
        self._bind_templates()
        with patch.object(type(self.group.env['ydental.supply.service']), '_allow_demo_supply', return_value=True):
            treatment, clinical, _queue, lease, _medical, document, args = opened_actual(self)
        issued = self._order(treatment, args)
        clinical._operate('handover', handover_args(document, lease))
        service, action = self._external_start(issued)
        draft = service._operate('draft', action | {'version': 0, 'findings': '合成附件所见',
            'measurements': {}, 'conclusion': ''}, key())
        raw = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/lXcAAAAASUVORK5CYII=')
        payload = {'line_id': action['line_id'], 'version': draft['version'],
            'filename': 'synthetic.png', 'mimetype': 'image/png',
            'encoded': base64.b64encode(raw).decode()}
        with self.assertRaises(ValidationError):
            service._operate('attach', payload | {'encoded': 'invalid'}, key())
        saved = service._operate('attach', payload, key())
        with self.assertRaises(AccessError):
            service._attachment_download(action['line_id'], saved['attachment_id'])
        self.admin._grant(self.second.id, self.stores[0].id, {'export': 'write'})
        content, kind, filename = service._attachment_download(action['line_id'], saved['attachment_id'])
        self.assertEqual((content, kind, filename), (raw, 'image/png', 'synthetic.png'))
        with self.assertRaises(AccessError):
            service._attachment_download(issued['line_ids'][1], saved['attachment_id'])
        self.assertFalse(self.root['ydental.treatment.event'].search_count([
            ('ydental_order_line_id', '=', action['line_id'])]))

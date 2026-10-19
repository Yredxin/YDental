"""S11 regression for continuing a confirmed examination the following day."""
from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

from odoo.addons.ydental_treatment_test.tests.common import (
    handover_args,
    key,
    lease_args,
    price,
    queue_bind,
    save_args,
    serving,
)
from odoo.addons.ydental_treatment_test.tests.treatment_common import (
    opened_actual,
)
from odoo.addons.ydental_treatment_test.tests.treatment_common import (
    setup as treatment_setup,
)


@tagged('post_install', '-at_install')
class TestS11NextDayExaminationContinuation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        treatment_setup(cls)

    def _bind_templates(self):
        service = self.group.env['ydental.exam.service']
        self.admin._grant(self.users['manager'].id, self.stores[0].id, {'exam': 'write'})
        for catalog, code, family in (
            (self.catalogs[2], 'panorama-demo-1', 'panorama'),
            (self.catalogs[3], 'cbct-demo-1', 'cbct'),
        ):
            service._operate('review_capability', {
                'capability_id': catalog.ydental_capability_id.id,
                'family': family,
                'reason': 'S11 synthetic reviewed examination capability',
            }, key())
            service._operate('bind_template', {
                'catalog_id': catalog.id,
                'code': code,
                'reason': 'S11 synthetic reviewed examination template',
            }, key())

    def _order(self, treatment, args):
        lines = [{
            'mapping_id': self.mappings[0][index].id,
            'quantity': 1,
            'uom_id': self.uom.id,
            'product_id': False,
            'specification': '',
            'usage': '',
            'frequency': '',
            'course': '',
        } for index in (2, 3)]
        draft = treatment._operate('order', args | {
            'kind': 'exam', 'purpose': 'S11 synthetic next-day continuation', 'lines': lines,
        }, key())
        return treatment._operate('issue', args | {
            'order_id': draft['order_id'], 'version': draft['version'],
        }, key())

    def _external_start(self, issued, index, user=None):
        task = self.root['ydental.intake.task'].browse(issued['task_ids'][index])
        self.front._operate('report', {'task_id': task.id, 'version': task.ydental_version}, key())
        examiner = queue_bind(self, user or self.second)
        lease = examiner._operate('enter', {'station_id': self.stations[0][2 + index].id})
        called = examiner._operate('call', lease_args(lease))
        self.assertEqual(called['task_id'], task.id)
        started = examiner._operate('start', lease_args(lease) | {'entry_id': called['entry_id']})
        return examiner.env['ydental.exam.service'], {
            'line_id': issued['line_ids'][index], 'execution_id': started['execution_id'],
            'lease_id': lease['lease_id'], 'lease_token': lease['token'], 'inline': False,
        }

    def _complete_external(self, service, action):
        draft = service._operate('draft', action | {
            'version': 0, 'findings': 'S11 synthetic panorama findings',
            'measurements': {}, 'conclusion': '',
        }, key())
        result = service._operate('perform', action | {
            'reason': 'S11 synthetic examination performed', 'materials': [],
        }, key())
        confirmed = service._operate('confirm', {
            'line_id': action['line_id'], 'version': draft['version'],
            'reason': 'S11 synthetic clinical confirmation',
        }, key())
        service._operate('finish', action | {'reason': 'S11 synthetic examination finished'}, key())
        return result, confirmed

    def test_yesterday_completed_panorama_today_revalidates_cbct(self):
        self._bind_templates()
        price(self, 80, catalog=self.catalogs[2])
        price(self, 120, catalog=self.catalogs[3])
        self.admin._grant(self.users['manager'].id, self.stores[0].id, {'exam': 'write'})
        with patch.object(type(self.group.env['ydental.supply.service']), '_allow_demo_supply', return_value=True):
            treatment, clinical, _queue, lease, medical, document, args = opened_actual(self)
        issued = self._order(treatment, args)
        handed = clinical._operate('handover', handover_args(document, lease))
        panorama_service, panorama_action = self._external_start(issued, 0)
        panorama, _confirmed = self._complete_external(panorama_service, panorama_action)
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
                supply._operate('business', {
                    'area_id': area.id, 'state': 'open', 'reason': 'S11 synthetic next-day reopening',
                }, key())
            self.front._operate('arrive', {'patient_id': medical.ydental_patient_id.id}, key())
            with self.assertRaises(UserError):
                self.front._operate('report', {'task_id': cbct_task.id, 'version': cbct_task.ydental_version}, key())

            continuation = self.root['ydental.intake.task'].browse(handed['continuation_task_id'])
            self.front._operate('report', {'task_id': continuation.id, 'version': continuation.ydental_version}, key())
            doctor, doctor_lease, current = serving(self, user=self.second,
                station=self.other_station, task=continuation)
            clinical_today = doctor.env['ydental.clinical.service']
            current_document = clinical_today._operate('open', {
                'execution_id': current.id, 'lease_id': doctor_lease['lease_id'],
                'lease_token': doctor_lease['token'],
            })
            current_document.update(clinical_today._operate('save', save_args(current_document)))
            validated = doctor.env['ydental.exam.service']._operate('revalidate', {
                'line_id': issued['line_ids'][1], 'execution_id': current.id,
                'lease_id': doctor_lease['lease_id'], 'lease_token': doctor_lease['token'],
                'document_id': current_document['document_id'],
                'document_version': current_document['version'], 'reason': 'S11 synthetic next-day CBCT revalidation',
            }, key())
            self.assertNotEqual(validated['validated_date'], str(yesterday))
            clinical_today._operate('handover', handover_args(current_document, doctor_lease))
            today_report = self.front._operate('report', {
                'task_id': cbct_task.id, 'version': cbct_task.ydental_version,
            }, key())
            self.assertEqual(today_report['task_id'], cbct_task.id)
            cbct_service, cbct_action = self._external_start(issued, 1, user=self.users['manager'])
            cbct, _confirmed = self._complete_external(cbct_service, cbct_action)

        self.assertEqual((panorama['event_state'], panorama['amount']), ('confirmed', 80))
        self.assertEqual((cbct['event_state'], cbct['amount']), ('confirmed', 120))
        self.assertEqual(self.root['ydental.treatment.line'].browse(issued['line_ids'][0]).state, 'done')
        self.assertEqual(self.root['ydental.treatment.fee'].search_count([
            ('ydental_event_id', '=', panorama['event_id'])]), 1)
        cbct_event = self.root['ydental.treatment.event'].browse(cbct['event_id'])
        cbct_fee = self.root['ydental.treatment.fee'].browse(cbct['fee_id'])
        self.assertEqual(cbct_event.ydental_order_line_id.id, issued['line_ids'][1])
        self.assertEqual(cbct_fee.ydental_event_id, cbct_event)

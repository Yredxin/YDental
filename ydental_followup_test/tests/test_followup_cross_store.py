from datetime import timedelta
from unittest.mock import patch

from odoo import Command, fields
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, new_test_user, tagged

from odoo.addons.ydental_treatment_test.tests.common import (
    bind,
    handover_args,
    key,
    price,
    save_args,
)
from odoo.addons.ydental_treatment_test.tests.treatment_common import (
    execute_args,
    receive,
)
from odoo.addons.ydental_treatment_test.tests.treatment_common import (
    setup as treatment_setup,
)


@tagged('post_install', '-at_install')
class TestFollowupCrossStore(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.demo_policy_patch = patch.object(
            type(cls.env['ydental.supply.service']), '_allow_demo_supply', return_value=True)
        cls.demo_policy_patch.start()
        cls.addClassCleanup(cls.demo_policy_patch.stop)
        internal_users = cls.env.ref('base.group_user')
        internal_users.write({'implied_ids': [
            Command.link(cls.env.ref('stock.group_stock_multi_warehouses').id),
            Command.link(cls.env.ref('stock.group_stock_multi_locations').id),
        ]})
        treatment_setup(cls)
        for store in cls.stores:
            cls.admin._grant(cls.users['manager'].id, store.id, {'followup': 'write'})

        cls.source_clinician = new_test_user(
            cls.root, name='S11 cross-store source clinician',
            login='s11_cross_source_' + key()[:8], password='s11-test-password',
            groups='ydental_base.ydental_base_group_user')
        cls.limited_source_clinician = new_test_user(
            cls.root, name='S11 cross-store limited clinician',
            login='s11_cross_limited_' + key()[:8], password='s11-test-password',
            groups='ydental_base.ydental_base_group_user')
        for user in (cls.source_clinician, cls.limited_source_clinician):
            for store in cls.stores:
                cls.admin._join(user.id, store.id)
            cls.admin._grant(user.id, cls.stores[0].id, {
                'medical': 'write', 'exam': 'write', 'followup': 'write',
            })
            user.write({'ydental_capability_ids': [Command.set(cls.capabilities.ids)]})
        # Source completion needs current source medical/write and follow-up/write,
        # but only medical/read at the referred-to store.
        cls.admin._grant(cls.source_clinician.id, cls.stores[1].id, {'medical': 'read'})

        # The actual target visit is performed by a different clinician. The
        # limited source clinician intentionally has no target-store medical grant.
        cls.admin._grant(cls.users['doctor'].id, cls.stores[1].id, {
            'medical': 'write', 'exam': 'write',
        })
        cls.admin._grant(cls.users['manager'].id, cls.stores[1].id, {'warehouse': 'write'})

    def _source_actual_visit(self, patient_id):
        service, lease, execution, document = self._open_actual(
            self.source_clinician, self.stores[0], patient_id)
        document.update(service._operate('save', save_args(document)))
        treatment = service.env['ydental.treatment.service']
        result = treatment._operate('execute', execute_args(self, self._execution_args(execution, lease, document)), key())
        event = self.root['ydental.treatment.event'].browse(result['event_id'])
        return service, treatment, lease, execution, document, event

    def _execution_args(self, execution, lease, document):
        return {
            'execution_id': execution.id,
            'lease_id': lease['lease_id'],
            'lease_token': lease['token'],
            'document_id': document['document_id'],
            'document_version': document['version'],
        }

    def _open_actual(self, user, store, patient_id):
        intake = bind(self, self.users['frontdesk'], store)
        task_result = intake._operate('reserve', {
            'patient_id': patient_id,
            'mapping_id': self.mappings[0 if store == self.stores[0] else 1][0].id,
            'start': fields.Datetime.to_string(self.start),
            'end': fields.Datetime.to_string(self.end),
        }, key())
        task = self.root['ydental.intake.task'].browse(task_result['task_id'])
        intake._operate('arrive', {'patient_id': task.ydental_patient_id.id}, key())
        intake._operate('report', {'task_id': task.id, 'version': task.ydental_version}, key())
        queue = bind(self, user, store).env['ydental.queue.service']._bind_connection(key() + key())
        lease = queue._operate('enter', {'station_id': self.stations[0 if store == self.stores[0] else 1][0].id})
        call = queue._operate('call', {'lease_id': lease['lease_id'], 'token': lease['token']})
        actual = queue._operate('start', {
            'lease_id': lease['lease_id'], 'token': lease['token'], 'entry_id': call['entry_id'],
        })
        execution = self.root['ydental.queue.execution'].browse(actual['execution_id'])
        clinical = queue.env['ydental.clinical.service']
        document = clinical._operate('open', {
            'execution_id': execution.id, 'lease_id': lease['lease_id'], 'lease_token': lease['token'],
        })
        return clinical, lease, execution, document

    def test_cross_store_referral_completes_followup_and_close_requires_reason(self):
        price(self, amount=137.25)
        receive(self)

        # Create a source patient through intake so the source treatment is a real
        # encounter, then use that exact source task as the referral provenance.
        source_intake = bind(self, self.users['manager'], self.stores[0])
        source_patient_id = source_intake.env['ydental.patient.service']._operate('create', {
            'values': {'name': 'S11 synthetic cross-store follow-up patient'},
        }, key())['id']
        source_service, source_treatment, source_lease, source_execution, source_document, source_event = (
            self._source_actual_visit(source_patient_id))
        source_task = source_execution.ydental_task_id
        target_store = self.stores[1]
        target_mapping = self.mappings[1][0]
        source_treatment._operate('refer', {
            'execution_id': source_execution.id,
            'lease_id': source_lease['lease_id'],
            'lease_token': source_lease['token'],
            'document_id': source_document['document_id'],
            'document_version': source_document['version'],
            'mode': 'untimed',
            'mapping_id': target_mapping.id,
            'valid_until': fields.Datetime.to_string(fields.Datetime.now() + timedelta(days=1)),
            'reason': 'Synthetic S11 cross-store follow-up referral',
            'source': key(),
        }, key())
        referral = self.root['ydental.intake.referral'].search([
            ('ydental_source_task_id', '=', source_task.id),
            ('ydental_store_id', '=', target_store.id),
            ('ydental_patient_id', '=', source_execution.ydental_patient_id.id),
        ], order='id desc', limit=1)
        self.assertTrue(referral)

        source_clinical = source_service
        source_clinical._operate('handover', handover_args(source_document, source_lease) | {
            'reason': 'Synthetic source encounter ended after referral',
        })
        source_execution.invalidate_recordset(['state'])
        self.assertEqual(source_execution.state, 'handover')

        # Acceptance establishes the same patient's target-store relation and
        # creates the target intake task through the real referral service.
        target_front = bind(self, self.users['frontdesk'], target_store)
        accepted = target_front._operate('accept_referral', {
            'record_id': referral.id,
            'version': referral.ydental_version,
            'start': fields.Datetime.to_string(self.start),
            'end': fields.Datetime.to_string(self.end),
        }, key())
        target_task = self.root['ydental.intake.task'].browse(accepted['task_id'])
        entitlement = target_task.ydental_entitlement_id
        self.assertTrue(entitlement)
        self.assertEqual(entitlement.ydental_source_task_id, source_task)
        self.assertEqual(target_task.ydental_patient_id, source_execution.ydental_patient_id)
        target_front._operate('report', {'task_id': target_task.id, 'version': target_task.ydental_version}, key())

        # Supply a real target-store stock lot and published local price so the
        # target visit can record a normal confirmed S06/S08 treatment event.
        target_manager = bind(self, self.users['manager'], target_store)
        target_stock = target_manager.env['ydental.inventory.service']
        target_stock._operate('setup', {'code': 'S11X' + str(target_store.id)}, key())
        target_product = target_stock._operate('product', {
            'code': 'S11X-MAT-' + key()[:8], 'name': 'S11 synthetic target material',
            'kind': 'material', 'stock_uom_id': self.uom.id, 'issue_uom_id': self.uom.id,
            'step': 1, 'specification': 'Synthetic target visit material',
        }, key())
        target_lot = target_stock._operate('lot', {
            'product_id': target_product['id'], 'name': 'S11X-LOT-' + key()[:8],
            'expiration': fields.Datetime.to_string(fields.Datetime.now() + timedelta(days=45)),
        }, key())
        target_stock._operate('receive', {
            'lot_id': target_lot['id'], 'quantity': 2, 'uom_id': self.uom.id,
            'source_key': key(), 'reason': 'Synthetic target-store physical receipt',
        }, key())
        price(self, amount=137.25, service=target_manager)

        target_clinical, target_lease, target_execution, target_document = self._open_task(
            self.users['doctor'], target_store, target_task)
        target_document.update(target_clinical._operate('save', save_args(target_document)))
        target_args = self._execution_args(target_execution, target_lease, target_document)
        target_treatment = target_clinical.env['ydental.treatment.service']
        target_event_result = target_treatment._operate('execute', execute_args(self, target_args) | {
            'materials': [{
                'lot_id': target_lot['id'], 'quantity': 1, 'uom_id': self.uom.id, 'kind': 'treatment',
            }],
        }, key())
        target_event = self.root['ydental.treatment.event'].browse(target_event_result['event_id'])
        target_clinical._operate('handover', handover_args(target_document, target_lease) | {
            'reason': 'Synthetic target encounter ended after actual treatment',
        })
        target_execution.invalidate_recordset(['state'])
        self.assertEqual(target_execution.state, 'handover')
        self.assertEqual((target_event.state, target_event.ydental_kind), ('confirmed', 'treatment'))
        self.assertEqual(target_event.ydental_execution_id.ydental_task_id.ydental_entitlement_id, entitlement)

        followup_service = bind(self, self.source_clinician, self.stores[0]).env['ydental.followup.service']
        payload = {
            'patient_id': source_execution.ydental_patient_id.id,
            'source_event_id': source_event.id,
            'followup_type': 'post_visit',
            'planned_at': fields.Datetime.to_string(fields.Datetime.now()),
            'responsible_id': self.source_clinician.id,
        }
        followup_result = followup_service._operate('create', payload)
        followup = self.root['ydental.followup'].browse(followup_result['id'])
        self.assertFalse(followup.ydental_appointment_id, 'a target-store reservation is never linked as source-store appointment')

        # A source actor with no target medical-read grant cannot complete from
        # the remote event, even when a valid referral exists.
        limited_service = bind(self, self.limited_source_clinician, self.stores[0]).env['ydental.followup.service']
        with self.assertRaises(AccessError):
            limited_service._operate('complete', {
                'followup_id': followup.id, 'event_id': target_event.id,
                'confirmed_unlinked': True, 'reason': 'Synthetic referral encounter association',
            })
        self.assertNotEqual(followup.state, 'done')

        # Authorized source clinician explicitly confirms the unlinked relation.
        completed = followup_service._operate('complete', {
            'followup_id': followup.id, 'event_id': target_event.id,
            'confirmed_unlinked': True, 'reason': 'Synthetic exact source-task referral to target encounter',
        })
        followup.invalidate_recordset(['state', 'ydental_appointment_status',
                                       'ydental_completed_event_id', 'ydental_completed_execution_id'])
        self.assertEqual(completed['state'], 'done')
        self.assertEqual(followup.state, 'done')
        self.assertEqual(followup.ydental_appointment_status, 'seen')
        self.assertEqual(followup.ydental_completed_event_id, target_event)
        self.assertEqual(followup.ydental_completed_execution_id, target_execution)
        self.assertEqual(target_event.ydental_execution_id.ydental_task_id.ydental_entitlement_id.ydental_source_task_id,
                         source_task)

        # Manual closure is available to an ordinary follow-up writer, with a
        # required reason; a frontdesk reader without follow-up/write is denied.
        close_result = followup_service._operate('create', payload | {
            'planned_at': fields.Datetime.to_string(fields.Datetime.now() + timedelta(hours=1)),
        })
        close_row = self.root['ydental.followup'].browse(close_result['id'])
        self.admin._grant(self.users['frontdesk'].id, self.stores[0].id, {'followup': 'write'})
        close_service = bind(self, self.users['frontdesk'], self.stores[0]).env['ydental.followup.service']
        reader_service = bind(self, self.users['reader'], self.stores[0]).env['ydental.followup.service']
        with self.assertRaises(ValidationError):
            close_service._operate('close', {'followup_id': close_row.id, 'reason': '   '})
        with self.assertRaises(AccessError):
            reader_service._operate('close', {'followup_id': close_row.id, 'reason': 'No follow-up grant'})
        closed = close_service._operate('close', {
            'followup_id': close_row.id, 'reason': 'Synthetic patient declined further contact',
        })
        close_row.invalidate_recordset(['state', 'ydental_closed_reason'])
        self.assertEqual(closed['state'], 'closed')
        self.assertEqual(close_row.state, 'closed')
        self.assertEqual(close_row.ydental_closed_reason, 'Synthetic patient declined further contact')

    def _open_task(self, user, store, task):
        queue = bind(self, user, store).env['ydental.queue.service']._bind_connection(key() + key())
        lease = queue._operate('enter', {'station_id': self.stations[1][0].id})
        call = queue._operate('call', {'lease_id': lease['lease_id'], 'token': lease['token']})
        self.assertEqual(call['task_id'], task.id)
        actual = queue._operate('start', {
            'lease_id': lease['lease_id'], 'token': lease['token'], 'entry_id': call['entry_id'],
        })
        execution = self.root['ydental.queue.execution'].browse(actual['execution_id'])
        clinical = queue.env['ydental.clinical.service']
        document = clinical._operate('open', {
            'execution_id': execution.id, 'lease_id': lease['lease_id'], 'lease_token': lease['token'],
        })
        return clinical, lease, execution, document

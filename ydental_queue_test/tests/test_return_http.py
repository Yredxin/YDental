import json
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

from lxml import html
from odoo.tests import tagged

from .common import accepted, bind, key, qualify
from .return_common import appender, close, external, report, source
from .test_http import TestQueueHTTP


@tagged('post_install', '-at_install')
class TestQueueReturnHTTP(TestQueueHTTP):
    def test_unavailable_patient_suppresses_pending_task_actions(self):
        task = accepted(self)
        self.select('frontdesk')
        service_type = type(self.env['ydental.patient.service'])
        for relations in ({}, {task.ydental_patient_id.id: SimpleNamespace(
                ydental_patient_id=SimpleNamespace(active=False))}):
            with patch.object(service_type, '_current_relations', return_value=relations):
                page = self.url_open('/ydental/queue')
            self.assertEqual(page.status_code, 200)
            row = html.fromstring(page.content).xpath('//div[@data-pending-task=$task]', task=str(task.id))[0]
            self.assertTrue(any(message in row.text_content() for message in (
                'Patient is archived or lacks a current store relationship',
                '患者已归档或缺少本店有效关联',
            )))
            self.assertFalse(row.xpath('.//form[@data-queue-form="query_return" or @data-queue-form="report" or @data-queue-form="append"]'))

    def test_merged_patient_task_displays_canonical_identity(self):
        front = self.front.env['ydental.patient.service']
        group = self.group.env['ydental.patient.service']
        source = front._operate('create', {'values': {'name': 'Synthetic merge source'}}, key())
        target = front._operate('create', {'values': {'name': 'Synthetic canonical patient'}}, key())
        merge = front._operate('request_merge', {'source_id': source['id'], 'target_id': target['id'],
                                                'reason': 'Synthetic identity verification'}, key())
        group._operate('confirm', {'request_id': merge['id'], 'version': merge['version'],
                                   'reason': 'Synthetic group verification'}, key())
        qualification = qualify(self, patient_id=source['id'])
        task = self.root['ydental.intake.task'].browse(qualification['task_id'])
        self.select('frontdesk')
        page = self.url_open('/ydental/queue')
        self.assertEqual(page.status_code, 200)
        row = html.fromstring(page.content).xpath('//div[@data-pending-task=$task]', task=str(task.id))[0]
        self.assertIn('Synthetic canonical patient', row.text_content())
        self.assertEqual(row.xpath('.//form[@data-queue-form="query_return"]/input[@name="patient_id"]/@value'), [str(target['id'])])
        self.assertTrue(row.xpath('.//form[@data-queue-form="report"]'))

    def test_pending_patient_return_is_scoped_to_frontdesk_and_store(self):
        task = accepted(self)
        patient = task.ydental_patient_id
        self.select('frontdesk')
        page = self.url_open('/ydental/queue')
        self.assertEqual(page.status_code, 200)
        row = html.fromstring(page.content).xpath('//div[@data-pending-task=$task]', task=str(task.id))[0]
        self.assertIn(patient.name, row.text_content())
        self.assertIn(patient.ydental_number, row.text_content())
        self.assertEqual(row.xpath('.//form[@data-queue-form="query_return"]/input[@name="patient_id"]/@value'), [str(patient.id)])
        result = self.action('query_return', {'patient_id': patient.id})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()['state'], 'no_hold')

        self.admin._grant(self.users['doctor'].id, self.stores[0].id,
                          {'medical': 'none', 'exam': 'none', 'pharmacy': 'read'})
        self.select('doctor')
        page = self.url_open('/ydental/queue')
        self.assertEqual(page.status_code, 200)
        row = html.fromstring(page.content).xpath('//div[@data-pending-task=$task]', task=str(task.id))[0]
        self.assertNotIn(patient.name, row.text_content())
        self.assertNotIn(patient.ydental_number, row.text_content())
        self.assertFalse(row.xpath('.//form[@data-queue-form="query_return"]'))

        self.select('frontdesk')
        switch = self.url_open('/ydental/access/action', data={
            'csrf_token': self.csrf, 'revision': self.revision, 'operation': 'switch',
            'payload': json.dumps({'store_id': self.stores[1].id}), 'output': 'json'})
        self.assertEqual(switch.status_code, 200)
        self.revision = switch.json()['revision']
        page = self.url_open('/ydental/queue')
        self.assertEqual(page.status_code, 200)
        self.assertFalse(html.fromstring(page.content).xpath('//div[@data-pending-task=$task]', task=str(task.id)))
        self.assertEqual(self.action('query_return', {'patient_id': patient.id}).status_code, 403)

        self.admin._grant(self.users['frontdesk'].id, self.stores[1].id, {'frontdesk': 'none'})
        self.assertEqual(self.action('query_return', {'patient_id': patient.id}).status_code, 403)

    def test_return_search_uses_current_store_patient_and_rechecks_authority(self):
        task = accepted(self)
        patient = task.ydental_patient_id
        self.select('frontdesk')
        page = self.url_open('/ydental/queue/search', data={'csrf_token': self.csrf, 'return_q': patient.ydental_number})
        self.assertEqual(page.status_code, 200)
        doc = html.fromstring(page.content)
        section = doc.xpath('//section[@id="patient-return-actions"]')[0]
        self.assertTrue(section.xpath('.//form[@action="/ydental/queue/search" and @method="post"]/input[@name="csrf_token"]'))
        self.assertTrue(section.xpath('.//a[@href="/ydental/queue"]'))
        self.assertEqual(self.url_open('/ydental/queue/search', data={'return_q': patient.ydental_number}).status_code, 400)
        self.assertEqual(self.url_open('/ydental/queue?return_q=synthetic').status_code, 400)
        self.assertEqual(section.xpath('.//form[@data-queue-form="query_return"]/input[@name="patient_id"]/@value'), [str(patient.id)])
        self.assertIn(patient.name, section.text_content())
        self.assertFalse(section.xpath('.//input[@name="patient_id" and @type="number"]'))
        switch = self.url_open('/ydental/access/action', data={
            'csrf_token': self.csrf, 'revision': self.revision, 'operation': 'switch',
            'payload': json.dumps({'store_id': self.stores[1].id}), 'output': 'json'})
        self.assertEqual(switch.status_code, 200)
        self.revision = switch.json()['revision']
        page = self.url_open('/ydental/queue/search', data={'csrf_token': self.csrf, 'return_q': patient.ydental_number})
        self.assertEqual(page.status_code, 200)
        self.assertNotIn(patient.ydental_number, html.fromstring(page.content).xpath('//section[@id="patient-return-actions"]')[0].text_content())
        self.assertEqual(self.action('query_return', {'patient_id': patient.id}).status_code, 403)
        self.admin._grant(self.users['frontdesk'].id, self.stores[1].id, {'frontdesk': 'none'})
        self.assertEqual(self.action('query_return', {'patient_id': patient.id}).status_code, 403)

    def test_return_search_rejects_medical_and_exam_without_frontdesk(self):
        task = accepted(self)
        term = task.ydental_patient_id.ydental_number
        for grants in ({'medical': 'write', 'exam': 'none'}, {'medical': 'none', 'exam': 'read'}):
            self.admin._grant(self.users['doctor'].id, self.stores[0].id, grants)
            self.select('doctor')
            page = self.url_open('/ydental/queue')
            self.assertEqual(page.status_code, 200)
            self.assertFalse(html.fromstring(page.content).xpath('//input[@name="return_q"]'))
            denied = self.url_open('/ydental/queue/search', data={'csrf_token': self.csrf, 'return_q': term})
            self.assertEqual(denied.status_code, 403)
            self.assertNotIn(term, denied.text)

    def test_current_execution_and_hold_have_scoped_return_query(self):
        args, execution = self.start_http()
        patient = execution.ydental_patient_id
        page = self.url_open('/ydental/queue')
        section = html.fromstring(page.content).xpath('//section[@id="patient-return-actions"]')[0]
        self.assertEqual(section.xpath('.//form[@data-queue-form="query_own_return"]/input[@name="patient_id"]/@value'), [str(patient.id)])
        self.assertEqual(self.action('query_own_return', {'patient_id': patient.id}).json()['state'], 'no_hold')
        self.assertEqual(self.action('query_own_return', {'patient_id': 2147483647}).status_code, 403)
        target = external(self, execution)
        source(self.front.env['ydental.queue.service'], execution, target)
        self.assertEqual(self.action('reserve', dict(args, execution_id=execution.id, target_task_id=target.id)).status_code, 200)
        page = self.url_open('/ydental/queue')
        section = html.fromstring(page.content).xpath('//section[@id="patient-return-actions"]')[0]
        self.assertEqual(section.xpath('.//form[@data-queue-form="query_own_return"]/input[@name="patient_id"]/@value'), [str(patient.id)])
        self.assertEqual(self.action('query_own_return', {'patient_id': patient.id}).json()['state'], 'holding')
        lease = self.root['ydental.queue.lease'].browse(args['lease_id'])
        lease._save({'ydental_expires_at': self.front.env['ydental.queue.service']._now() - timedelta(seconds=1)})
        self.assertEqual(self.action('expire_station', {'station_id': lease.ydental_station_id.id}).status_code, 200)
        page = self.url_open('/ydental/queue')
        section = html.fromstring(page.content).xpath('//section[@id="patient-return-actions"]')[0]
        self.assertTrue(section.xpath('.//form[@data-queue-form="query_own_return"]'))
        self.assertEqual(self.action('query_own_return', {'patient_id': patient.id}).json()['state'], 'verify')
        self.admin._grant(self.users['doctor'].id, self.stores[0].id, {'medical': 'none'})
        self.assertEqual(self.action('query_own_return', {'patient_id': patient.id}).status_code, 403)

    def test_exam_only_current_execution_can_query_own_patient(self):
        task = accepted(self, mapping=self.mappings[0][2])
        self.admin._grant(self.users['doctor'].id, self.stores[0].id, {'medical': 'none', 'exam': 'write'})
        self.select('doctor')
        response = self.action('enter', {'station_id': self.stations[0][2].id})
        self.assertEqual(response.status_code, 200)
        args = {'lease_id': response.json()['lease_id'], 'token': response.json()['token']}
        call = self.action('call', args)
        self.assertEqual(call.status_code, 200)
        started = self.action('start', dict(args, entry_id=call.json()['entry_id']))
        self.assertEqual(started.status_code, 200)
        page = self.url_open('/ydental/queue')
        section = html.fromstring(page.content).xpath('//section[@id="patient-return-actions"]')[0]
        self.assertEqual(section.xpath('.//form[@data-queue-form="query_own_return"]/input[@name="patient_id"]/@value'), [str(task.ydental_patient_id.id)])
        self.assertEqual(self.action('query_own_return', {'patient_id': task.ydental_patient_id.id}).json()['state'], 'no_hold')
        self.assertEqual(self.action('query_own_return', {'patient_id': 2147483647}).status_code, 403)

    def test_hold_context_denies_new_session_and_other_store(self):
        args, execution = self.start_http()
        patient = execution.ydental_patient_id
        target = external(self, execution)
        source(self.front.env['ydental.queue.service'], execution, target)
        self.assertEqual(self.action('reserve', dict(args, execution_id=execution.id, target_task_id=target.id)).status_code, 200)
        self.assertEqual(self.action('query_own_return', {'patient_id': patient.id}).json()['state'], 'holding')
        front_other = bind(self, self.users['frontdesk'], self.stores[1]).env['ydental.patient.service']
        front_other._operate('relation', {'patient_id': patient.id}, key())
        self.select('doctor')  # HttpCase creates a fresh authenticated browser session.
        page = self.url_open('/ydental/queue')
        section = html.fromstring(page.content).xpath('//section[@id="patient-return-actions"]')[0]
        self.assertFalse(section.xpath('.//form[@data-queue-form="query_own_return"]'))
        self.assertNotIn(patient.ydental_number, section.text_content())
        self.assertEqual(self.action('query_own_return', {'patient_id': patient.id}).status_code, 403)
        switch = self.url_open('/ydental/access/action', data={
            'csrf_token': self.csrf, 'revision': self.revision, 'operation': 'switch',
            'payload': json.dumps({'store_id': self.stores[1].id}), 'output': 'json'})
        self.assertEqual(switch.status_code, 200)
        self.revision = switch.json()['revision']
        self.assertEqual(self.action('query_own_return', {'patient_id': patient.id}).status_code, 403)
        self.assertEqual(self.action('query_return', {'patient_id': patient.id}).json()['state'], 'no_hold')

    def start_http(self):
        task = accepted(self)
        self.select()
        args = self.lease()
        call = self.action('call', args).json()
        result = self.action('start', dict(args, entry_id=call['entry_id']))
        self.assertEqual(result.status_code, 200, result.text)
        return args, self.root['ydental.queue.execution'].browse(result.json()['execution_id'])

    def test_reserve_choices_use_business_labels_and_recheck_source(self):
        args, execution = self.start_http()
        target = external(self, execution)
        other = external(self, execution)
        queue = self.front.env['ydental.queue.service']
        source(queue, execution, target)
        page = self.url_open('/ydental/queue')
        self.assertEqual(page.status_code, 200)
        options = html.fromstring(page.content).xpath('//select[@name="target_task_id"]/option')
        self.assertEqual([item.get('value') for item in options], [str(target.id)])
        label = options[0].text_content()
        self.assertIn(target.ydental_mapping_id.ydental_catalog_id.name, label)
        self.assertIn(target.ydental_mapping_id.ydental_area_id.name, label)
        self.assertIn('UTC', label)
        self.assertNotIn(' / ', label)
        self.assertEqual(self.action('reserve', dict(args, execution_id=execution.id,
                                                    target_task_id=other.id)).status_code, 403)
        service_type = type(self.env['ydental.queue.service'])
        with patch.object(service_type, '_external_target_authorized', return_value=True):
            page = self.url_open('/ydental/queue')
        self.assertEqual(page.status_code, 200)
        doc = html.fromstring(page.content)
        self.assertFalse(doc.xpath('//select[@name="target_task_id"]/option'))
        self.assertIn('有多项任务的信息相同', doc.text_content())

        self.admin._grant(self.users['doctor'].id, self.stores[0].id, {'medical': 'none'})
        page = self.url_open('/ydental/queue')
        if page.status_code == 200:
            self.assertFalse(html.fromstring(page.content).xpath('//select[@name="target_task_id"]/option'))
        self.assertEqual(self.action('reserve', dict(args, execution_id=execution.id,
                                                    target_task_id=target.id)).status_code, 403)

    def test_http_hold_query_and_confirmed_restore(self):
        args, execution = self.start_http()
        target = external(self, execution)
        queue = self.front.env['ydental.queue.service']
        source(queue, execution, target)
        held = self.action('reserve', dict(args, execution_id=execution.id, target_task_id=target.id))
        self.assertEqual(held.status_code, 200, held.text)
        page = self.url_open('/ydental/queue')
        self.assertIn('Reserved return', page.text)
        if 'ydental.clinical.service' in self.env:
            self.assertIn('患者尚未返回时', page.text)
            self.assertNotIn('data-queue-form="handover"', page.text)
        else:
            self.assertIn('data-queue-form="handover"', page.text)
            self.assertNotIn('患者尚未返回时', page.text)
        report(self, target)
        query = self.action('query_return', {'patient_id': target.ydental_patient_id.id})
        self.assertEqual(query.json()['result'], 'hint_only')
        self.assertEqual(self.action('call', args).status_code, 409)
        self.assertEqual(self.action('restore', dict(args, hold_id=held.json()['hold_id'], confirmed=False)).status_code, 403)
        restored = self.action('restore', dict(args, hold_id=held.json()['hold_id'], confirmed=True))
        self.assertEqual(restored.status_code, 200, restored.text)
        self.assertEqual(restored.json()['state'], 'serving')
        self.assertEqual(target.state, 'pending')

    def test_http_save_failure_retry_and_continuation(self):
        args, execution = self.start_http()
        page = self.url_open('/ydental/queue')
        if 'ydental.clinical.service' not in self.env:
            self.assertIn('data-queue-form="handover"', page.text)
            self.assertNotIn('进入当前接诊文书工作台', page.text)
        payload = dict(args, execution_id=execution.id)
        self.assertEqual(self.action('handover', payload).status_code, 403)
        queue = self.front.env['ydental.queue.service']
        source(queue, execution, save_ok=False)
        self.assertEqual(self.action('handover', payload).status_code, 409)
        self.assertEqual(execution.state, 'serving')
        source(queue, execution)
        response = self.action('handover', payload)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.action('handover', payload).json()['continuation_task_id'], response.json()['continuation_task_id'])
        task = self.root['ydental.intake.task'].browse(response.json()['continuation_task_id'])
        self.assertEqual(task.state, 'pending')
        self.assertFalse(task.ydental_entitlement_id)
        self.assertEqual(self.action('heartbeat', args).status_code, 200)

    def test_http_explicit_append_closed_missed_and_revoke(self):
        task = accepted(self)
        close(self)
        self.select('frontdesk')
        payload = {'task_id': task.id, 'reason': 'HTTP explicit append'}
        self.assertEqual(self.action('append', payload).status_code, 403)
        appender(self)
        permit = self.action('append', payload)
        self.assertEqual(permit.status_code, 200, permit.text)
        self.assertEqual(self.action('append', payload).json()['permit_id'], permit.json()['permit_id'])
        page = self.url_open('/ydental/queue')
        row = html.fromstring(page.content).xpath('//div[@data-permit=$permit]', permit=str(permit.json()['permit_id']))[0]
        self.assertIn(task.ydental_patient_id.name, row.text_content())
        self.assertIn(task.ydental_patient_id.ydental_number, row.text_content())
        self.assertIn(task.ydental_mapping_id.ydental_catalog_id.name, row.text_content())
        self.assertTrue(row.xpath('.//form[@data-queue-form="revoke"]'))
        self.select()
        args = self.lease()
        call = self.action('call', args)
        self.assertEqual(call.status_code, 200, call.text)
        self.assertEqual(self.action('missed', dict(args, entry_id=call.json()['entry_id'])).status_code, 200)
        self.select('frontdesk')
        self.assertEqual(self.action('revoke', {'permit_id': permit.json()['permit_id'], 'reason': 'HTTP revoke'}).status_code, 200)
        self.assertEqual(task.ydental_entitlement_id.state, 'held')

    def test_http_append_start_then_revoke_denied(self):
        task = accepted(self)
        close(self)
        appender(self)
        self.select('frontdesk')
        permit = self.action('append', {'task_id': task.id, 'reason': 'HTTP explicit append'}).json()
        self.select()
        args = self.lease()
        call = self.action('call', args).json()
        self.assertEqual(self.action('start', dict(args, entry_id=call['entry_id'])).status_code, 200)
        self.select('frontdesk')
        self.assertEqual(self.action('revoke', {'permit_id': permit['permit_id'], 'reason': 'too late'}).status_code, 409)
        self.assertEqual(task.state, 'started')

    def test_rpc_hold_permit_and_synthetic_source_bypass_denied(self):
        args, execution = self.start_http()
        for model, values in (
                ('ydental.queue.hold', {'ydental_execution_id': execution.id}),
                ('ydental.queue.append.permit', {'state': 'active'}),
                ('ydental.queue.execution', {'state': 'handover'}),
                ('ydental.intake.task', {'ydental_source_execution_id': execution.id}),
                ('ydental.queue.test.return.source', {'ydental_execution_id': execution.id, 'ydental_save_ok': True})):
            self.assertIn('error', self.rpc(model, 'create', [values], {'ydental_queue_mutation': True, 'ydental_return_test_source': True}))
        self.assertIn('error', self.rpc('ydental.queue.service', '_save_before_handover', [execution.id]))
        self.assertEqual(self.action('handover', dict(args, execution_id=execution.id, saved=True)).status_code, 409)

    def test_http_pharmacy_only_read_and_exact_task_start(self):
        catalog = self.catalogs[2]
        catalog._save({'ydental_kind': 'medicine'})
        self.stations[0][2].write({'ydental_kind': 'pharmacy', 'ydental_version': self.stations[0][2].ydental_version})
        self.admin._grant(self.users['doctor'].id, self.stores[0].id, {'medical': 'none', 'exam': 'none', 'pharmacy': 'write'})
        task = accepted(self, mapping=self.mappings[0][2])
        cancelled = accepted(self, mapping=self.mappings[0][2])
        self.select('frontdesk')
        claim = cancelled.ydental_entitlement_id.ydental_claim_id
        free_before = claim.ydental_slot_id.ydental_reservation_free
        response = self.url_open('/ydental/intake/action', data={'csrf_token': self.csrf,
            'revision': self.revision, 'operation': 'void', 'output': 'json', 'key': key(),
            'payload': json.dumps({'task_id': cancelled.id, 'version': cancelled.ydental_version,
                'reason': 'Explicit synthetic unused pharmacy qualification cancellation', 'cancel_qualification': True})})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json()['qualification_cancelled'])
        self.assertEqual(claim.state, 'cancelled')
        self.assertEqual(claim.ydental_slot_id.ydental_reservation_free, free_before + 1)
        self.select()
        self.assertEqual(self.url_open('/ydental/queue').status_code, 200)
        lease = self.action('enter', {'station_id': self.stations[0][2].id})
        self.assertEqual(lease.status_code, 200, lease.text)
        args = {k: lease.json()[k] for k in ('lease_id', 'token')}
        call = self.action('call', args)
        self.assertEqual(call.status_code, 200, call.text)
        self.assertEqual(self.action('start', dict(args, entry_id=call.json()['entry_id'])).status_code, 200)

    def test_http_verify_onsite_takeover_fail_closed_then_new_lease(self):
        from datetime import timedelta
        args, old = self.start_http()
        queue = self.front.env['ydental.queue.service']
        old.ydental_lease_id._save({'ydental_expires_at': queue._now() - timedelta(seconds=1)})
        queue._timeout()
        payload = {'execution_id': old.id, 'confirmed': True, 'reason': 'HTTP on-site confirmation'}
        self.assertEqual(self.action('takeover_verify', payload).status_code, 403)
        self.assertEqual(self.action('takeover_verify', dict(payload, confirmed=False)).status_code, 403)
        source(queue, old)
        response = self.action('takeover_verify', payload)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertNotEqual(response.json()['lease_id'], args['lease_id'])
        self.assertEqual(old.state, 'interrupted')
        self.assertEqual(self.action('takeover_verify', payload).status_code, 409)
        self.assertEqual(self.action('heartbeat', args).status_code, 403)
        self.assertIn('error', self.rpc('ydental.queue.service', '_onsite_source', [old.id, True, 'remote RPC']))

    def test_http_verify_hold_handover_and_untrusted_targets(self):
        from datetime import timedelta
        args, old = self.start_http()
        queue = self.front.env['ydental.queue.service']
        target = external(self, old)
        source(queue, old, target)
        held = self.action('reserve', dict(args, execution_id=old.id, target_task_id=target.id))
        self.assertEqual(held.status_code, 200, held.text)
        unrelated = external(self, old, self.mappings[0][0], independent=True)
        untrusted = external(self, old)
        self.select('frontdesk')
        for task in (unrelated, untrusted):
            response = self.url_open('/ydental/intake/action', data={'csrf_token': self.csrf,
                'revision': self.revision, 'operation': 'report', 'output': 'json', 'key': key(),
                'payload': json.dumps({'task_id': task.id, 'version': task.ydental_version})})
            self.assertEqual(response.status_code, 409, response.text)
        report(self, target)
        old.ydental_lease_id._save({'ydental_expires_at': queue._now() - timedelta(seconds=1)})
        queue._timeout()
        self.select()
        response = self.action('handover_verify_hold', {'execution_id': old.id, 'confirmed': True, 'reason': 'HTTP on-site hold handover'})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(queue._model('hold').browse(held.json()['hold_id']).state, 'handover')
        self.assertEqual(self.root['ydental.intake.task'].browse(response.json()['continuation_task_id']).state, 'pending')

    def test_http_revoked_permit_reopen_normal_report_call_start(self):
        task = accepted(self)
        close(self)
        appender(self)
        self.select('frontdesk')
        permit = self.action('append', {'task_id': task.id, 'reason': 'HTTP append before revoke'}).json()
        self.assertEqual(self.action('revoke', {'permit_id': permit['permit_id'], 'reason': 'HTTP revoke'}).status_code, 200)
        self.root['ydental.supply.service']._business_record(self.stores[0], self.areas[0][0].id)._save({'state': 'open'})
        response = self.url_open('/ydental/intake/action', data={'csrf_token': self.csrf,
            'revision': self.revision, 'operation': 'report', 'output': 'json', 'key': key(),
            'payload': json.dumps({'task_id': task.id, 'version': task.ydental_version})})
        self.assertEqual(response.status_code, 200, response.text)
        self.select()
        args = self.lease()
        call = self.action('call', args).json()
        response = self.action('start', dict(args, entry_id=call['entry_id']))
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.root['ydental.queue.append.permit'].browse(permit['permit_id']).state, 'revoked')

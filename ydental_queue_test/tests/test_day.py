from datetime import datetime, timedelta

from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged

from .common import accepted, arrive_report, bind, key, lease_args, qualify, queue_bind, setup
from .return_common import appender, external, report, reserve, source
from ..models.adapter import Clock
from odoo.addons.ydental_queue.models.ydental_queue_push import masked_name


def at(service, instant):
    return service.with_context(ydental_day_test_clock=Clock(instant))


@tagged('post_install', '-at_install')
class TestQueueDay(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup(cls)

    def setUp(self):
        super().setUp()
        self.root['ir.config_parameter'].set_str('ydental_queue.timeout_seconds', '7200')
        self.day = self.front._now().replace(hour=23, minute=55, second=0, microsecond=0)
        self.midnight = self.day.replace(hour=0, minute=0) + timedelta(days=1)

    def business(self, state, service=None, area=None):
        supply = (service if service is not None else self.group).env['ydental.supply.service']
        area = area if area is not None else self.areas[0][0]
        current = supply._business_record(self.stores[0], area.id)
        return supply._operate('business', dict(area_id=area.id, state=state, reason='S06C explicit business action',
            **({'version': current.ydental_version} if current else {})), key())

    def entry(self, task):
        return self.root['ydental.queue.entry'].search([('ydental_task_id', '=', task.id)], order='id desc', limit=1)

    def doctor_at(self, instant):
        queue = at(queue_bind(self), instant)
        lease = queue._operate('enter', {'station_id': self.stations[0][0].id})
        return queue, lease

    def test_report_then_draining_existing_call_and_expired_slot_start(self):
        task = accepted(self)
        self.business('draining')
        queue, lease = self.doctor_at(self.day)
        call = queue._operate('call', lease_args(lease))
        with self.assertRaises(UserError): self.business('closed')
        queue._operate('start', dict(lease_args(lease), entry_id=call['entry_id']))
        self.business('closed')
        self.assertEqual(task.ydental_entitlement_id.ydental_claim_id.state, 'consumed')

    def test_draining_report_and_combined_walkin_roll_back(self):
        qualification = qualify(self)
        self.front._operate('arrive', {'patient_id': self.root['ydental.intake.task'].browse(qualification['task_id']).ydental_patient_id.id}, key())
        self.business('draining')
        before = self.root['ydental.intake.task'].search_count([])
        with self.assertRaises(UserError):
            self.front._operate('report', {'task_id': qualification['task_id'], 'version': qualification['task_version']}, key())
        self.assertEqual(self.root['ydental.intake.task'].browse(qualification['task_id']).ydental_entitlement_id.state, 'held')
        with self.assertRaises(UserError):
            self.front._operate('walkin_report', {'patient_id': self.root['ydental.intake.task'].browse(qualification['task_id']).ydental_patient_id.id,
                'mapping_id': self.mappings[0][0].id, 'start': fields.Datetime.to_string(self.start), 'end': fields.Datetime.to_string(self.end)}, key())
        self.assertEqual(self.root['ydental.intake.task'].search_count([]), before)

    def test_business_auth_crud_and_closed_requires_draining(self):
        with self.assertRaises(AccessError): self.business('draining', self.front)
        with self.assertRaises(UserError): self.business('closed')
        business = self.group.env['ydental.supply.service']._business_record(self.stores[0], self.areas[0][0].id)
        with self.assertRaises(AccessError): business.with_user(self.users['manager']).write({'state': 'closed'})
        self.business('draining'); self.business('closed')
        self.assertEqual(business.state, 'closed')

    def test_closed_append_report_call_and_ordinary_rejected(self):
        q = qualify(self);task = self.root['ydental.intake.task'].browse(q['task_id'])
        self.front._operate('arrive', {'patient_id': task.ydental_patient_id.id}, key())
        self.business('draining');self.business('closed')
        with self.assertRaises(UserError): report(self, task)
        queue, lease = self.doctor_at(self.front._now())
        with self.assertRaises(UserError):queue._operate('call', lease_args(lease))
        appender(self)._operate('append', {'task_id': task.id, 'reason': 'C explicit append'})
        report(self, task)
        queue._operate('call', lease_args(lease))
        self.assertEqual(self.group.env['ydental.supply.service']._business_record(self.stores[0], self.areas[0][0].id).state, 'closed')

    def test_midnight_serving_and_hold_survive_cleanup(self):
        task = accepted(self);queue,lease = self.doctor_at(self.day)
        call=queue._operate('call',lease_args(lease));r=queue._operate('start',dict(lease_args(lease),entry_id=call['entry_id']))
        execution=self.root['ydental.queue.execution'].browse(r['execution_id'])
        cleanup=at(queue,self.midnight+timedelta(minutes=10))
        target=external(self,execution);source(queue,execution,target)
        held=queue._operate('reserve',dict(lease_args(lease),execution_id=execution.id,target_task_id=target.id))
        cleanup._cleanup_day(self.stores[0],self.day.date())
        self.assertEqual(execution.state,'reserved');self.assertEqual(execution.ydental_started_at,self.day)
        self.assertEqual(self.root['ydental.queue.hold'].browse(held['hold_id']).state,'active')

    def test_first_due_cleanup_retains_verify_execution_hold_and_disabled_station(self):
        self.root['ir.config_parameter'].set_str('ydental_queue.timeout_seconds','20')
        first=accepted(self);second=accepted(self)
        queue,lease=self.doctor_at(self.day)
        called=queue._operate('call',lease_args(lease))
        started=queue._operate('start',dict(lease_args(lease),entry_id=called['entry_id']))
        execution=self.root['ydental.queue.execution'].browse(started['execution_id'])
        hold,target=reserve(self,queue,lease,execution)
        other=at(queue_bind(self,self.second),self.day)
        other_lease=other._operate('enter',{'station_id':self.other_station.id})
        called=other._operate('call',lease_args(other_lease))
        started=other._operate('start',dict(lease_args(other_lease),entry_id=called['entry_id']))
        actual=self.root['ydental.queue.execution'].browse(started['execution_id'])
        at(queue,self.day+timedelta(seconds=21))._timeout()
        self.assertEqual((hold.state,actual.state),('verify','verify'))
        station=self.stations[0][0]
        station.write({'ydental_version':station.ydental_version,'ydental_enabled':False})
        before=self.root['ydental.supply.event'].search_count([])
        at(queue,self.midnight+timedelta(minutes=30))._cleanup_due()
        self.assertEqual((hold.state,actual.state),('verify','verify'))
        self.assertEqual((self.entry(first).state,self.entry(second).state),('reserved','verify'))
        self.assertEqual(self.root['ydental.supply.event'].search_count([]),before)
        self.assertFalse(station.ydental_enabled)

    def test_cleanup_wait_call_preserves_claim_and_is_idempotent(self):
        tasks=[accepted(self),accepted(self)];queue,lease=self.doctor_at(self.day)
        queue._operate('call',lease_args(lease))
        before=self.root['ydental.supply.event'].search_count([])
        cleanup=at(queue,self.midnight+timedelta(minutes=10))
        result=cleanup._cleanup_day(self.stores[0],self.day.date())
        self.assertEqual(len(result['ended']),2)
        self.assertEqual(cleanup._cleanup_day(self.stores[0],self.day.date())['watermark_id'],result['watermark_id'])
        self.assertFalse(queue._busy(queue._model('lease').browse(lease['lease_id'])))
        self.assertEqual(self.root['ydental.supply.event'].search_count([]),before)
        for task in tasks:
            self.assertEqual(self.entry(task).state,'day_closed');self.assertEqual(task.state,'pending')
            self.assertEqual(task.ydental_entitlement_id.state,'held');self.assertEqual(task.ydental_entitlement_id.ydental_claim_id.state,'held')

    def test_call_start_window_and_exact_0010_rejection(self):
        task=accepted(self);queue,lease=self.doctor_at(self.day)
        call=at(queue,self.midnight+timedelta(minutes=9))._operate('call',lease_args(lease))
        with self.assertRaises(AccessError):at(queue,self.midnight+timedelta(minutes=10))._operate('start',dict(lease_args(lease),entry_id=call['entry_id']))
        started=at(queue,self.midnight+timedelta(minutes=9,seconds=59))._operate('start',dict(lease_args(lease),entry_id=call['entry_id']))
        self.assertEqual(started['state'],'serving')

    def test_failed_cleanup_rolls_back_watermark_and_push(self):
        task=accepted(self);queue=at(queue_bind(self),self.midnight+timedelta(minutes=30))
        count=queue._model('outbox').search_count([])
        with self.assertRaises(RuntimeError),self.cr.savepoint():
            queue._cleanup_day(self.stores[0],self.day.date());raise RuntimeError('synthetic worker failure')
        self.assertEqual(self.entry(task).state,'waiting');self.assertEqual(queue._model('outbox').search_count([]),count)
        self.assertFalse(queue._model('cleanup').search([('ydental_store_id','=',self.stores[0].id)]))
        self.assertEqual(queue._cleanup_day(self.stores[0],self.day.date())['result'],'accepted')

    def test_today_new_segment_does_not_revive_yesterday(self):
        # Derived tasks have their own current S05 parent/source rules and no old
        # expired reservation. Re-report does not invent a new entitlement.
        parent=accepted(self)
        self.front._withdraw(parent,'Synthetic fixture prepares derived task')
        task=self.front._new('task',self.stores[0],dict(self.front._identity(parent.ydental_patient_id),name='C derived task',
            ydental_mapping_id=self.mappings[0][0].id,ydental_parent_task_id=parent.id,ydental_source_kind='derived'))
        report(self,task);old=self.entry(task);old._save({'ydental_missed_count':3,'ydental_return':True,'ydental_opportunity_used':True})
        appender(self);self.business('draining')
        permit=self.front.env['ydental.queue.service']._operate('append',{'task_id':task.id,'reason':'C yesterday permit'})
        today=at(self.group,self.midnight+timedelta(minutes=30));queue=today.env['ydental.queue.service']
        queue._cleanup_day(self.stores[0],self.day.date());self.business('open',today)
        front=at(self.front,self.midnight+timedelta(minutes=30))
        front._operate('arrive',{'patient_id':task.ydental_patient_id.id},key())
        front._operate('report',{'task_id':task.id,'version':task.ydental_version},key())
        new=self.entry(task)
        self.assertNotEqual(old.id,new.id);self.assertEqual(old.state,'day_closed');self.assertEqual(old.ydental_business_date,self.day.date())
        self.assertEqual(old.ydental_missed_count,3);self.assertEqual(new.ydental_missed_count,0);self.assertFalse(new.ydental_return or new.ydental_opportunity_used)
        self.assertEqual(self.root['ydental.queue.append.permit'].browse(permit['permit_id']).state,'expired')
        with self.assertRaises(AccessError):old._save({'ydental_business_date':new.ydental_business_date})

    def test_store_timezone_dst_cutoffs(self):
        store=self.stores[0]
        for zone,instant,expected in [('Asia/Shanghai',datetime(2026,10,11,16,9),datetime(2026,10,10).date()),
             ('Asia/Shanghai',datetime(2026,10,11,16,10),datetime(2026,10,11).date()),
             ('America/New_York',datetime(2026,11,1,4,10),datetime(2026,10,31).date()),
             ('America/New_York',datetime(2026,3,8,5,10),datetime(2026,3,7).date())]:
            store.write({'ydental_timezone':zone});self.assertEqual(at(queue_bind(self),instant)._cleanup_cutoff(store),expected)

    def test_delayed_cleanup_today_untouched_and_disabled_station(self):
        task=accepted(self);queue=at(queue_bind(self),self.midnight+timedelta(minutes=30))
        self.stations[0][0].write({'ydental_version':self.stations[0][0].ydental_version,'ydental_enabled':False})
        queue._cleanup_day(self.stores[0],self.day.date())
        self.assertFalse(self.stations[0][0].ydental_enabled)
        with self.assertRaises(UserError):queue._cleanup_day(self.stores[0],self.midnight.date())

    def test_masking_conservative_unicode(self):
        for raw,expected in [('张三丰','张**'),('A','*'),('',''),('  \u200b王 小 明 ','王**'),('<Bob>','<****')]:self.assertEqual(masked_name(raw),expected)

    def test_screen_digest_actual_station_revoke_scope_and_no_private_fields(self):
        task=accepted(self);queue,lease=self.doctor_at(self.front._now())
        call=queue._operate('call',lease_args(lease))
        manager=self.group.env['ydental.queue.service'];created=manager._operate('screen_create',{'area_id':self.areas[0][0].id})
        row=manager._model('screen.token').browse(created['credential_id'])
        self.assertNotEqual(row.ydental_token_hash,created['token'])
        data=manager._screen_snapshot(created['token']);self.assertEqual(data['rows'][0]['station'],self.stations[0][0].name)
        self.assertEqual(set(data['rows'][0]),{'number','name','state','station'})
        with self.assertRaises(AccessError):row.with_user(self.users['manager']).read(['ydental_token_hash'])
        manager._operate('screen_revoke',{'credential_id':row.id})
        with self.assertRaises(AccessError):manager._screen_snapshot(created['token'])
        with self.assertRaises(AccessError):manager._screen_events(created['token'],0)
        self.assertEqual(self.entry(task).state,'calling')

    def test_screen_permissions_unknown_credentials_and_settlement(self):
        with self.assertRaises(AccessError):self.front.env['ydental.queue.service']._operate('screen_create',{'area_id':self.areas[0][0].id})
        with self.assertRaises(AccessError):queue_bind(self)._screen_snapshot('x'*43)
        self.assertRaises(AccessError,queue_bind(self)._category,self.root['ydental.space.station'].create({
            'name':'C settlement','ydental_store_id':self.stores[0].id,'ydental_floor_id':self.stations[0][0].ydental_floor_id.id,
            'ydental_area_id':self.areas[0][0].id,'ydental_kind':'settlement','ydental_callable':False}))

    def test_bus_commit_preparation_and_savepoint_rollback(self):
        queue=self.group.env['ydental.queue.service'];scope=queue._scope_record(self.stores[0],self.areas[0][0])
        version=scope.ydental_version
        with self.assertRaises(RuntimeError),self.cr.savepoint(flush=False):
            queue._publish_scope(self.stores[0],self.areas[0][0]);self.env.flush_all();raise RuntimeError('synthetic rollback')
        self.env.invalidate_all();self.assertEqual(scope.ydental_version,version)
        self.cr.flush()
        messages=self.root['bus.bus'].search([('message','like','ydental.queue.version')])
        import json
        for row in messages:
            payload=json.loads(row.message)['payload'];self.assertEqual(set(payload),{'store','area','version'})

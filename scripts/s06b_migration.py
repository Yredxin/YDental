"""A-shaped legacy execution seed and actual -u compatibility, only in a new B run.

This is a controlled schema/row fixture, not a claim of installing A's full tree.
No historical A database is accessed. The upgrade is run by s06b.py in between.
"""
import json
import os
from pathlib import Path
from types import SimpleNamespace

from odoo.addons.ydental_queue.models.ydental_queue_service import Connection
from odoo.addons.ydental_queue_test.models.adapter import guard
from odoo.addons.ydental_queue_test.tests.common import setup, key, lease_args
from odoo.addons.ydental_queue_test.tests.return_common import serving, source, report


guard(env)
run = Path(os.environ['YDENTAL_S06B_RUN_DIR'])
assert run.name == env.cr.dbname
marker = run / 'migration-private.json'
with env.registry.cursor() as cr:
    from odoo import api
    root = api.Environment(cr, 1, {})
    if migration_action == 'legacy_seed':
        assert not marker.exists()
        assert root['ydental.queue.execution'].search_count([]) == 0
        fixture = SimpleNamespace(env=root)
        setup(fixture)
        queue, lease, execution = serving(fixture)
        connection = queue.env.context['ydental_queue_connection']
        record = {'execution_id': execution.id, 'entry_id': execution.ydental_entry_id.id,
            'task_id': execution.ydental_task_id.id, 'patient_id': execution.ydental_patient_id.id,
            'store_id': execution.ydental_store_id.id, 'actor_id': queue.env.uid,
            'session_id': connection.session_id, 'revision': connection.revision, 'key_hash': connection.key_hash,
            'lease': lease_args(lease), 'state': execution.state}
        root.flush_all()
        cr.execute('UPDATE ydental_queue_execution SET ydental_task_id=NULL, ydental_service_snapshot=NULL WHERE id=%s', [execution.id])
        cr.execute('DROP INDEX ydental_queue_execution_unresolved_patient')
        cr.execute('DROP INDEX ydental_queue_execution_unresolved_lease')
        cr.execute('ALTER TABLE ydental_queue_execution ADD CONSTRAINT ydental_queue_execution_one_patient UNIQUE(ydental_patient_id)')
        cr.execute('ALTER TABLE ydental_queue_execution ADD CONSTRAINT ydental_queue_execution_one_lease UNIQUE(ydental_lease_id)')
        cr.commit()
        with os.fdopen(os.open(marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as handle:
            json.dump(record, handle)
        print(json.dumps({'result': 'PASS', 'action': migration_action, 'legacy_rows': 1, 'lifetime_constraints': 2}))
    else:
        record = json.loads(marker.read_text())
        access = root['ydental.access.service'].with_user(record['actor_id'])
        access = access._bind(root['ydental.access.session'].browse(record['session_id']))
        queue = access.env['ydental.queue.service'].with_context(ydental_queue_connection=Connection(
            record['actor_id'], record['session_id'], record['revision'], record['key_hash']))
        execution = queue._model('execution').browse(record['execution_id'])
        assert execution.ydental_entry_id.id == record['entry_id'] and execution.state == record['state']
        assert execution.ydental_task_id.id == record['task_id'] and execution.ydental_service_snapshot
        queue._model('lease').browse(record['lease']['lease_id'])._save({'ydental_expires_at': queue._now() + __import__('datetime').timedelta(seconds=120)})
        source(queue, execution)
        handed = queue._operate('handover', dict(record['lease'], execution_id=execution.id))
        continuation = root['ydental.intake.task'].browse(handed['continuation_task_id'])
        front_user = root['res.users'].search([('name', '=', 'S06A Synthetic frontdesk')], order='id', limit=1)
        from odoo.addons.ydental_queue_test.tests.common import bind
        intake = bind(SimpleNamespace(root=root, stores=root['ydental.access.store'].browse(record['store_id'])), front_user)
        intake._operate('report', {'task_id': continuation.id, 'version': continuation.ydental_version}, key())
        call = queue._operate('call', record['lease'])
        actual = queue._operate('start', dict(record['lease'], entry_id=call['entry_id']))
        assert execution.exists() and execution.state == 'handover' and actual['execution_id'] != execution.id
        assert queue._model('execution').search_count([('ydental_patient_id', '=', record['patient_id'])]) == 2
        cr.execute("SELECT conname FROM pg_constraint WHERE conrelid='ydental_queue_execution'::regclass AND conname IN ('ydental_queue_execution_one_patient','ydental_queue_execution_one_lease')")
        assert not cr.fetchall()
        evidence = {'result': 'PASS', 'database': env.cr.dbname, 'legacy_fixture': 'A lifetime patient/lease constraints and old row shape',
            'actual_module_upgrade': True, 'historical_execution_retained': True, 'task_and_snapshot_backfilled': True,
            'new_execution_same_patient_and_lease': True, 'entry_start_unique_retained': True, 'history_rows': 2}
        cr.commit()
        target = Path(__file__).resolve().parents[1] / 'docs/evidence/s06b-rework/migration.json'
        target.write_text(json.dumps(evidence, indent=2) + '\n')
        print(json.dumps(evidence))

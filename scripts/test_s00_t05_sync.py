"""Safety checks for Project writes; these do not replace live synchronization."""
import copy
import unittest
from unittest.mock import patch

import s00_t05_sync as sync


class SafetyTests(unittest.TestCase):
    def test_connection_order_only_is_ignored(self):
        self.assertEqual(sync.canonical({'nodes': [{'id': 'a'}, {'id': 'b'}]}),
                         sync.canonical({'nodes': [{'id': 'b'}, {'id': 'a'}]}))

    def test_entity_native_status_and_workflow_changes_are_detected(self):
        baseline = {'state': 'OPEN', 'native_status': 'Todo', 'enabled': True, 'comments': 15}
        for key, value in [('state', 'CLOSED'), ('native_status', 'Done'),
                           ('enabled', False), ('comments', 16)]:
            changed = dict(baseline, **{key: value})
            self.assertNotEqual(sync.canonical(baseline), sync.canonical(changed))

    def test_duplicate_field_rejected(self):
        with self.assertRaises(RuntimeError):
            sync.field({'fields': {'nodes': [{'name': '阶段'}, {'name': '阶段'}]}}, '阶段')

    def test_duplicate_option_rejected(self):
        value = {'name': '执行状态', '__typename': 'ProjectV2SingleSelectField',
                 'options': [{'id': str(i), 'name': n} for i, n in enumerate(sync.STATES + ['待启用'])]}
        with self.assertRaises(RuntimeError):
            sync.field({'fields': {'nodes': [value]}}, '执行状态')

    def test_second_round_never_writes(self):
        runner = sync.Sync.__new__(sync.Sync)
        runner.round = 'second'
        runner.api = lambda *a: self.fail('A second-round write reached the API')
        with self.assertRaises(RuntimeError):
            runner.change('archiveProjectV2Item', {}, 'clientMutationId', lambda *a: None)

    def test_unexpected_readback_stops_after_one_mutation(self):
        runner = sync.Sync.__new__(sync.Sync)
        runner.round, runner.log, runner.mutations = 'first', [], 0
        runner.project = {'state': 'OPEN', 'isArchived': False}
        runner.api = lambda *a: ({'archiveProjectV2Item': {}}, {})
        runner.read = lambda *a: {'state': 'CLOSED', 'isArchived': True}
        original = copy.deepcopy(runner.project)
        with patch.object(sync, 'save'):
            with self.assertRaises(RuntimeError):
                runner.change('archiveProjectV2Item', {}, 'clientMutationId',
                              lambda p, _: p.update(isArchived=True))
        self.assertEqual(runner.mutations, 1)
        self.assertEqual(runner.project, original)


if __name__ == '__main__':
    unittest.main()

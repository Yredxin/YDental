"""Pure snapshot-shape tests for the S11 cancel/receive race harness."""

import unittest

import race_lab_cancel_receive as runner


class FakeCursor:
    def __init__(self, rows):
        self.rows = rows
        self.query = None
        self.params = None

    def execute(self, query, params):
        self.query = query
        self.params = params

    def fetchall(self):
        return self.rows


class TestTransitionSnapshot(unittest.TestCase):
    def test_nullable_persisted_values_are_added_even_when_orm_omits_them(self):
        events = [{"id": 1066, "ydental_kind": "sent"}, {"id": 1067, "ydental_kind": "received"}]
        cursor = FakeCursor([(1066, "draft", "sent"), (1067, "sent", "received")])

        result = runner.add_transition_columns(cursor, events)

        self.assertEqual(result[0]["ydental_before_state"], "draft")
        self.assertEqual(result[0]["ydental_after_state"], "sent")
        self.assertEqual(result[1]["ydental_before_state"], "sent")
        self.assertEqual(result[1]["ydental_after_state"], "received")
        self.assertEqual(cursor.params, [[1066, 1067]])

    def test_sql_null_is_preserved_and_missing_database_rows_fail_closed(self):
        events = [{"id": 1066, "ydental_kind": "legacy"}]
        runner.add_transition_columns(FakeCursor([(1066, None, None)]), events)
        self.assertIsNone(events[0]["ydental_before_state"])
        self.assertIsNone(events[0]["ydental_after_state"])

        with self.assertRaises(runner.common.Refusal):
            runner.add_transition_columns(FakeCursor([]), [{"id": 1066}])

    def test_normalized_snapshots_preserve_old_events_and_retain_new_event_detection(self):
        before_events = [{"id": 1066, "ydental_kind": "sent"}]
        after_events = [
            {"id": 1066, "ydental_kind": "sent"},
            {"id": 1067, "ydental_kind": "received"},
        ]

        runner.add_transition_columns(FakeCursor([(1066, "draft", "sent")]), before_events)
        runner.add_transition_columns(FakeCursor([
            (1066, "draft", "sent"), (1067, "sent", "received"),
        ]), after_events)

        self.assertEqual(before_events[0], after_events[0])
        self.assertEqual(len(after_events), len(before_events) + 1)
        self.assertNotEqual(before_events, after_events)


if __name__ == "__main__":
    unittest.main()

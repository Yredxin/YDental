"""Offline projection checks for the completed W1 synthetic user witness.

This module has no Odoo, PostgreSQL, subprocess, or network imports. It does
not grant permission to run another database or Odoo experiment.
"""

import json
import re
import unittest


FUTURE_AUTH_COMMENT_ID = None
SAFE_TYPE = re.compile(r"^[a-z][a-z0-9_.-]{0,31}(?:[/.][a-z][a-z0-9_.-]{0,31}){0,2}$")


def project_intent(channel, notification_type, _payload, synthetic_user_id):
    """Return only safe categorical metadata; never return channel IDs or payload."""

    safe_type = (
        notification_type if isinstance(notification_type, str)
        and len(notification_type) <= 80
        and SAFE_TYPE.fullmatch(notification_type)
        else "NOT_CAPTURED_UNSAFE"
    )
    model = channel[1] if isinstance(channel, tuple) and len(channel) >= 3 else None
    role = (
        "settings_actor" if model == "res.users"
        and synthetic_user_id is not None
        and channel[2] == synthetic_user_id else "other"
    )
    return {
        "notification_type": safe_type,
        "target_model_category": model if model in ("res.users", "discuss.channel", "res.groups") else "other",
        "target_role": role,
    }


class OfflineProjectionTests(unittest.TestCase):
    def test_real_type_not_collapsed_and_sensitive_values_excluded(self):
        result = project_intent(
            ("synthetic_db", "res.users", 724001), "mail.record/insert",
            {"payload": "private-token@example.invalid"}, 724001,
        )
        self.assertEqual(result["notification_type"], "mail.record/insert")
        self.assertEqual(result["target_role"], "settings_actor")
        encoded = json.dumps(result)
        for sensitive in ("synthetic_db", "724001", "private-token@example.invalid"):
            self.assertNotIn(sensitive, encoded)

    def test_unsafe_event_stays_uncaptured(self):
        result = project_intent(("synthetic_db", "res.users", 1),
                                "token@example.invalid", {}, 1)
        self.assertEqual(result["notification_type"], "NOT_CAPTURED_UNSAFE")

    def test_unexpected_target_stays_other(self):
        result = project_intent(("synthetic_db", "res.users", 2),
                                "mail.record/insert", {}, 1)
        self.assertEqual(result["target_role"], "other")

    def test_future_authorization_remains_closed(self):
        self.assertIsNone(FUTURE_AUTH_COMMENT_ID)


if __name__ == "__main__":
    unittest.main()

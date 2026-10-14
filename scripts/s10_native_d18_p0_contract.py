"""Offline design check for a future synthetic fixture; never connects to Odoo/PG.

SIMULATED checks only. This module deliberately has no fixture execution entry.
"""

from dataclasses import dataclass


FUTURE_AUTH_COMMENT_ID = None


@dataclass(frozen=True)
class Delta:
    baseline_messages: frozenset[int]
    current_messages: frozenset[int]
    baseline_mail: frozenset[int]
    current_mail: frozenset[int]
    baseline_attachments: frozenset[int]
    current_attachments: frozenset[int]


def classify_delta(snapshot: Delta, approved_new_message_ids: frozenset[int]) -> dict:
    """Classify observed IDs in the *same transaction cursor* before commit.

    Approval of message IDs also requires future model/subtype/origin review;
    this helper does not infer whether a message was sent externally.
    """
    if FUTURE_AUTH_COMMENT_ID is not None:
        raise RuntimeError("This offline contract must remain unauthorized")
    if not snapshot.baseline_messages <= snapshot.current_messages:
        raise ValueError("Baseline internal messages disappeared")
    if not snapshot.baseline_mail <= snapshot.current_mail:
        raise ValueError("Baseline mail queue disappeared")
    if not snapshot.baseline_attachments <= snapshot.current_attachments:
        raise ValueError("Baseline attachments disappeared")
    messages = snapshot.current_messages - snapshot.baseline_messages
    queued_mail = snapshot.current_mail - snapshot.baseline_mail
    attachments = snapshot.current_attachments - snapshot.baseline_attachments
    if messages != approved_new_message_ids or queued_mail:
        raise ValueError("Unapproved new internal messages or queued mail")
    return {"new_internal_messages": len(messages), "new_queued_mail": 0,
            "new_attachments_requiring_source_check": len(attachments)}


def classify_file(*, mime: str, sha256: str, size: int, expected_svg_sha: set[str],
                  checklist_for_known_file: bool, attachment_refs: int) -> str:
    """A file may be accepted only when source and reference state are explained."""
    if mime == "image/svg+xml" and sha256 in expected_svg_sha and size > 0:
        return "AVATAR_CANDIDATE_REVIEW_REFERENCE" if not attachment_refs else "AVATAR_REFERENCED"
    if size == 0 and checklist_for_known_file:
        return "GC_CHECKLIST_FOR_KNOWN_FILE"
    return "UNKNOWN_STOP"


def run_fixture(*_args, **_kwargs):
    raise RuntimeError("NOT_AUTHORIZED: D1.8-P0 has no database or Odoo execution budget")

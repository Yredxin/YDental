"""Offline-only contract for a possible future synthetic bus investigation.

This module never imports Odoo or a database driver. Its pure function is for
simulations; an execution gate stays closed until a later explicit authorization.
"""

from dataclasses import dataclass


FUTURE_AUTH_COMMENT_ID = None
FINANCE_FIELDS = ("account_payment", "account_partial_reconcile")
OBSERVED_FIELDS = ("mail_mail", "bus_bus", *FINANCE_FIELDS)
EXPECTED_MESSAGE_MODELS = ("res.partner", "res.users")


@dataclass(frozen=True)
class SimulatedPolicy:
    """Proposed constraints; never a production authorization."""

    bus_type: str
    bus_target_model: str = "res.users"
    bus_target_role: str = "settings_actor"
    source_action: str = "after_settings_user_create"
    maximum_intents: int = 1
    expected_svg_sha256: str = ""


def require_future_authorization():
    """Fail closed for any attempt to use this as an executable fixture."""

    if FUTURE_AUTH_COMMENT_ID is None:
        raise PermissionError("A new GPT authorization is required")
    raise PermissionError("This offline contract contains no Odoo execution path")


def assess_simulated(before, during, after_rollback, *, policy, source_proven=False):
    """Classify sanitized mock metadata; never read a file, Odoo or PostgreSQL."""

    if not isinstance(policy, SimulatedPolicy) or not source_proven:
        return "STOP_SOURCE_UNPROVEN"
    if during.get("source_action") != policy.source_action:
        return "STOP_SOURCE_ACTION"
    if during.get("cross_company_target") or during.get("global_group_changed"):
        return "STOP_CROSS_COMPANY_OR_GROUP"
    for name in OBSERVED_FIELDS:
        if before["counts"][name] != during["counts"][name]:
            return "STOP_COMPONENT_" + name.upper()
    if before["counts"] != after_rollback["counts"]:
        return "STOP_ROLLBACK_MISMATCH"
    if sorted(during.get("new_message_models", ())) != list(EXPECTED_MESSAGE_MODELS):
        return "STOP_MESSAGE_SOURCE"
    intents = during.get("bus_intents", ())
    if len(intents) != policy.maximum_intents:
        return "STOP_INTENT_COUNT"
    if any(i.get("type") in (None, "other", "UNKNOWN_REDACTED") for i in intents):
        return "NOT_CAPTURED"
    for intent in intents:
        if (intent.get("type"), intent.get("target_model"), intent.get("target_role")) != (
            policy.bus_type, policy.bus_target_model, policy.bus_target_role
        ):
            return "STOP_INTENT_SCOPE_OR_TYPE"
    files = during.get("files", ())
    if len(files) != 2 or {item.get("kind") for item in files} != {"avatar_svg", "gc_checklist"}:
        return "STOP_UNKNOWN_FILE"
    avatar = next(item for item in files if item["kind"] == "avatar_svg")
    checklist = next(item for item in files if item["kind"] == "gc_checklist")
    if not (
        avatar.get("sha256") == policy.expected_svg_sha256
        and avatar.get("exact_core_template") is True
        and avatar.get("content_addressed_path") is True
        and avatar.get("attachment_refs_after_rollback") == 0
        and checklist.get("sha256") == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        and checklist.get("for_avatar") is True
        and checklist.get("attachment_refs_after_rollback") == 0
    ):
        return "STOP_FILE_PROOF"
    return "SIMULATED_SYNTHETIC_ALLOWED"

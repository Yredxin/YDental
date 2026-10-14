"""Payload-free classification for the Odoo-C1-R1 synthetic Bus witness."""

import re


SAFE_TYPE = re.compile(r"^[a-z][a-z0-9_.-]{0,31}(?:[/.][a-z][a-z0-9_.-]{0,31}){0,2}$")
TARGET_MODELS = frozenset({'res.users', 'res.groups', 'discuss.channel'})


def project_intent(channel, notification_type, synthetic_roles):
    """Project only type, model category and role; never inspect a payload."""
    kind = (notification_type if isinstance(notification_type, str)
            and len(notification_type) <= 80 and SAFE_TYPE.fullmatch(notification_type)
            else 'NOT_CAPTURED_UNSAFE')
    model = channel[1] if isinstance(channel, tuple) and len(channel) > 1 else None
    role = (synthetic_roles.get(channel[2], 'other') if isinstance(channel, tuple)
            and len(channel) > 2 and model == 'res.users' else 'other')
    return {'type': kind, 'target_model': model if model in TARGET_MODELS else 'other',
            'scope': role}


def bus_stage(stage, row_delta, new_types):
    """Keep preparation and warehouse effects separate without declaring either safe."""
    if stage in ('warehouse_setup', 'after_rejected_setup', 'after_idempotent_same_key',
                 'after_idempotent_new_key'):
        if 'stock_group_sync' in new_types:
            return 'UNEXPECTED_STOCK_GROUP_SYNC'
        return 'WAREHOUSE_BUS_RECORDED' if row_delta or new_types else 'NO_WAREHOUSE_BUS'
    return 'PREPARATION_BUS_RECORDED' if row_delta or new_types else 'NO_PREPARATION_BUS'

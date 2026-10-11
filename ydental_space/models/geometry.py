import math

from odoo.exceptions import ValidationError


def check_geometry(record):
    values = [record.ydental_x, record.ydental_y, record.ydental_width,
              record.ydental_height, record.ydental_angle]
    if not all(math.isfinite(value) and abs(value) <= 100000 for value in values):
        raise ValidationError(record.env._('Geometry must use finite, bounded coordinates.'))
    if record.ydental_width <= 0 or record.ydental_height <= 0:
        raise ValidationError(record.env._('Width and height must be positive.'))


def capability_commands(env, commands, existing=()):
    current = set(existing)
    for command in commands:
        if not isinstance(command, (list, tuple)) or not command or command[0] not in (3, 4, 5, 6):
            raise ValidationError(env._('Select existing capabilities; nested editing is forbidden.'))
        ids = command[2] if command[0] == 6 else [command[1]] if command[0] in (3, 4) else []
        if not isinstance(ids, (list, tuple)) or any(type(value) is not int for value in ids):
            raise ValidationError(env._('Capability identifiers must be integers.'))
        found = env['ydental.access.capability'].sudo().with_context(active_test=False).browse(ids).exists()
        if set(found.ids) != set(ids):
            raise ValidationError(env._('Unknown capability.'))
        if command[0] in (4, 6):
            added = set(ids) - current
            if any(not capability.active for capability in found if capability.id in added):
                raise ValidationError(env._('New capability associations require active capabilities.'))
            current = set(ids) if command[0] == 6 else current | set(ids)
        elif command[0] == 3:
            current.difference_update(ids)
        else:
            current.clear()

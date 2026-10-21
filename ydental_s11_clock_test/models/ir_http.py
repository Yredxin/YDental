from datetime import datetime, timezone
import os

from odoo import models
from odoo.http import request

from .clock import Clock, EXPECTED_DB, guard, session_hash


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _pre_dispatch(cls, rule, args):
        super()._pre_dispatch(rule, args)
        if (request.env.uid and request.env.cr.dbname == EXPECTED_DB
                and os.environ.get('YDENTAL_S11_CLOCK_RUN_ID')
                and request.env.user.has_group('ydental_s11_clock_test.group_operator')):
            guard(request.env)
            key = session_hash(request.session.sid[:42])
            row = request.env['ydental.s11.clock.session'].sudo().search([
                ('session_hash', '=', key), ('actor_id', '=', request.env.uid),
                ('run_id', '=', __import__('os').environ.get('YDENTAL_S11_CLOCK_RUN_ID')),
                ('expires_at', '>', datetime.now(timezone.utc).replace(tzinfo=None)),
            ], limit=1)
            if row:
                request.update_context(ydental_s11_clock=Clock(
                    row.run_id, fields_to_utc(row.simulated_now), request.env.uid, key, row.store_id.id))


def fields_to_utc(value):
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)

import secrets
import unicodedata
from dataclasses import dataclass

from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError

from odoo.addons.bus.models.bus import SKIP_NOTIFICATION, channel_with_db

from .ydental_queue_service import digest


@dataclass(frozen=True)
class QueueNotice:
    outbox_id: int


def masked_name(value):
    visible = ''.join(c for c in (value or '') if not c.isspace() and not unicodedata.category(c).startswith('C'))
    return visible[0] + '*' * (len(visible) - 1) if len(visible) > 1 else ('*' if visible else '')


class YDentalQueueScope(models.Model):
    _name = 'ydental.queue.scope'
    _description = 'Area committed snapshot version'
    _inherit = 'ydental.queue.record'

    ydental_area_id = fields.Many2one('ydental.space.area', required=True, ondelete='restrict')
    ydental_channel = fields.Char(required=True, groups=fields.NO_ACCESS)
    _one_area = models.Constraint('UNIQUE(ydental_store_id, ydental_area_id)', 'One version scope per store area.')


class YDentalQueueOutbox(models.Model):
    _name = 'ydental.queue.outbox'
    _description = 'Transactional minimal queue version notification'
    _inherit = 'ydental.queue.record'

    ydental_scope_id = fields.Many2one('ydental.queue.scope', required=True, ondelete='restrict')
    ydental_scope_version = fields.Integer(required=True)
    _one_version = models.Constraint('UNIQUE(ydental_scope_id, ydental_scope_version)', 'A scope version is published once.')


class YDentalQueueScreenToken(models.Model):
    _name = 'ydental.queue.screen.token'
    _description = 'Revocable read-only area screen credential digest'
    _inherit = 'ydental.queue.record'

    ydental_area_id = fields.Many2one('ydental.space.area', required=True, ondelete='restrict')
    ydental_token_hash = fields.Char(required=True, groups=fields.NO_ACCESS, copy=False)
    ydental_actor_id = fields.Many2one('res.users', required=True, ondelete='restrict')
    ydental_revoked_at = fields.Datetime()
    state = fields.Selection([('active', 'Active'), ('revoked', 'Revoked')], required=True, default='active')
    _one_digest = models.Constraint('UNIQUE(ydental_token_hash)', 'Screen credential digests must be unique.')


class BusBus(models.Model):
    _inherit = 'bus.bus'

    def _prepare_payload(self, payload):
        if type(payload) is QueueNotice:
            # Even flush=False savepoint rollback cannot send a phantom success.
            row = self.env['ydental.queue.outbox'].sudo().browse(payload.outbox_id).exists()
            if not row:
                return SKIP_NOTIFICATION
            scope = row.ydental_scope_id
            return {'store': scope.ydental_store_id.id, 'area': scope.ydental_area_id.id,
                    'version': row.ydental_scope_version}
        return super()._prepare_payload(payload)


class YDentalQueueRecord(models.AbstractModel):
    _inherit = 'ydental.queue.record'

    def _changed_scopes(self):
        pairs = set()
        if self._name in ('ydental.queue.entry', 'ydental.queue.hold'):
            pairs.update((r.ydental_store_id.id, r.ydental_area_id.id) for r in self)
        elif self._name in ('ydental.queue.lease', 'ydental.queue.execution'):
            for record in self:
                lease = record if self._name == 'ydental.queue.lease' else record.ydental_lease_id
                pairs.add((record.ydental_store_id.id, lease.ydental_station_id.ydental_queue_area_id.id))
        for store_id, area_id in sorted(pairs):
            if area_id:
                self.env['ydental.queue.service']._publish_scope(
                    self.env['ydental.access.store'].sudo().browse(store_id), self.env['ydental.space.area'].sudo().browse(area_id))

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._changed_scopes()
        return records

    def write(self, vals):
        result = super().write(vals)
        if set(vals) - {'ydental_version', 'ydental_heartbeat_at', 'ydental_expires_at'}:
            self._changed_scopes()
        return result


class YDentalQueueService(models.AbstractModel):
    _inherit = 'ydental.queue.service'

    def _scope_record(self, store, area):
        return self._model('scope').search([('ydental_store_id', '=', store.id), ('ydental_area_id', '=', area.id)], limit=1)

    def _publish_scope(self, store, area):
        # All authoritative mutations hold supply/intake/queue fences already.
        scope = self._scope_record(store, area)
        if not scope:
            scope = self._model('scope')._new({'name': 'queue_version', 'ydental_store_id': store.id,
                'ydental_area_id': area.id, 'ydental_channel': secrets.token_urlsafe(32)})
        else:
            scope._save({})
        outbox = self._model('outbox')._new({'name': 'queue_version', 'ydental_store_id': store.id,
            'ydental_scope_id': scope.id, 'ydental_scope_version': scope.ydental_version})
        self.env['bus.bus']._sendone(scope.ydental_channel, 'ydental.queue.version', QueueNotice(outbox.id))

    def _screen_manage(self, operation, payload):
        store = self.env['ydental.supply.service']._access(write=True)
        with self.env.cr.savepoint():
            self._locks()
            if operation == 'screen_create' and set(payload) == {'area_id'}:
                area = self.env['ydental.supply.service']._space('area', payload['area_id'], store)
                if not area.ydental_reporting or area.ydental_purpose == 'settlement':
                    raise ValidationError(self.env._('screen_area_required: Select a clinical reporting area.'))
                token = secrets.token_urlsafe(32)
                row = self._model('screen.token')._new({'name': 'area_screen', 'ydental_store_id': store.id,
                    'ydental_area_id': area.id, 'ydental_token_hash': digest(token), 'ydental_actor_id': self.env.uid})
                self._audit('screen_create', row, {'area_id': area.id})
                return {'result': 'accepted', 'credential_id': row.id, 'token': token}
            if operation == 'screen_revoke' and set(payload) == {'credential_id'}:
                row = self._model('screen.token').browse(self.env['ydental.intake.service']._id(payload['credential_id'])).exists()
                if not row or row.ydental_store_id != store:
                    raise AccessError(self.env._('access_denied: Select a screen credential in the current store.'))
                if row.state != 'revoked':
                    row._save({'state': 'revoked', 'ydental_revoked_at': self._now()})
                    self._audit('screen_revoke', row, {'area_id': row.ydental_area_id.id})
                return {'result': 'accepted', 'credential_id': row.id}
            raise ValidationError(self.env._('Unknown or missing workstation arguments.'))

    def _operate(self, operation, payload):
        if operation in ('screen_create', 'screen_revoke'):
            if not isinstance(payload, dict):
                raise ValidationError(self.env._('Unknown or missing workstation arguments.'))
            return self._screen_manage(operation, payload)
        return super()._operate(operation, payload)

    def _screen_credential(self, token):
        if not isinstance(token, str) or not 40 <= len(token) <= 128:
            raise AccessError(self.env._('access_denied: Screen credential is invalid or revoked.'))
        row = self._model('screen.token').search([('ydental_token_hash', '=', digest(token)), ('state', '=', 'active')], limit=1)
        if row:
            # Read-only credential fence: revoke-first forces an RR retry; a
            # snapshot-first reader finishes before revoke can commit. No later
            # patient/supply/queue lock is acquired by the screen read path.
            self.env.cr.execute('SELECT id FROM ydental_queue_screen_token WHERE id=%s FOR SHARE', [row.id])
            row.invalidate_recordset()
        if not row or row.state != 'active' or not row.ydental_area_id.active or not row.ydental_area_id.ydental_reporting:
            raise AccessError(self.env._('access_denied: Screen credential is invalid or revoked.'))
        return row

    def _area_snapshot(self, store, area):
        scope = self._scope_record(store, area)
        entries = self._model('entry').search([('ydental_store_id', '=', store.id), ('ydental_area_id', '=', area.id),
            ('state', 'in', ('waiting', 'calling'))]).filtered(lambda e: not self._queue_day_expired(e) and
                e.ydental_task_id.ydental_mapping_id.ydental_catalog_id.ydental_kind in ('care', 'procedure', 'prosthesis', 'exam', 'medicine'))
        rows = []
        for entry in entries:
            calling = entry.state == 'calling' and entry.ydental_lease_id.ydental_active and entry.ydental_lease_id.ydental_expires_at > self._now()
            station = entry.ydental_lease_id.ydental_station_id.name if calling else ''
            rows.append({'number': entry.ydental_number, 'name': masked_name(entry.ydental_patient_id.name),
                'state': 'calling' if calling else 'waiting', 'station': station})
        business = self.env['ydental.supply.service']._business_record(store, area.id)
        return {'store': store.id, 'area': area.id, 'version': scope.ydental_version if scope else 0,
                'business_date': fields.Date.to_string(self._local_now(store).date()),
                'business': business.state if business else 'closed', 'rows': rows,
                'last_id': self.env['bus.bus'].sudo()._bus_last_id()}

    def _screen_snapshot(self, token):
        credential = self._screen_credential(token)
        return self._area_snapshot(credential.ydental_store_id, credential.ydental_area_id)

    def _screen_events(self, token, last_id):
        credential = self._screen_credential(token)
        scope = self._scope_record(credential.ydental_store_id, credential.ydental_area_id)
        if type(last_id) is not int or last_id < 0:
            raise ValidationError(self.env._('A nonnegative bus cursor is required.'))
        notifications = self.env['bus.bus']._poll([channel_with_db(self.env.cr.dbname, scope.ydental_channel)], last_id) if scope else []
        return {'events': [r['message']['payload'] for r in notifications if r['message']['type'] == 'ydental.queue.version'],
                'last_id': self.env['bus.bus'].sudo()._bus_last_id()}

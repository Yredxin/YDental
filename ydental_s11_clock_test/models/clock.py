import hashlib
import json
import os
import re
import stat
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from odoo import SUPERUSER_ID, api, fields, models
from odoo.exceptions import AccessError, ValidationError


EXPECTED_DB = 'ydental_s11_synth_20261023_01'
EXPECTED_OID = 2171423
EXPECTED_CLUSTER = '7694897083368259627'


@dataclass(frozen=True)
class Clock:
    run_id: str
    now: datetime
    actor_id: int
    session_hash: str
    store_id: int


def run_id():
    value = os.environ.get('YDENTAL_S11_CLOCK_RUN_ID', '')
    if not re.fullmatch(r'[0-9]{8}T[0-9]{6}Z-[a-f0-9]{12}', value):
        raise AccessError('S11 debug clock run is not active.')
    return value


def guard(env, live_database=True):
    current_run = run_id()
    if env.cr.dbname != EXPECTED_DB:
        raise AccessError('S11 debug clock refused outside its admitted scratch run.')
    root = Path(__file__).resolve().parents[2]
    run_dir = Path(os.environ.get('YDENTAL_S11_CLOCK_RUN_DIR', '/nonexistent'))
    expected_dir = root / '.local' / 's11' / 'new-target-clock-runs' / current_run
    if run_dir.resolve() != expected_dir.resolve():
        raise AccessError('S11 debug clock run directory does not match its fixed scope.')
    info = run_dir.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
        raise AccessError('S11 debug clock run directory is not private.')
    manifest_path = run_dir / 'clock.json'
    manifest_info = manifest_path.lstat()
    if not stat.S_ISREG(manifest_info.st_mode) or manifest_info.st_uid != os.getuid() or stat.S_IMODE(manifest_info.st_mode) != 0o600:
        raise AccessError('S11 debug clock manifest is not private.')
    raw = manifest_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != os.environ.get('YDENTAL_S11_CLOCK_MANIFEST_SHA256'):
        raise AccessError('S11 debug clock manifest digest does not match the admitted run.')
    manifest = json.loads(raw)
    if manifest.get('run_id') != current_run or manifest.get('mode') != 'S11_SESSION_CLOCK' or manifest.get('database_oid') != EXPECTED_OID:
        raise AccessError('S11 debug clock manifest target does not match.')
    active_path = root / '.local' / 's11' / 'new-target-active.json'
    active = json.loads(active_path.read_text())
    active_clock = active.get('s11_session_clock') or {}
    if (active.get('database_name') != EXPECTED_DB or active.get('database_oid') != EXPECTED_OID
            or active.get('cluster_ref') != manifest.get('database_cluster')
            or active.get('branch') != manifest.get('branch')
            or active.get('candidate_commit') != manifest.get('candidate_commit')
            or active.get('debugger_mode') != 'gdb'
            or active_clock.get('run_id') != current_run
            or active_clock.get('manifest_sha256') != os.environ.get('YDENTAL_S11_CLOCK_MANIFEST_SHA256')):
        raise AccessError('S11 owned GDB service no longer matches the clock run candidate.')
    if live_database:
        env.cr.execute('''
            SELECT d.oid, c.system_identifier::text
              FROM pg_database d CROSS JOIN pg_control_system() c
             WHERE d.datname = current_database()
        ''')
        row = env.cr.fetchone()
        if (not row or row[0] != EXPECTED_OID
                or row[1] != str(manifest.get('database_cluster'))):
            raise AccessError('S11 debug clock live database or cluster identity does not match.')
    else:
        env.cr.execute('SELECT oid FROM pg_database WHERE datname = current_database()')
        row = env.cr.fetchone()
        if not row or row[0] != EXPECTED_OID:
            raise AccessError('S11 debug clock database identity does not match.')


def session_hash(sid):
    return hashlib.sha256(sid.encode('utf-8')).hexdigest()


def app_now(service, fallback):
    source = service.env.context.get('ydental_s11_clock')
    if type(source) is Clock:
        guard(service.env, live_database=False)
        if source.run_id != run_id() or (source.actor_id != service.env.uid and service.env.uid != SUPERUSER_ID):
            raise AccessError('S11 debug clock session binding is invalid.')
        if service.env.uid != SUPERUSER_ID:
            access_session = service.env['ydental.access.service']._scope()
            if access_session.ydental_store_id.id != source.store_id:
                raise AccessError('S11 debug clock is bound to a different active store.')
        return source.now.replace(tzinfo=None)
    return fallback()


class ClockSession(models.Model):
    _name = 'ydental.s11.clock.session'
    _description = 'S11 session scoped synthetic application time'

    session_hash = fields.Char(required=True, index=True)
    actor_id = fields.Many2one('res.users', required=True, ondelete='cascade')
    store_id = fields.Many2one('ydental.access.store', required=True, ondelete='cascade')
    run_id = fields.Char(required=True, index=True)
    simulated_now = fields.Datetime(required=True)
    expires_at = fields.Datetime(required=True)

    _one_session = models.Constraint('UNIQUE(session_hash)', 'Only one S11 clock state may exist for a browser session.')


class ClockEvent(models.Model):
    _name = 'ydental.s11.clock.event'
    _description = 'S11 synthetic clock change audit'
    _order = 'id desc'

    run_id = fields.Char(required=True, index=True)
    actor_id = fields.Many2one('res.users', required=True, ondelete='restrict')
    store_id = fields.Many2one('ydental.access.store', required=True, ondelete='restrict')
    operation = fields.Selection([('start', 'Start'), ('advance', 'Advance'), ('clear', 'Clear')], required=True)
    old_now = fields.Datetime()
    new_now = fields.Datetime()
    physical_at = fields.Datetime(required=True)
    reason = fields.Char(required=True)

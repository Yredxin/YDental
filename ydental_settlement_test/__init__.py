import hashlib
import json
import os
from pathlib import Path
import re

from odoo.exceptions import AccessError


def pre_init_hook(env):
    database = env.cr.dbname
    run = Path(os.environ.get('YDENTAL_S10_RUN_DIR', '/nonexistent'))
    if (not re.fullmatch(r'ydental_s10_test_[0-9]{14}_[a-f0-9]{8}', database)
            or run.is_symlink() or run.name != database):
        raise AccessError('S10 synthetic adapter requires its own isolated database.')
    marker_path = run / 'database.json'
    config_path = run / 'odoo.conf'
    if (not marker_path.is_file() or marker_path.is_symlink() or
            not config_path.is_file() or config_path.is_symlink()):
        raise AccessError('S10 synthetic adapter requires its private marker and config.')
    marker = json.loads(marker_path.read_text())
    env.cr.execute('SELECT oid FROM pg_database WHERE datname=%s', [database])
    oid = env.cr.fetchone()[0]
    if (marker.get('database') != database or marker.get('oid') != oid or
            marker.get('cluster') != '7694897083368259627' or
            marker.get('core') != 'f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb' or
            hashlib.sha256(config_path.read_bytes()).hexdigest() != marker.get('config_sha256')):
        raise AccessError('S10 synthetic adapter database identity changed.')


from . import models

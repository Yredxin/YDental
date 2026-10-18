"""One non-secret native logger attestation for the MAIN-A engineering task."""
import hashlib
import json
import logging
import os
from pathlib import Path


class NativePrivacyAttestation(logging.Handler):
    """Observe levels after Odoo initializes logging; never read record payloads."""

    def __init__(self):
        super().__init__()
        self.saved = False

    def emit(self, record):
        if self.saved:
            return
        from s10_lc2_task_profile import MAIN_A_ENGINEERING, ROOT, profile_from_environment
        profile = profile_from_environment(os.environ)
        if profile is None or profile.message_id != MAIN_A_ENGINEERING:
            raise RuntimeError('NATIVE_PRIVACY_ATTESTATION_TASK_INVALID')
        run = Path(os.environ.get('YDENTAL_S10_RUN_DIR', ''))
        if run != profile.run_root / profile.database or run.is_symlink():
            raise RuntimeError('NATIVE_PRIVACY_ATTESTATION_RUN_INVALID')
        config = ROOT / 'config/logging-s10-main-a-engineering.example.json'
        directory = run / 'diagnostics'
        if directory.is_symlink() or not directory.is_dir() or config.is_symlink():
            raise RuntimeError('NATIVE_PRIVACY_ATTESTATION_PATH_INVALID')
        # record.name/message/args are deliberately never inspected or retained.
        value = {
            'kind': 'ACTUAL_OWNED_PROCESS_LOGGER_LEVEL', 'pid': os.getpid(),
            'task_message_id': profile.message_id,
            'logger': 'odoo.addons.base.models.res_device',
            'effective_level': logging.getLogger('odoo.addons.base.models.res_device').getEffectiveLevel(),
            'config_sha256': hashlib.sha256(config.read_bytes()).hexdigest(),
            'record_payload_retained': False,
        }
        raw = json.dumps(value, sort_keys=True).encode() + b'\n'
        path = directory / ('native-privacy-' + str(os.getpid()) + '.json')
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        if path.read_bytes() != raw:
            raise RuntimeError('NATIVE_PRIVACY_ATTESTATION_READBACK_INVALID')
        self.saved = True

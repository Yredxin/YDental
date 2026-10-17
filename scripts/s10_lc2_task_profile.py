"""Metadata for the separately authorized existing-scratch FRAMEWORK6 task."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import time


ROOT = Path(__file__).resolve().parents[1]
FRAMEWORK6 = 'YD-S10-LC2-FRAMEWORK6-20261017-01'
SCRATCH = 'ydental_s10_test_20261017105432_ce6dcbf8'
OLD_EPOCH = 1792238721.801
BASELINE = {'accident_ro': 2, 'create': 2, 'maintenance': 1,
            'odoo_start': 1, 'target_ro': 6, 'http': 0}
LOCAL_LIMITS = {'odoo_start': 3, 'target_ro': 8, 'http': 12}


@dataclass(frozen=True)
class TaskProfile:
    root: Path
    started_epoch: float
    deadline_epoch: float
    authority_sha256: str
    message_id: str = FRAMEWORK6

    @property
    def run_root(self):
        return self.root / 'targets'

    @property
    def data_dir(self):
        return ROOT / '.local/s10-lc2/20261017-lc2-exec01' / SCRATCH / 'data'

    def verify(self):
        if (self.root != ROOT / '.local/s10-lc2-framework6-20261017-01'
                or self.started_epoch != 1792250152.972942
                or self.deadline_epoch != self.started_epoch + 7200):
            raise RuntimeError('FRAMEWORK6_PROFILE_SCOPE_INVALID')
        raw = (self.root / 'scope.json').read_bytes()
        scope = json.loads(raw)
        if (self.message_id != FRAMEWORK6 or scope.get('message_id') != FRAMEWORK6
                or scope.get('scope') != 'EXISTING_SCRATCH_NATIVE_FRAMEWORK_ONLY'
                or scope.get('direct_user_authority') is not True
                or scope.get('parent_commit') != 'b99bb431315d201b4591e50785206779ac7fb524'
                or scope.get('started_epoch') != self.started_epoch
                or hashlib.sha256(raw).hexdigest() != self.authority_sha256
                or not self.started_epoch <= time.time() <= self.deadline_epoch):
            raise RuntimeError('FRAMEWORK6_AUTHORITY_OR_WINDOW_INVALID')

    def validate_ledger(self, value):
        self.verify()
        if (value.get('started_epoch') != OLD_EPOCH or value.get('task_message_id') != self.message_id
                or value.get('authority_message_id') != self.message_id
                or value.get('task_started_epoch') != self.started_epoch
                or value.get('authority_sha256') != self.authority_sha256
                or type(value.get('task_counts')) is not dict or type(value.get('counts')) is not dict
                or set(value['task_counts']) - set(LOCAL_LIMITS)):
            raise RuntimeError('FRAMEWORK6_BUDGET_IDENTITY_INVALID')
        for kind, maximum in LOCAL_LIMITS.items():
            count = value['task_counts'].get(kind, 0)
            if (type(count) is not int or not 0 <= count <= maximum
                    or value['counts'].get(kind, 0) != BASELINE[kind] + count):
                raise RuntimeError('FRAMEWORK6_BUDGET_CUMULATIVE_DRIFT')
        for kind in ('accident_ro', 'create', 'maintenance'):
            if value['counts'].get(kind) != BASELINE[kind]:
                raise RuntimeError('FRAMEWORK6_PROTECTED_RESOURCE_DRIFT')


def framework6_profile():
    root = ROOT / '.local/s10-lc2-framework6-20261017-01'
    raw = (root / 'scope.json').read_bytes()
    value = json.loads(raw)
    if (value.get('message_id') != FRAMEWORK6
            or value.get('scope') != 'EXISTING_SCRATCH_NATIVE_FRAMEWORK_ONLY'
            or value.get('direct_user_authority') is not True
            or value.get('parent_commit') != 'b99bb431315d201b4591e50785206779ac7fb524'
            or value.get('started_epoch') != 1792250152.972942):
        raise RuntimeError('FRAMEWORK6_AUTHORITY_SCOPE_INVALID')
    # Scope receipt is fixed; a new profile never edits the old epoch or STOP.
    profile = TaskProfile(root, value['started_epoch'], value['started_epoch'] + 7200,
                          hashlib.sha256(raw).hexdigest())
    profile.verify()
    return profile


def profile_from_environment(environment):
    selected = environment.get('YDENTAL_LC2_PROFILE')
    if selected is None:
        return None
    if selected != FRAMEWORK6:
        raise RuntimeError('UNKNOWN_LC2_TASK_PROFILE')
    return framework6_profile()

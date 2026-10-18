"""Fixed metadata for separately authorized, existing-target LC2 tasks."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import time


ROOT = Path(__file__).resolve().parents[1]
FRAMEWORK6 = 'YD-S10-LC2-FRAMEWORK6-20261017-01'
MAIN_A = 'YD-S10-LC2-MAIN-A-20261018-01'
MAIN_A_AUTONOMY = 'YD-S10-LC2-MAIN-A-20261018-02'
MAIN_A_ENGINEERING = 'YD-S10-LC2-MAIN-A-20261018-03'
MAIN_A_ORIGINAL_UI = 'YD-S10-LC2-MAIN-A-20261018-04'
CURRENT_PLAN = 'YD-S10-TECHNICAL-CLOSEOUT-V1'
CURRENT_ROOT = ROOT / '.local/s10-technical-closeout-v1'
MAIN_A_PROFILES = frozenset({MAIN_A, MAIN_A_AUTONOMY, MAIN_A_ENGINEERING, MAIN_A_ORIGINAL_UI})
MAIN_A_PRIVATE_LOG_PROFILES = frozenset({MAIN_A_ENGINEERING, MAIN_A_ORIGINAL_UI})
SCRATCH = 'ydental_s10_test_20261017105432_ce6dcbf8'
MAIN = 'ydental_s10_test_20261017105432_810a7d9c'
OLD_EPOCH = 1792238721.801
BASELINE = {'accident_ro': 2, 'create': 2, 'maintenance': 1,
            'odoo_start': 1, 'target_ro': 6, 'http': 0}
LOCAL_LIMITS = {'odoo_start': 3, 'target_ro': 8, 'http': 12}
MAIN_A_LIMITS = {'odoo_start': 3, 'target_ro': 8, 'http': 200,
                 'firefox': 1, 'original_get': 3}
MAIN_A_BASELINE = {'accident_ro': 2, 'create': 2, 'maintenance': 1,
                   'odoo_start': 2, 'target_ro': 9, 'http': 1,
                   'firefox': 0, 'original_get': 0}
MAIN_A_AUTONOMY_LIMITS = MAIN_A_LIMITS | {'odoo_start': 4}
MAIN_A_AUTONOMY_BASELINE = MAIN_A_BASELINE | {'target_ro': 11}
MAIN_A_ENGINEERING_LIMITS = MAIN_A_LIMITS | {'odoo_start': 4, 'target_ro': 12, 'firefox': 4}
MAIN_A_ENGINEERING_BASELINE = MAIN_A_BASELINE | {
    'odoo_start': 6, 'target_ro': 19, 'http': 5, 'firefox': 1}
MAIN_A_ORIGINAL_UI_LIMITS = MAIN_A_LIMITS | {'odoo_start': 2, 'firefox': 3}
MAIN_A_ORIGINAL_UI_BASELINE = MAIN_A_BASELINE | {
    'odoo_start': 8, 'target_ro': 25, 'http': 25, 'firefox': 5}
_SPECS = {
    FRAMEWORK6: ('s10-lc2-framework6-20261017-01', 1792250152.972942,
                 'EXISTING_SCRATCH_NATIVE_FRAMEWORK_ONLY',
                 'b99bb431315d201b4591e50785206779ac7fb524'),
    MAIN_A: ('s10-lc2-main-a-20261018-01', 1792277998.753601,
             'EXISTING_MAIN_DOCUMENT_AND_ORIGINAL_CLOSEOUT',
             '72ac77e0c73695fdfeb50326bbae1dcb27407e04'),
    MAIN_A_AUTONOMY: ('s10-lc2-main-a-20261018-02', 1792279870.0,
                      'EXISTING_MAIN_TEST_CREDENTIAL_SETUP_AND_A_CLOSEOUT',
                      '41e6c7c2b906653c9e264e4f402f5e572765bb98'),
    MAIN_A_ENGINEERING: ('s10-lc2-main-a-20261018-03', 1792281805.0,
                         'MAIN_A_TEST_ENGINEERING_AND_CLOSEOUT',
                         '4554545e99375dd9b6c0552b0611cd550a717808'),
    MAIN_A_ORIGINAL_UI: ('s10-lc2-main-a-20261018-04', 1792284787.0,
                        'MAIN_A_EXISTING_ORIGINAL_UI_ONLY',
                        '980eda60f011b1dec5fbf16ee8f10cc8e7cfa414'),
}


@dataclass(frozen=True)
class TaskProfile:
    root: Path
    started_epoch: float
    deadline_epoch: float
    authority_sha256: str
    message_id: str = FRAMEWORK6
    target_role: str = 'main'

    def current_scope(self):
        """Read the current plan receipt without changing any historical receipt."""
        if self.message_id != CURRENT_PLAN or self.root != CURRENT_ROOT:
            raise RuntimeError('CURRENT_PLAN_PROFILE_INVALID')
        raw = (self.root / 'scope.json').read_bytes()
        value = json.loads(raw)
        if (hashlib.sha256(raw).hexdigest() != self.authority_sha256
                or value.get('plan_id') != CURRENT_PLAN or value.get('version') != '1.0'
                or value.get('scope') != 'CURRENT_PLAN_EXISTING_MAIN'
                or value.get('identity') != {'database': MAIN, 'oid': 2144129,
                    'port': 18410, 'cluster': '7694897083368259627'}
                or value.get('direct_user_authority') is not True
                or not isinstance(value.get('execution_owner'), str) or not value['execution_owner']
                or value.get('started_epoch') != self.started_epoch
                or value.get('deadline_epoch') != self.deadline_epoch
                or not self.started_epoch <= time.time() <= self.deadline_epoch
                or not 0 < self.deadline_epoch - self.started_epoch <= 86400):
            raise RuntimeError('CURRENT_PLAN_SCOPE_OR_WINDOW_INVALID')
        if self.target_role not in {'main', 'scratch'}:
            raise RuntimeError('CURRENT_PLAN_TARGET_ROLE_INVALID')
        if self.target_role == 'scratch' and value.get('targets', {}).get('scratch') != {
                'database': SCRATCH, 'oid': 2144130, 'port': 18411, 'cluster': '7694897083368259627'}:
            raise RuntimeError('CURRENT_PLAN_SCRATCH_TARGET_NOT_REVIEWED')
        baseline, limits = value.get('baseline'), value.get('limits')
        protected = {'accident_ro', 'create', 'maintenance'}
        permitted = {'odoo_start', 'target_ro', 'http', 'firefox', 'original_get'}
        if (type(baseline) is not dict or set(baseline) != protected | permitted
                or any(type(n) is not int or n < 0 for n in baseline.values())
                or type(limits) is not dict or set(limits) != permitted
                or any(type(n) is not int or n <= 0 for n in limits.values())):
            raise RuntimeError('CURRENT_PLAN_RESOURCE_SCOPE_INVALID')
        def historical(item):
            if type(item) is not dict or set(item) != {'ref', 'sha256'}:
                raise RuntimeError('CURRENT_PLAN_HISTORY_REFERENCE_INVALID')
            path = ROOT / item['ref']
            if (not str(item['ref']).startswith('.local/') or '..' in Path(item['ref']).parts
                    or path.is_symlink() or not path.resolve().is_relative_to(ROOT / '.local')):
                raise RuntimeError('CURRENT_PLAN_HISTORY_PATH_INVALID')
            content = path.read_bytes()
            if hashlib.sha256(content).hexdigest() != item['sha256']:
                raise RuntimeError('CURRENT_PLAN_HISTORY_BYTES_CHANGED')
            return json.loads(content)
        ledgers = value.get('history_ledgers')
        if type(ledgers) is not list or not ledgers:
            raise RuntimeError('CURRENT_PLAN_HISTORY_LEDGER_REQUIRED')
        prior = [historical(item)['counts'] for item in ledgers]
        if baseline != {kind: max(row.get(kind, 0) for row in prior) for kind in baseline}:
            raise RuntimeError('CURRENT_PLAN_HISTORICAL_COUNTS_DRIFT')
        if historical(value.get('history_stop')).get('reason') != 'TOOL_SAFETY_REFUSAL':
            raise RuntimeError('CURRENT_PLAN_HISTORICAL_REFUSAL_REQUIRED')
        reviews = value.get('action_reviews')
        if type(reviews) is not dict or not reviews:
            raise RuntimeError('CURRENT_PLAN_ACTION_REVIEW_REQUIRED')
        for review in reviews.values():
            if (type(review) is not dict or review.get('current_refusal_stops') is not True
                    or any(not isinstance(review.get(key), str) or not review[key].strip()
                           for key in ('purpose', 'historical_refusal_boundary'))):
                raise RuntimeError('CURRENT_PLAN_ACTION_REVIEW_INVALID')
        return value

    def require_action(self, action):
        if self.message_id == CURRENT_PLAN and action not in self.current_scope()['action_reviews']:
            raise RuntimeError('CURRENT_PLAN_ACTION_NOT_REVIEWED')
        self.verify()

    @property
    def run_root(self):
        return self.root / 'targets'

    @property
    def data_dir(self):
        return ROOT / '.local/s10-lc2/20261017-lc2-exec01' / self.database / 'data'

    @property
    def database(self):
        if self.message_id == CURRENT_PLAN:
            return MAIN if self.target_role == 'main' else SCRATCH
        return MAIN if self.message_id in MAIN_A_PROFILES else SCRATCH

    @property
    def local_limits(self):
        if self.message_id == CURRENT_PLAN:
            return dict(self.current_scope()['limits'])
        if self.message_id == MAIN_A_ORIGINAL_UI:
            return dict(MAIN_A_ORIGINAL_UI_LIMITS)
        if self.message_id == MAIN_A_ENGINEERING:
            return dict(MAIN_A_ENGINEERING_LIMITS)
        if self.message_id == MAIN_A_AUTONOMY:
            return dict(MAIN_A_AUTONOMY_LIMITS)
        return dict(MAIN_A_LIMITS if self.message_id == MAIN_A else LOCAL_LIMITS)

    @property
    def baseline(self):
        if self.message_id == CURRENT_PLAN:
            return dict(self.current_scope()['baseline'])
        if self.message_id == MAIN_A_ORIGINAL_UI:
            return dict(MAIN_A_ORIGINAL_UI_BASELINE)
        if self.message_id == MAIN_A_ENGINEERING:
            return dict(MAIN_A_ENGINEERING_BASELINE)
        if self.message_id == MAIN_A_AUTONOMY:
            return dict(MAIN_A_AUTONOMY_BASELINE)
        return dict(MAIN_A_BASELINE if self.message_id == MAIN_A else BASELINE)

    @property
    def allowed_actions(self):
        if self.message_id == CURRENT_PLAN:
            return set(self.current_scope()['action_reviews']) & {
                self.target_role + suffix for suffix in ('-service', '-fixture', '-upgrade')}
        if self.message_id == MAIN_A_AUTONOMY:
            return {'main-service', 'main-credential-setup'}
        return {'main-service'} if self.message_id in MAIN_A_PROFILES else {'scratch-tests'}

    @property
    def run_id(self):
        if self.message_id == CURRENT_PLAN:
            return 's10-technical-closeout-v1'
        return _SPECS[self.message_id][0].removeprefix('s10-')

    def validate_target(self, database, oid, port=None):
        self.verify()
        main = self.message_id in MAIN_A_PROFILES or self.message_id == CURRENT_PLAN and self.target_role == 'main'
        expected = (MAIN, 2144129, 18410) if main else (SCRATCH, 2144130, 18411)
        if (database, oid) != expected[:2] or port is not None and port != expected[2]:
            raise RuntimeError('LC2_TASK_TARGET_SCOPE_INVALID')

    def verify(self):
        if self.message_id == CURRENT_PLAN:
            self.current_scope()
            return
        if self.message_id not in _SPECS:
            raise RuntimeError('UNKNOWN_LC2_TASK_PROFILE')
        root_name, started, authorized_scope, parent = _SPECS[self.message_id]
        if (self.root != ROOT / '.local' / root_name
                or self.started_epoch != started
                or self.deadline_epoch != self.started_epoch + (14400 if self.message_id in {MAIN_A_AUTONOMY, MAIN_A_ENGINEERING, MAIN_A_ORIGINAL_UI} else 7200)):
            raise RuntimeError('FRAMEWORK6_PROFILE_SCOPE_INVALID')
        raw = (self.root / 'scope.json').read_bytes()
        scope = json.loads(raw)
        if (scope.get('message_id') != self.message_id
                or scope.get('scope') != authorized_scope
                or scope.get('direct_user_authority') is not True
                or scope.get('parent_commit') != parent
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
                or set(value['task_counts']) - set(self.local_limits)):
            raise RuntimeError('FRAMEWORK6_BUDGET_IDENTITY_INVALID')
        if self.message_id in MAIN_A_PRIVATE_LOG_PROFILES:
            kinds = value.get('task_firefox_counts')
            if (type(kinds) is not dict or set(kinds) != {'diagnostic', 'ui'}
                    or any(type(n) is not int or not 0 <= n <= (3 if self.message_id == MAIN_A_ORIGINAL_UI else 2) for n in kinds.values())
                    or self.message_id == MAIN_A_ORIGINAL_UI and kinds['diagnostic'] != 0
                    or sum(kinds.values()) != value['task_counts'].get('firefox', 0)):
                raise RuntimeError('MAIN_A_FIREFOX_PURPOSE_LEDGER_INVALID')
        for kind, maximum in self.local_limits.items():
            count = value['task_counts'].get(kind, 0)
            if (type(count) is not int or not 0 <= count <= maximum
                    or value['counts'].get(kind, 0) != self.baseline[kind] + count):
                raise RuntimeError('FRAMEWORK6_BUDGET_CUMULATIVE_DRIFT')
        for kind in set(self.baseline) - set(self.local_limits):
            if value['counts'].get(kind) != self.baseline[kind]:
                raise RuntimeError('FRAMEWORK6_PROTECTED_RESOURCE_DRIFT')
        if (self.message_id in MAIN_A_PROFILES or self.message_id == CURRENT_PLAN) and set(value['counts']) != set(self.baseline):
            raise RuntimeError('MAIN_A_CUMULATIVE_RESOURCE_SET_DRIFT')


def framework6_profile():
    return _profile(FRAMEWORK6)


def current_plan_profile(target_role='main'):
    return _profile(CURRENT_PLAN, target_role=target_role)


def main_a_profile():
    return _profile(MAIN_A)


def main_a_autonomy_profile():
    return _profile(MAIN_A_AUTONOMY)


def main_a_engineering_profile():
    return _profile(MAIN_A_ENGINEERING)


def main_a_original_ui_profile():
    return _profile(MAIN_A_ORIGINAL_UI)


def _profile(message_id, *, target_role='main'):
    if message_id == CURRENT_PLAN:
        raw = (CURRENT_ROOT / 'scope.json').read_bytes()
        value = json.loads(raw)
        profile = TaskProfile(CURRENT_ROOT, value['started_epoch'], value['deadline_epoch'],
                              hashlib.sha256(raw).hexdigest(), CURRENT_PLAN, target_role)
        profile.verify()
        return profile
    root_name, started, authorized_scope, parent = _SPECS[message_id]
    root = ROOT / '.local' / root_name
    raw = (root / 'scope.json').read_bytes()
    value = json.loads(raw)
    if (value.get('message_id') != message_id
            or value.get('scope') != authorized_scope
            or value.get('direct_user_authority') is not True
            or value.get('parent_commit') != parent
            or value.get('started_epoch') != started):
        raise RuntimeError('FRAMEWORK6_AUTHORITY_SCOPE_INVALID')
    # Scope receipt is fixed; a new profile never edits the old epoch or STOP.
    duration = 14400 if message_id in {MAIN_A_AUTONOMY, MAIN_A_ENGINEERING, MAIN_A_ORIGINAL_UI} else 7200
    if (message_id in {MAIN_A_AUTONOMY, MAIN_A_ENGINEERING, MAIN_A_ORIGINAL_UI}
            and value.get('deadline_epoch') != started + duration):
        raise RuntimeError('MAIN_A_AUTONOMY_DEADLINE_DRIFT')
    profile = TaskProfile(root, value['started_epoch'], value['started_epoch'] + duration,
                          hashlib.sha256(raw).hexdigest(), message_id)
    profile.verify()
    return profile


def profile_from_environment(environment):
    selected = environment.get('YDENTAL_LC2_PROFILE')
    if selected is None:
        return None
    if selected not in _SPECS and selected != CURRENT_PLAN:
        raise RuntimeError('UNKNOWN_LC2_TASK_PROFILE')
    return _profile(selected, target_role=environment.get('YDENTAL_LC2_TARGET_ROLE', 'main'))

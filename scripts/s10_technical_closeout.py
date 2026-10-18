"""Current-plan existing-target RO and normal stored-original UI entrypoints.

Receipts and ownership are supplied by the coordinator, never generated here.
This entrypoint does not activate the historical closeout execution package.
"""
import argparse
import asyncio
import fcntl
import json
import os
from pathlib import Path
import uuid

from s10_lc2_evidence import collect_selection, runtime_gate, save_once
from s10_lc2_launch import OwnedApplication
from s10_lc2_logging import strict_loads
from s10_lc2_targets import PackageBudget, credentials, require_dispatch_unfrozen
from s10_lc2_task_profile import ROOT, current_plan_profile


def run_original(profile, approval, authority):
    from s10_lc2_browser import _DRIVER_ENV_KEYS
    from s10_lc2_main_a_original_runner import already_downloaded, original_ui
    profile.require_action('A-ORIGINAL')
    if already_downloaded(profile.root):
        raise RuntimeError('DOWNLOAD_ALREADY_SAVED_POSTPROCESS_ONLY_NO_RECLICK')
    before = strict_loads((profile.root / 'original-before.json').read_bytes())
    if before.get('original_reader5_eligible') is not True or before.get('editor_released') is not True:
        raise RuntimeError('ORIGINAL_BEFORE_PRECONDITION_INVALID')
    marker = strict_loads((profile.run_root / profile.database / 'database.json').read_bytes())
    attempt = uuid.uuid4().hex[:8]
    try:
        with OwnedApplication(marker, approval=approval,
                product_commit=authority['product_commit'], test_commit=authority['test_commit'],
                action='main-service', profile=profile) as app:
            app.start([])
            app.wait_ready(60)
            ambient = dict(os.environ)
            try:
                os.environ.clear()
                os.environ.update({key: value for key, value in ambient.items() if key in _DRIVER_ENV_KEYS})
                result = asyncio.run(original_ui(app.budget, profile.root / ('browser-ui-' + attempt)))
                save_once(profile.root / ('original-ui-' + attempt + '-result.json'), result)
            finally:
                os.environ.clear()
                os.environ.update(ambient)
            app.check()
        result = {'status': 'DOWNLOAD_RETURNED_INDEPENDENT_RO_AND_PDF_REVIEW_PENDING',
                  'application_directory': str(app.directory.relative_to(ROOT)),
                  'credential_actor': 5, 'clinical_operations': 0}
        save_once(profile.root / ('original-run-' + attempt + '-result.json'), result)
        return result
    except BaseException as error:
        save_once(profile.root / ('original-run-' + attempt + '-failure.json'), {
            'exception_type': type(error).__name__, 'raw_error_text_retained': False,
            'download_artifact_already_saved': already_downloaded(profile.root),
            'clinical_operations': 0, 'next_action': 'INSPECT_SAVED_EVIDENCE_BEFORE_RETRY'})
        raise


def execute(args, profile):
    """Caller holds the plan's exclusive runner lock for this whole operation."""
    require_dispatch_unfrozen(profile)
    approval = profile.root / 'runtime-approval.json'
    authority = strict_loads(approval.read_bytes())
    runtime_gate(approval, product_commit=authority['product_commit'],
                 test_commit=authority['test_commit'], profile=profile)
    save_once(profile.root / ('runner-owner-' + uuid.uuid4().hex[:12] + '.json'), {
        'execution_owner': profile.current_scope()['execution_owner'], 'pid': os.getpid(),
        'uid': os.getuid(), 'ppid': os.getppid(), 'action': args.action,
        'test_commit': authority['test_commit'], 'exclusive_runner_lock_held': True})
    if args.action == 'target-ro':
        profile.require_action('target-ro')
        import psycopg2
        directory = profile.root / ('capture-main-' + uuid.uuid4().hex[:12])
        run = profile.run_root / profile.database
        collect_selection(psycopg2.connect, credentials(), database=profile.database,
            expected_oid=2144129, selections=strict_loads(args.selections.read_bytes()),
            directory=directory, budget=PackageBudget(profile.root, profile=profile),
            allowed_target_names=[profile.database], target_directory=run,
            config_path=run / 'odoo.conf')
        return {'status': 'RO_CAPTURED_NOT_YET_INDEPENDENTLY_REVIEWED',
                'directory': str(directory.relative_to(ROOT))}
    return run_original(profile, approval, authority)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['target-ro', 'original-ui'])
    parser.add_argument('--selections', type=Path)
    args = parser.parse_args()
    if args.action == 'target-ro' and args.selections is None:
        parser.error('--selections is required for target-ro')
    profile = current_plan_profile()
    descriptor = os.open(profile.root / 'runner.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'a+b') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError('CURRENT_PLAN_OTHER_RUNNER_OWNS_TARGET') from None
        result = execute(args, profile)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()

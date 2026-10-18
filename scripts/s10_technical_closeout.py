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
import stat
import uuid

from s10_lc2_evidence import collect_selection, runtime_gate, save_once
from s10_lc2_launch import OwnedApplication
from s10_lc2_logging import strict_loads
from s10_lc2_targets import PackageBudget, credentials, require_dispatch_unfrozen
from s10_lc2_task_profile import ROOT, current_plan_profile


def prepare_reader(profile, approval, authority):
    from s10_lc2_cases import run_fixture
    profile.require_action('main-reader-prepare')
    intent = profile.root / 'reader-prepare-intent.json'
    if intent.exists():
        raise RuntimeError('READER_PREPARATION_ALREADY_ATTEMPTED_VERIFY_COMMIT_FIRST')
    save_once(intent, {'operation': 'main-reader-only', 'manager_id': 5, 'store_id': 1,
                      'economic_operations': 0, 'commit_observation': 'NOT_OBSERVED'})
    directory = profile.root / 'credentials'
    directory.mkdir(mode=0o700, exist_ok=True)
    if (directory.is_symlink() or directory.stat().st_uid != os.getuid()
            or stat.S_IMODE(directory.stat().st_mode) != 0o700):
        raise RuntimeError('CURRENT_READER_PROVIDER_DIRECTORY_INVALID')
    result = run_fixture('main', approval=approval, product_commit=authority['product_commit'],
        test_commit=authority['test_commit'], mode='main-reader-only', profile=profile)
    reader = result['ram'].pop('reader')
    path = directory / ('user-%d.json' % reader['user_id'])
    if strict_loads(path.read_bytes()) != {key: reader[key] for key in ('user_id', 'login', 'password')}:
        raise RuntimeError('CURRENT_READER_PRECOMMIT_PROVIDER_MISMATCH')
    reference = {'ref': str(path.relative_to(ROOT)), 'actor_id': reader['user_id']}
    save_once(profile.root / 'reader-provider.json', reference)
    save_once(profile.root / 'reader-prepare-result.json', result['safe'])
    return result['safe'] | {'provider_reference': reference,
        'status': 'ROLE_COMMIT_RETURNED_INDEPENDENT_RO_REQUIRED'}


def current_reader(profile):
    reference = strict_loads((profile.root / 'reader-provider.json').read_bytes())
    path = ROOT / reference['ref']
    directory = profile.root / 'credentials'
    if (path.parent != directory or directory.is_symlink()
            or directory.stat().st_uid != os.getuid() or stat.S_IMODE(directory.stat().st_mode) != 0o700
            or path.is_symlink()
            or path.stat().st_uid != os.getuid() or stat.S_IMODE(path.stat().st_mode) != 0o600):
        raise RuntimeError('CURRENT_READER_PROVIDER_INVALID')
    reader = strict_loads(path.read_bytes())
    if (set(reader) != {'user_id', 'login', 'password'} or reader['user_id'] != reference['actor_id']
            or reader['user_id'] <= 1 or reader['user_id'] in {5, 7}):
        raise RuntimeError('CURRENT_READER_IDENTITY_INVALID')
    return reference, reader


def run_b(profile, approval, authority, requested_path):
    """Normal-session manifest, rollback MODEL probes, then six real RPC probes."""
    from s10_lc2_cases import (Actor, Facts, b_collect_step, b_evidence_callbacks,
        b_selections, manifest_from_b_source, marker, run_b_only, run_fixture)
    from s10_lc2_evidence import CORE, collect_b_source
    import psycopg2
    profile.require_action('B-MODEL-6')
    profile.require_action('B-RPC-6')
    if (profile.root / 'B-ACTION-STOP.json').exists():
        raise RuntimeError('B_PRIOR_OUTCOME_OR_PRESERVATION_REQUIRES_INDEPENDENT_REVIEW')
    reference, reader = current_reader(profile)
    requested = strict_loads(requested_path.read_bytes())
    if requested.get('uid') != reader['user_id'] or requested.get('store_id') != 1:
        raise RuntimeError('B_CURRENT_READER_SCOPE_MISMATCH')
    b_selections(requested)
    directory = profile.root / ('B-' + uuid.uuid4().hex[:12])
    facts = Facts(directory)
    run = profile.run_root / profile.database
    binding = {'run_id': profile.run_id, 'task_id': 'S10-LOG-AND-CLOSEOUT-v2',
        'product_commit': authority['product_commit'], 'test_commit': authority['test_commit'],
        'core_commit': CORE, 'identity': {'database': profile.database, 'oid': 2144129,
            'cluster': '7694897083368259627'}}
    budget = PackageBudget(profile.root, profile=profile)
    database_args = credentials()
    def application():
        return OwnedApplication(marker('main', profile), approval=approval,
            product_commit=authority['product_commit'], test_commit=authority['test_commit'],
            action='main-service', profile=profile)
    with application() as preparation:
        preparation.start([])
        preparation.wait_ready(60)
        actor = Actor('main', 'current-B-reader', reader['user_id'], reader['login'], reader['password'],
            budget=budget, directory=directory / 'http')
        actor.login(1)
        info = actor.session_metadata(binding=binding)
        probe_directory = directory / 'write-probe-values'
        collect_selection(psycopg2.connect, database_args, database=profile.database,
            expected_oid=2144129, selections=[{'table': table, 'columns': ['id', field], 'ids': [requested[key]]}
                for table, field, key in (
                    ('ydental_settlement_source', 'ydental_original_amount', 'source_id'),
                    ('ydental_settlement_payment', 'ydental_amount', 'payment_id'),
                    ('ydental_access_audit', 'ydental_reason', 'audit_id'))],
            directory=probe_directory, budget=budget, allowed_target_names=[profile.database],
            target_directory=run, config_path=run / 'odoo.conf', max_rows=3)
        from s10_lc2_cases import stored_rows
        probes = {}
        for table, field, expected in (
                ('ydental_settlement_source', 'ydental_original_amount', 1),
                ('ydental_settlement_payment', 'ydental_amount', 1),
                ('ydental_access_audit', 'ydental_reason', 'LC2 denied tampering')):
            rows = stored_rows(probe_directory, table)
            probes[table] = len(rows) == 1 and rows[0][field] != expected
        facts.save('write-probe-values', {'nonempty_and_distinct': probes,
                   'source': str(probe_directory.relative_to(ROOT)), 'actual_values_retained': False})
        if not all(probes.values()):
            raise RuntimeError('B_WRITE_PROBE_MISSING_TARGET_OR_NO_CHANGE')
        manifest_ref = collect_b_source(psycopg2.connect, database_args, binding=binding,
            point='manifest', check_id='B-manifest', phase='B-pre', selections=b_selections(requested),
            directory=directory / 'manifest-source', budget=budget,
            target_directory=run, config_path=run / 'odoo.conf')
        manifest = manifest_from_b_source(manifest_ref, binding=binding, session_info=info,
            provider_ref=reference, requested=requested)
        facts.save('manifest', manifest)
    del reader
    collect = b_collect_step(binding=binding, connect=psycopg2.connect, connection_args=database_args,
        directory=directory / 'observations', budget=budget, target_directory=run,
        config_path=run / 'odoo.conf')
    live, callbacks = None, None
    def log_source(app):
        return {'app_directory': app.directory, 'target_directory': run, 'pid': app.process.pid}
    def model_probe(current_manifest):
        def factory(app):
            return b_evidence_callbacks(binding=binding, manifest=current_manifest, requested=requested,
                manifest_reference=manifest_ref, session_info=info, collect_step=collect,
                log_source=lambda: log_source(app), close_owned_service=lambda: None, phase='B-model')
        result = run_fixture('main', approval=approval, product_commit=authority['product_commit'],
            test_commit=authority['test_commit'], mode='main-b-only', manifest=current_manifest,
            provider_ref=reference, evidence_factory=factory, profile=profile)
        return result['safe']['model_checks']
    def close_live():
        nonlocal live
        if live is not None:
            current, live = live, None
            current.close()
    def actor_factory(provider_ref, current_manifest):
        nonlocal live, callbacks
        live = application()
        live.start([])
        live.wait_ready(60)
        actor.refresh()
        app = live
        callbacks = b_evidence_callbacks(binding=binding, manifest=current_manifest, requested=requested,
            manifest_reference=manifest_ref, session_info=lambda: actor.session_metadata(binding=binding),
            collect_step=collect, log_source=lambda: log_source(app), close_owned_service=close_live)
        return actor
    try:
        result = run_b_only(manifest=manifest, provider_ref=reference, approval=approval,
            product_commit=authority['product_commit'], test_commit=authority['test_commit'], facts=facts,
            model_probe=model_probe, actor_factory=actor_factory,
            observe=lambda *args: callbacks['observe'](*args),
            server_events=lambda *args: callbacks['server_events'](*args),
            terminal=lambda *args: callbacks['terminal'](*args), profile=profile)
        facts.save('result', result)
        rpc = result.get('rpc')
        if isinstance(rpc, dict) and any(
                row.get('dispatch_state') == 'UNKNOWN'
                or row.get('result_present') is True
                or row.get('dispatch_state') == 'RESPONSE_RECEIVED' and row.get('preservation') != 'VERIFIED'
                for row in rpc.get('checks', [])):
            save_once(profile.root / 'B-ACTION-STOP.json', {
                'reason': 'B_OUTCOME_OR_PRESERVATION_UNCONFIRMED', 'target': profile.database,
                'result_reference': str((directory / 'result.json').relative_to(ROOT)),
                'independent_read_only_investigation_required': True, 'automatic_retry': False})
        return {'status': result['status'], 'layer': 'MODEL_AND_HTTP_RPC',
                'directory': str(directory.relative_to(ROOT))}
    finally:
        close_live()


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
    if args.action == 'prepare-reader':
        return prepare_reader(profile, approval, authority)
    if args.action == 'b-only':
        return run_b(profile, approval, authority, args.requested)
    return run_original(profile, approval, authority)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['target-ro', 'original-ui', 'prepare-reader', 'b-only'])
    parser.add_argument('--selections', type=Path)
    parser.add_argument('--requested', type=Path)
    args = parser.parse_args()
    if args.action == 'target-ro' and args.selections is None:
        parser.error('--selections is required for target-ro')
    if args.action == 'b-only' and args.requested is None:
        parser.error('--requested is required for b-only')
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

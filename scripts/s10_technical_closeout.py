"""Current-plan existing-target RO and normal stored-original UI entrypoints.

Receipts and ownership are supplied by the coordinator, never generated here.
This entrypoint does not activate the historical closeout execution package.
"""
import argparse
import asyncio
import fcntl
import hashlib
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
        recovery = strict_loads((profile.root / 'reader-prepare-recovery.json').read_bytes())
        def recovered_reference(name):
            path = ROOT / recovery[name + '_ref']
            if path.is_symlink() or not path.resolve().is_relative_to(profile.root):
                raise RuntimeError('READER_STARTUP_RECOVERY_REFERENCE_INVALID')
            raw = path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != recovery[name + '_sha256']:
                raise RuntimeError('READER_STARTUP_RECOVERY_BYTES_CHANGED')
            return raw
        stop_raw = recovered_reference('archived_stop')
        ro = strict_loads(recovered_reference('zero_commit_ro'))
        terminal_raw = (profile.root / 'original-terminal.json').read_bytes()
        if hashlib.sha256(terminal_raw).hexdigest() != '9b119b859757c9a7f28efe84283237e0a52c83125be7a9458f52d972de0487b8':
            raise RuntimeError('READER_STARTUP_RECOVERY_A_TERMINAL_CHANGED')
        terminal = strict_loads(terminal_raw)
        parent = recovered_reference('parent_exit').decode('ascii').splitlines()
        if (recovery.get('reason') != 'STARTUP_OBSERVER_RACE_ZERO_ROLE_COMMIT'
                or recovery.get('attempt') != 2 or recovery.get('independent_reviewer') != '/root/acceptance_s10'
                or recovery.get('original_intent_sha256') != hashlib.sha256(intent.read_bytes()).hexdigest()
                or recovery.get('original_intent_sha256') != 'b8423aa53b846457c2e9646a007825a047ce8dfc20b2a18def56adfddc7f6b4e'
                or len(stop_raw) != 148 or hashlib.sha256(stop_raw).hexdigest() != 'd975cab019ec817aea70e735c797b6b0cd08bf9336e52e889bf093b87736689a'
                or strict_loads(stop_raw).get('reason') != 'DIAGNOSTIC_LOG_MISSING'
                or recovery.get('zero_commit_ro_sha256') != '54351c4bcbc7012f742fac194f0f2cde69e550dfbf77f7a70604057f2eb3c0e1'
                or recovery.get('zero_commit_ro_exit_code') != 0
                or not str(recovery.get('zero_commit_ro_candidate', '')).startswith('37e417c')
                or not any(row.split('\t')[0:1] == ['parent.end'] and row.split('\t')[2:5] == ['1785486', '-15', '15'] for row in parent)
                or any(ro.get(key) is not True for key in ('no_new_reader_observed', 'known_historical_audits_unchanged',
                    'zero_business_changes_asserted', 'rollback_returned', 'connection_closed'))
                or any(ro.get(key) != [] for key in ('possible_new_reader_rows', 'protected_domain_changes',
                    'new_native_devices', 'new_native_user_logins'))
                or any(ro.get(key) != terminal.get(key) for key in ('new_audits', 'audit_checkpoint'))
                or (profile.root / 'reader-provider.json').exists()
                or any((profile.root / 'credentials').glob('*.json'))):
            raise RuntimeError('READER_STARTUP_RECOVERY_NOT_VERIFIED_ZERO_COMMIT')
        save_once(profile.root / 'reader-prepare-attempt2-intent.json', {
            'attempt': 2, 'original_intent_sha256': recovery['original_intent_sha256'],
            'zero_commit_ro_sha256': recovery['zero_commit_ro_sha256'], 'automatic_retry': False})
    else:
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


def initialize_existing_reader(profile, approval, authority):
    """Initialize only the committed, independently verified pending reader 59."""
    from s10_lc2_cases import run_fixture
    profile.require_action('initialize-existing-reader')
    save_once(profile.root / 'reader-initialize-existing-intent.json', {
        'user_id': 59, 'operation': 'main-reader-password-only',
        'account_creation': False, 'native_admin_id': 2, 'automatic_retry': False})
    result = run_fixture('main', approval=approval, product_commit=authority['product_commit'],
        test_commit=authority['test_commit'], mode='main-reader-password-only', profile=profile)
    save_once(profile.root / 'reader-initialize-existing-result.json', result['safe'])
    reference = {'ref': str((profile.root / 'credentials/user-59.json').relative_to(ROOT)), 'actor_id': 59}
    save_once(profile.root / 'reader-provider.json', reference)
    return result['safe'] | {'status': 'EXISTING_READER_PASSWORD_COMMIT_RETURNED_RO_REQUIRED',
                             'provider_reference': reference}


def c_renderer_resolution(profile):
    """Consume only the independently classified current C renderer incident."""
    receipt = strict_loads((profile.root / 'C-renderer-resolution.json').read_bytes())
    def reference(name):
        path = ROOT / receipt[name + '_ref']
        if path.is_symlink() or not path.resolve().is_relative_to(profile.root) or path.stat().st_uid != os.getuid():
            raise RuntimeError('C_RENDERER_RESOLUTION_REFERENCE_INVALID')
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != receipt[name + '_sha256']:
            raise RuntimeError('C_RENDERER_RESOLUTION_REFERENCE_CHANGED')
        return strict_loads(raw)
    original = reference('original_stop')
    observed = reference('only_ro_verified')
    reference('failure_index')
    reference('original_runtime_snapshot')
    if (receipt.get('reason') != 'C_RENDERER_EXIT_ONE_NORMAL_PRODUCT_CONFIG_REPAIR'
            or receipt.get('original_stop_sha256') != 'c32c0944ec6eb0fa543082d6ecfb928d1cc33bf943c54d47ebf0afc06619eae6'
            or receipt.get('only_ro_verified_sha256') != 'a37901af09a55be018c760cf02471ecff318d29ecc18eab9ddc3dc47b9409ffb'
            or original.get('reason') != 'RENDERER_NONZERO_REQUIRES_VERIFICATION'
            or original.get('pid') != 1829480 or original.get('primary_event_id') != '6208b49b9433427bb9ca2d4020f7c775'
            or receipt.get('only_ro_exit_code') != 0 or receipt.get('independent_reviewer') != '/root/acceptance_s10'
            or receipt.get('allowed_resolution_actions') != ['report-parameters-only', 'repair-upgrade-main-font', 'c-main-tail']
            or any(receipt.get(key) is not True for key in ('no_native_crash', 'no_tool_refusal', 'old_r12_retained'))
            or any(observed.get(key) is not True for key in ('rollback_returned', 'connection_closed', 'ordinary59_retained'))
            or observed.get('other_connections') != []
            or observed.get('identity', {}).get('database') != profile.database
            or observed.get('identity', {}).get('oid') != 2144129):
        raise RuntimeError('C_RENDERER_ORDINARY_REPAIR_NOT_INDEPENDENTLY_RESOLVED')
    return receipt, observed


def repair_report_parameters(profile, approval, authority):
    from s10_lc2_cases import run_fixture
    profile.require_action('report-parameters-only')
    receipt, observed = c_renderer_resolution(profile)
    save_once(profile.root / 'REPORT-PARAMETERS-IN-FLIGHT.json', {
        'native_admin_id': 2, 'keys': ['report.url', 'web.base.url', 'web.base.url.freeze'],
        'observed_sha256': receipt['only_ro_verified_sha256'], 'automatic_retry': False,
        'economic_operations': 0})
    result = run_fixture('main', approval=approval, product_commit=authority['product_commit'],
        test_commit=authority['test_commit'], mode='main-report-parameters-only', profile=profile,
        manifest={'report_config_safe_components': observed['report_config_safe_components'],
                  'source_sha256': receipt['only_ro_verified_sha256']})
    save_once(profile.root / 'REPORT-PARAMETERS-RESULT.json', result['safe'])
    return result['safe'] | {'status': 'NATIVE_REPORT_PARAMETERS_COMMIT_RETURNED_POST_RO_REQUIRED'}


def b_zero_dispatch_recovery(profile):
    """Only the preserved first prelaunch bind failure can enter one new attempt."""
    root = profile.root
    receipt = strict_loads((root / 'B-zero-dispatch-recovery.json').read_bytes())
    def referenced(name):
        path = ROOT / receipt[name + '_ref']
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise RuntimeError('B_ZERO_DISPATCH_REFERENCE_INVALID')
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != receipt[name + '_sha256']:
            raise RuntimeError('B_ZERO_DISPATCH_REFERENCE_BYTES_CHANGED')
        return strict_loads(raw)
    latch_sha = hashlib.sha256((root / 'B-ACTION-IN-FLIGHT.json').read_bytes()).hexdigest()
    failure = referenced('failure_index')
    observation = referenced('zero_dispatch_ro')
    baseline_raw = (root / 'reader-password-verified.json').read_bytes()
    if hashlib.sha256(baseline_raw).hexdigest() != 'c29b8f2e81d5116e7094190819728e6f9944d7e6a2e7eeb9a099e729e7b4f3e6':
        raise RuntimeError('B_ZERO_DISPATCH_PASSWORD_BASELINE_CHANGED')
    baseline = strict_loads(baseline_raw)
    failed_app = root / 'application-main-fixture-55c98bb3'
    prep_exit = root / 'application-main-service-b47973a0/parent-exit.tsv'
    for relative, digest in failure.get('material_refs', {}).items():
        path = root / relative
        if not path.resolve().is_relative_to(root) or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise RuntimeError('B_ZERO_DISPATCH_ORIGINAL_FAILURE_BYTES_CHANGED')
    partial = strict_loads((failed_app / 'b-parent-failure.json').read_bytes())
    exits = [row.split('\t') for row in prep_exit.read_text().splitlines()]
    fixture_exits = [row.split('\t') for row in (failed_app / 'parent-exit.tsv').read_text().splitlines()]
    audit_delta = observation.get('new_fixture_audits', [])
    prior_audits = baseline.get('audits_since_a_before', [])
    if (receipt.get('reason') != 'FIXED_PORT_PRELAUNCH_EADDRINUSE_ZERO_B_DISPATCH'
            or receipt.get('attempt') != 2 or receipt.get('independent_reviewer') != '/root/acceptance_s10'
            or receipt.get('original_latch_sha256') != latch_sha
            or latch_sha != '1d73aea894c3b3b599c69e9589878520ee86e8b821bc175486cd54edb13e527d'
            or receipt.get('failure_index_sha256') != '1813b62f55a81dee9ad47ec1d796b945d77c0a70256efa4e249efa8a48c936b3'
            or failure.get('first_failure_errno') != 98 or failure.get('first_failure_type') != 'OSError'
            or any(failure.get(key) != 0 for key in ('B_model_checks_dispatched', 'B_rpc_checks_dispatched'))
            or not any(row[0] == 'parent.end' and row[2:4] == ['1801097', '0'] for row in exits)
            or len(fixture_exits) != 1 or fixture_exits[0][0] != 'parent.end'
            or fixture_exits[0][2:5] != ['None', 'None', 'None']
            or partial.get('fixture_commits') != 0 or partial.get('model_checks', {}).get('checks') != []
            or any((failed_app / name).exists() for name in ('launch-intent.json', 'stdout.log', 'stderr-faulthandler.log', 'odoo-native.log'))
            or list((root / 'targets' / profile.database / 'diagnostics').glob('B-MODEL-*-observation.json'))
            or receipt.get('zero_dispatch_ro_exit_code') != 0
            or observation.get('validation_status') != 'B_ZERO_MODEL_DISPATCH_OLD_PROTECTION_VERIFIED'
            or observation.get('reader_id') != 59
            or observation.get('identity') != {'database': profile.database, 'oid': 2144129,
                'cluster': '7694897083368259627', 'dbuser': 'odoo', 'readonly': 'on',
                'isolation': 'repeatable read'}
            or observation.get('reader') != [{'id': 59, 'active': True, 'share': False,
                'company_id': 1, 'create_uid': 5, 'write_uid': 2, 'password_present': True}]
            or any(observation.get(key) is not True for key in ('ordinary_nonadmin_preserved',
                'no_extra_role_created', 'rollback_returned', 'connection_closed'))
            or observation.get('other_connections') != []
            or len(observation.get('domain_hashes', {})) != 39
            or any(observation.get(key) != baseline.get(key) for key in ('domain_hashes', 'old_audit_hashes',
                'reader_groups', 'group_xmlids', 'implied_groups', 'memberships', 'grants',
                'companies', 'groups', 'reader5', 'document', 'modules', 'c_original161_mail_links'))
            or observation.get('audits_since_a_before', [])[:len(prior_audits)] != prior_audits
            or len(audit_delta) != 3
            or {row.get('ydental_event') for row in audit_delta} != {'login', 'login.scope', 'store.switch'}
            or any(row.get('ydental_user_id') != 59 or row.get('ydental_result') != 'accepted' for row in audit_delta)
            or observation.get('reader_session') != [{'ydental_user_id': 59,
                'ydental_store_id': 1, 'ydental_revision': 1}]
            or (root / 'B-ACTION-ATTEMPT2.json').exists() or (root / 'B-ACTION-COMPLETE.json').exists()):
        raise RuntimeError('B_ZERO_DISPATCH_RECOVERY_NOT_VERIFIED')
    return receipt


def run_b(profile, approval, authority, requested_path):
    """Normal-session manifest, rollback MODEL probes, then six real RPC probes."""
    from s10_lc2_cases import (Actor, Facts, b_collect_step, b_evidence_callbacks,
        b_selections, manifest_from_b_source, marker, run_b_only, run_fixture)
    from s10_lc2_evidence import CORE, collect_b_source
    import psycopg2
    profile.require_action('B-MODEL-6')
    profile.require_action('B-RPC-6')
    recovery = b_zero_dispatch_recovery(profile) if (profile.root / 'B-ACTION-IN-FLIGHT.json').exists() else None
    if (profile.root / 'B-ACTION-STOP.json').exists():
        raise RuntimeError('B_PRIOR_OUTCOME_OR_PRESERVATION_REQUIRES_INDEPENDENT_REVIEW')
    reference, reader = current_reader(profile)
    requested = strict_loads(requested_path.read_bytes())
    if requested.get('uid') != reader['user_id'] or requested.get('store_id') != 1:
        raise RuntimeError('B_CURRENT_READER_SCOPE_MISMATCH')
    b_selections(requested)
    directory = profile.root / ('B-' + uuid.uuid4().hex[:12])
    facts = Facts(directory)
    if recovery is not None:
        save_once(profile.root / 'B-ACTION-ATTEMPT2.json', {
            'original_latch_sha256': recovery['original_latch_sha256'],
            'zero_dispatch_ro_sha256': recovery['zero_dispatch_ro_sha256'],
            'directory': str(directory.relative_to(ROOT)), 'actor_id': 59,
            'stage': 'BEFORE_FRESH_AUTHENTICATION_FOR_UNSENT_MODEL_AND_RPC', 'automatic_retry': False})
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
    dispatch_intent = {
        'operation': 'B-MODEL-6_THEN_B-RPC-6', 'target': profile.database,
        'actor_id': actor.uid, 'stage': 'BEFORE_MODEL_DISPATCH',
        'directory': str(directory.relative_to(ROOT)),
        'automatic_retry': False, 'completion_reference': 'B-ACTION-COMPLETE.json',
        'failure_followup': 'INDEPENDENT_READ_ONLY_REVIEW_BEFORE_ANY_REENTRY'}
    if recovery is None:
        save_once(profile.root / 'B-ACTION-IN-FLIGHT.json', dispatch_intent)
    else:
        facts.save('B-attempt2-dispatch-intent', dispatch_intent)
    try:
        result = run_b_only(manifest=manifest, provider_ref=reference, approval=approval,
            product_commit=authority['product_commit'], test_commit=authority['test_commit'], facts=facts,
            model_probe=model_probe, actor_factory=actor_factory,
            observe=lambda *args: callbacks['observe'](*args),
            server_events=lambda *args: callbacks['server_events'](*args),
            terminal=lambda *args: callbacks['terminal'](*args), profile=profile)
        facts.save('result', result)
        if result['status'] == 'PASS':
            save_once(profile.root / 'B-ACTION-COMPLETE.json', {
                'status': 'PASS', 'target': profile.database,
                'result_reference': str((directory / 'result.json').relative_to(ROOT)),
                'model_and_rpc_terminal_preservation_verified': True,
                'automatic_replay_authorized': False})
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


def scratch_requested(profile, requested_path):
    if profile.target_role != 'scratch':
        raise RuntimeError('CURRENT_D_EXPLICIT_SCRATCH_TARGET_REQUIRED')
    request = strict_loads(requested_path.read_bytes())
    path = ROOT / request['manifest_ref']
    if path.is_symlink() or not path.resolve().is_relative_to(profile.root):
        raise RuntimeError('CURRENT_D_REFERENCE_INVALID')
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != request['manifest_sha256']:
        raise RuntimeError('CURRENT_D_REFERENCE_BYTES_CHANGED')
    value = strict_loads(raw)
    if (value.get('database') != profile.database or value.get('oid') != 2144130
            or value.get('cluster') != '7694897083368259627'
            or value.get('rollback_returned') is not True or value.get('connection_closed') is not True):
        raise RuntimeError('CURRENT_D_ACTUAL_TARGET_NOT_PROVEN')
    return request, value


def repair_upgrade_scratch_font(profile, approval, authority, requested_path):
    """Load the same product PDF repair before D; final data-bearing E-D remains separate."""
    from s10_lc2_cases import closed_log_report, marker
    from s10_lc2_launch import keep_primary
    profile.require_action('repair-upgrade-scratch-font')
    request, observed = scratch_requested(profile, requested_path)
    if (observed.get('validation_status') not in {'CURRENT_SCRATCH_EMPTY_CONFIGURATION_VERIFIED',
            'CURRENT_D_NATIVE_CONFIGURATION_VERIFIED'}
            or any(observed.get('business_counts', {}).get(name) != 0 for name in (
                'ydental_treatment_fee', 'ydental_settlement_source', 'ydental_settlement_payment',
                'ydental_settlement_refund', 'account_move', 'account_payment'))):
        raise RuntimeError('SCRATCH_FONT_REPAIR_BEFORE_TARGET_NOT_PROVEN')
    save_once(profile.root / 'FONT-REPAIR-UPGRADE-SCRATCH-IN-FLIGHT.json', {
        'before_sha256': request['manifest_sha256'], 'target': profile.database,
        'product_commit': authority['product_commit'], 'test_commit': authority['test_commit'],
        'final_E_D_claimed': False, 'automatic_retry': False})
    app = OwnedApplication(marker('scratch', profile), approval=approval,
        product_commit=authority['product_commit'], test_commit=authority['test_commit'],
        action='scratch-upgrade', profile=profile)
    try:
        app.start(['--stop-after-init', '--load-language=zh_CN', '-u', 'ydental_settlement'])
    except BaseException as error:
        primary = keep_primary(app.directory, error, stage='scratch_font_repair_upgrade_start')
        exit_path = app.directory / 'parent-exit.tsv'
        if not exit_path.exists() or not any(line.startswith(b'parent.end\t') for line in exit_path.read_bytes().splitlines()):
            app.close(primary=primary)
        raise
    code = app.wait(1200)
    if code != 0:
        raise RuntimeError('SCRATCH_FONT_REPAIR_UPGRADE_FAILED_KEEP_SAME_TARGET')
    logs = closed_log_report(app)
    result = {'status': 'SCRATCH_FONT_REPAIR_EXIT_ZERO_INDEPENDENT_POST_RO_REQUIRED',
        'exit_code': code, 'target': profile.database, 'scope': 'ydental_settlement_only',
        'application_directory': str(app.directory.relative_to(ROOT)),
        'diagnostic_records': logs['record_count'], 'final_E_D_claimed': False}
    save_once(profile.root / 'FONT-REPAIR-UPGRADE-SCRATCH-RESULT.json', result)
    return result


def prepare_scratch(profile, approval, authority, requested_path):
    from s10_lc2_cases import run_fixture
    profile.require_action('scratch-bootstrap')
    request, observed = scratch_requested(profile, requested_path)
    intent = profile.root / 'D-BOOTSTRAP-IN-FLIGHT.json'
    expected_status = ('CURRENT_SCRATCH_FIRST_BOOTSTRAP_ZERO_SETUP_COMMIT_INDEPENDENTLY_OBSERVED'
                       if intent.exists() else 'CURRENT_SCRATCH_EMPTY_CONFIGURATION_VERIFIED')
    if (observed.get('validation_status') != expected_status
            or observed.get('stores_count') != 0 or observed.get('all_mail_servers_count') != 0
            or any(observed.get('business_counts', {}).get(name) != 0 for name in (
                'ydental_treatment_fee', 'ydental_settlement_source', 'ydental_settlement_payment',
                'ydental_settlement_refund', 'account_move', 'account_payment'))):
        raise RuntimeError('CURRENT_D_BOOTSTRAP_NOT_EMPTY_OR_EXTERNAL_MAIL_POSSIBLE')
    if intent.exists():
        recovery = strict_loads((profile.root / 'D-bootstrap-startup-recovery.json').read_bytes())
        def recovered_reference(name):
            path = ROOT / recovery[name + '_ref']
            if (path.is_symlink() or not path.resolve().is_relative_to(profile.root)
                    or path.stat().st_uid != os.getuid()):
                raise RuntimeError('D_FIRST_BOOTSTRAP_RECOVERY_REFERENCE_INVALID')
            raw = path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != recovery[name + '_sha256']:
                raise RuntimeError('D_FIRST_BOOTSTRAP_RECOVERY_REFERENCE_CHANGED')
            return raw
        stop_raw = recovered_reference('archived_stop')
        parent = recovered_reference('parent_exit').decode('ascii').splitlines()
        recovered_ro = strict_loads(recovered_reference('zero_commit_ro'))
        if (recovery.get('reason') != 'SCRATCH_NATIVE_PRIVACY_DIRECTORY_MISSING_ZERO_COMMIT'
                or recovery.get('attempt') != 2 or recovery.get('independent_reviewer') != '/root/acceptance_s10'
                or recovery.get('original_intent_sha256') != hashlib.sha256(intent.read_bytes()).hexdigest()
                or recovery['original_intent_sha256'] != 'a95a198cfbf483c3b114f7bf2504cec97c3adf4a8598092046bed42355f43b27'
                or hashlib.sha256(stop_raw).hexdigest() != '7964f3d01119fae1b7bdd2a070fb9d14e56b3ae6e794835d2974db583e470a61'
                or strict_loads(stop_raw) != {'pid': 1877689, 'primary_event_id': None,
                    'reason': 'DIAGNOSTIC_LOG_MISSING', 'root_event_id': None,
                    'ts_utc': '2026-10-18T09:33:44.306305+00:00'}
                or recovery.get('zero_commit_ro_exit_code') != 0
                or recovery.get('zero_commit_ro_sha256') != request['manifest_sha256']
                or recovery['zero_commit_ro_sha256'] != 'd31d1ff258994ed489b6ee0983f80031d9a711fcb4c0179fbf34b436696aa823'
                or recovered_ro != observed
                or recovery.get('parent_exit_ref') != str((profile.root / 'application-scratch-fixture-8555cfde/parent-exit.tsv').relative_to(ROOT))
                or not any(row.split('\t')[:1] == ['parent.end'] and row.split('\t')[2:5] == ['1877689', '1', 'None'] for row in parent)
                or any(observed.get(key) is not True for key in ('old_46_domains_preserved',
                    'old_module_schema_view_parameters_preserved', 'old_50_accounts_7_journals_preserved',
                    'no_new_users_or_business_configuration', 'rollback_returned', 'connection_closed'))
                or observed.get('new_users_since_initial') != []
                or (profile.root / 'D-fixture-public-identities.json').exists()
                or (profile.root / 'D-bootstrap-result.json').exists()
                or any((profile.root / 'credentials').glob('scratch-user-*.json'))
                or any((profile.run_root / profile.database / 'diagnostics').glob('D-setup-*.json'))):
            raise RuntimeError('D_FIRST_BOOTSTRAP_STARTUP_ZERO_COMMIT_NOT_VERIFIED')
        save_once(profile.root / 'D-bootstrap-attempt2-intent.json', {
            'attempt': 2, 'original_intent_sha256': recovery['original_intent_sha256'],
            'zero_commit_ro_sha256': recovery['zero_commit_ro_sha256'],
            'failure_pid': 1877689, 'automatic_retry': False})
    else:
        save_once(intent, {'before_sha256': request['manifest_sha256'], 'target': profile.database,
            'stage': 'BEFORE_NEW_NATIVE_CONFIGURATION_ONLY', 'automatic_retry': False,
            'no_financial_source_or_transaction_factory': True})
    result = run_fixture('scratch', approval=approval, product_commit=authority['product_commit'],
        test_commit=authority['test_commit'], mode='scratch-bootstrap', profile=profile)
    fixture = result['ram']
    safe_fixture = {key: fixture[key] for key in ('store_id', 'area_id', 'station_id', 'capability_id',
        'uom_id', 'currency_id', 'company_id', 'manager_levels')}
    safe_fixture['actors'] = {role: {'user_id': fixture[role]['uid'],
        'provider_ref': str((profile.root / 'credentials' / ('scratch-user-%d.json' % fixture[role]['uid'])).relative_to(ROOT))}
        for role in ('manager', 'frontdesk', 'doctor')}
    save_once(profile.root / 'D-fixture-public-identities.json', safe_fixture)
    save_once(profile.root / 'D-bootstrap-result.json', result['safe'])
    return result['safe'] | {'status': 'CONFIGURATION_COMMIT_RETURNED_INDEPENDENT_RO_REQUIRED'}


def run_d_scratch(profile, approval, authority, requested_path):
    from s10_lc2_cases import Actor, Facts, closed_log_report, d_flow, d_observe, marker, verify_d
    for action in ('D-ADMIT', 'D-NORMAL-6', 'D-FAILED-2', 'D-RECOVER-2', 'D-LOST-REFUND-2', 'D-VERIFY-RETRY', 'LOG-02'):
        profile.require_action(action)
    request, observed = scratch_requested(profile, requested_path)
    if (profile.root / 'D-CHAIN-IN-FLIGHT.json').exists() or (profile.root / 'D-CHAIN-COMPLETE.json').exists():
        raise RuntimeError('CURRENT_D_PRIOR_CHAIN_EXISTS_READ_ONLY_REVIEW_NO_REPLAY')
    fixture_raw = (profile.root / 'D-fixture-public-identities.json').read_bytes()
    fixture = strict_loads(fixture_raw)
    if (observed.get('validation_status') != 'CURRENT_D_NATIVE_CONFIGURATION_VERIFIED'
            or observed.get('fixture_sha256') != hashlib.sha256(fixture_raw).hexdigest()
            or observed.get('ordinary_actual_actors_verified') is not True
            or observed.get('font_view_loaded') is not True
            or observed.get('report_parameters_expected') is not True
            or observed.get('all_mail_servers_count') != 0
            or fixture['manager_levels'].get('finance_approval') != 'write'
            or any(observed.get('business_counts', {}).get(name) != 0 for name in (
                'ydental_treatment_fee', 'ydental_settlement_source', 'ydental_settlement_payment',
                'ydental_settlement_refund', 'account_move', 'account_payment'))):
        raise RuntimeError('CURRENT_D_ACTORS_OR_EMPTY_FINANCIAL_BASELINE_NOT_PROVEN')
    schema_path = ROOT / observed['schema_ref']
    if schema_path.is_symlink() or not schema_path.resolve().is_relative_to(profile.root):
        raise RuntimeError('CURRENT_D_SCHEMA_REFERENCE_INVALID')
    schema_raw = schema_path.read_bytes()
    if hashlib.sha256(schema_raw).hexdigest() != observed['schema_sha256']:
        raise RuntimeError('CURRENT_D_SCHEMA_BYTES_CHANGED')
    schema = strict_loads(schema_raw)
    directory = profile.root / ('D-unique-' + uuid.uuid4().hex[:12])
    facts = Facts(directory)
    with OwnedApplication(marker('scratch', profile), approval=approval,
            product_commit=authority['product_commit'], test_commit=authority['test_commit'],
            action='scratch-service', profile=profile) as app:
        app.start([])
        app.wait_ready(60)
        actors = {}
        for role, reference in fixture['actors'].items():
            path = ROOT / reference['provider_ref']
            if (path.is_symlink() or not path.resolve().is_relative_to(profile.root / 'credentials')
                    or path.stat().st_uid != os.getuid() or stat.S_IMODE(path.stat().st_mode) != 0o600):
                raise RuntimeError('CURRENT_D_PROVIDER_BOUNDARY_INVALID')
            account = strict_loads(path.read_bytes())
            if account['user_id'] != reference['user_id']:
                raise RuntimeError('CURRENT_D_PROVIDER_ACTOR_MISMATCH')
            actor = Actor('scratch', 'current-D-' + role, account['user_id'], account['login'], account['password'],
                budget=app.budget, directory=directory / (role + '-http'))
            actor.login(fixture['store_id'])
            actors[role] = actor
        source = d_flow(actors['manager'], actors['frontdesk'], actors['doctor'], fixture, facts,
            profile=profile, observe=lambda label: d_observe(label, profile=profile, schema=schema),
            server_pid=app.process.pid)
        app.check()
    closed = closed_log_report(app)
    terminal = d_observe('terminal-after-service-exit', profile=profile, schema=schema)
    facts.save('D-closed-service-terminal-independent', verify_d(terminal, source,
        state='done', actual_refund=2, profile=profile) | {
            'source': str(terminal.relative_to(ROOT)), 'owned_service_closed': True,
            'closed_diagnostic_records': closed['record_count'], 'service_pid': app.process.pid,
            'native_exit_code': app.process.returncode})
    result = {'status': 'D_UNIQUE_SIX_TWO_COMMITTED_NATIVE_ACCOUNTING_INDEPENDENT_ACCEPTANCE_PENDING',
        'directory': str(directory.relative_to(ROOT)), 'source_ids': {key: value for key, value in source.items()
            if key not in {'pay_key', 'execute_key'}}, 'received': 6, 'actually_refunded': 2, 'net_received': 4,
        'application_directory': str(app.directory.relative_to(ROOT)), 'real_gateway_claimed': False}
    save_once(profile.root / 'D-CHAIN-COMPLETE.json', result)
    return result




def c_committed_d_source(profile, request):
    from s10_lc2_evidence import save_once
    path = ROOT / request['D_source_ref']
    if path.is_symlink() or not path.resolve().is_relative_to(profile.root):
        raise RuntimeError('C_COMMITTED_D_SOURCE_REFERENCE_INVALID')
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != request['D_source_sha256']:
        raise RuntimeError('C_COMMITTED_D_SOURCE_BYTES_CHANGED')
    # This is the original durable pre-execute record, read only after its
    # matching whole-chain COMPLETE and terminal independent commit evidence.
    source = strict_loads(raw)['source']
    complete = strict_loads((profile.root / 'D-CHAIN-COMPLETE.json').read_bytes())
    if (complete.get('status') != 'D_UNIQUE_SIX_TWO_COMMITTED_NATIVE_ACCOUNTING_INDEPENDENT_ACCEPTANCE_PENDING'
            or complete.get('received') != 6 or complete.get('actually_refunded') != 2
            or complete.get('net_received') != 4
            or complete.get('source_ids') != {key: value for key, value in source.items()
                                             if key not in {'pay_key', 'execute_key'}}):
        raise RuntimeError('C_UNIQUE_COMMITTED_D_SOURCE_AND_KEYS_NOT_PROVEN')
    return source



def c_company_create_zero_commit_recovery(profile, request, observed):
    """Only the preserved company-create read-guard failure permits attempt two."""
    receipt_path = profile.root / 'C-company-create-recovery.json'
    receipt = strict_loads(receipt_path.read_bytes())
    def reference(name):
        path = ROOT / receipt[name + '_ref']
        if path.is_symlink() or not path.resolve().is_relative_to(profile.root):
            raise RuntimeError('C_COMPANY_CREATE_RECOVERY_REFERENCE_INVALID')
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != receipt[name + '_sha256']:
            raise RuntimeError('C_COMPANY_CREATE_RECOVERY_BYTES_CHANGED')
        return raw
    original_raw = reference('original_intent')
    failure = strict_loads(reference('failure_index'))
    ro_raw = reference('zero_commit_ro')
    exits = [line.split('\t') for line in reference('parent_exit').decode().splitlines()]
    original = strict_loads(original_raw)
    if (receipt.get('reason') != 'C_COMPANY_CREATE_NATIVE_UNMANAGED_READ_GUARD_ZERO_CONFIGURATION_COMMIT'
            or receipt.get('attempt') != 2 or receipt.get('independent_reviewer') != '/root/acceptance_s10'
            or receipt.get('zero_commit_ro_exit_code') != 0
            or receipt['original_intent_sha256'] != '9ba3b7e731c5317026abedb0d0659008c8d1eb7ea5570ea050441e889bc022ca'
            or original_raw != (profile.root / 'C-SCRATCH-CONFIGURATION-IN-FLIGHT.json').read_bytes()
            or receipt['zero_commit_ro_sha256'] != 'c406c516904be9af4afdee3589bcb50873da7f43134669959042a911371f8dbd'
            or receipt['zero_commit_ro_ref'] != request['manifest_ref']
            or receipt['zero_commit_ro_sha256'] != request['manifest_sha256']
            or strict_loads(ro_raw) != observed
            or receipt['parent_exit_sha256'] != '74eb9ad7cba94677c8a8604a2b341a7789b0610f1ace3c51f6a08c60de180058'
            or sum(line[0] == 'parent.end' for line in exits) != 1
            or not any(line[0] == 'parent.end' and line[2:5] == ['1922420', '1', 'None'] for line in exits)
            or failure.get('actual_native_pid') != 1922420 or failure.get('actual_native_exit_code') != 1
            or failure.get('actual_native_signal') is not None
            or failure.get('first_error_class') != 'odoo.exceptions.AccessError'
            or failure.get('first_error_code') != 'access_denied: Native inventory is available only through the scoped workbench.'
            or observed.get('validation_status') != 'CURRENT_C_COMPANY_CREATE_FAILED_ZERO_CONFIGURATION_COMMIT_VERIFIED'
            or observed.get('actual_failed_C_setup_exit_code') != 1
            or observed.get('financial_actions_dispatched') != 0 or observed.get('business_operations') != 0
            or observed.get('possible_new_configuration_or_actor_rows') != {'companies': [], 'users': [], 'partners': []}
            or any(observed.get(key) is not True for key in ('rollback_returned', 'connection_closed',
                'normal_C_fixture_not_yet_created', 'unique_D_native_accounting_verified'))
            or observed.get('other_connections') != []
            or original.get('D_source_sha256') != request['D_source_sha256']
            or (profile.root / 'C-fixture-public-identities.json').exists()):
        raise RuntimeError('C_COMPANY_CREATE_EXACT_ZERO_COMMIT_DISPOSITION_NOT_PROVEN')
    baseline_path = ROOT / original['before_ref']
    baseline_raw = baseline_path.read_bytes()
    if (baseline_path.is_symlink() or not baseline_path.resolve().is_relative_to(profile.root)
            or hashlib.sha256(baseline_raw).hexdigest() != original['before_sha256']):
        raise RuntimeError('C_COMPANY_CREATE_ORIGINAL_PROTECTION_BASELINE_CHANGED')
    baseline = strict_loads(baseline_raw)
    for key in ('domain_hashes', 'D_native_current_rows', 'mutex_rows', 'configuration_audits',
                'native_admin_company_assignments', 'native_admin_safe_metadata'):
        if observed.get(key) != baseline.get(key):
            raise RuntimeError('C_COMPANY_CREATE_ZERO_COMMIT_BASELINE_DIFFERENCE')
    save_once(profile.root / 'C-SCRATCH-CONFIGURATION-ATTEMPT2-IN-FLIGHT.json', {
        'original_intent_sha256': receipt['original_intent_sha256'],
        'zero_commit_ro_sha256': request['manifest_sha256'],
        'recovery_sha256': hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
        'original_intent_retained': True, 'automatic_retry': False})


def run_native_inventory_read_regression(profile, approval, authority, requested_path):
    from s10_lc2_cases import run_fixture
    profile.require_action('inventory-native-read-regression')
    if profile.target_role != 'main':
        raise RuntimeError('NATIVE_INVENTORY_REGRESSION_MAIN_ONLY')
    request = strict_loads(requested_path.read_bytes())
    path = ROOT / request['manifest_ref']
    if (path.is_symlink() or not path.resolve().is_relative_to(profile.root)
            or hashlib.sha256(path.read_bytes()).hexdigest() != request['manifest_sha256']):
        raise RuntimeError('NATIVE_INVENTORY_ACTUAL_RO_TARGET_REFERENCE_INVALID')
    actual = strict_loads(path.read_bytes())
    if (actual.get('database') != profile.database or actual.get('oid') != 2144129
            or actual.get('cluster') != '7694897083368259627'
            or actual.get('validation_status') != 'CURRENT_NATIVE_INVENTORY_NONEMPTY_ROLE_TARGETS_VERIFIED'
            or any(actual.get(key) is not True for key in ('rollback_returned', 'connection_closed',
                'native_admin2_verified', 'ordinary_reader59_verified', 'nonempty_unmanaged_and_managed_verified'))):
        raise RuntimeError('NATIVE_INVENTORY_REAL_ROLES_AND_NONEMPTY_TARGETS_NOT_PROVEN')
    model = {key: actual[key] for key in ('admin_uid', 'ordinary_uid', 'unmanaged', 'managed')}
    save_once(profile.root / 'NATIVE-INVENTORY-READ-MODEL-IN-FLIGHT.json', {
        'before_ref': request['manifest_ref'], 'before_sha256': request['manifest_sha256'],
        'unmanaged_location_id': model['unmanaged']['id'], 'managed_location_id': model['managed']['id'],
        'native_mutations': 0, 'automatic_retry': False})
    result = run_fixture('main', approval=approval, product_commit=authority['product_commit'],
        test_commit=authority['test_commit'], mode='main-inventory-read-only', manifest=model, profile=profile)['safe']
    if (result.get('check_count') != 6 or result.get('fixture_commits') != 0
            or result.get('native_mutations') != 0 or len(result.get('checks', [])) != 6
            or any(row.get(key) is not True for row in result['checks']
                   for key in ('expected_result_matches', 'rollback_returned', 'cursor_closed'))):
        raise RuntimeError('NATIVE_INVENTORY_REAL_MODEL_RESULTS_INCOMPLETE')
    result['status'] = 'SIX_REAL_NATIVE_INVENTORY_MODEL_CHECKS_PASSED_INDEPENDENT_POST_RO_PENDING'
    save_once(profile.root / 'NATIVE-INVENTORY-READ-MODEL-RETURNED.json', result)
    return result



def run_c_company_stage(profile, approval, authority, requested_path):
    """Retry only the proven-uncommitted company/manager stage, then stop."""
    from s10_lc2_cases import run_fixture
    profile.require_action('scratch-c-company-stage')
    request, observed = scratch_requested(profile, requested_path)
    c_committed_d_source(profile, request)
    receipt = strict_loads((profile.root / 'C-chart-tax-guard-recovery.json').read_bytes())
    def reference(name):
        path = ROOT / receipt[name + '_ref']
        if path.is_symlink() or not path.resolve().is_relative_to(profile.root):
            raise RuntimeError('C_COMPANY_STAGE_RECOVERY_REFERENCE_INVALID')
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != receipt[name + '_sha256']:
            raise RuntimeError('C_COMPANY_STAGE_RECOVERY_BYTES_CHANGED')
        return raw
    original = reference('original_intent')
    attempt2 = reference('attempt2_intent')
    failure = strict_loads(reference('failure_index'))
    ro = reference('zero_commit_ro')
    exits = [line.split('\t') for line in reference('parent_exit').decode().splitlines()]
    if (receipt.get('reason') != 'C_CHART_DEFAULT_TAX_OWNED_CATALOG_GUARD_ZERO_COMPANY_STAGE_COMMIT'
            or receipt.get('stage') != 'company-and-manager-only'
            or receipt.get('independent_reviewer') != '/root/acceptance_s10' or receipt.get('zero_commit_ro_exit_code') != 0
            or receipt['original_intent_sha256'] != '9ba3b7e731c5317026abedb0d0659008c8d1eb7ea5570ea050441e889bc022ca'
            or original != (profile.root / 'C-SCRATCH-CONFIGURATION-IN-FLIGHT.json').read_bytes()
            or strict_loads(original).get('D_source_sha256') != request['D_source_sha256']
            or receipt['attempt2_intent_sha256'] != 'e8c6b73cc481dca6445b401ba42edc3d97aa2687fd9212967fc8e7faddb13d8b'
            or attempt2 != (profile.root / 'C-SCRATCH-CONFIGURATION-ATTEMPT2-IN-FLIGHT.json').read_bytes()
            or receipt['zero_commit_ro_sha256'] != '486ac4ba5fe40ed2e371a591e3e17df2d6fe2c924e6db092ebf9d226d1b3bd48'
            or receipt['zero_commit_ro_sha256'] != request['manifest_sha256']
            or receipt['zero_commit_ro_ref'] != request['manifest_ref'] or strict_loads(ro) != observed
            or receipt['parent_exit_sha256'] != 'ae184ea87d6da37bcd8555a6383760590adbf0329525521595e92ae3ef518029'
            or sum(line[0] == 'parent.end' for line in exits) != 1
            or not any(line[0] == 'parent.end' and line[2:5] == ['1933915', '1', 'None'] for line in exits)
            or failure.get('actual_native_pid') != 1933915 or failure.get('actual_native_exit_code') != 1
            or failure.get('actual_native_signal') is not None or failure.get('first_native_exception') != 'odoo.exceptions.AccessError'
            or failure.get('first_native_message') != 'access_denied: Native service data must use the controlled catalog or price action.'
            or observed.get('validation_status') != 'CURRENT_C_CHART_TAX_GUARD_FAILED_ZERO_CONFIGURATION_COMMIT_VERIFIED'
            or observed.get('possible_new_configuration_or_actor_rows') != {'companies': [], 'users': [], 'partners': []}
            or observed.get('financial_actions_dispatched') != 0 or observed.get('business_operations') != 0
            or observed.get('normal_C_fixture_not_yet_created') is not True
            or observed.get('unique_D_native_accounting_verified') is not True
            or (profile.root / 'C-fixture-public-identities.json').exists()):
        raise RuntimeError('C_COMPANY_STAGE_ONLY_ZERO_COMMIT_RECOVERY_NOT_PROVEN')
    save_once(profile.root / 'C-COMPANY-MANAGER-STAGE-IN-FLIGHT.json', {
        'zero_commit_ro_sha256': request['manifest_sha256'],
        'original_intent_sha256': receipt['original_intent_sha256'],
        'attempt2_intent_sha256': receipt['attempt2_intent_sha256'],
        'stage': 'company-and-manager-only', 'remaining_stages_dispatched': False,
        'automatic_retry': False, 'original_latches_retained': True})
    response = run_fixture('scratch', approval=approval, product_commit=authority['product_commit'],
        test_commit=authority['test_commit'], mode='scratch-c-company-stage', profile=profile)
    initial = response['safe']['initial']
    manager = response['ram']['manager']
    if manager['uid'] != initial['manager_id'] or response['safe']['fixture_commits'] != 1:
        raise RuntimeError('C_FIRST_STAGE_RETURNED_IDENTITY_INVALID')
    result = {'initial': initial, 'manager_provider_ref': str((profile.root / 'credentials' /
        ('scratch-user-%d.json' % initial['manager_id'])).relative_to(ROOT)),
        'fixture_commits': 1, 'product_commit': authority['product_commit'],
        'D_source_sha256': request['D_source_sha256'],
        'status': 'C_COMPANY_MANAGER_COMMIT_RETURNED_INDEPENDENT_POST_RO_REQUIRED',
        'remaining_stages_dispatched': False}
    save_once(profile.root / 'C-COMPANY-MANAGER-STAGE-RETURNED.json', result)
    return result


def run_c_remaining_configuration(profile, approval, authority, requested_path):
    from s10_lc2_cases import run_fixture
    profile.require_action('scratch-c-remaining-configuration')
    request, observed = scratch_requested(profile, requested_path)
    c_committed_d_source(profile, request)
    first_raw = (profile.root / 'C-COMPANY-MANAGER-STAGE-RETURNED.json').read_bytes()
    first = strict_loads(first_raw)
    if (observed.get('validation_status') != 'CURRENT_C_COMPANY_MANAGER_STAGE_INDEPENDENTLY_VERIFIED'
            or observed.get('company_stage_returned_sha256') != hashlib.sha256(first_raw).hexdigest()
            or observed.get('initial') != first['initial'] or first.get('remaining_stages_dispatched') is not False
            or first.get('D_source_sha256') != request['D_source_sha256']
            or first.get('product_commit') != authority['product_commit']
            or any(observed.get(key) is not True for key in ('company_manager_native_configuration_verified',
                'ordinary_new_manager_verified', 'owned_catalog_tax_baseline_preserved',
                'remaining_C_stages_not_run', 'unique_D_native_accounting_verified'))
            or observed.get('all_mail_servers_count') != 0
            or (profile.root / 'C-fixture-public-identities.json').exists()):
        raise RuntimeError('C_EXISTING_FIRST_STAGE_NOT_INDEPENDENTLY_VERIFIED')
    provider = ROOT / first['manager_provider_ref']
    if (provider.is_symlink() or provider.parent != profile.root / 'credentials'
            or provider.stat().st_uid != os.getuid() or stat.S_IMODE(provider.stat().st_mode) != 0o600):
        raise RuntimeError('C_EXISTING_MANAGER_PROVIDER_BOUNDARY_INVALID')
    account = strict_loads(provider.read_bytes())
    if account.get('user_id') != first['initial']['manager_id']:
        raise RuntimeError('C_EXISTING_MANAGER_PROVIDER_ID_CHANGED')
    save_once(profile.root / 'C-REMAINING-CONFIGURATION-IN-FLIGHT.json', {
        'company_stage_returned_sha256': observed['company_stage_returned_sha256'],
        'before_sha256': request['manifest_sha256'], 'company_and_manager_replayed': False,
        'stages': ['clinics', 'doctor-password', 'reader-password', 'native-finance-config'],
        'automatic_retry': False})
    response = run_fixture('scratch', approval=approval, product_commit=authority['product_commit'],
        test_commit=authority['test_commit'], mode='scratch-c-remaining-configuration', profile=profile,
        manifest={'initial': first['initial'], 'manager_account': account})
    safe, ram = response['safe'], response['ram']
    if safe.get('fixture_commits') != 4:
        raise RuntimeError('C_REMAINING_CONFIGURATION_RETURNED_STAGE_COUNT_INVALID')
    public = {'clinics': safe['clinics'], 'company2_id': safe['company2_id'],
        'actors': {role: {'user_id': ram[role]['uid'], 'provider_ref': str((profile.root /
            'credentials' / ('scratch-user-%d.json' % ram[role]['uid'])).relative_to(ROOT))}
            for role in ('manager', 'doctor', 'reader')}}
    save_once(profile.root / 'C-fixture-public-identities.json', public)
    save_once(profile.root / 'C-configuration-returned.json', safe | {'company_stage_replayed': False})
    return {'status': 'C_REMAINING_CONFIGURATION_COMMIT_RETURNED_POST_RO_REQUIRED',
        'clinic_count': len(public['clinics']), 'remaining_fixture_commits': 4,
        'company_and_manager_replayed': False, 'fund_dispatches': 0}


def run_native_tax_defaults_rollback(profile, approval, authority, requested_path):
    from s10_lc2_cases import run_fixture
    profile.require_action('tax-defaults-rollback')
    request, observed = scratch_requested(profile, requested_path)
    if (request['manifest_sha256'] != '486ac4ba5fe40ed2e371a591e3e17df2d6fe2c924e6db092ebf9d226d1b3bd48'
            or observed.get('validation_status') != 'CURRENT_C_CHART_TAX_GUARD_FAILED_ZERO_CONFIGURATION_COMMIT_VERIFIED'
            or observed.get('unique_D_native_accounting_verified') is not True):
        raise RuntimeError('TAX_DEFAULTS_ACTUAL_FIRST_BASELINE_NOT_PROVEN')
    taxes = observed['account_tax_baseline']
    model = {'company_id': 1,
        'known_sale_tax_ids': sorted(row['id'] for row in taxes if row['active'] and row['company_id'] == 1
            and row['type_tax_use'] in {'sale', 'all'}),
        'known_purchase_tax_ids': sorted(row['id'] for row in taxes if row['active'] and row['company_id'] == 1
            and row['type_tax_use'] in {'purchase', 'all'})}
    save_once(profile.root / 'TAX-DEFAULTS-ROLLBACK-IN-FLIGHT.json', {
        'before_sha256': request['manifest_sha256'], 'actor_id': 2, 'company_id': 1,
        'old_owned_product_writes': 0, 'fixture_commits': 0, 'automatic_retry': False})
    result = run_fixture('scratch', approval=approval, product_commit=authority['product_commit'],
        test_commit=authority['test_commit'], mode='scratch-tax-defaults-rollback', manifest=model, profile=profile)['safe']
    if (result.get('fixture_commits') != 0 or result.get('old_owned_product_writes') != 0
            or any(result.get(key) is not True for key in ('rollback_returned', 'cursor_closed'))
            or len(result.get('checks', [])) != 2
            or any(row.get('real_native_addition_observed') is not True for row in result['checks'])):
        raise RuntimeError('TAX_DEFAULTS_NATIVE_ROLLBACK_RESULTS_INCOMPLETE')
    save_once(profile.root / 'TAX-DEFAULTS-ROLLBACK-RETURNED.json', result)
    return result | {'independent_post_RO_preservation': 'PENDING'}


def prepare_c_scratch(profile, approval, authority, requested_path):
    from s10_lc2_cases import run_fixture
    profile.require_action('scratch-c-configuration')
    request, observed = scratch_requested(profile, requested_path)
    d_source = c_committed_d_source(profile, request)
    previous = profile.root / 'C-SCRATCH-CONFIGURATION-IN-FLIGHT.json'
    if previous.exists():
        c_company_create_zero_commit_recovery(profile, request, observed)
    elif observed.get('validation_status') != 'CURRENT_D_FINISHED_NATIVE_ACCOUNTING_VERIFIED_FOR_UNFUNDED_C':
        raise RuntimeError('C_NEW_CONFIGURATION_PREDECESSORS_NOT_INDEPENDENTLY_VERIFIED')
    if (observed.get('unique_D_native_accounting_verified') is not True
            or observed.get('all_mail_servers_count') != 0
            or observed.get('normal_C_fixture_not_yet_created') is not True):
        raise RuntimeError('C_NEW_CONFIGURATION_PREDECESSORS_NOT_INDEPENDENTLY_VERIFIED')
    if not previous.exists():
        save_once(previous, {
            'before_ref': request['manifest_ref'], 'before_sha256': request['manifest_sha256'],
            'D_source_sha256': request['D_source_sha256'], 'D_patient_id': d_source['patient_id'],
            'D_fee_id': d_source['fee_id'], 'automatic_retry': False,
            'scope': 'new_C_configuration_only_no_fee_account_move_payment_factory'})
    result = run_fixture('scratch', approval=approval, product_commit=authority['product_commit'],
        test_commit=authority['test_commit'], mode='scratch-c-configuration-only',
        manifest={'D_source_ids': complete_source_ids(d_source)}, profile=profile)
    safe, ram = result['safe'], result['ram']
    public = {'clinics': safe['clinics'], 'company2_id': safe['company2_id'],
              'actors': {role: {'user_id': ram[role]['uid'], 'provider_ref': str((profile.root /
                  'credentials' / ('scratch-user-%d.json' % ram[role]['uid'])).relative_to(ROOT))}
                  for role in ('manager', 'doctor', 'reader')}}
    save_once(profile.root / 'C-fixture-public-identities.json', public)
    save_once(profile.root / 'C-configuration-returned.json', safe)
    return {'status': 'C_NATIVE_CONFIGURATION_COMMIT_RETURNED_INDEPENDENT_RO_REQUIRED',
            'clinic_count': len(public['clinics']), 'fund_dispatches': 0}


def complete_source_ids(source):
    return {key: value for key, value in source.items() if key not in {'pay_key', 'execute_key'}}


def c_rank_tail_prefix(profile, request):
    """Consume the exact independently proved rank incident, never clear its latch."""
    def fixed_file(reference, digest):
        path = ROOT / reference
        if path.is_symlink() or not path.resolve().is_relative_to(profile.root):
            raise RuntimeError('C_RANK_TAIL_REFERENCE_BOUNDARY_INVALID')
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != digest:
            raise RuntimeError('C_RANK_TAIL_HISTORICAL_BYTES_CHANGED')
        return strict_loads(raw)
    bridge = fixed_file(request['rank_bridge_ref'], request['rank_bridge_sha256'])
    if (request['rank_bridge_sha256'] != '93d757f5250b4ebe99d84de961fe22e9330c64604d94494085b9740e6ceae0c4'
            or bridge.get('validation_status') != 'CURRENT_NEW_C_CANONICAL_PARTNER_NATIVE_CUSTOMER_RANK_DELTA_VERIFIED'
            or any(bridge.get(key) is not True for key in ('rollback_returned', 'connection_closed',
                'only_customer_rank_and_exact_native_write_metadata_changed'))
            or bridge.get('other_connections') != []):
        raise RuntimeError('C_RANK_TAIL_EXACT_INDEPENDENT_BRIDGE_REQUIRED')
    failure = fixed_file('.local/s10-technical-closeout-v1/C-scratch-source-first-failure-index.json',
        '44a618d47b7f3276d88f84c7727beda5c5bf7ea9c95c09f6a554f0ed22f69712')
    snapshot = fixed_file('.local/s10-technical-closeout-v1/C-scratch-source-first-failure-runtime-originals/index.json',
        '3fa41325fd75a660cdc20a500e5b08fda5b2e03ab2d09ddb10b6984224c0308d')
    entries = {item['original_ref']: item for item in snapshot['items']}
    def preserved(reference):
        return fixed_file(reference, entries[reference]['sha256'])
    original = fixed_file('.local/s10-technical-closeout-v1/C-SCRATCH-SOURCE-CHAIN-IN-FLIGHT.json',
        '5737815e0ff6adbc07250b21616d232fd1a6a3eff11c73119478ccbb6ea3945b')
    if (failure['owned_native_returncode'] != 0 or failure['owned_native_signal'] is not None
            or failure['first_error'] != 'C_BILLED_SOURCE_OR_FINANCIAL_OWNER_MUTATED_BY_LATER_C_ACTION'
            or original['directory'] != failure['actual_source_directory']
            or original['D_source_sha256'] != request['D_source_sha256']):
        raise RuntimeError('C_RANK_TAIL_FIRST_FAILURE_OR_D_REFERENCE_MISMATCH')
    prior = original['directory']
    source = preserved(prior + '/C-family-source-bill-returned.json')
    source.update(preserved(prior + '/C-family-source-original-committed.json'), original_expected=True)
    rows = [source, preserved(prior + '/C-family-target-bill-returned.json'),
        preserved(prior + '/C-family-unrelated-bill-returned.json'),
        preserved(prior + '/C-log-unbilled-upstream-returned.json'),
        preserved(prior + '/C-same-company-bill-returned.json')]
    merged = preserved(prior + '/C-new-family-confirmed-returned.json')
    if (merged['source_patient_id'] != 2 or merged['target_patient_id'] != 4
            or merged['state_is_accepted'] is not True or source['original_id'] != 1
            or source['attachment_id'] != 236):
        raise RuntimeError('C_RANK_TAIL_ACTUAL_MERGE_AND_ORIGINAL_NOT_BOUND')
    old_state = profile.root / 'capture-scratch-C-new-C-same-company-native-unpaid-bill'
    index_ref = str((old_state / 'sealed-index.json').relative_to(ROOT))
    index = preserved(index_ref)
    for item in index['files']:
        path = old_state / item['path']
        raw = path.read_bytes()
        reference = str(path.relative_to(ROOT))
        if (path.is_symlink() or len(raw) != item['bytes']
                or hashlib.sha256(raw).hexdigest() != item['sha256']
                or entries[reference]['sha256'] != item['sha256']):
            raise RuntimeError('C_RANK_TAIL_STORED_PREDECESSOR_CAPTURE_CHANGED')
    for label in ('before', 'after'):
        path = Path(bridge[label + '_capture_ref'])
        if (not path.resolve().is_relative_to(profile.root)
                or hashlib.sha256(path.read_bytes()).hexdigest() != bridge[label + '_capture_sha256']):
            raise RuntimeError('C_RANK_TAIL_BRIDGE_CAPTURE_CHANGED')
    guard = {'partner_id': 19, 'actor_id': 9, 'invoice_ids': [7, 8], 'customer_rank': 2,
        'immutable_partner_sha256': bridge['new_partner_fullrow_sha256'],
        'last_fullrow_sha256': bridge['new_partner_fullrow_sha256'], 'stable_sha256': None}
    return rows, guard, old_state, original


def run_c_scratch_sources(profile, approval, authority, requested_path, *, tail_only=False):
    from s10_lc2_cases import Actor, Facts, capture, closed_log_report, d_selection, marker, stored_rows, verify_d
    # The following small functions are merged into existing cases.py during
    # the authorized code window; no additional platform/runner is introduced.
    from s10_lc2_cases import (CRecordedActor, new_c_confirmed_fee, run_new_c_fixture_flow,
                              c_source_selections, current_c_read_manifest, run_current_c_read_cells,
                              run_current_c_error303, run_current_c_rank_tail, verify_c_sources)
    for action in ('C-SCOPE', 'C-ATTACHMENT', 'LOG-03', 'scratch-c-sources'):
        profile.require_action(action)
    request, observed = scratch_requested(profile, requested_path)
    d_source = c_committed_d_source(profile, request)
    fixture_raw = (profile.root / 'C-fixture-public-identities.json').read_bytes()
    fixture = strict_loads(fixture_raw)
    if (observed.get('validation_status') != 'CURRENT_C_NATIVE_CONFIGURATION_VERIFIED'
            or observed.get('fixture_sha256') != hashlib.sha256(fixture_raw).hexdigest()
            or any(observed.get(key) is not True for key in ('ordinary_actual_C_actors_verified',
                'new_C_clinics_native_configuration_verified', 'unique_D_native_accounting_verified',
                'font_view_loaded', 'report_parameters_expected'))
            or observed.get('all_mail_servers_count') != 0):
        raise RuntimeError('C_NEW_ORDINARY_ROLES_CLINICS_AND_D_PRESERVATION_NOT_PROVEN')
    schema_path = ROOT / observed['schema_ref']
    if (schema_path.is_symlink() or not schema_path.resolve().is_relative_to(profile.root)
            or hashlib.sha256(schema_path.read_bytes()).hexdigest() != observed['schema_sha256']):
        raise RuntimeError('C_CURRENT_ACTUAL_SCHEMA_REFERENCE_CHANGED')
    schema = strict_loads(schema_path.read_bytes())
    selections = c_source_selections(schema, d_selection=d_selection, profile=profile)
    directory = profile.root / ('C-scratch-' + uuid.uuid4().hex[:12])
    facts = Facts(directory)
    immutable = {}
    rank_guard = None
    if tail_only:
        rows, rank_guard, old_state, original = c_rank_tail_prefix(profile, request)
        if original['fixture_sha256'] != observed['fixture_sha256']:
            raise RuntimeError('C_RANK_TAIL_ORDINARY_FIXTURE_CHANGED')
        verify_c_sources(old_state, rows, d_source, stored_rows=stored_rows,
            verify_d=verify_d, profile=profile, immutable_billed=immutable)
        facts.save('C-rank-incident-exact-bridge', {
            'rank_bridge_ref': request['rank_bridge_ref'], 'rank_bridge_sha256': request['rank_bridge_sha256'],
            'old_fullrow_sha256': 'f55798df74ecbd390b976fb05ceb5e854a7297aad5975b78d2ba41a349b17035',
            'current_fullrow_sha256': rank_guard['immutable_partner_sha256'],
            'historical_capture_modified': False, 'immutable_reconstructed_from_verified_committed_prefix': True,
            'existing_fee_ids': [row['fee_id'] for row in rows],
            'existing_invoice_ids': [row['invoice_id'] for row in rows if 'invoice_id' in row]})
        save_once(profile.root / 'C-SCRATCH-RANK-TAIL-IN-FLIGHT.json', {
            'directory': str(directory.relative_to(ROOT)), 'rank_bridge_sha256': request['rank_bridge_sha256'],
            'original_directory': original['directory'], 'prefix_replayed': False,
            'first_original_recreated': False, 'funds_allowed': False, 'automatic_retry': False})
    else:
        save_once(profile.root / 'C-SCRATCH-SOURCE-CHAIN-IN-FLIGHT.json', {
            'directory': str(directory.relative_to(ROOT)), 'fixture_sha256': observed['fixture_sha256'],
            'D_source_sha256': request['D_source_sha256'], 'automatic_retry': False})
    final_observation, final_state, final_reference = None, None, None
    def observe(label, rows):
        nonlocal final_observation, final_state, final_reference
        state = capture('scratch', 'C-' + label, selections=selections,
            metadata=False, max_rows=2000, profile=profile)
        result = verify_c_sources(state, rows, d_source, stored_rows=stored_rows,
            verify_d=verify_d, profile=profile, immutable_billed=immutable, rank_guard=rank_guard)
        saved = facts.save('C-independent-' + label, result | {'source': str(state.relative_to(ROOT))})
        final_reference = {'source_ref': str(Path(saved['path']).relative_to(ROOT)),
                           'source_sha256': saved['sha256']}
        final_observation, final_state = result, state
        return result
    def store_original(manager, source, *, label):
        key = uuid.uuid4().hex
        facts.save('C-' + label + '-original-intent', {
            'actor_id': manager.uid, 'invoice_id': source['invoice_id'],
            'store_id': source['store_id'], 'company_id': source['company_id'],
            'stable_original_key': key, 'operation_ref': 'C-' + label + '-original-create',
            'stage': 'BEFORE_DISPATCH', 'automatic_retry': False})
        with manager.client.current_c_target(**final_reference, invoice_id=source['invoice_id'],
                actor_id=manager.uid, active_store_id=manager.store_id,
                create_original=True, request_key=key):
            response = manager.client.request('POST',
                '/ydental/settlement/bill-original/create/%d' % source['invoice_id'],
                form={'revision': manager.revision, 'csrf_token': manager.csrf, 'key': key},
                case_id='C-ATTACHMENT', operation_ref='C-' + label + '-original-create')
        facts.save('C-' + label + '-original-response', {
            'actor_id': manager.uid, 'invoice_id': source['invoice_id'],
            'request_id': response.request_id, 'status': response.status,
            'body_sha256': hashlib.sha256(response.body).hexdigest(), 'commit_claimed': False})
        response.require_status(303)
        # The caller currently owns rows; it will observe immediately below.
        # A bounded separate selection discovers the original by this invoice,
        # rather than predicting or borrowing an existing original ID.
        original_state = capture('scratch', 'C-' + label + '-original-discovery',
            selections=[entry for entry in selections if entry['table'] in {
                'ydental_settlement_bill_original', 'ir_attachment', 'message_attachment_rel'}],
            metadata=False, max_rows=2000, profile=profile)
        found = [row for row in stored_rows(original_state, 'ydental_settlement_bill_original')
                 if row['invoice_id'] == source['invoice_id']]
        if len(found) != 1 or found[0]['actor_id'] != manager.uid:
            raise RuntimeError('C_NORMAL_NEW_ORIGINAL_NOT_INDEPENDENTLY_DISCOVERED')
        original = found[0]
        return {'original_id': original['id'], 'attachment_id': original['attachment_id'],
                'pdf_sha256': original['pdf_sha256'],
                'original_discovery_ref': str(original_state.relative_to(ROOT))}
    with OwnedApplication(marker('scratch', profile), approval=approval,
            product_commit=authority['product_commit'], test_commit=authority['test_commit'],
            action='scratch-service', profile=profile) as app:
        app.start([])
        app.wait_ready(60)
        actors = {}
        for role, reference in fixture['actors'].items():
            path = ROOT / reference['provider_ref']
            if (path.is_symlink() or not path.resolve().is_relative_to(profile.root / 'credentials')
                    or path.stat().st_uid != os.getuid() or stat.S_IMODE(path.stat().st_mode) != 0o600):
                raise RuntimeError('C_PRIVATE_NORMAL_PROVIDER_BOUNDARY_INVALID')
            account = strict_loads(path.read_bytes())
            if account['user_id'] != reference['user_id']:
                raise RuntimeError('C_PRIVATE_NORMAL_PROVIDER_ID_CHANGED')
            actor = Actor('scratch', 'current-C-' + role, account['user_id'], account['login'],
                account['password'], budget=app.budget, directory=directory / (role + '-http'))
            actor.login(fixture['clinics'][0]['store_id'])
            actors[role] = actor
        if tail_only:
            # All current rows and the native rank bridge are checked before
            # the first not-yet-executed upstream action is dispatched.
            observe('tail-current-full-prefix-and-rank-bridge', rows)
            rows, source_manifest = run_current_c_rank_tail(actors['manager'], actors['doctor'],
                fixture['clinics'], facts, d_source, rows, observe=observe, store_original=store_original)
        else:
            observe('before-first-C-source', [])
            rows, source_manifest = run_new_c_fixture_flow(actors['manager'], actors['doctor'],
                fixture['clinics'], facts, d_source, observe=observe,
                new_c_confirmed_fee=new_c_confirmed_fee, recorded_actor=CRecordedActor,
                store_original=store_original)
        read_manifest = current_c_read_manifest(final_state, rows, fixture['clinics'])
        facts.save('C-scratch-actual-read-manifest', read_manifest)
        from s10_lc2_launch import stop
        run_current_c_read_cells(actors['reader'], facts, read_manifest, d_source,
            profile=profile, stop=stop, **final_reference)
        manager = actors['manager']
        run_current_c_error303(manager, facts, observe, rows, profile=profile, stop=stop)
        metadata_response = manager.client.request('POST', '/web/session/get_session_info',
            json_body={'jsonrpc': '2.0', 'id': uuid.uuid4().hex, 'method': 'call', 'params': {}},
            case_id='C-SCOPE', operation_ref='C-manager-native-session-for-log')
        metadata_response.require_status(200)
        native = metadata_response.json()['result']
        metadata = {key: native.get(key) for key in ('uid', 'db', 'is_admin', 'is_system', 'is_internal_user')}
        metadata.update(request_id=metadata_response.request_id, switch_request_id=manager.scope_request_id,
            revision=native.get('user_context', {}).get('ydental_revision'),
            store_id=manager.store_id,
            store_name_matches_independent_source=native.get('ydental_store_name') == read_manifest['cells'][0]['store_name'])
        facts.save('C-manager-native-session-for-log', metadata)
        if (metadata['uid'] != manager.uid or metadata['db'] != profile.database
                or metadata['is_admin'] is not False or metadata['is_system'] is not False
                or metadata['is_internal_user'] is not True or metadata['revision'] != manager.revision
                or metadata['store_id'] != fixture['clinics'][0]['store_id']
                or not metadata['store_name_matches_independent_source']):
            raise RuntimeError('C_MANAGER_ACTUAL_NATIVE_SESSION_FOR_ROLLBACK_LOG_NOT_PROVEN')
        observe('all-C-read-cells-complete', rows)
        app.check()
    closed = closed_log_report(app)
    terminal = observe('terminal-after-source-service-exit', rows)
    result = {'status': 'C_NEW_UNFUNDED_SOURCES_AND_SCOPE_CELLS_EXECUTED_INDEPENDENT_ACCEPTANCE_PENDING',
        'directory': str(directory.relative_to(ROOT)), 'sources': rows,
        'manifest': terminal, 'owned_service_closed': True,
        'native_exit_code': app.process.returncode, 'diagnostic_records': closed['record_count'],
        'C_fund_dispatches': 0, 'D_funds_globally_unique': True}
    save_once(profile.root / 'C-SCRATCH-SOURCE-CHAIN-RETURNED.json', result)
    return result


def run_log_rollback_pair(profile, approval, authority, requested_path):
    """Two native scratch MODEL processes, each fully rolled back; no new funds."""
    from s10_lc2_cases import capture, run_fixture, stored_rows
    from s10_lc2_log_rollback import _TABLES
    for action in ('LOG-06', 'LOG-10', 'LOG-12'):
        profile.require_action(action)
    request, observed = scratch_requested(profile, requested_path)
    model = observed['log_model_manifest']
    d = strict_loads((profile.root / 'D-CHAIN-COMPLETE.json').read_bytes())
    if (observed.get('validation_status') != 'CURRENT_LOG_ROLLBACK_NEW_FEE_VERIFIED'
            or any(observed.get(key) is not True for key in ('normal_upstream_source_verified',
                'ordinary_actor_verified', 'native_session_info_verified', 'unbilled_new_fee_verified'))
            or model.get('d_fee_id') != d['source_ids']['fee_id']
            or model.get('fee_id') == model.get('d_fee_id')
            or set(model) != {'actor_id', 'session_id', 'revision', 'store_id', 'fee_id', 'd_fee_id'}):
        raise RuntimeError('LOG_ROLLBACK_ACTUAL_SEPARATE_FIXTURE_NOT_PROVEN')
    save_once(profile.root / 'LOG-ROLLBACK-PAIR-IN-FLIGHT.json', {
        'manifest_sha256': request['manifest_sha256'], 'actor_id': model['actor_id'],
        'fee_id': model['fee_id'], 'protected_d_fee_id': model['d_fee_id'],
        'fixture_commits': 0, 'automatic_retry': False})
    operation_ref = 'LOG06-' + uuid.uuid4().hex
    selections = [{'table': name, 'columns': ['id'], 'row_digest': True} for name in _TABLES]
    def independently_stored(label):
        destination = capture('scratch', label + '-' + operation_ref, selections=selections,
                              max_rows=2000, profile=profile)
        rows = {name: stored_rows(destination, name) for name in _TABLES}
        return destination, rows
    before_dir, before = independently_stored('log-before')
    results = []
    for mode in ('ON', 'OFF'):
        save_once(profile.root / ('LOG-ROLLBACK-' + mode + '-INTENT.json'), {
            'operation_ref': operation_ref, 'diagnostics': mode, 'actor_id': model['actor_id'],
            'fee_id': model['fee_id'], 'd_fee_id': model['d_fee_id'], 'fixture_commits': 0})
        output = run_fixture('scratch', approval=approval, product_commit=authority['product_commit'],
            test_commit=authority['test_commit'], mode='log-rollback-only', profile=profile,
            manifest=model | {'diagnostics': mode, 'operation_ref': operation_ref})['safe']
        # Store the first actual process result before any postprocessing/RO.
        save_once(profile.root / ('LOG-ROLLBACK-' + mode + '-PROCESS-RESULT.json'), output)
        after_dir, after = independently_stored('log-after-' + mode.lower())
        if after != before:
            raise RuntimeError('LOG_ROLLBACK_INDEPENDENT_COMMITTED_ROWS_CHANGED')
        directory = ROOT / output['application_directory']
        pid = output['owned_process_pid']
        run = profile.run_root / profile.database
        files = list((run / 'diagnostics').glob('events-' + str(pid) + '-*.jsonl'))
        record_count = sum(len(path.read_bytes().splitlines()) for path in files)
        metrics = {'diagnostic_json_bytes': sum(path.stat().st_size for path in files),
            'diagnostic_json_records': record_count, 'model_elapsed_ns': output['elapsed_ns'],
            'native_exit_code': output['native_exit_code'],
            'independent_before_ref': str(before_dir.relative_to(ROOT)),
            'independent_after_ref': str(after_dir.relative_to(ROOT)),
            'independent_committed_rows_same': True}
        if (output.get('mode') != mode or output.get('fixture_commits') != 0
                or any(output.get(key) is not True for key in ('rollback_returned', 'cursor_close_returned',
                    'successful_bill_rolled_back', 'failed_bill_rolled_back'))
                or output.get('native_exit_code') != 0
                or mode == 'OFF' and (files or not (directory / 'optional-json-absence.json').is_file())
                or mode == 'ON' and (not files or record_count <= 0)):
            raise RuntimeError('LOG_ROLLBACK_NATIVE_PROCESS_CONTRACT_NOT_OBSERVED')
        result = output | {'metrics': metrics,
            'json_integrity_status': 'SEALED_VALIDATED_ON' if mode == 'ON' else 'EXPECTED_ABSENT_NOT_INTEGRITY_PASS'}
        save_once(profile.root / ('LOG-ROLLBACK-' + mode + '-VERIFIED.json'), result)
        results.append(result)
    economic_keys = ('success', 'version_conflict', 'day_closed', 'mandatory_audit_failure', 'isolated_program_failure')
    if any(results[0].get(key) != results[1].get(key) for key in economic_keys):
        raise RuntimeError('LOG_ON_OFF_ACTUAL_ECONOMIC_OR_NATIVE_EXCEPTION_OUTCOMES_DIFFER')
    result = {'status': 'REAL_MODEL_ON_OFF_ROLLBACK_INDEPENDENT_COMMITTED_FACTS_EQUAL',
        'actor_id': model['actor_id'], 'fee_id': model['fee_id'], 'd_fee_id': model['d_fee_id'],
        'economic_results_equal': True, 'mandatory_audit_failure_propagated_both': True,
        'modes': [{'mode': row['mode'], 'metrics': row['metrics'],
                   'model_trace_id': row['model_trace_id']} for row in results],
        'http_or_financial_competition_claimed': False, 'fixture_commits': 0}
    save_once(profile.root / 'LOG-ROLLBACK-PAIR-COMPLETE.json', result)
    return result


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


def run_c_main(profile, approval, authority, requested_path, *, tail_only=False):
    """Current new-reader permissions and native content, using normal S01 actions."""
    import psycopg2
    from s10_lc2_browser import Credentials, _DRIVER_ENV_KEYS, run_current_revoked_browser
    from s10_lc2_cases import Actor, Facts, main_c, marker, stored_rows
    from s10_lc2_main_a_original_runner import existing_reader5
    if tail_only:
        profile.require_action('c-main-tail')
    for action in ('C-SCOPE', 'C-ATTACHMENT', 'C-TOKEN', 'C-REVOKED-PAGE'):
        profile.require_action(action)
    request = strict_loads(requested_path.read_bytes())
    if tail_only:
        c_renderer_resolution(profile)
        repair = ROOT / request['repair_post_ro_ref']
        if repair.is_symlink() or not repair.resolve().is_relative_to(profile.root):
            raise RuntimeError('C_TAIL_REPAIR_POST_RO_REFERENCE_INVALID')
        repair_raw = repair.read_bytes()
        if hashlib.sha256(repair_raw).hexdigest() != request['repair_post_ro_sha256']:
            raise RuntimeError('C_TAIL_REPAIR_POST_RO_BYTES_CHANGED')
        repair_state = strict_loads(repair_raw)
        if (repair_state.get('database') != profile.database or repair_state.get('oid') != 2144129
                or any(repair_state.get(key) is not True for key in ('rollback_returned', 'connection_closed',
                    'report_parameters_expected', 'font_view_loaded'))):
            raise RuntimeError('C_TAIL_REPAIR_NOT_INDEPENDENTLY_VERIFIED')
    manifest_path = ROOT / request['manifest_ref']
    if manifest_path.is_symlink() or not manifest_path.resolve().is_relative_to(profile.root):
        raise RuntimeError('C_MANIFEST_REFERENCE_INVALID')
    raw = manifest_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != request['manifest_sha256']:
        raise RuntimeError('C_MANIFEST_BYTES_CHANGED')
    manifest = strict_loads(raw)
    foreign = manifest.get('foreign_stores', [])
    if (manifest.get('actor_id') != 59 or manifest.get('manager_id') != 5
            or manifest.get('manager_legal_business_management') is not True
            or manifest.get('database') != profile.database or manifest.get('oid') != 2144129
            or manifest.get('rollback_returned') is not True or manifest.get('connection_closed') is not True
            or type(manifest.get('store1_membership_id')) is not int
            or manifest.get('original161_mail_links') != []
            or type(foreign) is not list or len(foreign) > 2
            or len({row.get('store_id') for row in foreign}) != len(foreign)
            or len(foreign) < 2 and manifest.get('foreign_scope_status') != 'PARTIAL_NO_NONEMPTY_MAIN_SOURCE'
            or len(foreign) == 2 and {row.get('company_id') == 1 for row in foreign} != {False, True}
            or any(type(row.get('store_id')) is not int or row['store_id'] == 1
                   or type(row.get('own_patient_id')) is not int or row['own_patient_id'] <= 0
                   or type(row.get('own_invoice_id')) is not int or row['own_invoice_id'] <= 1
                   or type(row.get('patient1_related')) is not bool
                   or any(type(row.get('patient1_visible_' + kind + '_ids')) is not list
                          for kind in ('invoice', 'payment', 'refund'))
                   or row.get('patient1_related') and (any(type(row.get('patient1_visible_' + kind + '_ids')) is not list
                          for kind in ('fee', 'event')) or type(row.get('patient1_visible_invoices')) is not list
                          or type(row.get('store_visible_close_ids')) is not list)
                   or row.get('company_id') not in manifest.get('manager_allowed_company_ids', []) for row in foreign)):
        raise RuntimeError('C_NONEMPTY_SCOPE_OR_LEGAL_TOKEN_APPLICABILITY_NOT_PROVEN')
    directory = profile.root / ('C-main-' + uuid.uuid4().hex[:12])
    facts = Facts(directory)
    if tail_only:
        prior = profile.root / 'C-MAIN-IN-FLIGHT.json'
        if not prior.is_file() or (profile.root / 'C-MAIN-COMPLETE.json').exists():
            raise RuntimeError('C_TAIL_FIRST_FAILURE_NOT_PRESERVED')
        save_once(profile.root / 'C-MAIN-TAIL-IN-FLIGHT.json', {'directory': str(directory.relative_to(ROOT)),
            'actor_id': 59, 'automatic_retry': False, 'first_intent_sha256': hashlib.sha256(prior.read_bytes()).hexdigest(),
            'repair_post_ro_sha256': request['repair_post_ro_sha256'], 'prefix_replayed': False})
    else:
        save_once(profile.root / 'C-MAIN-IN-FLIGHT.json', {'directory': str(directory.relative_to(ROOT)),
            'actor_id': 59, 'automatic_retry': False, 'scope_manifest_sha256': request['manifest_sha256']})
    run = profile.run_root / profile.database
    budget = PackageBudget(profile.root, profile=profile)
    memberships = {1: manifest['store1_membership_id']}
    connection_args = credentials()
    def verify_levels(label, levels, store=1):
        destination = directory / ('permission-' + label)
        collect_selection(psycopg2.connect, connection_args, database=profile.database, expected_oid=2144129,
            selections=[{'table': 'ydental_access_membership', 'columns': [
                'id', 'ydental_user_id', 'ydental_store_id', 'ydental_employee_id', 'active'],
                'ids': [memberships[store]]}, {'table': 'ydental_access_grant', 'columns': [
                'id', 'ydental_membership_id', 'ydental_category', 'ydental_level'],
                'equals': {'ydental_membership_id': memberships[store]}}],
            directory=destination, budget=budget, allowed_target_names=[profile.database],
            target_directory=run, config_path=run / 'odoo.conf', max_rows=64)
        member = stored_rows(destination, 'ydental_access_membership')
        actual = {row['ydental_category']: row['ydental_level']
                  for row in stored_rows(destination, 'ydental_access_grant')}
        if (len(member) != 1 or member[0]['ydental_user_id'] != 59
                or member[0]['ydental_store_id'] != store or not member[0]['active']
                or any(actual.get(category, 'none') != level for category, level in levels.items())):
            raise RuntimeError('C_NORMAL_PERMISSION_COMMIT_NOT_INDEPENDENTLY_VERIFIED')
        facts.save('permission-' + label, {'actor_id': 59, 'store_id': store, 'levels': levels,
            'state_source': str(destination.relative_to(ROOT)), 'layer': 'INDEPENDENT_COMMITTED_RO'})
    reference, reader_credentials = current_reader(profile)
    manager_credentials = existing_reader5()
    with OwnedApplication(marker('main', profile), approval=approval,
            product_commit=authority['product_commit'], test_commit=authority['test_commit'],
            action='main-service', profile=profile) as app:
        app.start([])
        app.wait_ready(60)
        manager = Actor('main', 'C-normal-manager', 5, manager_credentials['login'],
            manager_credentials['password'], budget=budget, directory=directory / 'manager-http')
        reader = Actor('main', 'C-normal-new-reader', 59, reader_credentials['login'],
            reader_credentials['password'], budget=budget, directory=directory / 'reader-http')
        manager.login(1)
        reader.login(1)
        # Native placeholder bytes are a public installed core resource, not a fabricated response.
        placeholder_path = ROOT.parent / 'addons/web/static/img/placeholder.png'
        def scope_actors():
            for item in foreign:
                store = item['store_id']
                join = manager.action('access', 'join', {'user_id': 59, 'store_id': store}, case='C-SCOPE')
                memberships[store] = join['membership_id']
                levels = {'settlement': 'read', 'export': 'write'}
                manager.action('access', 'grant', {'user_id': 59, 'store_id': store, 'levels': levels}, case='C-SCOPE')
                verify_levels('foreign-' + str(store), levels, store)
                reader.refresh()
                reader.switch(store)
                yield reader, store, item['own_patient_id'], item
        main_c(manager, reader, None, placeholder_path.read_bytes(), facts, 161, scope_actors(),
            dynamic_pdf_admitted=True, profile=profile, verify_permission=verify_levels, tail_only=tail_only,
            token_applicability={'valid_token': 'NOT_APPLICABLE_NO_CURRENT_LEGAL_ISSUER',
                'mail_links': [], 'scope_manifest_sha256': request['manifest_sha256'],
                'source': 'ydental_settlement_bill_original has no portal.mixin; no linked mail.message producer'})
        reader.refresh()
        reader.switch(1)
        def set_reader(label, levels):
            manager.action('access', 'grant', {'user_id': 59, 'store_id': 1, 'levels': levels}, case='C-REVOKED-PAGE')
            verify_levels(label, levels)
        async def revoke():
            set_reader('browser-revoked', {'settlement': 'none', 'export': 'none'})
        async def restore():
            set_reader('browser-restored', {'settlement': 'read', 'export': 'write'})
        ambient = dict(os.environ)
        try:
            os.environ.clear()
            os.environ.update({key: value for key, value in ambient.items() if key in _DRIVER_ENV_KEYS})
            browser = asyncio.run(run_current_revoked_browser(base_url='http://127.0.0.1:18410',
                database=profile.database, owned_targets={profile.database: 'http://127.0.0.1:18410'},
                budget=budget, directory=directory / 'browser-revoked',
                credentials=Credentials(reader_credentials['login'], reader_credentials['password']),
                reader_id=59, store_id=1, patient_id=1, invoice_id=1, original_id=1,
                revoke_reader=revoke, restore_reader=restore))
        finally:
            os.environ.clear()
            os.environ.update(ambient)
        facts.save('C-browser-revoked-result', browser)
        app.check()
    from s10_lc2_cases import closed_log_report
    logs = closed_log_report(app)
    facts.save('C-application-closed-log-seal', {'diagnostic_records': logs['record_count'],
        'application_directory': str(app.directory.relative_to(ROOT)), 'owned_service_exited': True})
    result = {'status': 'C_MAIN_EXECUTED_INDEPENDENT_ACCEPTANCE_PENDING', 'actor_id': 59,
        'directory': str(directory.relative_to(ROOT)), 'application_directory': str(app.directory.relative_to(ROOT)),
        'foreign_nonempty_store_cases': len(foreign),
        'foreign_scope_status': 'EXECUTED_MAIN_SAME_AND_OTHER_COMPANY' if len(foreign) == 2 else 'PARTIAL_NO_NONEMPTY_MAIN_SOURCE',
        'family_nonempty_scratch_cases': 'NOT_RUN_SEPARATE_AFTER_D', 'valid_token': 'N/A_NO_CURRENT_LEGAL_ISSUER'}
    save_once(profile.root / ('C-MAIN-TAIL-COMPLETE.json' if tail_only else 'C-MAIN-COMPLETE.json'),
              result | {'prefix_replayed': False} if tail_only else result)
    return result


def repair_upgrade_main(profile, approval, authority, requested_path, *, font_repair=False):
    """Load the ordinary export-link repair; final E-MAIN remains separate."""
    from s10_lc2_cases import closed_log_report, marker
    from s10_lc2_launch import keep_primary
    profile.require_action('repair-upgrade-main-font' if font_repair else 'repair-upgrade-main')
    if font_repair:
        c_renderer_resolution(profile)
    request = strict_loads(requested_path.read_bytes())
    before = ROOT / request['manifest_ref']
    if before.is_symlink() or not before.resolve().is_relative_to(profile.root):
        raise RuntimeError('REPAIR_UPGRADE_BEFORE_REFERENCE_INVALID')
    raw = before.read_bytes()
    if hashlib.sha256(raw).hexdigest() != request['manifest_sha256']:
        raise RuntimeError('REPAIR_UPGRADE_BEFORE_BYTES_CHANGED')
    protection = strict_loads(raw)
    if (protection.get('database') != profile.database or protection.get('oid') != 2144129
            or protection.get('rollback_returned') is not True or protection.get('connection_closed') is not True
            or font_repair and protection.get('report_parameters_expected') is not True):
        raise RuntimeError('REPAIR_UPGRADE_ACTUAL_BEFORE_TARGET_NOT_PROVEN')
    save_once(profile.root / ('FONT-REPAIR-UPGRADE-MAIN-IN-FLIGHT.json' if font_repair else 'REPAIR-UPGRADE-MAIN-IN-FLIGHT.json'), {
        'before_ref': request['manifest_ref'], 'before_sha256': request['manifest_sha256'],
        'product_commit': authority['product_commit'], 'test_commit': authority['test_commit'],
        'target': profile.database, 'automatic_retry': False, 'final_E_MAIN_claimed': False})
    app = OwnedApplication(marker('main', profile), approval=approval,
        product_commit=authority['product_commit'], test_commit=authority['test_commit'],
        action='main-upgrade', profile=profile)
    try:
        app.start(['--stop-after-init', '--load-language=zh_CN', '-u', 'ydental_settlement'])
    except BaseException as error:
        primary = keep_primary(app.directory, error, stage='repair_upgrade_start')
        exit_path = app.directory / 'parent-exit.tsv'
        if not exit_path.exists() or not any(line.startswith(b'parent.end\t') for line in exit_path.read_bytes().splitlines()):
            app.close(primary=primary)
        raise
    # wait owns normal/error cleanup; a context manager would close it twice.
    code = app.wait(1200)
    if code != 0:
        raise RuntimeError('REPAIR_UPGRADE_FAILED_KEEP_SAME_DATABASE_AND_FILES')
    logs = closed_log_report(app)
    result = {'status': 'REPAIR_UPGRADE_EXIT_ZERO_INDEPENDENT_POST_RO_REQUIRED',
        'exit_code': code, 'target': profile.database, 'scope': 'ydental_settlement_only',
        'application_directory': str(app.directory.relative_to(ROOT)),
        'diagnostic_records': logs['record_count'], 'final_E_MAIN_claimed': False}
    save_once(profile.root / ('FONT-REPAIR-UPGRADE-MAIN-RESULT.json' if font_repair else 'REPAIR-UPGRADE-MAIN-RESULT.json'), result)
    return result



def run_final_s10_upgrade(profile, approval, authority, requested_path):
    """Final data-bearing upgrade of exactly one already verified current target."""
    from s10_lc2_cases import marker, closed_log_report
    from s10_lc2_launch import keep_primary
    profile.require_action('E-UPGRADE-S10-ONLY')
    role = profile.target_role
    expected_oid = 2144129 if role == 'main' else 2144130
    request = strict_loads(requested_path.read_bytes())
    before = ROOT / request['manifest_ref']
    if before.is_symlink() or not before.resolve().is_relative_to(profile.root):
        raise RuntimeError('FINAL_E_BEFORE_REFERENCE_INVALID')
    raw = before.read_bytes()
    if hashlib.sha256(raw).hexdigest() != request['manifest_sha256']:
        raise RuntimeError('FINAL_E_BEFORE_REFERENCE_CHANGED')
    state = strict_loads(raw)
    if (state.get('database') != profile.database or state.get('oid') != expected_oid
            or state.get('cluster') != '7694897083368259627'
            or state.get('product_commit') != authority['product_commit']
            or any(state.get(key) is not True for key in ('rollback_returned', 'connection_closed',
                'protected_baseline_complete', 'predecessor_evidence_complete'))
            or role == 'scratch' and state.get('unique_D_native_accounting_verified') is not True):
        raise RuntimeError('FINAL_E_ACTUAL_DATA_AND_PREREQUISITES_NOT_PROVEN')
    tag = 'E-MAIN' if role == 'main' else 'E-D'
    save_once(profile.root / (tag + '-IN-FLIGHT.json'), {
        'before_ref': request['manifest_ref'], 'before_sha256': request['manifest_sha256'],
        'product_commit': authority['product_commit'], 'test_commit': authority['test_commit'],
        'target': profile.database, 'automatic_retry': False, 'scope': 'ydental_settlement_only'})
    app = OwnedApplication(marker(role, profile), approval=approval,
        product_commit=authority['product_commit'], test_commit=authority['test_commit'],
        action=role + '-upgrade', profile=profile)
    try:
        app.start(['--stop-after-init', '--load-language=zh_CN', '-u', 'ydental_settlement'])
    except BaseException as error:
        primary = keep_primary(app.directory, error, stage=tag + '_upgrade_start')
        exit_path = app.directory / 'parent-exit.tsv'
        if not exit_path.exists() or not any(line.startswith(b'parent.end\t') for line in exit_path.read_bytes().splitlines()):
            app.close(primary=primary)
        raise
    code = app.wait(1200)
    if code != 0:
        raise RuntimeError('FINAL_E_UPGRADE_FAILED_PRESERVE_SAME_DATABASE_AND_FILES')
    logs = closed_log_report(app)
    result = {'status': 'UPGRADE_EXIT_ZERO_INDEPENDENT_POST_RO_AND_REGRESSION_REQUIRED',
        'case': tag, 'exit_code': code, 'target': profile.database,
        'product_commit': authority['product_commit'], 'test_commit': authority['test_commit'],
        'application_directory': str(app.directory.relative_to(ROOT)),
        'diagnostic_records': logs['record_count'], 'no_financial_or_document_action_replayed': True}
    save_once(profile.root / (tag + '-UPGRADE-RESULT.json'), result)
    return result


def run_final_scratch_read_only(profile, approval, authority, requested_path):
    """Two existing-D read GETs after E-D; no call to any money/fixture flow."""
    from decimal import Decimal
    from lxml import html
    from s10_lc2_cases import Actor, Facts, closed_log_report, marker
    profile.require_action('E-AFFECTED-REGRESSION')
    request, observed = scratch_requested(profile, requested_path)
    upgrade = strict_loads((profile.root / 'E-D-UPGRADE-RESULT.json').read_bytes())
    fixture_raw = (profile.root / 'D-fixture-public-identities.json').read_bytes()
    if (observed.get('product_commit') != authority['product_commit']
            or upgrade.get('exit_code') != 0 or upgrade.get('product_commit') != authority['product_commit']
            or observed.get('D_fixture_sha256') != hashlib.sha256(fixture_raw).hexdigest()
            or any(observed.get(key) is not True for key in ('normal_modules_verified',
                'old_protected_state_preserved', 'unique_D_native_accounting_verified',
                'ordinary_D_manager_verified'))):
        raise RuntimeError('E_D_POST_UPGRADE_AND_ORDINARY_D_OWNER_NOT_VERIFIED')
    fixture = strict_loads(fixture_raw)
    reference = fixture['actors']['manager']
    provider = ROOT / reference['provider_ref']
    if (reference['user_id'] != 6 or fixture['store_id'] != 1
            or provider.is_symlink() or not provider.resolve().is_relative_to(profile.root / 'credentials')
            or provider.stat().st_uid != os.getuid() or stat.S_IMODE(provider.stat().st_mode) != 0o600):
        raise RuntimeError('E_D_EXISTING_ORDINARY_PROVIDER_BOUNDARY_INVALID')
    account = strict_loads(provider.read_bytes())
    if account['user_id'] != 6:
        raise RuntimeError('E_D_ORDINARY_D_MANAGER_ID_CHANGED')
    facts = Facts(profile.root / ('E-D-read-only-' + uuid.uuid4().hex[:12]))
    save_once(profile.root / 'E-D-READ-ONLY-IN-FLIGHT.json', {
        'before_sha256': request['manifest_sha256'], 'directory': str(facts.directory.relative_to(ROOT)),
        'actor_id': 6, 'patient_id': 1, 'refund_id': 1, 'fund_actions_allowed': False})
    with OwnedApplication(marker('scratch', profile), approval=approval,
            product_commit=authority['product_commit'], test_commit=authority['test_commit'],
            action='scratch-service', profile=profile) as app:
        app.start([])
        app.wait_ready(60)
        actor = Actor('scratch', 'E-D-existing-reader', 6, account['login'], account['password'],
            budget=app.budget, directory=facts.directory / 'read-http')
        actor.login(1)
        response = actor.client.request('POST', '/web/session/get_session_info',
            json_body={'jsonrpc': '2.0', 'id': uuid.uuid4().hex, 'method': 'call', 'params': {}},
            case_id='E-AFFECTED-REGRESSION')
        response.require_status(200)
        info = response.json()['result']
        if (info.get('uid') != 6 or info.get('db') != profile.database
                or info.get('is_admin') is not False or info.get('is_system') is not False
                or info.get('is_internal_user') is not True
                or info.get('user_context', {}).get('ydental_revision') != actor.revision):
            raise RuntimeError('E_D_NATIVE_ORDINARY_IDENTITY_NOT_PROVEN')
        page = actor.client.request('GET', '/ydental/settlement?patient_id=1', case_id='E-AFFECTED-REGRESSION')
        facts.save('E-D-workbench-first-response', {'status': page.status, 'request_id': page.request_id,
            'body_sha256': hashlib.sha256(page.body).hexdigest(), 'raw_body_retained': False})
        page.require_status(200)
        tree = html.fromstring(page.body)
        invoices = [[''.join(td.itertext()).strip() for td in tr.xpath('./td')]
                    for tr in tree.xpath('//section[@name="settled-bills"]//tbody/tr')]
        paragraphs = tree.xpath('//section[h2[text()="线下付款与退款"]]/div/p')
        payments = [p.xpath('./span/text()') for p in paragraphs if ''.join(p.itertext()).strip().startswith('付款')]
        refunds = [p.xpath('./span/text()') for p in paragraphs if ''.join(p.itertext()).strip().startswith('退款')]
        valid = (len(invoices) == 1 and len(invoices[0]) >= 5 and invoices[0][0] == '1'
            and Decimal(invoices[0][3].replace(',', '')) == 6 and Decimal(invoices[0][4].replace(',', '')) == 0
            and len(payments) == len(refunds) == 1 and len(payments[0]) >= 3 and len(refunds[0]) >= 3
            and payments[0][0].strip() == refunds[0][0].strip() == '1'
            and Decimal(payments[0][2].replace(',', '')) == 6 and Decimal(refunds[0][1].replace(',', '')) == 2
            and refunds[0][2].strip() == 'done')
        facts.save('E-D-workbench-content', {'exact_existing_D_ids_and_amounts_match': valid,
            'invoice_id': 1, 'payment_id': 1, 'refund_id': 1,
            'received': 6 if valid else None, 'refunded': 2 if valid else None,
            'net_received': 4 if valid else None, 'pending_refund': 0 if valid else None})
        if not valid:
            raise RuntimeError('E_D_WORKBENCH_EXISTING_SIX_TWO_STATE_MISMATCH')
        pdf = actor.client.request('GET', '/ydental/settlement/pdf/refund/1',
            case_id='E-AFFECTED-REGRESSION', artifact_kind='pdf')
        facts.save('E-D-refund-PDF-first-response', {'status': pdf.status, 'request_id': pdf.request_id,
            'sha256': hashlib.sha256(pdf.body).hexdigest(), 'bytes': len(pdf.body)})
        pdf.require_status(200)
        if not pdf.body.startswith(b'%PDF-'):
            raise RuntimeError('E_D_REFUND_DOCUMENT_NOT_PDF')
        app.check()
    logs = closed_log_report(app)
    result = {'status': 'E_D_READ_ONLY_EXECUTED_PDF_AND_TERMINAL_RO_ACCEPTANCE_PENDING',
        'directory': str(facts.directory.relative_to(ROOT)), 'actor_id': 6,
        'native_exit_code': app.process.returncode, 'owned_service_exited': True,
        'diagnostic_records': logs['record_count'], 'fund_actions_replayed': False}
    save_once(profile.root / 'E-D-READ-ONLY-RETURNED.json', result)
    return result


def run_log_ui_read(profile, approval, authority, requested_path):
    from s10_lc2_browser import Credentials, _DRIVER_ENV_KEYS, run_current_log03_browser
    from s10_lc2_cases import Actor, Facts, closed_log_report, marker
    from s10_lc2_launch import stop
    for action in ('LOG-03', 'C-ATTACHMENT'):
        profile.require_action(action)
    if profile.target_role != 'main':
        raise RuntimeError('LOG03_EXISTING_MAIN_NEW_READER_ONLY')
    request = strict_loads(requested_path.read_bytes())
    before = ROOT / request['manifest_ref']
    if (before.is_symlink() or not before.resolve().is_relative_to(profile.root)
            or hashlib.sha256(before.read_bytes()).hexdigest() != request['manifest_sha256']):
        raise RuntimeError('LOG03_ACTUAL_READER_REFERENCE_INVALID')
    observed = strict_loads(before.read_bytes())
    if (observed.get('database') != profile.database or observed.get('oid') != 2144129
            or observed.get('reader_id') != 59 or type(observed.get('reader_partner_id')) is not int
            or any(observed.get(key) is not True for key in ('rollback_returned', 'connection_closed',
                'ordinary59_retained', 'original161_preserved', 'native_audit228_exists'))):
        raise RuntimeError('LOG03_ACTUAL_ORDINARY_READER_AND_NONEMPTY_TARGETS_NOT_PROVEN')
    _, account = current_reader(profile)
    facts = Facts(profile.root / ('LOG03-main-' + uuid.uuid4().hex[:12]))
    save_once(profile.root / 'LOG03-MAIN-IN-FLIGHT.json', {
        'before_sha256': request['manifest_sha256'], 'directory': str(facts.directory.relative_to(ROOT)),
        'reader_id': 59, 'attachment_id': 161, 'audit_id': 228, 'automatic_retry': False})
    with OwnedApplication(marker('main', profile), approval=approval,
            product_commit=authority['product_commit'], test_commit=authority['test_commit'],
            action='main-service', profile=profile) as app:
        app.start([])
        app.wait_ready(60)
        reader = Actor('main', 'current-LOG03-reader', 59, account['login'], account['password'],
            budget=app.budget, directory=facts.directory / 'reader-http')
        reader.login(1)
        response = reader.client.request('POST', '/web/session/get_session_info',
            json_body={'jsonrpc': '2.0', 'id': uuid.uuid4().hex, 'method': 'call', 'params': {}},
            case_id='LOG-03', operation_ref='current-LOG03-native-session-info')
        response.require_status(200)
        info = response.json()['result']
        session = {key: info.get(key) for key in ('uid', 'db', 'partner_id', 'is_admin', 'is_system', 'is_internal_user')}
        session.update(request_id=response.request_id,
            revision=info.get('user_context', {}).get('ydental_revision'),
            switch_request_id=reader.scope_request_id, requested_store_id=1)
        facts.save('LOG03-native-session-metadata', session)
        if (session['uid'] != 59 or session['db'] != profile.database
                or session['partner_id'] != observed['reader_partner_id']
                or session['is_admin'] is not False or session['is_system'] is not False
                or session['is_internal_user'] is not True or session['revision'] != reader.revision):
            raise RuntimeError('LOG03_NATIVE_AUTHENTICATED_IDENTITY_OR_SCOPE_MISMATCH')
        rpc_response, result = reader.rpc('ir.attachment', 'search_read',
            [[['id', '=', 161]], ['id', 'raw']], case='C-ATTACHMENT')
        value = result.get('result')
        filtered = {'request_id': rpc_response.request_id, 'actor_id': 59, 'store_id': 1,
            'model': 'ir.attachment', 'method': 'search_read', 'existing_target_id': 161,
            'http_status': rpc_response.status, 'result_type': type(value).__name__,
            'result_count': len(value) if type(value) is list else None,
            'response_sha256': hashlib.sha256(rpc_response.body).hexdigest(),
            'raw_response_retained': False, 'layer': 'REAL_RPC_FILTERED_EMPTY'}
        facts.save('C-existing-attachment161-filtered-empty', filtered)
        if type(value) is not list or value != []:
            stop('LOG03_PROTECTED_ATTACHMENT_RPC_UNEXPECTED_RESULT', profile=profile,
                 request_id=rpc_response.request_id)
            raise RuntimeError('LOG03_PROTECTED_ATTACHMENT_RPC_NOT_FILTERED_EMPTY')
        ambient = dict(os.environ)
        try:
            os.environ.clear()
            os.environ.update({key: value for key, value in ambient.items() if key in _DRIVER_ENV_KEYS})
            browser = asyncio.run(run_current_log03_browser(
                base_url='http://127.0.0.1:18410', database=profile.database,
                owned_targets={profile.database: 'http://127.0.0.1:18410'},
                budget=app.budget, directory=facts.directory / 'native-browser',
                credentials=Credentials(account['login'], account['password']),
                reader_id=59, reader_partner_id=session['partner_id'], store_id=1))
        finally:
            os.environ.clear()
            os.environ.update(ambient)
        facts.save('LOG03-native-browser-result', browser)
        app.check()
    logs = closed_log_report(app)
    result = {'status': 'LOG03_AND_ATTACHMENT_RPC_EXECUTED_INDEPENDENT_ACCEPTANCE_PENDING',
        'actor_id': 59, 'directory': str(facts.directory.relative_to(ROOT)),
        'application_directory': str(app.directory.relative_to(ROOT)),
        'owned_service_exited': True, 'native_exit_code': app.process.returncode,
        'diagnostic_records': logs['record_count'], 'attachment_filtered_empty_request_id': rpc_response.request_id}
    save_once(profile.root / 'LOG03-MAIN-RETURNED.json', result)
    return result


def run_final_original_ui(profile, approval, authority, requested_path):
    from s10_lc2_browser import Credentials, _DRIVER_ENV_KEYS, run_main_a_browser
    from s10_lc2_cases import Facts, ORIGINAL_SHA, closed_log_report, marker
    from s10_lc2_main_a_original_runner import existing_reader5
    profile.require_action('E-AFFECTED-REGRESSION')
    if profile.target_role != 'main':
        raise RuntimeError('E_POST_ORIGINAL_UI_EXISTING_MAIN_ONLY')
    request = strict_loads(requested_path.read_bytes())
    path = ROOT / request['manifest_ref']
    if (path.is_symlink() or not path.resolve().is_relative_to(profile.root)
            or hashlib.sha256(path.read_bytes()).hexdigest() != request['manifest_sha256']):
        raise RuntimeError('E_POST_ORIGINAL_UI_INDEPENDENT_BEFORE_REFERENCE_INVALID')
    observed = strict_loads(path.read_bytes())
    if (observed.get('database') != profile.database or observed.get('oid') != 2144129
            or observed.get('product_commit') != authority['product_commit']
            or any(observed.get(key) is not True for key in ('rollback_returned', 'connection_closed',
                'normal_modules_verified', 'old_protected_state_preserved', 'original161_preserved'))):
        raise RuntimeError('E_POST_UPGRADE_ORIGINAL_PROTECTION_NOT_INDEPENDENTLY_VERIFIED')
    upgrade = strict_loads((profile.root / 'E-MAIN-UPGRADE-RESULT.json').read_bytes())
    if upgrade.get('exit_code') != 0 or upgrade.get('product_commit') != authority['product_commit']:
        raise RuntimeError('E_POST_ORIGINAL_REQUIRES_ACTUAL_MATCHING_S10_ONLY_UPGRADE')
    facts = Facts(profile.root / ('E-main-original-post-' + uuid.uuid4().hex[:12]))
    save_once(profile.root / 'E-MAIN-ORIGINAL-POST-IN-FLIGHT.json', {
        'before_sha256': request['manifest_sha256'], 'directory': str(facts.directory.relative_to(ROOT)),
        'reader_id': 5, 'original_id': 1, 'original_sha256': ORIGINAL_SHA,
        'upgrade_product_commit': upgrade['product_commit'], 'automatic_retry': False})
    account = existing_reader5()
    with OwnedApplication(marker('main', profile), approval=approval,
            product_commit=authority['product_commit'], test_commit=authority['test_commit'],
            action='main-service', profile=profile) as app:
        app.start([])
        app.wait_ready(60)
        ambient = dict(os.environ)
        try:
            os.environ.clear()
            os.environ.update({key: value for key, value in ambient.items() if key in _DRIVER_ENV_KEYS})
            browser = asyncio.run(run_main_a_browser(base_url='http://127.0.0.1:18410',
                database=profile.database, owned_targets={profile.database: 'http://127.0.0.1:18410'},
                budget=app.budget, directory=facts.directory / 'native-browser',
                credentials=Credentials(account['login'], account['password']), store_id=1,
                invoice_id=1, original_id=1, original_sha256=ORIGINAL_SHA, patient_id=1, phase='post'))
        finally:
            os.environ.clear()
            os.environ.update(ambient)
        facts.save('E-main-post-original-browser-result', browser)
        app.check()
    logs = closed_log_report(app)
    result = {'status': 'E_POST_ORIGINAL_UI_DOWNLOADED_INDEPENDENT_PDF_AND_TERMINAL_RO_PENDING',
        'actor_id': 5, 'original_id': 1, 'original_sha256': ORIGINAL_SHA,
        'directory': str(facts.directory.relative_to(ROOT)),
        'application_directory': str(app.directory.relative_to(ROOT)),
        'owned_service_exited': True, 'native_exit_code': app.process.returncode,
        'diagnostic_records': logs['record_count'], 'financial_or_document_state_action_replayed': False}
    save_once(profile.root / 'E-MAIN-ORIGINAL-POST-RETURNED.json', result)
    return result


def execute(args, profile):
    """Caller holds the plan's exclusive runner lock for this whole operation."""
    require_dispatch_unfrozen(profile)
    if profile.target_role == 'scratch' and args.action not in {'target-ro', 'bootstrap-scratch', 'd-only', 'log-rollback', 'repair-upgrade-scratch-font', 'prepare-c-scratch', 'c-scratch-sources', 'c-scratch-tail', 'final-upgrade', 'final-scratch-read-only', 'c-company-stage', 'c-remaining-configuration', 'tax-defaults-rollback'}:
        raise RuntimeError('CURRENT_SCRATCH_ACTION_NOT_IMPLEMENTED')
    if profile.target_role == 'main' and args.action in {'bootstrap-scratch', 'd-only', 'log-rollback', 'repair-upgrade-scratch-font', 'prepare-c-scratch', 'c-scratch-sources', 'c-scratch-tail', 'final-scratch-read-only', 'c-company-stage', 'c-remaining-configuration', 'tax-defaults-rollback'}:
        raise RuntimeError('CURRENT_D_EXPLICIT_SCRATCH_TARGET_REQUIRED')
    approval = profile.root / ('runtime-approval-scratch.json' if profile.target_role == 'scratch' else 'runtime-approval.json')
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
        directory = profile.root / ('capture-' + profile.target_role + '-' + uuid.uuid4().hex[:12])
        run = profile.run_root / profile.database
        collect_selection(psycopg2.connect, credentials(), database=profile.database,
            expected_oid=2144129 if profile.target_role == 'main' else 2144130, selections=strict_loads(args.selections.read_bytes()),
            directory=directory, budget=PackageBudget(profile.root, profile=profile),
            allowed_target_names=[profile.database], target_directory=run,
            config_path=run / 'odoo.conf')
        return {'status': 'RO_CAPTURED_NOT_YET_INDEPENDENTLY_REVIEWED',
                'directory': str(directory.relative_to(ROOT))}
    if args.action == 'repair-upgrade-scratch-font':
        return repair_upgrade_scratch_font(profile, approval, authority, args.requested)
    if args.action == 'final-upgrade':
        return run_final_s10_upgrade(profile, approval, authority, args.requested)
    if args.action == 'final-scratch-read-only':
        return run_final_scratch_read_only(profile, approval, authority, args.requested)
    if args.action == 'log-ui-read':
        return run_log_ui_read(profile, approval, authority, args.requested)
    if args.action == 'final-original-ui':
        return run_final_original_ui(profile, approval, authority, args.requested)
    if args.action == 'inventory-native-read-regression':
        return run_native_inventory_read_regression(profile, approval, authority, args.requested)
    if args.action == 'c-company-stage':
        return run_c_company_stage(profile, approval, authority, args.requested)
    if args.action == 'c-remaining-configuration':
        return run_c_remaining_configuration(profile, approval, authority, args.requested)
    if args.action == 'tax-defaults-rollback':
        return run_native_tax_defaults_rollback(profile, approval, authority, args.requested)
    if args.action == 'prepare-c-scratch':
        return prepare_c_scratch(profile, approval, authority, args.requested)
    if args.action == 'c-scratch-sources':
        return run_c_scratch_sources(profile, approval, authority, args.requested)
    if args.action == 'c-scratch-tail':
        return run_c_scratch_sources(profile, approval, authority, args.requested, tail_only=True)
    if args.action == 'log-rollback':
        return run_log_rollback_pair(profile, approval, authority, args.requested)
    if args.action == 'bootstrap-scratch':
        return prepare_scratch(profile, approval, authority, args.requested)
    if args.action == 'd-only':
        return run_d_scratch(profile, approval, authority, args.requested)
    if args.action == 'prepare-reader':
        return prepare_reader(profile, approval, authority)
    if args.action == 'initialize-existing-reader':
        return initialize_existing_reader(profile, approval, authority)
    if args.action == 'b-only':
        return run_b(profile, approval, authority, args.requested)
    if args.action == 'c-main':
        return run_c_main(profile, approval, authority, args.requested)
    if args.action == 'report-parameters-only':
        return repair_report_parameters(profile, approval, authority)
    if args.action == 'c-main-tail':
        return run_c_main(profile, approval, authority, args.requested, tail_only=True)
    if args.action == 'repair-upgrade-main-font':
        return repair_upgrade_main(profile, approval, authority, args.requested, font_repair=True)
    if args.action == 'repair-upgrade-main':
        return repair_upgrade_main(profile, approval, authority, args.requested)
    return run_original(profile, approval, authority)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['target-ro', 'original-ui', 'prepare-reader',
                                         'initialize-existing-reader', 'b-only', 'c-main', 'repair-upgrade-main',
                                         'report-parameters-only', 'repair-upgrade-main-font', 'c-main-tail', 'bootstrap-scratch', 'd-only', 'log-rollback', 'repair-upgrade-scratch-font', 'prepare-c-scratch', 'c-scratch-sources', 'c-scratch-tail', 'final-upgrade', 'final-scratch-read-only', 'log-ui-read', 'final-original-ui', 'inventory-native-read-regression', 'c-company-stage', 'c-remaining-configuration', 'tax-defaults-rollback'])
    parser.add_argument('--target', choices=['main', 'scratch'], default='main')
    parser.add_argument('--selections', type=Path)
    parser.add_argument('--requested', type=Path)
    args = parser.parse_args()
    if args.action == 'target-ro' and args.selections is None:
        parser.error('--selections is required for target-ro')
    if args.action in {'b-only', 'c-main', 'repair-upgrade-main', 'repair-upgrade-main-font', 'c-main-tail', 'bootstrap-scratch', 'd-only', 'log-rollback', 'repair-upgrade-scratch-font', 'prepare-c-scratch', 'c-scratch-sources', 'c-scratch-tail', 'final-upgrade', 'final-scratch-read-only', 'log-ui-read', 'final-original-ui', 'inventory-native-read-regression', 'c-company-stage', 'c-remaining-configuration', 'tax-defaults-rollback'} and args.requested is None:
        parser.error('--requested is required for this action')
    profile = current_plan_profile(args.target)
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

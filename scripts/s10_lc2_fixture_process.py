"""Owned Odoo-shell stdin adapter. Secrets travel only through anonymous pipes.

Not imported by ordinary Python or addons. Each mutable actor owns a fresh native
cursor whose FIRST Environment is its actual uid; no default_env replacements.
"""
import json
import os
from pathlib import Path
import re
import secrets
import stat
from urllib.parse import urlsplit


def run_b_model_only(registry, request, run, *, environment, guard, model_denials, scope, observe,
                     checkpoint=None):
    """One B-only ordinary first Environment and rollback, no configuration writes.

    Explicit dependencies allow offline contract tests without an Odoo registry.
    The real caller remains the existing gated Odoo-shell launch path.
    """
    manifest = request['manifest']
    uid = manifest['actor']['uid']
    if (request['mode'] != 'main-b-only' or type(uid) is not int or uid <= 1 or uid == 7
            or manifest['identity']['database'] != 'ydental_s10_test_20261017105432_810a7d9c'):
        raise ValueError('B_MODEL_ONLY_INPUT_INVALID')
    actor = manifest['actor']
    reference = lambda value: (type(value) is str and bool(re.fullmatch(r'[A-Za-z0-9_./:-]{1,240}', value))
                               and '..' not in value.split('/'))
    fields = {'ydental.settlement.source': 'ydental_original_amount',
              'ydental.settlement.payment': 'ydental_amount', 'ydental.access.audit': 'ydental_reason'}
    if (set(manifest) != {'schema', 'identity', 'actor', 'store_id', 'targets', 'source_ref'}
            or manifest['schema'] != 'LC2_B_MANIFEST_1' or not reference(manifest['source_ref'])
            or manifest['identity'] != {'database': 'ydental_s10_test_20261017105432_810a7d9c',
                                       'oid': 2144129, 'cluster': '7694897083368259627'}
            or set(actor) != {'uid', 'active', 'internal', 'application_user', 'su', 'is_admin', 'is_system', 'metadata_ref'}
            or any(actor[key] is not True for key in ('active', 'internal', 'application_user'))
            or actor['su'] is not False or actor['is_admin'] is not False or actor['is_system'] is not False
            or not reference(actor['metadata_ref'])
            or type(manifest['store_id']) is not int or manifest['store_id'] <= 0
            or type(manifest['targets']) is not list or len(manifest['targets']) != 3
            or any(type(item) is not dict for item in manifest['targets'])
            or {item.get('model') for item in manifest['targets']} != set(fields)):
        raise ValueError('B_MODEL_MANIFEST_REQUIRED')
    for target in manifest['targets']:
        column = fields[target['model']]
        value = 'LC2 denied tampering' if column == 'ydental_reason' else 1
        if (set(target) != {'model', 'id', 'values', 'source_ref'}
                or type(target['id']) is not int or target['id'] <= 0
                or type(target['values']) is not dict or target['values'] != {column: value}
                or type(target['values'][column]) is not type(value) or not reference(target['source_ref'])):
            raise ValueError('B_MODEL_TARGET_MANIFEST_REQUIRED')
    with registry.cursor() as cr:
        env = environment(cr, uid, {'lang': 'en_US'})
        if (env.su or env.transaction.default_env.uid != uid or env.transaction.default_env.su):
            raise RuntimeError('FIXTURE_FIRST_ENV_NOT_ORDINARY_ACTOR')
        if (env.uid != uid or env.is_admin() or env.is_system() or env.user.active is not True or not env.user._is_internal()
                or not env.user.has_group('ydental_base.ydental_base_group_user')):
            raise RuntimeError('B_MODEL_CURRENT_ACTOR_METADATA_MISMATCH')
        if guard(env, str(run)) != manifest['identity'] | {'core': 'f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb'}:
            raise RuntimeError('B_MODEL_MANIFEST_IDENTITY_DRIFT')
        try:
            with scope(case_id='B-MODEL-6', actor_id=env.uid, effective_uid=env.uid, su_flag=env.su):
                return model_denials(env, uid=uid, targets=manifest['targets'],
                                     run_directory=str(run), phase='B-model', observe=observe,
                                     **({'checkpoint': checkpoint} if checkpoint is not None else {}))
        finally:
            # This adapter owns this fresh cursor. Never commits a B probe.
            cr.rollback()


def _save_b_model_observation(run, value):
    name = value['check_id']
    if name not in {'B-MODEL-%d-%s' % (index, operation)
                    for index in range(1, 4) for operation in ('write', 'unlink')}:
        raise ValueError('B_MODEL_CHECK_ID_INVALID')
    path = run / 'diagnostics' / (name + '-observation.json')
    raw = json.dumps(value, ensure_ascii=True, allow_nan=False, separators=(',', ':')).encode()
    if len(raw) > 16384:
        raise ValueError('B_MODEL_OBSERVATION_BOUND')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def main(shell_env):
    from odoo import Command, api
    from odoo.addons.ydental_access.diagnostics import context_scope
    from odoo.addons.ydental_settlement_test.models.lc2_fixture import (
        _guard, _model_denials, _create_reader, _initialize_reader_password, _limited_token,
    )
    run = Path(os.environ['YDENTAL_S10_RUN_DIR'])
    read_fd, write_fd = (int(os.environ[name]) for name in ['YDENTAL_LC2_INPUT_FD', 'YDENTAL_LC2_OUTPUT_FD'])
    if read_fd == write_fd or any(fd < 3 or not stat.S_ISFIFO(os.fstat(fd).st_mode) for fd in [read_fd, write_fd]):
        raise RuntimeError('FIXTURE_ANONYMOUS_PIPE_REQUIRED')
    input_stream = os.fdopen(read_fd, 'rb')
    raw = input_stream.readline(65537)
    if len(raw) > 65536:
        raise RuntimeError('FIXTURE_INPUT_BOUND_EXCEEDED')
    request = json.loads(raw)
    mode = request['mode']
    if mode != 'main-b-only':
        input_stream.close()
    database = shell_env.cr.dbname
    expected = {'main': 'ydental_s10_test_20261017105432_810a7d9c',
                'scratch': 'ydental_s10_test_20261017105432_ce6dcbf8'}
    if mode not in {'main-prepare', 'main-b-only', 'main-reader-only', 'main-reader-password-only', 'main-report-parameters-only', 'log-rollback-only', 'scratch-bootstrap'} or database != expected['scratch' if mode in {'scratch-bootstrap', 'log-rollback-only'} else 'main']:
        raise RuntimeError('FIXTURE_ROLE_MODE_DRIFT')
    import logging
    if logging.getLogger('odoo.http.server').getEffectiveLevel() != logging.CRITICAL:
        raise RuntimeError('TOKEN_TRANSPORT_LOG_PRIVACY_NOT_READY')
    registry = shell_env.registry

    if mode == 'log-rollback-only':
        from s10_lc2_task_profile import CURRENT_PLAN, profile_from_environment
        from s10_lc2_log_rollback import run_log_rollback
        profile = profile_from_environment(os.environ)
        if profile is None or profile.message_id != CURRENT_PLAN or profile.target_role != 'scratch':
            raise RuntimeError('LOG_ROLLBACK_CURRENT_SCRATCH_PROFILE_REQUIRED')
        for action in ('LOG-06', 'LOG-10', 'LOG-12'):
            profile.require_action(action)
        safe = run_log_rollback(registry, request['manifest'], str(run), guard=_guard)
        with os.fdopen(write_fd, 'wb') as stream:
            stream.write(json.dumps({'safe': safe | {'fixture_mode': mode}, 'ram': {}}).encode())
            stream.flush()
        return

    if mode == 'main-b-only':
        with os.fdopen(write_fd, 'wb') as stream:
            def checkpoint(point, check_id, target):
                stream.write(json.dumps({'event': 'b.checkpoint', 'point': point,
                    'check_id': check_id, 'target': target}).encode() + b'\n')
                stream.flush()
                ack = input_stream.readline(1025)
                if len(ack) > 1024 or json.loads(ack) != {'accepted': True, 'check_id': check_id, 'point': point}:
                    raise RuntimeError('B_PARENT_OBSERVATION_NOT_ACKNOWLEDGED')
            try:
                checks = run_b_model_only(registry, request, run, environment=api.Environment,
                    guard=_guard, model_denials=_model_denials, scope=context_scope,
                    observe=lambda value: _save_b_model_observation(run, value), checkpoint=checkpoint)
                response = {'event': 'b.result', 'safe': {'mode': mode, 'model_checks': checks,
                                                        'fixture_commits': 0}, 'ram': {}}
            except Exception as error:
                # Full exception strings and native stderr never enter the pipe.
                response = {'event': 'b.failure', 'safe': {'mode': mode, 'fixture_commits': 0,
                    'failure_type': type(error).__name__, 'status': 'PENDING'}, 'ram': {}}
            encoded = json.dumps(response).encode()
            if len(encoded) > 65536:
                raise RuntimeError('FIXTURE_RAM_OUTPUT_BOUND_EXCEEDED')
            stream.write(encoded + b'\n')
            stream.flush()
        input_stream.close()
        return

    def actor(uid, operation, *, commit=False, checkpoint=None):
        with registry.cursor() as cr:
            env = api.Environment(cr, uid, {})
            if env.su or env.transaction.default_env.uid != uid or env.transaction.default_env.su:
                raise RuntimeError('FIXTURE_FIRST_ENV_NOT_ORDINARY_ACTOR')
            _guard(env, str(run))
            case = ('C-REPORT-CONFIGURATION' if mode == 'main-report-parameters-only' else
                    'B-ACTOR-PREPARE' if mode in {'main-reader-only', 'main-reader-password-only'} else
                    'B-MODEL-6' if mode == 'main-prepare' and uid == 6 else
                    'C-SCOPE' if mode == 'main-prepare' else 'D-ADMIT')
            with context_scope(case_id=case,
                               actor_id=uid, effective_uid=uid, su_flag=False):
                result = operation(env)
                if commit:
                    env.flush_all()
                    if checkpoint is not None:
                        checkpoint('before_commit', result)
                    cr.commit()
                    if checkpoint is not None:
                        checkpoint('commit_returned', result)
                else:
                    cr.rollback()
                return result

    def report_configuration(env):
        if not env.is_system():
            raise RuntimeError('REPORT_CONFIGURATION_REQUIRES_NATIVE_ADMIN')
        base = 'http://127.0.0.1:' + ('18410' if mode == 'main-prepare' else '18411')
        parameters = env['ir.config_parameter']
        changes = []
        for key, value in [('report.url', base), ('web.base.url', base), ('web.base.url.freeze', 'True')]:
            before = parameters.get_str(key)
            if key.endswith('url') and before:
                parsed = urlsplit(before)
                if parsed.username or parsed.password or parsed.query or parsed.fragment:
                    raise RuntimeError('REPORT_CONFIGURATION_PRIOR_URL_HAS_PRIVATE_COMPONENT')
            parameters.set_str(key, value)
            record = parameters.search([('key', '=', key)])
            changes.append({'id': record.id, 'key': key, 'before': before, 'after': value})
        return changes
    if mode == 'main-report-parameters-only':
        from s10_lc2_evidence import save_once
        from s10_lc2_task_profile import CURRENT_PLAN, profile_from_environment
        profile = profile_from_environment(os.environ)
        if profile is None or profile.message_id != CURRENT_PLAN:
            raise RuntimeError('REPORT_PARAMETERS_CURRENT_PROFILE_REQUIRED')
        profile.require_action('report-parameters-only')
        expected_before = request['manifest']['report_config_safe_components']
        def repair_parameters(env):
            if env.uid != 2 or env.su or not env.is_system() or not env.user.has_group('base.group_erp_manager'):
                raise RuntimeError('REPORT_PARAMETERS_NATIVE_ADMIN_REQUIRED')
            parameters = env['ir.config_parameter']
            keys = ('report.url', 'web.base.url', 'web.base.url.freeze')
            before = []
            for key in keys:
                record = parameters.search([('key', '=', key)])
                expected = expected_before[key]
                if len(record) > 1 or bool(record) != expected['present'] or (record and record.id != expected['row_id']):
                    raise RuntimeError('REPORT_PARAMETERS_OBSERVED_IDENTITY_CHANGED')
                value = record.value if record else None
                if key != 'web.base.url.freeze':
                    parsed = urlsplit(value or '')
                    actual = {'present': bool(record), 'row_id': record.id or None,
                        'nonempty': bool(value), 'scheme': parsed.scheme or None, 'hostname': parsed.hostname,
                        'port': parsed.port, 'userinfo_present': parsed.username is not None or parsed.password is not None,
                        'query_present': bool(parsed.query), 'fragment_present': bool(parsed.fragment),
                        'path_is_empty_or_root': parsed.path in ('', '/'), 'raw_value_retained': False}
                    if actual != expected or actual['userinfo_present'] or actual['query_present'] or actual['fragment_present']:
                        raise RuntimeError('REPORT_PARAMETERS_OBSERVED_VALUE_CHANGED')
                elif record:
                    raise RuntimeError('REPORT_PARAMETERS_FREEZE_DRIFTED_FROM_ABSENT_BASELINE')
                before.append({'key': key, 'id': record.id or None, 'value': value})
            save_once(run / 'diagnostics' / ('report-parameters-before-write-%d.json' % os.getpid()),
                {'native_admin_id': 2, 'su': False, 'before': before, 'source_sha256': request['manifest']['source_sha256']})
            changes = []
            for key, value in (('report.url', 'http://127.0.0.1:18410'),
                               ('web.base.url', 'http://127.0.0.1:18410'), ('web.base.url.freeze', 'True')):
                parameters.set_str(key, value)
                record = parameters.search([('key', '=', key)])
                if len(record) != 1 or record.value != value:
                    raise RuntimeError('REPORT_PARAMETERS_NATIVE_WRITE_NOT_OBSERVED')
                changes.append({'id': record.id, 'key': key, 'after': value})
            return {'native_admin_id': 2, 'native_admin_su': False, 'changes': changes,
                    'account_writes': 0, 'economic_operations': 0}
        def checkpoint_parameters(point, value):
            save_once(run / 'diagnostics' / ('report-parameters-%s-%d.json' % (point, os.getpid())),
                value | {'point': point, 'independently_committed': False})
        safe = actor(2, repair_parameters, commit=True, checkpoint=checkpoint_parameters)
        with os.fdopen(write_fd, 'wb') as stream:
            stream.write(json.dumps({'safe': safe | {'mode': mode, 'fixture_commits': 1,
                'commit_observation': 'COMMIT_RETURNED_NOT_INDEPENDENTLY_VERIFIED'}, 'ram': {}}).encode())
            stream.flush()
        return

    if mode == 'main-reader-password-only':
        import hashlib
        from odoo.tools import config
        from s10_lc2_evidence import save_once
        from s10_lc2_task_profile import CURRENT_PLAN, profile_from_environment
        profile = profile_from_environment(os.environ)
        if profile is None or profile.message_id != CURRENT_PLAN:
            raise RuntimeError('EXISTING_READER_CURRENT_PROFILE_REQUIRED')
        profile.require_action('initialize-existing-reader')
        verified_raw = (profile.root / 'reader-pending-verified.json').read_bytes()
        if hashlib.sha256(verified_raw).hexdigest() != 'e69dd648bd5930b633299316bd1f6140a24a84f61ae4cb85b06d10b021f6fb63':
            raise RuntimeError('EXISTING_READER_VERIFIED_SOURCE_CHANGED')
        verified = json.loads(verified_raw)
        if (verified.get('reader_id') != 59 or verified.get('ordinary_nonadmin') is not True
                or verified.get('connection_closed') is not True or verified.get('rollback_returned') is not True):
            raise RuntimeError('EXISTING_READER_VERIFIED_SOURCE_INVALID')
        checkpoint = run / 'diagnostics/reader-create-commit_returned-1791877.json'
        if json.loads(checkpoint.read_bytes()).get('user_id') != 59:
            raise RuntimeError('EXISTING_READER_CREATION_CHECKPOINT_INVALID')
        provider_path = profile.root / 'credentials/user-59.json'
        for path, mode_bits in ((provider_path.parent, 0o700), (provider_path, 0o600)):
            if path.is_symlink() or path.stat().st_uid != os.getuid() or stat.S_IMODE(path.stat().st_mode) != mode_bits:
                raise RuntimeError('EXISTING_READER_PROVIDER_BOUNDARY_INVALID')
        provider = json.loads(provider_path.read_bytes())
        if set(provider) != {'user_id', 'login', 'password'} or provider['user_id'] != 59:
            raise RuntimeError('EXISTING_READER_PROVIDER_IDENTITY_INVALID')
        def initialize_existing(env):
            if env.uid != 2 or env.su or not env.is_system() or not env.user.has_group('base.group_erp_manager'):
                raise RuntimeError('EXISTING_READER_NATIVE_ADMIN_REQUIRED')
            if config.get('smtp_server') or env['ir.mail_server'].with_context(active_test=False).search_count([]):
                raise RuntimeError('EXISTING_READER_OUTBOUND_MAIL_NOT_DISABLED')
            user = env['res.users'].browse(59).exists()
            ordinary_groups = set(user.all_group_ids.ids)
            if (not user or user.create_uid.id != 5 or user.login != provider['login']
                    or user.name != 'LC2 synthetic C reader' or not user.active or not user._is_internal()
                    or user.company_id.id != 1 or user.company_id not in env.user.company_ids
                    or sorted(user.group_ids.ids) != sorted(row['gid'] for row in verified['reader_groups'])
                    or not {env.ref('base.group_user').id, env.ref('ydental_base.ydental_base_group_user').id} <= ordinary_groups
                    or ordinary_groups & {env.ref('base.group_erp_manager').id, env.ref('base.group_system').id}):
                raise RuntimeError('EXISTING_READER_ACTUAL_IDENTITY_CHANGED')
            env.cr.execute('SELECT password IS NULL FROM res_users WHERE id=%s', [59])
            if env.cr.fetchone() != (True,):
                raise RuntimeError('EXISTING_READER_PASSWORD_ALREADY_PRESENT_VERIFY_NO_REWRITE')
            user.write({'password': provider['password']})
            env.flush_all()
            env.cr.execute('SELECT password IS NOT NULL FROM res_users WHERE id=%s', [59])
            if env.cr.fetchone() != (True,):
                raise RuntimeError('EXISTING_READER_NATIVE_PASSWORD_NOT_INITIALIZED')
            return {'user_id': 59, 'native_admin_id': 2, 'native_admin_su': False,
                    'password_present': True, 'outbound_mail_disabled': True,
                    'groups_changed': False, 'business_operations': 0}
        def checkpoint_password(point, value):
            save_once(run / 'diagnostics' / ('reader-password-admin-%s-%d.json' % (point, os.getpid())),
                      value | {'point': point, 'independently_committed': False})
        safe = actor(2, initialize_existing, commit=True, checkpoint=checkpoint_password)
        del provider
        with os.fdopen(write_fd, 'wb') as stream:
            stream.write(json.dumps({'safe': safe | {'mode': mode, 'fixture_commits': 1,
                'commit_observation': 'COMMIT_RETURNED_NOT_INDEPENDENTLY_VERIFIED'}, 'ram': {}}).encode())
            stream.flush()
        return

    if mode == 'main-reader-only':
        from s10_lc2_evidence import save_once
        from s10_lc2_task_profile import CURRENT_PLAN, profile_from_environment
        profile = profile_from_environment(os.environ)
        if profile is None or profile.message_id != CURRENT_PLAN:
            raise RuntimeError('CURRENT_PLAN_READER_PROFILE_REQUIRED')
        profile.require_action('main-reader-prepare')
        provider_dir = profile.root / 'credentials'
        if (provider_dir.is_symlink() or not provider_dir.is_dir()
                or stat.S_IMODE(provider_dir.stat().st_mode) != 0o700):
            raise RuntimeError('CURRENT_READER_PROVIDER_DIRECTORY_INVALID')
        def created(point, value):
            if point == 'before_commit':
                save_once(provider_dir / ('user-%d.json' % value.user_id), {
                    'user_id': value.user_id, 'login': value.login, 'password': value.password})
            save_once(run / 'diagnostics' / ('reader-create-%s-%d.json' % (point, os.getpid())), {
                'kind': 'CURRENT_PLAN_READER_COMMIT_CHECKPOINT', 'point': point,
                'user_id': value.user_id, 'manager_id': 5, 'store_id': 1,
                'independently_committed': False, 'password_retained': False})
        def password(point, value):
            save_once(run / 'diagnostics' / ('reader-password-%s-%d.json' % (point, os.getpid())), {
                'kind': 'CURRENT_PLAN_READER_PASSWORD_CHECKPOINT', 'point': point,
                'user_id': value['user_id'], 'own_password_initialized': True,
                'independently_committed': False, 'password_retained': False})
        reader = actor(5, lambda env: _create_reader(env, manager_uid=5,
            store_ids=[1], initial_levels={'settlement': 'read', 'export': 'none'},
            run_directory=str(run)), commit=True, checkpoint=created)
        initialized = actor(reader.user_id, lambda env: _initialize_reader_password(
            env, reader, run_directory=str(run)), commit=True, checkpoint=password)
        response = {'safe': {'mode': mode, 'new_reader_id': reader.user_id,
            'manager_id': 5, 'store_ids': [1], 'fixture_commits': 2,
            'own_password_initialized': initialized['own_password_initialized'],
            'commit_observation': 'COMMIT_RETURNED_NOT_INDEPENDENTLY_VERIFIED'},
            'ram': {'reader': {name: getattr(reader, name) for name in reader.__dataclass_fields__}}}
        with os.fdopen(write_fd, 'wb') as stream:
            stream.write(json.dumps(response).encode())
            stream.flush()
        return

    scratch_profile = None
    if mode == 'scratch-bootstrap':
        from odoo.tools import config
        from s10_lc2_evidence import save_once
        from s10_lc2_task_profile import CURRENT_PLAN, profile_from_environment
        scratch_profile = profile_from_environment(os.environ)
        if scratch_profile is not None and scratch_profile.message_id != CURRENT_PLAN:
            scratch_profile = None
        if scratch_profile is not None:
            if scratch_profile.target_role != 'scratch':
                raise RuntimeError('CURRENT_D_SCRATCH_PROFILE_REQUIRED')
            scratch_profile.require_action('scratch-bootstrap')
            providers = scratch_profile.root / 'credentials'
            if (providers.is_symlink() or not providers.is_dir() or providers.stat().st_uid != os.getuid()
                    or stat.S_IMODE(providers.stat().st_mode) != 0o700):
                raise RuntimeError('CURRENT_D_PROVIDER_DIRECTORY_BOUNDARY_INVALID')
            def mail_guard(env):
                if (env.uid != 2 or env.su or not env.is_system()
                        or not env.user.has_group('base.group_erp_manager')
                        or config.get('smtp_server')
                        or env['ir.mail_server'].with_context(active_test=False).search_count([])):
                    raise RuntimeError('CURRENT_D_NATIVE_SETUP_OR_MAIL_BOUNDARY_INVALID')
            actor(2, mail_guard)
    def setup_checkpoint(stage):
        def save(point, value):
            if scratch_profile is not None:
                save_once(run / 'diagnostics' / ('D-setup-%s-%s-%d.json' % (stage, point, os.getpid())), {
                    'stage': stage, 'point': point, 'value': value, 'independently_committed': False})
        return save
    report_parameters = actor(2, report_configuration, commit=True,
                             checkpoint=setup_checkpoint('report-configuration'))

    if mode == 'main-prepare':
        checks = actor(6, lambda env: _model_denials(env, uid=6, targets=[
            {'model': 'ydental.settlement.source', 'id': 1, 'values': {'ydental_original_amount': 1}},
            {'model': 'ydental.settlement.payment', 'id': 1, 'values': {'ydental_amount': 1}},
            {'model': 'ydental.access.audit', 'id': 228, 'values': {'ydental_reason': 'LC2 denied tampering'}},
        ], run_directory=str(run)))
        if not checks['six_denied']:
            raise RuntimeError('MODEL_SIX_DENIALS_INCOMPLETE')
        reader = actor(5, lambda env: _create_reader(env, manager_uid=5, store_ids=[1], run_directory=str(run)), commit=True)
        initialized = actor(reader.user_id, lambda env: _initialize_reader_password(env, reader, run_directory=str(run)), commit=True)
        token = actor(5, lambda env: _limited_token(env, original_id=1, run_directory=str(run)), commit=True)
        from odoo.tools import image_guess_size_from_field_name, image_process
        import odoo
        core = Path(odoo.__file__).resolve().parent.parent
        raw_placeholder = (core / 'addons/web/static/img/placeholder.png').read_bytes()
        expected_placeholder = image_process(raw_placeholder, size=image_guess_size_from_field_name('raw'), crop=False)
        response = {'safe': {'mode': mode, 'model_checks': checks, 'new_reader_id': reader.user_id,
                             'own_password_initialized': initialized['own_password_initialized'],
                             'valid_limited_token_verified': token.verified, 'attachment_id': token.attachment_id,
                             'original_id': token.original_id, 'fixture_commits': 4,
                             'report_parameters': report_parameters,
                             'commit_observation': 'COMMIT_RETURNED_NOT_INDEPENDENTLY_VERIFIED'},
                    'ram': {'reader': {name: getattr(reader, name) for name in reader.__dataclass_fields__},
                            'limited_token': token.value, 'expected_placeholder_hex': expected_placeholder.hex()}}
    else:
        # Native administrator creates only new configuration and one bootstrap
        # actor. Business D source/fees/invoices/payments are never built here.
        password, login = secrets.token_urlsafe(32), 'lc2_d_manager_' + secrets.token_hex(8)

        def bootstrap(env):
            if not env.is_system() or env['ydental.access.store'].search_count([]):
                raise RuntimeError('SCRATCH_BOOTSTRAP_REQUIRES_NEW_EMPTY_CONFIGURATION')
            company = env.company
            template = env['account.chart.template']
            if not company.chart_template:
                mapping = template._get_chart_template_mapping()
                if mapping.get('generic_coa', {}).get('module') not in {'account', None}:
                    raise RuntimeError('SCRATCH_CHART_WOULD_INSTALL_UNAPPROVED_MODULE')
                template.try_loading('generic_coa', company, install_demo=False)
            env['ir.config_parameter'].set_str('ydental_queue.heartbeat_seconds', '10')
            env['ir.config_parameter'].set_str('ydental_queue.timeout_seconds', '300')
            user = env['res.users'].with_context(no_reset_password=True).create({
                'name': 'LC2 synthetic D manager', 'login': login, 'password': password, 'lang': 'en_US',
                'company_id': company.id, 'company_ids': [Command.set([company.id])],
                'group_ids': [Command.set([env.ref('ydental_access.ydental_group_manager').id])],
            })
            return {'manager_uid': user.id, 'company_id': company.id}

        def bootstrap_checkpoint(point, value):
            if scratch_profile is not None and point == 'before_commit':
                save_once(scratch_profile.root / 'credentials' / ('scratch-user-%d.json' % value['manager_uid']), {
                    'user_id': value['manager_uid'], 'login': login, 'password': password})
            setup_checkpoint('manager')(point, value)
        boot = actor(2, bootstrap, commit=True, checkpoint=bootstrap_checkpoint)
        role_passwords = {name: secrets.token_urlsafe(32) for name in ['frontdesk', 'doctor']}

        def clinic(env):
            access = env['ydental.access.service']
            session = access._session_for_key(secrets.token_hex(24))
            access = access._bind(session)
            store = access._create_store('LC2 independent synthetic D clinic', boot['company_id'], 'UTC')['store_id']
            access._grant(env.uid, store, dict.fromkeys(['frontdesk', 'patient', 'price', 'medical', 'capacity', 'space', 'export', 'settlement', 'finance_approval'], 'write'), source='lc2_new_d_configuration')
            access._switch(store)
            access = access._bind(session)
            cap = access.env['ydental.access.capability'].create({'name': 'LC2 synthetic care capability', 'ydental_code': 'lc2_d_care_' + secrets.token_hex(6)})
            access._update_profile(env.uid, 'LC2 synthetic D manager', [cap.id])
            roles = {}
            for name, levels in [('frontdesk', {'frontdesk': 'write', 'patient': 'write', 'settlement': 'write', 'finance_approval': 'write'}), ('doctor', {'medical': 'write'})]:
                role_login = 'lc2_d_' + name + '_' + secrets.token_hex(8)
                uid = access._create_account('LC2 synthetic D ' + name, role_login, store)['user_id']
                access._grant(uid, store, levels, source='lc2_new_d_configuration')
                if name == 'doctor':
                    access._update_profile(uid, 'LC2 synthetic D doctor', [cap.id])
                roles[name] = {'uid': uid, 'login': role_login, 'password': role_passwords[name]}
            floor = access.env['ydental.space.floor'].create({'name': 'LC2 synthetic D floor', 'ydental_store_id': store})
            area = access.env['ydental.space.area'].create({'name': 'LC2 synthetic D reporting', 'ydental_store_id': store, 'ydental_floor_id': floor.id,
                'ydental_reporting': True, 'ydental_purpose': 'care', 'ydental_missed_limit': 2})
            station = access.env['ydental.space.station'].create({'name': 'LC2 synthetic D chair', 'ydental_store_id': store, 'ydental_floor_id': floor.id,
                'ydental_area_id': area.id, 'ydental_kind': 'care', 'ydental_add_capability_ids': [Command.set([cap.id])]})
            supply = access.env['ydental.supply.service']
            supply._operate('policy', {'name': 'LC2 synthetic capacity policy', 'mode': 'demo', 'rounding': 'floor', 'phone_pool': 'reservation', 'cutoff_minutes': 0, 'reason': 'LC2 synthetic D admission'}, secrets.token_hex(24))
            supply._operate('business', {'area_id': area.id, 'state': 'open', 'reason': 'LC2 independent synthetic day'}, secrets.token_hex(24))
            return {'store_id': store, 'area_id': area.id, 'station_id': station.id, 'capability_id': cap.id,
                    'uom_id': env.ref('uom.product_uom_unit').id, 'currency_id': env.company.currency_id.id,
                    'company_id': env.company.id, 'manager_levels': access._levels(access._membership(env.uid, store)),
                    'manager': {'uid': env.uid, 'login': login, 'password': password}, **roles}

        def clinic_checkpoint(point, value):
            if scratch_profile is not None and point == 'before_commit':
                for role in ('frontdesk', 'doctor'):
                    account = value[role]
                    save_once(scratch_profile.root / 'credentials' / ('scratch-user-%d.json' % account['uid']), {
                        'user_id': account['uid'], 'login': account['login'], 'password': account['password']})
            setup_checkpoint('clinic')(point, {key: value[key] for key in (
                'store_id', 'area_id', 'station_id', 'capability_id', 'company_id', 'currency_id', 'uom_id')} |
                {'manager_id': value['manager']['uid'], 'frontdesk_id': value['frontdesk']['uid'], 'doctor_id': value['doctor']['uid']})
        fixture = actor(boot['manager_uid'], clinic, commit=True, checkpoint=clinic_checkpoint)
        for role in ['frontdesk', 'doctor']:
            def initialize(env, role=role):
                if scratch_profile is None:
                    env.user.write({'password': fixture[role]['password']})
                    return {'user_id': env.uid}
                mail_guard(env)
                account = fixture[role]
                user = env['res.users'].browse(account['uid']).exists()
                if (not user or user.create_uid.id != boot['manager_uid'] or user.login != account['login']
                        or user.company_id.id != fixture['company_id'] or not user.active or not user._is_internal()
                        or not user.has_group('ydental_base.ydental_base_group_user')
                        or user.has_group('base.group_system') or user.has_group('base.group_erp_manager')):
                    raise RuntimeError('CURRENT_D_NEW_ORDINARY_ACTOR_NOT_PROVEN')
                env.cr.execute('SELECT password IS NULL FROM res_users WHERE id=%s', [user.id])
                if env.cr.fetchone() != (True,):
                    raise RuntimeError('CURRENT_D_PASSWORD_PRESENT_NO_REINITIALIZATION')
                user.write({'password': account['password'], 'lang': 'en_US'})
                env.flush_all()
                env.cr.execute('SELECT password IS NOT NULL FROM res_users WHERE id=%s', [user.id])
                if env.cr.fetchone() != (True,):
                    raise RuntimeError('CURRENT_D_NATIVE_PASSWORD_NOT_INITIALIZED')
                return {'user_id': user.id, 'native_admin_id': 2, 'groups_changed': False, 'password_present': True, 'lang': user.lang}
            actor(2 if scratch_profile is not None else fixture[role]['uid'], initialize,
                  commit=True, checkpoint=setup_checkpoint(role + '-password'))

        def finance_config(env):
            company = env['res.company'].browse(boot['company_id'])
            income = env['account.account'].search([('account_type', '=', 'income'), ('company_ids', 'in', company.id)], limit=1)
            sales = env['account.journal'].search([('type', '=', 'sale'), ('company_id', '=', company.id)], limit=1)
            general = env['account.journal'].search([('type', '=', 'general'), ('company_id', '=', company.id)], limit=1)
            if not (income and sales and general):
                raise RuntimeError('SCRATCH_NATIVE_CHART_CONFIGURATION_INCOMPLETE')
            values = {'ydental_store_id': fixture['store_id'], 'company_id': company.id, 'ydental_policy': 'demo_confirmation',
                      'ydental_sales_journal_id': sales.id, 'ydental_income_account_id': income.id, 'ydental_adjustment_journal_id': general.id}
            for index, channel in enumerate(['cash', 'wechat', 'alipay', 'card'], 1):
                outstanding = env['account.account'].create({'name': 'LC2 synthetic outstanding ' + channel, 'code': 'LC2' + str(index),
                    'account_type': 'asset_current', 'company_ids': [Command.link(company.id)]})
                journal = env['account.journal'].create({'name': 'LC2 synthetic offline ' + channel, 'code': 'LC' + str(index), 'type': 'bank', 'company_id': company.id})
                methods = journal.inbound_payment_method_line_ids | journal.outbound_payment_method_line_ids
                methods.filtered(lambda line: line.payment_method_id.code == 'manual').write({'payment_account_id': outstanding.id})
                values['ydental_' + channel + '_journal_id'] = journal.id
            # This pre-existing protected factory seeds approved config only.
            # No fee, source, move, payment, receipt or refund factory is used.
            return env['ydental.settlement.config']._new(values).id
        config_id = actor(2, finance_config, commit=True, checkpoint=setup_checkpoint('native-finance-config'))
        def verify_no_money(env):
            if any(env[model].search_count([]) for model in [
                    'ydental.treatment.fee', 'ydental.settlement.source', 'ydental.settlement.payment',
                    'ydental.settlement.refund', 'account.move', 'account.payment']):
                raise RuntimeError('SCRATCH_BOOTSTRAP_UNEXPECTED_FINANCIAL_ROWS')
        actor(2, verify_no_money)
        response = {'safe': {'mode': mode, 'store_id': fixture['store_id'], 'config_id': config_id,
                             'manager_id': fixture['manager']['uid'], 'frontdesk_id': fixture['frontdesk']['uid'], 'doctor_id': fixture['doctor']['uid'],
                             'business_money_dispatches': 0, 'fee_or_transaction_rows_created': 0,
                             'fixture_commits': 6 if scratch_profile is not None else None,
                             'report_parameters': report_parameters,
                             'commit_observation': 'COMMIT_RETURNED_NOT_INDEPENDENTLY_VERIFIED'}, 'ram': fixture}
    encoded = json.dumps(response, separators=(',', ':')).encode()
    if len(encoded) > 65536:
        raise RuntimeError('FIXTURE_RAM_OUTPUT_BOUND_EXCEEDED')
    with os.fdopen(write_fd, 'wb') as stream:
        stream.write(encoded)
        stream.flush()


main(env)

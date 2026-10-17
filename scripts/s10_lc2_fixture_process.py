"""Owned Odoo-shell stdin adapter. Secrets travel only through anonymous pipes.

Not imported by ordinary Python or addons. Each mutable actor owns a fresh native
cursor whose FIRST Environment is its actual uid; no default_env replacements.
"""
import json
import os
from pathlib import Path
import secrets
import stat
from urllib.parse import urlsplit


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
    with os.fdopen(read_fd, 'rb') as stream:
        raw = stream.read(65537)
    if len(raw) > 65536:
        raise RuntimeError('FIXTURE_INPUT_BOUND_EXCEEDED')
    request = json.loads(raw)
    mode = request['mode']
    database = shell_env.cr.dbname
    expected = {'main': 'ydental_s10_test_20261017105432_810a7d9c',
                'scratch': 'ydental_s10_test_20261017105432_ce6dcbf8'}
    if mode not in {'main-prepare', 'scratch-bootstrap'} or database != expected['main' if mode == 'main-prepare' else 'scratch']:
        raise RuntimeError('FIXTURE_ROLE_MODE_DRIFT')
    import logging
    if logging.getLogger('odoo.http.server').getEffectiveLevel() != logging.CRITICAL:
        raise RuntimeError('TOKEN_TRANSPORT_LOG_PRIVACY_NOT_READY')
    registry = shell_env.registry

    def actor(uid, operation, *, commit=False):
        with registry.cursor() as cr:
            env = api.Environment(cr, uid, {})
            if env.su or env.transaction.default_env.uid != uid or env.transaction.default_env.su:
                raise RuntimeError('FIXTURE_FIRST_ENV_NOT_ORDINARY_ACTOR')
            _guard(env, str(run))
            with context_scope(case_id='B-MODEL-6' if mode == 'main-prepare' and uid == 6 else 'C-SCOPE' if mode == 'main-prepare' else 'D-ADMIT',
                               actor_id=uid, effective_uid=uid, su_flag=False):
                result = operation(env)
                if commit:
                    env.flush_all()
                    cr.commit()
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
    report_parameters = actor(2, report_configuration, commit=True)

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
                'name': 'LC2 synthetic D manager', 'login': login, 'password': password,
                'company_id': company.id, 'company_ids': [Command.set([company.id])],
                'group_ids': [Command.set([env.ref('ydental_access.ydental_group_manager').id])],
            })
            return {'manager_uid': user.id, 'company_id': company.id}

        boot = actor(2, bootstrap, commit=True)
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
                    'company_id': env.company.id, 'manager': {'uid': env.uid, 'login': login, 'password': password}, **roles}

        fixture = actor(boot['manager_uid'], clinic, commit=True)
        for role in ['frontdesk', 'doctor']:
            def initialize(env, role=role):
                env.user.write({'password': fixture[role]['password']})
            actor(fixture[role]['uid'], initialize, commit=True)

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
        config_id = actor(2, finance_config, commit=True)
        def verify_no_money(env):
            if any(env[model].search_count([]) for model in [
                    'ydental.treatment.fee', 'ydental.settlement.source', 'ydental.settlement.payment',
                    'ydental.settlement.refund', 'account.move', 'account.payment']):
                raise RuntimeError('SCRATCH_BOOTSTRAP_UNEXPECTED_FINANCIAL_ROWS')
        actor(2, verify_no_money)
        response = {'safe': {'mode': mode, 'store_id': fixture['store_id'], 'config_id': config_id,
                             'manager_id': fixture['manager']['uid'], 'frontdesk_id': fixture['frontdesk']['uid'], 'doctor_id': fixture['doctor']['uid'],
                             'business_money_dispatches': 0, 'fee_or_transaction_rows_created': 0,
                             'report_parameters': report_parameters,
                             'commit_observation': 'COMMIT_RETURNED_NOT_INDEPENDENTLY_VERIFIED'}, 'ram': fixture}
    encoded = json.dumps(response, separators=(',', ':')).encode()
    if len(encoded) > 65536:
        raise RuntimeError('FIXTURE_RAM_OUTPUT_BOUND_EXCEEDED')
    with os.fdopen(write_fd, 'wb') as stream:
        stream.write(encoded)
        stream.flush()


main(env)

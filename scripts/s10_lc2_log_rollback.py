"""Rollback probes called only by the existing scratch Odoo-shell fixture adapter.

No entry point, launcher, authentication, configuration or commits. The existing
adapter must validate its current target, manifest and pipe before invoking this.
Run once per native process with diagnostics either enabled or absent at startup.
"""
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import time
import uuid
from datetime import datetime, timezone
from unittest.mock import patch


_TABLES = (
    'account_move', 'account_move_line', 'account_payment',
    'account_partial_reconcile', 'ydental_settlement_source',
    'ydental_settlement_payment', 'ydental_settlement_refund',
    'ydental_settlement_receipt', 'ydental_settlement_close',
    'ydental_settlement_mutex', 'ydental_access_audit',
)


def _stored_fingerprint(cr):
    result = {}
    for table in _TABLES:
        # All identifiers are private constants. Full rows remain in RAM only.
        cr.execute('SELECT to_jsonb(t) FROM ' + table + ' t ORDER BY id')
        rows = [row[0] for row in cr.fetchall()]
        raw = json.dumps(rows, sort_keys=True, ensure_ascii=True,
                         separators=(',', ':'), default=str).encode()
        result[table] = {'rows': len(rows), 'sha256': hashlib.sha256(raw).hexdigest()}
    return result


def run_log_rollback(registry, manifest, run_directory, *, guard):
    """Exercise the real bill/audit transaction on a NEW unbilled scratch fee.

    Binding is derived by the native service from the actual existing ordinary
    actor/session, whose provenance must also be established by the caller's RO.
    The D money chain must never be supplied as this separate unpaid fixture.
    """
    from odoo import api
    from odoo.exceptions import UserError, ValidationError
    from odoo.addons.ydental_access import diagnostics
    from odoo.addons.ydental_access.diagnostics import context_scope, record_exception

    if (set(manifest) != {'actor_id', 'session_id', 'revision', 'store_id',
                          'fee_id', 'd_fee_id', 'operation_ref', 'diagnostics'}
            or any(type(manifest[name]) is not int or manifest[name] <= 0
                   for name in ('actor_id', 'session_id', 'revision', 'store_id', 'fee_id', 'd_fee_id'))
            or manifest['actor_id'] <= 2
            or manifest['fee_id'] == manifest['d_fee_id']
            or manifest['diagnostics'] not in ('ON', 'OFF')
            or type(manifest['operation_ref']) is not str
            or not re.fullmatch(r'[A-Za-z0-9_-]{1,90}', manifest['operation_ref'])):
        raise ValueError('LOG_ROLLBACK_MANIFEST_INVALID')

    class _RollbackSuccess(Exception):
        pass

    started = time.monotonic_ns()
    trace_id = uuid.uuid4().hex
    outcome = {'mode': manifest['diagnostics'], 'fixture_commits': 0,
               'model_trace_id': trace_id, 'http_request_id': None}
    logger = logging.getLogger(diagnostics.LOGGER_NAME)
    handlers = [handler for handler in logger.handlers
                if isinstance(handler, diagnostics.PidFileHandler)]
    if logger.disabled or logger.propagate or logger.getEffectiveLevel() != logging.INFO:
        raise RuntimeError('LOG_NATIVE_LOGGER_STATE_INVALID')
    if manifest['diagnostics'] == 'ON':
        selected = os.environ.get('YDENTAL_DIAGNOSTIC_DIR')
        if (not selected or len(handlers) != 1 or handlers[0].pid != os.getpid()
                or handlers[0].directory.resolve() != Path(selected).resolve()):
            raise RuntimeError('LOG_ON_NATIVE_PRODUCER_NOT_OBSERVED')
    elif ('YDENTAL_DIAGNOSTIC_DIR' in os.environ or handlers
          or diagnostics._DIRECTORY is not None
          or not any(isinstance(handler, logging.NullHandler) for handler in logger.handlers)):
        raise RuntimeError('LOG_OFF_NATIVE_STARTUP_OPTOUT_NOT_OBSERVED')
    outcome['producer'] = {'environment_selected': 'YDENTAL_DIAGNOSTIC_DIR' in os.environ,
                           'pid_file_handler_count': len(handlers),
                           'logger_disabled': logger.disabled,
                           'native_optout': manifest['diagnostics'] == 'OFF'}
    cr = registry.cursor()
    try:
        env = api.Environment(cr, manifest['actor_id'], {'lang': 'en_US'})
        if (env.su or env.transaction.default_env.uid != env.uid
                or env.transaction.default_env.su or env.is_admin() or env.is_system()
                or not env.user.active or not env.user._is_internal()
                or not env.user.has_group('ydental_base.ydental_base_group_user')):
            raise RuntimeError('LOG_ROLLBACK_ORDINARY_FIRST_ENV_REQUIRED')
        identity = guard(env, run_directory)
        if (identity['database'] != 'ydental_s10_test_20261017105432_ce6dcbf8'
                or identity['oid'] != 2144130
                or identity['cluster'] != '7694897083368259627'):
            raise RuntimeError('LOG_ROLLBACK_SCRATCH_IDENTITY_REQUIRED')
        session = env['ydental.access.session'].sudo().browse(manifest['session_id']).exists()
        bound = env['ydental.access.service']._bind(session, manifest['revision'])
        service = env['ydental.settlement.service'].with_context(bound.env.context)
        store = service._access(write=True)
        if store.id != manifest['store_id']:
            raise RuntimeError('LOG_ROLLBACK_STORE_DRIFT')
        fee = service._fee(manifest['fee_id'], store)
        if (fee.ydental_amount <= 0
                or service._model('source').search_count([('ydental_fee_id', '=', fee.id)])):
            raise RuntimeError('LOG_ROLLBACK_SEPARATE_UNBILLED_FEE_REQUIRED')
        payload = {'fee_ids': [fee.id], 'discount': 0, 'reason': 'Synthetic diagnostics rollback comparison'}
        before = _stored_fingerprint(cr)
        with context_scope(case_id='LOG-06', actor_id=env.uid, effective_uid=env.uid,
                           su_flag=False, store_id=store.id,
                           trace_id=trace_id,
                           operation_ref=manifest['operation_ref']):
            try:
                with cr.savepoint():
                    call_started = time.monotonic_ns()
                    result = service._operate('bill', payload, manifest['operation_ref'] + '-success')
                    outcome.setdefault('operation_elapsed_ns', {})['successful_bill'] = time.monotonic_ns() - call_started
                    invoice = env['account.move'].sudo().browse(result['invoice_id'])
                    sources = service._model('source').search([('ydental_fee_id', '=', fee.id)])
                    audits = env['ydental.access.audit'].sudo().search([
                        ('ydental_event', '=', 'settlement.bill'),
                        ('ydental_target_model', '=', 'account.move'),
                        ('ydental_target_id', '=', invoice.id),
                        ('ydental_user_id', '=', env.uid)])
                    env.flush_all()
                    if (result['result'] != 'accepted' or invoice.state != 'posted'
                            or invoice.amount_total != fee.ydental_amount
                            or invoice.amount_residual != fee.ydental_amount
                            or len(sources) != 1 or sources.ydental_invoice_id != invoice
                            or len(audits) != 1
                            or abs(sum(invoice.line_ids.mapped('balance'))) > 0.000001):
                        raise AssertionError('LOG_ROLLBACK_REAL_BILL_INVARIANTS_FAILED')
                    outcome['success'] = {'result': result['result'], 'state': invoice.state,
                        'amount': invoice.amount_total, 'residual': invoice.amount_residual,
                        'source_count': len(sources), 'audit_count': len(audits),
                        'balanced': True, 'actual_exception': None}

                    def expect_native_denial(operation, values, key, code, message):
                        prior = _stored_fingerprint(cr)
                        call_started = time.monotonic_ns()
                        try:
                            service._operate(operation, values, key)
                        except UserError as primary:
                            if (type(primary) is not UserError
                                    or primary.args != (message,)
                                    or getattr(primary, 'diagnostic_code', None) != code):
                                raise
                            with context_scope(operation=operation):
                                record_exception(primary, 'ydental_settlement.test', 'log.business_denial')
                        else:
                            raise AssertionError('LOG_EXPECTED_NATIVE_DENIAL_NOT_RAISED')
                        outcome['operation_elapsed_ns'][code] = time.monotonic_ns() - call_started
                        if _stored_fingerprint(cr) != prior:
                            raise AssertionError('LOG_DENIED_OPERATION_CHANGED_STORED_FACTS')
                        return {'type': 'odoo.exceptions.UserError', 'code': code,
                                'state_unchanged': True}

                    # A genuine changed payload hits the existing receipt's
                    # VERSION_CONFLICT, rather than a malformed-input precheck.
                    outcome['version_conflict'] = expect_native_denial(
                        'bill', dict(payload, discount=0.01),
                        manifest['operation_ref'] + '-success', 'VERSION_CONFLICT',
                        'version_conflict: This request key belongs to another action.')
                    now = datetime.now(timezone.utc)
                    day = service._local_date(store, now).isoformat()
                    service._operate('close', {'business_date': day, 'channel': 'cash'},
                                     manifest['operation_ref'] + '-rollback-close')
                    # This actor's NEW close exists only inside this savepoint.
                    # The invoice is genuinely posted/unpaid. Native DAY_CLOSED
                    # must refuse this otherwise valid payment before any funds.
                    outcome['day_closed'] = expect_native_denial(
                        'pay', {'invoice_ids': [invoice.id],
                                'amount': min(invoice.amount_residual, 1),
                                'channel': 'cash', 'actual_utc': now.isoformat(),
                                'proof': 'Synthetic rollback-only rejected payment'},
                        manifest['operation_ref'] + '-denied-pay', 'DAY_CLOSED',
                        'day_closed: A finance approver must unlock this cashier day.')
                    raise _RollbackSuccess()
            except _RollbackSuccess:
                pass
            if _stored_fingerprint(cr) != before:
                raise AssertionError('LOG_SUCCESS_SAVEPOINT_DID_NOT_ROLL_BACK')

            access_type = type(env['ydental.access.service'])
            original_audit = access_type._audit
            injected = []

            def fail_mandatory_audit(self, event, *args, **kwargs):
                if event == 'settlement.bill':
                    injected.append(event)
                    raise ValidationError('Synthetic mandatory audit storage failure')
                return original_audit(self, event, *args, **kwargs)

            # Only the mandatory audit for this isolated bill fails. The native
            # operation's own savepoint must roll back invoice, source and mutex.
            with patch.object(access_type, '_audit', fail_mandatory_audit):
                call_started = time.monotonic_ns()
                try:
                    service._operate('bill', payload, manifest['operation_ref'] + '-audit-failure')
                except ValidationError as primary:
                    if primary.args != ('Synthetic mandatory audit storage failure',) or injected != ['settlement.bill']:
                        raise
                    with context_scope(operation='bill'):
                        record_exception(primary, 'ydental_settlement.test', 'log.audit_failure')
                    outcome['mandatory_audit_failure'] = {'exception': type(primary).__name__,
                        'propagated': True, 'injected_calls': len(injected)}
                else:
                    raise AssertionError('MANDATORY_AUDIT_FAILURE_WAS_SWALLOWED')
                outcome['operation_elapsed_ns']['mandatory_audit_failure'] = time.monotonic_ns() - call_started
            after = _stored_fingerprint(cr)
            if after != before:
                raise AssertionError('MANDATORY_AUDIT_FAILURE_LEFT_BUSINESS_CHANGES')

            def fail_isolated_program(self, event, *args, **kwargs):
                if event == 'settlement.bill':
                    raise RuntimeError('Synthetic isolated program failure')
                return original_audit(self, event, *args, **kwargs)

            with context_scope(case_id='LOG-12'):
                with patch.object(access_type, '_audit', fail_isolated_program):
                    call_started = time.monotonic_ns()
                    try:
                        service._operate('bill', payload, manifest['operation_ref'] + '-program-failure')
                    except RuntimeError as primary:
                        if type(primary) is not RuntimeError or primary.args != ('Synthetic isolated program failure',):
                            raise
                        with context_scope(operation='bill'):
                            record_exception(primary, 'ydental_settlement.test', 'log.program_failure')
                        outcome['isolated_program_failure'] = {
                            'type': type(primary).__name__, 'propagated': True,
                            'synthetic_rollback_fixture': True}
                    else:
                        raise AssertionError('ISOLATED_PROGRAM_FAILURE_WAS_SWALLOWED')
                    outcome['operation_elapsed_ns']['isolated_program_failure'] = time.monotonic_ns() - call_started
                if _stored_fingerprint(cr) != before:
                    raise AssertionError('ISOLATED_PROGRAM_FAILURE_LEFT_BUSINESS_CHANGES')
            outcome.update(stored_before=before, stored_after=after,
                           successful_bill_rolled_back=True, failed_bill_rolled_back=True,
                           actor_id=env.uid, su=False, first_env_uid=env.transaction.default_env.uid)
    finally:
        try:
            cr.rollback()
        finally:
            cr.close()
    outcome.update(rollback_returned=True, cursor_close_returned=True,
                   elapsed_ns=time.monotonic_ns() - started)
    return outcome

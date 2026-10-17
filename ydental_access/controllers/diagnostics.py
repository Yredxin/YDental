"""HTTP-only adapter; models use the primitive diagnostic helper directly."""
from functools import wraps
import hashlib
import os
import re
import uuid

from odoo.http import request

from ..diagnostics import bind_context, emit_event, record_exception, reset_context


_LABEL = re.compile(r'[A-Za-z0-9_.:-]{1,96}\Z')
_CASE_IDS = frozenset({
    *(('L%02d' % number) for number in range(1, 13)),
    *(('LOG-%02d' % number) for number in range(1, 13)),
    'A-STATE', 'A-EDITOR', 'A-ORIGINAL', 'B-MODEL-6', 'B-RPC-6',
    'C-SCOPE', 'C-ATTACHMENT', 'C-TOKEN', 'C-REVOKED-PAGE',
    'D-ADMIT', 'D-NORMAL-6', 'D-FAILED-2', 'D-RECOVER-2',
    'D-LOST-REFUND-2', 'D-VERIFY-RETRY', 'E-PREBASELINE',
    'E-UPGRADE-S10-ONLY', 'E-PRESERVE', 'E-AFFECTED-REGRESSION',
})


def _environment_label(name):
    value = os.environ.get(name)
    return value if isinstance(value, str) and _LABEL.fullmatch(value) else None


def observed_http(component):
    def decorate(method):
        @wraps(method)
        def wrapped(*args, **kwargs):
            headers = request.httprequest.headers
            case_id = headers.get('X-YDental-Case-ID')
            operation_ref = headers.get('X-YDental-Operation-Ref')
            attempt = headers.get('X-YDental-Attempt')
            # Client labels are diagnostic hints only, never authorization.
            case_id = case_id if case_id in _CASE_IDS else None
            operation_ref = (hashlib.sha256(('ydental-client-operation:' + operation_ref).encode()).hexdigest()
                             if isinstance(operation_ref, str) and _LABEL.fullmatch(operation_ref) else None)
            attempt = int(attempt) if isinstance(attempt, str) and attempt.isascii() and attempt.isdecimal() and len(attempt) <= 4 else None
            token = bind_context(
                run_id=_environment_label('YDENTAL_RUN_ID'), task_id=_environment_label('YDENTAL_TASK_ID'),
                product_commit=_environment_label('YDENTAL_PRODUCT_COMMIT'),
                test_commit=_environment_label('YDENTAL_TEST_COMMIT'),
                core_commit=_environment_label('YDENTAL_CORE_COMMIT'),
                case_id=case_id, attempt=attempt, operation_ref=operation_ref,
                trace_id=uuid.uuid4().hex, request_id=uuid.uuid4().hex,
                actor_id=request.env.uid, effective_uid=request.env.uid, su_flag=request.env.su,
                component=component, stage='request.received', transaction_phase='IN_TRANSACTION',
            )
            try:
                emit_event('request.received')
                value = method(*args, **kwargs)
                emit_event('request.returned', stage='response.returned', outcome='returned')
                return value
            except Exception as error:
                record_exception(error, component)
                raise
            finally:
                reset_context(token)
        return wrapped
    return decorate

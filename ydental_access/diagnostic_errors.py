"""Attach a diagnostic code without changing the native RPC exception type."""
from odoo.exceptions import AccessError, UserError, ValidationError

from .diagnostics import ERROR_CODES


def native_error(error_type, message, code):
    if error_type not in (AccessError, UserError, ValidationError) or code not in ERROR_CODES:
        raise ValueError('INVALID_NATIVE_DIAGNOSTIC_ERROR')
    error = error_type(message)
    error.diagnostic_code = code
    return error

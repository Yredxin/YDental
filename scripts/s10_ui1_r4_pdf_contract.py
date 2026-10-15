"""Pure response classification for the UI1-R4 browser PDF gate."""

import json


RENDERER_ERRORS = frozenset({
    'Unable to find the pdf engine on this system. The PDF can not be created.',
    'The pdf engine on this system is not working.',
})


def classify_pdf_response(status, content_type, body):
    media_type = (content_type or '').split(';', 1)[0].strip().lower()
    if status == 200 and media_type == 'application/pdf':
        return 'PDF_200'
    if media_type != 'application/json' or not isinstance(body, bytes):
        return 'UNKNOWN_RESPONSE'
    try:
        payload = json.loads(body)
    except (UnicodeError, ValueError):
        return 'UNKNOWN_RESPONSE'
    if not isinstance(payload, dict) or not isinstance(payload.get('error'), str):
        return 'UNKNOWN_RESPONSE'
    error = payload['error'].strip()
    if status == 403 and error.startswith('access_denied:'):
        return 'ACCESS_DENIED'
    if status == 409 and error in RENDERER_ERRORS:
        return 'RENDERER_ONLY_ERROR'
    if status == 409 and error.startswith('version_conflict:'):
        return 'SCOPE_OR_VERSION_CONFLICT'
    if status == 409 and error.startswith('render_failed:'):
        return 'RENDER_FAILED_UNATTRIBUTED'
    return 'UNKNOWN_ERROR'

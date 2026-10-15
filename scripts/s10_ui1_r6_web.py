"""R6 browser request contract: credentials stay with their own page context."""

ACCESS = '/ydental/access'
ACTION = '/ydental/settlement/action'


def own_credentials(page, base):
    response = page.goto(base + ACCESS, wait_until='domcontentloaded')
    if response.status != 200:
        raise RuntimeError('own access page refused; STOP')
    form = page.locator('form[action="/ydental/access/action"]:has(input[name="operation"][value="switch"])')
    if form.count() != 1:
        raise RuntimeError('own access form missing; STOP')
    token = form.locator('input[name="csrf_token"]').input_value()
    revision = form.locator('input[name="revision"]').input_value()
    if not token or not revision.isdecimal():
        raise RuntimeError('own access credentials incomplete; STOP')
    return {'page_id': id(page), 'csrf_token': token, 'revision': revision}


def post(page, own, operation, payload, *, token_override=None):
    if own.get('page_id') != id(page) or not own.get('csrf_token') or not own.get('revision', '').isdecimal():
        raise RuntimeError('cross-role or incomplete credentials; STOP')
    if not isinstance(payload, dict) or not operation:
        raise RuntimeError('invalid request fixture; STOP')
    fields = {str(key): str(value) for key, value in payload.items()}
    fields.update(operation=operation, revision=own['revision'],
                  csrf_token=own['csrf_token'] if token_override is None else token_override)
    # Return the actual response class. Never silently treat a failed fetch as a refusal.
    result = page.evaluate('''async fields => {
        const body = new URLSearchParams(fields);
        const r = await fetch('/ydental/settlement/action', {method:'POST', body});
        const raw = await r.text();
        let data = null;
        if ((r.headers.get('content-type') || '').includes('application/json')) {
            try {data = JSON.parse(raw)} catch (_) {throw new Error('bad JSON response')}
        }
        return {sent:true, status:r.status, content_type:r.headers.get('content-type') || '',
                location:r.headers.get('location'), data,
                body_class: data ? 'json' : (raw.includes('<html') ? 'html' : 'other')};
    }''', fields)
    if result.get('sent') is not True or result.get('status') not in (200, 303, 400, 403, 409):
        raise RuntimeError('unexpected POST response; STOP')
    if result['status'] in (200, 403, 409) and result.get('body_class') != 'json':
        raise RuntimeError('application response is not JSON; STOP')
    if result['status'] in (403, 409) and (
            not isinstance(result.get('data'), dict) or not result['data'].get('error')):
        raise RuntimeError('refusal lacks a JSON error; STOP')
    return result

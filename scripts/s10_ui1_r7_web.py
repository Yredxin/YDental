"""R7 native close form inspection and own-session access credentials."""


def own_credentials(page, base):
    response = page.goto(base + '/ydental/access', wait_until='domcontentloaded')
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


def close_form_state(form):
    """Use the browser's native HTML5 validity checks; never submit by script."""
    field = form.locator('input[name="business_date"]')
    if field.count() != 1:
        raise RuntimeError('close date field missing; STOP')
    state = field.evaluate('''el => ({value:el.value,required:el.required,
        type:el.type,valid:el.validity.valid,
        validation_message:el.validationMessage})''')
    state['form_valid'] = form.evaluate('form => form.checkValidity()')
    state['invalid_fields'] = form.evaluate('''form => Array.from(form.elements)
        .filter(el => el.willValidate && !el.validity.valid)
        .map(el => ({name:el.name,type:el.type,required:el.required}))''')
    return state

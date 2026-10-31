const root = document.querySelector('.o_ydental_exam');
if (root) {
    let connection = sessionStorage.getItem('ydental_queue_connection');
    if (!connection) {
        connection = Array.from(crypto.getRandomValues(new Uint8Array(32)), b => b.toString(16).padStart(2, '0')).join('');
        sessionStorage.setItem('ydental_queue_connection', connection);
    }
    const holder = JSON.parse(sessionStorage.getItem('ydental_queue_holder') || 'null');
    const message = root.querySelector('#exam-message');
    let pending = false;
    let uncertain = false;
    let attempt = null;
    const checkable = new Set(['draft', 'perform', 'confirm', 'correct', 'abort', 'finish',
        'reconcile', 'verify_materials', 'attach']);
    const checkSubmission = root.querySelector('#exam-check-submission');
    checkSubmission.addEventListener('click', async () => {
        if (!attempt || pending) { return; }
        pending = true;
        checkSubmission.disabled = true;
        try {
            const response = await fetch('/ydental/exam/check-submission', {method: 'POST', credentials: 'same-origin', body: attempt});
            const result = await response.json();
            message.textContent = response.ok && result.status === 'committed' ? '本次操作已提交。请核对结果后返回工作台。' :
                '尚不能确认本次操作。请求可能仍在处理中，请由有权人员核查，未确认前不要重试。';
        } catch (_error) {
            message.textContent = '尚不能确认本次操作，请由有权人员核查，未确认前不要重试。';
        } finally {
            pending = false;
            checkSubmission.disabled = false;
        }
    });
    const random = () => Array.from(crypto.getRandomValues(new Uint8Array(24)), b => b.toString(16).padStart(2, '0')).join('');
    function showReconcile(form) {
        const reconcile = root.querySelector('#exam-reconcile');
        const lineId = Number(form.dataset.line);
        reconcile.href = Number.isSafeInteger(lineId) && lineId > 0 ?
            '/ydental/exam/result-view/' + lineId : '/ydental/exam';
        reconcile.hidden = false;
    }
    function measurements(form) {
        const result = {};
        for (const row of form.querySelectorAll('[data-measurement]')) {
            const status = row.querySelector('[name="measurement_status"]').value;
            if (!status) { continue; }
            const value = row.querySelector('[name="measurement_value"]').value;
            if (status === 'known' && (value === '' || !Number.isFinite(Number(value)))) {
                throw new Error('已测量项目需要有效数值。');
            }
            result[row.dataset.key] = {status, value: status === 'known' ? Number(value) : null,
                unit: row.dataset.unit};
        }
        return result;
    }
    function materials(form) {
        const result = [];
        for (const row of form.querySelectorAll('[data-material-row]')) {
            const select = row.querySelector('[name="lot_id"]');
            const qty = row.querySelector('[name="quantity"]').value;
            if (!select.value && !qty) { continue; }
            if (!select.value || !qty || Number(qty) <= 0) {
                throw new Error('耗材需要真实批次和正数量。');
            }
            result.push({lot_id: Number(select.value), quantity: Number(qty),
                uom_id: Number(select.selectedOptions[0].dataset.uom), kind: 'treatment'});
        }
        return result;
    }
    async function payload(form) {
        const data = Object.fromEntries(new FormData(form));
        const operation = form.dataset.operation;
        if (operation === 'grant_qualification') {
            return {user_id: Number(data.user_id), code: data.code,
                valid_from: data.valid_from.replace('T', ' '),
                valid_until: data.valid_until.replace('T', ' '), evidence: data.evidence};
        }
        if (operation === 'review_capability') {
            return {capability_id: Number(form.dataset.capability), family: data.family, reason: data.reason};
        }
        if (operation === 'bind_template') {
            return {catalog_id: Number(form.dataset.catalog), code: data.code, reason: data.reason,
                material_required: data.material_required === 'on'};
        }
        const line_id = Number(form.dataset.line);
        const version = Number(form.dataset.version);
        const actual = {line_id, execution_id: Number(root.dataset.execution), lease_id: holder?.lease_id,
            lease_token: holder?.token, inline: root.dataset.category === 'medical'};
        if (operation === 'draft') {
            return {...actual, version, findings: data.findings, conclusion: data.conclusion,
                measurements: measurements(form)};
        }
        if (operation === 'perform') {
            const {inline, ...external} = actual;
            return {...external, inline, reason: data.reason, materials: materials(form)};
        }
        if (operation === 'abort' || operation === 'finish') {
            return {...actual, reason: data.reason};
        }
        if (operation === 'confirm') { return {line_id, version, reason: data.reason}; }
        if (operation === 'correct') { return {line_id, version, findings: data.findings,
            measurements: measurements(form), conclusion: data.conclusion, reason: data.reason}; }
        if (operation === 'reconcile') { return {line_id, reason: data.reason}; }
        if (operation === 'verify_materials') { return {line_id, materials: materials(form), reason: data.reason}; }
        if (operation === 'attach') {
            const file = form.querySelector('[name="evidence"]').files[0];
            if (!file || file.size < 1 || file.size > 5000000 ||
                !['image/jpeg', 'image/png', 'application/pdf'].includes(file.type)) {
                throw new Error('请选择不超过5MB的JPEG、PNG或PDF证据文件。');
            }
            const encoded = await new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = () => resolve(String(reader.result).split(',')[1]);
                reader.onerror = reject;
                reader.readAsDataURL(file);
            });
            return {line_id, version, filename: file.name, mimetype: file.type, encoded};
        }
        if (operation === 'release_editor') { return {line_id, version}; }
        if (operation === 'takeover') { return {line_id, version, reason: data.reason}; }
        if (operation === 'revalidate') { const {inline, ...medical} = actual; return {...medical, document_id: Number(root.dataset.document),
            document_version: Number(root.dataset.documentVersion), reason: data.reason}; }
        throw new Error('invalid_action');
    }
    for (const form of root.querySelectorAll('form[data-operation]')) {
        const operation = form.dataset.operation;
        const needsExecution = ['draft', 'perform', 'abort', 'finish', 'revalidate'].includes(operation);
        const permission = operation === 'grant_qualification' ? root.dataset.qualificationWrite === '1' :
            operation === 'revalidate' || root.dataset.write === '1';
        form.dataset.allowed = String(Boolean(permission && (!needsExecution ||
            (Number(root.dataset.execution) > 0 && holder?.lease_id && holder?.token))));
        form.querySelectorAll('input,textarea,select,button').forEach(control => { control.disabled = form.dataset.allowed !== 'true'; });
        const actionKey = random();
        form.addEventListener('submit', async event => {
            event.preventDefault();
            if (pending || uncertain || form.dataset.allowed !== 'true') { return; }
            if (!window.confirm('请核对真实检查、文书与费用来源后确认操作。')) { return; }
            const before = JSON.stringify([...new FormData(form)].map(([name, value]) =>
                [name, value instanceof File ? [value.name, value.size, value.lastModified] : value]));
            const argsPromise = payload(form);
            pending = true;
            root.querySelectorAll('input,textarea,select,button').forEach(control => { control.disabled = true; });
            let dispatched = false;
            try {
                const args = await argsPromise;
                const check = new URLSearchParams({operation, payload: JSON.stringify(args), key: actionKey,
                    csrf_token: odoo.csrf_token});
                const action = new URLSearchParams({operation, revision: root.dataset.revision, connection,
                    payload: JSON.stringify(args), key: actionKey, csrf_token: odoo.csrf_token});
                if (check.toString().length > 7500000 || action.toString().length > 7500000) {
                    throw new Error('内容过大，本次未发送；请重新打开页面并缩小附件。');
                }
                attempt = checkable.has(operation) && Number.isSafeInteger(args.line_id) &&
                    args.line_id > 0 && args.line_id <= 2147483647 ? check : null;
                dispatched = true;
                const response = await fetch('/ydental/exam/action', {method: 'POST', credentials: 'same-origin',
                    body: action});
                const result = await response.json();
                if (!response.ok) { throw new Error(result.error); }
                root.querySelectorAll('input,textarea,select,button').forEach(control => {
                    control.disabled = control.closest('form')?.dataset.allowed !== 'true';
                });
                if (before !== JSON.stringify([...new FormData(form)].map(([name, value]) =>
                    [name, value instanceof File ? [value.name, value.size, value.lastModified] : value]))) {
                    uncertain = true;
                    showReconcile(form);
                    checkSubmission.hidden = !attempt;
                    checkSubmission.disabled = false;
                    message.textContent = attempt ? '表单在响应期间变化，请核对原始记录。' :
                        '表单在响应期间变化，请由有权人员人工核查，未确认前不要重试。';
                    return;
                }
                if (operation === 'finish' && root.dataset.category === 'exam') {
                    sessionStorage.removeItem('ydental_queue_holder');
                }
                window.location.reload();
            } catch (error) {
                if (!dispatched) {
                    message.textContent = error.message || '本次未发送，请核对输入。';
                    root.querySelectorAll('input,textarea,select,button').forEach(control => {
                        control.disabled = control.closest('form')?.dataset.allowed !== 'true';
                    });
                    return;
                }
                message.textContent = attempt ? (error.message || '结果未知，请核对服务端原始记录。') :
                    ((error.message || '结果未知。') + ' 请由有权人员人工核查，未确认前不要重试。');
                uncertain = true;
                showReconcile(form);
                checkSubmission.hidden = !attempt;
                checkSubmission.disabled = false;
            } finally {
                pending = false;
            }
        });
    }
}

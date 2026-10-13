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
    const random = () => Array.from(crypto.getRandomValues(new Uint8Array(24)), b => b.toString(16).padStart(2, '0')).join('');
    function payload(form) {
        const data = Object.fromEntries(new FormData(form));
        const operation = form.dataset.operation;
        const line_id = Number(form.dataset.line);
        const version = Number(form.dataset.version);
        const actual = {line_id, execution_id: Number(root.dataset.execution), lease_id: holder?.lease_id,
            lease_token: holder?.token, inline: root.dataset.category === 'medical'};
        if (operation === 'draft') {
            return {...actual, version, findings: data.findings, conclusion: data.conclusion, measurements: {}};
        }
        if (operation === 'perform') {
            const {inline, ...external} = actual;
            return {...external, inline, reason: data.reason, materials: []};
        }
        if (operation === 'abort' || operation === 'finish') {
            const {inline, ...external} = actual;
            return {...external, reason: data.reason};
        }
        if (operation === 'confirm') { return {line_id, version, reason: data.reason}; }
        if (operation === 'correct') { return {line_id, version, findings: data.findings,
            measurements: {}, conclusion: data.conclusion, reason: data.reason}; }
        if (operation === 'reconcile') { return {line_id, reason: data.reason}; }
        throw new Error('invalid_action');
    }
    for (const form of root.querySelectorAll('form[data-operation]')) {
        const operation = form.dataset.operation;
        const needsExecution = ['draft', 'perform', 'abort', 'finish'].includes(operation);
        form.dataset.allowed = String(root.dataset.write === '1' && (!needsExecution ||
            (Number(root.dataset.execution) > 0 && holder?.lease_id && holder?.token)));
        form.querySelectorAll('input,textarea,button').forEach(control => { control.disabled = form.dataset.allowed !== 'true'; });
        form.dataset.key = random();
        form.addEventListener('submit', async event => {
            event.preventDefault();
            if (pending || uncertain || form.dataset.allowed !== 'true') { return; }
            if (!window.confirm('请核对真实检查、文书与费用来源后确认操作。')) { return; }
            const before = JSON.stringify([...new FormData(form)]);
            const args = payload(form);
            pending = true;
            root.querySelectorAll('input,textarea,button').forEach(control => { control.disabled = true; });
            try {
                const response = await fetch('/ydental/exam/action', {method: 'POST', credentials: 'same-origin',
                    body: new URLSearchParams({operation, revision: root.dataset.revision, connection,
                        payload: JSON.stringify(args), key: form.dataset.key, csrf_token: odoo.csrf_token})});
                const result = await response.json();
                if (!response.ok) { throw new Error(result.error); }
                root.querySelectorAll('input,textarea,button').forEach(control => {
                    control.disabled = control.closest('form')?.dataset.allowed !== 'true';
                });
                if (before !== JSON.stringify([...new FormData(form)])) {
                    uncertain = true;
                    root.querySelector('#exam-reconcile').hidden = false;
                    message.textContent = '表单在响应期间变化，请核对原始记录。';
                    return;
                }
                if (operation === 'finish') { sessionStorage.removeItem('ydental_queue_holder'); }
                window.location.reload();
            } catch (error) {
                message.textContent = error.message || '结果未知，请核对服务端原始记录。';
                uncertain = true;
                root.querySelector('#exam-reconcile').hidden = false;
            } finally {
                pending = false;
            }
        });
    }
}

const root = document.querySelector('.o_ydental_treatment');
if (root) {
    const connection = sessionStorage.getItem('ydental_queue_connection');
    const holder = JSON.parse(sessionStorage.getItem('ydental_queue_holder') || 'null');
    const message = root.querySelector('#treatment-result');
    const check = root.querySelector('#treatment-reconcile');
    let pending = false;
    let uncertain = false;
    const random = () => Array.from(crypto.getRandomValues(new Uint8Array(24)), b => b.toString(16).padStart(2, '0')).join('');
    const medical = () => ({execution_id: Number(root.dataset.execution), lease_id: holder?.lease_id,
        lease_token: holder?.token, document_id: Number(root.dataset.document), document_version: Number(root.dataset.version)});
    const utc = value => value.replace('T', ' ') + (value.length === 16 ? ':00' : '');
    function payload(form) {
        const data = Object.fromEntries(new FormData(form));
        const op = form.dataset.operation;
        const order = form.closest('[data-order]');
        const line = form.closest('[data-line]');
        const event = form.closest('[data-event]');
        const actual = medical();
        const pharmacy = {execution_id: actual.execution_id, lease_id: actual.lease_id, lease_token: actual.lease_token,
            order_id: Number(order?.dataset.order), order_version: Number(order?.dataset.orderVersion)};
        if (op === 'execute') {
            const batch = form.querySelector('[name="lot_id"] option:checked');
            const tooth = Number(data.tooth);
            return {...actual, catalog_id: Number(data.catalog_id), quantity: Number(data.quantity), source: form.dataset.source,
                reason: data.reason, already_performed: data.already_performed === 'on', policy: 'demo_confirmation',
                materials: data.lot_id ? [{lot_id: Number(data.lot_id), quantity: Number(data.material_quantity),
                    uom_id: Number(batch.dataset.uom), kind: batch.dataset.kind}] : [],
                teeth: [{tooth, state: tooth ? 'present' : 'not_applicable', surfaces: data.surfaces ? data.surfaces.split(',').map(s => s.trim()) : []}]};
        }
        if (op === 'order') {
            const rows = [...form.querySelectorAll('.o_ydental_treatment_line')].map(row => {
                const input = name => row.querySelector(`[name="${name}"]`).value;
                return {mapping_id: Number(input('mapping_id')), quantity: Number(input('quantity')),
                    uom_id: Number(row.querySelector('[name="mapping_id"] option:checked').dataset.uom),
                    product_id: Number(input('product_id')) || false, specification: input('specification'),
                    usage: input('usage'), frequency: input('frequency'), course: input('course')};
            });
            return {...actual, kind: data.kind, purpose: data.purpose, lines: rows};
        }
        if (op === 'issue') { return {...actual, order_id: pharmacy.order_id, version: pharmacy.order_version}; }
        if (op === 'cancel_exam') { return {...actual, line_id: Number(line.dataset.line), order_version: pharmacy.order_version, reason: data.reason}; }
        if (op === 'dispense') { return {...pharmacy, line_id: Number(line.dataset.line), lot_id: Number(data.lot_id),
            quantity: Number(data.quantity), reason: data.reason, source: form.dataset.source, policy: 'demo_confirmation'}; }
        if (op === 'finish') { return {...pharmacy, reason: data.reason}; }
        if (op === 'reconcile') { return {event_id: Number(event.dataset.event), reason: data.reason}; }
        if (op === 'correct') { return {...actual, event_id: Number(event.dataset.event), delta: Number(data.delta),
            source: form.dataset.source, reason: data.reason, materials: []}; }
        if (op === 'refer') { return {...actual, mapping_id: Number(data.mapping_id), mode: data.mode, source: form.dataset.source,
            reason: data.reason, ...(data.mode === 'timed' ? {start: utc(data.start), end: utc(data.end)} : {valid_until: utc(data.valid_until)})}; }
        throw new Error('invalid_action');
    }
    for (const button of root.querySelectorAll('.add-order-line')) {
        button.addEventListener('click', () => {
            const rows = button.form.querySelector('.o_ydental_treatment_lines');
            if (rows.children.length >= 16) { return; }
            const row = rows.firstElementChild.cloneNode(true);
            row.querySelectorAll('input,select').forEach(input => { input.value = ''; });
            rows.append(row);
        });
    }
    for (const form of root.querySelectorAll('form[data-operation]')) {
        form.dataset.key = random();
        form.dataset.source = random();
        form.addEventListener('submit', async event => {
            event.preventDefault();
            if (pending || uncertain || !connection) { return; }
            const args = payload(form);
            if (!window.confirm(root.querySelector('#treatment-confirm').textContent)) { return; }
            const before = JSON.stringify([...new FormData(form)]);
            pending = true;
            root.querySelectorAll('input,select,button').forEach(input => { input.disabled = true; });
            try {
                const response = await fetch('/ydental/treatment/action', {method: 'POST', credentials: 'same-origin',
                    body: new URLSearchParams({operation: form.dataset.operation, revision: root.dataset.revision, connection,
                        key: form.dataset.key, payload: JSON.stringify(args), csrf_token: odoo.csrf_token})});
                const result = await response.json();
                if (!response.ok) { throw new Error(result.error); }
                // Keep a reviewable receipt and never replay a possibly committed
                // execution. Reload only when the full visible form is unchanged.
                root.querySelectorAll('input,select,button').forEach(input => { input.disabled = false; });
                message.textContent = JSON.stringify(result);
                if (before !== JSON.stringify([...new FormData(form)])) {
                    uncertain = true;
                    check.hidden = false;
                    message.textContent += ' / ' + root.querySelector('#treatment-offline').textContent;
                    return;
                }
                if (form.dataset.operation === 'finish') { sessionStorage.removeItem('ydental_queue_holder'); }
                window.location.reload();
            } catch (error) {
                uncertain = true;
                check.hidden = false;
                message.textContent = (error.message || '') + ' / ' + root.querySelector('#treatment-offline').textContent;
            } finally {
                pending = false;
                root.querySelectorAll('input,select,button').forEach(input => { input.disabled = uncertain; });
            }
        });
    }
    if (holder && connection) {
        setInterval(async () => {
            if (pending || uncertain) { return; }
            try {
                const response = await fetch('/ydental/queue/action', {method: 'POST', credentials: 'same-origin',
                    body: new URLSearchParams({operation: 'heartbeat', revision: root.dataset.revision, connection,
                        payload: JSON.stringify({lease_id: holder.lease_id, token: holder.token}), csrf_token: odoo.csrf_token})});
                if (!response.ok) { throw new Error(); }
            } catch {
                uncertain = true;
                check.hidden = false;
                message.textContent = root.querySelector('#treatment-offline').textContent;
                root.querySelectorAll('input,select,button').forEach(input => { input.disabled = true; });
            }
        }, Number(root.dataset.heartbeat) * 1000);
    }
}

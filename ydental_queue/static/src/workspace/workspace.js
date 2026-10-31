const workspace = document.querySelector('.o_ydental_queue_workspace');
if (workspace) {
    const storageKey = 'ydental_queue_holder';
    const connectionKey = 'ydental_queue_connection';
    let connection = sessionStorage.getItem(connectionKey);
    if (!connection) {
        const bytes = crypto.getRandomValues(new Uint8Array(32));
        connection = Array.from(bytes, (byte) => byte.toString(16).padStart(2, '0')).join('');
        sessionStorage.setItem(connectionKey, connection);
    }
    const resultNode = workspace.querySelector('#queue-result');
    const ownId = Number(workspace.querySelector('#holding-workstation')?.dataset.lease || 0);
    const canWrite = workspace.dataset.canWrite === 'yes';
    let holder = JSON.parse(sessionStorage.getItem(storageKey) || 'null');
    if (holder && holder.lease_id !== ownId) {
        holder = null;
        sessionStorage.removeItem(storageKey);
    }
    async function action(operation, extra = {}, quiet = false) {
        const reception = ['enter', 'expire_station', 'append', 'revoke', 'query_return', 'report', 'takeover_verify', 'handover_verify_hold', 'business', 'screen_create', 'screen_revoke'].includes(operation);
        const payload = reception ? extra : {...extra, lease_id: holder?.lease_id, token: holder?.token};
        try {
            const response = await fetch(operation === 'report' ? '/ydental/intake/action' : '/ydental/queue/action', {
                method: 'POST',
                body: new URLSearchParams({operation, revision: workspace.dataset.revision, connection,
                    csrf_token: workspace.querySelector('[name=csrf_token]').value, payload: JSON.stringify(payload),
                    key: crypto.randomUUID(), output: 'json'}),
            });
            const result = await response.json();
            if (!response.ok) {
                if (result.result === 'connection_expired') {
                    sessionStorage.removeItem(storageKey);
                    holder = null;
                }
                resultNode.textContent = result.error || workspace.querySelector('#expired-message').textContent;
                return;
            }
            if (['enter', 'switch', 'takeover_verify', 'handover_verify_hold'].includes(operation)) {
                sessionStorage.setItem(storageKey, JSON.stringify(result));
            } else if (operation === 'exit') {
                sessionStorage.removeItem(storageKey);
            }
            if (operation === 'screen_create') {
                const link = document.createElement('a');
                link.href = '/ydental/queue/screen?lang=' + encodeURIComponent(workspace.dataset.lang) + '#token=' + encodeURIComponent(result.token);
                link.textContent = workspace.querySelector('#screen-open-message').textContent;
                resultNode.replaceChildren(link);
                return;
            }
            if (operation === 'query_return') {
                resultNode.textContent = [result.message, result.area, result.station].filter(Boolean).join(' / ');
                return;
            }
            if (!quiet) {
                window.location.reload();
            }
        } catch {
            resultNode.textContent = workspace.querySelector('#offline-message').textContent;
        }
    }
    for (const button of workspace.querySelectorAll('[data-operation]')) {
        const operation = button.dataset.operation;
        button.disabled = button.disabled || (!['enter', 'expire_station'].includes(operation) && !holder);
        button.addEventListener('click', () => action(operation, {
            ...(button.dataset.station ? {station_id: Number(button.dataset.station)} : {}),
            ...(button.dataset.entry ? {entry_id: Number(button.dataset.entry)} : {}),
        }));
    }
    for (const form of workspace.querySelectorAll('[data-queue-form]')) {
        const operation = form.dataset.queueForm;
        if (!['append', 'revoke', 'query_return', 'report', 'takeover_verify', 'handover_verify_hold', 'business', 'screen_create', 'screen_revoke'].includes(operation) && !holder) {
            form.querySelector('button').disabled = true;
        }
        form.addEventListener('submit', (event) => {
            event.preventDefault();
            const extra = {};
            for (const [name, value] of new FormData(form)) {
                extra[name] = name.endsWith('_id') || name === 'version' ? Number(value) : value;
            }
            if (['restore', 'takeover_verify', 'handover_verify_hold'].includes(operation)) {
                extra.confirmed = form.querySelector('[name=confirmed]').checked;
            }
            action(operation, extra);
        });
    }
    const heartbeat = Number(workspace.dataset.heartbeat);
    if (canWrite && holder && heartbeat > 0) {
        window.setInterval(() => { if (holder) { action('heartbeat', {}, true); } }, heartbeat * 1000);
    }
}

const root = document.querySelector('.o_ydental_clinical');
if (root) {
    let documentId = Number(root.dataset.document);
    let version = Number(root.dataset.version);
    let state = root.dataset.state;
    let token = null;
    let dirty = false;
    let saving = false;
    let failed = false;
    let selected = null;
    let generation = 0;
    let timer;
    const teeth = new Map();
    const result = root.querySelector('#clinical-result');
    const textFields = [...root.querySelectorAll('textarea[name]')];
    let connection = sessionStorage.getItem('ydental_queue_connection');
    if (!connection) {
        connection = Array.from(crypto.getRandomValues(new Uint8Array(32)), b => b.toString(16).padStart(2, '0')).join('');
        sessionStorage.setItem('ydental_queue_connection', connection);
    }
    const holder = JSON.parse(sessionStorage.getItem('ydental_queue_holder') || 'null');
    const message = id => root.querySelector('#' + id).textContent;
    const editorKey = () => 'ydental_clinical_editor_' + documentId;
    function permissions() {
        textFields.forEach(field => { field.disabled = !token; });
        for (const id of ['save-document', 'confirm-document', 'correct-document', 'handover-document', 'release-document']) {
            root.querySelector('#' + id).disabled = !token || saving || failed;
        }
        root.querySelector('#save-document').disabled ||= state === 'confirmed';
        root.querySelector('#confirm-document').disabled ||= state === 'confirmed';
        root.querySelector('#correct-document').disabled ||= state !== 'confirmed';
        root.querySelector('#handover-document').disabled ||= !holder || root.dataset.canHandover !== 'yes';
        root.querySelector('#tooth-state').disabled = !token || selected === null;
    }
    function summary() {
        const list = root.querySelector('#tooth-summary');
        list.replaceChildren(...[...teeth.values()].sort((a,b) => a.tooth-b.tooth).map(row => {
            const li = document.createElement('li');
            li.textContent = `${row.tooth || '-'} / ${root.querySelector(`#tooth-state option[value="${row.state}"]`).textContent} / ${row.surfaces.join(', ')}`;
            return li;
        }));
    }
    function select(tooth) {
        selected = tooth;
        root.querySelector('#selected-tooth').textContent = tooth || '-';
        const row = teeth.get(tooth) || {tooth, state: tooth ? 'unknown' : 'not_applicable', surfaces: []};
        const stateSelect = root.querySelector('#tooth-state');
        stateSelect.value = row.state;
        for (const option of stateSelect.options) {
            option.disabled = tooth ? option.value === 'not_applicable' : option.value !== 'not_applicable';
        }
        const allowed = ['M', 'D', 'B', 'L', tooth % 10 <= 3 ? 'I' : 'O'];
        for (const box of root.querySelectorAll('#surfaces input')) {
            box.disabled = !token || !tooth || row.state !== 'present' || !allowed.includes(box.value);
            box.checked = row.surfaces.includes(box.value);
        }
        permissions();
    }
    function content() {
        return Object.fromEntries(textFields.map(field => [field.name, field.value]).concat([['teeth', [...teeth.values()]]]));
    }
    function load(data) {
        documentId = data.document_id;
        version = data.version;
        state = data.state;
        root.querySelector('#server-version').textContent = version;
        root.querySelector('#server-save').textContent = data.saved_at || '-';
        if (root.querySelector('#text-state')) { root.querySelector('#text-state').textContent = state; }
        textFields.forEach(field => { field.value = data.content[field.name]; });
        teeth.clear();
        data.content.teeth.forEach(row => teeth.set(row.tooth, row));
        summary();
        permissions();
    }
    async function action(operation, payload) {
        const response = await fetch('/ydental/clinical/action', {method: 'POST', body: new URLSearchParams({
            operation, payload: JSON.stringify(payload), revision: root.dataset.revision, connection,
            csrf_token: root.querySelector('[name=csrf_token]').value,
        })});
        const data = await response.json();
        if (!response.ok) { throw new Error(data.error); }
        return data;
    }
    function changed() {
        if (!token) { return; }
        dirty = true;
        generation++;
        result.textContent = message('unsynced-message');
        clearTimeout(timer);
        if (state !== 'confirmed' && !failed) { timer = setTimeout(() => save('save'), 900); }
    }
    async function save(operation) {
        if (!token || saving || failed) { return; }
        clearTimeout(timer);
        saving = true;
        permissions();
        const captured = generation;
        const payload = {document_id: documentId, editor_token: token, expected_version: version,
            content: content(), key: crypto.randomUUID()};
        if (operation === 'correct') { payload.reason = root.querySelector('#correction-reason').value; }
        if (operation === 'handover') {
            payload.lease_id = holder?.lease_id;
            payload.lease_token = holder?.token;
        }
        try {
            const data = await action(operation, payload);
            version = data.version;
            state = data.state === 'handover' ? state : data.state;
            root.querySelector('#server-version').textContent = version;
            root.querySelector('#server-save').textContent = data.saved_at || root.querySelector('#server-save').textContent;
            dirty = captured !== generation;
            result.textContent = message(dirty ? 'unsynced-message' : 'saved-message');
            if (operation === 'handover') {
                token = null;
                sessionStorage.removeItem(editorKey());
                window.location.assign('/ydental/clinical?document_id=' + documentId);
            } else if (operation !== 'save') {
                sessionStorage.removeItem(editorKey());
                await action('release', {document_id: documentId, editor_token: token});
                token = null;
                window.location.assign('/ydental/clinical?document_id=' + documentId);
            }
        } catch (error) {
            failed = true;
            dirty = true;
            result.textContent = error.message || message('offline-message');
        } finally {
            saving = false;
            permissions();
            if (dirty && !failed && state !== 'confirmed') { timer = setTimeout(() => save('save'), 900); }
        }
    }
    root.querySelector('#open-document').addEventListener('click', async () => {
        try {
            const stored = sessionStorage.getItem(editorKey());
            if (documentId && stored) {
                await action('heartbeat', {document_id: documentId, editor_token: stored});
                token = stored;
            } else {
                const data = await action(documentId ? 'acquire' : 'open', documentId ? {
                    document_id: documentId, lease_id: holder?.lease_id, lease_token: holder?.token,
                } : {execution_id: Number(root.dataset.execution), lease_id: holder?.lease_id, lease_token: holder?.token});
                load(data);
                token = data.editor_token;
                sessionStorage.setItem(editorKey(), token);
                // Preserve the document identity on refresh without another server write.
                history.replaceState(null, '', '/ydental/clinical?document_id=' + documentId);
            }
            failed = false;
            result.textContent = message('saved-message');
            permissions();
        } catch (error) { result.textContent = error.message || message('offline-message'); }
    });
    root.querySelector('#release-document').addEventListener('click', async () => {
        if (dirty || saving) { result.textContent = message('unsynced-message'); return; }
        try {
            await action('release', {document_id: documentId, editor_token: token});
            token = null;
            sessionStorage.removeItem(editorKey());
            permissions();
            result.textContent = message('readonly-message');
        } catch (error) { result.textContent = error.message || message('offline-message'); }
    });
    for (const [id, operation] of [['save-document', 'save'], ['confirm-document', 'confirm'], ['correct-document', 'correct'], ['handover-document', 'handover']]) {
        root.querySelector('#' + id).addEventListener('click', () => save(operation));
    }
    textFields.forEach(field => field.addEventListener('input', changed));
    root.querySelectorAll('[data-tooth]').forEach(button => button.addEventListener('click', () => select(Number(button.dataset.tooth))));
    root.querySelector('#no-tooth').addEventListener('click', () => {
        select(0);
        if (token) { teeth.set(0, {tooth: 0, state: 'not_applicable', surfaces: []}); summary(); changed(); }
    });
    root.querySelector('#tooth-state').addEventListener('change', event => {
        if (!token || selected === null) { return; }
        teeth.set(selected, {tooth: selected, state: event.target.value, surfaces: []});
        select(selected); summary(); changed();
    });
    root.querySelectorAll('#surfaces input').forEach(box => box.addEventListener('change', () => {
        if (!token || selected === null) { return; }
        teeth.set(selected, {tooth: selected, state: 'present', surfaces: [...root.querySelectorAll('#surfaces input:checked')].map(b => b.value)});
        summary(); changed();
    }));
    root.querySelector('#transfer-document')?.addEventListener('click', async () => {
        try {
            await action('transfer', {document_id: documentId, expected_version: version,
                user_id: Number(root.querySelector('#transfer-user').value), reason: root.querySelector('#transfer-reason').value});
            window.location.reload();
        } catch (error) { result.textContent = error.message || message('offline-message'); }
    });
    for (const li of root.querySelectorAll('#tooth-summary [data-row]')) {
        teeth.set(Number(li.dataset.row), {tooth: Number(li.dataset.row), state: li.dataset.state, surfaces: li.dataset.surfaces.split(',').filter(Boolean)});
    }
    setInterval(async () => {
        try {
            if (saving) { return; }
            if (holder && Number(root.dataset.execution)) {
                const response = await fetch('/ydental/queue/action', {method: 'POST', body: new URLSearchParams({
                    operation: 'heartbeat', revision: root.dataset.revision, connection,
                    csrf_token: root.querySelector('[name=csrf_token]').value, payload: JSON.stringify({lease_id: holder.lease_id, token: holder.token}),
                })});
                if (!response.ok) { throw new Error(message('offline-message')); }
            }
            if (token) { await action('heartbeat', {document_id: documentId, editor_token: token}); }
        } catch (error) { failed = true; result.textContent = error.message || message('offline-message'); permissions(); }
    }, Number(root.dataset.heartbeat) * 1000);
    window.addEventListener('offline', () => { failed = true; result.textContent = message('offline-message'); permissions(); });
    window.addEventListener('beforeunload', event => { if (dirty) { event.preventDefault(); event.returnValue = ''; } });
    permissions();
}

function start() {
    const root = document.querySelector('.o_ydental_print');
    if (!root) { return; }
    const field = (id) => root.querySelector(`#print-${id}`);
    const messages = Object.fromEntries([...root.querySelectorAll('[data-message]')].map((el) => [el.dataset.message, el.textContent]));
    let reviewed = null;
    let job = null;
    let busy = false;
    let blobUrl = null;
    let generationKey = null;
    function permissions() {
        for (const el of root.querySelectorAll('input:not([type=hidden]),select,button')) { el.disabled = busy; }
        field('generate').disabled = busy || !reviewed;
        for (const id of ['view', 'download', 'request']) { field(id).disabled = busy || !job; }
    }
    function selection() {
        return {kind: field('kind').value, source_id: Number(field('source').value), version: Number(field('version').value), purpose: field('purpose').value || null};
    }
    function resetFrame(id) {
        const previous = field(id);
        const fresh = previous.cloneNode(false);
        fresh.removeAttribute('src');
        fresh.removeAttribute('srcdoc');
        fresh.hidden = true;
        previous.replaceWith(fresh);
        return fresh;
    }
    function invalidate() {
        reviewed = null;
        job = null;
        generationKey = null;
        resetFrame('html');
        resetFrame('pdf');
        field('provenance').textContent = '';
        if (blobUrl) { URL.revokeObjectURL(blobUrl); blobUrl = null; }
        permissions();
    }
    for (const id of ['kind', 'source', 'version', 'purpose']) { field(id).addEventListener('input', invalidate); }
    field('choice').addEventListener('change', () => {
        const option = field('choice').selectedOptions[0];
        if (option.dataset.kind) {
            field('kind').value = option.dataset.kind;
            field('source').value = option.value;
            field('version').value = option.dataset.version;
            field('purpose').value = '';
        }
        invalidate();
    });
    async function operate(operation) {
        if (busy) { return; }
        const printWindow = operation === 'print_request' ? window.open('about:blank', '_blank') : null;
        const submitted = JSON.stringify(selection());
        const selected = selection();
        const payload = operation === 'preview' ? selected : operation === 'generate' ? {...selected, expected_digest: reviewed.source_digest, key: generationKey} : {job_id: job.job_id};
        busy = true;
        permissions();
        field('result').textContent = messages.busy;
        try {
            const response = await fetch('/ydental/print/action', {method: 'POST', body: new URLSearchParams({operation, revision: root.dataset.revision, csrf_token: root.querySelector('[name=csrf_token]').value, payload: JSON.stringify(payload)})});
            if (!response.ok) { throw new Error('request_failed'); }
            if (submitted !== JSON.stringify(selection())) { throw new Error('selection_changed'); }
            if (operation === 'preview') {
                reviewed = await response.json();
                generationKey = crypto.randomUUID();
                const frame = resetFrame('html');
                frame.srcdoc = reviewed.html;
                frame.hidden = false;
                field('provenance').textContent = `${reviewed.template} / SHA256 ${reviewed.source_digest} / ${JSON.stringify(reviewed.versions)}`;
                field('result').textContent = messages.reviewed;
            } else if (operation === 'generate') {
                job = await response.json();
                field('result').textContent = messages.generated;
                field('provenance').textContent += ` / PDF SHA256 ${job.pdf_digest}`;
            } else {
                if (!response.headers.get('Content-Type')?.startsWith('application/pdf')) { throw new Error('invalid_pdf'); }
                const bytes = new Uint8Array(await response.arrayBuffer());
                if (new TextDecoder().decode(bytes.slice(0, 5)) !== '%PDF-') { throw new Error('invalid_pdf'); }
                if (blobUrl) { URL.revokeObjectURL(blobUrl); }
                blobUrl = URL.createObjectURL(new Blob([bytes], {type: 'application/pdf'}));
                if (operation === 'download') {
                    const a = document.createElement('a');
                    a.href = blobUrl;
                    a.download = 'ydental-demonstration.pdf';
                    a.click();
                    field('result').textContent = messages.downloaded;
                } else if (operation === 'print_request') {
                    if (printWindow) {
                        printWindow.opener = null;
                        printWindow.location.replace(blobUrl);
                        field('result').textContent = messages.print_requested;
                    } else {
                        field('result').textContent = messages.dialog_failed;
                    }
                } else {
                    resetFrame('html');
                    const frame = resetFrame('pdf');
                    frame.hidden = false;
                    frame.src = blobUrl;
                    frame.scrollIntoView({block: 'start'});
                    field('result').textContent = messages.viewed;
                }
            }
        } catch {
            if (printWindow) { printWindow.close(); }
            invalidate();
            field('result').textContent = messages.failed;
        } finally {
            busy = false;
            permissions();
        }
    }
    for (const [id, operation] of [['preview', 'preview'], ['generate', 'generate'], ['view', 'pdf_view'], ['download', 'download'], ['request', 'print_request']]) {
        field(id).addEventListener('click', () => operate(operation));
    }
    window.addEventListener('pagehide', () => { if (blobUrl) { URL.revokeObjectURL(blobUrl); } });
    permissions();
}
if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', start); }
else { start(); }

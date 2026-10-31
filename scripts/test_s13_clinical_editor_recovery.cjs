'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('ydental_clinical/static/src/document/document.js', 'utf8');

function setup(replies) {
    const calls = [];
    const listeners = new Map();
    const nodes = new Map();
    const storage = new Map([
        ['ydental_queue_connection', 'connection'],
        ['ydental_queue_holder', JSON.stringify({lease_id: 10, token: 'lease'})],
        ['ydental_clinical_editor_9', 'expired-token'],
        ['ydental_clinical_editor_10', 'unrelated-token'],
    ]);
    const textField = {name: 'chief_complaint', value: 'server text', addEventListener(event, handler) { listeners.set('textarea:' + event, handler); }};
    const root = {
        dataset: {document: '9', version: '2', state: 'draft', execution: '3', heartbeat: '30', revision: '1', canHandover: 'yes'},
        querySelector(selector) {
            if (selector === '#text-state' || selector === '#transfer-document' || selector === '#complete-document') { return null; }
            if (!nodes.has(selector)) {
                nodes.set(selector, {value: '', textContent: selector === '#editor-expired-retry-message' ? 'REOPEN' : selector,
                    dataset: {}, options: [], addEventListener(event, handler) { listeners.set(selector + ':' + event, handler); },
                    replaceChildren() {}});
            }
            return nodes.get(selector);
        },
        querySelectorAll(selector) { return selector === 'textarea[name]' ? [textField] : []; },
    };
    let interval;
    const context = {
        document: {querySelector: () => root, createElement: () => ({})},
        sessionStorage: {getItem: key => storage.get(key) ?? null, setItem: (key, value) => storage.set(key, value), removeItem: key => storage.delete(key)},
        window: {addEventListener() {}, location: {assign() {}, reload() {}}},
        history: {replaceState() {}}, navigator: {onLine: true}, URLSearchParams,
        crypto: {getRandomValues: array => array, randomUUID: () => 'test-key'},
        setInterval: handler => { interval = handler; }, setTimeout: () => 1, clearTimeout() {},
        fetch: async (_url, opts) => {
            const op = opts.body.get('operation');
            calls.push(op);
            if (op === 'heartbeat' && _url === '/ydental/queue/action') { return {ok: true}; }
            const next = await replies.shift();
            if (next instanceof Error) { throw next; }
            return {ok: next.status === 200, status: next.status, json: async () => next.body};
        },
    };
    vm.runInNewContext(source, context, {filename: 'document.js'});
    return {calls, storage, listeners, nodes, textField, interval};
}

(async () => {
    const expired = setup([{status: 403, body: {error: 'editor_expired: old editor'}},
        {status: 200, body: {result: 'accepted', document_id: 9, version: 2, state: 'draft', editor_token: 'new-token', content: {chief_complaint: 'server text', teeth: []}}}]);
    await expired.listeners.get('#open-document:click')();
    assert.deepEqual(expired.calls, ['heartbeat']);
    assert.equal(expired.storage.has('ydental_clinical_editor_9'), false);
    assert.equal(expired.storage.get('ydental_clinical_editor_10'), 'unrelated-token');
    assert.equal(expired.nodes.get('#clinical-result').textContent, 'REOPEN');
    await expired.listeners.get('#open-document:click')();
    assert.deepEqual(expired.calls, ['heartbeat', 'acquire']);
    assert.equal(expired.storage.get('ydental_clinical_editor_9'), 'new-token');

    for (const reply of [{status: 403, body: {error: 'access_denied: revoked'}},
        {status: 409, body: {error: 'editor_expired: not a 403'}}, new TypeError('offline')]) {
        const other = setup([reply]);
        await other.listeners.get('#open-document:click')();
        assert.deepEqual(other.calls, ['heartbeat']);
        assert.equal(other.storage.get('ydental_clinical_editor_9'), 'expired-token');
        assert.equal(other.nodes.get('#open-document').disabled, false);
    }

    let finishHeartbeat;
    const pendingHeartbeat = new Promise(resolve => { finishHeartbeat = resolve; });
    const concurrent = setup([pendingHeartbeat]);
    const firstOpen = concurrent.listeners.get('#open-document:click')();
    assert.equal(concurrent.nodes.get('#open-document').disabled, true);
    await concurrent.listeners.get('#open-document:click')();
    assert.deepEqual(concurrent.calls, ['heartbeat']);
    finishHeartbeat({status: 403, body: {error: 'editor_expired: ownership changed'}});
    await firstOpen;
    assert.deepEqual(concurrent.calls, ['heartbeat']);
    assert.equal(concurrent.nodes.get('#open-document').disabled, false);
    assert.equal(concurrent.storage.has('ydental_clinical_editor_9'), false);

    const dirty = setup([{status: 200, body: {result: 'accepted'}},
        {status: 403, body: {error: 'editor_expired: old editor'}}]);
    await dirty.listeners.get('#open-document:click')();
    dirty.textField.value = 'unsynchronized';
    dirty.listeners.get('textarea:input')();
    await dirty.interval();
    await dirty.listeners.get('#open-document:click')();
    assert.equal(dirty.textField.value, 'unsynchronized');
    assert.equal(dirty.storage.get('ydental_clinical_editor_9'), 'expired-token');
    assert.deepEqual(dirty.calls, ['heartbeat', 'heartbeat', 'heartbeat']);
    console.log('PASS clinical editor recovery: explicit expiration, retry, unknown failure, and unsaved content');
})().catch(error => { console.error(error); process.exitCode = 1; });

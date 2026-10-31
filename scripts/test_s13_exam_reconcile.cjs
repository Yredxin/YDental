'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

async function run({line = '42', operation = 'perform', reason = 'synthetic', responseChanges = false, expected = 'supported', expectedBytes = null} = {}) {
    let submit, verify, calls = 0, actionBytes = null, values = [['reason', reason], ['valid_from', '2026-10-31T09:00'],
        ['valid_until', '2026-10-31T10:00'], ['code', 'synthetic'], ['evidence', 'synthetic'], ['user_id', '1']];
    const reconcile = {hidden: true, href: ''};
    const check = {hidden: true, disabled: false, addEventListener(_event, handler) { verify = handler; }};
    const message = {textContent: ''};
    const form = {dataset: {operation, line, version: '0'},
        querySelectorAll() { return []; },
        addEventListener(_event, handler) { submit = handler; }};
    const root = {dataset: {write: '1', qualificationWrite: '1', execution: '9', category: 'exam', revision: '1'},
        querySelector(selector) { return selector === '#exam-message' ? message : selector === '#exam-check-submission' ? check : reconcile; },
        querySelectorAll(selector) { return selector === 'form[data-operation]' ? [form] : []; }};
    class SyntheticFormData { constructor() { this.values = values.slice(); } *[Symbol.iterator]() { yield* this.values; } }
    const context = {document: {querySelector: () => root},
        sessionStorage: {getItem: key => key === 'ydental_queue_connection' ? 'connection' : '{"lease_id":1,"token":"synthetic"}'},
        crypto: {getRandomValues: value => value}, URLSearchParams, FormData: SyntheticFormData, File: class {},
        odoo: {csrf_token: 'synthetic'}, window: {confirm: () => true, location: {reload() { throw Error('unexpected reload'); }}},
        fetch: async (url, options) => { calls++; if (url.endsWith('check-submission')) { return {ok: true, json: async () => ({status: 'committed'})}; }
            actionBytes = Buffer.byteLength(options.body.toString());
            if (!responseChanges) { throw new TypeError('offline'); }
            values = [['reason', 'changed']]; return {ok: true, json: async () => ({result: 'accepted'})}; }};
    vm.runInNewContext(fs.readFileSync('ydental_exam/static/src/workbench/workbench.js', 'utf8'), context);
    const event = {preventDefault() {}};
    await submit(event);
    await submit(event);
    if (expected === 'oversize') {
        assert.equal(calls, 0, 'oversized action is rejected before any request');
        assert.equal(check.hidden, true);
        assert.equal(reconcile.hidden, true);
        assert.match(message.textContent, /本次未发送/);
        return;
    }
    assert.equal(reconcile.hidden, false);
    assert.equal(calls, 1, 'unknown result must not replay the business request');
    if (expectedBytes !== null) { assert.equal(actionBytes, expectedBytes); }
    if (expected === 'unsupported') {
        assert.equal(check.hidden, true);
        assert.match(message.textContent, /人工核查/);
        await verify();
        assert.equal(calls, 1);
        return;
    }
    assert.equal(check.hidden, false);
    await verify();
    assert.equal(calls, 2, 'only the explicit check request is sent');
    assert.match(message.textContent, /本次操作已提交/);
}
(async () => {
    await run();
    await run({responseChanges: true});
    await run({line: '', expected: 'unsupported'});
    await run({operation: 'release_editor', expected: 'unsupported'});
    await run({operation: 'takeover', expected: 'unsupported'});
    await run({operation: 'revalidate', expected: 'unsupported'});
    await run({operation: 'grant_qualification', expected: 'unsupported'});
    await run({operation: 'review_capability', expected: 'unsupported'});
    await run({operation: 'bind_template', expected: 'unsupported'});
    const fields = {line_id: 42, execution_id: 9, lease_id: 1, lease_token: 'synthetic', inline: false,
        reason: '中+ &', materials: []};
    const action = reason => new URLSearchParams({operation: 'perform', revision: '1', connection: 'connection',
        payload: JSON.stringify({...fields, reason}), key: '00'.repeat(24), csrf_token: 'synthetic'}).toString();
    const prefix = '中+ &';
    const padding = 7500000 - Buffer.byteLength(action(prefix));
    await run({reason: prefix + 'a'.repeat(padding), expectedBytes: 7500000});
    await run({reason: prefix + 'a'.repeat(padding + 1), expected: 'oversize'});
    console.log('PASS exam explicit receipt checks, unsupported actions, escaped request-size boundary and no replay');
})().catch(error => { console.error(error); process.exitCode = 1; });

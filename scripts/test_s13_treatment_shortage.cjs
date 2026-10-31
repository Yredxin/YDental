// Exercise the workbench's actual submit handler without an Odoo server.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

async function run(reply) {
    let submit;
    const controls = [{disabled: false, closest: () => form}];
    const form = {
        dataset: {operation: 'finish', order: '1', orderVersion: '1'},
        closest: selector => selector === '[data-order]' ? {dataset: {order: '1', orderVersion: '1'}} : null,
        querySelectorAll: () => controls,
        addEventListener: (name, callback) => { if (name === 'submit') submit = callback; },
    };
    const message = {textContent: ''};
    const check = {hidden: true};
    const root = {
        dataset: {role: 'pharmacy', execution: '1', revision: '1', write: '1', heartbeat: '30'},
        querySelector: selector => ({'#treatment-result': message, '#treatment-reconcile': check,
            '#treatment-confirm': {textContent: '确认'}, '#treatment-offline': {textContent: '结果未知'}})[selector],
        querySelectorAll: selector => selector === 'form[data-operation]' ? [form] :
            selector === 'input,select,button' ? controls : [],
    };
    const holder = JSON.stringify({lease_id: 1, token: 'fixture'});
    const context = {document: {querySelector: () => root}, sessionStorage: {
        getItem: key => key === 'ydental_queue_connection' ? 'fixture' : holder, removeItem() {},
    }, crypto: {getRandomValues: bytes => bytes.fill(1)}, Uint8Array, URLSearchParams,
    FormData: class { constructor() { return [['reason', 'test']][Symbol.iterator](); } },
    window: {confirm: () => true, location: {reload: () => { throw new Error('unexpected reload'); }}},
    odoo: {csrf_token: 'fixture'}, setInterval() {}, fetch: async () => {
        if (reply instanceof Error) throw reply;
        return reply;
    }};
    vm.runInNewContext(fs.readFileSync('ydental_treatment/static/src/workbench/workbench.js', 'utf8'), context);
    await submit({preventDefault() {}});
    return {message: message.textContent, check: check.hidden, disabled: controls[0].disabled};
}

(async () => {
    const shortage = await run({status: 409, ok: false, json: async () => ({error: 'insufficient_balance: 可发库存不足。'})});
    assert.match(shortage.message, /可发库存不足/);
    assert.equal(shortage.check, true);
    assert.equal(shortage.disabled, false);
    const unknown = await run(new Error('network'));
    assert.equal(unknown.check, false);
    assert.equal(unknown.disabled, true);
    const conflict = await run({status: 409, ok: false, json: async () => ({error: 'version_conflict: changed'})});
    assert.equal(conflict.check, false);
    assert.equal(conflict.disabled, true);
    console.log('treatment shortage/unknown/conflict handling: PASS (VM)');
})().catch(error => { console.error(error); process.exitCode = 1; });

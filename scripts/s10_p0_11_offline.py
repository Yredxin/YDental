"""Offline request/gate negative checks; never opens a DB, browser or HTTP."""
import ast
from copy import deepcopy
import json
from pathlib import Path

import s10_p0_11_control as c
import s10_p0_11_browser as browser


def main():
    results = []
    for p in sorted(c.ROOT.glob('scripts/s10_p0_11_*.py')):
        ast.parse(p.read_text())
    base = c.baseline()
    current = dict(base, signatures=c.ro.read(c.OUT / 'read-only-sql.json')['all_table_signatures'])
    c.gate(current, 'startup', {})
    results.append('unchanged_all643_snapshot_accepted')
    def rejected(name, call):
        try:
            call()
        except (AssertionError, KeyError):
            results.append(name)
        else:
            raise AssertionError('gate failed to reject ' + name)
    def mutate(table, field, value):
        copy = deepcopy(current)
        row = json.loads(copy['tables'][table][0])
        row[field] = value
        copy['tables'][table][0] = json.dumps(row, ensure_ascii=False, sort_keys=True)
        return copy
    rejected('money_change_rejected', lambda: c.gate(mutate('account_move', 'amount_total', 741), 'startup', {}))
    rejected('unplanned_fence_rejected', lambda: c.gate(mutate('ydental_queue_mutex', 'ydental_revision', -1), 'startup', {}))
    rejected('old_version_change_rejected', lambda: c.gate(mutate('ydental_clinical_version', 'ydental_kind', 'confirm'), 'startup', {}))
    rejected('scope_write_before_login_rejected', lambda: c.gate(mutate('ydental_access_session', 'ydental_revision', 999), 'startup', {}))
    rejected('unplanned_audit_rejected', lambda: c.gate(mutate('ydental_access_audit', 'ydental_event', 'clinical.view'), 'startup', {}))
    doc = c.rows(base)['ydental_clinical_document'][0]
    connection, editor = 'A' * 64, 'B' * 43
    context = {'connection_sha256': c.sha(connection.encode()), 'editor_sha256': c.sha(editor.encode()),
               'csrf_sha256': c.sha(b'csrf-offline-only'), 'old_keys': ['old-key-offline-only']}
    def form(op):
        payload = {'document_id': 1}
        if op != 'acquire':
            payload['editor_token'] = editor
        if op == 'confirm':
            payload.update(expected_version=2, content=doc['ydental_content'], key='unique-offline-only-key')
        return {'operation': [op], 'payload': [json.dumps(payload)], 'revision': ['1'],
                'connection': [connection], 'csrf_token': ['csrf-offline-only']}
    for op in ('acquire', 'confirm', 'release'):
        assert browser.validate_action(form(op), context, doc)[0] == op
        results.append(op + '_native_request_shape_accepted_offline')
    rejected('heartbeat_rejected', lambda: browser.validate_action(form('heartbeat'), context, doc))
    rejected('wrong_revision_rejected', lambda: browser.validate_action(form('confirm') | {'revision': ['2']}, context, doc))
    rejected('wrong_csrf_rejected', lambda: browser.validate_action(form('confirm') | {'csrf_token': ['other']}, context, doc))
    rejected('wrong_connection_rejected', lambda: browser.validate_action(form('confirm') | {'connection': ['C' * 64]}, context, doc))
    f = form('confirm')
    payload = json.loads(f['payload'][0])
    payload['expected_version'] = 3
    rejected('wrong_doc_version_rejected', lambda: browser.validate_action(f | {'payload': [json.dumps(payload)]}, context, doc))
    payload['expected_version'] = 2
    payload['key'] = context['old_keys'][0]
    rejected('old_key_rejected', lambda: browser.validate_action(f | {'payload': [json.dumps(payload)]}, context, doc))
    payload['key'] = 'unique-offline-only-key'
    payload['content']['history'] += 'OFFLINE MUTATION'
    rejected('content_change_rejected', lambda: browser.validate_action(f | {'payload': [json.dumps(payload)]}, context, doc))
    result = {'status': 'PASS', 'checks': results, 'count': len(results),
              'scope': 'offline validation of request rejection and immutable source rows only',
              'SQL_connections': 0, 'CREATE': 0, 'HTTP': 0, 'Firefox': 0, 'real_or_simulated_business_POST': 0}
    c.save(c.OUT / 'offline-checks.json', result)
    print(json.dumps({'status': 'PASS', 'offline_checks': len(results)}))


if __name__ == '__main__':
    main()

"""Fault injection through the P0-03 controller and Web validators. No writes to Odoo."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
from unittest.mock import patch

import s10_p0_02_snapshot as r3
import s10_p0_03_control as c
from s10_p0_03_browser import guard_send, validate_action, validate_form, validate_response


def form(operation, ident):
    return {'action': '/ydental/settlement/action', 'method': 'post', 'visible': True,
            'valid': True, 'output': 'html', 'csrf': True, 'key': True,
            'revision_match': True, 'reason': True, 'record': str(ident),
            'operation': operation, 'button_enabled': True}


def response(operation, ident, accepted=True):
    field = 'refund_id' if operation == 'refund_reject' else 'close_id'
    return {'method': 'POST', 'path': '/ydental/settlement/action',
            'content_type': 'application/x-www-form-urlencoded',
            'post': {'operation': [operation], 'output': ['html'], field: [str(ident)],
                     'csrf_token': ['OWN'], 'revision': ['CURRENT'], 'key': ['UNIQUE']},
            'status': 303, 'location_path': '/ydental/settlement', 'notice': True,
            'feedback': ('操作已受理，请核对下方业务记录。' if accepted else
                         '请求未完成，请核对权限、门店或输入后重试。')}


def fact_pair():
    return {'refund': {'id': 14, 'ydental_state': 'requested', 'ydental_requester_id': 5,
                       'ydental_approver_id': None, 'ydental_decision_reason': None,
                       'ydental_native_payment_id': None, 'ydental_credit_note_id': None},
            'close': {'id': 9, 'ydental_state': 'confirmed', 'ydental_gross': '0.00',
                      'ydental_refunded': '0.00', 'ydental_pending': '0.00',
                      'ydental_cycle': 1, 'ydental_unlocked_by_id': None,
                      'ydental_unlock_reason': None}, 'audit': []}


def mutate_sig(state, table):
    state['all']['signatures'][table]['sha256'] = 'SIMULATED_CHANGE'
    if table in state['managed']['tables']:
        state['managed']['tables'][table]['sha256'] = 'SIMULATED_CHANGE'


class FakeOps:
    def __init__(self, source, fault=None):
        self.source = source
        self.fault = fault
        self.stages = []
        self.posts = []
        self.stopped = False
        self.ledger = set()

    def source_readonly(self):
        self.stages.append('source_readonly')
        value = deepcopy(self.source)
        if self.fault == 'source_oid':
            value['managed']['oid'] = 1
        return value

    def check_source(self, before):
        self.stages.append('check_source')
        c.source_gate(r3.snapshot(r3.SOURCE, business=True), before['managed'], before['all'])

    def clone_compare(self, before):
        self.stages.append('clone_compare')
        self.cloned = deepcopy(before)
        self.cloned['managed']['database'] = c.s.TARGET
        self.cloned['managed']['oid'] = 9999999
        if self.fault == 'clone_business':
            mutate_sig(self.cloned, 'account_payment')
        c.clone_equal(before, self.cloned)
        return self.cloned

    def start_http(self):
        self.stages.append('start_http')

    def browser_flow(self, clone):
        self.stages.append('browser_flow')
        current = deepcopy(clone)
        # Same web_diff used in live mode. Simulate a real cache-generated asset
        # and its Odoo _mark_for_gc checklist companion.
        content = b'\n/* simulated local web asset */\n'
        digest = hashlib.sha1(content).hexdigest()
        fname = digest[:2] + '/' + digest
        root = c.s.TARGET_RUN / 'data/filestore' / c.s.TARGET
        path = root / fname
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        marker = root / ('checklist/' + fname)
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_bytes(b'')
        files = current['managed']['filestore']['files']
        files[fname] = c.s.sha(content)
        files['checklist/' + fname] = c.s.sha(b'')
        current['managed']['filestore']['count'] += 2
        current['managed']['filestore']['sha256'] = c.s.sha(b''.join(
            (key + ' ' + files[key] + '\n').encode() for key in sorted(files)))
        aid = max(current['all']['rows']['ir_attachment']) + 1
        asset = deepcopy(current['all']['rows']['ir_attachment'][1075])
        asset.update({'id': aid, 'name': 'web.assets_frontend.min.css',
                      'url': '/web/assets/123abcd/web.assets_frontend.min.css',
                      'mimetype': 'text/css', 'type': 'binary', 'public': True,
                      'res_model': 'ir.ui.view', 'res_id': 0, 'create_uid': 1, 'write_uid': 1,
                      'checksum': digest, 'store_fname': fname, 'file_size': len(content),
                      'index_content': content.decode().strip()})
        current['all']['rows']['ir_attachment'][aid] = asset
        current['managed']['attachment_pointers'] += 1
        mutate_sig(current, 'ir_attachment')
        if self.fault == 'asset_owner': asset['res_model'] = 'account.move'
        if self.fault == 'asset_cross_model': asset['res_id'] = 14
        if self.fault == 'asset_sensitive': asset['name'] = 'patient_chart.pdf'
        if self.fault == 'asset_extra_file':
            files['checklist/ff/unknown'] = c.s.sha(b'')
            current['managed']['filestore']['count'] += 1
            current['managed']['filestore']['sha256'] = c.s.sha(b''.join(
                (key + ' ' + files[key] + '\n').encode() for key in sorted(files)))
        if self.fault == 'asset_missing_checklist':
            del files['checklist/' + fname]
            current['managed']['filestore']['count'] -= 1
            current['managed']['filestore']['sha256'] = c.s.sha(b''.join(
                (key + ' ' + files[key] + '\n').encode() for key in sorted(files)))
        if self.fault == 'asset_wrong_hash': asset['checksum'] = '0' * 40
        if self.fault == 'mail_bad':
            row = deepcopy(current['all']['rows']['mail_message'][1832])
            row.update({'id': max(current['all']['rows']['mail_message']) + 1,
                        'model': 'account.move', 'res_id': 14, 'create_uid': 10})
            current['all']['rows']['mail_message'][row['id']] = row
            mutate_sig(current, 'mail_message')
        if self.fault == 'user_extra_field':
            current['all']['rows']['res_users'][10]['login'] = 'changed'
            mutate_sig(current, 'res_users')
        if self.fault == 'audit_bad':
            row = deepcopy(current['all']['rows']['ydental_access_audit'][2657])
            row.update({'id': max(current['all']['rows']['ydental_access_audit']) + 1,
                        'ydental_event': 'account.create'})
            current['all']['rows']['ydental_access_audit'][row['id']] = row
            mutate_sig(current, 'ydental_access_audit')
        if self.fault == 'economy': mutate_sig(current, 'account_payment')
        if self.fault == 'module': current['managed']['modules']['account']['latest_version'] = '999'
        if self.fault == 'view': current['managed']['views']['ydental_settlement.ydental_settlement_tokens']['languages']['en_US']['has_output_html'] = False
        c.web_diff(clone, current)
        facts = fact_pair()
        for index, (operation, ident) in enumerate((('refund_reject', 14), ('unlock', 9))):
            if self.fault == 'wrong_page' and index == 0: raise AssertionError('page two link')
            if self.fault == 'missing_record' and index == 0: raise AssertionError('old record absent')
            if self.fault == 'bad_role' and index == 0: raise AssertionError('approval role')
            fields = form(operation, ident)
            field_faults = {'output': 'output', 'html5': 'valid', 'csrf': 'csrf',
                            'key': 'key', 'revision': 'revision_match'}
            if self.fault in field_faults and index == 0:
                fields[field_faults[self.fault]] = False
            validate_form(fields, operation, ident)
            guard_send(self.ledger, 6, operation, ident)
            self.posts.append(operation)
            observed = response(operation, ident)
            if self.fault in ('http200', 'http403', 'http409') and index == 0:
                observed['status'] = int(self.fault[-3:])
            if self.fault == 'lost_response' and index == 0:
                raise TimeoutError('simulated committed request without response')
            validate_response(observed, operation, ident, accepted=True)
            before = deepcopy(facts)
            if operation == 'refund_reject':
                facts['refund'].update(ydental_state='rejected', ydental_approver_id=6,
                                       ydental_decision_reason='synthetic')
                facts['audit'].append((1, 'settlement.refund.reject', 'accepted', 6, 1))
                current['all']['rows']['ydental_settlement_refund'][14].update(
                    ydental_state='rejected', ydental_approver_id=6,
                    ydental_decision_reason='synthetic')
                mutate_sig(current, 'ydental_settlement_refund')
            else:
                facts['close'].update(ydental_state='unlocked', ydental_unlocked_by_id=6,
                                      ydental_unlock_reason='synthetic')
                facts['audit'].append((2, 'settlement.unlock', 'accepted', 6, 1))
                current['all']['rows']['ydental_settlement_close'][9].update(
                    ydental_state='unlocked', ydental_unlocked_by_id=6,
                    ydental_unlock_reason='synthetic')
                mutate_sig(current, 'ydental_settlement_close')
            if self.fault == 'partial_money' and index == 0:
                mutate_sig(current, 'account_payment')
            validate_action(before, facts, operation)
            c.web_diff(clone, current, refund=True, close=(operation == 'unlock'))
        for operation, ident in (('unlock', 9), ('refund_reject', 14)):
            guard_send(self.ledger, 14 if operation == 'unlock' else 10, operation, ident)
            self.posts.append('negative_' + operation)
            denial = response(operation, ident, accepted=False)
            if self.fault == 'negative_accepted': denial['feedback'] = '操作已受理，请核对下方业务记录。'
            validate_response(denial, operation, ident, accepted=False)
            c.web_diff(clone, current, refund=True, close=True)
        if self.fault == 'duplicate_post': guard_send(self.ledger, 6, 'refund_reject', 14)
        self.current = current

    def stop_http(self):
        self.stages.append('stop_http'); self.stopped = True

    def readonly_final(self, before, clone):
        self.stages.append('readonly_final')
        c.web_diff(clone, self.current, refund=True, close=True)
        return self.current


def main():
    source = c.capture(c.s.SOURCE, business=True)
    source['managed']['business']['grants'] = [list(x) for x in source['managed']['business']['grants']]
    cases = ['PASS', 'source_oid', 'clone_business', 'asset_owner', 'asset_cross_model',
             'asset_sensitive', 'asset_extra_file', 'asset_missing_checklist', 'asset_wrong_hash',
             'mail_bad', 'user_extra_field', 'audit_bad', 'economy', 'module', 'view',
             'wrong_page', 'missing_record', 'bad_role', 'output', 'html5', 'csrf', 'key',
             'revision', 'http200', 'http403', 'http409', 'lost_response',
             'partial_money', 'negative_accepted', 'duplicate_post']
    results = {}
    with tempfile.TemporaryDirectory(prefix='s10-p003-fake-') as temp:
        conf = Path(temp) / 'preflight.json'
        conf.write_text(json.dumps({'source_all_signatures': source['all']['signatures']}))
        run = Path(temp) / 'target'
        with patch.object(c, 'PREFLIGHT', conf), patch.object(c.s, 'TARGET_RUN', run):
            for case in cases:
                fake = FakeOps(source, None if case == 'PASS' else case)
                try:
                    c.execute_pipeline(fake)
                    assert case == 'PASS', ('unexpected_pass', case)
                    results[case] = 'SIMULATED_PASS'
                except (AssertionError, TimeoutError, KeyError, ValueError) as error:
                    assert case != 'PASS', error
                    assert fake.stopped or 'start_http' not in fake.stages
                    if case in ('http200', 'http403', 'http409', 'lost_response', 'partial_money'):
                        assert len(fake.posts) == 1
                    results[case] = 'FAIL_CLOSED'
    assert results['PASS'] == 'SIMULATED_PASS'
    assert all(v == 'FAIL_CLOSED' for k, v in results.items() if k != 'PASS')
    print(json.dumps({'status': 'SIMULATED_PASS', 'cases': results, 'count': len(results)}, ensure_ascii=False))


if __name__ == '__main__':
    main()

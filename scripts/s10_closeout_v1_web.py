"""One owned HTTP/Firefox window, quiescent native upgrade, bounded shutdown."""
from datetime import datetime
import json
import os
import socket
import subprocess
import time
import s10_closeout_v1_contract as c
from s10_closeout_v1_control import native_env, run_native


def action_projections(snapshot):
    parent = snapshot['tables']['ir_actions']
    children = ('ir_act_window', 'ir_act_report_xml', 'ir_act_url', 'ir_act_server', 'ir_act_client')
    for projected in parent:
        physical = projected['__physical_table__']
        assert physical in ('ir_actions',) + children
        if physical == 'ir_actions':
            continue
        candidates = [row for row in snapshot['tables'][physical]
                      if row['id'] == projected['id'] and row['__physical_table__'] == physical]
        assert len(candidates) == 1
        child = candidates[0]
        assert all(child[name] == value for name, value in projected.items()), 'ACTION_PARENT_CHILD_INCONSISTENCY'
    keys = [(row['__physical_table__'], row['id']) for row in parent]
    assert len(keys) == len(set(keys)), 'DUPLICATE_ACTION_PHYSICAL_KEY'


def upgrade_gate(before, after, changes):
    assert before['schema'] == after['schema'], 'UNEXPECTED_SCHEMA_MIGRATION'
    action_projections(before); action_projections(after)
    module_ids = {row['id'] for row in before['tables']['ir_module_module'] if row['name'] in {'ydental_settlement', 'ydental_settlement_test'}}
    view_ids = {row['res_id'] for row in before['tables']['ir_model_data'] if row['module'] == 'ydental_settlement' and row['model'] == 'ir.ui.view'}
    technical = {'write_uid', 'write_date'}
    metadata = {'ir_model', 'ir_model_fields', 'ir_model_fields_selection', 'ir_model_constraint', 'ir_model_relation',
                'ir_model_data', 'ir_ui_view', 'ir_actions', 'ir_act_report_xml', 'ir_act_url',
                'ir_ui_menu', 'ir_module_module_dependency'}
    own = [row for row in before['tables']['ir_model_data'] if row['module'] == 'ydental_settlement']
    own_ids = {'ir_act_url': {row['res_id'] for row in own if row['model'] == 'ir.actions.act_url'},
               'ir_act_report_xml': {row['res_id'] for row in own if row['model'] == 'ir.actions.report'},
               'ir_ui_menu': {row['res_id'] for row in own if row['model'] == 'ir.ui.menu'}}
    explanations = []
    signal_counts = {}
    for row in changes:
        table = row['table']
        if table.startswith('orm_signaling_'):
            assert row['before_count'] == 0 and row['after_count'] == 1
            assert set(row['after'][0]) == {'id', 'date', '__physical_table__', '__physical_oid__'}
            signal_counts[table] = signal_counts.get(table, 0) + 1
            assert signal_counts[table] <= 4
            reason = 'fixed registry.py1086-1150 append-only module/cache signaling'
        elif table == 'ir_module_module':
            assert row['physical_key'][2] in module_ids and set(row['columns']) <= technical
            reason = 'same installed module; native loading technical timestamp only'
        elif table in metadata:
            assert row['before_count'] == row['after_count'] == 1
            physical = row['physical_key'][1]
            if table in own_ids or table == 'ir_actions':
                assert physical in own_ids and row['physical_key'][2] in own_ids[physical], 'NON_S10_ACTION_OR_MENU_WRITE'
            allowed = technical.copy()
            if table == 'ir_ui_view' and row['physical_key'][2] in view_ids:
                allowed.add('arch_prev')
                if 'arch_prev' in row['columns']:
                    value = row['after'][0]['arch_prev']; architecture = row['before'][0]['arch_db']
                    assert value == (architecture.get('en_US') if isinstance(architecture, dict) else architecture)
            assert set(row['columns']) <= allowed, ('SEMANTIC_METADATA_DRIFT', table, row['columns'])
            reason = 'native reflection/XML update: exact existing physical record, all semantic fields equal; ir_ui_view.py:667 previous-arch if applicable'
        else:
            raise AssertionError(('UPGRADE_PROTECTED_ROW_DRIFT', table, row['physical_key'], row['columns']))
        explanations.append({'table': table, 'physical_key': row['physical_key'], 'columns': row['columns'], 'purpose': reason})
    c.save(c.OUT / 'E-metadata-field-explanations.json', explanations)
    return {'all_business_clinical_permissions_old_attachments_originals_exact': True,
            'every_changed_metadata_row_and_column_explained': True, 'changed_rows': len(changes)}


def window(mode):
    c.gate(business=True)
    service = browser = None
    status = {'mode': mode, 'status': 'BLOCKED'}
    previous = [json.loads(v) for v in (c.OUT / 'events.jsonl').read_text().splitlines()]
    assert sum(v['event'] == 'Odoo_process_intent' for v in previous) < 6
    c.event('Odoo_process_intent', action='HTTP-' + mode)
    try:
        with (c.RUN / ('http-' + mode + '.log')).open('xb') as stream:
            service = subprocess.Popen([str(c.PYTHON), str(c.CORE_ROOT / 'odoo-bin'), '-c', str(c.RUN / 'odoo.conf')],
                cwd=c.ROOT, env=native_env('http-' + mode), stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT)
        start = time.monotonic()
        while True:
            assert service.poll() is None
            try:
                with socket.create_connection(('127.0.0.1', c.PORT), timeout=1): break
            except OSError:
                assert time.monotonic() - start < 60
                time.sleep(.2)
        with (c.RUN / ('browser-' + mode + '.log')).open('xb') as stream:
            browser = subprocess.Popen([str(c.PYTHON), str(c.ROOT / 'scripts/s10_closeout_v1_browser.py'), mode],
                cwd=c.ROOT, env=native_env('browser-' + mode), stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT)
        begin = time.monotonic(); completed = set()
        while browser.poll() is None:
            assert service.poll() is None and time.monotonic() - begin < 1200
            assert not (c.PRIVATE / 'STOP.json').exists()
            for action in ['revoke', 'restore']:
                marker = c.PRIVATE / ('browser-wait-' + action + '.json')
                if mode == 'pre' and action not in completed and marker.exists():
                    assert run_native(action) == 0
                    c.save(c.PRIVATE / ('continue-' + action + '.json'), {'committed_and_read_back': True})
                    completed.add(action)
            time.sleep(.2)
        status.update(browser_runner_exit_code=browser.returncode)
        assert browser.returncode == 0
        if mode == 'pre': assert completed == {'revoke', 'restore'}
        status['status'] = 'BROWSER_COMPLETE'
    except BaseException:
        c.stop('WEB_WINDOW_FAILED:' + mode)
        raise
    finally:
        c.event('Web_stop_new_dispatches', mode=mode)
        if browser and browser.poll() is None: browser.terminate(); browser.wait(timeout=20)
        if service and service.poll() is None: service.terminate(); service.wait(timeout=20)
        status.update(HTTP_pid=service.pid if service else None, HTTP_exit_code=service.returncode if service else None,
                      browser_runner_pid=browser.pid if browser else None,
                      owned_HTTP_stopped=bool(service and service.poll() is not None))
        c.save(c.OUT / ('Web-process-result-' + mode + '.json'), status)
        assert not service or service.returncode not in {-11, 139}, 'NATIVE_CRASH_STOP'


def main():
    window('pre')
    assert c.read(c.OUT / 'Web-process-result-pre.json')['owned_HTTP_stopped']
    before = c.readonly('E-before-upgrade', full=True)
    c.save(c.PRIVATE / 'E-before-filestore.json', c.filetree(c.RUN / 'data/filestore' / c.NAME))
    assert run_native('upgrade') == 0
    after = c.readonly('E-after-upgrade', full=True)
    c.persist('E-S10-only-upgrade', before, after, upgrade_gate)
    assert c.read(c.PRIVATE / 'E-before-filestore.json') == c.filetree(c.RUN / 'data/filestore' / c.NAME)
    window('post')
    c.save(c.OUT / 'Web-and-upgrade-result.json', {'pre_and_post_HTTP_stopped': True,
           'upgrade_only_after_pre_HTTP_stopped': True, 'S10_only_upgrade_count': 1,
           'all_business_and_originals_preserved': True})


if __name__ == '__main__':
    os.umask(0o077)
    main()

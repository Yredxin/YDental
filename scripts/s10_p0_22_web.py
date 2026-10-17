"""One owned HTTP/Firefox window, quiescent native upgrade, bounded shutdown."""
from datetime import datetime
import json
import os
import socket
import subprocess
import time
import s10_p0_22_contract as c
from s10_p0_22_control import native_env, run_native


def upgrade_gate(before, after, changes):
    assert before['schema'] == after['schema'], 'UNEXPECTED_SCHEMA_MIGRATION'
    module_ids = {row['id'] for row in before['tables']['ir_module_module'] if row['name'] in {'ydental_settlement', 'ydental_settlement_test'}}
    view_ids = {row['res_id'] for row in before['tables']['ir_model_data'] if row['module'] == 'ydental_settlement' and row['model'] == 'ir.ui.view'}
    technical = {'write_uid', 'write_date'}
    metadata = {'ir_model', 'ir_model_fields', 'ir_model_fields_selection', 'ir_model_constraint', 'ir_model_relation',
                'ir_model_data', 'ir_ui_view', 'ir_actions', 'ir_act_report_xml', 'ir_module_module_dependency'}
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


def main():
    c.gate(business=True)
    c.save(c.PRIVATE / 'Web-owned-process-intent.json', {'HTTP': 1, 'Firefox': 1, 'contexts': 3,
           'source_database_HTTP': 0, 'original_generation': 0, 'original_GET_cap': 4, 'HTTP_cap': 600})
    service = browser = None
    status = {'status': 'BLOCKED'}
    try:
        with (c.RUN / 'http.log').open('xb') as stream:
            service = subprocess.Popen([str(c.PYTHON), str(c.CORE_ROOT / 'odoo-bin'), '-c', str(c.RUN / 'odoo.conf')],
                cwd=c.ROOT, env=native_env('http'), stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT)
        start = time.monotonic()
        while True:
            assert service.poll() is None
            try:
                with socket.create_connection(('127.0.0.1', c.PORT), timeout=1): break
            except OSError:
                assert time.monotonic() - start < 60; time.sleep(.2)
        with (c.RUN / 'browser.log').open('xb') as stream:
            browser = subprocess.Popen([str(c.PYTHON), str(c.ROOT / 'scripts/s10_p0_22_browser.py')],
                cwd=c.ROOT, env=native_env('browser'), stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT)
        begin = time.monotonic(); revoked = upgraded = False
        while browser.poll() is None:
            assert service.poll() is None and time.monotonic() - begin < 1200
            if (c.PRIVATE / 'STOP.json').exists(): raise AssertionError('STOP_MARKER')
            if not revoked and (c.PRIVATE / 'browser-wait-revoke.json').exists():
                assert run_native('revoke') == 0
                c.save(c.PRIVATE / 'continue-revoke.json', {'committed_and_read_back': True})
                revoked = True
            if not upgraded and (c.PRIVATE / 'browser-wait-upgrade.json').exists():
                before = c.readonly('E-before-upgrade')
                assert run_native('upgrade') == 0
                after = c.readonly('E-after-upgrade')
                c.persist('E-S10-only-upgrade', before, after, upgrade_gate)
                c.save(c.PRIVATE / 'continue-upgrade.json', {'full_upgrade_gate_passed': True})
                upgraded = True
            time.sleep(.2)
        status.update(browser_runner_exit_code=browser.returncode, upgrade_performed=upgraded)
        assert browser.returncode == 0 and upgraded and revoked
        status['status'] = 'COMPLETE_PENDING_FINAL_INDEPENDENT_TAIL_VISUAL_REVIEW'
    except BaseException:
        c.stop('WEB_OR_UPGRADE_WINDOW_FAILED')
        raise
    finally:
        c.event('Web_stop_new_dispatches')
        if browser and browser.poll() is None: browser.terminate(); browser.wait(timeout=20)
        if service and service.poll() is None: service.terminate(); service.wait(timeout=20)
        status.update(HTTP_pid=service.pid if service else None,
                      HTTP_exit_code=service.returncode if service else None,
                      browser_runner_pid=browser.pid if browser else None)
        c.save(c.OUT / 'Web-process-result.json', status)
    print(json.dumps(status))


if __name__ == '__main__':
    os.umask(0o077)
    main()

"""Pure-file preflight counterexamples and final sealing; no database imports."""
import copy
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch
import s10_p0_24_contract as c


def optional(path):
    return c.parse(path.read_bytes()) if path.exists() else None


def preflight():
    baseline = (c.ROOT / 'docs/evidence/s10-p0-23/diagnostic-fixed/arch_prev-tail.txt').read_bytes()
    assert c.sha(baseline) == c.BASELINE_SHA
    for path in sorted((c.ROOT / 'scripts').glob('s10_p0_24_*.py')):
        compile(path.read_bytes(), str(path), 'exec')
    def envelope(value):
        raw = value.encode()
        return {'id': 929, 'key': c.KEY, 'table_oid': 2122563, 'physical_table': 'ir_ui_view',
                'arch_prev_type': 'text', 'arch_prev_is_null': False, 'arch_prev_text': value,
                'arch_prev_characters': len(value), 'arch_prev_UTF8_bytes': len(raw),
                'arch_prev_UTF8_hex': raw.hex(), 'arch_prev_server_sha256': c.sha(raw),
                'arch_db_server_sha256': 'STATIC_SYNTHETIC_NOT_A_SERVER_DIGEST'}
    tests = []
    def run(label, raw, expected):
        base = c.PRIVATE / ('STATIC-' + label); base.mkdir(mode=0o700)
        c.write(base / 'target-return.utf8', raw)
        result = c.analyze('STATIC-' + label)
        assert (base / 'analysis.json').exists(), 'EVIDENCE_BEFORE_DECISION'
        assert result is expected
        tests.append({'case': label, 'expected': expected, 'actual': result, 'evidence_saved': True})
    row = envelope(baseline.decode())
    run('normal', c.encode(row), True)
    bad = copy.deepcopy(row); bad['arch_prev_text'] = bad['arch_prev_text'][:1992] + '6' + bad['arch_prev_text'][1993:]
    run('v-to-6-with-unchanged-synthetic-server-digest', c.encode(bad), False)
    run('literal-control-1F', b'{"opaque":"' + bytes([31]) + b'"}', False)
    escaped = envelope('STATIC ' + chr(31))
    assert bytes([31]) not in c.encode(escaped)
    run('normal-escaped-control', c.encode(escaped), True)
    run('duplicate-key', b'{"id":929,"id":930}', False)
    run('truncated', c.encode(row)[:-5], False)
    base = c.PRIVATE / 'STATIC-readback-mismatch'; base.mkdir(mode=0o700)
    c.write(base / 'target-return.utf8', c.encode(row))
    original = Path.read_bytes
    def injected(path):
        data = original(path)
        if path == base / 'serialized.json':
            pos = data.index(b'Invoice Notifications')
            return data[:pos] + b'X' + data[pos+1:]
        return data
    with patch.object(Path, 'read_bytes', injected):
        result = c.analyze('STATIC-readback-mismatch')
    saved = c.parse((base / 'analysis.json').read_bytes())
    assert result is False and not saved['comparisons']['serialized_write_readback_bytes']
    assert (base / 'serialized-reopened.bin').exists()
    tests.append({'case': 'injected-readback-mismatch', 'actual': False, 'evidence_saved': True,
                  'synthetic_read_fault_not_real_database_or_disk_corruption': True})
    for name, action in [('nonfinite-parse', lambda: c.parse(b'{"value":NaN}')),
                         ('nonfinite-serialize', lambda: c.encode({'value': float('nan')}))]:
        try: action()
        except ValueError: tests.append({'case': name, 'rejected': True})
        else: raise AssertionError(name)
    result = {'exit_code': 0, 'pure_file_tests': tests, 'count': len(tests),
              'STATIC_server_fields_synthesized_not_measured': True,
              'DB_connections_Odoo_business_HTTP': 0, 'old_modules_imported': False,
              'all_three_scripts_compile': True}
    c.save(c.OUT / 'pure-file-preflight.json', result)
    c.save(c.OUT / 'SQL-contract.json', {'normal_explicit_statements_per_client': c.STATEMENTS,
        'maximum_connections': 2, 'maximum_explicit_statements_per_client': 6,
        'startup_options': c.OPTIONS, 'host': '127.0.0.1', 'port': 5432, 'database': c.DATABASE,
        'OID': c.OID, 'cluster': c.CLUSTER, 'target': {'id': 929, 'key': c.KEY, 'table_oid_expected': 2122563},
        'target_envelope_max_bytes': c.MAX_RETURN, 'field_UTF8_max_bytes': 8192,
        'connect_timeout_s': 5, 'statement_timeout_ms': 5000, 'total_client_timeout_s': 30,
        'no_commit_retry_reconnect_fallback': True})
    print(json.dumps({'exit_code': 0, 'pure_file_counterexamples': len(tests), 'connections': 0}))


def seal():
    c.gate()
    collection = optional(c.PRIVATE / 'collection-result.json')
    analyses = {label: optional(c.PRIVATE / label / 'analysis.json') for label in ['psql', 'python']}
    processes = {label: optional(c.PRIVATE / label / 'process-result.json') for label in ['psql', 'python']}
    rows = {label: optional(c.PRIVATE / label / 'parsed-server-envelope.json') for label in ['psql', 'python']}
    cross = {}
    if all(rows.values()):
        stable = ['id', 'key', 'table_oid', 'physical_table', 'arch_prev_type', 'arch_prev_is_null',
                  'arch_prev_text', 'arch_prev_characters', 'arch_prev_UTF8_bytes', 'arch_prev_UTF8_hex',
                  'arch_prev_server_sha256', 'arch_db_type', 'arch_db_is_null', 'arch_db_server_sha256',
                  'write_uid', 'write_date', 'server_encoding', 'client_encoding']
        cross = {key: rows['psql'].get(key) == rows['python'].get(key) for key in stable}
    completed = bool(collection and collection['psql_completed'] and collection['python_exit'] == 0
                     and all(analyses.values()) and all(a.get('completed') for a in analyses.values()))
    differences = any(a and a.get('completed') and not a.get('all_layer_comparisons_match') for a in analyses.values())
    differences = differences or bool(cross and not all(cross.values()))
    differences = differences or any(p and p.get('stdout_pipe_disk_equal') is False for p in processes.values())
    classification = '采集层间不一致' if differences else ('当前有限观测一致' if completed and cross and all(cross.values()) else '无法完成')
    baseline = (c.ROOT / 'docs/evidence/s10-p0-23/diagnostic-fixed/arch_prev-tail.txt').read_bytes().decode()
    known_bad = baseline[:1992] + '6' + baseline[1993:]
    public_records = {}
    for label, row in rows.items():
        public = c.OUT / label; public.mkdir(mode=0o700)
        process = processes[label]
        if process:
            safe_process = {k: v for k, v in process.items() if k != 'error'}
            safe_process['error_present'] = bool(process.get('error'))
            safe_process['error_detail_private'] = True
            c.save(public / 'process-result.json', safe_process)
        if analyses[label]: c.save(public / 'layer-analysis.json', analyses[label])
        approved = bool(row and row.get('arch_prev_text') in [baseline, known_bad])
        public_records[label] = {'raw_return_present': (c.PRIVATE / label / 'target-return.utf8').exists(),
                                 'full_text_disclosure_approved_against_GPT_reviewed_template': approved}
        if row and approved:
            c.save(public / 'server-generated-envelope.json', row)
            c.write(public / 'client-received-target.utf8', (c.PRIVATE / label / 'target-return.utf8').read_bytes())
            c.write(public / 'arch_prev.utf8', row['arch_prev_text'].encode())
            c.write(public / 'serialized.json', (c.PRIVATE / label / 'serialized.json').read_bytes())
            c.write(public / 'serialized-reopened.bin', (c.PRIVATE / label / 'serialized-reopened.bin').read_bytes())
        elif row:
            c.save(public / 'restricted-field.json', {k: v for k, v in row.items() if k not in ['arch_prev_text', 'arch_prev_UTF8_hex']})
        for name in ['stdout.raw', 'stderr.raw']:
            path = c.PRIVATE / label / name
            if path.exists():
                public_records[label][name] = {'bytes': path.stat().st_size, 'sha256': c.sha(path.read_bytes()), 'raw_private_only': True}
    result = {'classification': classification, 'collection': collection, 'cross_client_stable_fields': cross,
              'client_analyses': analyses, 'public_disclosure': public_records,
              'current_observations_only': True, 'same_object_copies_not_independent_measurements': True,
              'clients_may_share_libpq_and_host': True,
              'raw_capture_boundary': 'psql stdout / psycopg2-decoded text; not network capture or pre-driver protocol bytes',
              'historical_root_cause_fixed': False, 'database_overall_integrity_proven': False,
              'five_groups': 'unchanged: A BLOCKED; B/C/D/E NOT_RUN', 'S10_stage_exit': 'BLOCKED',
              'business_operations': 0, 'other_databases': 0}
    c.save(c.OUT / 'diagnostic-result.json', result)
    manifest = []
    for path in sorted(c.PRIVATE.rglob('*')):
        if path.is_file() and path.name not in ['pgpass', 'credential-reference.json']:
            manifest.append({'path': str(path.relative_to(c.ROOT)), 'bytes': path.stat().st_size, 'sha256': c.sha(path.read_bytes())})
    c.save(c.OUT / 'private-evidence-manifest.json', {'files': manifest,
        'exclude': 'credential material and later delivery REST proof; private root 0700', 'old_inputs_not_regenerated': True})
    print(json.dumps({'classification': classification, 'business_operations': 0}, ensure_ascii=False))


if __name__ == '__main__':
    os.umask(0o077)
    if sys.argv[1] == 'preflight': preflight()
    elif sys.argv[1] == 'seal': seal()
    else: raise SystemExit('unknown pure-file mode')

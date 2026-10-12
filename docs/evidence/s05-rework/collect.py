"""Collect allowlisted, synthetic S05 evidence. Never publish raw runtime logs."""
from pathlib import Path
import hashlib
import json
import re


ROOT = Path(__file__).resolve().parents[3]
TARGET = Path(__file__).resolve().parent / 'isolation-attempts'
TARGET.mkdir(exist_ok=True)
for run in sorted((ROOT / '.local').glob('ydental_s05_test_*')):
    if not re.fullmatch(r'ydental_s05_test_[0-9]{14}_[a-f0-9]{8}', run.name) or run.is_symlink() or run.name < 'ydental_s05_test_20261012013438':
        continue
    marker = run / 'database.json'
    if not marker.is_file() or marker.is_symlink():
        continue
    data = json.loads(marker.read_text())
    assert data['database'] == run.name and data['endpoint'] == {'host': '127.0.0.1', 'port': '5432', 'user': 'odoo'}
    assert data['cluster'] == '7694897083368259627'
    assert hashlib.sha256((run / 'odoo.conf').read_bytes()).hexdigest() == data['config_sha256']
    entries = []
    actions = run / 'actions.jsonl'
    if actions.exists():
        for line in actions.read_text().splitlines():
            action = json.loads(line)
            log = run / action['log']
            assert log.parent == run and log.is_file() and not log.is_symlink()
            assert hashlib.sha256(log.read_bytes()).hexdigest() == action['log_sha256']
            entries.append({k: action[k] for k in ('action', 'exit_code', 'log_sha256', 'time_utc', 'tested_commit', 'tests', 'verification_exit') if k in action})
    evidence = {'database': data['database'], 'oid': data['oid'], 'created_utc': data['created_utc'],
        'endpoint': data['endpoint'], 'cluster': data['cluster'], 'core': data['core'], 'port': data['port'],
        'config_sha256': data['config_sha256'], 'actions': entries,
        'boundary': {'new_database_only': True, 'exact_dbfilter': '^' + run.name + '$', 'private_config_data_logs': True,
            'cron_threads': 0, 'smtp': 'disabled loopback sink', 'process_egress': 'only approved loopback database and this HTTP port',
            'existing_services_modified': False, 'system_dependencies_installed': False}}
    (TARGET / (run.name + '.json')).write_text(json.dumps(evidence, indent=2) + '\n')

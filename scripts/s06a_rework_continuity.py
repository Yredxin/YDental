"""Verify original business tests and real races are retained in S06-A rework."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = '840df8921cfb5a70c601e6e8ed81fb7d03aacd5b'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--db', required=True)
args = parser.parse_args()
assert re.fullmatch(r'ydental_s06a_test_[0-9]{14}_[a-f0-9]{8}', args.db)
run = ROOT / '.local' / args.db
metadata = json.loads((run / 'database.json').read_text())
assert metadata['database'] == args.db and not run.is_symlink()
assert hashlib.sha256((run / 'odoo.conf').read_bytes()).hexdigest() == metadata['config_sha256']
head = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
original = json.loads(subprocess.check_output(['git', '-C', str(ROOT), 'show',
    ORIGINAL + ':docs/evidence/s06a/model-http-cases.json'], text=True))['cases']
cases = []
for file in sorted((ROOT / 'ydental_queue_test/tests').glob('test_*.py')):
    for cls in ast.parse(file.read_text()).body:
        if isinstance(cls, ast.ClassDef):
            cases.extend({'class': cls.name, 'method': method.name, 'file': str(file.relative_to(ROOT)),
                          'kind': 'HTTP/RPC' if 'HTTP' in cls.name else 'model'}
                         for method in cls.body if isinstance(method, ast.FunctionDef) and method.name.startswith('test_'))
assert len(original) == 32 and all(case in cases for case in original)
for file in {case['file'] for case in original}:
    before = ast.parse(subprocess.check_output(['git', '-C', str(ROOT), 'show', ORIGINAL + ':' + file], text=True))
    after = ast.parse((ROOT / file).read_text())
    assert ast.dump(before) == ast.dump(after), 'Original business methods changed: ' + file
actions = [json.loads(line) for line in (run / 'actions.jsonl').read_text().splitlines()]
for action in ('install', 'upgrade'):
    record = next(row for row in reversed(actions) if row['action'] == action)
    assert record['tested_commit'] == head and record['exit_code'] == 0 and record['tests'][:2] == [0, 0]
    log = (run / record['log']).read_text()
    actual = set(re.findall(r'Starting (\w+\.test_\w+)', log))
    expected = {case['class'] + '.' + case['method'] for case in cases}
    assert expected <= actual, (action, sorted(expected - actual))
old_probe = json.loads(subprocess.check_output(['git', '-C', str(ROOT), 'show', ORIGINAL +
    ':docs/evidence/s06a/probe-attempts/ydental_s06a_test_20261012025405_2fd04bd7-20261012T025542887339.json'], text=True))
paths = sorted((ROOT / 'docs/evidence/s06a-rework/probe-attempts').glob(args.db + '-*.json'))
probe_path = next(path for path in reversed(paths) if json.loads(path.read_text()).get('result') == 'PASS')
probe = json.loads(probe_path.read_text())
assert len(old_probe['races']) == 16
assert [row['name'] for row in probe['races'][:16]] == [row['name'] for row in old_probe['races']]
assert all(row['result'] == 'PASS' and row['connections'] == 2 and len(set(row['backend_pids'])) == 2 for row in probe['races'])
assert all(probe['invariants'].values()) and probe['deadlocks'] == 0
evidence = ROOT / 'docs/evidence/s06a-rework'
result = {'database': args.db, 'original_final': ORIGINAL, 'test': head, 'original_methods_unchanged': 32,
          'business_methods': len(cases), 'model_methods': sum(case['kind'] == 'model' for case in cases),
          'http_methods': sum(case['kind'] == 'HTTP/RPC' for case in cases), 'original_races_preserved': 16,
          'total_races': len(probe['races']), 'actual_install_upgrade_methods_verified': True,
          'probe': str(probe_path.relative_to(ROOT)), 'result': 'PASS'}
(evidence / 'continuity.json').write_text(json.dumps(result, indent=2) + '\n')
(evidence / 'model-http-cases.json').write_text(json.dumps({'test': head, 'count': len(cases), 'cases': cases}, indent=2) + '\n')
print(json.dumps(result))

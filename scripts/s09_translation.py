"""Compare a live S09 export with the shipped Simplified Chinese catalog."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

import polib


root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--db', required=True)
args = parser.parse_args()
if not re.fullmatch(r'ydental_s09_test_[0-9]{14}_[a-f0-9]{8}', args.db):
    parser.error('Recorded isolated S09 database required')
run = root / '.local' / args.db
metadata = json.loads((run / 'database.json').read_text())
assert metadata['database'] == args.db
assert hashlib.sha256((run / 'odoo.conf').read_bytes()).hexdigest() == metadata['config_sha256']
pot = polib.pofile(str(run / 'ydental_exam.pot'))
po = polib.pofile(str(root / 'ydental_exam/i18n/zh_CN.po'))
translated = {entry.msgid: entry.msgstr for entry in po if 'fuzzy' not in entry.flags}
entries = {entry.msgid: entry for entry in po}
missing = [entry.msgid for entry in pot if not translated.get(entry.msgid)]
invalid_metadata = [entry.msgid for entry in pot if entry.msgid not in entries or any(
    marker in entry.comment and marker not in entries[entry.msgid].comment
    for marker in ('odoo-python', 'odoo-javascript'))]
invalid_codes = [entry.msgid for entry in po if re.match(r'^[a-z_]+:', entry.msgid)
                 and not entry.msgstr.startswith(entry.msgid.split(':')[0] + ':')]
result = {'database': args.db,
          'test': subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip(),
          'exported_terms': len(pot), 'translated_terms': len(pot) - len(missing),
          'missing': missing, 'invalid_code_metadata': invalid_metadata,
          'invalid_codes': invalid_codes,
          'result': 'FAIL' if missing or invalid_metadata or invalid_codes else 'PASS'}
evidence = root / 'docs/evidence/s09-rework'
evidence.mkdir(parents=True, exist_ok=True)
(evidence / ('translation-' + args.db + '.json')).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'result': result['result'], 'terms': len(pot), 'missing': len(missing),
                  'invalid_metadata': len(invalid_metadata), 'invalid_codes': len(invalid_codes)}))
raise SystemExit(result['result'] != 'PASS')

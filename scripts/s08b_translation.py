"""Check real exported S08B terms against the shipped Simplified Chinese PO."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

import polib
from lxml import etree


root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--db', required=True)
args = parser.parse_args()
if not re.fullmatch(r'ydental_s08b_test_[0-9]{14}_[a-f0-9]{8}', args.db):
    parser.error('Recorded isolated S08B database required')
run = root / '.local' / args.db
metadata = json.loads((run / 'database.json').read_text())
assert metadata['database'] == args.db
assert hashlib.sha256((run / 'odoo.conf').read_bytes()).hexdigest() == metadata['config_sha256']
pot = polib.pofile(str(run / 'ydental_treatment.pot'))
po = polib.pofile(str(root / 'ydental_treatment/i18n/zh_CN.po'))
translated = {entry.msgid: entry.msgstr for entry in po if 'fuzzy' not in entry.flags}
entries = {entry.msgid: entry for entry in po}
missing = [entry.msgid for entry in pot if not translated.get(entry.msgid)]
invalid_metadata = [entry.msgid for entry in pot if entry.msgid not in entries or any(
    marker in entry.comment and marker not in entries[entry.msgid].comment
    for marker in ('odoo-python', 'odoo-javascript'))]
result = {'database': args.db,
    'test': subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip(),
    'exported_terms': len(pot), 'translated_terms': len(pot) - len(missing), 'missing': missing,
    'source_codes_preserved': all(not e.msgid.startswith(('access_denied:', 'version_conflict:', 'lot_', 'return_', 'precision_error:', 'insufficient_balance:')) or e.msgstr.startswith(e.msgid.split(':')[0]+':') for e in po), 'invalid_code_metadata': invalid_metadata,
    'result': 'FAIL' if missing or invalid_metadata else 'PASS'}
evidence = root / 'docs/evidence/s08b-rework'
evidence.mkdir(parents=True, exist_ok=True)
(evidence / ('translation-' + args.db + '.json')).write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'result': result['result'], 'terms': len(pot), 'missing': len(missing), 'invalid_metadata': len(invalid_metadata)}))
raise SystemExit(bool(missing or invalid_metadata))

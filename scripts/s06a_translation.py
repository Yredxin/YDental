"""Check real exported S06-A terms against the shipped Simplified Chinese PO."""
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
if not re.fullmatch(r'ydental_s06a_test_[0-9]{14}_[a-f0-9]{8}', args.db):
    parser.error('Recorded isolated S06-A database required')
run = root / '.local' / args.db
metadata = json.loads((run / 'database.json').read_text())
assert metadata['database'] == args.db
assert hashlib.sha256((run / 'odoo.conf').read_bytes()).hexdigest() == metadata['config_sha256']
pot = polib.pofile(str(run / 'ydental_queue.pot'))
po = polib.pofile(str(root / 'ydental_queue/i18n/zh_CN.po'))
translated = {entry.msgid: entry.msgstr for entry in po if 'fuzzy' not in entry.flags}
missing = [entry.msgid for entry in pot if not translated.get(entry.msgid)]
for entry in pot:
    if 'id="expired-message"' in entry.msgid:
        fragment = etree.fromstring(('<root>' + translated[entry.msgid] + '</root>').encode())
        assert set(fragment.xpath('span/@id')) == {'expired-message', 'offline-message'}
        assert all('连接' in ''.join(span.itertext()) for span in fragment)
result = {'database': args.db,
    'test': subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip(),
    'exported_terms': len(pot), 'translated_terms': len(pot) - len(missing), 'missing': missing,
    'connection_message_ids_preserved': True, 'result': 'FAIL' if missing else 'PASS'}
evidence = root / 'docs/evidence/s06a'
evidence.mkdir(parents=True, exist_ok=True)
(evidence / 'translation.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'result': result['result'], 'terms': len(pot), 'missing': len(missing)}))
raise SystemExit(bool(missing))

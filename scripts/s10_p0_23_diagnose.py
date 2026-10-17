"""Supplemental FILE_ONLY diagnosis; preserve the first strict parser failure.

Full-document validity and strict standalone target-array validity are separate
claims. Never repair old JSON or substitute permissive parsing for validation.
"""
import ast
from collections import Counter, defaultdict
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / '.local/s10-p0-23'
BASE = ROOT / 'docs/evidence/s10-p0-23'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def parse(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('DUPLICATE_JSON_MEMBER')
            result[key] = value
        return result
    return json.loads(raw.decode('utf-8'), parse_float=Decimal, object_pairs_hook=unique)


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True, default=str)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def array_bounds(raw):
    """Locate one old pretty-printed tables.ir_ui_view array without fixing bytes."""
    root_marker = b'\n  "tables": {'
    assert raw.count(root_marker) == 1
    root = raw.index(root_marker)
    table_marker = b'\n    "ir_ui_view": ['
    assert raw.count(table_marker, root) == 1
    start = raw.index(table_marker, root) + len(table_marker) - 1
    depth = 0; quoted = False; escaped = False
    for pos in range(start, len(raw)):
        byte = raw[pos]
        if quoted:
            if escaped:
                escaped = False
            elif byte == 92:
                escaped = True
            elif byte == 34:
                quoted = False
        elif byte == 34:
            quoted = True
        elif byte in (91, 123):
            depth += 1
        elif byte in (93, 125):
            depth -= 1
            if depth == 0:
                return start, pos + 1
    raise ValueError('ARRAY_NOT_CLOSED')


def error_info(error, text):
    result = {'type': type(error).__name__}
    if isinstance(error, json.JSONDecodeError):
        result.update(message=error.msg, character_offset=error.pos,
                      byte_offset=len(text[:error.pos].encode()), line=error.lineno, column=error.colno,
                      offending_codepoint=ord(text[error.pos]) if error.pos < len(text) else None)
    return result


def row_bounds(raw):
    """Lexical object spans in the saved pretty-printed array; not JSON validation."""
    depth = 0; quoted = False; escaped = False; start = None
    for pos, byte in enumerate(raw):
        if quoted:
            if escaped: escaped = False
            elif byte == 92: escaped = True
            elif byte == 34: quoted = False
        elif byte == 34: quoted = True
        elif byte in (91, 123):
            if depth == 1:
                start = pos
            depth += 1
        elif byte in (93, 125):
            depth -= 1
            if depth == 1 and start is not None:
                yield start, pos + 1
                start = None


def main():
    label = sys.argv[1]
    assert label in {'diagnostic-system', 'diagnostic-fixed'}
    out = BASE / label
    out.mkdir()
    proof = parse((PRIVATE / 'supplement-api-readback.json').read_bytes())
    assert proof['body_exact'] is True
    assert proof['diagnoser_sha256'] == sha(Path(__file__).read_bytes())
    assert proof['inputs_sha256'] == sha((BASE / 'inputs.json').read_bytes())
    assert proof['initial_verifier_sha256'] == sha((ROOT / 'scripts/s10_p0_23_verify.py').read_bytes())
    initial_exit = (PRIVATE / 'verification.exit').read_text().strip()
    assert initial_exit == '1'
    # Only AST-extract small independent file helpers from the first frozen P023
    # verifier, not its main and never a P022 capture/readonly/fixture main.
    import copy
    import re
    ns = {'json': json, 'hashlib': hashlib, 'Path': Path, 'Decimal': Decimal,
          'Counter': Counter, 'defaultdict': defaultdict, 'os': os, 'copy': copy,
          'PRIVATE': PRIVATE / label, 'KEY': 'account.portal_my_journal_mail_notifications',
          'DECODER': json.JSONDecoder()}
    ns['PRIVATE'].mkdir(mode=0o700)
    names = {'span', 'canonical', 'sha', 'target', 'value_evidence', 'differences',
             'structure', 'old_functions', 'pure_counterexamples', 'unique_object', 'parse'}
    tree = ast.parse((ROOT / 'scripts/s10_p0_23_verify.py').read_text())
    funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert {n.name for n in funcs} == names
    exec(compile(ast.Module(body=funcs, type_ignores=[]), 'P023-PURE-FILE-HELPERS-ONLY', 'exec'), ns)
    inputs = parse((BASE / 'inputs.json').read_bytes())['inputs']
    checks, observations, values = [], [], {}
    for item in inputs:
        raw = (ROOT / item['path']).read_bytes()
        assert sha(raw) == item['sha256'] and len(raw) == item['bytes']
        check = {'path': item['path'], 'bytes': len(raw), 'sha256': sha(raw), 'old_manifest_match': True}
        if item['kind'] not in {'snapshot', 'full_diff', 'static_fixture'}:
            checks.append(check)
            continue
        text = raw.decode('utf-8')
        # Save strict parse outcomes independently of selected-array extraction.
        try:
            data = parse(raw)
            check['whole_JSON_strict_valid'] = True
        except (json.JSONDecodeError, ValueError) as error:
            data = None
            check['whole_JSON_strict_valid'] = False
            check['error'] = error_info(error, text)
        entries = []
        if item['kind'] == 'snapshot':
            start, end = array_bounds(raw)
            table_raw = raw[start:end]
            try:
                rows = parse(table_raw)
            except (json.JSONDecodeError, ValueError) as error:
                rows = None
                check['target_array_strict_valid'] = False
                check['target_array_error'] = error_info(error, table_raw.decode())
            if rows is not None:
                check['target_array_strict_valid'] = True
                hits = [(i, row) for i, row in enumerate(rows) if row.get('id') == 929]
                assert sum(row.get('key') == ns['KEY'] for row in rows) == 1
                i, row = hits[0]
                array_text = table_raw.decode()
                a, b = ns['span'](array_text, [i, 'arch_prev'])
                token_offset = start + len(array_text[:a].encode())
                token = array_text[a:b]
                check['target_table_canonical_sha256'] = sha(ns['canonical'](rows).encode())
            else:
                # Preserve whole-array FAIL; inspect separately strict valid row
                # slices. Unparsed rows remain explicit and cannot be omitted
                # from a table signature or represented as a repaired document.
                hits = []; invalid = []
                for i, (lo, hi) in enumerate(row_bounds(table_raw)):
                    row_raw = table_raw[lo:hi]
                    try:
                        candidate = parse(row_raw)
                    except (json.JSONDecodeError, ValueError) as error:
                        invalid.append({'row_index': i, 'array_byte_start': lo,
                                        'error': error_info(error, row_raw.decode())})
                        continue
                    if candidate.get('id') == 929:
                        hits.append((i, candidate, lo, row_raw))
                check['unparsed_row_slices'] = invalid
                assert len(hits) == 1
                i, row, lo, row_raw = hits[0]
                # Identity is unique in strict valid rows and in the exact old
                # raw top-level member spelling, not a whole-array validity claim.
                assert len(re.findall(rb'^        "id": 929,?$', table_raw, re.M)) == 1
                assert len(re.findall(rb'^        "key": "account\.portal_my_journal_mail_notifications",?$', table_raw, re.M)) == 1
                a, b = ns['span'](row_raw.decode(), ['arch_prev'])
                token = row_raw.decode()[a:b]
                token_offset = start + lo + len(row_raw.decode()[:a].encode())
                check['target_row_strict_valid'] = True
                check['raw_formatted_identity_unique'] = True
                check['strict_whole_array_signature'] = 'NOT_RECOMPUTABLE; do not skip invalid row slices'
                hits = [(i, row)]
            assert len(hits) == 1 and ns['target'](hits[0][1])
            assert json.loads(token) == row['arch_prev']
            check.update(target_array_byte_start=start, target_array_byte_end_exclusive=end,
                         target_array_raw_sha256=sha(table_raw))
            for signature in item.get('signatures', []):
                signed = parse((ROOT / signature).read_bytes())['tables']['ir_ui_view']
                if rows is not None:
                    assert signed == {'rows': len(rows), 'sha256': check['target_table_canonical_sha256']}
                    check['saved_table_signature_match'] = True
                else:
                    check['saved_table_signature_match'] = 'NOT_PROVEN_STRICTLY'
            entries = [('snapshot-target', row, '/tables/ir_ui_view/' + str(i) + '/arch_prev',
                        token_offset, token)]
        elif item['kind'] == 'full_diff':
            assert data is not None, 'FULL_DIFF_NOT_STRICT_JSON'
            for i, delta in enumerate(data):
                if delta['table'] == 'ir_ui_view' and delta['physical_key'] == ['public', 'ir_ui_view', 929]:
                    assert delta['columns'] == ['arch_prev']
                    for side in ['before', 'after']:
                        assert len(delta[side]) == 1 and ns['target'](delta[side][0])
                        assert sha(ns['canonical'](delta[side]).encode()) == delta[side + '_sha256']
                        path = [i, side, 0, 'arch_prev']
                        a, b = ns['span'](text, path)
                        entries.append(('full-diff-' + side, delta[side][0], '/' + '/'.join(map(str, path)),
                                        len(text[:a].encode()), text[a:b]))
            assert bool(entries) == item['target_expected']
        else:
            assert data is not None
            tables = sorted(data['tables']) if isinstance(data, dict) else sorted({d['table'] for d in data})
            check['static_fixture_tables'] = tables
            assert 'ir_ui_view' not in tables
        for kind, row, pointer, offset, token in entries:
            value = row['arch_prev']
            assert json.loads(token) == value
            rec = {'file': item['path'], 'label': kind, 'JSON_pointer': pointer,
                   'physical_table': row['__physical_table__'], 'physical_oid': row['__physical_oid__'],
                   'id': row['id'], 'key': row['key'], 'raw_token_byte_start': offset,
                   'raw_token_bytes': len(token.encode()), 'raw_token_sha256': sha(token.encode()),
                   'whole_row_sha256': sha(ns['canonical'](row).encode()), **ns['value_evidence'](value)}
            observations.append(rec); values[(item['path'], kind)] = value
        checks.append(check)
    save(out / 'file-diagnostics.json', {'checks': checks, 'initial_strict_verifier_exit': 1,
        'interpretation': 'whole-file strict validity, target-array validity, and target-row validity are separate claims'})
    # Publish no content until fixed-template disclosure checks pass.
    a, b, c = [values[('.local/s10-p0-22/' + name + '.json', 'snapshot-target')]
               for name in ['A-owner-scope-precommit', 'A-owner-scope-committed-RO', 'final-tail-RO']]
    core = ET.fromstring((ROOT / '../addons/account/views/account_portal_templates.xml').read_bytes())
    fixed = core.findall(".//template[@id='portal_my_journal_mail_notifications']")
    actual = ET.fromstring(a)
    assert len(fixed) == 1 and actual.attrib == {'name': fixed[0].attrib['name'], 't-name': ns['KEY']}
    assert [ns['structure'](x) for x in actual] == [ns['structure'](x) for x in fixed[0]]
    assert not re.search(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', a)
    assert b == a[:1992] + '6' + a[1993:] and c == a
    copies = []
    for group in parse((BASE / 'inputs.json').read_bytes())['same_capture_groups']:
        members = [next(o for o in observations if o['file'] == m['path'] and o['label'] == m['label']) for m in group['members']]
        assert len({o['field_sha256'] for o in members}) == 1
        assert len({o['whole_row_sha256'] for o in members}) == 1
        copies.append({'capture': group['name'], 'whole_target_rows_equal': True, 'members': group['members'],
                       'not_independent_database_measurements': True})
    save(out / 'field-observations.json', {'observations': observations, 'copies': copies})
    save(out / 'field-values.json', {'disclosure': 'fixed core literal template only; no row or patient values',
        'template_body_all_attributes_and_literals_match': True,
        'values': {name: {'text': v, **ns['value_evidence'](v)} for name, v in [('precommit', a), ('readback', b), ('tail', c)]}})
    for name, v in [('precommit', a), ('readback', b), ('tail', c)]:
        with (out / ('arch_prev-' + name + '.txt')).open('xb') as f:
            f.write(v.encode()); f.flush(); os.fsync(f.fileno())
    save(out / 'comparisons.json', {'precommit_to_readback': ns['differences'](a, b),
        'readback_to_tail': ns['differences'](b, c), 'precommit_to_tail': ns['differences'](a, c)})
    save(out / 'pure-counterexamples.json', ns['pure_counterexamples']((ROOT / 'scripts/s10_p0_22_contract.py').read_text(), a))
    assert all(sha((ROOT / item['path']).read_bytes()) == item['sha256'] for item in inputs)
    result = {'diagnostic_exit': 0, 'label': label, 'interpreter': sys.executable, 'version': sys.version,
        'inputs_match_old_manifests': len(checks), 'strict_JSON_failures': [x for x in checks if x.get('whole_JSON_strict_valid') is False],
        'strict_target_values_recovered_without_editing': len(observations),
        'all_same_capture_target_rows_equal': True, 'field_sha256': [sha(v.encode()) for v in [a, b, c]],
        'no_permissive_JSON_or_old_input_modification': True,
        'database_cause_or_business_resume_proven': False, 'cause': 'UNKNOWN',
        'runtime_operations': 0, 'initial_strict_failure_preserved': True,
        'boundary': '离线证据止于采集后对象，数据库/驱动/内存/落盘分层无法由现存材料区分'}
    save(out / 'result.json', result)
    print(json.dumps({'diagnostic_exit': 0, 'label': label, 'strict_JSON_failure_count': len(result['strict_JSON_failures']),
                      'strict_target_occurrences': len(observations), 'field_sha256': result['field_sha256']}, ensure_ascii=False))


if __name__ == '__main__':
    main()

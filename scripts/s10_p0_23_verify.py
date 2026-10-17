"""FILE_ONLY: verify existing P022 evidence bytes; never import the old runner.

Only stdlib file/AST/JSON/XML work. A matching saved value does not prove what
PostgreSQL returned. Run only after the frozen preflight REST readback.
"""
import ast
from collections import Counter, defaultdict
import copy
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/evidence/s10-p0-23'
PRIVATE = ROOT / '.local/s10-p0-23'
KEY = 'account.portal_my_journal_mail_notifications'
PARENT = '42107b731775e239ef516e718f46347382147171'
DECODER = json.JSONDecoder()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), default=str)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('DUPLICATE_JSON_OBJECT_KEY')
        result[key] = value
    return result


def parse(raw):
    return json.loads(raw.decode('utf-8'), parse_float=Decimal, object_pairs_hook=unique_object)


def save(name, value):
    path = OUT / name
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2, default=str)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def span(text, path, start=0):
    """Independent raw-token location through a known JSON path, no reserialization."""
    def ws(pos):
        while pos < len(text) and text[pos] in ' \n\r\t':
            pos += 1
        return pos
    start = ws(start)
    if not path:
        _, end = DECODER.raw_decode(text, start)
        return start, end
    head, *rest = path
    pos = ws(start + 1)
    if text[start] == '{':
        while text[pos] != '}':
            key, pos = DECODER.raw_decode(text, pos)
            pos = ws(pos)
            assert text[pos] == ':'
            pos = ws(pos + 1)
            if key == head:
                return span(text, rest, pos)
            _, pos = DECODER.raw_decode(text, pos)
            pos = ws(pos)
            if text[pos] == ',':
                pos = ws(pos + 1)
    elif text[start] == '[':
        index = 0
        while text[pos] != ']':
            if index == head:
                return span(text, rest, pos)
            _, pos = DECODER.raw_decode(text, pos)
            pos = ws(pos)
            if text[pos] == ',':
                pos = ws(pos + 1)
            index += 1
    raise KeyError(path)


def value_evidence(value):
    assert isinstance(value, str)
    encoded = value.encode('utf-8')
    return {'type': type(value).__name__, 'characters': len(value), 'UTF8_bytes': len(encoded),
            'field_sha256': sha(encoded), 'UTF8_hex': encoded.hex()}


def differences(left, right):
    """Offsets are zero based. Explicitly handle length differences as well."""
    chars, bytes_ = [], []
    for i in range(max(len(left), len(right))):
        a = left[i] if i < len(left) else None
        b = right[i] if i < len(right) else None
        if a != b:
            chars.append({'character_offset': i, 'left': a, 'right': b,
                          'left_codepoint': ord(a) if a is not None else None,
                          'right_codepoint': ord(b) if b is not None else None,
                          'left_UTF8_offset': len(left[:i].encode()), 'right_UTF8_offset': len(right[:i].encode()),
                          'left_context': left[max(0, i - 20):i + 21],
                          'right_context': right[max(0, i - 20):i + 21]})
    a, b = left.encode(), right.encode()
    for i in range(max(len(a), len(b))):
        x = a[i] if i < len(a) else None
        y = b[i] if i < len(b) else None
        if x != y:
            bytes_.append({'byte_offset': i, 'left': x, 'right': y})
    return {'equal': left == right, 'character_differences': chars, 'byte_differences': bytes_}


def target(row):
    return row.get('id') == 929 and row.get('key') == KEY and row.get('__physical_table__') == 'ir_ui_view'


def record(raw, path, row, label):
    assert target(row) and isinstance(row.get('__physical_oid__'), int)
    value = row['arch_prev']
    text = raw.decode('utf-8')
    a, b = span(text, path)
    token = text[a:b]
    assert json.loads(token) == value
    return {'label': label, 'JSON_pointer': '/' + '/'.join(map(str, path)),
            'physical_schema': 'public (fixed capture SQL)', 'physical_table': row['__physical_table__'],
            'physical_oid': row['__physical_oid__'], 'id': row['id'], 'key': row['key'],
            'whole_target_row_sha256': sha(canonical(row).encode()),
            'raw_JSON_token_character_start': a, 'raw_JSON_token_character_end_exclusive': b,
            'raw_JSON_token_byte_start': len(text[:a].encode()), 'raw_JSON_token_bytes': len(token.encode()),
            'raw_JSON_token_sha256': sha(token.encode()), **value_evidence(value)}


def structure(node):
    """Ignore formatting whitespace only; keep every literal and attribute."""
    return [node.tag, sorted(node.attrib.items()), (node.text or '').strip(),
            [[structure(child), (child.tail or '').strip()] for child in node]]


def old_functions(source, names, namespace):
    """Compile only named pure helpers, never the old module or its main/imports."""
    tree = ast.parse(source)
    selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    assert {node.name for node in selected} == set(names)
    assert not any(isinstance(node, (ast.Import, ast.ImportFrom)) for f in selected for node in ast.walk(f))
    exec(compile(ast.Module(body=selected, type_ignores=[]), 'P022-AST-PURE-HELPERS-ONLY', 'exec'), namespace)
    return selected


def pure_counterexamples(source, text):
    dest = PRIVATE / 'pure-examples'
    dest.mkdir(mode=0o700)
    namespace = {'Counter': Counter, 'defaultdict': defaultdict, 'Path': Path, 'hashlib': hashlib,
                 'json': json, 'os': os, 'PRIVATE': dest, 'OUT': dest}
    old_functions(source, ['canonical', 'sha', 'economic', 'diff', 'save', 'persist', 'exact'], namespace)
    diff, persist = namespace['diff'], namespace['persist']
    row = {'id': 929, 'key': KEY, '__physical_table__': 'ir_ui_view', '__physical_oid__': 1, 'arch_prev': text}
    a = {'tables': {'ir_ui_view': [row]}, 'schema': {'ir_ui_view': []}}
    bad = copy.deepcopy(a)
    bad['tables']['ir_ui_view'][0]['arch_prev'] = text[:1992] + '6' + text[1993:]
    baseline = canonical(a)
    tests = []
    assert not diff(a, copy.deepcopy(a))[0]
    tests.append('equal independently decoded objects => no diff')
    delta = diff(a, bad)[0]
    assert len(delta) == 1 and delta[0]['columns'] == ['arch_prev']
    assert delta[0]['before'][0]['arch_prev'] == text
    tests.append('exact v-to-6 synthetic substitution => arch_prev only')
    def reject(before, after, changes):
        assert all((dest / ('reject-' + suffix + '.json')).exists() for suffix in ['before', 'after', 'full-diff', 'diff-index'])
        assert changes and canonical(before) == baseline
        raise AssertionError('SYNTHETIC_EXPECTED_REJECTION')
    try:
        persist('reject', a, bad, reject)
    except AssertionError:
        pass
    else:
        raise AssertionError('MISSING_SYNTHETIC_REJECTION')
    assert canonical(a) == baseline
    fail_sha = sha((dest / 'reject-decision.json').read_bytes())
    tests.append('before/after/full-diff/index written before rejection; input unchanged')
    persist('later-equal', a, copy.deepcopy(a), namespace['exact'])
    assert sha((dest / 'reject-decision.json').read_bytes()) == fail_sha
    tests.append('later equality does not overwrite earlier FAIL')
    try:
        namespace['save'](dest / 'reject-decision.json', {'tamper': True})
    except FileExistsError:
        pass
    else:
        raise AssertionError('EXCLUSIVE_SAVE_BROKEN')
    assert sha((dest / 'reject-decision.json').read_bytes()) == fail_sha
    tests.append('exclusive x open refuses duplicate output path')
    duplicate = copy.deepcopy(a)
    duplicate['tables']['ir_ui_view'].append(copy.deepcopy(row))
    assert diff(a, duplicate)[0][0]['duplicate_key_preserved']
    tests.append('same physical table/id duplicate is retained, not dictionary overwritten')
    reversed_rows = {'tables': {'ir_ui_view': [row, dict(row, id=930)]}, 'schema': a['schema']}
    rearranged = copy.deepcopy(reversed_rows)
    rearranged['tables']['ir_ui_view'].reverse()
    assert not diff(reversed_rows, rearranged)[0]
    tests.append('row reordering does not make a field delta')
    unicode = differences('牙v', '牙6')
    assert unicode['character_differences'][0]['character_offset'] == 1
    assert unicode['byte_differences'][0]['byte_offset'] == 3
    tests.append('UTF8 multibyte positive counterexample separates character and byte offsets')
    try:
        parse(b'{"id":929,"id":930}')
    except ValueError:
        pass
    else:
        raise AssertionError('INDEPENDENT_DUPLICATE_JSON_KEY_ACCEPTED')
    tests.append('independent parser rejects duplicate JSON member names')
    original = {'schema': {'ir_ui_view': [{'column': 'arch_prev'}]}, 'tables': {'ir_ui_view': [row]}}
    shallow = {k: v for k, v in original.items() if k != 'tables'}
    shallow['tables'] = {'ir_ui_view': copy.deepcopy(original['tables']['ir_ui_view'])}
    shallow['schema']['ir_ui_view'][0]['column'] = 'SYNTHETIC_METADATA_MUTATION'
    assert original['schema']['ir_ui_view'][0]['column'] == 'SYNTHETIC_METADATA_MUTATION'
    assert shallow['tables']['ir_ui_view'][0] is not original['tables']['ir_ui_view'][0]
    tests.append('fixture pattern shares schema metadata, but deepcopied table rows are independent')
    escaped = json.dumps(text, ensure_ascii=True)
    literal = json.dumps(text, ensure_ascii=False)
    assert json.loads(escaped) == json.loads(literal) == text
    # Two synthetic layer histories give the same saved object; no claim either happened.
    raw_variant = json.loads(json.dumps({'arch_prev': text[:1992] + '6' + text[1993:]}))
    object_variant = json.loads(json.dumps({'arch_prev': text}))
    object_variant['arch_prev'] = object_variant['arch_prev'][:1992] + '6' + object_variant['arch_prev'][1993:]
    assert canonical(raw_variant) == canonical(object_variant)
    tests.append('synthetic pre-parse vs post-parse substitution is indistinguishable after object-only save')
    return {'exit_code': 0, 'tests_passed': len(tests), 'tests': tests,
            'old_main_capture_readonly_native_fixture_executed': False,
            'examples_are_synthetic_not_P022_reconstructed_raw_queries': True,
            'shared_fixture_metadata_can_explain_exact_observed_arch_prev_delta': False,
            'general_possibility_is_not_root_cause': True}


def main():
    proof = parse((PRIVATE / 'preflight-api-readback.json').read_bytes())
    assert proof['body_exact'] is True and proof['comment_id'] > 0
    assert sha((OUT / 'inputs.json').read_bytes()) == proof['inputs_sha256']
    manifest = parse((OUT / 'inputs.json').read_bytes())
    assert sha(Path(__file__).read_bytes()) == proof['verifier_sha256']
    checks = []
    for item in manifest['inputs']:
        path = ROOT / item['path']
        raw = path.read_bytes()
        checks.append({'path': item['path'], 'bytes': len(raw), 'sha256': sha(raw),
                       'expected_sha256': item['sha256'], 'expected_bytes': item['bytes'],
                       'match': sha(raw) == item['sha256'] and len(raw) == item['bytes'],
                       'authority': item['authority'], 'Git_blob': item.get('Git_blob')})
    save('input-byte-verification.json', {'checks': checks, 'all_match': all(x['match'] for x in checks)})
    assert all(x['match'] for x in checks), 'INPUT_BYTES_OR_OLD_MANIFEST_MISMATCH'
    public_index = {x['path']: x for x in parse((ROOT / 'docs/evidence/s10-p0-22/file-sha256.json').read_bytes())['files']}
    private_index = {x['path']: x for x in parse((ROOT / 'docs/evidence/s10-p0-22/private-evidence-manifest.json').read_bytes())['files']}
    for item in manifest['inputs']:
        if item['authority'] in {'P022 public manifest', 'P022 private manifest'}:
            old = (public_index if item['authority'] == 'P022 public manifest' else private_index)[item['path']]
            assert item['sha256'] == old['sha256'] and item['bytes'] == old['bytes']
    # Only now parse old snapshots: all exact raw bytes have first matched old manifests.
    observations, tables, values, comparisons = [], {}, {}, []
    for item in manifest['inputs']:
        if item['kind'] not in {'snapshot', 'full_diff'}:
            continue
        raw = (ROOT / item['path']).read_bytes()
        data = parse(raw)
        entries = []
        if item['kind'] == 'snapshot':
            rows = data['tables']['ir_ui_view']
            matches = [(i, row) for i, row in enumerate(rows) if row.get('id') == 929]
            assert len(matches) == 1 and target(matches[0][1])
            assert sum(row.get('key') == KEY for row in rows) == 1
            i, row = matches[0]
            path = ['tables', 'ir_ui_view', i, 'arch_prev']
            entries.append((path, row, 'snapshot-target'))
            tables[item['path']] = {'rows': len(rows), 'sha256': sha(canonical(rows).encode()),
                                   'row929_sha256': sha(canonical(row).encode())}
            for signature in item.get('signatures', []):
                signed = parse((ROOT / signature).read_bytes())
                assert signed['tables']['ir_ui_view'] == {'rows': len(rows), 'sha256': tables[item['path']]['sha256']}
                comparisons.append({'kind': 'table_signature', 'snapshot': item['path'],
                                    'signature': signature, 'ir_ui_view_match': True,
                                    'scope': 'only this saved table signature; not 645-table remeasurement'})
        else:
            assert isinstance(data, list)
            for i, change in enumerate(data):
                if change.get('table') == 'ir_ui_view' and change['physical_key'] == ['public', 'ir_ui_view', 929]:
                    assert change['columns'] == ['arch_prev']
                    for side in ['before', 'after']:
                        assert len(change[side]) == 1
                        row = change[side][0]
                        assert sha(canonical(change[side]).encode()) == change[side + '_sha256']
                        entries.append(([i, side, 0, 'arch_prev'], row, 'full-diff-' + side))
            assert bool(entries) == item['target_expected']
        current = []
        for path, row, label in entries:
            rec = record(raw, path, row, label)
            rec['file'] = item['path']
            observations.append(rec)
            values[(item['path'], label)] = row['arch_prev']
            current.append({'JSON_pointer': rec['JSON_pointer'], 'field_sha256': rec['field_sha256']})
        if not entries:
            comparisons.append({'kind': 'no_target_in_full_diff', 'file': item['path'], 'changes': len(data)})
        del data, raw
    for group in manifest['same_capture_groups']:
        members = [next(rec for rec in observations if rec['file'] == member['path'] and rec['label'] == member['label']) for member in group['members']]
        assert len({rec['field_sha256'] for rec in members}) == 1
        assert len({rec['whole_target_row_sha256'] for rec in members}) == 1
        comparisons.append({'kind': 'same_capture_saved_copies', 'capture': group['name'], 'members': group['members'],
                            'field_values_equal': True, 'whole_target_rows_equal': True, 'not_independent_database_measurements': True,
                            'distinct_full_file_sha256': sorted({next(x['sha256'] for x in checks if x['path'] == rec['file']) for rec in members})})
    a = values[('.local/s10-p0-22/A-owner-scope-precommit.json', 'snapshot-target')]
    b = values[('.local/s10-p0-22/A-owner-scope-committed-RO.json', 'snapshot-target')]
    c = values[('.local/s10-p0-22/final-tail-RO.json', 'snapshot-target')]
    assert a == c and len(differences(a, b)['character_differences']) == 1
    assert differences(a, b)['character_differences'][0]['character_offset'] == 1992
    assert a[1992] == 'v' and b[1992] == '6'
    # Establish disclosure scope against fixed core literals before publishing any full value.
    core = ET.fromstring((ROOT / '../addons/account/views/account_portal_templates.xml').read_bytes())
    templates = core.findall(".//template[@id='portal_my_journal_mail_notifications']")
    assert len(templates) == 1
    actual = ET.fromstring(a)
    assert actual.tag == 't' and actual.attrib == {'name': templates[0].attrib['name'], 't-name': KEY}
    assert [structure(x) for x in actual] == [structure(x) for x in templates[0]]
    assert not re.search(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', a)
    assert b == a[:1992] + '6' + a[1993:] and c == a
    disclosure = {'fixed_core_template_children_and_all_literals_attributes_match': True,
                  'root_loader_conversion': 'template id/name => t name/t-name plus XML declaration and formatting whitespace',
                  'literal_csrf_expression_not_a_token': 'request.csrf_token()',
                  'literal_email_variables_not_patient_values': ['t-if=email', 't-out=email'],
                  'observed_variant_only_exact_single_character_difference': True,
                  'whole_database_rows_published': False}
    save('disclosure-check.json', disclosure)
    # Hex and nearby fragments also disclose content: save them only after this gate.
    save('field-observations.json', {'observations': observations, 'target_table_signatures': tables})
    save('comparisons.json', {'comparisons': comparisons, 'precommit_to_readback': differences(a, b),
                            'readback_to_tail': differences(b, c), 'precommit_to_tail': differences(a, c)})
    for name, val in [('precommit', a), ('readback', b), ('tail', c)]:
        with (OUT / ('arch_prev-' + name + '.txt')).open('xb') as stream:
            stream.write(val.encode()); stream.flush(); os.fsync(stream.fileno())
    save('field-values.json', {'scope': 'only core-template arch_prev, not entire row or snapshot',
                              'disclosure': disclosure,
                              'values': {name: {'text': val, **value_evidence(val)} for name, val in [('precommit', a), ('readback', b), ('tail', c)]}})
    source = (ROOT / 'scripts/s10_p0_22_contract.py').read_text()
    save('pure-counterexamples.json', pure_counterexamples(source, a))
    fixtures = []
    for item in manifest['inputs']:
        if item['kind'] != 'static_fixture':
            continue
        data = parse((ROOT / item['path']).read_bytes())
        if isinstance(data, dict):
            tables_ = sorted(data['tables'])
            assert 'ir_ui_view' not in tables_
            fixtures.append({'path': item['path'], 'fixture_tables': tables_,
                             'target_view_table_present': False,
                             'full_schema_may_be_shared_but_tables_are_selected_deepcopies': True})
        else:
            assert not any(row['table'] == 'ir_ui_view' for row in data)
            fixtures.append({'path': item['path'], 'changed_tables': sorted({row['table'] for row in data}),
                             'target_view_table_present': False})
    save('saved-static-fixture-audit.json', {'fixtures': fixtures,
        'can_explain_exact_observed_view_delta': False, 'old_fixture_main_executed': False})
    code_map = []
    for item in manifest['inputs']:
        if item['kind'] != 'source' or not item['path'].endswith('.py'):
            continue
        tree = ast.parse((ROOT / item['path']).read_text())
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                code_map.append({'file': item['path'], 'function': node.name, 'first_line': node.lineno,
                                 'last_line': node.end_lineno, 'AST_sha256': sha(ast.dump(node, include_attributes=False).encode())})
    save('AST-source-map.json', {'functions': code_map, 'source_modules_imported': False})
    # Final original-byte recheck. Never write an old file, including old FAIL decisions.
    assert all(sha((ROOT / item['path']).read_bytes()) == item['sha256'] for item in manifest['inputs'])
    result = {'FILE_ONLY_verifier_exit': 0, 'input_count': len(checks), 'field_occurrences': len(observations),
              'whole_input_bytes_before_after_unchanged': True, 'same_capture_copies_consistent': True,
              'field_lengths': [value_evidence(v) for v in [a, b, c]],
              'cause': 'UNKNOWN', 'boundary': '离线证据止于采集后对象，数据库/驱动/内存/落盘分层无法由现存材料区分',
              'missing': ['original per-row to_jsonb return text', 'same-statement server field SHA/hex',
                          'pre-json.loads buffer or immediate post-parse field digest'],
              'runtime_budget_actual': {k: 0 for k in ['database_connections', 'SELECT', 'CREATE', 'DML', 'Odoo', 'business_HTTP_RPC',
                  'browser', 'PDF', 'scope_login', 'document_actions', 'payments_refunds', 'upgrade_install', 'permission_changes',
                  'product_core_changes', 'sudo', 'OS_PG_Docker_network_hardware_special']},
              'five_business_groups': 'unchanged A BLOCKED; B/C/D/E NOT_RUN', 'S10_stage_exit': 'BLOCKED',
              'database_integrity_or_business_resume_proven': False}
    save('verification-result.json', result)
    print(json.dumps({k: result[k] for k in ['FILE_ONLY_verifier_exit', 'input_count', 'field_occurrences', 'same_capture_copies_consistent', 'cause', 'boundary']}, ensure_ascii=False))


if __name__ == '__main__':
    main()

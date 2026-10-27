#!/usr/bin/env python3
"""Restore only enumerated P13 presentation and compare all frozen source bytes.

SOURCE/PURE only: this does not submit a bill or prove a loaded browser result.
"""
import argparse
import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess

from lxml import etree

ROOT = Path(__file__).resolve().parents[2]
BASE = '4e3e3aa1027286de473044d23f54d5faa81c9384'
XML = 'ydental_settlement/views/ydental_settlement_templates.xml'
MANIFEST = 'ydental_settlement/__manifest__.py'
ASSET = 'ydental_settlement/static/src/scss/settlement_bill_panel.scss'
PREFIX = 'o_ydental_settlement_bill_'
SCOPE = 'settlement-bill-panel'
ACTIONS = SCOPE + '-actions'
XPATH = ".//details[@name='settlement-operation'][form/input[@name='operation'][@value='bill']]"
WRAPPERS = {
    PREFIX + name for name in ('fee_group', 'fees', 'fee_text', 'fields', 'submit', 'action_label')
}
_spec = importlib.util.spec_from_file_location(
    'p13_original_p12_source_helpers', ROOT / 'scripts/s13_dl_p12/source_contracts.py')
_helpers = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_helpers)
parse, canonical, unwrap = _helpers.parse, _helpers.canonical, _helpers.unwrap


def original(path):
    return subprocess.check_output(['git', 'show', BASE + ':' + path], cwd=ROOT)


def bill(tree):
    found = tree.xpath(XPATH)
    assert len(found) == 1, 'Exactly one native bill operation is required'
    node = found[0]
    assert node.get('t-if') == 'can_write and (today or history)'
    assert not node.xpath('.//details'), 'Do not introduce nested operations'
    return node


def split(raw):
    start = raw.index(b'<details name="settlement-operation"')
    end = raw.index(b'</details>', start) + len(b'</details>')
    assert b'name="operation" value="bill"' in raw[start:end]
    return raw[:start], raw[start:end], raw[end:]


def restore(tree):
    node = bill(tree)
    assert node.get('data-dl-scope') == SCOPE
    wrappers = [n for n in node.iter() if n.get('class') in WRAPPERS]
    for n in wrappers:
        allowed = {'class', 't-translation'} if n.tag == 'span' else {'class'}
        assert set(n.attrib) <= allowed, 'A wrapper cannot contain business attributes'
        assert n.tag in ('div', 'span')
        if 't-translation' in n.attrib:
            assert n.get('class') == PREFIX + 'action_label'
            assert n.get('t-translation') == 'on'
    for n in node.iter():
        classes = n.get('class', '').split()
        kept = [c for c in classes if not c.startswith(PREFIX)]
        if classes != kept:
            if kept:
                n.set('class', ' '.join(kept))
            else:
                n.attrib.pop('class', None)
        if 'data-dl-scope' in n.attrib:
            assert n is node and n.get('data-dl-scope') == SCOPE
            n.attrib.pop('data-dl-scope')
        if 'data-dl-actions' in n.attrib:
            assert n.tag in ('summary', 'button', 'a') and n.get('data-dl-actions') == ACTIONS
            n.attrib.pop('data-dl-actions')
    for n in reversed(wrappers):
        unwrap(n)
    labels = node.xpath(".//label[@t-foreach='today | history'][@t-as='fee']")
    assert len(labels) == 1
    assert labels[0].get('style') in (None, 'display:block')
    labels[0].set('style', 'display:block')
    return parse(etree.tostring(tree))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=('before', 'after'), required=True)
    args = parser.parse_args()
    before = original(XML)
    after = (ROOT / XML).read_bytes()
    old_tree, new_tree = parse(before), parse(after)
    old_bill, new_bill = bill(old_tree), bill(new_tree)
    css_result = None
    prefix, _, suffix = split(before)
    new_prefix, _, new_suffix = split(after)
    assert prefix == new_prefix, 'Complete header/lookup prefix must remain byte exact'
    assert suffix == new_suffix, 'Complete suffix after the first bill must remain byte exact'
    paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', BASE], cwd=ROOT, text=True).splitlines()
    frozen = []
    for path in paths:
        if not path.startswith('ydental_') or (args.phase == 'after' and path in (XML, MANIFEST)):
            continue
        raw = (ROOT / path).read_bytes()
        assert raw == original(path), 'Frozen source changed: ' + path
        frozen.append({'file': path, 'sha256': hashlib.sha256(raw).hexdigest()})
    if args.phase == 'after':
        assert canonical(restore(copy.deepcopy(new_tree))) == canonical(old_tree), 'Restored complete business XML differs'
        old_manifest = ast.literal_eval(original(MANIFEST).decode())
        new_manifest = ast.literal_eval((ROOT / MANIFEST).read_text())
        assets = new_manifest['assets']['web.assets_frontend']
        assert assets.count(ASSET) == 1
        assets.remove(ASSET)
        assert old_manifest == new_manifest, 'Only the one new CSS asset is allowed'
        changes = subprocess.check_output(['git', 'diff', '--name-only', BASE], cwd=ROOT, text=True).splitlines()
        changes += subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard'], cwd=ROOT, text=True).splitlines()
        addon_changes = sorted({p for p in changes if p.startswith('ydental_')})
        assert addon_changes == sorted([XML, MANIFEST, ASSET]), addon_changes
        import sass
        mixin = ROOT / 'ydental_access/static/src/scss/_actions.scss'
        css = sass.compile(string=mixin.read_text() + '\n' + (ROOT / ASSET).read_text())
        scope = '.o_ydental_settlement_bill_panel[data-dl-scope="' + SCOPE + '"]'
        leaves = []
        for match in re.finditer(r'([^{}]+)\{', css):
            selector = match.group(1).strip()
            if selector.startswith('@'):
                assert selector.startswith('@media'), 'Unexpected global CSS at-rule'
                continue
            for leaf in selector.split(','):
                assert leaf.strip().startswith(scope), 'Unscoped CSS: ' + leaf
                leaves.append(leaf.strip())
        assert leaves and 'zoom:' not in css and 'scale(' not in css
        css_result = {'bytes': len(css.encode()), 'sha256': hashlib.sha256(css.encode()).hexdigest(),
                      'all_selector_leaves_scoped': True, 'leaf_count': len(leaves)}
    else:
        assert before == after and canonical(old_bill) == canonical(new_bill)
    print(json.dumps({
        'status': 'P13_' + args.phase.upper() + '_FROZEN_SOURCE_CONTRACT_PASS',
        'layer': 'SOURCE_PURE_NOT_LOADED_OR_BROWSER', 'baseline': BASE,
        'candidate': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'prefix_lookup_and_entire_suffix_bytes_exact': True,
        'whole_business_XML_restored_exact': True,
        'frozen_addon_count': len(frozen),
        'frozen_inventory_sha256': hashlib.sha256(json.dumps(frozen, sort_keys=True).encode()).hexdigest(),
        'contract_form_action': new_bill.find('form').get('action'),
        'compiled_css': css_result,
        'live_submission_performed': False,
    }))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Restore enumerated P12 presentation and check the full original source (PURE)."""
import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from lxml import etree

ROOT = Path(__file__).resolve().parents[2]
BASE = 'bd0f73a99eb6f49c27d99a5db4cc6d4f8dedf008'
FILE = 'ydental_settlement/views/ydental_settlement_templates.xml'
MANIFEST = 'ydental_settlement/__manifest__.py'
ASSET = 'ydental_settlement/static/src/scss/settlement_readonly_actions.scss'
SCOPE = 'settlement-readonly-actions'
OPT = 'settlement_readonly_actions'
PREFIX = 'o_ydental_settlement_'
ICONS = {
    'ydental_inventory.p7_icon_search',
    'ydental_inventory.p7_icon_chevron_left',
    'ydental_inventory.p7_icon_chevron_right',
    'ydental_inventory.p7_icon_arrow_right',
}


def original(name):
    return subprocess.check_output(['git', 'show', BASE + ':' + name], cwd=ROOT)


def parse(raw):
    # XML formatting-only whitespace is separate from all meaningful text/tails.
    return etree.fromstring(raw, etree.XMLParser(remove_blank_text=True))


def canonical(tree):
    return etree.tostring(tree, method='c14n')


def inside(node):
    return bool(node.xpath('ancestor-or-self::div[@data-dl-scope="settlement-lookup"]'))


def shared(node):
    return bool(node.xpath('ancestor-or-self::template[@id="ydental_settlement_page_links"]'))


def drop(node):
    parent = node.getparent()
    tail = node.tail
    index = parent.index(node)
    parent.remove(node)
    if tail:
        if index:
            parent[index - 1].tail = (parent[index - 1].tail or '') + tail
        else:
            parent.text = (parent.text or '') + tail


def unwrap(node):
    parent = node.getparent()
    index = parent.index(node)
    text, tail, children = node.text, node.tail, list(node)
    if text:
        if index:
            parent[index - 1].tail = (parent[index - 1].tail or '') + text
        else:
            parent.text = (parent.text or '') + text
    for offset, child in enumerate(children):
        node.remove(child)
        parent.insert(index + offset, child)
    parent.remove(node)
    if tail:
        if children:
            children[-1].tail = (children[-1].tail or '') + tail
        elif index:
            parent[index - 1].tail = (parent[index - 1].tail or '') + tail
        else:
            parent.text = (parent.text or '') + tail


def expression(value, enabled):
    parsed = ast.parse(value, mode='eval')
    allowed = (ast.Expression, ast.IfExp, ast.Name, ast.Load, ast.Constant,
               ast.BoolOp, ast.Or, ast.And, ast.UnaryOp, ast.Not)
    assert all(isinstance(node, allowed) for node in ast.walk(parsed)), value
    assert {node.id for node in ast.walk(parsed) if isinstance(node, ast.Name)} <= {OPT}
    return eval(compile(parsed, '<P12 presentation-only expression>', 'eval'),
                {'__builtins__': {}}, {OPT: enabled})


def shared_branches(tree, enabled):
    """Reduce only the named presentation flag, never a business condition."""
    for parent in list(tree.iter()):
        children = list(parent)
        for node in children:
            condition = node.get('t-if')
            if condition not in (OPT, 'not ' + OPT):
                continue
            assert shared(node), 'Presentation branching must remain in shared pager'
            sibling = node.getnext()
            alternative = sibling if sibling is not None and sibling.get('t-else') is not None else None
            choose = enabled if condition == OPT else not enabled
            if choose:
                node.attrib.pop('t-if')
                if alternative is not None:
                    drop(alternative)
                if node.tag == 't':
                    unwrap(node)
            else:
                drop(node)
                if alternative is not None:
                    alternative.attrib.pop('t-else')
                    if alternative.tag == 't':
                        unwrap(alternative)
    return tree


def restore(tree, old, enabled):
    tree = shared_branches(copy.deepcopy(tree), enabled)
    icons = []
    for node in list(tree.iter()):
        name = node.get('t-call', '')
        if name.startswith('ydental_inventory.p7_icon_'):
            assert (inside(node) or shared(node)) and name in ICONS
            icons.append(name)
            drop(node)
    for node in list(tree.iter()):
        if node.tag != 'span':
            continue
        classes = node.get('class', '').split()
        if classes == [PREFIX + 'action_label']:
            assert inside(node) or shared(node)
            assert node.get('t-translation') == 'on'
            assert set(node.attrib) == {'class', 't-translation'} and not len(node)
            unwrap(node)
        elif classes == [PREFIX + 'trace_body']:
            assert inside(node) and node.getparent().tag == 'details'
            assert set(node.attrib) == {'class'}
            assert not node.xpath('.//a|.//button|.//form|.//summary|.//details')
            unwrap(node)
    prior = list(old.iter())
    current = list(tree.iter())
    assert len(prior) == len(current), 'No business/wrapper nodes beyond enumerated presentation'
    call_markers = 0
    for before, after in zip(prior, current):
        assert before.tag == after.tag, (before.tag, after.tag)
        before_classes = before.get('class', '').split()
        after_classes = after.get('class', '').split()
        extra = [name for name in after_classes if name not in before_classes]
        if extra:
            assert inside(after) or shared(after), 'Class escapes lookup/shared opt-in'
            assert all(name.startswith(PREFIX) for name in extra), extra
        assert [name for name in after_classes if name in before_classes] == before_classes
        if 'class' in before.attrib:
            after.set('class', before.get('class'))
        else:
            after.attrib.pop('class', None)
        if after.get('data-dl-actions') is not None:
            assert inside(after) and after.tag in ('button', 'a', 'summary')
            assert after.get('data-dl-actions') == SCOPE
            after.attrib.pop('data-dl-actions')
        if after.get(OPT) is not None:
            assert inside(after) and after.get('t-call') == 'ydental_settlement.ydental_settlement_page_links'
            assert after.get(OPT) == 'True'
            call_markers += 1
            after.attrib.pop(OPT)
        for attribute in ('t-att-class', 't-att-data-dl-actions'):
            if OPT not in after.get(attribute, ''):
                continue
            assert shared(after) and attribute not in before.attrib
            off = expression(after.get(attribute), False)
            on = expression(after.get(attribute), True)
            assert off is None, 'Every default shared call must retain its original attributes'
            if attribute == 't-att-data-dl-actions':
                assert on == SCOPE
            else:
                assert isinstance(on, str) and on
                assert all(name.startswith(PREFIX) for name in on.split())
            after.attrib.pop(attribute)
    assert call_markers == 3
    assert canonical(old) == canonical(tree), 'Full business XML changed outside enumerated presentation'
    return tree, icons


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-only', action='store_true',
                        help='Check initial unchanged product sources before implementation')
    args = parser.parse_args()
    old_raw = original(FILE)
    raw = (ROOT / FILE).read_bytes()
    old, new = parse(old_raw), parse(raw)
    scope = new.xpath('.//div[@data-dl-scope="settlement-lookup"]')
    assert len(scope) == 1
    main_node = scope[0].getparent()
    first_operation = main_node.xpath('./details[@name="settlement-operation"]')[0]
    assert main_node.index(scope[0]) < main_node.index(first_operation)
    assert not scope[0].xpath('.//details[@name="settlement-operation"]|.//form[@method="post"]')
    suffix = b'<details name="settlement-operation"'
    assert old_raw[old_raw.index(suffix):] == raw[raw.index(suffix):], 'Original first-operation through file end must remain exact bytes'
    page_start = b'<main class="container py-4 o_ydental_settlement"'
    lookup_start = b'<div class="o_ydental_settlement_lookup"'
    assert old_raw[old_raw.index(page_start):old_raw.index(lookup_start)] == raw[raw.index(page_start):raw.index(lookup_start)], 'Original page header remains exact bytes'
    if args.baseline_only:
        assert old_raw == raw
        restored, icons = new, []
    else:
        restored, icons = restore(new, old, True)
        default, _ = restore(new, old, False)
        assert canonical(default) == canonical(restored)
    before = ast.literal_eval(original(MANIFEST).decode())
    after = ast.literal_eval((ROOT / MANIFEST).read_text())
    if not args.baseline_only:
        assert after['assets']['web.assets_frontend'].count(ASSET) == 1
        after['assets']['web.assets_frontend'].remove(ASSET)
    assert before == after, 'Only the new local final SCSS asset is allowed'
    changed = subprocess.check_output(['git', 'diff', '--name-only', BASE], cwd=ROOT, text=True).splitlines()
    untracked = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard'], cwd=ROOT, text=True).splitlines()
    addon_changes = {name for name in changed + untracked if name.startswith('ydental_')}
    allowed = set() if args.baseline_only else {FILE, MANIFEST, ASSET}
    assert addon_changes == allowed, sorted(addon_changes)
    frozen = ['ydental_settlement/static/src/scss/settlement_lookup.scss',
              'ydental_access/static/src/scss/_actions.scss',
              'ydental_inventory/views/ydental_inventory_templates.xml',
              'ydental_inventory/static/lib/lucide/SOURCE.json',
              'ydental_inventory/static/lib/lucide/LICENSE',
              'ydental_reporting/static/src/report_source_detail/report_source_detail.scss']
    for name in frozen:
        assert original(name) == (ROOT / name).read_bytes(), name
    sys.path.insert(0, str(ROOT.parent))
    from odoo.tools.translate import xml_translate
    def terms(tree):
        values = []
        xml_translate(lambda value: values.append(value) or value,
                      etree.tostring(tree, encoding='unicode'))
        return values
    prior_terms, new_terms = terms(old), terms(new)
    # Shared opt-in branches may repeat the same original pager label. Their
    # exact native extraction multiplicity is reported; no source term may vanish.
    assert set(prior_terms) == set(new_terms), 'Native extracted source labels must stay unchanged'
    print(json.dumps({'status':'P12_BASELINE_SOURCE_PASS' if args.baseline_only else 'P12_FULL_CANONICAL_SOURCE_MANIFEST_FROZEN_TERMS_PASS',
        'base':BASE,'candidate':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'layer':'SOURCE_PURE_NOT_LOADED_BROWSER','canonical_sha256':hashlib.sha256(canonical(restored)).hexdigest(),
        'exact_prefix_and_suffix_bytes':True,'restored_optin_true_and_default_false':not args.baseline_only,
        'addon_changes':sorted(addon_changes),'icons':icons,'title_icons':len(scope[0].xpath('.//h2//*[@t-call]')),
        'native_source_terms_before':len(prior_terms),'native_source_terms_after':len(new_terms),
        'frozen':[{'file':name,'sha256':hashlib.sha256((ROOT/name).read_bytes()).hexdigest()} for name in frozen]}))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""P11 exact business-template restoration and frozen source contract (PURE)."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from lxml import etree

ROOT = Path(__file__).resolve().parents[2] if 'scripts' in Path(__file__).parts else Path.cwd()
BASE = '6d74bbe0b95fc1dbfbacd51e9d2475ee52749e36'
FILE = 'ydental_reporting/views/ydental_reporting_templates.xml'
PREFIX = 'o_ydental_reporting_source_'


def original(name):
    return subprocess.check_output(['git', 'show', BASE + ':' + name], cwd=ROOT)


def canonical(tree):
    return etree.tostring(tree, method='c14n')


def main():
    old = etree.fromstring(original(FILE))
    raw = (ROOT / FILE).read_bytes()
    new = etree.fromstring(raw)
    # Enumerate the only two permissible fixed, decorative icon calls.
    for node in list(new.iter()):
        if node.get('t-call', '').startswith('ydental_inventory.p7_icon_'):
            # P10 calls are frozen by the later full canonical comparison.
            source = node.xpath('ancestor::template[@id="ydental_operating_report_source"]')
            if source:
                assert node.get('t-call') in ('ydental_inventory.p7_icon_chevron_left',
                                             'ydental_inventory.p7_icon_arrow_right')
                node.getparent().remove(node)
    for node in list(new.iter()):
        if node.tag == 'span' and node.get('class') == PREFIX + 'action_label':
            assert node.get('t-translation') == 'on' and not len(node)
            parent = node.getparent()
            assert parent.text is None and len(parent) == 1
            parent.text = node.text
            parent.remove(node)
    # Restore exactly the original decorative separator between the two source actions.
    old_action=old.xpath("//template[@id='ydental_operating_report_source']//p[a[@t-att-href=\"row['business_url']\"]]")[0]
    new_action=new.xpath("//template[@id='ydental_operating_report_source']//p[a[@t-att-href=\"row['business_url']\"]]")[0]
    assert len(new_action)==2 and len(old_action)==2
    assert (new_action[0].tail or '').strip() in ('','·')
    new_action[0].tail=old_action[0].tail
    old_nodes, new_nodes = list(old.iter()), list(new.iter())
    assert len(old_nodes) == len(new_nodes), 'No extra business/wrapper nodes'
    for before, after in zip(old_nodes, new_nodes):
        assert before.tag == after.tag
        original_classes = before.get('class', '').split()
        classes = after.get('class', '').split()
        extra = [c for c in classes if c not in original_classes]
        assert all(c.startswith(PREFIX) for c in extra), extra
        assert [c for c in classes if c in original_classes] == original_classes
        if 'class' in before.attrib:
            after.set('class', before.get('class'))
        else:
            after.attrib.pop('class', None)
        if after.get('report_detail_actions') is not None:
            assert after.get('report_detail_actions') == 'True'
            assert after.get('t-call') in (
                'ydental_reporting.ydental_operating_report_navigation',
                'ydental_reporting.ydental_operating_report_scope')
            assert after.xpath('ancestor::template[@id="ydental_operating_report_source"]')
            del after.attrib['report_detail_actions']
        if after.get('data-dl-layout') == 'report-source-detail':
            assert after.tag == 'main' and 'o_ydental_reporting_source' in classes
            del after.attrib['data-dl-layout']
        if after.get('data-dl-actions') == 'report-source-actions':
            assert after.tag in ('a', 'summary')
            del after.attrib['data-dl-actions']
        for attribute in ('t-att-class', 't-att-data-dl-actions'):
            if 'report_detail_actions' in after.get(attribute, ''):
                expression = after.get(attribute)
                prior = before.get(attribute)
                assert prior is not None
                for main in (False, True):
                    for detail in (False, True):
                        scope = {'report_main_actions': main, 'report_detail_actions': detail}
                        actual = eval(expression, {'__builtins__': {}}, scope)
                        expected = eval(prior, {'__builtins__': {}}, scope)
                        if main or not detail:
                            assert actual == expected, 'P10/default branch changed'
                        else:
                            assert actual is not None
                            if attribute == 't-att-data-dl-actions':
                                assert actual == 'report-source-actions'
                            else:
                                assert all(c.startswith(PREFIX) or c in (expected or '').split()
                                           for c in actual.split())
                after.set(attribute, prior)
    assert canonical(old) == canonical(new), 'Business XML differs beyond enumerated P11 presentation'
    manifest = 'ydental_reporting/__manifest__.py'
    before = ast.literal_eval(original(manifest).decode())
    after = ast.literal_eval((ROOT / manifest).read_text())
    asset = 'ydental_reporting/static/src/report_source_detail/report_source_detail.scss'
    assert after['assets']['web.assets_frontend'].count(asset) == 1
    after['assets']['web.assets_frontend'].remove(asset)
    assert before == after, 'Only one local final asset is permitted'
    changed = subprocess.check_output(['git', 'diff', '--name-only', BASE], cwd=ROOT,
                                     text=True).splitlines()
    allowed = {FILE, manifest, asset}
    addon_changes = [p for p in changed if p.startswith('ydental_')]
    assert set(addon_changes) == allowed, addon_changes
    frozen = ['ydental_reporting/static/src/reporting/reporting.js',
              'ydental_reporting/static/src/reporting/reporting.scss',
              'ydental_reporting/static/src/report_filters/report_filters.js',
              'ydental_reporting/static/src/report_filters/report_filters.scss',
              'ydental_reporting/static/src/report_actions/report_actions.scss',
              'ydental_reporting/static/src/report_spacing/report_spacing.scss',
              'ydental_access/static/src/scss/_actions.scss',
              'ydental_inventory/views/ydental_inventory_templates.xml',
              'ydental_inventory/static/lib/lucide/SOURCE.json']
    for name in frozen:
        assert original(name) == (ROOT / name).read_bytes(), name
    sys.path.insert(0, str(ROOT.parent))
    from odoo.tools.translate import xml_translate
    def terms(tree):
        values = []
        xml_translate(lambda value: values.append(value) or value,
                      etree.tostring(tree, encoding='unicode'))
        return values
    assert terms(old) == terms(etree.fromstring(raw)), 'Native translation occurrences/order differ'
    print(json.dumps({'status': 'P11_FULL_CANONICAL_SOURCE_MANIFEST_FROZEN_NATIVE_TERMS_PASS',
        'base': BASE, 'candidate': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        'layer': 'SOURCE_PURE_NOT_LOADED_BROWSER', 'canonical_sha256': hashlib.sha256(canonical(new)).hexdigest(),
        'addon_changes': addon_changes, 'translation_occurrences': len(terms(old)),
        'frozen': [{'file': p, 'sha256': hashlib.sha256((ROOT / p).read_bytes()).hexdigest()} for p in frozen]}))


if __name__ == '__main__':
    main()

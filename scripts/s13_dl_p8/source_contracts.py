#!/usr/bin/env python3
"""Restore only the 25 authorized P8 presentation nodes, then compare all XML."""
import hashlib
import json
from pathlib import Path
import subprocess
from lxml import etree

ROOT = Path(__file__).resolve().parents[2]
BASE = '9f5ce4626895cb8f3da0562d9170e79220728378'
PATH = 'ydental_print/views/ydental_document_templates.xml'
raw = subprocess.check_output(['git', 'show', BASE + ':' + PATH], cwd=ROOT)
current = (ROOT / PATH).read_bytes()
old = etree.fromstring(raw)
new = etree.fromstring(current)
page = old.xpath('./template[@id="ydental_document_page"]')[0]
nodes = page.xpath('.//button | .//summary | .//a | .//h2[@id="ydental-documents-query-title" or @id="ydental-documents-originals-title"]')
counts = {tag: sum(n.tag == tag for n in nodes) for tag in ('button', 'summary', 'a', 'h2')}
assert counts == {'button': 9, 'summary': 7, 'a': 7, 'h2': 2}, counts
mapping = []
for before in nodes:
    xpath = old.getroottree().getpath(before)
    actual = new.xpath(xpath)
    assert len(actual) == 1 and actual[0].tag == before.tag, xpath
    after = actual[0]
    assert after.get('data-dl-actions') == 'documents-actions', xpath
    allowed_attributes = {'class', 'data-dl-actions'}
    assert {k: v for k, v in after.attrib.items() if k not in allowed_attributes} == {
        k: v for k, v in before.attrib.items() if k not in allowed_attributes}, xpath
    original_classes = set(before.get('class', '').split())
    classes = set(after.get('class', '').split())
    assert original_classes <= classes, xpath
    assert all(c.startswith('o_ydental_print_document_') for c in classes - original_classes), xpath
    labels = after.xpath('./span[@class="o_ydental_print_document_action_label"]')
    assert len(labels) == 1, xpath
    label = labels[0]
    assert label.attrib == {'class': 'o_ydental_print_document_action_label', 't-translation': 'on'}, xpath
    assert len(label) == 0 and label.text == before.text, xpath
    icons = []
    for child in after:
        assert child is label or child.tag == 't' and list(child.attrib) == ['t-call'] and child.get('t-call') in {
            'ydental_inventory.p7_icon_search', 'ydental_inventory.p7_icon_arrow_right',
            'ydental_inventory.p7_icon_chevron_left', 'ydental_inventory.p7_icon_chevron_right',
            'ydental_inventory.p7_icon_list'}, xpath
        if child is not label:
            icons.append(child.get('t-call'))
    assert len(icons) <= 1, xpath
    mapping.append({'tag': before.tag, 'text': before.text, 'xpath': xpath,
                    'classes': sorted(classes - original_classes), 'icons': icons})
    after.attrib.clear()
    after.attrib.update(before.attrib)
    for child in list(after):
        after.remove(child)
    after.text = before.text
    after.tail = before.tail
assert etree.tostring(new, method='c14n') == etree.tostring(old, method='c14n'), 'Any frozen XML changed outside authorized controls'
frozen = ('ydental_print/controllers', 'ydental_print/models', 'ydental_print/security',
          'ydental_print/static/src/documents_query/documents_query.js',
          'ydental_inventory/views/ydental_inventory_templates.xml',
          'ydental_inventory/static/lib/lucide')
assert not subprocess.check_output(['git', 'diff', BASE, '--name-only', '--', *frozen], cwd=ROOT).strip(), 'Frozen business/selector/icons changed'
print(json.dumps({'status': 'P8_FULL_BASELINE_XML_RESTORED_AFTER_ONLY_AUTHORIZED_PRESENTATION',
                  'baseline': BASE, 'baseline_sha256': hashlib.sha256(raw).hexdigest(),
                  'current_sha256': hashlib.sha256(current).hexdigest(), 'counts': counts,
                  'mapping': mapping, 'frozen_contracts_exact': True}, ensure_ascii=False, indent=2))

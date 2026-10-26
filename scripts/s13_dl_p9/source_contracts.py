"""Offline P9 contract restoration against the actual P8 handoff commit."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
from lxml import etree

ROOT = Path(__file__).resolve().parents[2]
BASE = '756df60286d078a4243f87c885dc7a10de1f9b8b'
PREFIX = 'o_ydental_print_spacing_'
FILES = ('ydental_print/views/ydental_document_templates.xml',
         'ydental_print/views/ydental_consent_templates.xml')

def original(name):
    return subprocess.check_output(['git', 'show', BASE + ':' + name], cwd=ROOT)

def canonical(raw, restore=False):
    tree = etree.fromstring(raw)
    if restore:
        for node in tree.iter():
            if not isinstance(node.tag, str):
                continue
            if node.get('data-dl-layout') == 'documents-spacing':
                del node.attrib['data-dl-layout']
            if 'class' in node.attrib:
                classes = [c for c in node.attrib['class'].split() if not c.startswith(PREFIX)]
                if classes:
                    node.attrib['class'] = ' '.join(classes)
                else:
                    del node.attrib['class']
    return etree.tostring(tree, method='c14n')

def main():
    results = []
    for name in FILES:
        before = canonical(original(name))
        after = canonical((ROOT / name).read_bytes(), restore=True)
        assert before == after, name + ': source/contract differs beyond spacing classes'
        results.append({'file': name, 'restored_canonical_sha256': hashlib.sha256(after).hexdigest()})
    consent = etree.parse(str(ROOT / FILES[1]))
    assert consent.xpath('count(//xpath/details[contains(@class,"spacing_inherited")])') == 3
    assert consent.find('.//xpath').get('expr') == "//details[@name='document_template_review']"
    main_tree = etree.parse(str(ROOT / FILES[0]))
    page = main_tree.find('.//main')
    assert page.get('data-dl-layout') == 'documents-spacing'
    assert not page.xpath('.//form//form')
    name = 'ydental_print/__manifest__.py'
    before = ast.literal_eval(original(name).decode())
    after = ast.literal_eval((ROOT / name).read_text())
    bundle = after['assets']['web.assets_frontend']
    new = 'ydental_print/static/src/documents_spacing/documents_spacing.scss'
    assert bundle.count(new) == 1 and bundle[-1] == new
    bundle.remove(new)
    assert before == after, 'Manifest changes exceed one final asset'
    allowed = set(FILES) | {name, new,
        'ydental_print/static/src/documents_query/documents_query.scss',
        'ydental_print/static/src/documents_header/documents_header.scss',
        'ydental_print/static/src/documents_originals/documents_originals.scss'}
    changed = subprocess.check_output(['git', 'diff', '--name-only', BASE, '--', 'ydental_*'], cwd=ROOT, text=True).splitlines()
    assert set(changed) <= allowed, changed
    print(json.dumps({'status': 'P9_SOURCE_CONTRACT_CANONICAL_EXACT', 'base': BASE,
                      'candidate': subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                      'layer': 'SOURCE_PURE_NO_RUNTIME_CLAIM', 'xml': results,
                      'product_files': changed, 'inherited_top_level_only': True}))

if __name__ == '__main__':
    main()

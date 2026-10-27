#!/usr/bin/env python3
"""Check the one authorized A04 frontend exception against the fixed P12 product.

SOURCE/PURE only. The original P12 checker and its no-product-JS assertion stay
unchanged. This checker permits one exact new frontend asset and the necessary native
resource-only head bootstrap. Removing that exact bootstrap restores all prior
XML bytes; table structure, CSS and financial code stay byte identical.
"""
import ast
import hashlib
import json
from pathlib import Path
import subprocess

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import source_contracts as p12

ROOT = Path(__file__).resolve().parents[2]
PRODUCT = 'ba3a5b0da4f3a8d2b27c3c5f84fbf533896f104f'
TOOLS = 'a161aa3f956d16eb24dc4255955202db002f5857'
JS = 'ydental_settlement/static/src/fee_focus/fee_focus.js'
MANIFEST = 'ydental_settlement/__manifest__.py'
XML = 'ydental_settlement/views/ydental_settlement_templates.xml'
BOOTSTRAP = b'''<t t-call-assets="web.assets_frontend" t-js="false"/>
            <script type="text/javascript" data-ydental-fee-focus-bootstrap="true">
                odoo.__session_info__ = <t t-out="json.dumps(env['ir.http'].get_frontend_session_info())"/>;
            </script>
            <t t-call-assets="web.assets_frontend_minimal" t-css="false" defer_load="True"/>
            <t t-call-assets="web.assets_frontend_lazy" t-css="false" lazy_load="True"/></t>'''
OLD_CSS = b'<t t-call-assets="web.assets_frontend" t-js="false"/></t>'


def source(name):
    return subprocess.check_output(['git', 'show', PRODUCT + ':' + name], cwd=ROOT)


def main():
    changed = subprocess.check_output(
        ['git', 'diff', '--name-only', PRODUCT], cwd=ROOT, text=True).splitlines()
    untracked = subprocess.check_output(
        ['git', 'ls-files', '--others', '--exclude-standard'], cwd=ROOT,
        text=True).splitlines()
    addon = sorted({name for name in changed + untracked
                    if name.startswith('ydental_')})
    assert addon == sorted([JS, MANIFEST, XML]), addon
    raw_xml = (ROOT / XML).read_bytes()
    assert raw_xml.count(BOOTSTRAP) == 1, 'Only exact native three-node asset bootstrap is authorized'
    restored_xml = raw_xml.replace(BOOTSTRAP, OLD_CSS, 1)
    assert restored_xml == source(XML), 'Full prior XML bytes must restore after the exact resource bootstrap is removed'
    body = b'<t t-call="web.layout" head="head">'
    assert raw_xml[raw_xml.index(body):] == source(XML)[source(XML).index(body):], 'Whole native body and original layout call must stay byte exact'
    before = ast.literal_eval(source(MANIFEST).decode())
    after = ast.literal_eval((ROOT / MANIFEST).read_text())
    assets = after['assets']['web.assets_frontend']
    assert assets.count(JS) == 1
    assets.remove(JS)
    assert before == after, 'Only the exact local A04 frontend registration is authorized'
    paths = subprocess.check_output(
        ['git', 'ls-tree', '-r', '--name-only', PRODUCT], cwd=ROOT,
        text=True).splitlines()
    frozen = []
    for name in paths:
        if not name.startswith('ydental_') or name in (MANIFEST, XML):
            continue
        raw = (ROOT / name).read_bytes()
        assert raw == source(name), name
        frozen.append({'file': name, 'sha256': hashlib.sha256(raw).hexdigest()})
    xml = p12.parse(restored_xml)
    old = p12.parse(p12.original(p12.FILE))
    restored, icons = p12.restore(xml, old, True)
    default, _ = p12.restore(xml, old, False)
    assert p12.canonical(restored) == p12.canonical(default)
    js = (ROOT / JS).read_text()
    assert '@web/public/interaction' in js, 'Use the locked native interaction mechanism'
    # Forbidden capabilities are source checks, not a dynamic proof. Runtime
    # evidence separately verifies native focus, local-only scroll and teardown.
    forbidden = ['preventDefault(', '.focus(', 'tabIndex =', 'tabindex=',
                 'window.scroll', 'document.documentElement.scroll', 'fetch(',
                 'XMLHttpRequest', 'keydown:', 'keyup:', 'setInterval(']
    for text in forbidden:
        assert text not in js, ('Forbidden A04 capability', text)
    print(json.dumps({
        'status': 'P12_A04_SINGLE_FRONTEND_EXCEPTION_SOURCE_PASS',
        'layer': 'SOURCE_PURE_NOT_BROWSER', 'baseline_product': PRODUCT,
        'candidate': subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'only_changed_addon_paths': addon,
        'frontend_asset': JS, 'frontend_sha256': hashlib.sha256(js.encode()).hexdigest(),
        'all_prior_addon_bytes_preserved_except_exact_bootstrap': True,
        'whole_layout_call_and_body_bytes_preserved': True,
        'resource_bootstrap_exact_removed_restores_prior_full_XML': True,
        'bootstrap_source': 'locked core web.frontend_layout native session_info + minimal defer + lazy lazy asset calls, without changing layout or wrapping body',
        'frozen_addon_file_count': len(frozen),
        'frozen_inventory_sha256': hashlib.sha256(
            json.dumps(frozen, sort_keys=True).encode()).hexdigest(),
        'original_canonical_sha256': hashlib.sha256(p12.canonical(restored)).hexdigest(),
        'original_optin_default_off_contract_restored': True,
        'original_checker_unchanged': (ROOT / 'scripts/s13_dl_p12/source_contracts.py').read_bytes()
            == subprocess.check_output(['git', 'show', TOOLS + ':scripts/s13_dl_p12/source_contracts.py'], cwd=ROOT),
        'scope': 'Only local readonly lookup fee tables; JS-off assessed separately',
    }))


if __name__ == '__main__':
    main()

"""Verify a guarded S00-B preview in a real browser and inspect downloaded PDFs.

Credentials and session data remain local. Only synthetic screenshots and PDFs
are written to the evidence directory.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

import fitz
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', required=True)
    args = parser.parse_args()
    if not re.fullmatch(r'ydental_s00b_test_[0-9]{14}_[a-f0-9]{8}', args.db):
        parser.error('Only a newly recorded S00-B test database is allowed')
    run = ROOT / '.local' / args.db
    metadata = json.loads((run / 'database.json').read_text())
    if (run.is_symlink() or metadata['database'] != args.db
            or metadata['endpoint'] != {'host': '127.0.0.1', 'port': '5432', 'user': 'odoo'}
            or metadata['cluster'] != '7694897083368259627'
            or not 18000 <= metadata['port'] <= 18999):
        parser.error('Preview creation record differs from approved isolation')
    config = run / 'odoo.conf'
    if hashlib.sha256(config.read_bytes()).hexdigest() != metadata['config_sha256']:
        parser.error('Preview configuration changed')
    pid = int((run / 'serve.pid').read_text())
    cmdline = Path('/proc/%s/cmdline' % pid).read_bytes().split(b'\0')
    if str(config).encode() not in cmdline:
        parser.error('Preview process identity differs; refusing HTTP requests')
    base = 'http://127.0.0.1:%s' % metadata['port']
    access = json.loads((run / 'access.json').read_text())
    evidence = ROOT / 'docs/evidence/s00-b'
    evidence.mkdir(exist_ok=True)
    results = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, chromium_sandbox=True)
        def context(role=None):
            result = browser.new_context(viewport={'width': 1280, 'height': 900})
            # Restrict browser navigation/assets to the exact preview origin.
            result.route('**/*', lambda route: route.continue_() if route.request.url.startswith(base + '/') else route.abort())
            if role:
                credential = access[role]
                response = result.request.post(base + '/web/session/authenticate', data={
                    'jsonrpc': '2.0', 'method': 'call', 'id': 1,
                    'params': {'db': args.db, 'login': credential['login'], 'password': credential['password']},
                })
                payload = response.json()
                info = payload['result']
                assert info['uid'] == credential['id'] and info['db'] == args.db
            return result
        for role, heading, welcome in (
            ('authorized_zh', '牙科', '欢迎使用 YDental。'),
            ('authorized_en', 'Dental', 'Welcome to YDental.'),
        ):
            ctx = context(role)
            page = ctx.new_page()
            response = page.goto(base + '/ydental')
            assert response.status == 200
            assert page.locator('h1').inner_text() == heading
            assert welcome in page.locator('main').inner_text()
            assert 'P00' not in page.locator('main').inner_text()
            assert 'YDental' in page.title()
            page.screenshot(path=str(evidence / (role + '.png')), full_page=True)
            menu = ctx.request.get(base + '/web/webclient/load_menus').json()
            dental = [m for m in menu.values() if isinstance(m, dict) and m.get('name') == heading]
            assert len(dental) == 1
            results.append({'role': role, 'entry_status': 200, 'menu_count': len(dental),
                            'heading': heading, 'title': page.title()})
            if role == 'authorized_zh':
                for paper, width, height in (('a4', 210, 297), ('narrow', 80, 200)):
                    response = ctx.request.get(base + '/ydental/sample/' + paper)
                    value = response.body()
                    assert response.status == 200 and value.startswith(b'%PDF-')
                    assert response.headers['content-type'] == 'application/pdf'
                    assert response.headers['cache-control'] == 'no-store'
                    path = evidence / ('sample-' + paper + '.pdf')
                    path.write_bytes(value)
                    doc = fitz.open(stream=value, filetype='pdf')
                    assert len(doc) == 1
                    first = doc[0]
                    assert abs(first.rect.width * 25.4 / 72 - width) < 1
                    assert abs(first.rect.height * 25.4 / 72 - height) < 1
                    text = first.get_text()
                    for expected in ('牙科合成 PDF 样张', '虚拟患者：样例一', '合成样张结束。'):
                        assert expected in text, (paper, expected)
                    assert text.count('核对中文字形与自动换行。') == 12
                    assert '\ufffd' not in text
                    blocks = [block[:4] for block in first.get_text('blocks') if block[4].strip()]
                    assert all(x0 >= 0 and y0 >= 0 and x1 <= first.rect.width and y1 <= first.rect.height
                               for x0, y0, x1, y1 in blocks)
                    fonts = [font[3] for font in first.get_fonts()]
                    assert any('NotoSansCJK' in font for font in fonts)
                    first.get_pixmap(matrix=fitz.Matrix(1.4, 1.4)).save(str(evidence / ('sample-' + paper + '.png')))
                    native = ctx.request.get(base + '/report/pdf/ydental_base.ydental_sample_' + paper)
                    assert native.status == 200 and native.body().startswith(b'%PDF-')
                    results.append({'role': role, 'paper': paper, 'custom_status': response.status,
                                    'native_status': native.status, 'bytes': len(value),
                                    'sha256': hashlib.sha256(value).hexdigest(), 'pages': len(doc),
                                    'width_mm': first.rect.width * 25.4 / 72,
                                    'height_mm': first.rect.height * 25.4 / 72,
                                    'fonts': fonts, 'all_text_blocks_inside_page': True,
                                    'chinese_lines': 12, 'extracted_text': text})
            ctx.close()
        for role in ('unauthorized', 'portal'):
            ctx = context(role)
            paths = ['/ydental'] + ['/ydental/sample/' + p for p in ('a4', 'narrow')]
            paths += ['/report/' + fmt + '/ydental_base.ydental_sample_' + p
                      for fmt in ('pdf', 'html') for p in ('a4', 'narrow')]
            for path in paths:
                response = ctx.request.get(base + path)
                assert response.status == 403
                assert not response.body().startswith(b'%PDF-')
                results.append({'role': role, 'path': path, 'status': response.status})
            page = ctx.new_page()
            page.goto(base + '/ydental')
            page.screenshot(path=str(evidence / (role + '-denied.png')), full_page=True)
            ctx.close()
        ctx = context()
        for path in ('/ydental', '/ydental/sample/a4', '/ydental/sample/narrow',
                     '/report/pdf/ydental_base.ydental_sample_a4'):
            response = ctx.request.get(base + path, max_redirects=0)
            assert response.status == 303 and '/web/login' in response.headers['location']
            results.append({'role': 'anonymous', 'path': path, 'status': response.status})
        page = ctx.new_page()
        page.goto(base + '/ydental')
        assert '/web/login' in page.url
        page.screenshot(path=str(evidence / 'anonymous-login.png'), full_page=True)
        ctx.close()
        browser.close()
    output = {'database': args.db, 'port': metadata['port'], 'browser': 'Playwright Chromium',
              'checks': results, 'count': len(results), 'exit_code': 0,
              'pdf_visual_review': 'pending human/agent image inspection'}
    (evidence / 'browser-pdf.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
    print('Browser and PDF checks:', len(results), '; exit 0')


if __name__ == '__main__':
    main()

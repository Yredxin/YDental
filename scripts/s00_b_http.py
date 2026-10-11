"""Actual HTTP and PDF checks for an identity-verified S00-B preview.

This verifier does not launch a browser. It preserves synthetic PDF artifacts
and rasterizations, and never publishes credentials, cookies or raw HTML.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import unicodedata

import pymupdf as fitz
from lxml import html
import requests


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
        parser.error('Creation record differs from approved isolation')
    config = run / 'odoo.conf'
    if hashlib.sha256(config.read_bytes()).hexdigest() != metadata['config_sha256']:
        parser.error('Runtime configuration changed')
    pid = int((run / 'serve.pid').read_text())
    if str(config).encode() not in Path('/proc/%s/cmdline' % pid).read_bytes().split(b'\0'):
        parser.error('Preview process identity differs; refusing HTTP requests')
    base = 'http://127.0.0.1:%s' % metadata['port']
    access = json.loads((run / 'access.json').read_text())
    evidence = ROOT / 'docs/evidence/s00-b'
    results = []
    def session(role=None):
        result = requests.Session()
        result.trust_env = False
        if role:
            credential = access[role]
            response = result.post(base + '/web/session/authenticate', json={
                'jsonrpc': '2.0', 'method': 'call', 'id': 1,
                'params': {'db': args.db, 'login': credential['login'], 'password': credential['password']},
            }, timeout=30)
            info = response.json()['result']
            assert info['uid'] == credential['id'] and info['db'] == args.db
        return result
    for role, heading, welcome in (
        ('authorized_zh', '牙科', '欢迎使用 YDental。'),
        ('authorized_en', 'Dental', 'Welcome to YDental.'),
    ):
        with session(role) as client:
            response = client.get(base + '/ydental', timeout=30)
            dom = html.fromstring(response.content)
            assert response.status_code == 200
            assert dom.xpath('//h1/text()') == [heading]
            assert welcome in dom.xpath('//main')[0].text_content()
            assert 'P00' not in dom.xpath('//main')[0].text_content()
            title = dom.xpath('//title/text()')[0]
            assert 'YDental' in title
            menu = client.get(base + '/web/webclient/load_menus', timeout=30).json()
            dental = [m for m in menu.values() if isinstance(m, dict) and m.get('name') == heading]
            assert len(dental) == 1
            results.append({'role': role, 'entry_status': 200, 'menu_count': len(dental),
                            'heading': heading, 'title': title})
            if role == 'authorized_zh':
                for paper, width, height in (('a4', 210, 297), ('narrow', 80, 200)):
                    response = client.get(base + '/ydental/sample/' + paper, timeout=45)
                    value = response.content
                    assert response.status_code == 200 and value.startswith(b'%PDF-')
                    assert response.headers['content-type'] == 'application/pdf'
                    assert response.headers['cache-control'] == 'no-store'
                    (evidence / ('sample-' + paper + '.pdf')).write_bytes(value)
                    doc = fitz.open(stream=value, filetype='pdf')
                    assert len(doc) == 1
                    first = doc[0]
                    assert abs(first.rect.width * 25.4 / 72 - width) < 1
                    assert abs(first.rect.height * 25.4 / 72 - height) < 1
                    raw_text = first.get_text()
                    text = unicodedata.normalize('NFKC', raw_text)
                    for expected in ('牙科合成 PDF 样张', '虚拟患者：样例一', '合成样张结束。'):
                        assert unicodedata.normalize('NFKC', expected) in text, (paper, expected)
                    assert text.count('核对中文字形与自动换行。') == 12
                    assert '\ufffd' not in text
                    blocks = [block[:4] for block in first.get_text('blocks') if block[4].strip()]
                    assert all(x0 >= 0 and y0 >= 0 and x1 <= first.rect.width and y1 <= first.rect.height
                               for x0, y0, x1, y1 in blocks)
                    fonts = [font[3] for font in first.get_fonts()]
                    assert any('NotoSansCJK' in font for font in fonts)
                    first.get_pixmap(matrix=fitz.Matrix(1.4, 1.4)).save(str(evidence / ('sample-' + paper + '.png')))
                    native = client.get(base + '/report/pdf/ydental_base.ydental_sample_' + paper, timeout=45)
                    assert native.status_code == 200 and native.content.startswith(b'%PDF-')
                    results.append({'role': role, 'paper': paper, 'custom_status': response.status_code,
                                    'native_status': native.status_code, 'bytes': len(value),
                                    'sha256': hashlib.sha256(value).hexdigest(), 'pages': len(doc),
                                    'width_mm': first.rect.width * 25.4 / 72,
                                    'height_mm': first.rect.height * 25.4 / 72,
                                    'fonts': fonts, 'all_text_blocks_inside_page': True,
                                    'chinese_lines': 12, 'extracted_text': text,
                                    'raw_extracted_text': raw_text, 'normalization': 'NFKC'})
    for role in ('unauthorized', 'portal'):
        with session(role) as client:
            paths = ['/ydental'] + ['/ydental/sample/' + p for p in ('a4', 'narrow')]
            paths += ['/report/' + fmt + '/ydental_base.ydental_sample_' + p
                      for fmt in ('pdf', 'html') for p in ('a4', 'narrow')]
            for path in paths:
                response = client.get(base + path, timeout=30)
                assert response.status_code == 403 and not response.content.startswith(b'%PDF-')
                results.append({'role': role, 'path': path, 'status': response.status_code})
    with session() as client:
        for path in ('/ydental', '/ydental/sample/a4', '/ydental/sample/narrow',
                     '/report/pdf/ydental_base.ydental_sample_a4'):
            response = client.get(base + path, allow_redirects=False, timeout=30)
            assert response.status_code == 303 and '/web/login' in response.headers['location']
            results.append({'role': 'anonymous', 'path': path, 'status': response.status_code})
    output = {'database': args.db, 'port': metadata['port'], 'client': 'requests + lxml + PyMuPDF',
              'checks': results, 'count': len(results), 'exit_code': 0,
              'browser_screenshots': 'BLOCKED: Chromium No usable sandbox; no security control disabled',
              'pdf_visual_review': 'pending image inspection'}
    (evidence / 'http-pdf.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
    print('HTTP/PDF checks:', len(results), '; exit 0; no browser claim')


if __name__ == '__main__':
    main()

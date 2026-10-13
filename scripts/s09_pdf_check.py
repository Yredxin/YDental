"""Render every examination PDF page and verify visible Chinese source labels."""
import argparse
import hashlib
import json
from pathlib import Path
import unicodedata

import pypdfium2 as pdfium


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pdf', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raw = args.pdf.read_bytes()
    assert raw.startswith(b'%PDF-') and len(raw) <= 10000000
    document = pdfium.PdfDocument(raw)
    assert 1 <= len(document) <= 20
    args.output.mkdir(parents=True, exist_ok=True)
    pages = []
    for index in range(len(document)):
        page = document[index]
        text = unicodedata.normalize('NFKC', page.get_textpage().get_text_range())
        image = args.output / f'examination-page-{index + 1:02}.png'
        page.render(scale=1.5).to_pil().save(image)
        assert len(text) > 100 and 'æ' not in text and '□' not in text
        pages.append({'page': index + 1, 'characters': len(text),
                      'text_sha256': hashlib.sha256(text.encode()).hexdigest(),
                      'image': image.name, 'image_sha256': hashlib.sha256(image.read_bytes()).hexdigest()})
    all_text = ''.join(unicodedata.normalize('NFKC', document[index].get_textpage().get_text_range())
                       for index in range(len(document)))
    for required in ('检查结果演示报告', '未审核签发', '患者编号', '来源事件', '人工结论', '已确认'):
        assert required in all_text, required
    result = {'result': 'PASS', 'pdf_sha256': hashlib.sha256(raw).hexdigest(),
              'pdf_bytes': len(raw), 'page_count': len(document), 'pages': pages,
              'manual_visual_review': 'REQUIRED'}
    (args.output / 'pdf-check.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()

"""Prepare process-local S00-B PDF assets without installing system packages."""
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.request


ROOT = Path(__file__).resolve().parents[1] / '.local/s00-b-deps'
ASSETS = (
    ('downloads/wkhtmltox.deb',
     'https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-2/wkhtmltox_0.12.6.1-2.jammy_amd64.deb',
     'ee88d74834bdec650f7432c7d3ef1c981e42ae7a762a75a01f7f5da59abc18d5'),
    ('fonts/NotoSansCJKsc-Regular.otf',
     'https://raw.githubusercontent.com/notofonts/noto-cjk/Sans2.004/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf',
     '2c76254f6fc379fddfce0a7e84fb5385bb135d3e399294f6eeb6680d0365b74b'),
)


def main():
    records = []
    for relative, url, expected in ASSETS:
        target = ROOT / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            with urllib.request.urlopen(url, timeout=60) as response:
                value = response.read()
            if hashlib.sha256(value).hexdigest() != expected:
                raise RuntimeError('Downloaded asset SHA256 mismatch: ' + relative)
            with target.open('xb') as output:
                output.write(value)
        if hashlib.sha256(target.read_bytes()).hexdigest() != expected:
            raise RuntimeError('Existing asset SHA256 mismatch; file preserved: ' + relative)
        records.append({'url': url, 'path': relative, 'sha256': expected})
    binary = ROOT / 'wkhtmltox/usr/local/bin/wkhtmltopdf'
    if not binary.exists():
        subprocess.run(['dpkg-deb', '-x', str(ROOT / ASSETS[0][0]), str(ROOT / 'wkhtmltox')], check=True)
    subprocess.run([str(binary), '--version'], check=True)
    font_config = '''<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">
<fontconfig><dir>%s</dir><cachedir>%s</cachedir></fontconfig>
''' % (ROOT / 'fonts', ROOT / 'cache')
    config = ROOT / 'fonts.conf'
    if config.exists() and config.read_text() != font_config:
        raise RuntimeError('Existing local font configuration differs; preserved')
    if not config.exists():
        config.write_text(font_config)
    (ROOT / 'asset-manifest.json').write_text(json.dumps(records, indent=2) + '\n')
    print('Process-local assets ready under', ROOT)


if __name__ == '__main__':
    main()

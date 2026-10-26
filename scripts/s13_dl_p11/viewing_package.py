#!/usr/bin/env python3
"""Construct an exclusive private P11 viewing ZIP from explicit original images.

No network, database, configuration, source, request or business original is
included. An independent reader must verify every source/image/member/privacy.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import zipfile

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
PRIVATE = ROOT / '.local/dl-p11'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selection', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    selection_path = ROOT / args.selection
    selection = json.loads(selection_path.read_text())
    output = ROOT / args.output
    assert PRIVATE in output.resolve().parents and output.suffix == '.zip'
    assert not output.exists()
    members = {}
    manifest = {'plan_id': 'YD-S13-DL-P11 / 1.0', 'layer': 'VIEW_ONLY_ORIGINAL_BROWSER_IMAGES',
                'user_hand_effect': 'PENDING', 'members': [], 'independent_review': 'PENDING'}
    for item in selection['images']:
        source = ROOT / item['source']
        assert PRIVATE in source.resolve().parents and source.suffix == '.png' and not source.is_symlink()
        raw = source.read_bytes()
        with Image.open(io.BytesIO(raw)) as image:
            image.verify()
        with Image.open(io.BytesIO(raw)) as image:
            width, height = image.size
        name = item['member']
        assert name.endswith('.png') and '..' not in Path(name).parts and not Path(name).is_absolute()
        assert name not in members
        members[name] = raw
        manifest['members'].append({'path': name, 'source': str(source.relative_to(ROOT)),
            'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
            'width': width, 'height': height, 'pixels_edited': False,
            'layer': item['layer'], 'stage': item['stage'], 'engine': item['engine'],
            'description': item['description']})
    readme = selection['readme'].encode()
    members['README.txt'] = readme
    manifest['members'].append({'path': 'README.txt', 'bytes': len(readme),
        'sha256': hashlib.sha256(readme).hexdigest()})
    raw = json.dumps(manifest, ensure_ascii=False, indent=2).encode()
    members['manifest.json'] = raw
    members['SHA256SUMS.txt'] = ''.join(hashlib.sha256(v).hexdigest()+'  '+k+'\n'
        for k, v in members.items()).encode()
    output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(output, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            for name, value in members.items():
                archive.writestr(name, value)
    output.chmod(0o400)
    raw = output.read_bytes()
    print(json.dumps({'status': 'CONSTRUCTED_INDEPENDENT_REVIEW_PENDING',
        'file': str(output.relative_to(ROOT)), 'bytes': len(raw),
        'sha256': hashlib.sha256(raw).hexdigest(), 'members': len(members),
        'pngs': len(selection['images'])}))


if __name__ == '__main__':
    main()

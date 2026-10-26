#!/usr/bin/env python3
"""Construct an exclusive private P12 viewing ZIP from explicit original images.

No network, database, configuration, source, request or business original is
included. An independent reader must verify every source/image/member/privacy.
"""
import argparse
import hashlib
import io
import json
import os
import re
from pathlib import Path
import zipfile

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
PRIVATE = ROOT / '.local/dl-p12'


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
    manifest = {'plan_id': 'YD-S13-DL-P12 / 1.0', 'layer': 'VIEW_ONLY_ORIGINAL_BROWSER_IMAGES',
                'user_hand_effect': 'PENDING', 'members': [], 'independent_review': 'PENDING'}
    for item in selection['images']:
        assert re.fullmatch(r'[0-9a-f]{40}', item['candidate'])
        assert set(item['actor']) == {'alias', 'uid'} and item['actor'] == {'alias': 'settlement', 'uid': 14}
        assert set(item['viewport']) <= {'width', 'height', 'rootFont', 'dpr', 'scrollX', 'scrollY', 'rootClient', 'rootScroll'}
        assert {'width', 'height', 'rootFont', 'dpr', 'scrollX', 'scrollY'} <= set(item['viewport'])
        scene = item['scenario']
        allowed_scenarios = {
            'ACTUAL_SETTLEMENT_LOOKUP': {'kind', 'selected_patient_id', 'search_contract'},
            'ACTUAL_OTHER_STORE_MINIMAL_SUMMARY': {'kind', 'selected_patient_id', 'no_store_switch'},
            'LOADED_QWEB_MEMORY_COMPONENT': {'kind', 'fixture_file', 'fixture_sha256', 'ordinary_actor_is_browser_context_only_not_fixture_authorization'},
        }
        assert set(scene) == allowed_scenarios[scene['kind']]
        if scene['kind'] == 'ACTUAL_SETTLEMENT_LOOKUP':
            assert scene['search_contract'] == 'q_candidates_only_explicit_patient_id_selection'
        if scene['kind'] == 'ACTUAL_OTHER_STORE_MINIMAL_SUMMARY':
            assert scene['no_store_switch'] is True
        source_result = ROOT / item['source_result']
        assert PRIVATE in source_result.resolve().parents and not source_result.is_symlink()
        result_raw = source_result.read_bytes()
        assert hashlib.sha256(result_raw).hexdigest() == item['source_result_sha256']
        original_result = json.loads(result_raw)
        original_shot = next(x for x in original_result['screenshots'] if x['file'] == item['source'])
        assert original_result['actor'] == item['actor'] and original_shot['candidate'] == item['candidate']
        assert {key: original_shot['viewport'][key] for key in item['viewport']} == item['viewport']
        source = ROOT / item['source']
        assert PRIVATE in source.resolve().parents and source.suffix == '.png' and not source.is_symlink()
        raw = source.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == original_shot['sha256'] and len(raw) == original_shot['bytes']
        assert original_shot['image_pixels_edited'] is False
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
            'actual_capture_candidate': item['candidate'], 'actor': item['actor'],
            'viewport': item['viewport'], 'scenario': item['scenario'],
            'original_client_status': item['client_status'],
            'source_result': item['source_result'], 'source_result_sha256': item['source_result_sha256'],
            'layer': item['layer'], 'stage': item['stage'], 'engine': item['engine'],
            'description': item['description']})
    assert re.fullmatch(r'[0-9a-f]{40}', selection['product_candidate'])
    manifest['final_product_candidate'] = selection['product_candidate']
    measurements = json.dumps(selection['measurements'], ensure_ascii=False, indent=2).encode()
    members['measurements.json'] = measurements
    manifest['members'].append({'path': 'measurements.json', 'bytes': len(measurements),
        'sha256': hashlib.sha256(measurements).hexdigest()})
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

#!/usr/bin/env python3
"""Compare bounded P9 browser evidence, separating permitted layout movement.

Reads only explicitly named local result artifacts. Never makes requests or
normalizes business values. The sole preview clock exception requires exactly
one known UTC text field and byte-identical surrounding source.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write_new(p, value):
    raw = json.dumps(value, indent=2, ensure_ascii=False).encode()
    fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
    return hashlib.sha256(raw).hexdigest()


def preview_equal(before, after):
    a, b = copy.deepcopy(before), copy.deepcopy(after)
    clocks = []
    assert len(a['iframe']) == len(b['iframe'])
    for left, right in zip(a['iframe'], b['iframe']):
        x, y = left.pop('srcdoc'), right.pop('srcdoc')
        assert left == right, 'Frozen iframe attributes changed'
        if x == y:
            clocks.append({'source_bytes_exact': True})
            continue
        pattern = r'(?<=<span>实际生成与提取时间（UTC）：</span> )\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?=;</span>)'
        old, new = list(re.finditer(pattern, x)), list(re.finditer(pattern, y))
        assert len(old) == len(new) == 1, 'Only one exact native extraction UTC field permitted'
        ox, ny = old[0], new[0]
        assert x[:ox.start()] == y[:ny.start()] and x[ox.end():] == y[ny.end():], 'Preview changed beyond exact UTC extraction field'
        clocks.append({'source_bytes_exact': False, 'exact_field': 'actual extraction UTC', 'before': ox.group(), 'after': ny.group(), 'prefix_bytes_exact': True, 'suffix_bytes_exact': True, 'before_sha256': hashlib.sha256(x.encode()).hexdigest(), 'after_sha256': hashlib.sha256(y.encode()).hexdigest()})
    assert a == b, 'Preview business/form/row projection changed'
    return clocks


def without_width(value):
    if isinstance(value, dict):
        return {k: without_width(v) for k, v in value.items() if k != 'width'}
    if isinstance(value, list):
        return [without_width(v) for v in value]
    return value


def compare(before_file, after_file):
    before, after = json.loads(before_file.read_text()), json.loads(after_file.read_text())
    assert before['engine'] == after['engine'], 'Same actual engine required'
    assert before['actor'] == after['actor']
    checks = []
    for key in ['initial', 'page1', 'page2']:
        assert before[key] == after[key], key+' full semantic projection changed'
        checks.append(key+'_full_semantics_exact')
    clocks = preview_equal(before['preview_projection'], after['preview_projection'])
    checks.append('preview_full_semantics_exact_except_one_classified_native_UTC')
    for key in ['unaffected_initial', 'unaffected_preview']:
        left, right = copy.deepcopy(before[key]), copy.deepcopy(after[key])
        if key == 'unaffected_preview':
            for sample, full in ((left, before['preview_projection']), (right, after['preview_projection'])):
                assert len(sample['iframe']) == len(full['iframe'])
                for frame, source in zip(sample['iframe'], full['iframe']):
                    assert all(source[k] == v for k, v in frame.items())
            for frame in left['iframe'] + right['iframe']:
                frame.pop('srcdoc')  # Exact source classification already passed above.
        assert without_width(left) == without_width(right), key+' frozen control internals changed'
        checks.append(key+'_frozen_style_and_contracts_exact_except_allowed_width')
    layout = []
    for view in ['1366x768', '1440x900', '768x1024', '390x844', '320x800', 'post-preview']:
        a, b = [json.loads((p.parent / ('controls-'+view+'.json')).read_text()) for p in [before_file, after_file]]
        assert a['inherited'] == b['inherited'], view+' inherited descendants changed'
        strips = lambda items: [{k:v for k,v in x.items() if k != 'rect'} for x in items]
        assert strips(a['targets']) == strips(b['targets']), view+' P8 internal styles/labels changed'
        old, new = a['rootBounds'], b['rootBounds']
        assert new['scroll']-new['client'] <= old['scroll']-old['client']+1, view+' new root overflow'
        layout.append({'view':view,'before_root':old,'after_root':new,'target_rect_change_count':sum(x['rect'] != y['rect'] for x,y in zip(a['targets'],b['targets'])),'target_style_count':len(a['targets']),'inherited_blocks':len(a['inherited'])})
    return {'status':'P9_SAME_ENGINE_BEFORE_AFTER_CONTRACTS_FROZEN_INTERNALS_INHERITED_AND_NO_NEW_ROOT_SPILL_PASS','before_sha256':digest(before_file),'after_sha256':digest(after_file),'engine':after['engine'],'actor':after['actor'],'checks':checks,'native_preview_clock_classification':clocks,'allowed_layout_changes':layout,'business_values_normalized':False,'screenshots_independently_reviewed':False}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--before',type=Path,required=True);p.add_argument('--after',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=compare(a.before,a.after);sha=write_new(a.output,result);print(json.dumps({'status':result['status'],'sha256':sha}));return 0

if __name__=='__main__':raise SystemExit(main())

"""Capture the six financial after views with controlled client object lifetime.

This is a normal read-only browser helper. The caller must record its real
process exit independently; a saved manifest never proves native exit zero.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import urlencode

from admission_probe import PRIVATE, ROOT, write_receipt
from http_client import BASE, ROLE_PROVIDER, owned_service, private_json
import browser_client as browser
from browser_ux import visit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--label', required=True)
    args = parser.parse_args()
    if not args.label or len(args.label) > 60 or any(char not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for char in args.label):
        raise RuntimeError('Use a fresh bounded explicit label.')
    output = PRIVATE / 'verification' / ('paired-financial-' + args.label)
    output.mkdir(mode=0o700, parents=True)
    result = {'status': 'INCOMPLETE', 'client_pid': os.getpid(), 'client_parent_pid': os.getppid(),
        'tool_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'service': owned_service(args.run_id), 'same_before_filters': {
            'date_from': '2026-10-23', 'date_to': '2026-10-24', 'store_ids': '1', 'currency_id': '1'},
        'pairs': [], 'economic_business_submitted': False, 'user_hand_verified': False,
        'visual_review': 'PENDING_INDEPENDENT', 'manifest_is_not_process_exit_proof': True}
    write_receipt(output / 'intent.json', result)
    account = private_json(ROLE_PROVIDER)['users']['settlement']
    sync_playwright = browser.import_browser()
    result['browser_environment'] = browser.loaded_browser_environment_facts()
    client = context = page = observer = None
    try:
        with sync_playwright() as playwright:
            client = playwright.chromium.launch(headless=True, executable_path=str(browser.CHROMIUM))
            try:
                context = client.new_context(locale='zh-CN', timezone_id='UTC', viewport={'width': 1366, 'height': 768})
                observer = browser.Observer(context)
                page = context.new_page()
                result['login'] = browser.login(page, account, account['id'])
                result['store'] = browser.switch_store(page, 1)
                for width, height in ((1366, 768), (1440, 900)):
                    page.set_viewport_size({'width': width, 'height': height})
                    for metric in ('collections', 'refunds', 'receivables'):
                        before = PRIVATE / 'verification/before' / f'settlement-{metric}-{width}x{height}.png'
                        if not before.is_file():
                            raise RuntimeError('The exact earlier screenshot is unavailable; do not fabricate a comparison.')
                        item = visit(page, '/ydental/reports?' + urlencode(dict(metric=metric, **result['same_before_filters'])),
                                     output, f'{metric}-{width}x{height}')
                        if item['status'] != 200 or not item['root_no_overflow'] or not item['no_clipped_container']:
                            raise RuntimeError('A real financial view failed its status or width assertion.')
                        item.update(metric=metric, viewport={'width': width, 'height': height},
                            before_image=str(before.relative_to(ROOT)), before_sha256=hashlib.sha256(before.read_bytes()).hexdigest())
                        result['pairs'].append(item)
            finally:
                try:
                    if context is not None:
                        context.close()
                finally:
                    client.close()
        result['api_context_exit_complete'] = True
        result['status'] = 'SAME_FILTER_VIEWPORT_PAIRS_CAPTURED_REQUIRES_REAL_EXIT_READBACK'
        code = 0
    except Exception as error:
        result.update(status='BROWSER_PAIR_CAPTURE_FAILED_NO_REPLAY', error_class=type(error).__name__)
        code = 2
    finally:
        # Release proxy references while Python is running. This narrows object
        # lifetime; it does not establish the old native fault's cause or cure.
        account = page = observer = context = client = sync_playwright = None
    digest = write_receipt(output / 'result.json', result)
    print(json.dumps({'status': result['status'], 'pairs': len(result['pairs']),
        'sha256': digest, 'output': str((output / 'result.json').relative_to(ROOT))}))
    return code


if __name__ == '__main__':
    raise SystemExit(main())

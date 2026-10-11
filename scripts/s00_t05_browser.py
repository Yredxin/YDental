"""Check Project #4 UI access with a normal private Firefox profile.

No CLI token, browser cookie export/import, login bypass or security override.
An optional desktop login opens the regular GitHub page for the user to sign in.
The user closes that browser after login; this script never reads credentials.
"""
import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from urllib.parse import quote, urlsplit

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / '.local/s00-t05/github-firefox-profile'
EVIDENCE = ROOT / 'docs/evidence/s00-t05'
URL = 'https://github.com/users/Yredxin/projects/4/workflows'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--interactive-login', action='store_true')
    args = parser.parse_args()
    if PROFILE.is_symlink():
        raise RuntimeError('Profile symlink refused')
    PROFILE.mkdir(parents=True, exist_ok=True, mode=0o700)
    if PROFILE.stat().st_mode & 0o077:
        raise RuntimeError('Private profile permissions required')
    if args.interactive_login and not (os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')):
        raise RuntimeError('Interactive login needs a user desktop display')
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    result = {'scope': 'S00-T05 normal browser authentication probe', 'requested_url': URL,
              'started_utc': datetime.now(timezone.utc).isoformat(), 'browser_type': 'firefox',
              'playwright_version': version('playwright'), 'viewport': {'width': 1280, 'height': 900},
              'code_commit': subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'], text=True).strip(),
              'authentication': 'normal persistent browser profile; no imported credentials or cookies',
              'project_mutations': 0}
    with sync_playwright() as p:
        ctx = p.firefox.launch_persistent_context(str(PROFILE), headless=not args.interactive_login,
                                                   viewport=result['viewport'], timeout=30000)
        result['browser_version'] = ctx.browser.version
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        response = page.goto(URL, wait_until='domcontentloaded', timeout=60000)
        page.wait_for_load_state('load', timeout=60000)
        meta = page.locator('meta[name=user-login]')
        logged_in = bool(meta.count() and meta.get_attribute('content'))
        result['project_page'] = {'http_status': response.status,
                                  'url': urlsplit(page.url)._replace(query='',fragment='').geturl(),
                                  'title': page.title(), 'normal_browser_authenticated': logged_in}
        if args.interactive_login:
            if not logged_in:
                page.goto('https://github.com/login?return_to=' + quote(URL, safe=''))
            print('Regular GitHub login window opened. Complete login/2FA, then close the browser.', flush=True)
            # GUI remains under user control; no form values or cookies are read.
            while ctx.pages:
                try:
                    page.wait_for_timeout(500)
                except Exception:
                    break
            ctx.close()
            return 0
        result['status'] = 'PASS' if logged_in and response.status == 200 else 'BLOCKED'
        result['reason'] = ('Authenticated UI available; workflow details still require explicit inspection'
                            if result['status'] == 'PASS' else 'Normal browser GitHub login/2FA required')
        if not logged_in:
            login_response = page.goto('https://github.com/login?return_to=' + quote(URL, safe=''),
                                       wait_until='load', timeout=60000)
            result['login_page'] = {'http_status': login_response.status, 'url': 'https://github.com/login',
                                    'title': page.title(), 'login_field_present': page.locator('input[name=login]').count()>0,
                                    'password_field_present': page.locator('input[name=password]').count()>0}
            for selector in ('input[name=login]', 'input[name=password]'):
                locator = page.locator(selector)
                if locator.count() and locator.input_value():
                    raise RuntimeError('Populated credential form; screenshot refused')
            body = page.locator('body').inner_text()
            if re.search(r'(?i)(?:session_id|csrf_token|authorization|token)\s*[:=]', body):
                raise RuntimeError('Sensitive text; screenshot refused')
            image = EVIDENCE / 'project-workflows-login-required.png'
            page.screenshot(path=str(image), full_page=True)
            result.update(screenshot=str(image.relative_to(ROOT)), screenshot_sha256=hashlib.sha256(image.read_bytes()).hexdigest())
        ctx.close()
    result.update(finished_utc=datetime.now(timezone.utc).isoformat(), exit_code=0 if result['status']=='PASS' else 2)
    (EVIDENCE/'browser-access.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('Project browser access:',result['status'],'; exit',result['exit_code'])
    return result['exit_code']


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as error:
        print('Browser access probe stopped safely:',type(error).__name__)
        sys.exit(2)

"""Bounded, credential-free Firefox blank-page diagnostic for MAIN-A.

The worker never imports an Odoo client or reads a credential/session provider.
Only this diagnostic worker receives DEBUG=pw:browser. The authenticated browser
adapter keeps its existing environment whitelist.
"""
import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
PLAYWRIGHT_ROOT = ROOT / '.local/s00-b-deps/verify-lib'
FIREFOX = ROOT / '.local/s00-b-deps/browsers/firefox-1543/firefox/firefox'


def diagnostic_admitted(worker_passed, outcome, process_facts):
    """Unknown or failed parent/browser exit never grants authenticated UI."""
    return (worker_passed is True and outcome.get('returncode') == 0
            and outcome.get('timed_out') is False and outcome.get('native_crash') is False
            and bool(process_facts) and all(item.get('currently_exists') is False
                and item.get('debug_exit_code') == '0' and item.get('debug_exit_signal') == 'null'
                for item in process_facts))


def parse_browser_debug(debug):
    """Parse the actual Playwright producer's closing ``>`` delimiter."""
    pids = sorted({int(value) for value in re.findall(r'(?:\[pid=|<launched> pid=)([0-9]+)', debug)})
    facts = []
    for pid in pids:
        exited = re.findall(r'\[pid=%d\].*?process did exit: exitCode=([^,>]+), signal=([^\s\x1b>]+)' % pid, debug)
        facts.append({'pid': pid, 'debug_exit_code': exited[-1][0] if exited else 'UNKNOWN',
                      'debug_exit_signal': exited[-1][1] if exited else 'UNKNOWN'})
    return facts


def diagnostic_driver_environment(ambient):
    """Consume the existing supervisor's Python-only flag before its driver."""
    from s10_lc2_browser import _DRIVER_ENV_KEYS
    if ambient.get('PYTHONFAULTHANDLER') != '1':
        raise RuntimeError('DIAGNOSTIC_SUPERVISOR_ENVIRONMENT_INVALID')
    child = {key: value for key, value in ambient.items() if key != 'PYTHONFAULTHANDLER'}
    if set(child) - (_DRIVER_ENV_KEYS | {'DEBUG'}) or child.get('DEBUG') != 'pw:browser':
        raise RuntimeError('DIAGNOSTIC_ENVIRONMENT_INVALID')
    return child


def pairing_metadata():
    import configparser
    parser = configparser.ConfigParser()
    parser.read(FIREFOX.parent / 'application.ini')
    browsers = json.loads((PLAYWRIGHT_ROOT / 'playwright/driver/package/browsers.json').read_bytes())
    required = next(item for item in browsers['browsers'] if item['name'] == 'firefox')
    metadata = list(PLAYWRIGHT_ROOT.glob('playwright-*.dist-info/METADATA'))
    versions = [line.split(': ', 1)[1] for path in metadata for line in path.read_text().splitlines()
                if line.startswith('Version: ')]
    value = {'playwright_versions': versions, 'required_firefox_revision': required['revision'],
             'required_firefox_version': required['browserVersion'],
             'selected_firefox_revision': FIREFOX.parents[1].name.removeprefix('firefox-'),
             'selected_firefox_version': parser['App']['Version'],
             'selected_firefox_build_id': parser['App']['BuildID'],
             'executable': str(FIREFOX.relative_to(ROOT)),
             'browsers_metadata_sha256': hashlib.sha256((PLAYWRIGHT_ROOT / 'playwright/driver/package/browsers.json').read_bytes()).hexdigest()}
    value['pairing_matches'] = (value['selected_firefox_revision'] == value['required_firefox_revision']
                                and value['selected_firefox_version'] == value['required_firefox_version'])
    return value


async def blank_page_worker(directory):
    # The parent supplies a clean diagnostic-only environment. No provider or
    # application session path enters this process or the browser context.
    from s10_lc2_evidence import save_once
    from s10_lc2_browser import firefox_environment
    clean = diagnostic_driver_environment(dict(os.environ))
    os.environ.clear()
    os.environ.update(clean)
    sys.path.insert(0, str(PLAYWRIGHT_ROOT))
    from playwright.async_api import async_playwright
    result = {'credential_provider_read': False, 'application_url_requested': False,
              'network_requests': 0, 'blank_page_pass': False, 'browser_returned': False,
              'context_created': False, 'driver_stop_returned': False,
              'supervisor_python_flag_removed_before_driver': True}
    driver = browser = context = None
    started = time.monotonic()
    try:
        driver = await async_playwright().start()
        browser = await driver.firefox.launch(executable_path=str(FIREFOX), headless=True,
                                              env=firefox_environment(dict(os.environ), FIREFOX, diagnostic=True),
                                              timeout=60000)
        result['browser_returned'] = True
        result['reported_browser_version'] = browser.version
        context = await browser.new_context()
        result['context_created'] = True

        async def deny_network(route):
            result['network_requests'] += 1
            await route.abort('blockedbyclient')

        await context.route('**/*', deny_network)
        page = await context.new_page()
        await page.goto('about:blank', timeout=10000)
        result['blank_page_pass'] = await page.evaluate('document.URL === "about:blank"')
    except BaseException as error:
        # This worker has never received a secret. Retain bounded launch text,
        # which the authenticated adapter deliberately cannot export.
        text = str(error)[:16384]
        text = re.sub(r'(/tmp/[^\s]+)', '[temporary-path]', text)
        result.update(exception_type=type(error).__name__, launch_error_text=text)
    finally:
        cleanup_errors = []
        for stage, instance, method, timeout in (
                ('context.close', context, 'close', 5),
                ('browser.close', browser, 'close', 5),
                ('driver.stop', driver, 'stop', 10)):
            if instance is None:
                continue
            try:
                await asyncio.wait_for(getattr(instance, method)(), timeout)
                if stage == 'driver.stop':
                    result['driver_stop_returned'] = True
            except BaseException as secondary:
                cleanup_errors.append({'stage': stage, 'exception_type': type(secondary).__name__})
        result['cleanup_errors'] = cleanup_errors
        result['diagnostic_pass'] = (result['blank_page_pass'] and not cleanup_errors
                                     and result['driver_stop_returned'] and result['network_requests'] == 0
                                     and 'exception_type' not in result)
        result['elapsed_seconds'] = round(time.monotonic() - started, 3)
        save_once(directory / 'blank-page-result.json', result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker', type=Path)
    parser.add_argument('--attempt', type=int, choices=(1, 2))
    args = parser.parse_args()
    if args.worker is not None:
        expected = ROOT / '.local/s10-lc2-main-a-20261018-03'
        if args.worker.parent != expected or not re.fullmatch(r'browser-diagnostic-[12]', args.worker.name):
            raise RuntimeError('DIAGNOSTIC_WORKER_DIRECTORY_INVALID')
        result = asyncio.run(blank_page_worker(args.worker))
        print(json.dumps({'blank_page_pass': result['blank_page_pass'], 'no_credentials': True}))
        return
    if args.attempt is None:
        parser.error('--attempt is required')
    from s10_lc2_task_profile import main_a_engineering_profile
    from s10_lc2_targets import PackageBudget
    from s10_lc2_evidence import runtime_gate, save_once
    from s10_lc2_supervisor import launch
    from s10_lc2_browser import _DRIVER_ENV_KEYS
    profile = main_a_engineering_profile()
    approval = profile.root / 'runtime-approval.json'
    authority = json.loads(approval.read_bytes())
    runtime_gate(approval, product_commit=authority['product_commit'], test_commit=authority['test_commit'], profile=profile)
    directory = profile.root / ('browser-diagnostic-%d' % args.attempt)
    directory.mkdir(mode=0o700)
    pairing = pairing_metadata()
    save_once(directory / 'pairing.json', pairing)
    if not pairing['pairing_matches']:
        raise RuntimeError('FIREFOX_PAIRING_MISMATCH_NO_LAUNCH')
    clean = {key: value for key, value in os.environ.items() if key in _DRIVER_ENV_KEYS}
    clean['DEBUG'] = 'pw:browser'
    PackageBudget(profile.root, profile=profile).consume('firefox', firefox_purpose='diagnostic')
    outcome = launch([sys.executable, str(Path(__file__).resolve()), '--worker', str(directory)],
                     directory / 'process', env=clean, cwd=ROOT, timeout=80, attempt=args.attempt)
    save_once(directory / 'parent-result.json', outcome)
    result_path = directory / 'blank-page-result.json'
    # DEBUG belongs only to this credential-free child, so its PID/exit lines
    # may be observed without reading any existing browser or provider state.
    debug = (directory / 'process/stderr-faulthandler.log').read_text(errors='replace')
    parsed = parse_browser_debug(debug)
    process_facts = []
    for parsed_fact in parsed:
        pid = parsed_fact['pid']
        try:
            os.kill(pid, 0)
            currently_exists = True
            try:
                executable_matches = Path(os.readlink('/proc/%d/exe' % pid)).resolve() == FIREFOX.resolve()
            except (OSError, PermissionError):
                executable_matches = 'UNKNOWN'
        except ProcessLookupError:
            currently_exists, executable_matches = False, False
        process_facts.append(parsed_fact | {
            'currently_exists': currently_exists, 'selected_executable_matches_if_alive': executable_matches})
    save_once(directory / 'browser-process-observations.json', {'browser_processes': process_facts,
        'browser_pid_available': bool(parsed), 'global_process_kill': False,
        'observation': 'CURRENT_CREDENTIAL_FREE_ATTEMPT_DEBUG_AND_EXACT_PID_ONLY'})
    native_signals = {'SIGILL', 'SIGABRT', 'SIGBUS', 'SIGFPE', 'SIGSEGV', '4', '6', '7', '8', '11'}
    native = outcome.get('native_crash') is True or any(item['debug_exit_signal'] in native_signals for item in process_facts)
    worker_passed = result_path.exists() and json.loads(result_path.read_bytes()).get('diagnostic_pass') is True
    passed = diagnostic_admitted(worker_passed, outcome, process_facts)
    save_once(directory / 'diagnostic-final-result.json', {'diagnostic_pass': passed,
        'blank_page_pass': worker_passed, 'firefox_native_crash_observed': native,
        'browser_pid_observed': bool(process_facts), 'owned_browser_pids_currently_gone': not any(item['currently_exists'] for item in process_facts),
        'worker_returncode': outcome['returncode'], 'worker_timed_out': outcome.get('timed_out'),
        'credential_provider_read': False,
        'application_or_business_network_requested': False})
    print(json.dumps({'diagnostic_attempt': args.attempt, 'blank_page_pass': passed,
                      'parent_returncode': outcome['returncode'], 'directory': str(directory.relative_to(ROOT))}))


if __name__ == '__main__':
    main()

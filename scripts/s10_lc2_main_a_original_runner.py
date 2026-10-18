"""MAIN-A original-only normal Firefox login and existing workbench download.

No clinical actor, editor method, credential reset or dynamic PDF entrypoint is
imported or dispatched. A saved download prevents another business click.
"""
import asyncio
import json
import os
from pathlib import Path
import stat
import uuid

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_SHA = '05928780e7d97a06cf29019634f64b010eb4994c2f1c5032d561008a50b059b4'


def existing_reader5():
    directory = ROOT / '.local/s10-lc2-main-a-20261018-02/credentials'
    path = directory / 'user-5.json'
    if (directory.is_symlink() or path.is_symlink()
            or stat.S_IMODE(directory.stat().st_mode) != 0o700
            or stat.S_IMODE(path.stat().st_mode) != 0o600):
        raise RuntimeError('READER_PROVIDER_MODE_INVALID')
    value = json.loads(path.read_bytes())
    if set(value) != {'user_id', 'login', 'password'} or value['user_id'] != 5:
        raise RuntimeError('READER_PROVIDER_IDENTITY_INVALID')
    return value


def already_downloaded(directory):
    return any(directory.glob('browser-ui-*/binary-artifacts/*.stored-original.pdf'))


async def original_ui(budget, directory):
    from s10_lc2_browser import Credentials, run_main_a_browser
    value = existing_reader5()
    credential = Credentials(value['login'], value['password'])
    del value
    return await run_main_a_browser(base_url='http://127.0.0.1:18410',
        database=budget.profile.database, owned_targets={budget.profile.database: 'http://127.0.0.1:18410'},
        budget=budget, directory=directory, credentials=credential, store_id=1,
        invoice_id=1, original_id=1, original_sha256=ORIGINAL_SHA, patient_id=1)


def main():
    from s10_lc2_task_profile import main_a_original_ui_profile
    from s10_lc2_launch import OwnedApplication
    from s10_lc2_browser import _DRIVER_ENV_KEYS
    from s10_lc2_evidence import save_once
    profile = main_a_original_ui_profile()
    directory = profile.root
    if already_downloaded(directory):
        raise RuntimeError('DOWNLOAD_ALREADY_SAVED_POSTPROCESS_ONLY_NO_RECLICK')
    before = json.loads((directory / 'original-before.json').read_bytes())
    if before.get('original_reader5_eligible') is not True or before.get('editor_released') is not True:
        raise RuntimeError('ORIGINAL_BEFORE_PRECONDITION_INVALID')
    approval = directory / 'runtime-approval.json'
    authority = json.loads(approval.read_bytes())
    marker = json.loads((profile.run_root / profile.database / 'database.json').read_bytes())
    attempt = uuid.uuid4().hex[:8]
    try:
        with OwnedApplication(marker, approval=approval, product_commit=authority['product_commit'],
                test_commit=authority['test_commit'], action='main-service', profile=profile) as app:
            app.start([])
            app.wait_ready(60)
            ambient = dict(os.environ)
            clean = {key: value for key, value in ambient.items() if key in _DRIVER_ENV_KEYS}
            try:
                os.environ.clear()
                os.environ.update(clean)
                result = asyncio.run(original_ui(app.budget, directory / ('browser-ui-' + attempt)))
                save_once(directory / ('original-ui-' + attempt + '-result.json'), result)
            finally:
                os.environ.clear()
                os.environ.update(ambient)
            app.check()
            application_directory = app.directory
        save_once(directory / ('runner-' + attempt + '-result.json'), {
            'status': 'DOWNLOAD_RETURNED_INDEPENDENT_RO_AND_PDF_REVIEW_PENDING',
            'application_directory': str(application_directory.relative_to(ROOT)),
            'credential_actor': 5, 'clinical_operations': 0})
        print(json.dumps({'status': 'DOWNLOAD_RETURNED_RO_AND_VISUAL_PENDING', 'actor_id': 5}))
    except BaseException as error:
        save_once(directory / ('runner-' + attempt + '-failure.json'), {
            'exception_type': type(error).__name__, 'raw_error_text_retained': False,
            'download_artifact_already_saved': already_downloaded(directory),
            'clinical_operations': 0, 'next_action': 'INSPECT_SAVED_EVIDENCE_BEFORE_RETRY'})
        print(json.dumps({'status': 'FAILED_STOP', 'exception_type': type(error).__name__,
                          'download_saved': already_downloaded(directory)}))
        raise SystemExit(1) from None


if __name__ == '__main__':
    main()

"""One authorized closeout window; failure never dispatches another business action."""
import json
import os
import subprocess
import sys
import s10_closeout_v1_contract as c
from s10_closeout_v1_control import create, run_native, source_final
from s10_closeout_v1_web import main as web_main


def main():
    os.umask(0o077)
    c.gate(business=True)
    assert not (c.PRIVATE / 'window-intent.json').exists(), 'WINDOW_ALREADY_ATTEMPTED'
    c.save(c.PRIVATE / 'window-intent.json', {'single_attempt': True, 'authority': c.AUTH})
    result = {'status': 'BLOCKED', 'no_automatic_retry': True}
    try:
        create()
        assert run_native('prepare-all') == 0
        web_main()
        result['status'] = 'A_B_C_D_E_RUN_COMPLETED_PENDING_TAIL_AND_VISUAL'
    except BaseException as error:
        result.update(error_type=type(error).__name__, error_sha256=c.sha(str(error).encode()))
        c.stop('CLOSEOUT_WINDOW_STOP:' + type(error).__name__)
    finally:
        if (c.RUN / 'database.json').exists():
            try: c.readonly('final-tail', full=True)
            except BaseException as error:
                c.stop('FINAL_TAIL_INCOMPLETE:' + type(error).__name__)
                result['final_tail_error'] = type(error).__name__
        if (c.PRIVATE / 'source-before-RO.json').exists():
            try: source_final()
            except BaseException as error:
                c.stop('SOURCE_FINAL_INCOMPLETE:' + type(error).__name__)
                result['source_final_error'] = type(error).__name__
        c.save(c.OUT / 'window-result.json', result)
    print(json.dumps(result))
    return 1 if (c.PRIVATE / 'STOP.json').exists() else 0


if __name__ == '__main__':
    sys.exit(main())

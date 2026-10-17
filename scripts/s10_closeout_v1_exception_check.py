"""Offline tests of the actual observer: primary failures survive unsafe snapshots."""
import os
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import s10_closeout_v1_contract as c
import s10_closeout_v1_runtime as r


def main():
    results = []
    os.environ['YDENTAL_CLOSEOUT_ACTION'] = 'STATIC-exception'
    for scenario in ['business_call', 'actor_flush', 'before_snapshot', 'after_snapshot']:
        primary = RuntimeError('PRIMARY_' + scenario)
        secondary = AssertionError('DIRTY_NO_UID1_FLUSH')
        order = []
        count = 0
        def snap(env):
            nonlocal count
            count += 1
            order.append('snapshot')
            if scenario == 'before_snapshot' or (scenario == 'after_snapshot' and count > 1):
                raise primary
            if count > 1: raise secondary
            return {'before': True}
        def call():
            order.append('business')
            if scenario == 'business_call': raise primary
            return 7
        def flush():
            order.append('actor_flush')
            if scenario == 'actor_flush': raise primary
        real_save = c.save
        def save(path, value):
            if str(path).endswith('-primary-exception.json'): order.append('primary_saved')
            real_save(path, value)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.multiple(c, ROOT=root, PRIVATE=root/'private', OUT=root/'public'), patch.object(c, 'save', save), patch.object(r, 'snapshot', snap):
                try: r.observe(None, scenario, call, lambda *args: True, actor_env=SimpleNamespace(flush_all=flush))
                except BaseException as actual: assert actual is primary
                else: raise AssertionError('PRIMARY_NOT_RERAISED')
                path = next(path for path in (root/'private').glob('*-primary-exception.json')
                            if not path.name.endswith('-secondary-primary-exception.json'))
                assert c.read(path)['message'] == str(primary)
                if scenario in {'business_call', 'actor_flush'}:
                    assert order.index('primary_saved') < len(order)-1
                    assert 'snapshot' in order[order.index('primary_saved')+1:]
                if scenario == 'before_snapshot': assert 'business' not in order
        results.append({'scenario': scenario, 'primary_identity_preserved': True, 'order': order})
    c.save(c.OUT/'R1-exception-path-regression.json', {'pure_files_only': True, 'exit_code': 0, 'results': results,
        'unsafe_snapshot_unavailable_not_flushed': True, 'real_observe_implementation_executed': True})
    print('EXCEPTION_PATHS_PASS; DB_ODOO_HTTP=0')


if __name__ == '__main__': main()

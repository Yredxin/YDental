"""Parse the exact R3 Odoo command with the locked core, without starting Odoo."""

from contextlib import redirect_stderr
import hashlib
import io
import json
import os
from pathlib import Path
import socket
import sys

from s10_ui1_r2_evidence import write_once
import s10_ui1_r3_control as control


def blocked(*_args, **_kwargs):
    raise RuntimeError('CLI-only guard: database, socket, or service startup attempted')


def audit(event, _args):
    if event in ('socket.connect', 'socket.bind', 'subprocess.Popen'):
        blocked()


def parse(mode, config_path):
    assert mode in ('legacy_invalid', 'upgrade', 'http')
    config_path = Path(config_path).resolve(strict=True)
    argv = control.argv(mode, config_path)
    assert argv[:2] == [str(control.PYTHON), str(control.CORE / 'odoo-bin')]
    sys.addaudithook(audit)
    socket.socket.connect = blocked
    socket.socket.bind = blocked
    import psycopg2
    psycopg2.connect = blocked
    sys.path.insert(0, str(control.CORE))
    from odoo.tools.config import configmanager
    manager = configmanager()
    try:
        with redirect_stderr(io.StringIO()):
            manager._parse_config(argv[2:])
    except SystemExit as error:
        if mode == 'legacy_invalid' and error.code == 2:
            return {'status': 'CLI_PARSE_EXPECTED_REJECT', 'mode': mode,
                    'exit_code': 2, 'argv': argv,
                    'config_sha256': control.digest(config_path),
                    'reason': 'unregistered --test-disable'}
        raise
    if mode == 'legacy_invalid':
        raise AssertionError('Locked Odoo parser unexpectedly accepted --test-disable')
    opts = {name: manager[name] for name in (
        'db_name', 'init', 'update', 'http_enable', 'stop_after_init',
        'addons_path', 'data_dir', 'dbfilter', 'http_interface', 'http_port',
        'test_enable', 'test_tags', 'test_file')}
    assert opts['db_name'] == [control.NAME], opts['db_name']
    assert opts['init'] == {}
    assert opts['update'] == ({'ydental_settlement': True} if mode == 'upgrade' else {})
    assert opts['http_enable'] is (mode == 'http')
    assert opts['stop_after_init'] is (mode == 'upgrade')
    assert opts['addons_path'] == [str(x) for x in
        (control.CORE / 'odoo/addons', control.CORE / 'addons', control.ROOT)]
    assert opts['data_dir'] == str(control.RUN / 'data')
    assert opts['dbfilter'] == '^' + control.NAME + '$'
    assert opts['http_interface'] == '127.0.0.1' and opts['http_port'] == control.PORT
    assert opts['test_enable'] is False and not opts['test_tags'] and not opts['test_file']
    return {'status': 'CLI_PARSE_PASS', 'mode': mode, 'argv': argv,
            'config_sha256': control.digest(config_path), 'options': opts,
            'guard': 'NO_DB_NO_SOCKET_NO_SERVICE'}


def main():
    if len(sys.argv) != 4:
        raise ValueError('Use mode config_path evidence_path')
    mode, config_path, out = sys.argv[1:]
    proof = parse(mode, config_path)
    write_once(out, proof)
    print(json.dumps({'status': proof['status'], 'mode': mode,
                      'config_sha256': proof['config_sha256'],
                      'argv_sha256': hashlib.sha256(json.dumps(proof['argv']).encode()).hexdigest(),
                      'options': proof.get('options')}, ensure_ascii=False))


if __name__ == '__main__':
    main()

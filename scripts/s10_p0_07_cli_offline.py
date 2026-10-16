"""Parse the exact P0-07 HTTP command with the installed Odoo20 CLI parser."""

import configparser
import json
from pathlib import Path
import sys
import tempfile

from s10_p0_07_control import BROWSER_ARGV, HTTP_ARGV
from s10_p0_07_snapshot import CORE, PORT, ROOT, TARGET, TARGET_RUN

sys.path.insert(0, str(CORE))
from odoo.tools.config import configmanager


def main():
    assert len(HTTP_ARGV) == 4 and HTTP_ARGV[2:] == ('-c', str(TARGET_RUN / 'odoo.conf'))
    with tempfile.TemporaryDirectory(prefix='s10-p007-cli-') as dirname:
        conf = Path(dirname) / 'odoo.conf'
        data = Path(dirname) / 'data'; data.mkdir()
        opts = configparser.ConfigParser(interpolation=None)
        opts['options'] = {'db_host': '127.0.0.1', 'db_port': '5432', 'db_user': 'odoo',
            'db_password': 'SIMULATED_NO_CONNECTION', 'db_name': TARGET,
            'dbfilter': '^' + TARGET + '$',
            'addons_path': ','.join(str(p) for p in (CORE / 'odoo/addons', CORE / 'addons', ROOT)),
            'data_dir': str(data), 'http_interface': '127.0.0.1', 'http_port': str(PORT),
            'list_db': 'False', 'workers': '0', 'max_cron_threads': '0',
            'smtp_server': '127.0.0.1', 'smtp_port': '1'}
        with conf.open('w') as stream: opts.write(stream)
        argv = [str(conf) if x == str(TARGET_RUN / 'odoo.conf') else x for x in HTTP_ARGV]
        parsed = configmanager()
        parsed.parse_config(argv[2:], setup_logging=False)
        assert parsed['db_name'] == [TARGET] and parsed['dbfilter'] == '^' + TARGET + '$'
        assert parsed['data_dir'] == str(data) and parsed['http_port'] == PORT
        assert parsed['http_interface'] == '127.0.0.1'
        assert parsed['max_cron_threads'] == parsed['workers'] == 0
        assert not parsed['init'] and not parsed['update'] and not parsed['test_enable']
        assert not parsed['test_tags'] and not parsed['test_file']
        assert not parsed['stop_after_init'] and parsed['http_enable']
    assert BROWSER_ARGV[-1].endswith('scripts/s10_p0_07_browser.py')
    print(json.dumps({'status': 'REAL_CLI_PARSER_PASS', 'http_argv': HTTP_ARGV,
                      'browser_argv': BROWSER_ARGV, 'update': False, 'init': False,
                      'test': False, 'cron': 0, 'workers': 0, 'port': PORT}))


if __name__ == '__main__':
    main()

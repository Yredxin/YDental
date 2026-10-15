"""Parse W3's final Odoo argv with the locked core, without a registry or socket."""

import configparser
import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from odoo.cli.command import find_command
from odoo.tools.config import configmanager

from s10_e2e_w3_control import CORE, NAME, PORT, ROOT


def main():
    assert find_command('shell') is not None
    with tempfile.TemporaryDirectory(prefix='s10-w3-cli-') as tmp:
        path = Path(tmp) / 'odoo.conf'
        data_dir = Path(tmp) / 'data'
        data_dir.mkdir()
        cfg = configparser.ConfigParser(interpolation=None)
        cfg['options'] = {
            'db_host':'127.0.0.1', 'db_port':'5432', 'db_user':'odoo',
            'db_password':'SIMULATED_NO_CONNECTION', 'db_name':NAME,
            'dbfilter':'^' + NAME + '$',
            'addons_path':','.join(str(x) for x in (CORE / 'odoo/addons', CORE / 'addons', ROOT)),
            'data_dir':str(data_dir), 'http_interface':'127.0.0.1',
            'http_port':str(PORT), 'list_db':'False', 'workers':'0',
            'max_cron_threads':'0', 'smtp_server':'127.0.0.1', 'smtp_port':'1'}
        with path.open('w') as stream: cfg.write(stream)
        result = {}
        for mode, argv in (
            ('prepare_shell', ['-c',str(path),'--no-http']),
            ('http', ['-c',str(path)])):
            options = configmanager()
            options.parse_config(argv, setup_logging=False)
            assert options['db_name'] == [NAME]
            assert options['dbfilter'] == '^' + NAME + '$'
            assert options['data_dir'] == str(data_dir)
            assert options['http_port'] == PORT
            assert options['http_enable'] is (mode == 'http')
            assert not options['init'] and not options['update']
            assert options['stop_after_init'] is False
            assert options['test_enable'] is False
            assert not options['test_tags'] and not options['test_file']
            assert options['max_cron_threads'] == 0
            result[mode] = {'argv':argv, 'db_name':options['db_name'],
                            'http_enable':options['http_enable'], 'update':options['update'],
                            'init':options['init'], 'test_enable':options['test_enable']}
        print(json.dumps({'status':'REAL_ODOO_PARSER_PASS','commands':result}))


if __name__ == '__main__': main()

"""Parse the exact W5 HTTP argv with the real Odoo 20 CLI."""

import configparser
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT.parent
sys.path.insert(0, str(CORE))
from odoo.tools.config import configmanager

from s10_e2e_w5_control import HTTP_ARGV
from s10_e2e_w5_snapshot import NAME, PORT


def main():
    assert HTTP_ARGV[:2] == (str(CORE / '.venv/bin/python'), str(CORE / 'odoo-bin'))
    with tempfile.TemporaryDirectory(prefix='s10-w5-cli-') as folder:
        config = Path(folder) / 'odoo.conf'
        data = Path(folder) / 'data'; data.mkdir()
        options = configparser.ConfigParser(interpolation=None)
        options['options'] = {'db_host':'127.0.0.1','db_port':'5432','db_user':'odoo',
            'db_password':'SIMULATED_NO_CONNECTION','db_name':NAME,'dbfilter':'^'+NAME+'$',
            'addons_path':','.join(str(path) for path in (CORE/'odoo/addons',CORE/'addons',ROOT)),
            'data_dir':str(data),'http_interface':'127.0.0.1','http_port':str(PORT),
            'list_db':'False','workers':'0','max_cron_threads':'0',
            'smtp_server':'127.0.0.1','smtp_port':'1'}
        with config.open('w') as stream: options.write(stream)
        result = {}
        for label, argv in (('http',HTTP_ARGV),):
            simulated = [str(config) if value == str(ROOT/'.local'/NAME/'odoo.conf') else value
                         for value in argv]
            parsed = configmanager()
            parsed.parse_config(simulated[2:], setup_logging=False)
            assert parsed['db_name'] == [NAME] and parsed['dbfilter'] == '^'+NAME+'$'
            assert parsed['data_dir'] == str(data) and parsed['http_port'] == PORT
            assert parsed['max_cron_threads'] == 0 and not parsed['init']
            assert parsed['test_enable'] is False and not parsed['test_tags'] and not parsed['test_file']
            assert not parsed['update'] and parsed['stop_after_init'] is False
            assert parsed['http_enable'] is True and parsed['workers'] == 0
            result[label] = {'argv':list(argv),'update':parsed['update'],
                'stop_after_init':parsed['stop_after_init'],'http_enable':parsed['http_enable'],
                'test_enable':parsed['test_enable'],'db_name':parsed['db_name']}
        print(json.dumps({'status':'REAL_ODOO20_CLI_PASS','commands':result}))


if __name__ == '__main__':
    main()

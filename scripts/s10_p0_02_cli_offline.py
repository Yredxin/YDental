"""Use the installed Odoo 20 parser on the exact planned argv, without a DB."""

import configparser
import json
from pathlib import Path
import sys
import tempfile

from s10_p0_02_control import BROWSER_ARGV, HTTP_ARGV, UPGRADE_ARGV
from s10_p0_02_snapshot import CORE, PORT, ROOT, TARGET, TARGET_RUN

sys.path.insert(0,str(CORE))
from odoo.tools.config import configmanager


def main():
    assert UPGRADE_ARGV[-4:] == ('-u','ydental_settlement','--stop-after-init','--no-http')
    assert HTTP_ARGV == UPGRADE_ARGV[:-4]
    with tempfile.TemporaryDirectory(prefix='s10-p002-cli-') as dirname:
        conf = Path(dirname)/'odoo.conf'
        data = Path(dirname)/'data'; data.mkdir()
        opts = configparser.ConfigParser(interpolation=None)
        opts['options'] = {'db_host':'127.0.0.1','db_port':'5432','db_user':'odoo',
            'db_password':'SIMULATED_NO_CONNECTION','db_name':TARGET,'dbfilter':'^'+TARGET+'$',
            'addons_path':','.join(str(p) for p in (CORE/'odoo/addons',CORE/'addons',ROOT)),
            'data_dir':str(data),'http_interface':'127.0.0.1','http_port':str(PORT),
            'list_db':'False','workers':'0','max_cron_threads':'0','smtp_server':'127.0.0.1',
            'smtp_port':'1'}
        with conf.open('w') as stream: opts.write(stream)
        output = {}
        for kind,argv in (('upgrade',UPGRADE_ARGV),('http',HTTP_ARGV)):
            simulated = [str(conf) if arg == str(TARGET_RUN/'odoo.conf') else arg
                         for arg in argv]
            parsed = configmanager()
            parsed.parse_config(simulated[2:],setup_logging=False)
            assert parsed['db_name'] == [TARGET] and parsed['dbfilter'] == '^'+TARGET+'$'
            assert parsed['data_dir'] == str(data) and parsed['http_port'] == PORT
            assert parsed['max_cron_threads'] == 0 and parsed['workers'] == 0
            assert not parsed['init'] and not parsed['test_enable']
            assert not parsed['test_tags'] and not parsed['test_file']
            if kind=='upgrade':
                assert parsed['update'] == {'ydental_settlement':True}
                assert parsed['stop_after_init'] and not parsed['http_enable']
            else:
                assert not parsed['update'] and not parsed['stop_after_init']
                assert parsed['http_enable']
            output[kind] = {'argv':argv,'update':parsed['update'],
                'http_enable':parsed['http_enable'],'max_cron_threads':parsed['max_cron_threads'],
                'stop_after_init':parsed['stop_after_init']}
    assert BROWSER_ARGV[-1].endswith('scripts/s10_p0_02_browser.py')
    print(json.dumps({'status':'REAL_CLI_PARSER_PASS','commands':output},default=list))


if __name__=='__main__':
    main()

"""Negative isolation checks; no database connection or service change."""
from pathlib import Path
import subprocess
import tempfile
import unittest
import os


ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT.parent / '.venv/bin/python'


class TestIsolationGuard(unittest.TestCase):
    def run_guard(self, *args):
        return subprocess.run([str(PYTHON), str(ROOT / 'scripts/s08c.py'), *args], capture_output=True, text=True)

    def test_reject_business_and_historical_databases(self):
        for name in ('odoo20_dev', 'ydental_s00b_test_20261011073303_8137af81', 'ydental_s08c_test_fake'):
            result = self.run_guard('upgrade', '--db', name)
            self.assertEqual(result.returncode, 2)
            self.assertIn('Database must be a new', result.stderr)

    def test_reject_service_port(self):
        result = self.run_guard('upgrade', '--db', 'ydental_s08c_test_20261011000000_01234567', '--port', '8069')
        self.assertEqual(result.returncode, 2)
        self.assertIn('isolated range', result.stderr)

    def test_reject_wrong_endpoint_before_connection(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / 'config'
            config.write_text('[options]\ndb_host=192.0.2.1\ndb_port=5432\ndb_user=odoo\n')
            result = self.run_guard('upgrade', '--db', 'ydental_s08c_test_20261011000000_01234567', '--config', str(config))
        self.assertEqual(result.returncode, 2)
        self.assertIn('no connection attempted', result.stderr)

    def test_process_egress_blocks_external_resolution(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, 'sitecustomize.py').write_text((ROOT / 'scripts/s08c_network_policy.py').read_text())
            result = subprocess.run([str(PYTHON), '-c', "import socket; socket.getaddrinfo('example.invalid',443)"],
                                    capture_output=True, text=True, env=dict(os.environ, PYTHONPATH=directory))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('external name resolution denied', result.stderr)

    def test_process_egress_blocks_other_loopback_services(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, 'sitecustomize.py').write_text((ROOT / 'scripts/s08c_network_policy.py').read_text())
            result = subprocess.run([str(PYTHON), '-c', "import socket; socket.socket().connect(('127.0.0.1',8069))"],
                                    capture_output=True, text=True, env=dict(os.environ, PYTHONPATH=directory))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('process egress denied', result.stderr)


if __name__ == '__main__':
    unittest.main()

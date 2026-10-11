"""Negative isolation checks; no database connection or service change."""
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT.parent / '.venv/bin/python'


class TestIsolationGuard(unittest.TestCase):
    def run_guard(self, *args):
        return subprocess.run([str(PYTHON), str(ROOT / 'scripts/s01.py'), *args], capture_output=True, text=True)

    def test_reject_business_and_historical_databases(self):
        for name in ('odoo20_dev', 'ydental_s00b_test_20261011073303_8137af81', 'ydental_s01_test_fake'):
            result = self.run_guard('upgrade', '--db', name)
            self.assertEqual(result.returncode, 2)
            self.assertIn('Database must be a new', result.stderr)

    def test_reject_service_port(self):
        result = self.run_guard('upgrade', '--db', 'ydental_s01_test_20261011000000_01234567', '--port', '8069')
        self.assertEqual(result.returncode, 2)
        self.assertIn('isolated range', result.stderr)

    def test_reject_wrong_endpoint_before_connection(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / 'config'
            config.write_text('[options]\ndb_host=192.0.2.1\ndb_port=5432\ndb_user=odoo\n')
            result = self.run_guard('upgrade', '--db', 'ydental_s01_test_20261011000000_01234567', '--config', str(config))
        self.assertEqual(result.returncode, 2)
        self.assertIn('no connection attempted', result.stderr)


if __name__ == '__main__':
    unittest.main()

"""Offline child-interpreter dependency probe; never imports Odoo or opens a DB."""
import importlib
import importlib.metadata
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
DEPENDENCIES = ROOT / '.local/s04-deps'


def probe():
    expected_path = os.pathsep.join([str(ROOT / 'scripts'), str(DEPENDENCIES)])
    if Path.cwd() != ROOT or os.environ.get('PYTHONPATH') != expected_path:
        raise RuntimeError('DEPENDENCY_PROBE_CWD_OR_CONTROLLED_PATH_DRIFT')
    if not DEPENDENCIES.is_dir() or DEPENDENCIES.is_symlink():
        raise RuntimeError('EXISTING_DEPENDENCY_DIRECTORY_UNAVAILABLE')
    versions = []
    for distribution, module_name in [('phonenumbers', 'phonenumbers'), ('psycopg2-binary', 'psycopg2'),
                                      ('Pillow', 'PIL'), ('Werkzeug', 'werkzeug'), ('lxml', 'lxml')]:
        try:
            info = importlib.metadata.distribution(distribution)
        except importlib.metadata.PackageNotFoundError:
            if distribution != 'psycopg2-binary':
                raise
            info = importlib.metadata.distribution('psycopg2')
        module = importlib.import_module(module_name)
        path = Path(module.__file__).resolve()
        if not (path.is_relative_to(DEPENDENCIES) or path.is_relative_to(ROOT.parent / '.venv')):
            raise RuntimeError('DEPENDENCY_IMPORT_SOURCE_OUTSIDE_EXISTING_APPROVED_ROOTS')
        version = info.version
        if module_name == 'phonenumbers' and (version != '9.0.16' or module.__version__ != version
                                              or not path.is_relative_to(DEPENDENCIES)):
            raise RuntimeError('EXISTING_PHONENUMBERS_IDENTITY_DRIFT')
        versions.append({'distribution': info.metadata['Name'], 'version': version,
                         'module': module_name, 'import_file': str(path),
                         'metadata_root': str(Path(info.locate_file('')).resolve())})
    return {'cwd': str(ROOT), 'python_executable': sys.executable, 'python_version': sys.version.split()[0],
            'controlled_pythonpath': expected_path, 'dependencies': versions,
            'odoo_imported': any(name == 'odoo' or name.startswith('odoo.') for name in sys.modules),
            'database_connection_performed': False}


if __name__ == '__main__':
    print(json.dumps(probe(), sort_keys=True))

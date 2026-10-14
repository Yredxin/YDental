"""Offline execution of the exact, unmodified AST body of queue._settings."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'ydental_queue/models/ydental_queue_service.py'
HEARTBEAT = 'ydental_queue.heartbeat_seconds'
TIMEOUT = 'ydental_queue.timeout_seconds'

class UserError(Exception):
    pass

class Params:
    def __init__(self, values):
        self.values = values
        self.reads = []
    def sudo(self):
        return self
    def get_str(self, key, default=''):
        assert key in (HEARTBEAT, TIMEOUT)
        self.reads.append(key)
        return self.values.get(key, default)

class Env:
    def __init__(self, values):
        self.params = Params(values)
    def __getitem__(self, key):
        assert key == 'ir.config_parameter'
        return self.params
    def _(self, message):
        return message

class Service:
    def __init__(self, values):
        self.env = Env(values)

source = SOURCE.read_text()
tree = ast.parse(source)
methods = [node for cls in tree.body if isinstance(cls, ast.ClassDef)
           for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == '_settings']
assert len(methods) == 1
method = methods[0]
assert ast.get_source_segment(source, method).count("get_str('ydental_queue.") == 2
namespace = {'UserError': UserError}
exec(compile(ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[])), str(SOURCE), 'exec'), namespace)
Service._settings = namespace['_settings']

positive = [(2, 20), (2, 600), (1, 86400)]
negative = [
    ('missing_both', {}),
    ('missing_heartbeat', {TIMEOUT: '20'}),
    ('missing_timeout', {HEARTBEAT: '2'}),
    ('empty_heartbeat', {HEARTBEAT: '', TIMEOUT: '20'}),
    ('empty_timeout', {HEARTBEAT: '2', TIMEOUT: ''}),
    ('nonnumeric_heartbeat', {HEARTBEAT: 'two', TIMEOUT: '20'}),
    ('nonnumeric_timeout', {HEARTBEAT: '2', TIMEOUT: 'twenty'}),
    ('zero_heartbeat', {HEARTBEAT: '0', TIMEOUT: '20'}),
    ('negative_heartbeat', {HEARTBEAT: '-1', TIMEOUT: '20'}),
    ('equal', {HEARTBEAT: '20', TIMEOUT: '20'}),
    ('timeout_lower', {HEARTBEAT: '21', TIMEOUT: '20'}),
    ('timeout_over_max', {HEARTBEAT: '2', TIMEOUT: '86401'}),
]
for heartbeat, timeout in positive:
    service = Service({HEARTBEAT: str(heartbeat), TIMEOUT: str(timeout)})
    assert service._settings() == (heartbeat, timeout)
    assert service.env.params.reads == [HEARTBEAT, TIMEOUT]
for label, values in negative:
    service = Service(values)
    try:
        service._settings()
    except UserError as error:
        assert str(error).startswith('configuration_required:'), (label, str(error))
    else:
        raise AssertionError('original _settings accepted ' + label)
print(json.dumps({'mode':'SIMULATED_ACTUAL_AST_BODY', 'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'first_line':method.lineno,'last_line':method.end_lineno,'positive':len(positive),'negative':len(negative),
    'positive_values':positive,'negative_labels':[x[0] for x in negative], 'odoo_processes':0,'pg_writes':0}))

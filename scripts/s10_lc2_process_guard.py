"""Small fail-closed diagnostic consumer; never starts a process or application."""
import hashlib
import os
from pathlib import Path
import stat

from s10_lc2_logging import MAX_LINE, OPTIONAL_TYPES, REQUIRED, strict_loads


class ObservationBlocked(RuntimeError):
    """A fixed code only; the original event remains in the producer's log."""


class ProcessEvents:
    def __init__(self, pid, run_id):
        self.pid = pid
        self.run_id = run_id
        self.sequence = 0
        self.started = False
        self.ended = False
        self.failure = None
        self.seen = set()

    def fail(self, code, event=None):
        if self.failure is None:
            row = event or {}
            self.failure = {'reason': code, 'event_id': row.get('event_id'),
                            'root_event_id': row.get('root_event_id')}
        raise ObservationBlocked(self.failure['reason'])

    def consume(self, row):
        if self.failure:
            self.fail(self.failure['reason'])
        if type(row) is not dict:
            self.fail('DIAGNOSTIC_RECORD_INVALID')
        fields = REQUIRED | OPTIONAL_TYPES
        if any((key not in row or type(row[key]) is not expected) for key, expected in REQUIRED.items()):
            self.fail('DIAGNOSTIC_RECORD_INVALID')
        if any(row.get(key) is not None and type(row[key]) is not expected for key, expected in fields.items()):
            self.fail('DIAGNOSTIC_RECORD_INVALID')
        if row.get('outcome') is not None and type(row['outcome']) is not str:
            self.fail('DIAGNOSTIC_RECORD_INVALID')
        if (row['schema_version'] != '1.0' or row['pid'] != self.pid or row.get('run_id') != self.run_id
                or row['process_seq'] != self.sequence + 1 or self.ended):
            self.fail('DIAGNOSTIC_SEQUENCE_OR_IDENTITY_DRIFT')
        if row['event_id'] in self.seen or len(self.seen) >= 100000:
            self.fail('DIAGNOSTIC_EVENT_REPLAY_OR_COUNT_BOUND')
        if not self.started and row['event'] != 'run.start':
            self.fail('DIAGNOSTIC_START_MISSING')
        if self.started and row['event'] == 'run.start':
            self.fail('DIAGNOSTIC_START_REPEATED')
        self.started = True
        self.sequence = row['process_seq']
        self.seen.add(row['event_id'])
        for field in ('renderer_pid', 'renderer_exit_code', 'renderer_signal'):
            if row.get(field) is not None and row[field] < 0:
                self.fail('DIAGNOSTIC_RENDERER_FIELD_INVALID', row)
        if row.get('renderer_signal', 0):
            self.fail('RENDERER_SIGNAL_HARD_STOP', row)
        if row.get('event') == 'renderer.error' or (row['event'] == 'renderer.exit' and row.get('outcome') == 'UNKNOWN'):
            self.fail('RENDERER_RESULT_UNKNOWN', row)
        if row.get('renderer_exit_code', 0):
            self.fail('RENDERER_NONZERO_REQUIRES_VERIFICATION', row)
        if row.get('outcome') in {'REAP_FAILED', 'NATIVE_CRASH'}:
            self.fail('RENDERER_RECOVERY_UNCONFIRMED', row)
        if row.get('event') == 'renderer.cleanup_failed' or row.get('error_class') == 'EVIDENCE_ERROR':
            self.fail('DIAGNOSTIC_EVIDENCE_UNAVAILABLE', row)
        self.ended = row['event'] == 'run.end'


class ProcessLogGuard:
    """Incremental bounded reads of one owned PID; retained segments never vanish."""
    def __init__(self, directory, pid, run_id):
        self.directory = Path(directory)
        self.state = ProcessEvents(pid, run_id)
        self.files = {}

    def verify_seal(self, path, segment):
        try:
            with os.fdopen(os.open(str(path) + '.seal', os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), 'rb') as stream:
                if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                    self.state.fail('DIAGNOSTIC_SEAL_INVALID')
                raw = stream.read(1025)
            if len(raw) > 1024:
                self.state.fail('DIAGNOSTIC_SEAL_INVALID')
            seal = strict_loads(raw)
            with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), 'rb') as stream:
                if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                    self.state.fail('DIAGNOSTIC_LOG_UNREADABLE')
                contents = stream.read(10 * 1024 * 1024 + 1)
            if (type(seal) is not dict or set(seal) != {'file', 'bytes', 'sha256', 'segment'}
                    or type(seal['bytes']) is not int or type(seal['segment']) is not int
                    or seal['file'] != path.name or seal['segment'] != segment
                    or seal['bytes'] != len(contents) or len(contents) > 10 * 1024 * 1024
                    or seal['sha256'] != hashlib.sha256(contents).hexdigest()):
                self.state.fail('DIAGNOSTIC_SEAL_MISMATCH')
        except (OSError, ValueError, UnicodeError):
            self.state.fail('DIAGNOSTIC_SEAL_MISSING_OR_INVALID')

    def observe(self, *, allow_starting=False, final=False):
        if self.state.failure:
            self.state.fail(self.state.failure['reason'])
        paths = sorted(self.directory.glob('events-%s-*.jsonl' % self.state.pid))
        if not paths:
            if allow_starting and not self.state.started and not self.files:
                return False
            self.state.fail('DIAGNOSTIC_LOG_MISSING')
        if len(paths) > 5 or not set(self.files) <= {p.name for p in paths}:
            self.state.fail('DIAGNOSTIC_SEGMENT_MISSING_OR_BOUND')
        prefixes = {p.name.rsplit('-', 1)[0] for p in paths}
        if len(prefixes) != 1 or any(p.name.rsplit('-', 1)[1] != '%03d.jsonl' % i for i, p in enumerate(paths)):
            self.state.fail('DIAGNOSTIC_SEGMENT_ORDER_INVALID')
        try:
            for segment, path in enumerate(paths):
                with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), 'rb') as stream:
                    info = os.fstat(stream.fileno())
                    previous = self.files.get(path.name)
                    identity = (info.st_dev, info.st_ino)
                    offset = previous[1] if previous else 0
                    if (not stat.S_ISREG(info.st_mode) or info.st_size > 10 * 1024 * 1024
                            or previous and (previous[0] != identity or info.st_size < offset)):
                        self.state.fail('DIAGNOSTIC_LOG_REPLACED_OR_TRUNCATED')
                    stream.seek(offset)
                    remaining = info.st_size - offset
                    while remaining:
                        raw = stream.readline(min(MAX_LINE + 1, remaining))
                        if not raw:
                            self.state.fail('DIAGNOSTIC_LOG_CHANGED_DURING_READ')
                        remaining -= len(raw)
                        if len(raw) > MAX_LINE or not raw.endswith(b'\n'):
                            self.state.fail('DIAGNOSTIC_LOG_PARTIAL_OR_OVERSIZE')
                        try:
                            row = strict_loads(raw.decode('utf-8'))
                        except (ValueError, UnicodeError):
                            self.state.fail('DIAGNOSTIC_JSON_INVALID')
                        self.state.consume(row)
                    self.files[path.name] = (identity, stream.tell())
                if final or segment < len(paths) - 1:
                    self.verify_seal(path, segment)
        except OSError:
            self.state.fail('DIAGNOSTIC_LOG_UNREADABLE')
        if final and not self.state.ended:
            self.state.fail('DIAGNOSTIC_END_MISSING')
        if not self.state.started:
            if allow_starting:
                return False
            self.state.fail('DIAGNOSTIC_START_MISSING')
        return True

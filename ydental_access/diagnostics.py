"""Bounded diagnostic events; this module deliberately has no ORM dependency."""
from contextvars import ContextVar
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import stat
import sys
import threading
import time
import uuid


LOGGER_NAME = 'ydental.events'
MAX_EVENT_BYTES = 16 * 1024
ERROR_CODES = frozenset({
    'AUTHZ_DENIED', 'INPUT_REJECTED', 'INPUT_PARSE_ERROR',
    'BUSINESS_RULE_REJECTED', 'DAY_CLOSED', 'VERSION_CONFLICT',
    'REFUND_RECOVERY_REQUIRED', 'APPLICATION_ERROR', 'DIAGNOSTIC_FAILURE',
})
_FIELDS = (
    'event_id', 'run_id', 'task_id', 'case_id', 'attempt', 'trace_id',
    'request_id', 'operation_ref', 'idempotency_ref', 'component', 'operation',
    'stage', 'event', 'outcome', 'severity', 'actor_id', 'effective_uid',
    'su_flag', 'company_id', 'store_id', 'scope_revision', 'product_commit',
    'test_commit', 'core_commit', 'runtime_version', 'ts_utc', 'monotonic_ns',
    'pid', 'thread_id', 'process_seq', 'duration_ms', 'error_code',
    'error_class', 'exception_type', 'root_event_id', 'stack_ref',
    'transaction_phase', 'commit_observation', 'checkpoint_ref',
    'evidence_refs', 'object_ref', 'version_before', 'version_after', 'diff_ref',
    'audit_ref', 'context_missing',
)
_INTS = frozenset({
    'attempt', 'actor_id', 'effective_uid', 'company_id', 'store_id',
    'scope_revision', 'monotonic_ns', 'pid', 'thread_id', 'process_seq',
    'version_before', 'version_after', 'audit_ref',
})
_TOKEN = re.compile(r'[A-Za-z0-9_.:/-]{1,160}\Z')
_CONTEXT = ContextVar('ydental_diagnostic_context', default=None)
_LOGGER = logging.getLogger(LOGGER_NAME)
_CONFIG_LOCK = threading.RLock()
_SEQUENCE_LOCK = threading.Lock()
_SEQUENCE = 0
_PID = os.getpid()
_DIRECTORY = None
_FAILED = False


def _primitive(name, value):
    if value is None:
        return None
    if name in _INTS:
        if type(value) is not int or value < 0:
            raise ValueError('INVALID_DIAGNOSTIC_INTEGER')
        return value
    if name in {'su_flag', 'context_missing'}:
        if type(value) is not bool:
            raise ValueError('INVALID_DIAGNOSTIC_BOOLEAN')
        return value
    if name == 'duration_ms':
        if type(value) not in (int, float) or not 0 <= value < 1e12:
            raise ValueError('INVALID_DIAGNOSTIC_DURATION')
        return value
    if name == 'evidence_refs':
        if type(value) not in (list, tuple) or len(value) > 16:
            raise ValueError('INVALID_DIAGNOSTIC_REFERENCES')
        return [_primitive('stack_ref', item) for item in value]
    if type(value) is not str or not _TOKEN.fullmatch(value):
        raise ValueError('INVALID_DIAGNOSTIC_TOKEN')
    if name == 'error_code' and value not in ERROR_CODES:
        raise ValueError('INVALID_DIAGNOSTIC_CODE')
    return value


def _validated(values):
    if set(values) - set(_FIELDS):
        raise ValueError('UNKNOWN_DIAGNOSTIC_FIELD')
    return {name: _primitive(name, value) for name, value in values.items()}


def current_context():
    """Return a copy of primitive metadata, never a request or Environment."""
    return {name: list(value) if type(value) is list else value
            for name, value in (_CONTEXT.get() or {}).items()}


def bind_context(**values):
    try:
        selected = _validated(values)
    except Exception:
        _failure()
        selected = {}
    return _CONTEXT.set(selected)


def reset_context(token):
    try:
        _CONTEXT.reset(token)
    except Exception:
        _failure()


def update_context(**values):
    try:
        _CONTEXT.set(current_context() | _validated(values))
    except Exception:
        _failure()


@contextmanager
def context_scope(**values):
    token = bind_context(**(current_context() | values))
    try:
        yield
    finally:
        reset_context(token)


def _failure():
    """Independent fixed-text fallback; never serialize the original failure."""
    global _FAILED
    _FAILED = True
    try:
        os.write(2, b'YDENTAL_DIAGNOSTIC_FAILURE\n')
    except OSError:
        pass
    if _DIRECTORY is not None:
        try:
            path = _DIRECTORY / ('diagnostics-failed-%s.txt' % os.getpid())
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            try:
                os.write(fd, b'DIAGNOSTIC_FAILURE\n')
            finally:
                os.close(fd)
        except OSError:
            pass


def diagnostics_failed():
    return _FAILED


class JsonlFormatter(logging.Formatter):
    def format(self, record):
        # Never format arbitrary message, args, exception strings or locals.
        value = record.__dict__.get('ydental_event')
        if type(value) is not dict or value.get('schema_version') != '1.0':
            raise ValueError('INVALID_DIAGNOSTIC_RECORD')
        raw = json.dumps(value, ensure_ascii=True, allow_nan=False, separators=(',', ':'))
        if len(raw.encode('utf-8')) + 1 > MAX_EVENT_BYTES:
            raise ValueError('DIAGNOSTIC_EVENT_TOO_LARGE')
        return raw


class PidFileHandler(logging.Handler):
    """One exclusive file per PID/launch; seal segments without deleting any."""
    def __init__(self, directory, segment_bytes=10 * 1024 * 1024, max_segments=5):
        super().__init__(logging.INFO)
        if not 128 <= segment_bytes <= 10 * 1024 * 1024 or not 1 <= max_segments <= 5:
            raise ValueError('INVALID_DIAGNOSTIC_BUDGET')
        self.directory = Path(directory)
        self.pid = os.getpid()
        self.segment_bytes = segment_bytes
        self.max_segments = max_segments
        self.prefix = 'events-%s-%s' % (self.pid, uuid.uuid4().hex)
        self.segment = -1
        self.fd = None
        self.size = 0
        self.digest = hashlib.sha256()
        self._open_segment()

    def _open_segment(self):
        if self.segment + 1 >= self.max_segments:
            raise OSError('DIAGNOSTIC_SEGMENT_LIMIT')
        self.segment += 1
        self.path = self.directory / ('%s-%03d.jsonl' % (self.prefix, self.segment))
        self.fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        self.size = 0
        self.digest = hashlib.sha256()

    def _seal(self):
        if self.fd is None:
            return
        os.fsync(self.fd)
        os.close(self.fd)
        self.fd = None
        raw = json.dumps({'file': self.path.name, 'bytes': self.size,
                          'sha256': self.digest.hexdigest(), 'segment': self.segment},
                         separators=(',', ':')).encode('ascii') + b'\n'
        fd = os.open(str(self.path) + '.seal', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        try:
            os.write(fd, raw)
            os.fsync(fd)
        finally:
            os.close(fd)

    def emit(self, record):
        try:
            if self.pid != os.getpid():
                raise OSError('DIAGNOSTIC_INHERITED_HANDLER')
            raw = (self.format(record) + '\n').encode('utf-8')
            if len(raw) > self.segment_bytes:
                raise ValueError('DIAGNOSTIC_EVENT_EXCEEDS_SEGMENT')
            if self.size + len(raw) > self.segment_bytes:
                self._seal()
                self._open_segment()
            if self.fd is None:
                raise OSError('DIAGNOSTIC_HANDLER_CLOSED')
            view = memoryview(raw)
            while view:
                count = os.write(self.fd, view)
                if count <= 0:
                    raise OSError('DIAGNOSTIC_SHORT_WRITE')
                view = view[count:]
            self.size += len(raw)
            self.digest.update(raw)
        except Exception:
            _failure()

    def close(self):
        self.acquire()
        try:
            if self.pid == os.getpid():
                self._seal()
            elif self.fd is not None:
                os.close(self.fd)
                self.fd = None
        except Exception:
            _failure()
        finally:
            self.release()
            super().close()


def configure_once(directory=None):
    """Opt-in only, called during native addon loading, never per request."""
    global _DIRECTORY, _PID, _SEQUENCE
    with _CONFIG_LOCK:
        _LOGGER.propagate = False
        _LOGGER.setLevel(logging.INFO)
        existing = [h for h in _LOGGER.handlers if isinstance(h, PidFileHandler)]
        if any(h.pid == os.getpid() for h in existing):
            return True
        for handler in existing:
            _LOGGER.removeHandler(handler)
            handler.close()
        if not _LOGGER.handlers:
            _LOGGER.addHandler(logging.NullHandler())
        selected = directory if directory is not None else os.environ.get('YDENTAL_DIAGNOSTIC_DIR')
        if not selected:
            return False
        try:
            candidate = Path(selected)
            info = candidate.lstat()
            if (not candidate.is_absolute() or not stat.S_ISDIR(info.st_mode)
                    or candidate.resolve() != candidate or info.st_uid != os.getuid()
                    or stat.S_IMODE(info.st_mode) != 0o700):
                raise ValueError('INVALID_PRIVATE_DIAGNOSTIC_DIRECTORY')
            _DIRECTORY = candidate
            _PID = os.getpid()
            _SEQUENCE = 0
            handler = PidFileHandler(candidate)
            handler.setFormatter(JsonlFormatter())
            _LOGGER.addHandler(handler)
            return True
        except Exception:
            _failure()
            return False


def emit_event(event, **values):
    """Optional diagnostics cannot modify a caller's transaction or exception."""
    global _SEQUENCE
    try:
        metadata = current_context() | _validated(values)
        event_id = metadata.pop('event_id', None) or uuid.uuid4().hex
        with _SEQUENCE_LOCK:
            _SEQUENCE += 1
            sequence = _SEQUENCE
            result = dict.fromkeys(_FIELDS)
            result.update(metadata)
            result.update(schema_version='1.0', event_id=event_id,
                          event=_primitive('event', event),
                          ts_utc=datetime.now(timezone.utc).isoformat(),
                          monotonic_ns=time.monotonic_ns(), pid=os.getpid(),
                          thread_id=threading.get_ident(), process_seq=sequence,
                          runtime_version='python-' + sys.version.split()[0])
            result['context_missing'] = not all(result[name] is not None for name in
                                               ('run_id', 'task_id', 'case_id', 'trace_id', 'request_id'))
            result['commit_observation'] = result['commit_observation'] or 'NOT_OBSERVED'
            result['severity'] = result['severity'] or 'INFO'
            # Reserve and synchronously write in one short diagnostic section.
            # Handler failures use fixed stderr/files and never recurse here.
            _LOGGER.log(getattr(logging, result['severity'], logging.INFO), '', extra={'ydental_event': result})
        return event_id
    except Exception:
        _failure()
        return None


def classify_error(error, stage=None):
    """Classify only types and allowlisted codes, never localized messages."""
    code = error.__dict__.get('diagnostic_code')
    if type(code) is str and code in ERROR_CODES and code != 'APPLICATION_ERROR':
        return 'BUSINESS_REJECTION', code
    ancestry = {(item.__module__, item.__name__) for item in type(error).__mro__}
    if ('odoo.exceptions', 'AccessError') in ancestry:
        return 'BUSINESS_REJECTION', 'AUTHZ_DENIED'
    if ('odoo.exceptions', 'ValidationError') in ancestry:
        return 'BUSINESS_REJECTION', 'INPUT_REJECTED'
    if ('odoo.exceptions', 'UserError') in ancestry:
        return 'BUSINESS_REJECTION', 'BUSINESS_RULE_REJECTED'
    if stage == 'request.parse' and isinstance(error, (ValueError, TypeError, KeyError)):
        return 'BUSINESS_REJECTION', 'INPUT_PARSE_ERROR'
    return 'APPLICATION_ERROR', 'APPLICATION_ERROR'


def safe_exception_frames(error):
    """Only structural frame locations, with no messages/source/locals."""
    frames = []
    tb = error.__traceback__
    while tb is not None and len(frames) < 32:
        code = tb.tb_frame.f_code
        frames.append({'file': Path(code.co_filename).name[:128],
                       'function': code.co_name[:128], 'line': tb.tb_lineno})
        tb = tb.tb_next
    return frames


def _minimal_exception(event_id, component, stage, error_class, code, exception_type, root_event_id=None):
    """Fixed ASCII protocol, independent from JSON/formatters/stack serialization."""
    fields = {'event_id': event_id, 'component': component, 'stage': stage,
              'error_class': error_class, 'error_code': code,
              'exception_type': exception_type, 'root_event_id': root_event_id}
    context = current_context()
    for name in ('run_id', 'task_id', 'case_id', 'trace_id', 'request_id', 'operation_ref'):
        fields[name] = context.get(name)
    lines = []
    for name, value in fields.items():
        safe = value if type(value) is str and _TOKEN.fullmatch(value) else 'UNKNOWN'
        lines.append(name + '=' + safe + '\n')
    raw = ''.join(lines).encode('ascii')
    if _DIRECTORY is None:
        return
    fd = os.open(_DIRECTORY / ('exception-%s-%s.txt' % (os.getpid(), event_id)),
                 os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        view = memoryview(raw)
        while view:
            count = os.write(fd, view)
            if count <= 0:
                raise OSError('DIAGNOSTIC_SHORT_WRITE')
            view = view[count:]
        os.fsync(fd)
    finally:
        os.close(fd)


def record_exception(error, component, stage=None):
    """First preserve minimal primary, then optional structured/stack evidence."""
    try:
        return _record_exception(error, component, stage)
    except Exception:
        _failure()
        return None


def _record_exception(error, component, stage):
    primary_id = uuid.uuid4().hex
    selected_stage = stage or current_context().get('stage')
    error_class, code = classify_error(error, selected_stage)
    exception_type = type(error).__name__
    try:
        _minimal_exception(primary_id, component, selected_stage, error_class, code, exception_type)
    except Exception:
        # Even a directory/permission failure must not replace the business error.
        try:
            os.write(2, ('YDENTAL_PRIMARY event_id=%s error_code=%s\n' % (primary_id, code)).encode('ascii'))
        except OSError:
            pass
        _failure()
    emit_event('operation.rejected' if error_class == 'BUSINESS_REJECTION' else 'operation.error',
               event_id=primary_id, component=component, stage=selected_stage, error_class=error_class,
               error_code=code, exception_type=exception_type,
               outcome='denied' if error_class == 'BUSINESS_REJECTION' else 'error',
               severity='INFO' if error_class == 'BUSINESS_REJECTION' else 'ERROR')
    try:
        if error_class == 'APPLICATION_ERROR' and _DIRECTORY is not None:
            stack_ref = 'stack-%s-%s.json' % (os.getpid(), uuid.uuid4().hex)
            raw = json.dumps(safe_exception_frames(error), ensure_ascii=True,
                             separators=(',', ':')).encode('ascii')
            fd = os.open(_DIRECTORY / stack_ref, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            try:
                os.write(fd, raw)
            finally:
                os.close(fd)
            emit_event('exception.stack.saved', component=component, root_event_id=primary_id,
                       stack_ref=stack_ref, stage='evidence.finalization')
    except Exception as secondary:
        secondary_id = uuid.uuid4().hex
        try:
            _minimal_exception(secondary_id, component, 'evidence.finalization', 'EVIDENCE_ERROR',
                               'DIAGNOSTIC_FAILURE', type(secondary).__name__, primary_id)
        except Exception:
            pass
        emit_event('exception.secondary', event_id=secondary_id, component=component,
                   stage='evidence.finalization', error_class='EVIDENCE_ERROR', error_code='DIAGNOSTIC_FAILURE',
                   exception_type=type(secondary).__name__, root_event_id=primary_id, severity='ERROR')
        _failure()
    return primary_id

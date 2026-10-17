"""Bounded diagnostic events; this module deliberately has no ORM dependency."""
from contextvars import ContextVar
from contextlib import contextmanager
from datetime import datetime, timezone
import atexit
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
    'audit_ref', 'context_missing', 'native_http_log_level', 'diagnostic_log_level',
)
_INTS = frozenset({
    'attempt', 'actor_id', 'effective_uid', 'company_id', 'store_id',
    'scope_revision', 'monotonic_ns', 'pid', 'thread_id', 'process_seq',
    'version_before', 'version_after', 'audit_ref', 'native_http_log_level', 'diagnostic_log_level',
})
_TOKEN = re.compile(r'[A-Za-z0-9_.:/-]{1,160}\Z')
_CONTEXT = ContextVar('ydental_diagnostic_context', default=None)
_LOGGER = logging.getLogger(LOGGER_NAME)
_CONFIG_LOCK = threading.RLock()
_SEQUENCE_LOCK = threading.RLock()
_SEQUENCE = 0
_PID = os.getpid()
_DIRECTORY = None
_FAILED = False
_LIFECYCLE_PIDS = set()
_CLOSING_PIDS = set()
_LIFECYCLE_LABELS = {}
_ENV_LABEL = re.compile(r'[A-Za-z0-9_.:-]{1,96}\Z')
MAX_EXCEPTION_CHAIN_BYTES = 128 * 1024


def _lifecycle_labels():
    """Snapshot only the existing non-secret launch labels, never ORM state."""
    selected = {}
    for name in ('run_id', 'task_id', 'product_commit', 'test_commit', 'core_commit'):
        value = os.environ.get('YDENTAL_' + name.upper())
        selected[name] = value if type(value) is str and _ENV_LABEL.fullmatch(value) else None
    return selected


def _lifecycle_event(event, labels, outcome):
    # A process event is not an HTTP request or evidence of a committed unit.
    token = bind_context(**labels)
    try:
        levels = ({'native_http_log_level': logging.getLogger('odoo.http.server').getEffectiveLevel(),
                   'diagnostic_log_level': _LOGGER.getEffectiveLevel()} if event == 'run.start' else {})
        emit_event(event, component='ydental_access.diagnostics',
                   stage='process.diagnostics', outcome=outcome,
                   transaction_phase='NOT_OBSERVED', commit_observation='NOT_OBSERVED', **levels)
    finally:
        reset_context(token)


def _close_lifecycle(pid, labels):
    """A shared reentrant sequence/handler lock permits native shutdown too."""
    with _SEQUENCE_LOCK:
        if pid != os.getpid() or pid in _CLOSING_PIDS:
            return
        _CLOSING_PIDS.add(pid)
        try:
            _lifecycle_event('run.end', labels, 'DIAGNOSTIC_CLOSING')
        except Exception:
            _failure()


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
        # One lock, not two inversely ordered locks: logging.shutdown acquires
        # handler.lock before close, while emit_event assigns the next sequence
        # before logging acquires handler.lock. Native close can safely emit the
        # final lifecycle event under this same reentrant diagnostic-only lock.
        self.lock = _SEQUENCE_LOCK
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
                if self.pid in _LIFECYCLE_LABELS:
                    _close_lifecycle(self.pid, _LIFECYCLE_LABELS[self.pid])
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
            if _PID not in _LIFECYCLE_PIDS:
                _LIFECYCLE_PIDS.add(_PID)
                labels = _lifecycle_labels()
                _LIFECYCLE_LABELS[_PID] = labels
                # logging registered shutdown at import time. This later
                # callback normally runs first. Odoo may explicitly call
                # shutdown earlier; handler.close emits the same event once.
                atexit.register(_close_lifecycle, _PID, labels)
                _lifecycle_event('run.start', labels, 'DIAGNOSTIC_READY')
            return True
        except Exception:
            _failure()
            return False


def emit_event(event, **values):
    """Optional diagnostics cannot modify a caller's transaction or exception."""
    global _SEQUENCE
    try:
        metadata = _LIFECYCLE_LABELS.get(os.getpid(), {}) | current_context() | _validated(values)
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


def _structural_name(value):
    """Source/type labels only, bounded ASCII with no control characters."""
    return re.sub(r'[^A-Za-z0-9_.<>-]', '_', value[:128]) or 'UNKNOWN'


def _exception_frames(error, limit):
    frames = []
    tb = BaseException.__traceback__.__get__(error)
    while tb is not None and len(frames) < limit:
        code = tb.tb_frame.f_code
        frames.append({'file': _structural_name(Path(code.co_filename).name),
                       'function': _structural_name(code.co_name), 'line': tb.tb_lineno})
        tb = tb.tb_next
    return frames, tb is not None


def safe_exception_frames(error):
    """One traceback, for existing callers; full chain uses the helper below."""
    return _exception_frames(error, 32)[0]


def safe_exception_chain(error, *, max_depth=8, max_frames=32, max_total_frames=64):
    """Outer-to-first-visible-cause structure, never messages/args/locals.

    Explicit causes take precedence, as in Python's traceback display. A
    suppressed implicit context is not traversed or identified. Object IDs are
    only used in RAM for cycle detection; artifact node IDs are local ordinals.
    """
    if (not isinstance(error, BaseException)
            or type(max_depth) is not int or not 1 <= max_depth <= 8
            or type(max_frames) is not int or not 1 <= max_frames <= 32
            or type(max_total_frames) is not int or not 1 <= max_total_frames <= 64):
        raise ValueError('INVALID_DIAGNOSTIC_CHAIN_BOUND')
    nodes, seen = [], {}
    current = error
    remaining = max_total_frames
    termination = 'COMPLETE'
    while current is not None:
        node_id = 'exception-%s' % len(nodes)
        seen[id(current)] = node_id
        frames, frames_truncated = _exception_frames(current, min(max_frames, remaining))
        remaining -= len(frames)
        cause = BaseException.__cause__.__get__(current)
        context = BaseException.__context__.__get__(current)
        suppressed = BaseException.__suppress_context__.__get__(current)
        node = {'node_id': node_id, 'exception_type': _structural_name(type(current).__name__),
                'exception_module': _structural_name(type(current).__module__),
                'frames': frames, 'frames_truncated': frames_truncated,
                'context_suppressed': suppressed, 'link_type': 'none', 'next_node_id': None}
        nodes.append(node)
        if cause is not None:
            next_error, relationship = cause, 'cause'
        elif context is not None and not suppressed:
            next_error, relationship = context, 'context'
        else:
            if context is not None and suppressed:
                termination = 'CONTEXT_SUPPRESSED'
            break
        node['link_type'] = relationship
        if id(next_error) in seen:
            node['next_node_id'] = seen[id(next_error)]
            termination = 'CYCLE'
            break
        if len(nodes) >= max_depth:
            termination = 'DEPTH_LIMIT'
            break
        node['next_node_id'] = 'exception-%s' % len(nodes)
        current = next_error
    chain_truncated = termination in {'CYCLE', 'DEPTH_LIMIT'}
    return {'schema_version': '1.0', 'kind': 'PRIMARY_EXCEPTION_CHAIN',
            'outer_node_id': 'exception-0', 'nodes': nodes,
            'deepest_visible_node_id': nodes[-1]['node_id'],
            'first_cause_node_id': None if chain_truncated else nodes[-1]['node_id'],
            'first_cause_status': ('TRUNCATED' if chain_truncated else
                                   'VISIBLE_BOUNDARY_ONLY' if termination == 'CONTEXT_SUPPRESSED' else
                                   'VISIBLE_CHAIN_COMPLETE'),
            'termination': termination, 'truncated': chain_truncated or any(
                node['frames_truncated'] for node in nodes),
            'frame_count': max_total_frames - remaining,
            'limits': {'depth': max_depth, 'frames_per_node': max_frames,
                       'total_frames': max_total_frames, 'bytes': MAX_EXCEPTION_CHAIN_BYTES}}


def _minimal_chain(chain, primary_id):
    """Independent ASCII chain survives a failing JSON serializer/formatter."""
    lines = ['primary_event_id=' + primary_id + '\n',
             'kind=PRIMARY_EXCEPTION_CHAIN\n', 'termination=' + chain['termination'] + '\n',
             'first_cause_status=' + chain['first_cause_status'] + '\n',
             'truncated=' + str(int(chain['truncated'])) + '\n']
    for node in chain['nodes']:
        prefix = node['node_id'] + '.'
        for name in ('exception_type', 'exception_module', 'link_type'):
            lines.append(prefix + name + '=' + node[name] + '\n')
        lines.append(prefix + 'next=' + (node['next_node_id'] or 'NONE') + '\n')
        lines.append(prefix + 'context_suppressed=' + str(int(node['context_suppressed'])) + '\n')
        lines.append(prefix + 'frames_truncated=' + str(int(node['frames_truncated'])) + '\n')
        for number, frame in enumerate(node['frames']):
            frame_prefix = prefix + 'frame-%s.' % number
            for name in ('file', 'function', 'line'):
                lines.append(frame_prefix + name + '=' + str(frame[name]) + '\n')
    raw = ''.join(lines).encode('ascii')
    if len(raw) > MAX_EXCEPTION_CHAIN_BYTES:
        raise ValueError('DIAGNOSTIC_CHAIN_TOO_LARGE')
    name = 'chain-%s-%s.txt' % (os.getpid(), primary_id)
    fd = os.open(_DIRECTORY / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
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
    return name


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
        if _DIRECTORY is not None:
            stack_ref = 'stack-%s-%s.json' % (os.getpid(), uuid.uuid4().hex)
            chain = safe_exception_chain(error)
            chain['primary_event_id'] = primary_id
            chain_ref = _minimal_chain(chain, primary_id)
            raw = json.dumps(chain, ensure_ascii=True,
                             separators=(',', ':')).encode('ascii')
            if len(raw) > MAX_EXCEPTION_CHAIN_BYTES:
                raise ValueError('DIAGNOSTIC_CHAIN_TOO_LARGE')
            fd = os.open(_DIRECTORY / stack_ref, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
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
            emit_event('exception.stack.saved', component=component, root_event_id=primary_id,
                       stack_ref=stack_ref, evidence_refs=[chain_ref], stage='evidence.finalization')
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

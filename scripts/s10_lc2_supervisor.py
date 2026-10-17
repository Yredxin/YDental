"""Independent process exit and primary-error evidence, without Odoo or JSON dependency."""
from datetime import datetime, timezone
import os
from pathlib import Path
import signal
import subprocess
import time
import traceback
import uuid


def _utc():
    return datetime.now(timezone.utc).isoformat()


def append_plain(path, fields):
    """Only caller-supplied safe primitive values; no dynamic exception messages."""
    text = '\t'.join(str(value).replace('\n', '?').replace('\r', '?').replace('\t', '?')[:512]
                     for value in fields) + '\n'
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        os.write(fd, text.encode('utf-8'))
        os.fsync(fd)
    finally:
        os.close(fd)


def private_file(path):
    return os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'wb')


def safe_plain(path, fields):
    try:
        append_plain(path, fields)
        return True
    except OSError:
        try:
            os.write(2, b'LC2_PARENT_EVIDENCE_UNAVAILABLE\n')
        except OSError:
            pass
        return False


def save_primary(directory, error, *, stage, root_event_id=None):
    """Failure save never calls the JSON serializer or formats exception values/locals."""
    event_id = uuid.uuid4().hex
    path = Path(directory) / (event_id + '-exception.txt')
    rows = [event_id, root_event_id or '-', _utc(), stage, type(error).__module__, type(error).__name__]
    try:
        append_plain(path, rows)
        for frame in traceback.extract_tb(error.__traceback__):
            append_plain(path, ['frame', Path(frame.filename).name, frame.lineno, frame.name])
    except OSError:
        # Distinct smallest path; neither exception string nor the failed writer recurs.
        try:
            os.write(2, ('LC2_PRIMARY_SAVE_UNAVAILABLE ' + event_id + '\n').encode('ascii'))
        except OSError:
            pass
    return {'event_id': event_id, 'root_event_id': root_event_id, 'path': str(path)}


def launch(command, directory, *, timeout, attempt, last_checkpoint=None, env=None, cwd=None):
    directory = Path(directory)
    directory.mkdir(mode=0o700, parents=True, exist_ok=False)
    exit_path = directory / 'parent-exit.tsv'
    started = time.monotonic_ns()
    append_plain(exit_path, ['parent.start', _utc(), os.getpid(), attempt, last_checkpoint or 'NOT_OBSERVED'])
    child = None
    timed_out = False
    try:
        with private_file(directory / 'stdout.log') as stdout, private_file(directory / 'stderr-faulthandler.log') as stderr:
            child_env = dict(os.environ if env is None else env)
            child_env['PYTHONFAULTHANDLER'] = '1'
            child = subprocess.Popen(command, stdout=stdout, stderr=stderr, stdin=subprocess.DEVNULL,
                                     env=child_env, cwd=cwd)
            append_plain(exit_path, ['child.start', _utc(), child.pid])
            try:
                child.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                append_plain(exit_path, ['child.timeout', _utc(), child.pid])
                child.terminate()
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait(timeout=5)
    except BaseException as error:
        primary = save_primary(directory, error, stage='supervisor')
        if child is not None and child.poll() is None:
            safe_plain(exit_path, ['child.cleanup_intent', _utc(), child.pid, 'OUTCOME_UNKNOWN'])
            try:
                child.terminate()
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait(timeout=5)
            except BaseException as secondary:
                save_primary(directory, secondary, stage='supervisor_owned_child_cleanup',
                             root_event_id=primary['event_id'])
        raise
    finally:
        returncode = child.returncode if child else None
        observed_signal = -returncode if returncode is not None and returncode < 0 else None
        evidence_complete = safe_plain(exit_path, ['parent.end', _utc(), child.pid if child else '-', returncode,
                                                  observed_signal, timed_out, time.monotonic_ns() - started,
                                                  last_checkpoint or 'NOT_OBSERVED'])
    return {'pid': child.pid, 'returncode': returncode, 'signal': observed_signal,
            'timed_out': timed_out, 'exit_path': str(exit_path),
            'native_crash': observed_signal in {signal.SIGILL, signal.SIGABRT, signal.SIGBUS, signal.SIGFPE, signal.SIGSEGV},
            'parent_evidence_complete': evidence_complete,
            'transaction_outcome': 'NOT_OBSERVED'}

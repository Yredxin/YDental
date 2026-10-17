"""Two sequential existing clients; <=2 connections, <=6 explicit SQL each."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import time
import s10_p0_24_contract as c


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def event(kind, **data):
    with (c.PRIVATE / 'events.jsonl').open('ab') as stream:
        stream.write(json.dumps({'event': kind, 'UTC': now(), **data}, ensure_ascii=False, allow_nan=False, sort_keys=True).encode() + b'\n')
        stream.flush(); os.fsync(stream.fileno())


def clean_env(label):
    return {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8',
            'PYTHONDONTWRITEBYTECODE': '1', 'PGAPPNAME': 'ydental-s10-p0-24-' + label,
            'PGCONNECT_TIMEOUT': '5', 'PGCLIENTENCODING': 'UTF8', 'PGSSLMODE': 'disable', 'PGOPTIONS': c.OPTIONS}


def psql_client():
    base = c.PRIVATE / 'psql'; base.mkdir(mode=0o700)
    auth = c.credentials()
    def escape(value): return str(value).replace('\\', '\\\\').replace(':', '\\:')
    pgpass = ':'.join(escape(x) for x in ['127.0.0.1', 5432, c.DATABASE, 'odoo', auth['password']]) + '\n'
    with (base / 'pgpass').open('x') as stream:
        os.chmod(base / 'pgpass', 0o600); stream.write(pgpass); stream.flush(); os.fsync(stream.fileno())
    env = clean_env('psql'); env['PGPASSFILE'] = str(base / 'pgpass')
    argv = ['/usr/lib/postgresql/18/bin/psql', '-X', '-w', '-q', '-A', '-t', '-P', 'pager=off',
            '-v', 'ON_ERROR_STOP=0', '-v', 'ON_ERROR_ROLLBACK=off', '-v', 'FETCH_COUNT=0', '-v', 'AUTOCOMMIT=on',
            '-h', '127.0.0.1', '-p', '5432', '-U', 'odoo', '-d', c.DATABASE, '-f', '-']
    started = time.monotonic(); hard_deadline = started + 30
    records = []; identity = None; error = None; rolled_back = False
    received_digest = hashlib.sha256(); received_bytes = 0
    c.save(base / 'process-intent.json', {'argv': argv, 'UTC': now(), 'connect_timeout_s': 5, 'total_timeout_s': 30})
    with (base / 'stdout.raw').open('xb') as output, (base / 'stderr.raw').open('xb') as errors:
        process = subprocess.Popen(argv, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=errors)
        event('client_process_started', label='psql', pid=process.pid)
        select = selectors.DefaultSelector(); select.register(process.stdout, selectors.EVENT_READ)
        pending = b''
        def phase(label, sql, rollback=False):
            nonlocal pending, received_bytes
            assert len(records) < 6
            number = len(records) + 1
            marker = ('__P024_END_%s__' % number).encode()
            command = sql.encode() + b'\n\\echo ' + marker + b' :ERROR :SQLSTATE\n'
            c.write(base / ('%02d-%s.command' % (number, label)), command)
            rec = {'number': number, 'label': label, 'SQL': sql, 'intent_UTC': now()}
            records.append(rec); event('statement_intent', client='psql', number=number, label=label)
            process.stdin.write(command); process.stdin.flush()
            accumulated = b''
            end = hard_deadline if rollback else min(hard_deadline - 5, time.monotonic() + 6)
            while True:
                while b'\n' in pending:
                    line, pending = pending.split(b'\n', 1)
                    accumulated += line + b'\n'
                    if line.startswith(marker + b' '):
                        parts = line.split()
                        rec.update(returned_UTC=now(), SQL_error=parts[1].decode(), SQLSTATE=parts[2].decode())
                        body = accumulated[:-len(line)-1]
                        c.write(base / ('%02d-%s.stdout' % (number, label)), accumulated)
                        errors.flush(); os.fsync(errors.fileno())
                        c.save(base / ('%02d-%s.result.json' % (number, label)), rec)
                        if parts[1:] != [b'false', b'00000']:
                            raise RuntimeError('SQL_ERROR:' + label)
                        return body
                remaining = end - time.monotonic()
                if remaining <= 0: raise TimeoutError('PSQL_PHASE_TIMEOUT:' + label)
                if not select.select(remaining): raise TimeoutError('PSQL_OUTPUT_TIMEOUT:' + label)
                chunk = os.read(process.stdout.fileno(), 65536)
                if not chunk: raise RuntimeError('PSQL_CLOSED_BEFORE_MARKER:' + label)
                received_digest.update(chunk); received_bytes += len(chunk)
                output.write(chunk); output.flush(); os.fsync(output.fileno())
                pending += chunk
        try:
            phase('begin', c.BEGIN)
            assert phase('show-readonly', c.SHOW_RO).decode().strip() == 'on'
            assert phase('show-isolation', c.SHOW_ISO).decode().strip() == 'repeatable read'
            raw = phase('identity', c.IDENTITY)
            c.write(base / 'identity-return.utf8', raw)
            identity = c.parse(raw)
            c.save(base / 'identity-parsed.json', identity)
            assert c.identity_ok(identity), 'IDENTITY_OR_TRANSACTION_REJECTED'
            raw = phase('target', c.TARGET)
            io = c.write(base / 'target-return.utf8', raw)
            c.save(base / 'target-receive-write.json', io)
            # Do not parse the target until raw bytes are persisted and connection closed.
        except BaseException as exc:
            error = type(exc).__name__ + ':' + str(exc)
            c.save(base / 'failure-before-close.json', {'error': error, 'UTC': now()})
        finally:
            if process.poll() is None and len(records) < 6 and time.monotonic() < hard_deadline:
                try:
                    phase('rollback', c.ROLLBACK, rollback=True); rolled_back = True
                except BaseException as exc:
                    error = error or type(exc).__name__ + ':' + str(exc)
            try: process.stdin.close()
            except BrokenPipeError: pass
            try:
                process.wait(timeout=max(0.001, hard_deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                process.kill(); process.wait(); error = error or 'CLIENT_TOTAL_TIMEOUT_30S'
            select.close(); output.flush(); os.fsync(output.fileno()); errors.flush(); os.fsync(errors.fileno())
    result = {'client': 'psql', 'pid': process.pid, 'exit_code': process.returncode,
              'duration_s': time.monotonic() - started, 'explicit_statements': records,
              'explicit_ROLLBACK_returned': rolled_back, 'process_closed': process.poll() is not None,
              'identity': identity, 'error': error, 'UTC': now()}
    result.update(stdout_pipe_bytes=received_bytes, stdout_pipe_sha256=received_digest.hexdigest(),
                  stdout_disk_sha256=c.sha((base / 'stdout.raw').read_bytes()),
                  stdout_pipe_disk_equal=received_digest.hexdigest() == c.sha((base / 'stdout.raw').read_bytes()))
    c.save(base / 'process-result.json', result)
    return not error and process.returncode == 0 and rolled_back and len(records) == 6 and result['stdout_pipe_disk_equal']


def python_client():
    import psycopg2
    c.gate()
    assert (c.PRIVATE / 'python-process-intent.json').exists()
    assert c.parse((c.PRIVATE / 'psql/analysis.json').read_bytes())['all_layer_comparisons_match']
    base = c.PRIVATE / 'python'; base.mkdir(mode=0o700)
    start = time.monotonic(); conn = None; cur = None; records = []; error = None; identity = None; rollback = False
    def alarm(signum, frame): raise TimeoutError('PYTHON_CLIENT_BODY_TIMEOUT')
    signal.signal(signal.SIGALRM, alarm); signal.setitimer(signal.ITIMER_REAL, 25)
    def phase(label, sql):
        assert len(records) < 6
        number = len(records) + 1
        c.write(base / ('%02d-%s.sql' % (number, label)), sql.encode())
        rec = {'number': number, 'label': label, 'SQL': sql, 'intent_UTC': now()}
        records.append(rec); event('statement_intent', client='python', number=number, label=label)
        try:
            cur.execute(sql)
            rows = cur.fetchall() if cur.description else []
            cells = []
            for i, row in enumerate(rows):
                value = row[0]
                if not isinstance(value, str):
                    c.save(base / ('%02d-cell-%s-unexpected-type.json' % (number, i)), {'type': type(value).__name__, 'repr': repr(value)})
                    raise TypeError('EXPECTED_TEXT_DRIVER_RESULT')
                encoded = value.encode('utf-8')
                io = c.write(base / ('%02d-cell-%s.utf8' % (number, i)), encoded)
                cells.append({'row': i, 'Python_type': type(value).__name__, 'characters': len(value),
                              'UTF8_bytes': len(encoded), 'sha256': c.sha(encoded), 'description_type_oid': cur.description[0].type_code,
                              'write_readback': io})
            rec.update(returned_UTC=now(), status=cur.statusmessage, rows=len(rows), cells=cells)
            c.save(base / ('%02d-%s.result.json' % (number, label)), rec)
            return rows
        except BaseException as exc:
            c.save(base / ('%02d-%s.error.json' % (number, label)), {'type': type(exc).__name__, 'pgcode': getattr(exc, 'pgcode', None), 'UTC': now()})
            raise
    try:
        auth = c.credentials()
        event('python_connect_intent', database=c.DATABASE)
        conn = psycopg2.connect(dbname=c.DATABASE, connect_timeout=5, options=c.OPTIONS,
                               application_name='ydental-s10-p0-24-python', client_encoding='UTF8', sslmode='disable', **auth)
        conn.autocommit = True  # explicit BEGIN only; no driver-generated transaction start
        cur = conn.cursor()
        phase('begin', c.BEGIN)
        assert phase('show-readonly', c.SHOW_RO) == [('on',)]
        assert phase('show-isolation', c.SHOW_ISO) == [('repeatable read',)]
        rows = phase('identity', c.IDENTITY)
        assert len(rows) == 1
        raw = rows[0][0].encode('utf-8')
        c.write(base / 'identity-return.utf8', raw)
        identity = c.parse(raw); c.save(base / 'identity-parsed.json', identity)
        assert c.identity_ok(identity) and identity['backend_pid'] == conn.get_backend_pid(), 'IDENTITY_REJECTED'
        rows = phase('target', c.TARGET)
        c.save(base / 'target-row-count.json', {'rows': len(rows)})
        assert len(rows) == 1, 'TARGET_NOT_UNIQUE'
        # Already saved each driver's original text/type/UTF8 before any JSON parsing.
        io = c.write(base / 'target-return.utf8', rows[0][0].encode('utf-8'))
        c.save(base / 'target-receive-write.json', io)
    except BaseException as exc:
        error = type(exc).__name__ + ':' + str(exc)
        c.save(base / 'failure-before-close.json', {'error': error, 'UTC': now()})
    finally:
        signal.setitimer(signal.ITIMER_REAL, max(0.01, 29.5 - (time.monotonic() - start)))
        if cur is not None and conn is not None and not conn.closed and len(records) < 6:
            try: phase('rollback', c.ROLLBACK); rollback = True
            except BaseException as exc: error = error or type(exc).__name__ + ':' + str(exc)
        if cur is not None: cur.close()
        if conn is not None: conn.close()
        signal.setitimer(signal.ITIMER_REAL, 0)
    result = {'client': 'python/psycopg2', 'pid': os.getpid(), 'duration_s': time.monotonic() - start,
              'explicit_statements': records, 'explicit_ROLLBACK_returned': rollback,
              'connection_closed': conn is None or bool(conn.closed), 'identity': identity, 'error': error, 'UTC': now()}
    c.save(base / 'process-result.json', result)
    return 0 if not error and rollback and len(records) == 6 else 1


def main():
    os.umask(0o077)
    if len(sys.argv) == 2 and sys.argv[1] == 'python-client':
        sys.exit(python_client())
    c.gate()
    assert not (c.PRIVATE / 'run-intent.json').exists(), 'NO_REPLAY_OR_RECONNECT'
    c.save(c.PRIVATE / 'run-intent.json', {'UTC': now(), 'mode': 'one psql then one python, no retries'})
    (c.PRIVATE / 'events.jsonl').open('xb').close()
    psql_ok = psql_client()
    psql_layers_ok = c.analyze('psql') if (c.PRIVATE / 'psql/target-return.utf8').exists() else False
    python_started = False; python_code = None; python_ok = False
    if psql_ok and psql_layers_ok:
        python_started = True
        argv = [str(c.ROOT.parent / '.venv/bin/python'), str(Path(__file__).resolve()), 'python-client']
        c.save(c.PRIVATE / 'python-process-intent.json', {'argv': argv, 'UTC': now(), 'hard_timeout_s': 30})
        launched = time.monotonic(); timed_out = False
        with (c.PRIVATE / 'python.stdout').open('xb') as stdout, (c.PRIVATE / 'python.stderr').open('xb') as stderr:
            process = subprocess.Popen(argv, env=clean_env('python'), stdout=stdout, stderr=stderr)
            try: process.wait(timeout=30)
            except subprocess.TimeoutExpired: timed_out = True; process.kill(); process.wait()
            stdout.flush(); os.fsync(stdout.fileno()); stderr.flush(); os.fsync(stderr.fileno())
        python_code = process.returncode
        c.save(c.PRIVATE / 'python-process-result.json', {'pid': process.pid, 'exit_code': python_code,
            'duration_s': time.monotonic() - launched, 'hard_timeout': timed_out, 'UTC': now()})
        if (c.PRIVATE / 'python/target-return.utf8').exists():
            python_ok = c.analyze('python')
    c.save(c.PRIVATE / 'collection-result.json', {'psql_completed': psql_ok, 'psql_layers_ok': psql_layers_ok,
        'python_started': python_started, 'python_exit': python_code, 'python_layers_ok': python_ok,
        'UTC': now(), 'no_retry': True, 'business_actions': 0})
    print(json.dumps({'psql_completed': psql_ok, 'psql_layers_ok': psql_layers_ok, 'python_started': python_started,
                      'python_exit': python_code, 'python_layers_ok': python_ok, 'business_actions': 0}))
    return 0 if psql_ok and psql_layers_ok and python_ok else 1


if __name__ == '__main__':
    sys.exit(main())

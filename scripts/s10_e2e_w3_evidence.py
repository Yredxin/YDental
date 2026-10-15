"""Typed, durable JSON evidence for the isolated W3 run."""

from datetime import date, datetime
from decimal import Decimal
import json
import os
from pathlib import Path


def encode(value):
    if isinstance(value, datetime):
        return {'__w3_type__': 'datetime', 'value': value.isoformat()}
    if isinstance(value, date):
        return {'__w3_type__': 'date', 'value': value.isoformat()}
    if isinstance(value, Decimal):
        return {'__w3_type__': 'decimal', 'value': str(value)}
    if isinstance(value, (list, tuple)):
        return [encode(item) for item in value]
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise TypeError('Evidence keys must be strings')
        return {key: encode(item) for key, item in value.items()}
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError('Unsupported evidence value: ' + type(value).__name__)


def decode(value):
    if isinstance(value, list):
        return [decode(item) for item in value]
    if isinstance(value, dict):
        if set(value) == {'__w3_type__', 'value'}:
            kind = value['__w3_type__']
            if kind == 'date':
                return date.fromisoformat(value['value'])
            if kind == 'datetime':
                return datetime.fromisoformat(value['value'])
            if kind == 'decimal':
                return Decimal(value['value'])
            raise ValueError('Unknown evidence type')
        return {key: decode(item) for key, item in value.items()}
    return value


def write_once(path, value):
    """Publish a complete file only after serialization, fsync, and readback."""
    path = Path(path)
    if path.exists():
        raise FileExistsError(path)
    payload = json.dumps(encode(value), ensure_ascii=False, sort_keys=True, indent=2) + '\n'
    partial = path.with_name(path.name + '.partial')
    fd = os.open(partial, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        assert decode(json.loads(partial.read_text())) == decode(json.loads(payload))
        if path.exists():
            raise FileExistsError(path)
        os.replace(partial, path)
        dir_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except BaseException:
        partial.unlink(missing_ok=True)
        raise


def read_complete(path):
    path = Path(path)
    if not path.is_file() or path.name.endswith('.partial'):
        raise ValueError('Complete evidence file absent')
    return decode(json.loads(path.read_text()))

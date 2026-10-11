"""Process-local Python egress policy for the isolated S04 runner.

Copied as sitecustomize.py into the private run. No system firewall, existing
process or core source is changed. Libpq is separately endpoint/cluster guarded.
"""
import ipaddress
import os
import socket


_http_port = int(os.environ.get('YDENTAL_S04_HTTP_PORT', '18089'))
if not 18000 <= _http_port <= 18999:
    raise PermissionError('S04 isolated HTTP port refused')

_original_connect = socket.socket.connect
_original_connect_ex = socket.socket.connect_ex
_original_getaddrinfo = socket.getaddrinfo


def _allowed_host(host):
    try:
        return ipaddress.ip_address(host).is_loopback
    except (TypeError, ValueError):
        return host in ('localhost', b'localhost')


def _validate(address):
    if not isinstance(address, tuple) or len(address) < 2 or not _allowed_host(address[0]) or address[1] not in (5432, _http_port):
        raise PermissionError('S04 process egress denied by isolated validation policy')


def _connect(self, address):
    _validate(address)
    return _original_connect(self, address)


def _connect_ex(self, address):
    _validate(address)
    return _original_connect_ex(self, address)


def _getaddrinfo(host, port, *args, **kwargs):
    # Block external DNS lookup before attempting name resolution.
    if host is not None and not _allowed_host(host):
        raise PermissionError('S04 external name resolution denied by isolated validation policy')
    return _original_getaddrinfo(host, port, *args, **kwargs)


socket.socket.connect = _connect
socket.socket.connect_ex = _connect_ex
socket.getaddrinfo = _getaddrinfo

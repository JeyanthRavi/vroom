"""Authentication guard for endpoints that can write data or use the network."""
from __future__ import annotations

import hmac
import ipaddress
import os

from fastapi import HTTPException, Request


def _loopback(value: str) -> bool:
    try:
        return ipaddress.ip_address(value).is_loopback
    except ValueError:
        return value == 'localhost'


def require_admin(request: Request) -> None:
    configured = os.environ.get('F1_ADMIN_TOKEN', '')
    supplied = request.headers.get('x-f1-admin-token', '')
    authorization = request.headers.get('authorization', '')
    if authorization.lower().startswith('bearer '):
        supplied = authorization[7:]
    if configured and supplied and hmac.compare_digest(configured, supplied):
        return
    local_enabled = os.environ.get('F1_ALLOW_LOCAL_IMPORT') == '1'
    bind_host = os.environ.get('F1_BIND_HOST', '127.0.0.1')
    client_host = request.client.host if request.client else ''
    if not configured and local_enabled and _loopback(bind_host) and _loopback(client_host):
        return
    raise HTTPException(
        403,
        'Import/write endpoint disabled. Configure F1_ADMIN_TOKEN, or explicitly enable loopback-only local imports.',
    )

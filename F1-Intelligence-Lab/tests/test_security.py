from starlette.requests import Request
from fastapi import HTTPException
import pytest

from f1_intelligence_lab.security import require_admin


def request(host='127.0.0.1', headers=None):
    raw=[(key.lower().encode(),value.encode()) for key,value in (headers or {}).items()]
    return Request({'type':'http','method':'POST','path':'/','headers':raw,
                    'client':(host,1234),'server':('127.0.0.1',8000),'scheme':'http'})


def test_admin_token_is_required_and_constant_path_accepts_header(monkeypatch):
    monkeypatch.setenv('F1_ADMIN_TOKEN','secret-value')
    with pytest.raises(HTTPException) as denied:
        require_admin(request(headers={'x-f1-admin-token':'wrong'}))
    assert denied.value.status_code==403
    assert require_admin(request(headers={'authorization':'Bearer secret-value'})) is None


def test_explicit_local_mode_requires_loopback_client_and_bind(monkeypatch):
    monkeypatch.delenv('F1_ADMIN_TOKEN',raising=False)
    monkeypatch.setenv('F1_ALLOW_LOCAL_IMPORT','1')
    monkeypatch.setenv('F1_BIND_HOST','127.0.0.1')
    assert require_admin(request()) is None
    with pytest.raises(HTTPException):require_admin(request(host='203.0.113.4'))
    monkeypatch.setenv('F1_BIND_HOST','0.0.0.0')
    with pytest.raises(HTTPException):require_admin(request())

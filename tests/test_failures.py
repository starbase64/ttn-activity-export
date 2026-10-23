import json
from types import SimpleNamespace
from garminconnect import GarminConnectConnectionError,GarminConnectTooManyRequestsError
from failures import diagnostic,RatePause


def test_safe_diagnostics_keep_http_and_retry_after_not_response_text():
    exc=GarminConnectTooManyRequestsError('private-token user@example.invalid https://private.example')
    exc.response=SimpleNamespace(status_code=429,headers={'Retry-After':'120'})
    detail=diagnostic(exc)
    assert detail['http_status']==429 and detail['reason']=='rate_limit' and detail['retry_after_seconds']==120
    assert 'private' not in json.dumps(detail) and '@' not in json.dumps(detail)
    assert diagnostic(GarminConnectConnectionError('400 Client Error: private'))['http_status']==400


def test_rate_pause_persists_and_does_not_shorten(tmp_path,monkeypatch):
    monkeypatch.setattr('failures.time.time',lambda:1000)
    path=tmp_path/'pause.json';pause=RatePause(path)
    assert pause.record({'reason':'rate_limit'})==900
    assert RatePause(path).remaining()==900
    pause.record({'reason':'rate_limit','retry_after_seconds':30})
    assert RatePause(path).remaining()==900
    monkeypatch.setattr('failures.time.time',lambda:2000)
    assert RatePause(path).remaining()==0
    assert pause.record({'reason':'connection'})==0


def test_retry_after_is_respected(tmp_path):
    pause=RatePause(tmp_path/'pause.json')
    pause.record({'reason':'rate_limit','retry_after_seconds':120})
    assert 118<=pause.remaining()<=120

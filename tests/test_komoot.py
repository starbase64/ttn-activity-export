"""Own-account API fixtures only; never contact Komoot in these tests."""
import json
import threading
from urllib.error import HTTPError
import pytest
from archive import Archive,OfflineAccountMismatch
from datahub import load_archive
from engine import account_key
from komoot_client import KomootClient,KomootError,download_tours,tour_summary
from tests.test_datahub import GPX


def tour(ident=123,**kw):
    return {'id':ident,'name':'Trip','date':'2020-01-01T10:00:00Z','sport':'touringbicycle','type':'tour_recorded','distance':2500.,'duration':600.,**kw}


def client(tmp_path,transport):
    api=KomootClient(tmp_path/'pause.json',transport);api.user='42';api.token='secret-token';return api


def test_login_uses_password_once_then_token_and_no_redirects(tmp_path):
    import base64
    calls=[]
    def transport(path,headers,binary):
        calls.append((path,base64.b64decode(headers['Authorization'][6:]).decode()))
        return json.dumps({'username':'42','password':'token'} if 'account/email' in path else {'_embedded':{'tours':[]}}).encode()
    api=client(tmp_path,transport).login('my+name@example.invalid','password')
    r=api.inventory('2020-01-01','2020-01-02')
    assert r['complete'] and calls[0][1]=='my+name@example.invalid:password' and calls[1][1]=='42:token'
    assert '%2B' in calls[0][0] and '%40' in calls[0][0]
    from komoot_client import NoRedirect
    assert NoRedirect().redirect_request(None,None,302,'',{},'https://other.invalid') is None
    assert not (tmp_path/'pause.json').exists()


def test_inventory_keeps_valid_pages_and_reports_error_without_advancing(tmp_path):
    calls=[]
    def transport(path,*args):
        calls.append(path)
        if 'page=0' in path:return json.dumps({'_embedded':{'tours':[tour(),tour(124,date='2019-01-01')]}}).encode()
        raise HTTPError('redacted',503,'',{},None)
    api=client(tmp_path,transport);r=api.inventory('2020-01-01','2020-12-31')
    assert len(r['items'])==1 and r['offset']==1 and not r['complete'] and r['error']['http_status']==503
    api.transport=lambda *a:b'{"_embedded":{"tours":[]}}'
    resumed=api.inventory('2020-01-01','2020-12-31',previous=r)
    assert resumed['complete'] and len(resumed['items'])==1
    with pytest.raises(ValueError):api.inventory('2020-01-02','2020-12-31',previous=r)


def test_429_persists_pause_without_spending_another_request(tmp_path):
    calls=[]
    def limited(*args):calls.append(1);raise HTTPError('redacted',429,'',{'Retry-After':'60'},None)
    api=client(tmp_path,limited)
    with pytest.raises(KomootError):api.request('/v007/test')
    other=client(tmp_path,limited)
    with pytest.raises(KomootError):other.request('/v007/test')
    assert len(calls)==1 and other.pause.remaining()>0
    text=(tmp_path/'pause.json').read_text();assert 'token' not in text


def test_download_cache_offline_map_and_correct_account_link(tmp_path):
    calls=[]
    def transport(path,*args):calls.append(path);return GPX
    api=client(tmp_path,transport);path=tmp_path/'komoot.sqlite';account=account_key('komoot:mine');items=[tour_summary(tour())]
    r=download_tours(api,path,account,items)
    assert r['files']==1 and not r['error'] and (tmp_path/'gpx/123.gpx').read_bytes()==GPX
    r=download_tours(api,path,account,items)
    assert r['cached']==1 and len(calls)==1
    data=load_archive(path);assert len(data['activities'])==1 and data['tracks']
    from activity_table import table_row
    assert table_row(data['activities'][0],'2020-01-01',language='en')['Activity link']=='https://www.komoot.com/tour/123'
    with pytest.raises(OfflineAccountMismatch):download_tours(api,path,account_key('komoot:other'),items)


def test_metadata_only_and_forbidden_gpx_preserve_tour(tmp_path):
    calls=[]
    def transport(path,*args):calls.append(path);raise HTTPError('redacted',403,'',{},None)
    api=client(tmp_path,transport);path=tmp_path/'komoot.sqlite';account=account_key('komoot:mine');items=[tour_summary(tour())]
    r=download_tours(api,path,account,items,gpx=False)
    assert not calls and r['imported']==1
    r=download_tours(api,path,account,items)
    assert r['error']['http_status']==403 and api.token and len(load_archive(path)['activities'])==1
    assert not (tmp_path/'gpx').exists()


def test_cancel_and_malformed_responses_never_claim_complete(tmp_path):
    api=client(tmp_path,lambda *a:b'{}');r=api.inventory('2020-01-01','2020-12-31')
    assert not r['complete'] and r['error'] and r['offset']==0
    cancel=threading.Event();cancel.set();r=api.inventory('2020-01-01','2020-12-31',cancel=cancel)
    assert r['cancelled'] and not r['complete']
    with pytest.raises(ValueError):tour_summary(tour('../123'))
    with pytest.raises(ValueError):api.request('https://attacker.invalid')

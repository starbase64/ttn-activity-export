import threading
from pathlib import Path
from archive import Archive
from engine import account_key
from cache_discovery import discover_cache


def archive(path,account):
    with Archive(path,account) as db:db.put('summary','2020-01-01',{}, {'steps':42})
    return path


def test_known_old_and_new_roots_find_only_matching_account(tmp_path):
    account=account_key('mine');other=account_key('other')
    old=tmp_path/'Garmin_Export';new=tmp_path/'TTN_Activity_Export'/'Garmin'
    db=archive(new/('account-'+account)/'garmin-offline.sqlite',account)
    archive(new/('account-'+other)/'foreign.sqlite',other)
    cache=old/('account-'+account)/'cache-v1';file=cache/'activities/2020/2020-01-01-test.json'
    file.parent.mkdir(parents=True);file.write_text('{"request":{},"data":[]}')
    result=discover_cache(account,[old,new])
    assert {r['path'] for r in result}=={str(db.resolve()),str(cache.resolve())}
    assert result[0]['kind']=='sqlite' and result[0]['responses']==1 and result[0]['start']=='2020-01-01'


def test_explicit_database_is_deduplicated_and_validated(tmp_path):
    account=account_key('mine');path=archive(tmp_path/'custom.sqlite',account)
    result=discover_cache(account,[tmp_path,tmp_path],[path,path])
    assert len(result)==1
    assert not discover_cache(account_key('other'),[tmp_path],[path])
    (tmp_path/'bad.sqlite').write_bytes(b'not sqlite')
    assert len(discover_cache(account,[tmp_path]))==1


def test_empty_cancelled_and_outside_depth_are_not_candidates(tmp_path):
    account=account_key('mine')
    with Archive(tmp_path/'empty.sqlite',account):pass
    archive(tmp_path/'a/b/c/d/e/outside.sqlite',account)
    assert not discover_cache(account,[tmp_path])
    cancel=threading.Event();cancel.set()
    assert not discover_cache(account,[tmp_path],cancel=cancel)
    assert not discover_cache(None,[tmp_path])


def test_cache_import_keeps_existing_database_responses(tmp_path):
    from datahub import import_cache
    account=account_key('mine');path=archive(tmp_path/'archive.sqlite',account)
    folder=tmp_path/('account-'+account)/'cache-v1';file=folder/'summary/2020/2020-01-01-old.json'
    file.parent.mkdir(parents=True);file.write_text('{"request":{},"data":{"steps":1}}')
    result=import_cache(path,folder,account)
    assert result['responses']==0 and result['skipped']==1 and not result['errors']
    with Archive(path,readonly=True) as db:assert db.get('summary','2020-01-01',{})['data']['steps']==42

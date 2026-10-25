import base64
import json
import sys
import pytest
from engine import account_key
from secure_sessions import KomootSessions


def fake_codec(data,entropy,decrypt):
    # Test double, deliberately not offered as an application cipher.
    prefix=base64.b64encode(entropy)+b':'
    if decrypt:
        if not data.startswith(prefix):raise ValueError('Wrong account')
        return base64.b64decode(data[len(prefix):],validate=True)
    return prefix+base64.b64encode(data)


def test_protected_tokens_roundtrip_account_isolation_and_removal(tmp_path):
    a=account_key('a');b=account_key('b');store=KomootSessions(tmp_path,fake_codec)
    store.save(a,'42','private-session-token');store.save(b,'43','other-token')
    assert b'private-session-token' not in store.path(a).read_bytes()
    assert store.load(a)==('42','private-session-token') and store.load(b)==('43','other-token')
    original=store.path(b).read_bytes();store.path(b).write_bytes(store.path(a).read_bytes())
    with pytest.raises(ValueError):store.load(b)
    store.path(b).write_bytes(original);store.forget(a);store.forget(a)
    assert store.load(a) is None and store.load(b)==('43','other-token')
    with pytest.raises(ValueError):store.path('../escape')
    store.path(b).write_bytes(b'invalid protected data')
    with pytest.raises(ValueError):store.load(b)


def test_storage_failure_does_not_write_plaintext_or_leave_temporary_files(tmp_path):
    def fail(*a):raise OSError('Could not encrypt')
    store=KomootSessions(tmp_path,fail)
    with pytest.raises(OSError):store.save(account_key('a'),'42','secret')
    assert not list(tmp_path.iterdir())


@pytest.mark.skipif(sys.platform!='win32',reason='Native Windows DPAPI integration')
def test_native_windows_dpapi_persists_across_instances_and_binds_account(tmp_path):
    import subprocess
    a=account_key('a');b=account_key('b');store=KomootSessions(tmp_path)
    store.save(a,'42','native-private-token-ä')
    assert b'native-private-token' not in store.path(a).read_bytes()
    assert KomootSessions(tmp_path).load(a)==('42','native-private-token-ä')
    code='from secure_sessions import KomootSessions; import sys; assert KomootSessions(sys.argv[1]).load(sys.argv[2]) == ("42", "native-private-token-ä")'
    subprocess.run([sys.executable,'-c',code,str(tmp_path),a],check=True)
    store.path(b).write_bytes(store.path(a).read_bytes())
    with pytest.raises(OSError):store.load(b)
    store.forget(a);assert store.load(a) is None

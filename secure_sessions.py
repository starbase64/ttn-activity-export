"""Account-bound Komoot tokens protected for the current Windows user by DPAPI."""
import ctypes
import json
import os
from pathlib import Path
import re
import sys
import tempfile


def dpapi(data,entropy,decrypt=False):
    if sys.platform!='win32':raise OSError('Secure session storage unavailable')
    from ctypes import wintypes
    class Blob(ctypes.Structure):
        _fields_=[('size',wintypes.DWORD),('data',ctypes.POINTER(ctypes.c_ubyte))]
    raw=ctypes.create_string_buffer(data);extra=ctypes.create_string_buffer(entropy)
    source=Blob(len(data),ctypes.cast(raw,ctypes.POINTER(ctypes.c_ubyte)))
    salt=Blob(len(entropy),ctypes.cast(extra,ctypes.POINTER(ctypes.c_ubyte)));out=Blob()
    crypt=ctypes.WinDLL('crypt32',use_last_error=True);kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    func=crypt.CryptUnprotectData if decrypt else crypt.CryptProtectData
    func.argtypes=[ctypes.POINTER(Blob),ctypes.c_void_p,ctypes.POINTER(Blob),ctypes.c_void_p,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(Blob)]
    func.restype=wintypes.BOOL
    kernel.LocalFree.argtypes=[ctypes.c_void_p];kernel.LocalFree.restype=ctypes.c_void_p
    if not func(ctypes.byref(source),None,ctypes.byref(salt),None,None,1,ctypes.byref(out)):
        raise OSError('Secure session operation failed')
    try:return ctypes.string_at(out.data,out.size)
    finally:
        if out.data:
            ctypes.memset(out.data,0,out.size);kernel.LocalFree(out.data)


class KomootSessions:
    def __init__(self,folder,codec=None):self.folder=Path(folder);self.codec=codec or dpapi;self.available=codec is not None or sys.platform=='win32'
    def path(self,account):
        if not isinstance(account,str) or not re.fullmatch('[a-f0-9]{20}',account):raise ValueError('Invalid account identity')
        return self.folder/(account+'.bin')
    def exists(self,account):return self.path(account).is_file()
    def forget(self,account):self.path(account).unlink(missing_ok=True)
    def load(self,account):
        path=self.path(account)
        if not path.exists():return None
        with path.open('rb') as stream:raw=stream.read(16385)
        if len(raw)>16384:raise ValueError('Invalid protected session')
        data=json.loads(self.codec(raw,('TTN-Komoot:'+account).encode(),True))
        if not isinstance(data,dict) or data.get('account')!=account or data.get('schema')!=1:raise ValueError('Invalid protected session')
        user=data.get('user');token=data.get('token')
        if not isinstance(user,str) or not user.isdigit() or len(user)>32 or not isinstance(token,str) or not token or len(token)>4096:raise ValueError('Invalid protected session')
        return user,token
    def save(self,account,user,token):
        if not self.available:raise OSError('Secure session storage unavailable')
        if not isinstance(user,str) or not user.isdigit() or len(user)>32 or not isinstance(token,str) or not token or len(token)>4096:raise ValueError('Invalid session')
        raw=json.dumps({'schema':1,'account':account,'user':user,'token':token}).encode()
        encrypted=self.codec(raw,('TTN-Komoot:'+account).encode(),False)
        if not encrypted or len(encrypted)>16384:raise ValueError('Invalid protected session')
        path=self.path(account);path.parent.mkdir(parents=True,exist_ok=True)
        fd,name=tempfile.mkstemp(prefix='.session-',dir=path.parent)
        try:
            with os.fdopen(fd,'wb') as stream:stream.write(encrypted)
            os.replace(name,path)
            if self.load(account)!=(user,token):
                self.forget(account);raise OSError('Could not verify saved session')
        finally:Path(name).unlink(missing_ok=True)

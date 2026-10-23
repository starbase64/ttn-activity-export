"""Safe error details and persistent local rate-limit backoff; never stores response bodies."""
import math
import re
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
import json


def exception_chain(exc):
    seen=set()
    while exc is not None and id(exc) not in seen:
        seen.add(id(exc));yield exc
        exc=exc.__cause__ or exc.__context__


def error_status(exc):
    for item in exception_chain(exc):
        status=getattr(getattr(item,'response',None),'status_code',None)
        if isinstance(status,int):return status
        match=re.search(r'(?:API Error|HTTP|status|error)\s*[:(]?\s*([45]\d{2})',str(item),re.I)
        if match:return int(match.group(1))
        match=re.search(r'\b([45]\d{2})\s+(?:Client|Server)\s+Error',str(item),re.I)
        if match:return int(match.group(1))
    return None


def diagnostic(exc):
    code=error_status(exc)
    name=type(exc).__name__
    chain=list(exception_chain(exc))
    # Inspect text locally to identify a category; never return arbitrary server text.
    text=' '.join(str(item) for item in chain).lower()
    reason='unknown'
    if code==429 or name=='GarminConnectTooManyRequestsError':reason='rate_limit'
    elif 'cloudflare' in text or 'captcha' in text or 'challenge' in text:reason='challenge'
    elif code==401 or name=='GarminConnectAuthenticationError':reason='authentication'
    elif code==403:reason='forbidden'
    elif code in (400,405,422):reason='invalid_request'
    elif code==404:reason='not_found'
    elif code and code>=500:reason='server'
    elif any('timeout' in type(item).__name__.lower() or 'timed out' in str(item).lower() for item in chain):reason='timeout'
    elif any('ssl' in str(item).lower() or 'certificate' in str(item).lower() for item in chain):reason='tls'
    elif any('connection' in type(item).__name__.lower() or 'resolve host' in str(item).lower() for item in chain):reason='connection'
    retry_after=None
    for item in chain:
        headers=getattr(getattr(item,'response',None),'headers',{}) or {}
        raw=headers.get('Retry-After') or headers.get('retry-after')
        if raw is None:continue
        try:
            delay=float(raw)
        except (TypeError,ValueError):
            try:delay=parsedate_to_datetime(str(raw)).timestamp()-time.time()
            except (ValueError,TypeError,OverflowError):continue
        if math.isfinite(delay):retry_after=max(1,math.ceil(delay));break
    return {'error_type':name,'http_status':code,'reason':reason,'retry_after_seconds':retry_after}


class RatePause:
    """Applies to this local app, including after restarting; never retries automatically."""
    def __init__(self,path):self.path=Path(path);self.until=0.0
    def remaining(self):
        end=self.until
        try:
            stored=float(json.loads(self.path.read_text(encoding='utf-8'))['until'])
            if math.isfinite(stored):end=max(end,stored)
        except (OSError,ValueError,KeyError,TypeError):pass
        return max(0,math.ceil(end-time.time()))
    def record(self,detail):
        if detail.get('reason')!='rate_limit' and detail.get('http_status')!=429:return 0
        # Garmin's Retry-After takes precedence; otherwise use a cautious local 15-minute pause.
        seconds=detail.get('retry_after_seconds') or 15*60
        seconds=max(1,int(seconds),self.remaining())
        self.until=time.time()+seconds
        try:
            self.path.parent.mkdir(parents=True,exist_ok=True)
            tmp=self.path.with_suffix('.tmp')
            tmp.write_text(json.dumps({'until':self.until}),encoding='utf-8')
            tmp.replace(self.path)
        except OSError:pass  # Still protect the current session when the profile is unwritable.
        return seconds

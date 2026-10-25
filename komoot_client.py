"""Experimental, read-only own-account connector. No website scraping or access-control bypass."""
import base64
import hashlib
import json
import math
import threading
import time
from collections import defaultdict
from datetime import date,datetime
from pathlib import Path
from types import SimpleNamespace
from urllib.request import Request,build_opener,HTTPRedirectHandler
from urllib.parse import quote,urlencode
from urllib.error import HTTPError
from archive import Archive
from datahub import activities_from_archive,parse_activity,MAX_FILE
from failures import RatePause,diagnostic


class KomootError(Exception):
    def __init__(self,status=None,headers=None):
        self.response=SimpleNamespace(status_code=status,headers=headers or {})
        super().__init__('Komoot request failed')


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None


def tour_summary(item):
    ident=str(item.get('id',''))
    if not ident.isdigit() or len(ident)>32:raise ValueError('Invalid tour ID')
    stamp=datetime.fromisoformat(str(item['date']).replace('Z','+00:00')).isoformat()
    result={'activityId':-int(hashlib.sha256(('komoot:'+ident).encode()).hexdigest()[:14],16),
        'activityName':str(item.get('name') or ('Komoot '+ident)), 'startTimeLocal':stamp,
        'activityType':{'typeKey':str(item.get('sport') or 'other')},'sourceProvider':'komoot',
        'sourceActivityId':ident,'sourceTourType':item.get('type'),'importSource':'komoot-online',
        'komootMetadata':item}
    for src,dest in [('distance','distance'),('duration','duration'),('elevation_up','elevationGain'),('elevation_down','elevationLoss')]:
        value=item.get(src)
        if isinstance(value,(float,int)) and math.isfinite(value) and value>=0:result[dest]=value
    return result


class KomootClient:
    def __init__(self,pause_path,transport=None):
        self.pause=RatePause(pause_path);self.user=None;self.token=None;self.last=0.
        self.transport=transport;self.opener=build_opener(NoRedirect())
    def request(self,path,*,credentials=None,binary=False,cancel=None):
        cancel=cancel or threading.Event()
        if self.pause.remaining():raise KomootError(429,{'Retry-After':str(self.pause.remaining())})
        if cancel.wait(max(0,.5-(time.monotonic()-self.last))):raise InterruptedError('Stopped')
        if not path.startswith('/v00') or '..' in path:raise ValueError('Invalid API path')
        user,password=credentials or (self.user,self.token)
        if not user or not password:raise KomootError(401)
        headers={'User-Agent':'TTNActivityExport/0.6.3 (local desktop export)',
                 'Authorization':'Basic '+base64.b64encode((user+':'+password).encode()).decode(),
                 'Accept':'application/gpx+xml' if binary else 'application/hal+json,application/json'}
        self.last=time.monotonic()
        try:
            if self.transport:raw=self.transport(path,headers,binary)
            else:
                with self.opener.open(Request('https://api.komoot.de'+path,headers=headers),timeout=30) as response:
                    raw=response.read((MAX_FILE if binary else 16*1024**2)+1)
            if len(raw)>(MAX_FILE if binary else 16*1024**2):raise ValueError('Response size limit')
            return raw if binary else json.loads(raw)
        except HTTPError as exc:
            error=KomootError(exc.code,dict(exc.headers or {}));exc.close()
            if exc.code==429:self.pause.record(diagnostic(error))
            if exc.code==401:self.token=None
            raise error from None
    def login(self,email,password,cancel=None):
        self.user=None;self.token=None
        result=self.request('/v006/account/email/'+quote(email,safe='')+'/',credentials=(email,password),cancel=cancel)
        ident=str(result.get('username',''));token=result.get('password')
        if not ident.isdigit() or not isinstance(token,str) or not token:raise KomootError(401)
        self.user=ident;self.token=token
        return self
    def inventory(self,start,end,kind='tour_recorded',previous=None,cancel=None,event=lambda *a:None):
        date.fromisoformat(start);date.fromisoformat(end)
        if start>end or kind not in ('','tour_recorded','tour_planned'):raise ValueError('Invalid filters')
        cancel=cancel or threading.Event();previous=previous or {}
        if previous and (previous['start'],previous['end'],previous['kind'])!=(start,end,kind):raise ValueError('Filters changed')
        result={'provider':'komoot','start':start,'end':end,'kind':kind,'items':list(previous.get('items',[])),
                'offset':previous.get('offset',0),'complete':previous.get('complete',False),'error':None}
        seen={str(i['activityId']) for i in result['items']}
        for _ in range(10):
            if result['complete'] or cancel.is_set():break
            try:
                query=urlencode({'page':result['offset'],'limit':100,'start_date':start,'end_date':end,'type':kind,'sort_field':'date','sort_direction':'desc'})
                data=self.request('/v007/users/'+self.user+'/tours/?'+query,cancel=cancel)
                batch=data.get('_embedded',{}).get('tours')
                if not isinstance(batch,list):raise ValueError('Unknown tour list format')
                if not batch:result['complete']=True;break
                normalized=[tour_summary(t) for t in batch]
                if not any(str(t['activityId']) not in seen for t in normalized):raise ValueError('Repeated tour page')
                for item in normalized:
                    ident=str(item['activityId']);day=item['startTimeLocal'][:10]
                    if ident not in seen:
                        seen.add(ident)
                        if start<=day<=end and (not kind or item['sourceTourType']==kind):result['items'].append(item)
                result['offset']+=1;event('komoot_inventory',len(result['items']))
                # Empty pages are authoritative; do not assume a short page means complete.
            except Exception as exc:
                if not cancel.is_set():result['error']=diagnostic(exc)
                break
        result['checked_at']=time.time();result['cancelled']=cancel.is_set();return result


def download_tours(client,path,account,items,gpx=True,cancel=None,event=lambda *a:None):
    cancel=cancel or threading.Event();report={'imported':0,'files':0,'cached':0,'error':None,'cancelled':False}
    with Archive(path,account) as db:
        by_day=defaultdict(dict);old_days={}
        for a in activities_from_archive(db):
            if a.get('importSource'):
                by_day[a['_day']][str(a['activityId'])]={k:v for k,v in a.items() if not k.startswith('_')}
                old_days[str(a['activityId'])]=a['_day']
        for item in items:
            if cancel.is_set():break
            summary=tour_summary(item['komootMetadata']);ident=summary['activityId'];day=summary['startTimeLocal'][:10]
            by_day[day][str(ident)]=summary;db.put('activities',day,{'import':'activity-files-v1'},list(by_day[day].values()))
            if str(ident) in old_days and old_days[str(ident)]!=day:
                old=old_days[str(ident)];by_day[old].pop(str(ident),None);db.put('activities',old,{'import':'activity-files-v1'},list(by_day[old].values()))
            report['imported']+=1
            if gpx:
                dataset='activity-'+str(ident)+'-gpx';request={'import':'original-file-v1','format':'gpx'}
                try:
                    cached=db.get(dataset,day,request)
                    if cached is not None:part=cached['data'];report['cached']+=1
                    else:
                        part=client.request('/v007/tours/'+summary['sourceActivityId']+'.gpx',binary=True,cancel=cancel)
                        parse_activity(part,'gpx')  # Validate real GPX before retaining it; never synthesize a route.
                        db.put(dataset,day,request,part,True);report['files']+=1
                    folder=Path(path).parent/'gpx';folder.mkdir(parents=True,exist_ok=True)
                    target=folder/(summary['sourceActivityId']+'.gpx');tmp=target.with_suffix('.gpx.tmp');tmp.write_bytes(part);tmp.replace(target)
                except Exception as exc:
                    if not cancel.is_set():report['error']=diagnostic(exc)
                    break
            event('komoot_download',report['imported'],len(items))
        report['cancelled']=cancel.is_set();db.record_run({'operation':'komoot_download',**report})
    return report

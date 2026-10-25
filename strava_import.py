"""Offline import of user-downloaded Strava account ZIPs. No network/authentication."""
import csv
import gzip
import hashlib
import io
import math
import os
import re
import shutil
import stat
import threading
import zipfile
from contextlib import contextmanager
from types import SimpleNamespace
from collections import defaultdict
from datetime import datetime
from pathlib import Path,PurePosixPath
from archive import Archive
from datahub import activities_from_archive,parse_activity,MAX_FILE,MAX_ZIP_FILES

MAX_TOTAL=8*1024**3
MAX_CSV=32*1024**2
MONTHS={m:i for i,m in enumerate(('Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'),1)}
SPORTS={'Ride':'cycling','Virtual Ride':'virtual_ride','EBikeRide':'e_bike_fitness','E-Bike Ride':'e_bike_fitness',
        'Run':'running','Virtual Run':'virtual_run','Walk':'walking','Hike':'hiking','Swim':'swimming',
        'Weight Training':'strength_training','WeightTraining':'strength_training','Workout':'other'}


def member_path(name):
    if not isinstance(name,str) or '\\' in name or ':' in name:raise ValueError('Invalid member path')
    p=PurePosixPath(name)
    if p.is_absolute() or '..' in p.parts:raise ValueError('Invalid member path')
    return p.as_posix()


def bounded_read(stream,limit):
    value=stream.read(limit+1)
    if len(value)>limit:raise ValueError('Member exceeds import limit')
    return value


class FolderSource:
    """ZIP-compatible read-only view of a folder; never follow symbolic links."""
    def __init__(self,root):
        self.root=Path(root).resolve();self.entries={}
        for parent,dirs,files in os.walk(self.root,followlinks=False):
            dirs[:]=[d for d in dirs if not (Path(parent)/d).is_symlink()]
            for name in files:
                path=Path(parent)/name
                if path.is_symlink():continue
                key=member_path(path.relative_to(self.root).as_posix())
                if not path.is_file():continue
                self.entries[key]=SimpleNamespace(filename=key,file_size=path.stat().st_size,is_dir=lambda:False)
                if len(self.entries)>MAX_ZIP_FILES:raise ValueError('Folder member count limit')
    def infolist(self):return list(self.entries.values())
    def open(self,info):
        path=self.root/info.filename
        if path.is_symlink() or not path.resolve().is_relative_to(self.root):raise ValueError('Unsafe source path')
        fd=os.open(path,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0)|getattr(os,'O_BINARY',0))
        if not stat.S_ISREG(os.fstat(fd).st_mode):os.close(fd);raise ValueError('Not a regular source file')
        return os.fdopen(fd,'rb')


@contextmanager
def open_source(source):
    source=Path(source)
    if source.is_dir():yield FolderSource(source)
    else:
        with zipfile.ZipFile(source) as archive:yield archive


def prepare_source(source,destination,copy_source=False,cancel=None):
    """Validate either source type, optionally retain a complete copy in a fresh account subfolder."""
    import uuid
    source=Path(source).resolve();cancel=cancel or threading.Event()
    with open_source(source) as archive:
        infos=archive.infolist()
        if len(infos)>MAX_ZIP_FILES:raise ValueError('Source member count limit')
        manifests=[i for i in infos if not i.is_dir() and PurePosixPath(i.filename).name=='activities.csv']
        if len(manifests)!=1:raise ValueError('Expected one activities.csv')
        with archive.open(manifests[0]) as stream:
            headers=next(csv.reader(io.StringIO(bounded_read(stream,MAX_CSV).decode('utf-8-sig'))),[])
        if not {'Activity ID','Activity Date','Activity Name','Activity Type'}<=set(headers):raise ValueError('Unsupported activity CSV headers')
    if not copy_source:return source
    destination=Path(destination).resolve()
    if source.is_dir() and destination.is_relative_to(source):raise ValueError('Copy destination is inside source folder')
    destination.mkdir(parents=True,exist_ok=True)
    target=destination/('strava-'+uuid.uuid4().hex)
    staging=destination/('.copy-'+uuid.uuid4().hex)
    staging.mkdir()
    try:
        total=0
        if source.is_dir():
            folder=FolderSource(source)
            for info in folder.infolist():
                out=staging/info.filename;out.parent.mkdir(parents=True,exist_ok=True)
                with folder.open(info) as src,out.open('xb') as dst:
                    while True:
                        if cancel.is_set():raise InterruptedError('Source copy cancelled')
                        chunk=src.read(1024**2)
                        if not chunk:break
                        total+=len(chunk)
                        if total>MAX_TOTAL:raise ValueError('Source copy size limit')
                        dst.write(chunk)
            result=target
        else:
            with source.open('rb') as src,(staging/source.name).open('xb') as dst:
                while True:
                    if cancel.is_set():raise InterruptedError('Source copy cancelled')
                    chunk=src.read(1024**2)
                    if not chunk:break
                    total+=len(chunk)
                    if total>MAX_TOTAL:raise ValueError('Source copy size limit')
                    dst.write(chunk)
            result=target/source.name
        staging.rename(target)
        return result
    except BaseException:
        shutil.rmtree(staging,ignore_errors=True)
        raise


def timestamp(value):
    value=value.strip()
    try:return datetime.fromisoformat(value.replace('Z','+00:00')).isoformat()
    except ValueError:pass
    m=re.fullmatch(r'([A-Za-z]{3}) (\d{1,2}), (\d{4}), (\d{1,2}):(\d{2}):(\d{2})\s*(AM|PM)?',value)
    if not m or m[1] not in MONTHS:raise ValueError('Unsupported activity date')
    hour=int(m[4]);suffix=m[7]
    if suffix:hour=hour%12+(12 if suffix=='PM' else 0)
    return datetime(int(m[3]),MONTHS[m[1]],int(m[2]),hour,int(m[5]),int(m[6])).isoformat()


def numeric(value):
    try:
        n=float(value.strip())
        return n if math.isfinite(n) and n>=0 else None
    except (ValueError,AttributeError):return None


def row_summary(headers,row):
    def values(name):return [row[i].strip() for i,h in enumerate(headers) if h==name and i<len(row)]
    def first(name):return next((v for v in values(name) if v),'')
    ident=first('Activity ID')
    if not ident.isdigit() or len(ident)>32 or int(ident)<=0:raise ValueError('Invalid Strava activity ID')
    start=timestamp(first('Activity Date'))
    kind=first('Activity Type')
    summary={'activityId':-int(hashlib.sha256(('strava:'+ident).encode()).hexdigest()[:14],16),
        'activityName':first('Activity Name') or 'Strava '+ident,'startTimeLocal':start,
        'activityType':{'typeKey':SPORTS.get(kind,re.sub(r'[^a-z0-9]+','_',kind.lower()).strip('_') or 'other')},
        'importSource':'strava-account-export','sourceProvider':'strava','sourceActivityId':ident,
        'sourceFilename':first('Filename'),'sourceDateText':first('Activity Date'),
        'sourceTimeZone':'explicit' if datetime.fromisoformat(start).tzinfo else 'unspecified',
        # Preserve duplicate CSV columns rather than guessing which similarly named field was meant.
        'stravaCsv':list(zip(headers,row))}
    distances=values('Distance')
    # Strava's full account CSV has a display-distance column (km) followed by a metric distance column (m).
    distance=numeric(distances[-1]) if len(distances)>1 else None
    if len(distances)>1 and distance is None:
        display=numeric(distances[0]);distance=display*1000 if display is not None else None
    if distance is not None:summary['distance']=distance
    for source,dest in [('Moving Time','duration'),('Elevation Gain','elevationGain'),('Elevation Loss','elevationLoss'),
                        ('Average Heart Rate','averageHR'),('Max Heart Rate','maxHR'),('Average Watts','avgPower'),('Calories','calories')]:
        candidates=[numeric(v) for v in values(source)];value=next((v for v in reversed(candidates) if v is not None),None)
        if value is not None:summary[dest]=value
    if 'duration' not in summary:
        candidates=[numeric(v) for v in values('Elapsed Time')];value=next((v for v in reversed(candidates) if v is not None),None)
        if value is not None:summary['duration']=value
    if summary.get('duration') and summary.get('distance') is not None:summary['averageSpeed']=summary['distance']/summary['duration']
    return summary


def import_strava_archive(path,source,account,cancel=None,event=lambda *a:None):
    """Stream the ZIP; preserve CSV metadata even if a referenced activity file is absent/broken."""
    cancel=cancel or threading.Event()
    stats={'imported':0,'duplicates':0,'failed':0,'files':0,'rows':0,'errors':[],'cancelled':False,'limited':False}
    with open_source(source) as z:
        entries={}
        infos=z.infolist()
        if len(infos)>MAX_ZIP_FILES:raise ValueError('Archive member count limit')
        for info in infos:
            if info.is_dir():continue
            try:key=member_path(info.filename)
            except ValueError:continue  # Never extract paths or follow a reference outside this archive.
            if key in entries:raise ValueError('Ambiguous archive member names')
            entries[key]=info
        manifests=[k for k in entries if PurePosixPath(k).name=='activities.csv']
        if len(manifests)!=1:raise ValueError('Expected one activities.csv')
        manifest=manifests[0]
        if entries[manifest].file_size>MAX_CSV:raise ValueError('Activity list size limit')
        with z.open(entries[manifest]) as f:raw=bounded_read(f,MAX_CSV)
        reader=csv.reader(io.StringIO(raw.decode('utf-8-sig'),newline=''))
        headers=next(reader,[])
        if len(headers)>512:raise ValueError('Too many CSV columns')
        if not {'Activity ID','Activity Date','Activity Name','Activity Type'}<=set(headers):raise ValueError('Unsupported activity CSV headers')
        prefix=PurePosixPath(manifest).parent
        budget=len(raw);seen=set()
        with Archive(path,account) as db:
            by_day=defaultdict(dict);known={}
            for a in activities_from_archive(db):
                if a.get('importSource'):
                    clean={k:v for k,v in a.items() if not k.startswith('_')};by_day[a['_day']][str(a['activityId'])]=clean
                    if a.get('sourceProvider')=='strava':known[str(a.get('sourceActivityId'))]=(a['_day'],clean)
            for row_number,row in enumerate(reader,2):
                if cancel.is_set():break
                if not row or not any(row):continue
                stats['rows']+=1
                try:
                    if len(row)>512:raise ValueError('Too many CSV columns')
                    summary=row_summary(headers,row);source_id=summary['sourceActivityId']
                    if source_id in seen:raise ValueError('Duplicate activity ID in CSV')
                    seen.add(source_id);ident=summary['activityId'];day=summary['startTimeLocal'][:10]
                    filename=summary['sourceFilename'];part=None;kind=None
                    if filename:
                        try:
                            key=member_path(filename)
                            candidates=[key,member_path(str(prefix/key))]
                            matches=list(dict.fromkeys(k for k in candidates if k in entries))
                            if len(matches)!=1:raise ValueError('Missing or ambiguous activity file')
                            info=entries[matches[0]]
                            if info.file_size>MAX_FILE:raise ValueError('Activity file size limit')
                            with z.open(info) as f:part=bounded_read(f,MAX_FILE)
                            budget+=len(part)
                            if filename.lower().endswith('.gz'):
                                with gzip.GzipFile(fileobj=io.BytesIO(part)) as f:part=bounded_read(f,MAX_FILE)
                                budget+=len(part);filename=filename[:-3]
                            if budget>MAX_TOTAL:raise ValueError('Total uncompressed import limit')
                            kind=PurePosixPath(filename).suffix.lower().lstrip('.')
                            if kind not in ('fit','gpx','tcx'):raise ValueError('Unsupported activity file')
                            decoded,_=parse_activity(part,kind)
                            for k,v in decoded.items():
                                if summary.get(k) is None:summary[k]=v
                        except Exception as exc:
                            part=None;kind=None;stats['failed']+=1
                            if len(stats['errors'])<100:stats['errors'].append({'row':row_number,'activity':source_id,'error_type':type(exc).__name__,'stage':'file'})
                    previous=known.get(source_id)
                    if previous:
                        old_day,old=previous
                        # Keep already parsed values when a later package has no usable original file.
                        for key,value in old.items():
                            if summary.get(key) is None:summary[key]=value
                        stats['duplicates']+=1
                    else:stats['imported']+=1
                    if summary.get('averageSpeed') is None and summary.get('duration') and summary.get('distance') is not None:summary['averageSpeed']=summary['distance']/summary['duration']
                    by_day[day][str(ident)]=summary
                    # Same request identity as other local activity imports: these are partial local days.
                    db.put('activities',day,{'import':'activity-files-v1'},list(by_day[day].values()))
                    if previous and previous[0]!=day:
                        by_day[previous[0]].pop(str(ident),None)
                        db.put('activities',previous[0],{'import':'activity-files-v1'},list(by_day[previous[0]].values()))
                    if part is not None:db.put('activity-'+str(ident)+'-'+kind,day,{'import':'original-file-v1','format':kind},part,True);stats['files']+=1
                    known[source_id]=(day,summary)
                except (OSError,):raise
                except Exception as exc:
                    # Database errors must stop the import, not be misreported as malformed CSV rows.
                    import sqlite3
                    if isinstance(exc,sqlite3.Error):raise
                    stats['failed']+=1
                    if len(stats['errors'])<100:stats['errors'].append({'row':row_number,'error_type':type(exc).__name__,'stage':'row'})
                event('import',stats['imported'],stats['duplicates'],stats['failed'])
                if budget>MAX_TOTAL:stats['limited']=True;break
            stats['cancelled']=cancel.is_set()
            db.record_run({'operation':'strava_local_import',**stats})
    return stats

"""One readable row per Garmin activity, with explicit metric units."""
import math
from datetime import datetime
from sports import SPORT_LABELS

COLUMNS = [
 ('date','Datum','Date'),('time','Startzeit','Start time'),('name','Aktivität','Activity'),
 ('sport','Sportart','Sport type'),('location','Ort','Location'),('distance','Distanz (km)','Distance (km)'),
 ('duration','Dauer (hh:mm:ss)','Duration (hh:mm:ss)'),('speed','Ø Geschwindigkeit (km/h)','Avg speed (km/h)'),
 ('ascent','Anstieg (m)','Ascent (m)'),('descent','Abstieg (m)','Descent (m)'),
 ('power','Ø Leistung (W)','Avg power (W)'),('heart_rate','Ø Herzfrequenz (bpm)','Avg heart rate (bpm)'),
 ('calories','Kalorien (kcal)','Calories (kcal)'),('id','Aktivitäts-ID','Activity ID'),
 ('url','Aktivitäts-Link','Activity link'),
]


def headers(language):
    return [de if language=='de' else en for _,de,en in COLUMNS]


def number(value,scale=1,digits=2):
    if isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value):
        return round(value*scale,digits)
    return None


def table_row(activity,source_date,language='de'):
    timestamp=activity.get('startTimeLocal') or ''
    day,clock=source_date,''
    if isinstance(timestamp,str):
        try:
            dt=datetime.fromisoformat(timestamp.replace('Z','+00:00'))
            day,clock=dt.date().isoformat(),dt.strftime('%H:%M:%S')
        except ValueError:
            pass
    duration=number(activity.get('duration'),digits=0)
    duration_text=''
    if duration is not None and duration>=0:
        hours,rem=divmod(int(duration),3600);minutes,seconds=divmod(rem,60)
        duration_text=f'{hours:02d}:{minutes:02d}:{seconds:02d}'
    kind=activity.get('activityType') or {}
    key=kind.get('typeKey','') if isinstance(kind,dict) else str(kind)
    pair=SPORT_LABELS.get(key)
    sport=pair[0 if language=='de' else 1] if pair else key.replace('_',' ').capitalize()
    ident=activity.get('activityId')
    url=f'https://connect.garmin.com/modern/activity/{ident}' if str(ident).isdigit() else ''
    if activity.get('sourceProvider')=='strava' and str(activity.get('sourceActivityId','')).isdigit():url='https://www.strava.com/activities/'+str(activity['sourceActivityId'])
    values={
        'date':day,'time':clock,'name':activity.get('activityName') or '',
        'sport':sport,'location':activity.get('locationName') or '',
        'distance':number(activity.get('distance'),.001,2),'duration':duration_text,
        'speed':number(activity.get('averageSpeed'),3.6,1),
        'ascent':number(activity.get('elevationGain'),digits=1),'descent':number(activity.get('elevationLoss'),digits=1),
        'power':number(activity.get('avgPower'),digits=1),'heart_rate':number(activity.get('averageHR'),digits=1),
        'calories':number(activity.get('calories'),digits=1),'id':ident,'url':url,
    }
    return {(de if language=='de' else en):values[key] for key,de,en in COLUMNS}


def type_graph(payload):
    """Build a type-key -> descendant-key map using Garmin's numeric parent links."""
    nodes={}
    def visit(value):
        if isinstance(value,dict):
            if value.get('typeKey') and value.get('typeId') is not None:
                nodes[str(value['typeId'])]=value
            for child in value.values():
                if isinstance(child,(dict,list)):visit(child)
        elif isinstance(value,list):
            for child in value:visit(child)
    visit(payload)
    descendants={}
    for ident,node in nodes.items():
        key=node['typeKey'];seen=set();current=ident
        while current in nodes and current not in seen:
            seen.add(current);ancestor=nodes[current]
            descendants.setdefault(ancestor['typeKey'],set()).add(key)
            current=str(ancestor.get('parentTypeId'))
    return descendants

# API source paths for filtering the corresponding readable summary columns.
SOURCE_PATHS = {
 'date':'startTimeLocal','time':'startTimeLocal','name':'activityName','sport':'activityType/typeKey',
 'location':'locationName','distance':'distance','duration':'duration','speed':'averageSpeed',
 'ascent':'elevationGain','descent':'elevationLoss','power':'avgPower','heart_rate':'averageHR',
 'calories':'calories','id':'activityId','url':'activityId',
}

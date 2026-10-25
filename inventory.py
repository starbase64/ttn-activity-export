"""Bounded Garmin metadata listing, separate from detail/file retrieval and archives."""
from datetime import date
import threading
import time
from failures import diagnostic

FIELDS=('activityId','activityName','startTimeLocal','distance','duration','elevationGain','activityType','locationName')

def read_inventory(api,start,end,*,previous=None,pages=10,interval=.5,cancel=None,event=lambda *a:None):
    date.fromisoformat(start);date.fromisoformat(end)
    if start>end or not 1<=pages<=100:raise ValueError('Invalid inventory range')
    cancel=cancel or threading.Event()
    previous=previous or {}
    if previous and (previous.get('start'),previous.get('end'))!=(start,end):raise ValueError('Inventory range changed')
    items=list(previous.get('items',[]));seen={str(a['activityId']) for a in items}
    offset=int(previous.get('offset',0));complete=bool(previous.get('complete',False))
    result={'schema':1,'start':start,'end':end,'items':items,'offset':offset,'complete':complete,'requests':0,'error':None}
    if complete:return result
    search=getattr(api,'search_activities',None)
    if not callable(search):raise ValueError('Paged activity listing unavailable')
    for _ in range(pages):
        if cancel.is_set():break
        if result['requests'] and cancel.wait(max(0,interval)):break
        try:
            result['requests']+=1
            batch=search(start=result['offset'],limit=100,startDate=start,endDate=end)
            if not isinstance(batch,list):raise ValueError('Invalid list response')
            if not batch:result['complete']=True;break
            page=[];page_ids=set()
            for item in batch:
                if not isinstance(item,dict) or not str(item.get('activityId','')).isdigit():raise ValueError('Invalid activity identifier')
                ident=str(item['activityId'])
                if ident not in seen and ident not in page_ids:
                    page.append({k:item[k] for k in FIELDS if k in item});page_ids.add(ident)
            if not page:raise ValueError('Repeated activity page')
            # A complete validated page is committed at once; never advance past malformed data.
            items.extend(page);seen.update(page_ids);result['offset']+=len(batch)
            event('inventory_page',len(items),result['requests'])
        except Exception as exc:
            result['error']=diagnostic(exc)
            if result['error']['reason']=='rate_limit':event('rate_limit',result['error'])
            break
    result['checked_at']=time.time();result['cancelled']=cancel.is_set()
    return result

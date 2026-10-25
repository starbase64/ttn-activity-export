"""Bounded, read-only account-specific discovery in known local storage locations."""
import os
import re
import threading
from collections import deque
from pathlib import Path
from archive import Archive


def has_cached_files(folder,cancel):
    queue=deque([(folder,0)]);visited=0
    while queue and visited<100 and not cancel.is_set():
        current,depth=queue.popleft();visited+=1
        try:
            with os.scandir(current) as entries:
                for n,entry in enumerate(entries):
                    if n>=2000 or cancel.is_set():break
                    if entry.is_symlink():continue
                    if depth==2 and entry.is_file(follow_symlinks=False):return True
                    if depth<2 and len(queue)<100 and entry.is_dir(follow_symlinks=False):queue.append((Path(entry.path),depth+1))
        except OSError:continue
    return False


def discover_cache(account,roots,archives=(),cancel=None):
    if not account or not re.fullmatch('[a-f0-9]{20}',account):return []
    cancel=cancel or threading.Event();found={};seen=set();queue=deque()
    if cancel.is_set():return []
    def database(path):
        path=Path(path)
        if path.is_symlink() or not path.is_file():return
        try:
            with Archive(path,account,readonly=True) as db:
                row=db.db.execute("SELECT COUNT(*),MIN(CASE WHEN day!='snapshot' THEN day END),MAX(CASE WHEN day!='snapshot' THEN day END) FROM responses").fetchone()
                if not row[0]:return
            key=str(path.resolve());found[key]={'path':key,'kind':'sqlite','responses':row[0],'start':row[1],'end':row[2]}
        except Exception:pass  # Unrelated, corrupt or another account: never open it as the selected account.
    for path in archives:
        if path:database(path)
    for root in roots:
        if root:queue.append((Path(root).expanduser(),0))
    # Do not traverse user drives or trees containing per-day files and imported source packages.
    skip={'exports','gpx','sources','runtime','node_modules','venv','.venv','.git','__pycache__'}
    while queue and len(seen)<400 and not cancel.is_set():
        folder,depth=queue.popleft()
        try:
            if folder.is_symlink() or not folder.is_dir():continue
            folder=folder.resolve();key=str(folder)
            if key in seen:continue
            seen.add(key)
            if folder.name.startswith('account-') and folder.name!='account-'+account:continue
            if folder.name=='cache-v1':
                if folder.parent.name=='account-'+account:
                    # Presence check only: never scan thousands of raw response files here.
                    if has_cached_files(folder,cancel):found[key]={'path':key,'kind':'cache','responses':None,'start':None,'end':None}
                continue
            with os.scandir(folder) as entries:
                for n,entry in enumerate(entries):
                    if n>=2000 or cancel.is_set():break
                    if entry.is_symlink():continue
                    if entry.is_file(follow_symlinks=False) and Path(entry.name).suffix.lower() in ('.sqlite','.sqlite3','.db'):
                        database(entry.path)
                    elif depth<4 and len(queue)<400 and entry.is_dir(follow_symlinks=False) and entry.name not in skip and not entry.name.startswith('.'):
                        queue.append((Path(entry.path),depth+1))
        except OSError:continue
    return sorted(found.values(),key=lambda r:(r['kind']!='sqlite',r['path']))

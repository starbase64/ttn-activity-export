"""Local account/job metadata. Never persist passwords or live client objects."""
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import json
from engine import Plan, account_key, atomic_json

PROVIDERS = ('garmin', 'komoot', 'strava')
DEFAULT_ORDER = ('garmin', 'komoot', 'strava')

def now():return datetime.now(timezone.utc).isoformat(timespec='seconds')

class Workspace:
    def __init__(self,path):
        self.path=Path(path);self.data={'schema':1,'accounts':[],'jobs':[],'tooltips':True,'order':list(DEFAULT_ORDER)}
        if self.path.exists():
            saved=json.loads(self.path.read_text(encoding='utf-8'))
            if not isinstance(saved,dict) or saved.get('schema')!=1:raise ValueError('Invalid workspace')
            self.data.update(saved)
            if not isinstance(self.accounts,list) or not isinstance(self.jobs,list):raise ValueError('Invalid workspace')
            for a in self.accounts:
                if not isinstance(a,dict) or a.get('provider') not in PROVIDERS or not isinstance(a.get('email'),str):raise ValueError('Invalid account')
                if a.get('id')!=self.key(a['provider'],a['email'],a.get('china',False)):raise ValueError('Invalid account identity')
            for j in self.jobs:
                if not isinstance(j,dict) or j.get('action') not in ('download','export'):raise ValueError('Invalid job')
                Plan(**j['plan']).validate()
                if j.get('status')=='running':j['status']='interrupted'
    @property
    def accounts(self):return self.data['accounts']
    @property
    def jobs(self):return self.data['jobs']
    @staticmethod
    def key(provider,email,china=False):
        return account_key(email,china) if provider=='garmin' else account_key(provider+':'+email)
    def save(self):atomic_json(self.path,self.data)
    def add_account(self,provider,email,output,china=False):
        email=email.strip()
        if provider not in PROVIDERS or not email or len(email)>320:raise ValueError('Invalid account')
        ident=self.key(provider,email,china)
        found=next((a for a in self.accounts if a['id']==ident),None)
        if found:return found
        found={'id':ident,'provider':provider,'email':email,'china':bool(china),'output':str(output),'created':now()}
        self.accounts.append(found);self.save();return found
    def enqueue(self,account,plan,action):
        import uuid
        snapshot=deepcopy(vars(plan));Plan(**snapshot).validate()
        if plan.account!=account['id'] or account['provider']!='garmin':raise ValueError('Unavailable provider')
        job={'id':uuid.uuid4().hex,'account':account['id'],'provider':account['provider'],'email':account['email'],
             'plan':snapshot,'action':action,'status':'queued','created':now()}
        self.jobs.append(job);self.save();return job

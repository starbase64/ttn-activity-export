"""Synthetic offline fixtures: never mistaken for real Garmin responses."""
from datetime import datetime, timezone

class DemoGarmin:
    def get_daily_heart_rate_stats(self,start,end):
        from engine import days
        return [{'DEMO_SYNTHETIC':True,'calendarDate':day,'restingHeartRate':57,'maxHeartRate':122,'minHeartRate':48} for day in days(start,end)]

    def get_sleep_daily(self,start,end):
        from engine import days
        return [{'DEMO_SYNTHETIC':True,'calendarDate':day,'totalSleepSeconds':25200,'sleepScore':82} for day in days(start,end)]

    def get_activity_types(self):
        return [{'typeId':1,'typeKey':'cycling'}, {'typeId':2,'typeKey':'e_bike_mountain','parentTypeId':1},
                {'typeId':3,'typeKey':'running'}, {'typeId':4,'typeKey':'hiking'},
                {'typeId':5,'typeKey':'walking'}, {'typeId':6,'typeKey':'swimming'}]

    def get_activities_by_date(self,startdate,enddate):
        return self.search_activities(start=0,limit=100,startDate=startdate,endDate=enddate)

    def search_activities(self,start=0,limit=100,**filters):
        day=filters.get('startDate','2020-01-01')
        from datetime import date,timedelta
        first=date.fromisoformat(day);last=date.fromisoformat(filters.get('endDate',day))
        calendar=[(first+timedelta(days=i)).isoformat() for i in range((last-first).days+1)]
        return [{'DEMO_SYNTHETIC':True,'activityId':int(day.replace('-',''))*100+i+1,
                 'activityName':f'DEMO – Beispielfahrt {i+1}', 'locationName':'Demo-Ort',
                 'startTimeLocal':day+' 10:00:00','activityType':{'typeKey':'e_bike_mountain'},
                 'distance':15670+i*100,'duration':3682+i*60,'averageSpeed':4.25,
                 'elevationGain':216,'elevationLoss':211,'avgPower':None,'averageHR':140,'calories':500}
                for day in calendar for i in range(30)][start:start+limit]

    def get_user_summary(self,cdate):
        return {'DEMO_SYNTHETIC':True,'calendarDate':cdate,'totalSteps':6240,'totalDistanceMeters':4720,
                'totalKilocalories':2340,'activeKilocalories':510,'restingHeartRate':57,'missingExample':None}
    def get_heart_rates(self,cdate):
        t=int(datetime.fromisoformat(cdate).replace(tzinfo=timezone.utc).timestamp()*1000)
        return {'DEMO_SYNTHETIC':True,'calendarDate':cdate,'restingHeartRate':57,'maxHeartRate':122,
                'heartRateValues':[[t,60],[t+120000,64],[t+240000,None]],'startTimestampGMT':cdate+'T00:00:00.000'}
    def get_sleep_data(self,cdate):
        return {'DEMO_SYNTHETIC':True,'dailySleepDTO':{'calendarDate':cdate,'sleepTimeSeconds':25200,'deepSleepSeconds':5400,
                'remSleepSeconds':4800,'lightSleepSeconds':15000},'sleepLevels':[{'startGMT':cdate+'T00:00:00','endGMT':cdate+'T01:30:00','activityLevel':0}]}

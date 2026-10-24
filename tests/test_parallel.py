"""Parallel retrieval: same archive contents, one shared request interval, clean stop on 429."""
import threading
import time
from engine import Plan, Exporter, account_key
from offline import ArchiveSync
from archive import Archive
from demo_data import DemoGarmin


class Api(DemoGarmin):
    """Synthetic API with latency, activity extras and a thread-safe call log."""
    latency = 0.0

    def __init__(self):
        self.lock = threading.Lock(); self.log = []

    def note(self, name):
        with self.lock: self.log.append((time.monotonic(), name))
        if self.latency: time.sleep(self.latency)

    def get_user_summary(self, cdate):
        self.note('summary'); return super().get_user_summary(cdate)

    def get_heart_rates(self, cdate):
        self.note('heart_rate'); return super().get_heart_rates(cdate)

    def get_sleep_data(self, cdate):
        self.note('sleep'); return super().get_sleep_data(cdate)

    def search_activities(self, start=0, limit=100, **filters):
        self.note('activities')
        return [dict(a, activityId=a['activityId']) for a in super().search_activities(start, limit, **filters)][:2] if start == 0 else []

    def get_activity_splits(self, ident):
        self.note('splits'); return {'activityId': ident, 'splits': [1, 2]}

    def get_activity_weather(self, ident):
        self.note('weather'); return {'activityId': ident, 'temp': 12}

    def download_activity(self, ident, dl_fmt=None):
        self.note('file'); return b'PK-synthetic-' + str(ident).encode()


def plan(tmp_path, name, **kwargs):
    values = dict(start='2020-01-01', end='2020-01-10', datasets=['summary', 'heart_rate', 'sleep', 'activities'],
                  output=str(tmp_path / name), account=account_key('parallel@example.invalid'),
                  archive_path=str(tmp_path / (name + '.sqlite')), delay=0, refresh_days=0, optimize=False,
                  activity_details=['get_activity_splits', 'get_activity_weather'], activity_files=['ORIGINAL'])
    return Plan(**(values | kwargs))


def archive_contents(path):
    with Archive(path, readonly=True) as db:
        return sorted((r['dataset'], r['day'], r['request_json'], bytes(r['payload']))
                      for r in db.db.execute('SELECT * FROM responses'))


def test_parallel_archive_is_identical_to_sequential(tmp_path):
    sequential = ArchiveSync(Api(), plan(tmp_path, 'seq', workers=1)).run_sync()
    parallel_api = Api()
    parallel = ArchiveSync(parallel_api, plan(tmp_path, 'par', workers=4)).run_sync()
    assert sequential['report']['completed'] and parallel['report']['completed']
    assert parallel['report']['transfer']['parallel_requests'] > 0
    strip = lambda rows: [r for r in rows if r[0] != 'activity_types']
    assert strip(archive_contents(tmp_path / 'seq.sqlite')) == strip(archive_contents(tmp_path / 'par.sqlite'))
    # 10 days x (summary, heart rate, sleep, activity list) + 10 days x 2 activities x 3 extras.
    assert parallel['report']['stats']['downloaded'] == 1 + 10 * 4 + 10 * 2 * 3  # + sport taxonomy


def test_parallel_export_files_match_sequential(tmp_path):
    a = Exporter(Api(), plan(tmp_path, 'a', workers=1, formats=['json', 'csv'], activity_files=[]))
    b = Exporter(Api(), plan(tmp_path, 'b', workers=4, formats=['json', 'csv'], activity_files=[]))
    out_a, report_a = a.run(); out_b, report_b = b.run()
    assert report_a['completed'] and report_b['completed']
    from pathlib import Path
    files = sorted(p.name for p in Path(out_a).iterdir() if p.name != 'report.json')
    assert files == sorted(p.name for p in Path(out_b).iterdir() if p.name != 'report.json')
    for name in files:
        assert (Path(out_a) / name).read_bytes() == (Path(out_b) / name).read_bytes()


def test_interval_is_shared_by_all_workers(tmp_path):
    api = Api()
    p = plan(tmp_path, 'gap', workers=4, delay=0.04, datasets=['heart_rate', 'sleep'], end='2020-01-06',
             activity_details=[], activity_files=[])
    assert ArchiveSync(api, p).run_sync()['report']['completed']
    starts = sorted(t for t, _ in api.log)
    assert len(starts) == 12
    assert min(b - a for a, b in zip(starts, starts[1:])) >= 0.035


def test_workers_overlap_slow_requests(tmp_path):
    def duration(workers):
        api = Api(); api.latency = 0.05
        p = plan(tmp_path, f'speed{workers}', workers=workers, datasets=['heart_rate', 'sleep'], end='2020-01-12',
                 activity_details=[], activity_files=[])
        began = time.monotonic(); report = ArchiveSync(api, p).run_sync()['report']
        assert report['completed'] and len(api.log) == 24
        return time.monotonic() - began
    assert duration(4) < duration(1) * 0.6


def test_rate_limit_in_worker_stops_new_requests_and_keeps_saved_data(tmp_path):
    from garminconnect import GarminConnectTooManyRequestsError

    class Limited(Api):
        def get_heart_rates(self, cdate):
            self.note('heart_rate')
            if cdate == '2020-01-04': raise GarminConnectTooManyRequestsError('429')
            return DemoGarmin.get_heart_rates(self, cdate)

    api = Limited(); api.latency = 0.01
    p = plan(tmp_path, 'limit', workers=3, datasets=['heart_rate', 'sleep'], end='2020-01-20',
             activity_details=[], activity_files=[])
    result = ArchiveSync(api, p).run_sync()
    report = result['report']
    assert report['fatal_diagnostic']['reason'] == 'rate_limit' and not report['completed']
    # Workers already waiting may finish, but nothing near the full workload is requested.
    assert len(api.log) <= 4 + 3 * 2
    assert not [name for _, name in api.log if name == 'sleep']
    with Archive(p.archive_path, readonly=True) as db:
        days = {r['day'] for r in db.db.execute("SELECT day FROM responses WHERE dataset='heart_rate'")}
    assert {'2020-01-01', '2020-01-02', '2020-01-03'} <= days and '2020-01-04' not in days


def test_skipped_days_after_rejected_method_are_recorded_for_repair(tmp_path):
    from garminconnect import GarminConnectConnectionError

    class Rejects(Api):
        def get_user_summary(self, cdate):
            self.note('summary'); raise GarminConnectConnectionError('API Error 400')

    for workers in (1, 3):
        p = plan(tmp_path, f'skip{workers}', workers=workers, datasets=['summary'], end='2020-01-05',
                 activity_details=[], activity_files=[])
        report = ArchiveSync(Rejects(), p).run_sync()['report']
        assert report['blocked_methods'] == ['get_user_summary']
        with Archive(p.archive_path, readonly=True) as db:
            missing = {r['day'] for r in db.db.execute("SELECT day FROM attempts WHERE dataset='summary'")}
        assert missing == {f'2020-01-0{i}' for i in range(1, 6)}
        assert report['stats']['errors'] + report['stats']['skipped'] == 5


def test_activity_outside_one_batch_does_not_disable_later_batches(tmp_path):
    class Shifted(Api):
        def search_activities(self, start=0, limit=100, **filters):
            if start: return []  # Count first-page calls only.
            self.note('activities')
            day = filters['startDate']
            if filters['startDate'] != filters['endDate'] and day == '2020-01-01':
                # One activity reported with a local date before the requested batch.
                return [{'activityId': 1, 'startTimeLocal': '2019-12-31 23:30:00', 'activityType': {'typeKey': 'running'}}]
            return [{'activityId': int(day.replace('-', '')), 'startTimeLocal': day + ' 10:00:00',
                     'activityType': {'typeKey': 'running'}}]

    api = Shifted()
    p = plan(tmp_path, 'shift', start='2020-01-01', end='2020-01-20', datasets=['activities'], optimize=True,
             activity_batch_days=10, activity_details=[], activity_files=[])
    exporter = Exporter(api, p); exporter.run()
    assert 'activities' not in exporter.range_disabled
    # First batch: 1 failed range call + 10 daily calls; second batch: one range call.
    assert len([n for _, n in api.log if n == 'activities']) == 1 + 10 + 1


def test_daily_wellness_fit_is_stored_resumed_and_exported_as_file(tmp_path):
    from offline import OfflineExporter
    from dataclasses import replace
    api = Api(); calls = []
    api.download_health_snapshot = lambda day: calls.append(day) or b'PK\x03\x04synthetic-' + day.encode()
    p = plan(tmp_path, 'fit', datasets=['wellness_fit'], end='2020-01-05', workers=3,
             activity_details=[], activity_files=[])
    first = ArchiveSync(api, p).run_sync()['report']
    assert first['completed'] and len(calls) == 5
    again = ArchiveSync(api, p).run_sync()['report']
    assert again['completed'] and len(calls) == 5 and again['stats']['cached'] == 5  # resumable, no re-download
    out, report = OfflineExporter(replace(p, source='offline', formats=['json'])).run()
    from pathlib import Path
    files = sorted(Path(out, 'wellness_fit').iterdir())
    assert report['completed'] and len(files) == 5 and files[0].read_bytes().startswith(b'PK')


def test_successes_after_earlier_failure_are_saved(tmp_path):
    from garminconnect import GarminConnectTooManyRequestsError
    for archive in (False, True):
        barrier=threading.Barrier(3)
        class FailsFirst(Api):
            def get_heart_rates(self, day):
                self.note(day)
                barrier.wait(timeout=5)
                if day=='2020-01-01':raise GarminConnectTooManyRequestsError('429')
                time.sleep(.03)
                return DemoGarmin.get_heart_rates(self,day)
        api=FailsFirst()
        p=plan(tmp_path,f'late-{archive}',workers=3,datasets=['heart_rate'],end='2020-01-03',activity_details=[],activity_files=[])
        if archive:
            report=ArchiveSync(api,p).run_sync()['report']
            with Archive(p.archive_path,readonly=True) as db:
                saved={r['day'] for r in db.db.execute("SELECT day FROM responses WHERE dataset='heart_rate'")}
        else:
            _,report=Exporter(api,p).run()
            saved={r['date'] for r in report['records']}
        assert not report['completed'] and report['fatal_diagnostic']['reason']=='rate_limit'
        assert saved=={'2020-01-02','2020-01-03'}
        assert report['stats']['downloaded']==2+int(archive) and len(api.log)==3


def test_stop_preserves_inflight_successes(tmp_path):
    for archive in (False,True):
        cancel=threading.Event();barrier=threading.Barrier(3)
        class Stops(Api):
            def get_heart_rates(self,day):
                self.note(day);barrier.wait(timeout=5);cancel.set()
                return DemoGarmin.get_heart_rates(self,day)
        p=plan(tmp_path,f'stop-{archive}',workers=3,datasets=['heart_rate'],end='2020-01-03',activity_details=[],activity_files=[])
        if archive:
            report=ArchiveSync(Stops(),p,cancel).run_sync()['report']
            with Archive(p.archive_path,readonly=True) as db:
                assert db.db.execute("SELECT COUNT(*) FROM responses WHERE dataset='heart_rate'").fetchone()[0]==3
        else:
            _,report=Exporter(Stops(),p,cancel).run()
            assert len(report['records'])==3
        assert report['cancelled'] and not report['completed'] and report['stats']['downloaded']==3+int(archive)


def test_exporter_records_parallel_wall_clock_costs_for_remaining_time(tmp_path):
    api=Api();api.latency=.01
    p=plan(tmp_path,'eta',workers=3,datasets=['heart_rate'],end='2020-01-06',activity_details=[],activity_files=[])
    exporter=Exporter(api,p);_,report=exporter.run()
    assert report['completed'] and exporter.eta.workers==3
    assert 'heart_rate' in exporter.eta.parallel_families
    assert exporter.eta.parallel_samples['heart_rate']
    assert sum(exporter.eta.pending.values())==0


def test_rate_limit_is_kept_when_saving_completed_responses_also_fails(tmp_path, monkeypatch):
    from garminconnect import GarminConnectTooManyRequestsError

    class Limited(Api):
        def get_heart_rates(self, cdate):
            self.note('heart_rate')
            if cdate == '2020-01-02': raise GarminConnectTooManyRequestsError('429')
            return DemoGarmin.get_heart_rates(self, cdate)

    p = plan(tmp_path, 'keep', workers=3, datasets=['heart_rate'], end='2020-01-08', activity_details=[], activity_files=[])
    sync = ArchiveSync(Limited(), p)
    monkeypatch.setattr(sync, 'save_staged_successes', lambda: (_ for _ in ()).throw(OSError('disk full')))
    report = sync.run_sync()['report']
    assert report['fatal_diagnostic']['reason'] == 'rate_limit'
    assert 'save_after_error_failed:OSError' in report['warnings']
    exporter = Exporter(Limited(), plan(tmp_path, 'keep-export', workers=3, datasets=['heart_rate'], end='2020-01-08',
                                        activity_details=[], activity_files=[], formats=['json']))
    monkeypatch.setattr(exporter, 'save_staged_successes', lambda: (_ for _ in ()).throw(OSError('disk full')))
    _, export_report = exporter.run()
    assert export_report['fatal_diagnostic']['reason'] == 'rate_limit'


def test_rate_limit_event_precedes_final_report_write_failures(tmp_path,monkeypatch):
    import pytest,engine
    from garminconnect import GarminConnectTooManyRequestsError,GarminConnectConnectionError
    from archive import Archive
    for use_archive in (False,True):
        for exception in (GarminConnectTooManyRequestsError('429'),GarminConnectConnectionError('API Error 429')):
            events=[]
            p=plan(tmp_path,f'failed-report-{use_archive}-{type(exception).__name__}',datasets=['heart_rate'],end='2020-01-01',activity_details=[],activity_files=[])
            exporter=(ArchiveSync if use_archive else Exporter)(Api(),p,event=lambda *e:events.append(e))
            def fail():raise exception
            exporter.collect=lambda:exporter.call(fail)
            with monkeypatch.context() as patch:
                if use_archive:patch.setattr(Archive,'record_run',lambda *args:(_ for _ in ()).throw(OSError('full')))
                else:patch.setattr(engine,'atomic_json',lambda *args:(_ for _ in ()).throw(OSError('full')))
                with pytest.raises(OSError):
                    exporter.run_sync() if use_archive else exporter.run()
            rate_events=[e[1] for e in events if e[0]=='rate_limit']
            assert rate_events and rate_events[0]['reason']=='rate_limit'

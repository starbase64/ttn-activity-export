"""Curated, read-only Garmin exports. Labels are deliberately independent of API keys."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Dataset:
    key: str
    de: str
    en: str
    method: str
    kind: str = 'day'  # day, range, account

DATASETS = [
    Dataset('summary', 'Tagesübersicht', 'Daily summary', 'get_user_summary'),
    Dataset('heart_rate', 'Puls – Tageswerte und Verlauf', 'Heart rate – summary and timeline', 'get_heart_rates'),
    Dataset('sleep', 'Schlaf – Werte und Phasen', 'Sleep – summary and stages', 'get_sleep_data'),
    Dataset('stress', 'Stress – Werte und Verlauf', 'Stress – summary and timeline', 'get_stress_data'),
    Dataset('body_battery', 'Body Battery – Verlauf', 'Body Battery – timeline', 'get_body_battery', 'range'),
    Dataset('body_battery_events', 'Body Battery – Ereignisse', 'Body Battery – events', 'get_body_battery_events'),
    Dataset('steps', 'Schritte – Verlauf', 'Steps – timeline', 'get_steps_data'),
    Dataset('floors', 'Etagen', 'Floors', 'get_floors'),
    Dataset('intensity', 'Intensitätsminuten', 'Intensity minutes', 'get_intensity_minutes_data'),
    Dataset('respiration', 'Atemfrequenz', 'Respiration', 'get_respiration_data'),
    Dataset('spo2', 'Sauerstoffsättigung (SpO₂)', 'Oxygen saturation (SpO₂)', 'get_spo2_data'),
    Dataset('hrv', 'Herzfrequenzvariabilität (HRV)', 'Heart rate variability (HRV)', 'get_hrv_data'),
    Dataset('resting_hr', 'Ruhepuls', 'Resting heart rate', 'get_rhr_day'),
    Dataset('weight', 'Gewicht – einzelne Messungen', 'Weight – individual readings', 'get_daily_weigh_ins'),
    Dataset('body', 'Körperzusammensetzung', 'Body composition', 'get_body_composition', 'range'),
    Dataset('blood_pressure', 'Blutdruck', 'Blood pressure', 'get_blood_pressure', 'range'),
    Dataset('hydration', 'Trinkmenge', 'Hydration', 'get_hydration_data'),
    Dataset('training_status', 'Trainingsstatus', 'Training status', 'get_daily_training_status'),
    Dataset('readiness', 'Trainingsbereitschaft', 'Training readiness', 'get_training_readiness'),
    Dataset('vo2max', 'VO₂max / maximale Leistungswerte', 'VO₂max / maximum metrics', 'get_max_metrics'),
    Dataset('fitness_age', 'Fitnessalter', 'Fitness age', 'get_fitnessage_data'),
    Dataset('endurance', 'Ausdauerwert', 'Endurance score', 'get_endurance_score', 'range'),
    Dataset('hill', 'Hill Score', 'Hill score', 'get_hill_score', 'range'),
    Dataset('activities', 'Aktivitäten – Übersicht', 'Activities – summary', 'get_activities_by_date', 'range'),
    Dataset('devices', 'Geräte (aktueller Stand)', 'Devices (current snapshot)', 'get_devices', 'account'),
    Dataset('records', 'Persönliche Rekorde (aktueller Stand)', 'Personal records (current snapshot)', 'get_personal_record', 'account'),
    Dataset('goals', 'Aktive Ziele (aktueller Stand)', 'Active goals (current snapshot)', 'get_goals', 'account'),
]
ACTIVITY_DETAILS = {
    'get_activity_details': ('Messverläufe (Garmin-Auflösung)', 'Metric timelines (Garmin resolution)'),
    'get_activity_laps': ('Runden', 'Laps'),
    'get_activity_splits': ('Zwischenzeiten', 'Splits'),
    'get_activity_hr_in_timezones': ('Herzfrequenzzonen', 'Heart rate zones'),
    'get_activity_exercise_sets': ('Trainingssätze', 'Exercise sets'),
    'get_activity_weather': ('Wetter', 'Weather'),
}

# Statistics are separate resources: never let a short daily series satisfy a
# request for a detailed timeline (or overwrite its existing cache/archive).
DAILY_METHODS = {
    'heart_rate': 'get_daily_heart_rate_stats',
    'sleep': 'get_sleep_daily',
    'stress': 'get_daily_stress_stats',
    'body_battery': 'get_daily_body_battery_stats',
    'steps': 'get_daily_steps',
    'floors': 'get_daily_floors_stats',
    'intensity': 'get_daily_intensity_minutes_stats',
    'respiration': 'get_daily_respiration_stats',
    'hydration': 'get_daily_hydration_stats',
    'resting_hr': 'get_rhr_daily',
}
DAILY_DATASETS = [Dataset(d.key+'-daily',d.de.split(' – ')[0]+' – Tageskennzahlen',d.en.split(' – ')[0]+' – daily statistics',
                          DAILY_METHODS[d.key],'range') for d in DATASETS if d.key in DAILY_METHODS]

def selected_datasets(plan):
    daily={d.key.removesuffix('-daily'):d for d in DAILY_DATASETS}
    return [daily.get(d.key,d) if plan.health_detail=='daily' else d for d in DATASETS if d.key in plan.datasets]

def all_definitions():
    return DATASETS+DAILY_DATASETS

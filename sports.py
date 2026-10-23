"""Garmin activity type keys with bilingual labels; unknown keys remain selectable."""
# A small offline fallback. A successful Garmin response replaces it with the full taxonomy.
SPORT_LABELS = {
 'running': ('Laufen', 'Running'),
 'cycling': ('Radfahren', 'Cycling'),
 'walking': ('Gehen', 'Walking'),
 'hiking': ('Wandern', 'Hiking'),
 'swimming': ('Schwimmen', 'Swimming'),
 'lap_swimming': ('Schwimmen im Schwimmbad', 'Pool swimming'),
 'open_water_swimming': ('Freiwasserschwimmen', 'Open water swimming'),
 'trail_running': ('Trailrunning', 'Trail running'),
 'treadmill_running': ('Laufband', 'Treadmill running'),
 'track_running': ('Bahntraining', 'Track running'),
 'indoor_running': ('Indoor-Laufen', 'Indoor running'),
 'ultra_run': ('Ultralauf', 'Ultra running'),
 'virtual_run': ('Virtuelles Laufen', 'Virtual running'),
 'mountain_biking': ('Mountainbike', 'Mountain biking'),
 'road_biking': ('Rennrad', 'Road cycling'),
 'gravel_cycling': ('Gravelbike', 'Gravel cycling'),
 'indoor_cycling': ('Indoor-Radfahren', 'Indoor cycling'),
 'virtual_ride': ('Virtuelle Radfahrt', 'Virtual ride'),
 'e_bike_fitness': ('E-Bike', 'E-bike'),
 'e_bike_mountain': ('E-Mountainbike', 'E-mountain bike'),
 'bike_commuting': ('Pendeln mit dem Rad', 'Bike commuting'),
 'fitness_equipment': ('Fitnesstraining', 'Fitness equipment'),
 'strength_training': ('Krafttraining', 'Strength training'),
 'cardio_training': ('Cardiotraining', 'Cardio training'),
 'elliptical': ('Crosstrainer', 'Elliptical'),
 'stair_climbing': ('Treppensteigen', 'Stair climbing'),
 'indoor_rowing': ('Indoor-Rudern', 'Indoor rowing'),
 'rowing': ('Rudern', 'Rowing'),
 'yoga': ('Yoga', 'Yoga'),
 'pilates': ('Pilates', 'Pilates'),
 'breathwork': ('Atemübungen', 'Breathwork'),
 'meditation': ('Meditation', 'Meditation'),
 'hiit': ('HIIT', 'HIIT'),
 'multi_sport': ('Multisport', 'Multisport'),
 'triathlon': ('Triathlon', 'Triathlon'),
 'duathlon': ('Duathlon', 'Duathlon'),
 'transition': ('Wechselzone', 'Transition'),
 'other': ('Sonstige', 'Other'),
 'golf': ('Golf', 'Golf'),
 'tennis': ('Tennis', 'Tennis'),
 'table_tennis': ('Tischtennis', 'Table tennis'),
 'badminton': ('Badminton', 'Badminton'),
 'squash': ('Squash', 'Squash'),
 'pickleball': ('Pickleball', 'Pickleball'),
 'padel': ('Padel', 'Padel'),
 'soccer': ('Fußball', 'Soccer'),
 'basketball': ('Basketball', 'Basketball'),
 'volleyball': ('Volleyball', 'Volleyball'),
 'boxing': ('Boxen', 'Boxing'),
 'martial_arts': ('Kampfsport', 'Martial arts'),
 'climbing': ('Klettern', 'Climbing'),
 'indoor_climbing': ('Indoor-Klettern', 'Indoor climbing'),
 'bouldering': ('Bouldern', 'Bouldering'),
 'mountaineering': ('Bergsteigen', 'Mountaineering'),
 'kayaking': ('Kajak', 'Kayaking'),
 'canoeing': ('Kanufahren', 'Canoeing'),
 'stand_up_paddleboarding': ('Stand-up-Paddeln', 'Stand-up paddleboarding'),
 'sailing': ('Segeln', 'Sailing'),
 'surfing': ('Surfen', 'Surfing'),
 'windsurfing': ('Windsurfen', 'Windsurfing'),
 'water_skiing': ('Wasserski', 'Water skiing'),
 'downhill_skiing': ('Ski Alpin', 'Downhill skiing'),
 'cross_country_skiing': ('Skilanglauf', 'Cross-country skiing'),
 'resort_skiing_snowboarding': ('Ski / Snowboard', 'Skiing / snowboarding'),
 'snowboarding': ('Snowboarden', 'Snowboarding'),
 'snow_shoe': ('Schneeschuhwandern', 'Snowshoeing'),
 'ice_skating': ('Eislaufen', 'Ice skating'),
 'inline_skating': ('Inlineskaten', 'Inline skating'),
 'horseback_riding': ('Reiten', 'Horseback riding'),
 'fishing': ('Angeln', 'Fishing'),
 'hunting': ('Jagen', 'Hunting'),
 'diving': ('Tauchen', 'Diving'),
 'jump_rope': ('Seilspringen', 'Jump rope'),
 'dance': ('Tanzen', 'Dance'),
 'wheelchair_push_walk': ('Rollstuhl – Gehen', 'Wheelchair push walk'),
 'wheelchair_push_run': ('Rollstuhl – Laufen', 'Wheelchair push run'),
}
FALLBACK_SPORTS = ('running','cycling','walking','hiking','swimming','fitness_equipment','multi_sport','other')


def activity_type_keys(payload):
    """Read flat Garmin arrays or wrapped responses without assuming type IDs."""
    found = set()
    def visit(value):
        if isinstance(value, dict):
            key = value.get('typeKey') or value.get('activityTypeKey')
            if isinstance(key, str) and key.strip():
                found.add(key.strip())
            for child in value.values():
                if isinstance(child, (dict, list)):
                    visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
    visit(payload)
    return sorted(found)


def sport_label(key, language):
    pair = SPORT_LABELS.get(key)
    title = pair[0 if language == 'de' else 1] if pair else key.replace('_', ' ').capitalize()
    # Keeping the exact key visible makes unrecognized/new Garmin types unambiguous.
    return f'{title} ({key})'

# Garmin uses this key for E-MTB activities. Keep the older fallback key as an alias.
SPORT_LABELS["e_bike_mountain"] = ("E-Mountainbike", "E-mountain bike")

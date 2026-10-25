"""Public identity and report compatibility; storage profile deliberately stays stable."""
APP_NAME = 'TTN Activity Export'
APP_ID = 'ttn-activity-export'
REPORT_APP_IDS = (APP_ID, 'ttn-garmin-export')
# Preserve QStandardPaths locations for sessions, preferences, dates, logs and pauses.
STORAGE_PROFILE = 'GarminExportStudio'

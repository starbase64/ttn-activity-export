# Validation — 0.5.0-preview

2026-10-23 · prepared on Linux / Python 3.12.

- 106 tests passed, including existing export/offline/map/UI tests and new starter packaging, missing/corrupt-file repair, no redundant download, wheel traversal rejection and SHA-256 mismatch tests.
- App --smoke-test passed with the renamed application; legacy internal profile remains for session compatibility.
- Official Python 3.13.16 Windows x64 embeddable archive downloaded and SHA-256 matched against Python.org.
- All 20 resolved Windows wheels checked against PyPI's published SHA-256, installed with the bootstrap's actual wheel installer and reverified from disk. Required Qt, platform plugin, WebEngine process and CFFI files present. No preinstalled system Python needed by the distributed starter.
- First-time setup, offline restart and cached missing-package repair have a native Windows CI workflow. See the Actions run for this commit for actual execution status; local Linux checks do not prove Windows execution.
- No Garmin account traffic during these tests, no universal download acceleration claimed. Existing full-detail archive behavior remains.

Earlier validation history follows:

# Validation — 0.4.0-preview

2026-10-23 · Linux, Python 3.12, PySide6 6.12.0.

- 99 tests passed; app --smoke-test exit 0. Existing download, rate-stop, preview, archive, import, repair, map, log, UI and export tests retained.
- Synthetic full daily-summary fixture: 56 days, two 28-day API calls instead of 56 daily calls. Every field, nested value, null and day retained; disabling batching after that causes zero requests due to compatible daily fingerprints. Old daily cache imports and offline export verified.
- All ten daily-statistics adapters: 56 days in two library calls each with one dated record per day. Generic CSV/JSON output, separate -daily resources, cache resumption, archive coexistence, strict offline export and missing-full-detail behavior checked. This is an API-call-count result on synthetic fixtures, not a measured live speedup.
- Missing range dates trigger individual checks. Empty series require single-day checks before persisting empties. Foreign dates reject batch before storage. HTTP 400 range fallback stays on the statistics endpoint; 401/403/429 stop without extra requests.
- Daily preview has a strict request budget and does not fetch the complete interval or create cache files. Missing-data repair selects matching statistics resources. Health table reads supported daily statistics fields. Old presets default to full detail; new settings roundtrip. All-data archive button explicitly retains full detail.
- Default output uses QStandardPaths.DownloadLocation/Garmin_Export. Test redirects Downloads and verifies output; actual Windows known-folder lookup not executed here.
- German/English UI checked at 150% scale, 1180×1000 and 900×650 logical window sizes. Output controls retain styled minimum heights; small Export pages scroll. Synthetic screenshots use an example path and no Garmin account data.
- No dependency changes. Windows update overlays the existing portable 0.2/0.3 runtime. Source and ZIP contents statically checked. No Windows execution or live Garmin range/data-schema verification. No universal speedup claim; detailed health endpoints still run daily. Monitoring FIT ingestion and lossless HRV range adaptation remain deferred.

Earlier validation history follows:

# Validation — 0.3.0-preview

2026-10-23 · Linux, Python 3.12, PySide6 6.12.0.

- `python -m pytest -q`: **74 passed**, exit 0.
- `QT_QPA_PLATFORM=offscreen python app.py --smoke-test`: exit 0.
- Body Battery fixture, 14 days: 2 app API calls instead of 14 with optimization disabled; all 14 original daily records preserved. Existing old daily cache and SQLite archive reuse verified, with zero requests on a warm historical run.
- Activity fixture, 14 days / 420 activities: 6 paginated range calls instead of 28 daily calls (including explicit empty terminal pages); every activity retained under its original day.
- Additional tests: truncated range dates fetched individually; one daily fallback after rejected range; no fallback/extra requests after HTTP 429; activity date-filter validation; cancellation/resumption retaining completed days; offline archive exports without network.
- ETA tests cover measured request timing, cache weighting, newly discovered slow file work, provisional activity counts, retry countdown, rate-limit stop, and local export completion. Selected-category archive sync tested. Preset and prior UI/backup/import/map tests retained.
- Synthetic DE/EN ETA screenshots visually inspected; no account data in source/update packages.
- Windows update is an overlay for the previously assembled portable 0.2 runtime. No dependency changes. Source compile/smoke tests passed here; Windows execution and live Garmin range calls were not tested. Detailed daily health endpoints remain daily, default pacing is unchanged; no universal speedup factor is claimed.

Previous 0.2 validation notes follow for unchanged features:

# Validation — 0.2.0-preview

Date: 2026-10-23. Host: Linux, Python 3.12, PySide6 6.12.0.

- `python -m pytest -q`: **63 passed**, exit 0.
- `QT_QPA_PLATFORM=offscreen python app.py --smoke-test`: exit 0. Online synthetic export, SQLite sync, offline export/preview, actual GPX import, archive backup/integrity, bilingual UI, map rendering and PNG output.
- New integration tests cover valid binary FIT decoding with CRC, segmented GPX, nested Garmin activity ZIPs without disk extraction, duplicate handling, partial imported days, offline export, formula-safe CSV/XLSX, native JSON, health units, missing readings, SQLite reopen/backup, account mismatch, targeted GPS repair, forced failed-request retry, 429 stop, cache migration, route-frequency normalization and approximate route matching.
- Qt tests exercise actual Ctrl/Shift clicks, checkbox/row selection sync, filters, DE/EN with selection retained, lazy background GPS loading, missing-track handling, image export, masking, persistent logs beyond 500 lines/clear and bounded oldest-date lookup.
- Synthetic DE/EN data page and checkbox screenshots visually inspected. Data page scrolls at smaller sizes. No real account data used in screenshots or package.
- Windows portable bundle: official Python 3.13.16 x64 archive SHA-256 checked against Python.org; Windows-targeted wheels extracted with full metadata/licenses, paths, x64 executables, platform plugin, QtWebEngine and native CFFI files checked. Dependency SHA-256 manifest included. **Not executed on Windows here.**
- GitHub/PyInstaller workflow is provided but not run here. No live Garmin multi-year sync, Google Maps API-key rendering, OSM network-tile session, My Maps upload/link creation or Windows launch was tested here. No claim of complete Garmin account recovery from official account ZIPs; only supported activity files are imported.

## 0.3.1 output layout hotfix

74 existing tests passed, followed by the app smoke test. Offscreen PySide6 layout checks at QT_SCALE_FACTOR=1.5 verified that all Output input/button/combo/checkbox heights meet their styled size hints in German and English, at 1180×870 and 900×650 logical window sizes. Export contents remain accessible by scrolling. Screenshots output-v031-*.png contain no Garmin account data. No Windows execution or live Garmin request was performed.

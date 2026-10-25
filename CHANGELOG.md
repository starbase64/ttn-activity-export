# 0.6.6-preview · Strava TCX import and Komoot inventory

- Accept ASCII whitespace before an XML declaration in TCX/GPX parsing. This handles indented TCX recordings in downloaded Strava archives while preserving original file bytes and the parser-level DTD/entity protection.
- Re-importing the same package repairs missing recording files without duplicating existing activity summaries.
- Use provider-aware Komoot inventory errors and keep Komoot failures separate from Garmin rate pauses. Request tour lists with page, limit and an optional nonempty type; apply date filters locally to reduce endpoint filter incompatibilities. HTTP 400 on the user account still requires a live retest.
- Add a synthetic regression test for an indented TCX file, byte-preserving storage, repeat import and unchanged XML declaration security checks. No user activity data is included in the repository or build.

# 0.6.5-preview · account-specific data views

- Prefix the Data selection summary with the total number of local activities, retaining selection/track counts and showing the visible count when filters narrow the list. Keep the total visible while GPS is loaded; translate both languages.
- Selecting Garmin, Komoot or Strava immediately switches the Data source to the account’s saved/custom archive or managed default location. Clear the previous table, map and account filters; automatically load an existing matching archive without authentication or network requests. Missing archives show an empty state and intended path, without creating a database.
- Create each provider/account storage directory when registering an account; reject unwritable targets without saving a broken account entry.
- Accept German/English Strava CSV headers, comma/semicolon/tab delimiters, decimal commas and explicit German date formats while preserving original columns. Add allowlisted translated import errors for unsupported headers, missing lists, corrupt ZIPs and size/copy limits; do not expose arbitrary exception text.
- Remember chosen archive paths per account. Validate archive ownership and reject stale results after rapid account switches; existing work finishes before a deferred local read starts.

# 0.6.4-preview · cache discovery and consistent names

- Search known account destinations, prior standard folders and current archive paths for matching Garmin SQLite archives and legacy cache-v1 response folders. Search in a bounded background task without network requests; open/import a single match directly, offer a choice for multiple matches, and show the manual folder picker only when no matching data was found. Never merge another account’s data or overwrite an already stored response when importing an older cache.
- Remove the obsolete compatibility CMD launcher from source and Windows packages. Use TTN_Activity_Export as the new Downloads directory, with provider/account subfolders. Retain existing saved paths and legacy report readers to preserve previous data and sessions.
- Document actual platform status: Windows x64 starter tested, source/tests run on Linux, no validated macOS build and no Android/iOS application.

# 0.6.3-preview · OSM defaults, inventory layout and experimental Komoot

- Enable OSM basemaps by default in Data; retain the offline toggle. Draw the empty GPS-selection hint as black text on an opaque white panel over map imagery. Demo maps do not send tile requests.
- Size online-inventory columns to all loaded contents initially. Preserve manual widths and movable headers, provide pixel-based horizontal scrolling and a native maximize button.
- Add a read-only experimental Komoot connector: memory-only email/password sign-in, token-only subsequent requests, bounded paged inventory for recorded/planned tours, explicit selected-tour review, metadata-only or GPX download, account-isolated SQLite and GPX files, cached GPX reuse and persistent per-account 429 pauses. No web scraping, region/CAPTCHA bypass or background retries. Keep Komoot separate from Garmin's persistent job queue in this preview.
- Use Komoot source links in readable exports and allow local Data date filters to include future planned routes. No new runtime dependencies. Synthetic tests only; a live Komoot account and real Strava package still need user validation.

# 0.6.2-preview · Strava folders and source retention

- Accept extracted Strava account folders as well as ZIPs, using the same CSV/recording import path. Read source folders without following symbolic links.
- Ask whether to leave the source in place or retain a complete copy in the account folder. Copy in a cancellable worker to a new directory; remove partial copies on failure and never merge or overwrite source data. Remember the retained source location separately from the local activity database. Full source copies are limited to 8 GiB.
- Unify new default destinations under Downloads/TTN Activity Export/provider/account-ID. Preserve saved custom paths and existing archives.

# 0.6.1-preview · Strava is a local import source

- Keep Strava account entries, but replace the connection placeholder with a local-only account-ZIP workflow. No Strava online sign-in, API keys, budgets, scraping or automatic website/API retrieval are offered or planned.
- Stream a user-selected Strava ZIP: parse activities.csv with duplicate-column preservation, import referenced FIT/GPX/TCX recordings including bounded gzip decoding, keep metadata-only activities, and report missing/corrupt/unsupported records. Never extract archive paths to disk. Ignore non-activity account content.
- Store source activity IDs/provider and update repeated imports idempotently in an account-isolated SQLite database. Keep the original ZIP untouched. Local import works during a Garmin request pause and opens the existing local filter/map/CSV/XLSX/JSON-selection export tools.
- Use a provider-neutral Activity link column with the correct Strava source URL; invalidate readable activity-table output signatures once so old Garmin-link headers are rebuilt. Other dataset signatures remain unchanged.
- Document manual download/import steps, timezone and unit uncertainty, limits and the distinction from a full account backup. Synthetic coverage is not a real-account/package validation.

# 0.6.0-preview · compact desktop and explicit jobs

- Introduce four primary tabs: Accounts, Download, Data, User guide. Move detailed export/retrieval settings, fields, Expert and offline management into an Apply/Cancel dialog; move the full session log into a separate window. Add a persistent global tooltip toggle.
- Add account metadata and explicit saved defaults, isolated Garmin client sessions, provider-specific default destinations for new accounts and migration of the existing remembered Garmin account without moving old archives. Komoot and Strava entries are clearly marked as not connected/implemented; no live API support is claimed.
- Add a bounded, resumable Garmin activity metadata inventory with search/sport filters, Ctrl/Shift selection, partial/complete states, timestamps and account/date-scoped local caching. No per-activity details, files or maps are requested by listing.
- Add activity-ID selection throughout online/offline collection and output signatures. Preserve unfiltered summary caches for later selections. Missing chosen IDs make the result incomplete.
- Persist immutable job snapshots and their order/status. Interrupted work waits for manual review after restart. Review shows dates, scope, paths, formats, extras, local base-request planning and time-estimation limitations. Rejecting review does not start work. Other ready Garmin jobs can proceed past missing-login jobs.
- Preserve legacy controls and engine behavior beneath the new shell, use no additional runtime dependency, keep the existing profile identity, and prevent simultaneous new-desktop instances from writing the same job file.
- This is a test build of the new Garmin workflow. Multi-provider online connectors, Strava API budgets, automatic app updates and a guaranteed pre-start total ETA are not included.

# 0.5.8-preview · TTN Activity Export

- Rename the application to **TTN Activity Export**. German subtitle: “Deine Aktivitäten. Deine Daten. Alles lokal.” English: “Your activities. Your data. All local.”
- Update window/dialog titles, session log branding, map export attribution, help, documentation, Windows launcher, package names and build workflows. Retain the previous starter filename as a forwarding launcher. Include GitHub-readable manuals in the starter.
- Preserve the internal GarminExportStudio profile and current output directory so existing sessions, preferences, remembered dates, request pauses and account archives stay accessible. New export reports use the new identity; both old and new reports remain accepted for verified reuse and managed-file cleanup.
- This is a rename of the existing Garmin app, not the planned multi-provider release. Strava and Komoot remain planned. Historical changelog entries retain their original names.

# 0.5.7-preview · light and dark mode

- Add a bilingual theme button next to the language switch. Dark mode uses a dark blue-gray background and soft light foreground, with theme-aware inputs, visible checkboxes, disabled states, tables, selections, headers, menus, tooltips, app dialogs and logs.
- Persist theme selection locally in ui-preferences.json. Missing/invalid settings default to light. Switching preserves sign-in, export configuration, selections and running work.
- Offline map grid, overlays and route/table colors follow the palette; external online tile imagery is unchanged. Update bilingual guide. No new dependencies.

# 0.5.6-preview · faster file generation and separate download

- Export-tab Download only saves the selected normal resources directly to the account archive with no CSV/XLSX/JSON file generation. Uses Export/Options activity extras; sign-in required. Existing Offline-data actions remain.
- JSON, CSV and write-only Excel share one streaming payload pass (wide layout still scans once for columns). Original files stream separately. No added dependencies.
- Optional export reuse defaults on. Source-content hashes and output settings identify each dataset/year/format; existing output SHA-256 is checked before retaining files in place. Changed/missing outputs rebuild, added formats are generated. Initial old exports need one rebuild. Disabling reuse forces regeneration. Publication rollback and stale-file cleanup preserve unrelated files.
- Progress and timed logs cover download/archive reads, conversion, Excel save/compression, checksums and copies. Reports include file counts and times; concurrency, request interval and inferred-skip setting are logged.
- No promise of a fixed speedup on live Garmin accounts; initial Excel generation and integrity checks still take time. File generation remains non-cancellable. No database schema changes.

# 0.5.5-preview · parallel request limit

- Raise the configurable parallel request limit from 8 to 50, in both UI and plan validation. Default remains 3; the shared request interval, bounded prefetch windows and stop/rate-limit behavior are unchanged.
- Update German/English documentation. All 0.5.4 features remain included.

# 0.5.4-preview · optional inferred skips

- Experimental skip option is off by default. Requires explicit null fields; no sport-name rules. Summaries are processed before dependent requests are scheduled.
- Skips remain unverified/missing, with request and rule evidence in an additive optional SQLite table. Existing responses take precedence; offline exports flag missing data and inferred runs are incomplete.
- Offline-data button retries marked requests in the chosen date range without inference. Actual responses remove the marker; failures remain retryable. Rate limits remain enforced.
- Shared account storage, export folders and saved first-activity dates from 0.5.3 are retained. No added dependencies. Savings are not validated against live Garmin accounts.

# 0.5.3-preview · 2026-10-24

- Default to one exports/current folder per account; optional history uses output settings instead of transfer tuning for its identity. Stage output before publication, clean stale generated files, preserve unrelated files and roll back ordinary publication failures.
- Online exports reuse the selected SQLite archive and store new responses there, sharing the same source as archive sync. Legacy cache responses are imported without network requests, including older nested account caches.
- Normalize account-folder output selections without nesting account directories. Existing older export folders are not removed. No database schema or dependency changes.

# 0.5.2-preview · 2026-10-24

- Remember the detected first activity date per account, including after session restoration. Missing dates are looked up once when the suggestion option is enabled; cached dates avoid repeated account queries.
- Retain user-selected start dates separately for Export and Data. Add bilingual reset buttons that restore the saved account first activity date without network requests. End dates retain their existing behavior.
- Keep accounts and local archive selections isolated; incomplete local history never replaces the detected account date.

## Review follow-ups

- Rate limits are signalled to the UI immediately, even if later storage/report writes fail. A storage error while saving already received responses no longer hides the original stop reason. A rate limit (429) is kept, so the local request pause still applies; the storage error is listed as a warning.
- A rejected or expired saved session no longer shows an error dialog on every start: the email stays filled in, the automatic sign-in is turned off and a hint appears in the log. Temporary network/server errors keep the saved account for the next start.
- The UI explicitly explains that unchecking Remember disables automatic sign-in while retaining tokens. Remove local session remains the explicit deletion action.

# 0.5.1-preview · 2026-10-23

- Restore the remembered account on startup using saved session tokens, without saving passwords. Verify token writes explicitly and report save failures. Respect request pauses. Allow removing expired local sessions without signing in. After updating, sign in once with Remember enabled.

- Estimate parallel downloads from measured batch wall-clock throughput, keeping serial work and cached data separate.
- Data browser: full-height map pane, compact tools/selection menus, guide as final tab, and activity inventory diagnostics distinguishing missing requests from empty responses.

- Parallel requests (Options → "Parallele Abfragen", 1–8, default 3) for independent single-day requests and activity details/files. One shared schedule: the request interval is the minimum gap between any two request starts across all workers. Responses are stored in the original order; stored response payloads and exported data files match sequential runs in synthetic tests (timestamps and reports differ).
- Completed parallel responses are saved even after an earlier request failed or Stop was pressed. Actual request starts use a shared schedule that handles delayed workers.
- A rate limit, authentication or server/network failure in any worker stops new requests at once; already received responses are saved and the run stays resumable.
- Archive sync no longer forces a 2 s interval; it uses the configured interval (minimum 0.25 s, default 0.5 s) and retries transient network/5xx errors (never 4xx/429).
- New opt-in dataset "Tagesrohdaten als FIT-Datei": one /download-service/files/wellness/{date} ZIP per day (monitoring FIT files), stored and exported unchanged. Not part of "all supported data"; no table conversion yet.
- Fix: days skipped after Garmin rejected a query type are now recorded as missing (coverage, "retry failed" queue) instead of silently absent.
- Fix: one activity outside its range batch no longer switches all later activity batches to daily requests.
- Security: XML import refused DTDs only by byte search, bypassable with UTF-16; now checked by the parser for every encoding.
- Fix: GPX/TCX files mixing UTC ("Z") and naive timestamps no longer fail to import.

# 0.5.0-preview · 2026-10-23

- Introduced a distinct public application name for the original Garmin-only exporter. Retained internal application profile name for existing sessions/logs.
- Small Windows x64 starter: private Python runtime, pinned/checksummed PyPI wheels, missing/corrupt-package repair, local download cache, progress and setup.log. No admin or preinstalled Python required.
- Reproducible starter builder, locked full transitive Windows dependency set and Windows CI for first setup, offline restart and cached missing-file repair.
- Existing 0.4 export behavior retained, including full-detail archive sync and optional daily statistics. No claim of faster complete archive downloads or live Garmin verification.

# 0.4.0-preview · 2026-10-23

- Full daily summary batching, configurable 1–28 days, preserving original daily cache/archive identities and returned fields.
- Explicit full-timeline/default versus daily-statistics health mode for ten categories, with distinct -daily resources, matching bilingual labels and preview/fields/offline/preset/repair integration.
- Strict dated-range validation; missing days and unsupported ranges use matching daily reads, never substituting statistics for detailed timelines. Auth/rate/connection errors stop.
- Actual system Downloads/Garmin_Export as default output, including redirected Windows Downloads. Existing data is not moved automatically.
- Full archive button retains full-detail behavior; selected-category sync honors mode. No dependency changes; existing Windows runtime reused.
- Monitoring FIT ingestion and HRV/detail endpoint batching are not implemented in this release. No live Garmin or Windows execution test.

# 0.3.1-preview · 2026-10-23

- Fix clipped Output text and checkbox indicators: normal control font weight, font-aware minimum heights and spacing.
- Export page scrolls at small window sizes or high display scaling instead of squeezing the Output form.
- German/English offscreen layout checks at 150% scaling, 1180×870 and 900×650 logical window sizes. Windows execution remains unverified.
- Existing download optimization and ETA retained; no dependency or data-format changes.

# 0.3.0-preview · 2026-10-23

- Bounded Body Battery and paginated activity-range retrieval; only contiguous missing days are batched. Existing request fingerprints and daily archives preserved.
- Conservative response validation, daily fallback for missing dates or unsupported ranges, no fallback on rate/auth/connection blocks.
- Measured transfer ETA with cache/file weighting, provisional activity workload, retry-wait display, request count and separate writing phase.
- Selected-category archive sync; optimization toggle and activity range size saved in presets.
- Windows overlay update uses the existing bundled runtime; no new Python installation or dependency update required.
- Detailed heart rate, sleep and stress endpoints remain daily; pacing is unchanged. Synthetic regression tests and smoke test, not live Garmin or Windows validation.

# 0.2.0-preview · 2026-10-23

New local data browser, Ctrl/Shift multi-selection maps and heatmap, optional OSM/Google views, PNG/KML sharing with endpoint masking, FIT/GPX/TCX/activity ZIP import and cache migration, daily health tables, month/year totals, comparison and approximate route matching, validated SQLite backups and targeted repair queues. Persistent session logs and log buttons, visible checkbox indicators, and optional oldest activity date suggestion. Existing SQLite schema remains compatible; imported partial days are explicitly marked. Separate Windows portable CMD bundle assembled with the official embedded runtime; no custom app EXE or live Windows/Garmin/Google account validation in this release.

# Changes

## 2026-10-23 · Sportart-Dropdown / Sport dropdown

- Durchsuchbare Auswahl mit „Alle Sportarten“, deutschen/englischen Bezeichnungen und stabilen Garmin-Schlüsseln.
- Vollständige Sportartenliste nach der Anmeldung und über „Liste aktualisieren“.
- Eigene Schlüssel und vorhandene Vorlagen bleiben unterstützt.
- Optionen sind scrollbar, damit alle Einstellungen zugänglich bleiben.
- Searchable bilingual sport list, live Garmin taxonomy retrieval and manual refresh; custom keys and existing presets remain supported.

## 2026-10-23 · Layout „Abruf und Tabellen“

- Beschriftungen über den Eingabefeldern statt in einer schmalen Seitenspalte.
- Kürzere Texte und separate Erklärung zur Cache-Einstellung.
- Deutsche und englische Darstellung bei 150 % Skalierung geprüft.

## 2026-10-23 · Lesbare Aktivitätsliste und Abrufkorrektur

- Eine Zeile pro Aktivität mit Datum, Tourname, Ort, Distanz, Zeit, Geschwindigkeit und weiteren üblichen Summenwerten.
- Schnellwahl „Nur Aktivitätsliste (CSV)“; Original-CSV als „CSV (Runden)“ kenntlich gemacht.
- Tageslisten ohne Sportarten-Serverfilter abrufen, explizite Paginierung und lokale Auswahl nach Typ/Untertyp.
- Bei Abruffehlern den verfügbaren HTTP-Status im Protokoll/Bericht anzeigen, ohne private Serverantworten zu speichern.
- Mit 30 simulierten E-Mountainbike-Aktivitäten geprüft; echter Kontotest noch erforderlich.

## 2026-10-23 · Begrenzte Exportvorschau

- Neuer Button „Vorschau anzeigen“ vor dem Export, mit Tabellen und JSON-Ausschnitten.
- Dieselben Formate, Spalten, Einheiten, Sportarten- und Feldfilter wie bei der Dateiausgabe.
- Einstellbare Zeilen-/Abfragelimits, Abbruch und Hinweise zu unvollständigen Stichproben.
- Keine Export-/Cache-Dateien und kein Download der eingestellten Originaldateien.

## 2026-10-23 · Verbindungsfehler und Ratenlimit

- Keine doppelten API-Wiederholungen in App und Bibliothek.
- Verbindungsfehler stoppen die Serie; Fehlermeldungen zeigen HTTP-Status und sichere Diagnosekategorien.
- Nach Ratenlimit keine neuen Aufrufe bis zum Ende einer lokalen Pause; Retry-After wird berücksichtigt, sonst 15 Minuten. Kein automatischer Neustart.
- Ratenlimit beim Laden der Sportarten nach der Anmeldung wird nicht mehr verschluckt.

## 2026-10-23 · Optionale SQLite-Offlinedatenbank

- Neue Seite „Offline-Daten“ mit Sammelsicherung aller 27 unterstützten Standarddatenarten im gewählten Zeitraum.
- Optionale Aktivitätsdetails und ORIGINAL/GPX/TCX/KML/Runden-CSV; erfolgreiche Antworten einzeln und dauerhaft gespeichert.
- Fortsetzen, Lücken ergänzen, jüngere Daten aktualisieren und vorhandenen Dateicache übernehmen.
- Bestandsübersicht mit gespeicherten/fehlenden Tagen, leeren Antworten und offenen Abruffehlern.
- Offline-Vorschau und Export ohne Anmeldung oder Online-Fallback, auch während einer lokalen Abrufpause.
- Datenbanken sind pro Konto geschützt; private SQLite-Dateien in .gitignore ausgeschlossen.

# TTN Activity Export — user guide

For source version **0.6.0-preview**. [Deutsch](ANLEITUNG.md) · [Project overview](../README.md) · [Planned features](../ROADMAP.md)

This local desktop app downloads supported Garmin Connect data, keeps a reusable local archive and creates export files. You choose the dates, datasets and output formats. Strava and Komoot are not integrated yet. Older application downloads may not include every feature described here.

## Getting started with preview 0.6

This guide covers the new desktop. **Garmin is operational. Strava and Komoot have prepared account entries and destinations but no live online connector yet.** This build cannot sign in to all three providers. Strava API budget displays and automatic application updates remain future work.

The four main tabs are **Accounts**, **Download**, **Data**, and **User guide**. The detailed reference below still applies; its former Export/Output, Options, Fields, Expert and Offline data areas are now inside **Download → Options …**. Apply keeps edits for new jobs; Cancel restores the prior selection. Existing queued jobs never change. **Save as account defaults** explicitly saves your current selection for that account.

### Quick start: create a CSV list

1. Under **Accounts → Add account**, select Garmin and enter your email. An existing remembered Garmin account is imported. Use **Sign in / settings** to connect. Password and two-factor prompts are still handled during sign-in.
2. Under **Download**, choose the account, dates and **Activity list** preset.
3. Choose **Download and export files** and enable CSV to create a CSV file. The default **Download only** action stores source responses in the database without creating output files. **Export offline only** creates files from a local archive without sign-in or network retrieval.
4. Optionally click **Show online inventory**. The initial request is bounded to ten list pages of up to 100 entries each. No individual activity files, measurement streams, photos or maps are requested.
5. Search names/dates or filter sports. Ctrl adds individual rows; Shift selects a range. **Select all visible** only includes visible, already loaded results. **Use selection** sets the chosen IDs and clears a potentially conflicting sport filter. Without a specific selection, matching activities from the dates and sport filter are used.
6. Click **Add to job list**. Add further jobs with different settings or Garmin accounts and reorder them with Move up/Move down.
7. **Review and start jobs** displays each immutable job's settings. Only **Start download / export** executes them; Back starts nothing. To revise a queued job, remove it and add the revised selection.
8. Open the results folder after exporting files. To browse local tables/maps, open the corresponding database under Data.

### Understanding inventory

Each list belongs to one account and date range. Changing dates or account clears the current selection. **Refresh inventory** starts over; **Load more pages** resumes pagination. The timestamp identifies the observation time. Failed, repeated or interrupted pages keep the result **partially loaded**. Only a final empty list page establishes complete listing for that range. A previously saved inventory may open without another request.

This is neither a complete health-data catalog nor proof of locally saved FIT files. Execution may retrieve the activity list again; extra details/files are requested only for chosen IDs. A missing selected ID makes the result incomplete. Bounded output preview is disabled for an ID selection because those IDs may lie outside the sample. Download that selection first, then export offline.

### Jobs, restart and duration

Account, dates, selection, formats and retrieval options are copied when a job is added. Later edits only affect new jobs. After restart, interrupted jobs remain visible but do not run until reviewed and started again. Missing login or an active Garmin request pause puts a job in a waiting state; other ready jobs may proceed. Stop cancels the current download and prevents further jobs in that run. Successfully stored responses remain available.

Review reads matching base responses from SQLite locally and plans outstanding base queries. Extra list pages, details, old file caches, range fallbacks and retries can change the real workload. Time calculated from request spacing is not a complete download prediction. Duration remains explicitly unknown when there is no reliable basis. During download, actual throughput informs ETA. Excel generation is additional local work after retrieval.

Multiple exports for one account can replace earlier results in the shared `exports/current` directory. To retain each output separately, enable **Keep separate export folders** in Options before adding jobs. Jobs are not backups.

### Accounts, folders and assistance

New accounts use `Downloads/TTN Activity Export/Garmin`, `Komoot` or `Strava`, with separate account directories underneath. A previously remembered Garmin account retains the old output folder; no downloaded data is moved. For resumption select your existing SQLite file under Options → Offline archive. Multiple Garmin accounts can be signed in one after another during a session. Startup auto sign-in still uses the most recently explicitly remembered Garmin account; connect other accounts through their sign-in settings as needed.

**Show hover tooltips** in Options is a persistent global toggle. Essential status/errors stay visible. **Log …** opens the log window with Open log and Export current session log. Language and theme remain accessible at the top. Only one new-desktop instance may use a profile at a time; close the older app before testing too.

## Detailed reference

The following explanations cover the detailed controls retained inside Options. The former direct export-start action is replaced by adding, reviewing and starting a job in the compact desktop.

## Contents

- [First launch](#first-launch)
- [Account and sign-in](#account-and-sign-in)
- [Create a simple activity list](#create-a-simple-activity-list)
- [Download, export and offline storage](#download-export-and-offline-storage)
- [Datasets and detail level](#datasets-and-detail-level)
- [Output formats and file reuse](#output-formats-and-file-reuse)
- [Options reference](#options-reference)
- [Fields and expert queries](#fields-and-expert-queries)
- [Browse local activities and maps](#browse-local-activities-and-maps)
- [Import, backup and migration](#import-backup-and-migration)
- [Progress, logs and troubleshooting](#progress-logs-and-troubleshooting)
- [Terms and limitations](#terms-and-limitations)

## First launch

1. Download the Windows Starter ZIP for the version you want. Check the release notes: the latest source and published release can differ.
2. Extract the entire ZIP into a writable folder, for example inside your user folder. Do not run it from inside the ZIP.
3. Double-click `Start-TTN-Activity-Export.cmd`. First launch installs a private Python runtime and pinned libraries. Keep the console window open until the app appears.
4. Use the language button at the top for German/English. The adjacent button switches light/dark mode; the color choice is remembered locally.
5. Sign in on **Account**. Start with a few days and the activity list to check the result before requesting years of detailed data.

No existing Python installation or administrator privileges are required. First-time setup needs internet. The starter does not modify your system Python. Its local `runtime/` and `.setup-cache/` folders support startup and repair. If setup is interrupted, run the same starter again. Check the console and `setup.log` in the program folder when setup fails. Company policies may block PowerShell scripts.

The current tabs are **Account**, **Export**, **Options**, **Fields**, **Expert**, **Offline data**, **Data**, and finally **User guide**. Most first-time exports only need Account, Export and sometimes Options. These former tabs are now inside Options; the four main tabs are described above.

## Account and sign-in

Enter your Garmin email and password, then click **Sign in**. Follow the two-factor authentication prompt if Garmin requests it. **China account** is only for accounts using garmin.cn.

**Remember session locally** stores authentication tokens for later session restoration. Your password is not stored. Tokens currently have no additional encryption: protect your Windows account and do not share the app profile. The session path is shown on Account. The internal profile name remains `GarminExportStudio` for compatibility.

Unchecking the remember option disables automatic sign-in; it does not delete existing tokens. Use **Remove local session** to delete those tokens, even when you are not signed in. Expired credentials may require a fresh sign-in.

**Suggest first activity as start date** looks up the earliest activity date. That date and your custom Export/Data start dates are remembered per account. **First activity** on Export resets the start to the stored account date. This is a suggestion, not a history limit: health data may predate the first activity. Check the end date before starting another job.

The sport list is loaded after sign-in. Use **Options → Refresh list** to reload it. The sport filter affects activities, not sleep, steps or other health datasets.

## Create a simple activity list

Example: export one month's cycling activities as a CSV with date, name, distance and duration.

1. On **Export**, click **Activity list only (CSV)**. This selects the activity summary and clears additional activity requests.
2. Choose the first and last date. **Through** includes the final day. Multiple years are supported; the overall date range is not limited to 365 days.
3. Under **Options → Sport type**, select cycling or the relevant Garmin type. Leave the filter empty/select all for every sport.
4. Check the output folder on Export. The current default is `Downloads\Garmin_Export`.
5. Keep **Activities: one table row per activity** enabled. Leave year splitting off if you want a single combined list.
6. Optionally click **Show preview** for a bounded sample. This does not inspect the whole history.
7. Choose **Download and export files**, add the job and start it after review, then **Open results folder**.

This list does not need original files, weather or metric streams. **Activities – summary** must be selected: choosing a sport alone does not enable that dataset. Not every activity has every field. Manually entered or indoor activities may have no GPS track.

## Download, export and offline storage

| Action | What it does |
| --- | --- |
| **Download only** | Saves the selection from Export/Options to the account archive without subsequently creating CSV, Excel or JSON output files. Requires sign-in. |
| **Start export** | Retrieves required data or reuses saved responses, then generates the selected formats. |
| **Use offline data only for previews and exports** | Reads only the chosen local database. Missing data is not silently fetched online. |
| **Download / update all supported data** | Archives the 27 included datasets for the Export dates with full health timelines. Uses its own activity detail/file settings on Offline data. |
| **Download / update selected datasets** | Uses the selected Export datasets and health detail level, with activity extras configured separately on Offline data. |

Use **Download only** to secure data first and decide on output files later. Additional Expert queries are not supported by this action; use normal export for those.

“All supported data” is not every possible Garmin account resource, nor every date regardless of your selection. Export's From/Through dates still apply. This action ignores the sport filter and uses its own **Include activity details**, **Include original activity files**, and additional format controls. Details and originals are initially enabled there. It can therefore request much more than a simple CSV list. Conversely, an earlier partial archive may contain less data than a later export with every category and extra enabled.

Each account has a separate directory and a `garmin-offline.sqlite` database underneath the output folder. Online export and offline sync can share that archive. To resume, keep the same output directory and database selected. Creating a fresh CSV does not necessarily download its source again. **Refresh recent days** can deliberately fetch recent responses again.

Use **Inspect stored data** to check local coverage. **Retrieve skipped requests anyway** requests experiment-based omissions within the selected dates. A saved empty Garmin response, a failed request and an unverified skipped request are different states.

## Datasets and detail level

Supported categories include daily summary, heart rate, sleep, stress, Body Battery and events, steps, floors, intensity minutes, respiration, SpO₂, HRV, resting heart rate, weight, body composition, blood pressure, hydration, training status, readiness, VO₂max, fitness age, endurance score, hill score and activities. Devices, personal records and active goals represent current account snapshots, not complete historical inventories.

Availability depends on your device and account. A category may return no values or be unavailable. The app cannot reconstruct measurements that were never recorded.

Under **Export → Output → Health data**, choose:

- **Full measurement timelines** for detailed time series and sleep stages. Many endpoints still require daily requests.
- **Daily statistics** for faster summaries without full timelines. Applies to heart rate, sleep, stress, Body Battery, steps, floors, intensity minutes, respiration, hydration and resting heart rate. Other categories are unchanged.

**Daily raw data as FIT file** optionally stores wellness ZIPs unchanged. The app does not yet turn their contents into tables or automatically substitute them for selected JSON requests. This optional category is not included in the standard 27-dataset full sync.

Activity extras under Options include metric timelines, laps, splits, heart rate zones, exercise sets and weather. Each selected extra can add a request per activity. **ORIGINAL** downloads Garmin's original file, often a ZIP containing FIT. GPX, TCX, KML and lap CSV are separate downloadable representations when Garmin provides them. The lap CSV option is different from the simple activity summary CSV.

## Output formats and file reuse

| Setting | Purpose |
| --- | --- |
| **CSV** | Simple lists and downstream processing; configure the separator in Options. |
| **XLSX** | Excel workbooks; large datasets need time for writing and compression. |
| **JSON** | Nested source responses for custom processing. Field filters do not trim raw JSON. |
| **Long layout** | Detailed leaf values with paths; potentially many rows. |
| **Wide layout** | Records with columns; diverse responses can create many columns. |
| **One table row per activity** | A readable activity summary rather than flattened nested detail values. |
| **Split files by year** | Smaller output groups for multi-year exports. |

The default result directory is `exports/current` for each account. Another export updates files managed by the app there. Save a separate copy if you need an exact historical result. **Keep separate export folders** enables separate result directories; existing older folders are not automatically removed.

**Reuse unchanged export files** is on by default. The app checks source content, output settings and existing output checksums. Unchanged groups can stay in place; changed, missing or damaged outputs are rebuilt. Old exports may need a one-time rebuild. Reading the archive and checking integrity still takes time. Disable reuse to force regeneration.

After retrieval, local work includes reading responses, converting tables, compressing Excel workbooks, calculating checksums and publishing files. This explains activity after the last network request. **Download only** defers file generation. Download can be stopped; file generation itself is currently not cancellable.

## Options reference

Defaults below apply to a fresh configuration without a loaded preset. Always inspect the displayed values after loading one.

| Option | Default | Effect |
| --- | --- | --- |
| Request interval | 0.5 seconds | Shared minimum spacing between request starts across all workers. |
| Parallel requests | 3; range 1–50 | Overlaps response waiting. Additional workers do not bypass the shared interval. |
| Batch supported date ranges | On | Uses range endpoints where supported. |
| Activities: days per range query | 31; range 1–365 | Size of a retrieval block, not a limit on total history. |
| Health: days per range query | 28; range 1–28 | Block size for supported statistics endpoints. Detailed heart rate/sleep stays daily; Body Battery timelines use up to 7 days. |
| Network error retries | 2 | Bounded retries for temporary failures, not a way around throttling. |
| Refresh recent days | 2 | Fetches recent saved days again. 0 reuses existing responses. |
| Skip likely empty requests | Off, experimental | Uses hints from daily summaries. Omitted details remain unverified; the rule does not prove absence. |
| Preview rows per table | 10 | Maximum sample rows displayed per table. |
| Preview maximum queries | 12 | Bounds retrieval work for the preview. |
| CSV separator | Semicolon | Change to comma or tab if required by the receiving program. |

Offline sync actions apply additional safeguards, including a minimum interval of 0.25 seconds. Being able to enter a smaller value elsewhere does not guarantee that effective sync speed.

At a 0.5-second interval, at most about two requests per second can start over time, regardless of the worker count. Response latency, local processing and server throttling can reduce throughput. The app does not know a universally safe Garmin rate. A successful run on one account is not a guarantee for other accounts or future runs.

**Save selection preset** and **Load preset** help reuse configurations. Before starting, check dates, account, output directory and data source. A preset is not a backup of your downloaded data.

## Fields and expert queries

The **Fields** tab restricts CSV/Excel output by path. Blank means all fields. **Load fields** samples the first selected dataset on the start date; an empty response may provide no useful fields. Apply checked fields or enter one path pattern per line, such as `/totalSteps` or `/heartRateValues/*/*`.

Filters apply across selected categories. A pattern that matches one category may remove visible values from another. Raw JSON, cached responses and original files remain complete. Clear field filters first when a table is unexpectedly empty.

**Expert** enables additional permitted read queries from the Garmin library. Read the method documentation and supply valid JSON parameters. Available placeholders are `{date}`, `{start}` and `{end}`. **Run per day** is appropriate for daily methods; turn it off as needed for range methods. Required arguments and pagination are not handled arbitrarily for every method. Normal activity lists do not require Expert queries.

## Browse local activities and maps

1. Open **Data**, choose the SQLite file and click **Load data**.
2. Filter by text, sport, dates and minimum distance. A restrictive date filter can hide already stored activities.
3. Select an activity to show its locally available track in the right-hand map.
4. Hold **Ctrl** to select individual additional rows, or **Shift** for a consecutive range. The Selection menu can select all filtered rows.
5. Enable the heatmap or export a selection. Customize columns or save filter presets for repeated use.

Activity summaries do not necessarily contain track geometry. Maps require locally stored tracks from supported details or imported files. An empty map does not mean the activity itself is missing. Indoor and manual activities may have no GPS data at all.

The default track view works without an online basemap. Enabling the online map downloads tiles from an external service. Tile imagery keeps its original colors in dark mode. The Google Maps view needs your own API key and may incur costs under Google's terms. For **Google My Maps**, export KML, import it on Google's site and create the share link there. Local heatmap rendering is not transferred as a heatmap. Check private start/end locations before sharing.

## Import, backup and migration

Under **Data → Tools**, find file import, database backup, validation and missing-data repair. Supported FIT, GPX and TCX files can also be imported from ZIP archives. Imports only contain information available in their source format; they do not recreate an entire Garmin health history.

Use **Create backup** to make a database backup, then **Open file** to reopen it later. Finish active writes before manually copying files. On another computer, set up the app, transfer the backup and open it. Pure offline analysis does not require Garmin sign-in.

**Import export cache** helps migrate older saved response caches into the local archive. An arbitrary edited CSV/Excel file is not a full database backup and cannot generally be reimported without loss. Keep the database and original files for future analyses. Authentication tokens are not required for this migration.

## Progress, logs and troubleshooting

Download ETA uses observed throughput. It can fluctuate during initial sampling, cache hits, retries or changes in dataset type. After download, status messages describe local processing. Download ETA is not a guaranteed total duration including every Excel workbook.

**Open log** opens the saved log file. **Export current session log** saves the current app session's log for sharing. The visible log window is bounded; the file contains more history. Inspect logs for personal details and local paths before posting them publicly.

| Problem | Checks |
| --- | --- |
| Empty Data table | Correct SQLite file? Activity summaries actually downloaded? Matching date/sport filters? Import an older export cache if necessary. |
| Unexpected CSV structure | Use Activity list only (CSV), check sport and clear field filters. |
| No route on map | Are track data stored locally? Was GPS recorded? The summary alone may not be sufficient. |
| `GarminConnectConnectionError` | Check connectivity/Garmin availability; keep saved data and resume the same job later. |
| `GarminConnectTooManyRequestsError` / HTTP 429 | Wait for the displayed request pause. The run stops; resume manually later. Already started requests may still finish. |
| Repeated sign-in | Enable session remembering and check persistence messages. Remove an invalid local session, then sign in again. |
| App busy after download | Check conversion, Excel compression and checksum steps. Consider Download only or fewer formats next time. |
| New requests after resuming | Recent-day refresh, new categories/detail levels or missing responses can require retrieval. |
| File writing fails | Check disk space, permissions and result files open in Excel. A write failure does not necessarily mean downloaded responses were lost. |

For a useful issue report, include version, action, dates, selected datasets/formats and exception class. Do not post passwords, tokens or private databases. Synthetic tests and demo data do not establish complete access to every live Garmin resource.

## Terms and limitations

- **Download:** retrieve data from Garmin.
- **Offline archive:** locally stored responses and supported activity files in SQLite.
- **Export:** generate output files from saved or newly retrieved data.
- **Preview:** a small sample of expected output, not a complete online inventory.
- **Empty response:** Garmin answered without corresponding values.
- **Skipped, unverified:** an experimental rule omitted the request; detail availability remains unknown.

**Online inventory before downloading** is available for Garmin activities as described above. It shows metadata without fetching individual FIT/GPX files or measurement streams. This does not provide a reliable inventory of all health-data days. See the [roadmap](../ROADMAP.md).

## Experimental skip rules

The skip option remains off by default. Empty daily statistics do not prove that detailed data is absent. Omitted requests remain unverified, and the Offline archive controls can explicitly retrieve them later.

Presets store dataset/output options, not account-specific inventory ID selections. Select the desired activities again after loading a preset.

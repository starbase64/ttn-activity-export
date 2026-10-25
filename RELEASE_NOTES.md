# TTN Activity Export · 0.6.1-preview · Testversion

**Deine Aktivitäten. Deine Daten. Alles lokal.**

Diese Testversion führt die vereinfachte Oberfläche ein. Vier Hauptreiter: Konten, Download, Daten, Anleitung. Detailoptionen, Felder, Experten und Offline-Verwaltung liegen jetzt im Optionen-Fenster mit Übernehmen/Abbrechen. Das Protokoll hat ein eigenes Fenster.

Neu: mehrere getrennte Kontoeinträge und Zielordner, ausdrücklich speicherbare Kontovorgaben, Garmin-Bestandsübersicht nur aus Listenmetadaten mit Paginierung und Teilstatus, Aktivitätsauswahl, gespeicherte und sortierbare Aufträge mit Zusammenfassung vor dem Start, lokale Grundabfragenplanung und abschaltbare Tooltips. Ein unterbrochener Auftrag wird nach einem Neustart nicht automatisch ausgeführt. Gewählte Aktivitäts-IDs gelten auch für Details, Originaldateien und Offline-Exporte; fehlen gewählte Aktivitäten, wird der Lauf unvollständig gemeldet.

**Strava ist jetzt ausschließlich eine lokale Importquelle.** Der Nutzer lädt das Strava-Konto-ZIP selbst herunter und wählt es unter Strava → Datenpaket importieren aus. Die App liest `activities.csv` und referenzierte FIT-/GPX-/TCX-Dateien, einschließlich GZIP. CSV-Einträge ohne Datei bleiben als Aktivitätsübersicht erhalten. Wiederholte Paketimporte werden anhand der Strava-ID erkannt. Fehler und Größenlimits werden ausgewiesen. Keine Anmeldung, API-Schlüssel, API-Budgets oder automatisierten Strava-Abfragen in der App. Original-ZIP unverändert aufbewahren; Fotos, Kommentare und weitere Kontoinhalte werden nicht importiert.

**Garmin bleibt nutzbar; Komoot ist noch nicht online angebunden.** Automatische App-Updates sind noch nicht enthalten.

Erste Schritte: ZIP vollständig entpacken, `Start-TTN-Activity-Export.cmd` starten. Bestehende Garmin-Anmeldung wird soweit möglich übernommen. Unter Konten anmelden, unter Download Zeitraum/Vorgabe/Aktion wählen, zur Auftragsliste hinzufügen und „Aufträge prüfen und starten“ drücken. Die Vorgabe „Nur herunterladen“ erzeugt keine CSV/Excel-Dateien; dafür „Download und Dateien exportieren“ oder „Nur lokal exportieren“ wählen.

Bisheriger Profilname GarminExportStudio und bestehende SQLite-Datenbanken bleiben kompatibel. Bestehende Nutzer wählen ihren bisherigen Ordner und dieselbe Datenbank. Neue Konten verwenden Downloads\TTN Activity Export\Garmin beziehungsweise Komoot/Strava. Keine automatischen Datenverschiebungen. Vor dem Test die bisherige App schließen und die Datenbank über deren Sicherungsfunktion sichern. Ein alter Programmstand kann neu hinzugefügte ID-Auswahlvorlagen nicht zuverlässig auswerten; dafür einen neuen Auftrag mit 0.6 anlegen.

Die Zeit vor dem Start ist eine lokale Planung. Zusätzliche Listenseiten, Bereichs-Fallbacks, Wiederholungen und unbekannte Aktivitätsdetails können den Aufwand ändern. Die tatsächliche Restzeit wird während des Downloads gemessen. Excel-Erzeugung bleibt ein eigener Schritt.

English: this preview introduces the four-tab desktop, account settings, metadata-only Garmin inventory, selected activity IDs, persistent/reorderable jobs, pre-start review and optional tooltips. Garmin is operational. Strava is a local-only importer for a user-downloaded account ZIP, including activities.csv and supported recordings/gzip files. No Strava sign-in/API key/automatic retrieval. Komoot remains a configured placeholder with no online sign-in/list/download yet. No automatic app updater. Existing profile and archives stay compatible; new accounts use Downloads/TTN Activity Export/provider. Download only is the default action; choose download-and-export or offline export to create output files. Close the older app and back up the archive before testing.

# TTN Activity Export 0.6.9

Diese Version behebt einen Fehler, durch den die App beim Neustart wieder einen alten Datenbankpfad verwendete.

- Eine unter **Daten** geöffnete Datenbank wird sofort für das passende Konto gemerkt.
- Beim Beenden bleibt ein gültiger geänderter Pfad erhalten, auch ohne vorherigen Kontowechsel oder erneutes Laden. Ein ausdrücklich eingegebener neuer SQLite-Zielpfad wird ebenfalls gespeichert.
- Eine wiederhergestellte Garmin-Anmeldung setzt die Auswahl nicht mehr auf den alten Kontoeintrag zurück.
- Fremde oder ungültige Datenbanken überschreiben den gemerkten Kontopfad nicht.
- Der Standardordner heißt exakt **Downloads\TTN_Activity_Export**, mit den Unterordnern **Garmin**, **Komoot** und **Strava** sowie getrennten Kontoordnern.

**Nach dem Update:** Unter **Daten → Datei öffnen** einmal die gewünschte vorhandene SQLite-Datei am neuen Speicherort auswählen. Die App verschiebt oder löscht keine vorhandenen Dateien und lädt wegen dieser Korrektur keine Daten erneut herunter.

## Windows herunterladen

Unter **Assets** die Datei **TTN-Activity-Export-Windows-0.6.9.zip** herunterladen, vollständig entpacken und **Start-TTN-Activity-Export.cmd** starten. Vorher die alte App schließen. Vorhandene Profile und Daten bleiben kompatibel. Der Starter installiert bei Bedarf seine private Python-Laufzeit; keine eigene Python-Installation erforderlich. Eine SHA-256-Prüfsumme liegt bei.

Die Update-Prüfung in Version 0.6.8 erkennt dieses Release. Sie öffnet über **Download öffnen** die GitHub-Seite; das ZIP wird anschließend wie oben entpackt und gestartet.

[Deutsche Anleitung](https://github.com/starbase64/ttn-activity-export/blob/v0.6.9/docs/ANLEITUNG.md) · [English guide](https://github.com/starbase64/ttn-activity-export/blob/v0.6.9/docs/USER_GUIDE.md) · [Changelog](https://github.com/starbase64/ttn-activity-export/blob/v0.6.9/CHANGELOG.md)

## English

Fix account archive locations reverting after restarting the app. Opened matching databases are remembered immediately; valid edits and explicitly entered new SQLite targets persist when closing, without switching accounts first. Restored Garmin sign-in preserves the selected archive. Foreign/invalid databases do not overwrite the saved account path.

The exact default root remains **Downloads/TTN_Activity_Export**, with Garmin, Komoot and Strava account directories. Select the desired existing database once under **Data → Open file**. Existing files are not moved or deleted. Version 0.6.8 can detect this release through **Check updates**.

Download the Windows x64 ZIP under **Assets**, extract it completely and start **Start-TTN-Activity-Export.cmd**. Close the old app first. Existing profiles and data stay compatible; a checksum is included.

Dependencies and research acknowledgements, including python-garminconnect and GarminDB, remain documented in [third-party notices](https://github.com/starbase64/ttn-activity-export/blob/v0.6.9/THIRD_PARTY_NOTICES.md). Komoot remains experimental; Strava remains local import only.

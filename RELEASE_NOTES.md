# TTN Activity Export 0.6.8

**Deine Aktivitäten. Deine Daten. Alles lokal.**

Die geprüfte Version mit Garmin-Export, lokalem Strava-Import und experimenteller Komoot-Anbindung ist jetzt veröffentlicht.

## Windows herunterladen und starten

1. Unter **Assets** `TTN-Activity-Export-Windows-0.6.8.zip` herunterladen.
2. ZIP vollständig in einen beschreibbaren Programmordner entpacken.
3. **Start-TTN-Activity-Export.cmd** doppelklicken.

Der kleine Windows-10/11-x64-Starter lädt beim ersten Start eine private Python-Laufzeit und fehlende Pakete. Dafür ist Internet nötig; eine eigene Python-Installation und Administratorrechte sind nicht erforderlich. Eine SHA-256-Prüfsumme liegt als separate Datei bei. Vor einem Wechsel die alte App schließen. Vorhandene Konten, Einstellungen, Datenbanken und Downloadordner bleiben verwendbar.

## Enthaltene Funktionen

- **Garmin:** mehrjährige Zeiträume, einzelne Datenarten oder Aktivitäten, parallele Abfragen, wiederverwendbarer Offline-Bestand und CSV-/Excel-/JSON-Exporte.
- **Strava:** selbst heruntergeladenes Konto-ZIP oder entpackten Ordner importieren, einschließlich deutscher/englischer Aktivitätslisten und referenzierter FIT-/GPX-/TCX-Dateien, auch komprimiert. Wiederholte Importe aktualisieren vorhandene Aktivitäten. Die App meldet sich nicht bei Strava an und ruft dort keine Daten automatisch ab.
- **Komoot:** experimentelle E-Mail-/Passwort-Anmeldung, Tourenübersicht und ausgewählter Metadaten-/GPX-Download. Anmeldung unter Windows optional verschlüsselt merken; das Passwort wird nicht gespeichert. Das erste Aktivitätsdatum bleibt erhalten und lässt sich per Button wiederherstellen. GPX setzt die nötige Exportberechtigung beziehungsweise freigeschaltete Region voraus.
- **Daten:** Aktivitäten filtern, mehrere Strecken gemeinsam anzeigen, optionale OSM-Karte, Gesamt-/Auswahlstatistik und automatische Datenbankauswahl beim Kontowechsel.
- **Oberfläche:** Deutsch/Englisch, hell/dunkel, vier Hauptreiter, zusätzliche Optionen in separaten Fenstern, ausführliche Anleitung und Sitzungsprotokolle.
- **Updates:** manuell neben der Sprache prüfen oder die Prüfung beim Start aktivieren. Neuere veröffentlichte Versionen führen zur GitHub-Downloadseite. Automatische Installation und Delta-Updates folgen separat.

## Geprüft und bekannte Grenzen

Die Windows-Prüfung umfasst Regressionstests, Erstinstallation, App-Smoke-Test, Offline-Start und Reparatur fehlender Abhängigkeiten. Anmeldung und Abruf bei Garmin/Komoot sowie der Import eines echten Strava-Kontopakets wurden zusätzlich auf dem Nutzer-PC geprüft.

Komoot verwendet weiterhin eine experimentelle Schnittstelle und läuft getrennt von der gespeicherten Garmin-Auftragsliste. Strava-Fotos, Kommentare und weitere Kontoinhalte werden nicht in die Aktivitätendatenbank importiert. Garmin-Sitzungsschlüssel sind weiterhin nicht zusätzlich verschlüsselt; die neue Windows-Verschlüsselung betrifft Komoot. Linux kann aus dem Quellcode verwendet werden; ein fertiges macOS- oder Mobilpaket gehört nicht zu diesem Release.

[Deutsche Anleitung](https://github.com/starbase64/ttn-activity-export/blob/v0.6.8/docs/ANLEITUNG.md) · [English user guide](https://github.com/starbase64/ttn-activity-export/blob/v0.6.8/docs/USER_GUIDE.md) · [Changelog](https://github.com/starbase64/ttn-activity-export/blob/v0.6.8/CHANGELOG.md)

## English

Download the Windows x64 ZIP under **Assets**, extract it completely and double-click **Start-TTN-Activity-Export.cmd**. First use downloads a private Python runtime and pinned packages; internet is required, but no system Python or administrator rights are needed. Close the old app first; existing profiles and data remain compatible. A SHA-256 checksum is included.

This release includes Garmin downloads and offline exports, local import of user-downloaded Strava account ZIPs/folders, experimental Komoot inventory/GPX downloads with optional Windows-encrypted session storage, account-specific activity browsing/maps, German/English, light/dark themes and manual/optional startup update checks. Strava is local import only. Komoot remains experimental and separate from the Garmin job queue. Update checks open a release page; automatic installation and delta updates are future work.

## Acknowledgements

Thanks to [python-garminconnect](https://github.com/cyberjunky/python-garminconnect), PySide6/Qt, openpyxl, fitdecode and the OpenStreetMap contributors. [GarminDB](https://github.com/tcgoetz/GarminDB) informed offline archive and wellness FIT research; it is not bundled or a runtime dependency. See [third-party notices](https://github.com/starbase64/ttn-activity-export/blob/v0.6.8/THIRD_PARTY_NOTICES.md). This independent community app is not affiliated with Garmin, Komoot or Strava.

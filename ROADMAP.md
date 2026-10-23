# Review follow-ups

The external review identified additional items outside the parallel-download patch: Windows credential protection (DPAPI/keyring), removing expired local sessions without signing in, explicit local-date handling for imported FIT UTC timestamps, equal wheel-path checks in the portable build helper, and pinning GitHub Actions to commit SHAs. These remain open and are not claimed as fixed by this change.

## 0.4.0-preview · implemented

Full daily summary ranges, opt-in daily statistics for ten health categories with separate storage, adjustable health batch size, matching offline/preset/preview/repair behavior, and system Downloads/Garmin_Export default. Monitoring FIT-based multi-metric downloads and lossless HRV/detail range adaptation remain future work pending data/schema comparisons. Windows and live account checks remain outstanding.

# Funktionsstand / Feature status — 0.3.0-preview

## In 0.3.0 umgesetzt: Download-Restzeit und optimierte Zeiträume

Die Restzeitanzeige ist nun implementiert. Sie berücksichtigt gemessene Arbeitszeiten, Datenarten, Cache-Treffer, zusätzliche Aktivitätsdateien und Wiederholungswartezeiten. Noch unbekannter Aktivitätsumfang wird als vorläufig gekennzeichnet. Bei Ratenlimit stoppt der Download; die Abrufpause ist keine automatische Fertigstellungszeit.

Unterstützte Body-Battery- und Aktivitätsabfragen werden gebündelt, alte Tagescaches/SQLite-Dateien weiterverwendet. Unter Offline-Daten gibt es eine Sicherung nur der ausgewählten Kategorien. Puls-, Schlaf- und Stressdetails bleiben tagweise. Keine reduzierte Datenauflösung und keine Erhöhung der voreingestellten Anfragerate.

Offen: Windows-Ausführung und Live-Garmin-Kontotests der neuen Bereichsabfragen. Weitere sichere Bündelungen anderer Endpunkte können nach deren Schema-/Vollständigkeitsprüfung ergänzt werden.

Die zuvor gesammelten Wünsche sind in dieser Quellversion umgesetzt. Der frühere Status „geplant, noch nicht implementiert“ gilt nicht mehr.

| Wunsch | Umsetzung |
|---|---|
| Datenseite und Filter | Lokale Aktivitätstabelle; Datum, Sportart, Suche, Mindestdistanz, gespeicherte Filter und Spalten |
| Karte neben Tabelle | Aufgezeichnete GPS-Strecken; Größe per Trennlinie veränderbar |
| Strg / Shift / Checkboxen | Gemeinsame Auswahl, alle gefilterten auswählen, mehrere farbige Tracks |
| Heatmap | Fahrthäufigkeit je Rasterzelle, pro Aktivität höchstens eine Stimme; ungefähre Darstellung |
| Google Maps | Optionale Google-Maps-JavaScript-Ansicht mit eigenem Schlüssel; kein Schlüssel im Programm enthalten |
| Teilen | PNG-Bild, KML-Datei und manuelles Google-My-Maps-Teilen; optionale Start-/Endmaskierung |
| Sichtbare Checkboxen | Große, kontrastreiche Indikatoren mit eigenem Häkchenbild |
| Logdateien | Fortlaufend pro App-Sitzung, Öffnen und Exportkopie, unabhängig vom Anzeige-Limit |
| Erstes Aktivitätsdatum | Optionale Abfrage nach Anmeldung; bestehende Datumsauswahl wird erhalten |
| Gesundheitsübersicht | Unterstützte Tageskennzahlen, leere Felder bei fehlenden Daten |
| Monats-/Jahresauswertung | Kilometer, Zeit, Höhenmeter und Anzahl nach Sportart |
| Dateiimport | FIT/GPX/TCX, verschachtelte ZIPs mit Aktivitätsdateien; lokale Duplikaterkennung |
| Fehlende Daten ergänzen | Ausgewählte GPS-Dateien, fehlgeschlagene Abrufe, fehlende gewählte Tagesdaten |
| Aktivitäten vergleichen | 2–20 Aktivitäten als Kennzahlentabelle; ungefähre Streckenwiedererkennung |
| Backup | SQLite-Sicherung per Datenbank-Backup und Integritätsprüfung, vorhandene Archive öffnen |
| Deutsch / Englisch | Neue Oberfläche und Anleitung in beiden Sprachen |

## Grenzen und weiterer Prüfbedarf

- Das separate Windows-Portable-Paket mit CMD-Start und mitgelieferter Laufzeit ist zusammengestellt und statisch geprüft. Windows-Ausführung, regulärer PyInstaller-EXE-Build und Tests mit echten Garmin-Konten/Google-Schlüsseln stehen aus.
- GPS-Strecken werden lokal geladen. Online-Karten brauchen Internet; OSM lädt nur sichtbare Kacheln und bietet keinen Gebietsdownload. Eine vollständig offline nutzbare Straßenkarte ist nicht enthalten.
- Der Google-Schlüssel bleibt in der temporären Browseransicht. Schlüsselbeschränkungen und Abrechnung können die Anzeige verhindern. Automatische My-Maps-Uploads oder Freigabelinks sind nicht implementiert; KML-Import/Linkfreigabe erfolgen beim Nutzer in My Maps.
- Garmin-Konto-ZIP-Import gilt für enthaltene Aktivitätsdateien. Wellness-FIT und andere Konto-JSON-Dateien werden nicht als Tagesdaten rekonstruiert. Einzelne GPX/TCX benötigen ein Aktivitätsdatum. Die Duplikaterkennung kann bei unterschiedlichen Zeitzonen/abweichenden Summenwerten zusätzliche Einträge lassen.
- Wiederkehrende Strecken werden nur näherungsweise anhand geografischer Raster erkannt. Die Heatmap zeigt Aktivitätenhäufigkeit, keine Aufenthaltsdauer oder medizinische Aussage.
- Große Kartenansichten werden vereinfacht; Originaldateien und Datenbankdaten bleiben erhalten. Datenbankintegrität bestätigt Lesbarkeit, nicht die Vollständigkeit aller Garmin-Daten.

English: all collected feature requests have implementations in this source preview; important remaining work is real Garmin/Google and Windows validation. Basemaps require internet, Google requires the user's key, My Maps sharing is manual via KML, and Garmin ZIP import is limited to supported activity files. Approximate route matching/heatmaps and display simplification do not modify stored originals. A separate portable CMD bundle includes the official Windows runtime; no custom application EXE or Windows execution validation is supplied.

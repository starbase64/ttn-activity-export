# Roadmap

Planungsstand nach **0.5.7-preview**. Diese Seite unterscheidet vorhandene Funktionen von Entwürfen; sie ist kein Veröffentlichungsversprechen. [README](README.md) · [Anleitung](docs/ANLEITUNG.md) · [English guide](docs/USER_GUIDE.md)

## Bereits vorhanden

Garmin-Export mit mehrjährigen Zeiträumen, CSV/XLSX/JSON, Aktivitätsliste, wählbaren Details und Originalformaten; gemeinsamer SQLite-Bestand pro Konto; Offline-Export, Dateiimport, Sicherung und lokale Datenansicht mit Karten/Heatmap. Dazu Vorschau, Download-Restzeit, gespeicherte erste Aktivität und Anfangsdaten, Sitzungswiederherstellung, Logs, 1–50 parallele Abfragen mit gemeinsamem Mindestabstand, gebündelte unterstützte Anfragen, „Nur herunterladen“, geprüfte Wiederverwendung unveränderter Exportdateien sowie Hell/Dunkel und Deutsch/Englisch.

Die experimentelle Erkennung vermutlich leerer Abfragen ist standardmäßig aus. Ihre Auslassungen bleiben ungeprüft und können gezielt nachgeladen werden. Sie ist kein Nachweis fehlender Garmin-Daten.

## 1. Bestandsübersicht vor dem Download — neu aufgenommen

Ziel: Erst sehen, welche Aktivitäten vorhanden sind, dann gezielt auswählen. **Noch nicht implementiert.**

- Button **Online-Bestand anzeigen**, anschließend **Übersicht aktualisieren**. Kein automatischer vollständiger Historienabruf bei jedem App-Start.
- Zunächst ausschließlich verfügbare Listenmetadaten: Anbieter, Konto, ID, Titel, Datum, Sportart, Distanz, Dauer und gegebenenfalls Höhenmeter. Fehlende Felder als unbekannt anzeigen.
- Keine zusätzlichen Einzelabfragen für fehlende Spalten, keine FIT-/GPX-Dateien, Messverläufe, Fotos oder Kartenkacheln während dieses Schritts. Eventuell vom Listenendpunkt mitgelieferte Felder erfordern keine zusätzlichen Detailabrufe.
- Übersicht zeigt Anzahl im geprüften Umfang, früheste/späteste gelistete Aktivität und Aufteilung nach Sport/Jahr, soweit aus den vollständig gelesenen Listenseiten ableitbar. Anbieterzählungen und lokal gezählte Treffer getrennt beschriften.
- Sichtbarer Prüfzeitpunkt, Konto, Zeitraum und Berechtigungsumfang. Bei Abbruch, Seitenlimit, Fehler oder HTTP 429 eindeutig **teilweise geladen**, niemals fälschlich **vollständig**.
- Filtern und einzelne/mehrere Aktivitäten auswählen; daraus einen Downloadauftrag mit gewünschten Zusätzen und Formaten erstellen. Strg-/Shift-Auswahl unterstützen.
- Vorhandene lokale Antworten und Dateien für die gewählten Einträge daneben anzeigen. „Aktivität bekannt“ bedeutet nicht „alle Details und Originaldateien vorhanden“.
- Eine solche Liste benötigt weiterhin Netzwerkanfragen und Paginierung; sie spart die einzelnen Datei- und Detailabrufe. Gespeicherte Ansichten und ihre Aufbewahrung müssen zu den jeweiligen Anbieterbedingungen passen.

| Anbieter | Technische Grundlage | Grenzen |
| --- | --- | --- |
| Garmin | Aktivitätsanzahl und paginierte Aktivitäten-/Zeitraumlisten der verwendeten Bibliothek | Kein universelles Verzeichnis aller Gesundheitsmessungen. Eine Aktivitätsliste beweist weder Schlaf- noch Pulsdaten für jeden Tag. Kompatibilität mit der konkret gesperrten Bibliotheksversion prüfen. |
| Strava | Offizieller Endpunkt `GET /athlete/activities` liefert `SummaryActivity` | OAuth, passende Sichtbarkeitsrechte, App-Zulassung, Ratenlimits und Nutzungsbedingungen gelten auch für Listen. Private Aktivitäten benötigen entsprechende Freigabe. Kein Versprechen dauerhafter API-Archive. |
| Komoot | Inoffizielle Projekte können Touren zunächst auflisten | Geplante Routen und aufgezeichnete Aktivitäten klar trennen. Keine öffentliche allgemeine API; Zugriff und Stabilität müssen geprüft werden. |

Für Garmin-Gesundheitsdaten soll die Ansicht zwischen **unterstützt**, **nachweislich vorhanden**, **lokal vorhanden** und **nicht geprüft** unterscheiden. Keine tageweise Komplettabfrage im Hintergrund nur zum Aufbau einer scheinbar kostenlosen Übersicht. Falls eine Kategorie keinen geeigneten Übersichtsabruf hat, diese Grenze offen anzeigen und gegebenenfalls eine ausdrücklich gewählte, begrenzte Prüfung anbieten.

Primärquellen zur Machbarkeit: [Garmin-Bibliothek](https://github.com/cyberjunky/python-garminconnect), [Strava-Referenz](https://developers.strava.com/docs/reference/), [Strava-Ratenlimits](https://developers.strava.com/docs/rate-limits/), [Strava-API-Bedingungen](https://www.strava.com/legal/api_policy), [Komoot-API-Hinweis](https://support.komoot.com/hc/en-us/articles/10331570510618-komoot-API), [KomootGPX mit Listenfunktion](https://github.com/timschneeb/KomootGPX). Recherche belegt eine technische Grundlage, keinen erfolgreichen Test mit den Nutzerkonten.

## 2. Oberfläche vereinfachen und Konten hinzufügen

Vier Hauptreiter: **Konten**, **Download**, **Daten**, **Anleitung**. Anleitung bleibt zuletzt. Bisherige Optionen, Felder, Experten und Offline-Verwaltung in passende Dialoge oder Kontextbereiche verschieben.

Konten beginnt weitgehend leer mit **Konto hinzufügen** und der Auswahl Garmin, Komoot oder Strava. Kompakte Kontokarten zeigen Anbieter, Anzeigename, Status und letzten Abgleich. Mehrere Konten desselben Anbieters bleiben getrennt.

Im Download zunächst nur Konto, Zeitraum, einfache Datenauswahl und Ziel anzeigen. Zusätzliche Einstellungen über **Downloadoptionen**, **Exportoptionen** und **Kontoeinstellungen** öffnen. Übernehmen/Abbrechen und ausdrücklich gespeicherte Kontovorgaben verhindern überraschende dauerhafte Änderungen.

Geplanter neuer Standard: `Downloads\TTN Garmin Export\Garmin`, `Komoot` und `Strava`, jeweils mit getrennten Kontobereichen. Bestehende Garmin-Verzeichnisse beibehalten oder kontrolliert migrieren; kein automatisches Verschieben oder erneutes Herunterladen.

## 3. Anbieterzugriff klären

**Garmin:** Bestehende Funktionen erhalten; Übersicht und Auswahl auf dem gemeinsamen Bestand aufbauen.

**Komoot:** Einzelne geplante Routen und aufgezeichnete Aktivitäten zuerst; Gesamtauswahl optional. Offizielle GPX-Möglichkeiten und Dateiimport berücksichtigen. Inoffizielle Schnittstellen können sich ändern. Zugang, Formate, Metadaten und Lizenzpflichten verwendeter Projekte vor Integration prüfen; GPL-Code nicht ungeprüft in das MIT-Projekt übernehmen.

**Strava:** Offizielle OAuth-Freigabe, Zulassung und ein für eine öffentlich verteilte lokale App geeignetes Anmeldeverfahren klären. Kein gemeinsam eingebettetes Client-Secret als sichere Lösung darstellen. Einzelaktivitäten, Listen und Importe unterscheiden; nicht jede API-Repräsentation ist eine Originaldatei.

Stravas aktuelle Bedingungen beschränken unter anderem bestimmte Massenausleitungen und dauerhafte API-Archive. Lange Pausen lösen ein Berechtigungs- oder Nutzungsproblem nicht. Für zulässige Vorgänge Ratenlimit-Header auswerten, Anfragen budgetieren und Wiederaufnahme ermöglichen; Gesamt- und Leselimits der App berücksichtigen. Für historische Gesamtdaten den offiziellen Kontoexport und dessen Import prüfen. Keine Umgehung durch zusätzliche Tokens oder App-IDs.

## 4. Auftragsliste und Zusammenfassung vor dem Start

Einzelne Aufträge und mehrere Konten gemeinsam unterstützen. Standardreihenfolge **Garmin → Komoot → Strava**, vom Nutzer veränderbar und speicherbar. Aufträge enthalten feste Schnappschüsse ihrer Einstellungen. Verschieben per Pfeilbuttons und optional Ziehen; Wartezustände pro Anbieter sichtbar halten. Optional andere bereite Aufträge weiterbearbeiten, während ein Anbieter pausiert.

Vor dem eigentlichen Start ein Fenster **Aufträge prüfen und starten**:

- Konto/Anbieter, Zeitraum, ausgewählte Aktivitäten und Kategorien, Details, Formate und Zielordner.
- Lokal vorhanden gegenüber noch abzurufen; bekannte/geplante Anfragezahl und Grenzen der Schätzung.
- Getrennte Zeitschätzung für Download, vorgeschriebene Wartezeiten und lokale Dateierzeugung. Unbekannte Dauer ehrlich kennzeichnen.
- Konkrete Hinweise bei vollständigen Tagesverläufen, erstmaliger großer Excel-Erzeugung oder anbieterbedingten langen Wartezeiten.
- **Zurück zu den Einstellungen** oder **Download starten**. Das Öffnen des Fensters beginnt noch keinen eigentlichen Download.

## 5. Anleitung und Bedienhilfen

GitHub-Anleitungen in Deutsch und Englisch sind vorhanden; eingebaute Hilfe parallel pflegen. Bei neuen Oberflächen und Anbietern die Abläufe aktualisieren: Schnellstart, typische Aufgaben, jede Option mit Vorgabe/Wirkung/Beispiel, Dateiformate, Aufwand und Fehlerhilfe.

Zusätzliche Tooltips standardmäßig an, unter Einstellungen global abschaltbar und lokal gespeichert. Hinweise beim Verweilen mit der Maus sowie über Tastaturfokus zugänglich machen. Wichtige Fehlermeldungen und Statusangaben bleiben unabhängig davon sichtbar.

## 6. Programmupdates

Manueller **Nach Updates suchen**-Button, optional Prüfung beim Start. Bevorzugt inkrementelle Dateiupdates statt binärer Delta-Patches: nur geänderte geprüfte Dateien beziehen. Ausschließlich veröffentlichte Versionen des gewählten Kanals, keine unbeaufsichtigten Updates von `main`.

Signiertes Manifest und Hashprüfung, Updatehelfer nach App-Ende, temporäre Installation, Sicherung, Selbsttest und Rücknahme bei Fehler. Nutzerdaten und Anmeldungen erhalten. Laufzeit/Bibliotheken nur bei Bedarf aktualisieren; vorhandene Setup-Reparatur ist noch kein App-Updater. Ein erstes manuelles Update wäre zur Einführung nötig.

## 7. Weitere technische Aufgaben

- Anmeldeschlüssel mit einer geeigneten Betriebssystemlösung schützen; Migration und Umgang mit abgelaufenen Tokens testen.
- UTC und lokale Zeit beim FIT-Import sauber trennen, besonders für Aktivitäten um Mitternacht.
- Wheel-Pfadprüfung im portablen Build an die strengere Starterprüfung angleichen.
- GitHub Actions nach Prüfung auf konkrete Commit-SHAs pinnen.
- Neue Anbieter und UI schrittweise mit synthetischen Tests und ausdrücklich autorisierten Kontotests prüfen. Keine feste Beschleunigung oder vollständige Kontosicherung versprechen.

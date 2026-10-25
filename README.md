# TTN Activity Export

**Deine Aktivitäten. Deine Daten. Alles lokal.**

**Aktivitäten von Garmin und Komoot herunterladen, Strava-Datenpakete importieren und deine Daten lokal durchsuchen, auf Karten ansehen und als CSV, Excel oder JSON exportieren.**

TTN Activity Export ist eine lokale Desktop-App mit deutscher und englischer Oberfläche, hellem und dunklem Farbschema und einem Windows-Starter ohne vorausgesetzte Python-Installation. Du kannst einzelne Datenarten oder mehrjährige Zeiträume sichern und aus dem lokalen Bestand weitere Exporte erstellen.

Unabhängiges Community-Projekt; kein offizielles Produkt von Garmin, Komoot oder Strava.

[Anleitung auf Deutsch](docs/ANLEITUNG.md) · [English user guide](docs/USER_GUIDE.md) · [Downloads](https://github.com/starbase64/ttn-activity-export/releases) · [Änderungen](CHANGELOG.md) · [Planung](ROADMAP.md)

## Namensänderung

Die App wird ausschließlich als **TTN Activity Export** ausgeliefert. Bestehende Profile, Downloads und Datenbanken bleiben lesbar.

## Aktueller Stand

Die veröffentlichte Version ist **0.6.9**. **Garmin Connect wird unterstützt. Strava ist eine lokale Importquelle. Die Komoot-Online-Anbindung bleibt experimentell.**

[Windows 10/11 x64 herunterladen](https://github.com/starbase64/ttn-activity-export/releases/download/v0.6.9/TTN-Activity-Export-Windows-0.6.9.zip) · [Release und Prüfsumme](https://github.com/starbase64/ttn-activity-export/releases/tag/v0.6.9)

ZIP vollständig entpacken und **Start-TTN-Activity-Export.cmd** doppelklicken. Beim ersten Start lädt der Starter eine private Python-Laufzeit und fehlende Pakete; eine eigene Python-Installation oder Administratorrechte sind nicht erforderlich. Internet ist für die Ersteinrichtung nötig. Bestehende Profile und Datenbanken bleiben verwendbar.

## Neu in Version 0.6

Vier Hauptreiter: **Konten, Download, Daten, Anleitung**. Zusätzliche Einstellungen liegen unter **Optionen …** mit Übernehmen/Abbrechen. Das Protokoll öffnet sich in einem eigenen Fenster.

**Garmin:** Bestandsliste ohne Detail-/Dateidownload, einzelne Aktivitäten auswählen, getrennte Kontovorgaben, gespeicherte und sortierbare Aufträge und eine Zusammenfassung vor dem Start. Standardaktion ist **Nur herunterladen**. Für CSV/Excel/JSON die Aktion **Download und Dateien exportieren** beziehungsweise **Nur lokal exportieren** wählen.

**Strava:** ausschließlich lokaler Import eines vom Nutzer selbst heruntergeladenen Konto-ZIPs oder entpackten Ordners. Kein API-Schlüssel, keine Strava-Anmeldung und keine automatischen Strava-Abfragen in der App. Aktivitätenübersicht aus `activities.csv` und referenzierte FIT/GPX/TCX-Dateien (auch `.gz`) werden eingelesen. Danach lokal filtern, Karten ansehen und ausgewählte Tabellen exportieren. Fotos, Kommentare und andere Kontoinhalte werden nicht importiert. [Anleitung](docs/ANLEITUNG.md#strava-als-lokale-importquelle).

**Komoot:** Experimentelle Anmeldung per E-Mail/Passwort, Bestandsliste für geplante oder aufgezeichnete Touren und ausgewählter GPX-Export. Unter Windows lässt sich die Anmeldung verschlüsselt merken. Das erste Aktivitätsdatum wird gespeichert und ist per Button wiederherstellbar. Noch nicht in der gemeinsamen Auftragsliste enthalten. Oben bei der Sprache lassen sich veröffentlichte GitHub-Updates prüfen; die Prüfung beim Start ist optional. Automatische Installation und Delta-Updates folgen separat.

Neue Konten verwenden `Downloads\TTN_Activity_Export\Garmin` beziehungsweise `Komoot`/`Strava`. Bestehende Garmin-Verzeichnisse und der interne Profilname bleiben erhalten. Es werden keine alten Daten automatisch verschoben. [Testhinweise](RELEASE_NOTES.md).

## Was die App kann

| Aufgabe | Möglichkeiten |
| --- | --- |
| Daten auswählen | Datumsbereich auch über mehrere Jahre, einzelne Kategorien, Sportart und optionale Aktivitätszusätze |
| Aktivitätenliste erstellen | Eine lesbare Zeile pro Aktivität, etwa Datum, Name, Sportart, Distanz und Dauer |
| Gesundheitsdaten sichern | Tageskennzahlen oder vollständige Verläufe für unterstützte Kategorien; Verfügbarkeit hängt vom Konto und Gerät ab |
| Dateien exportieren | CSV, XLSX, JSON; optionale Originaldateien, GPX, TCX, KML und Runden-CSV, soweit Garmin sie liefert |
| Lokal weiterarbeiten | Gemeinsamer SQLite-Bestand pro Konto; fortsetzbare Downloads und Exporte ohne erneute Anmeldung im Offline-Modus |
| Daten ansehen | Aktivitätstabelle mit Suche und Filtern, Mehrfachauswahl mit Strg/Shift, große Karte rechts und Heatmap |
| Eigene Dateien nutzen | Unterstützte FIT-, GPX- und TCX-Dateien sowie ZIP-Archive importieren; Datenbanksicherung erstellen und öffnen |
| Aufwand begrenzen | Vorschau mit Abruflimit, „Nur herunterladen“, gebündelte Abfragen, 1–50 parallele Abfragen und geprüfte Wiederverwendung unveränderter Exportdateien |
| Ablauf verfolgen | Restzeitschätzung beim Download, Fortschritt der Dateierzeugung und Sitzungslogs mit Öffnen-/Exportieren-Buttons |
| Oberfläche anpassen | Deutsch/Englisch und Hell/Dunkel; Farbschema wird lokal gespeichert |

„Alle unterstützten Daten“ ist kein vollständiges Backup sämtlicher Garmin-Kontofunktionen. Die Offline-Gesamtsicherung umfasst 27 unterstützte Datenarten; Tagesrohdaten als Wellness-FIT-ZIP sind zusätzlich ausdrücklich auswählbar. Diese ZIPs werden unverändert gespeichert und ersetzen keine JSON-Verläufe automatisch.

## Unter Windows starten

1. Ein **Windows-Starter-ZIP** für die gewünschte Version herunterladen.
2. Vollständig in einen eigenen, beschreibbaren Ordner entpacken. Nicht im ZIP starten.
3. `Start-TTN-Activity-Export.cmd` doppelklicken.
4. Beim ersten Start die Einrichtung abwarten. Anschließend unter **Konten** ein Garmin-Konto hinzufügen und über **Anmelden / Einstellungen** anmelden.
5. Unter **Download** die Vorgabe **Aktivitätenliste**, den Zeitraum und die Aktion **Download und Dateien exportieren** wählen; CSV eingeschaltet lassen.
6. Bei Bedarf **Online-Bestand anzeigen**, einzelne Aktivitäten markieren und die Auswahl übernehmen. Zur Auftragsliste hinzufügen, anschließend **Aufträge prüfen und starten** drücken.

Der Starter richtet eine eigene Python-Laufzeit und festgelegte Abhängigkeiten ein. Keine Administratorrechte und keine eigene Python-Installation nötig. Der erste Start braucht Internet; Python kommt von python.org, Pakete von PyPI/files.pythonhosted.org. Versionen und SHA-256-Prüfsummen sind in `windows-dependencies.lock.json` festgelegt. Fehlende oder beschädigte Komponenten werden beim Start bei Bedarf repariert. Dabei wird kein App-Update von GitHub installiert.

Bei Einrichtungsproblemen: Konsolenmeldung und `setup.log` im Programmordner prüfen. Weitere Abläufe, Beispiele und Fehlerhilfe stehen in der [ausführlichen Anleitung](docs/ANLEITUNG.md).

## Downloads, Offline-Bestand und Exportdateien

**Nur herunterladen** speichert die Auswahl von Export/Optionen in der Kontodatenbank, ohne anschließend CSV/Excel/JSON-Dateien zu erzeugen. Die Aktion **Download und Dateien exportieren** beschafft benötigte Daten und erstellt die ausgewählten Dateien. Mit **Nur Offline-Daten verwenden** erfolgt der Export ausschließlich aus dem lokalen Bestand.

Bestehende Konten behalten ihren bisherigen Standard **Downloads\Garmin_Export**; neue Konten verwenden die oben beschriebene Ordnerstruktur. Darunter liegen getrennte Kontobereiche mit SQLite-Datenbank und standardmäßig `exports/current`. Neue Ergebnisordner bedeuten nicht automatisch neue Downloads. Verwende zum Fortsetzen denselben Datenbestand. Die letzten Tage können entsprechend der eingestellten Aktualisierung erneut geladen werden.

Große Erstexporte, vollständige Messverläufe und Excel-Dateien brauchen Zeit. Mehr parallele Abfragen heben den gemeinsamen Mindestabstand zwischen Anfragen nicht auf. Garmin kann Anfragen begrenzen; bei HTTP 429 stoppt der Lauf und die App zeigt eine Abrufpause. Bereits geladene Antworten bleiben erhalten. Eine feste Beschleunigung oder Dauer wird nicht zugesichert.

## English

A local Garmin Connect desktop app for downloading selected data or years of history, keeping a reusable SQLite archive, browsing activities and maps, and exporting CSV, Excel or JSON. Includes German/English UI, persistent light/dark mode, bounded previews, download ETA and session logs. The Windows starter installs a private Python runtime and pinned, hash-verified dependencies; no existing Python installation is required.

**Release: 0.6.9. [Download the Windows x64 starter](https://github.com/starbase64/ttn-activity-export/releases/tag/v0.6.9). Extract the ZIP and double-click Start-TTN-Activity-Export.cmd. First use installs a private Python runtime and pinned dependencies; no system Python or admin rights are required. Garmin is supported. Strava imports user-downloaded ZIPs/folders only. Komoot offers experimental sign-in, inventory and GPX export.** See the [English user guide](docs/USER_GUIDE.md) for installation, examples, settings and troubleshooting, and [Actions](https://github.com/starbase64/ttn-activity-export/actions) for automated Windows validation.

## Entwicklung / Development

```sh
python -m venv .venv
# Activate .venv for your operating system, then:
python -m pip install -r requirements.txt -r requirements-build.txt
python -m pytest -q
python app.py --demo
```

Synthetic tests do not access Garmin accounts. `python app.py --smoke-test` checks app/export/archive/import integration. The GUI source/tests also run on Linux with dependencies (GUI checks here use Qt offscreen mode); the automatic starter targets **Windows 10/11 x64**. No macOS build has been validated. There is no Android/iOS version. On Linux create a Python virtual environment, install requirements and run `python app.py`; Windows CMD/PowerShell launchers do not apply.

Build a starter:

```sh
python build_starter.py dist/TTN-Activity-Export-Windows-Starter.zip
```

Regenerate dependency locks only after reviewing updates. Download Windows wheels with `pip download --only-binary=:all: --platform win_amd64 --python-version 3.13 --implementation cp --abi cp313 -r requirements.txt -d windows-wheels`, then run `python generate_windows_lock.py windows-wheels`. The generator checks PyPI SHA-256 values. Do not commit downloaded wheels or runtimes. `.github/workflows/starter.yml` checks native Windows setup, offline startup and cached dependency repair. A separate manual Windows workflow can build the full PyInstaller package.

The GitHub-readable manuals describe the current application. The built-in help and its HTML versions remain in [German](docs/guide-de.html) and [English](docs/guide-en.html). After editing the Markdown manuals, run `python generate_help.py` to regenerate embedded help and HTML copies.

## Datenschutz, Herkunft und Lizenz / Privacy and credits

Das Passwort wird nicht gespeichert. Gemerkte Anmeldeschlüssel liegen lokal im App-Profil und sind derzeit nicht zusätzlich verschlüsselt. **Sitzung merken** abwählen deaktiviert die automatische Anmeldung; **Lokale Sitzung entfernen** löscht die gespeicherten Schlüssel. Der interne Profilname `GarminExportStudio` bleibt für bestehende Installationen erhalten.

Zugangsdaten, GPS-Tracks, Datenbanken und Nutzerexporte gehören nicht in öffentliche Issues oder ins Repository. Onlinekarten und externe Kartenansichten nutzen Drittanbieter; Details stehen in der Anleitung.

MIT for this application's code; dependency licences remain applicable. Uses [python-garminconnect](https://github.com/cyberjunky/python-garminconnect), PySide6, openpyxl and fitdecode. **GarminDB is not a code dependency**; its approach informed research. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and [LICENSE](LICENSE). Garmin and other provider names are trademarks of their respective owners. This app is neither made nor endorsed by them.

[Validation notes](docs/VALIDATION.md) · [Changelog](CHANGELOG.md) · [Roadmap](ROADMAP.md)

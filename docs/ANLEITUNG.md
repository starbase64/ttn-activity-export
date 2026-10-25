# TTN Activity Export – Anleitung

Für den Quellstand **0.5.8-preview**. [English](USER_GUIDE.md) · [Projektübersicht](../README.md) · [Geplante Funktionen](../ROADMAP.md)

Die App arbeitet lokal auf deinem Computer. Sie kann unterstützte Garmin-Connect-Daten herunterladen, in einer lokalen Datenbank aufbewahren und daraus Dateien erstellen. Du entscheidest über Zeitraum, Datenarten und Ausgabeformat. Strava und Komoot sind noch nicht integriert. Ältere Downloads der App können weniger Funktionen enthalten als hier beschrieben.

## Inhalt

- [Erster Start](#erster-start)
- [Konto und Anmeldung](#konto-und-anmeldung)
- [Eine einfache Aktivitätenliste erstellen](#eine-einfache-aktivitätenliste-erstellen)
- [Download, Export und Offline-Sicherung](#download-export-und-offline-sicherung)
- [Datenarten und Detailgrad](#datenarten-und-detailgrad)
- [Ausgabeformate und Tabellenaufbau](#ausgabeformate-und-tabellenaufbau)
- [Optionen verstehen](#optionen-verstehen)
- [Felder und Expertenabfragen](#felder-und-expertenabfragen)
- [Lokale Daten ansehen und Karten verwenden](#lokale-daten-ansehen-und-karten-verwenden)
- [Sichern, importieren und auf einen anderen PC umziehen](#sichern-importieren-und-auf-einen-anderen-pc-umziehen)
- [Fortschritt, Protokolle und Fehlerhilfe](#fortschritt-protokolle-und-fehlerhilfe)
- [Begriffe und Grenzen](#begriffe-und-grenzen)

## Erster Start

1. Lade das Windows-Starter-ZIP der gewünschten Version herunter. Prüfe die Versionshinweise: Der aktuelle Quellstand und das letzte veröffentlichte Release können verschieden sein.
2. Entpacke das gesamte ZIP in einen beschreibbaren Ordner, etwa in deinem Benutzerordner. Starte die App nicht innerhalb des ZIPs.
3. Öffne `Start-TTN-Activity-Export.cmd` per Doppelklick. Beim ersten Start werden eine eigene Python-Laufzeit und die festgelegten Bibliotheken eingerichtet. Lass das Konsolenfenster geöffnet, bis die App erscheint.
4. Wähle oben Deutsch oder Englisch. Daneben wechselst du zwischen hellem und dunklem Farbschema; die Farbwahl bleibt nach einem Neustart erhalten.
5. Melde dich im Reiter **Konto** an. Für einen ersten Versuch reichen ein paar Tage und die Aktivitätenliste.

Du musst Python nicht selbst installieren. Der Starter verändert keine vorhandene Python-Installation und benötigt keine Administratorrechte. Die Erstinstallation braucht Internet. Die lokalen Ordner `runtime/` und `.setup-cache/` gehören zur Einrichtung; der Cache kann für spätere Reparaturen verwendet werden. Wird die Einrichtung unterbrochen, starte denselben Starter erneut. Bei Problemen findest du Meldungen im Konsolenfenster und in `setup.log` im Programmordner. Unternehmensrichtlinien können den Start von PowerShell-Skripten verhindern.

Die Reiter heißen derzeit **Konto**, **Export**, **Optionen**, **Felder**, **Experten**, **Offline-Daten**, **Daten** und zuletzt **Anleitung**. Für den Einstieg brauchst du normalerweise nur Konto, Export und gegebenenfalls Optionen. Die geplante vereinfachte Oberfläche ist noch nicht enthalten.

## Konto und Anmeldung

Trage E-Mail-Adresse und Passwort deines Garmin-Kontos ein und klicke auf **Anmelden**. Falls Garmin eine Zwei-Faktor-Authentifizierung verlangt, folge dem Dialog. **China-Konto** ist nur für Konten auf garmin.cn gedacht.

**Sitzung lokal merken** speichert Anmeldeschlüssel, damit die App die Sitzung beim nächsten Start wiederherstellen kann. Das Passwort selbst wird nicht gespeichert. Die Schlüssel sind derzeit nicht zusätzlich verschlüsselt; schütze deshalb dein Windows-Benutzerkonto und gib das App-Profil nicht weiter. Der angezeigte Sitzungspfad hilft, den Speicherort zu finden. Der interne Profilname lautet weiterhin `GarminExportStudio`.

Das Abwählen von **Sitzung lokal merken** deaktiviert die automatische Wiederherstellung. Es löscht vorhandene Schlüssel nicht. Verwende dafür **Lokale Sitzung entfernen**; das geht auch ohne vorherige Anmeldung. Bei abgelaufenen Schlüsseln kann eine erneute Anmeldung erforderlich sein.

Die Option **Erste Aktivität als Anfangsdatum vorschlagen** ermittelt das früheste Aktivitätsdatum des Kontos. Dieses Datum und deine eigenen Anfangsdaten für Export und Daten werden pro Konto gespeichert. **Erste Aktivität** auf der Exportseite setzt den Anfang auf den gespeicherten Kontowert zurück. Das Datum begrenzt die App nicht: Gesundheitsdaten können auch vor der ersten Aktivität vorhanden sein. Das Enddatum solltest du vor jedem Lauf kontrollieren.

Nach dem Anmelden wird die Sportartenliste geladen. Unter **Optionen → Liste aktualisieren** kannst du sie erneut abrufen. Der Sportartenfilter wirkt auf Aktivitäten, nicht auf Schlaf, Schritte oder andere Gesundheitskategorien.

## Eine einfache Aktivitätenliste erstellen

Beispiel: Du möchtest alle Fahrradtouren eines Monats in einer CSV-Datei mit Datum, Name, Distanz und Dauer.

1. Öffne **Export** und klicke **Nur Aktivitätsliste (CSV)**. Damit wird die Aktivitätenübersicht ausgewählt und zusätzliche Aktivitätsabfragen werden abgewählt.
2. Wähle den ersten und letzten Tag. **Bis einschließlich** bedeutet, dass auch dieser Tag berücksichtigt wird. Mehrere Jahre sind möglich; es gibt kein allgemeines 365-Tage-Limit für den Gesamtzeitraum.
3. Wähle unter **Optionen → Sportart** den gewünschten Typ. Für alle Sportarten lass den Filter leer beziehungsweise wähle alle.
4. Prüfe auf Export den Zielordner. Standard ist `Downloads\Garmin_Export`.
5. Lass **Aktivitäten: eine Tabellenzeile pro Aktivität** eingeschaltet. Für eine einzige zusammenhängende Datei lass die Trennung nach Jahr ausgeschaltet.
6. Klicke bei Bedarf **Vorschau anzeigen**. Die Vorschau lädt nur eine begrenzte Stichprobe; sie prüft nicht den gesamten Zeitraum.
7. Klicke **Export starten**, anschließend **Ergebnisordner öffnen**.

Für diese Tabelle brauchst du keine Originaldateien, Wetterdaten oder Messverläufe. Die Kategorie **Aktivitäten – Übersicht** muss ausgewählt sein; allein ein Sportartenfilter aktiviert sie nicht. Garmin liefert nicht bei jeder Aktivität jedes Feld. Eine manuelle Aktivität kann beispielsweise keine GPS-Strecke enthalten.

## Download, Export und Offline-Sicherung

Diese Aktionen erfüllen unterschiedliche Aufgaben:

| Aktion | Ergebnis |
| --- | --- |
| **Nur herunterladen** | Speichert die Auswahl von Export und Optionen direkt im Kontobestand; erzeugt danach keine CSV-, Excel- oder JSON-Ausgabedateien. Anmeldung nötig. |
| **Export starten** | Lädt benötigte Daten beziehungsweise nutzt gespeicherte Antworten und erzeugt die ausgewählten Ausgabeformate. |
| **Nur Offline-Daten verwenden** | Vorschau und Export lesen ausschließlich die gewählte lokale Datenbank. Fehlende Daten werden nicht automatisch online ergänzt. |
| **Alle unterstützten Daten sichern / ergänzen** | Sichert die 27 dafür vorgesehenen Datenarten im Exportzeitraum mit vollständigen Gesundheitsverläufen; Aktivitätszusätze werden auf Offline-Daten separat eingestellt. |
| **Nur gewählte Daten sichern / ergänzen** | Verwendet die gewählten Kategorien und den Gesundheitsdetailgrad der Exportseite; Aktivitätszusätze stammen aus den Einstellungen auf Offline-Daten. |

**Nur herunterladen** ist sinnvoll, wenn du erst Daten sichern und später in Ruhe Dateiformate ausprobieren möchtest. Aktivierte Expertenabfragen sind dafür nicht vorgesehen; verwende für diese den normalen Export.

**Alle unterstützten Daten** bedeutet weder sämtliche denkbaren Kontodaten noch alle Daten unabhängig vom Datum. Der Von/Bis-Zeitraum auf Export gilt weiter. Diese Sicherung ignoriert den Sportartenfilter und verwendet die eigenen Optionen **Aktivitätsdetails mitsichern**, **Original-Aktivitätsdateien mitsichern** sowie weitere Formate. Details und Originale sind dort anfänglich eingeschaltet. Deshalb kann sie deutlich mehr abrufen als eine einfache CSV-Liste. Umgekehrt kann eine früher durchgeführte Teilsicherung weniger enthalten als ein späterer Export mit allen Kategorien und Zusätzen.

Unterhalb des Zielordners wird pro Konto ein eigener Bestand mit `garmin-offline.sqlite` geführt. Online-Export und Offline-Sicherung können denselben Bestand nutzen. Zum Fortsetzen wähle denselben Ausgabeordner und dieselbe Datenbank. Eine neu erzeugte CSV-Datei bedeutet nicht, dass ihre Quelldaten erneut heruntergeladen wurden. Die Option **Letzte Tage neu laden** kann aktuelle Daten bewusst auffrischen.

Mit **Gespeicherten Bestand prüfen** erhältst du eine Übersicht der lokalen Abdeckung. **Übersprungene Abfragen trotzdem laden** holt im eingestellten Zeitraum experimentell ausgelassene Anfragen nach. Ein gespeicherter leerer Garmin-Datensatz, ein fehlgeschlagener Abruf und eine ungeprüft übersprungene Anfrage sind unterschiedliche Zustände.

## Datenarten und Detailgrad

Die Kategorien umfassen Tagesübersicht, Puls, Schlaf, Stress, Body Battery und Ereignisse, Schritte, Etagen, Intensitätsminuten, Atmung, SpO₂, HRV, Ruhepuls, Gewicht, Körperzusammensetzung, Blutdruck, Trinkmenge, Trainingsstatus, Trainingsbereitschaft, VO₂max, Fitnessalter, Ausdauerwert, Hill Score und Aktivitäten. Geräte, Rekorde und aktive Ziele sind aktuelle Kontostände, keine vollständigen historischen Verzeichnisse.

Nicht jede Uhr misst jede Kategorie. Garmin kann leere Antworten liefern oder eine Funktion für das Konto nicht anbieten. Die App kann fehlende Messungen nicht erzeugen.

Unter **Export → Ausgabe → Gesundheitsdaten** wählst du:

- **Vollständige Messverläufe:** Für Zeitreihen, Schlafphasen und detaillierte Auswertungen. Viele Abrufe bleiben tageweise.
- **Tageskennzahlen:** Schnellere Zusammenfassungen ohne vollständige Verläufe. Gilt für Puls, Schlaf, Stress, Body Battery, Schritte, Etagen, Intensitätsminuten, Atmung, Trinkmenge und Ruhepuls. Andere Kategorien bleiben unverändert.

**Tagesrohdaten als FIT-Datei** speichert zusätzlich Wellness-ZIPs unverändert. Die App wandelt deren Inhalt noch nicht in Tabellen um und verwendet sie nicht automatisch als Ersatz für gewählte JSON-Abfragen. Diese optionale Kategorie gehört nicht zur pauschalen Sicherung der 27 Datenarten.

Unter Optionen kannst du für Aktivitäten Messverläufe, Runden, Zwischenzeiten, Herzfrequenzzonen, Trainingssätze und Wetter zuschalten. Das sind zusätzliche Abrufe pro Aktivität. **ORIGINAL** lädt die von Garmin angebotene Originaldatei, häufig als ZIP mit FIT-Datei. GPX, TCX, KML und CSV für Runden sind weitere separate Downloads, sofern verfügbar. Die CSV-Option bei diesen Originaldownloads ist nicht die einfache Aktivitätenübersicht.

## Ausgabeformate und Tabellenaufbau

| Einstellung | Wann sie hilft |
| --- | --- |
| **CSV** | Für einfache Listen und die Weiterverarbeitung in Tabellenprogrammen. Trennzeichen unter Optionen einstellbar. |
| **XLSX** | Für Excel-Arbeitsmappen. Große Datenmengen brauchen zusätzliche Zeit zum Schreiben und Komprimieren. |
| **JSON** | Für verschachtelte Originalantworten und eigene Auswertungen. Feldfilter reduzieren diese Rohantworten nicht. |
| **Langformat** | Verschachtelte Detailwerte mit ihren Pfaden ausgeben; viele Zeilen möglich. |
| **Breitformat** | Werte als Datensätze mit Spalten ausgeben; bei unterschiedlich aufgebauten Antworten viele Spalten möglich. |
| **Eine Zeile pro Aktivität** | Lesbare Aktivitätenübersicht statt einer Auflösung sämtlicher verschachtelter Detailwerte. |
| **Dateien nach Jahr trennen** | Kleinere Teildateien bei mehrjährigen Exporten. |

Standardmäßig liegen erzeugte Ergebnisse pro Konto unter `exports/current`. Ein neuer Export aktualisiert die von der App verwalteten Dateien dort. Sichere Ergebnisse separat, wenn du einen bestimmten Stand behalten möchtest. **Separate Exportordner behalten** aktiviert getrennte Ergebnisordner; ältere vorhandene Ordner werden nicht automatisch entfernt.

**Unveränderte Exportdateien wiederverwenden** ist standardmäßig an. Die App prüft Quellinhalt, Ausgabeeinstellungen und Prüfsummen der vorhandenen Dateien. Unveränderte Gruppen können erhalten bleiben; geänderte, fehlende oder beschädigte Dateien werden neu erzeugt. Bereits vorhandene alte Exporte benötigen gegebenenfalls einmalig eine Neuerstellung. Auch das Lesen der Datenbank und die Integritätsprüfung brauchen etwas Zeit. Ausschalten erzwingt eine Neuerstellung.

Nach dem Download werden Antworten gelesen, in Tabellen umgewandelt, Excel-Dateien komprimiert, Prüfsummen berechnet und Dateien veröffentlicht. Das erklärt Wartezeit nach dem letzten Netzabruf. **Nur herunterladen** verschiebt diese Dateierzeugung auf später. Die Dateierzeugung selbst lässt sich derzeit nicht abbrechen; der Download kann gestoppt werden.

## Optionen verstehen

Die folgenden Werte gelten bei einem frischen Start ohne geladene Vorlage. Prüfe nach dem Laden einer Vorlage die tatsächlich angezeigten Werte.

| Option | Vorgabe | Wirkung |
| --- | --- | --- |
| Abrufpause | 0,5 Sekunden | Gemeinsamer Mindestabstand zwischen Anfragestarts aller Threads. |
| Parallele Abfragen | 3; einstellbar 1–50 | Überlappt Wartezeit auf Antworten. Mehr Threads überwinden den Mindestabstand nicht. |
| Zeitraumabfragen bündeln | An | Nutzt Bereichsabfragen, wo die Datenart sie unterstützt. |
| Aktivitäten: Tage je Zeitraumabfrage | 31; einstellbar 1–365 | Größe eines Abrufblocks, nicht maximale Gesamthistorie. |
| Gesundheit: Tage je Zeitraumabfrage | 28; einstellbar 1–28 | Blockgröße für unterstützte Kennzahlenabfragen. Detaillierte Puls-/Schlafdaten bleiben täglich. Body Battery wird höchstens in 7-Tage-Blöcken geladen. |
| Netzwerkfehler wiederholen | 2 | Begrenzte Wiederholungen kurzzeitiger Fehler; keine Umgehung einer Sperre. |
| Letzte Tage neu laden | 2 | Jüngere gespeicherte Tage erneut prüfen. 0 nutzt vorhandene Antworten. |
| Vermutlich leere Abfragen überspringen | Aus, experimentell | Nutzt Hinweise aus Tagesübersichten. Übersprungene Details bleiben ungeprüft; die Regel beweist keine Datenlosigkeit. |
| Vorschau: Zeilen je Tabelle | 10 | Begrenzte Zahl angezeigter Beispielzeilen. |
| Vorschau: maximale Abfragen | 12 | Begrenzt den Abrufaufwand der Vorschau. |
| CSV-Trennzeichen | Semikolon | Bei Bedarf Komma oder Tabulator wählen. |

Die Offline-Sicherungsaktionen verwenden zusätzlich Schutzvorgaben, etwa mindestens 0,25 Sekunden Abrufpause. Die an anderer Stelle erlaubte Eingabe kleinerer Werte ist deshalb keine Garantie für die effektive Sicherungsgeschwindigkeit.

Bei 0,5 Sekunden Abstand können langfristig höchstens ungefähr zwei Anfragen pro Sekunde starten, unabhängig von der Threadzahl. Zusätzlich begrenzen Serverantwortzeit, lokale Verarbeitung und Ratenlimits den Durchsatz. Die App kennt keine allgemeingültige sichere Garmin-Grenze. Erfolgreiche Läufe mit einem bestimmten Konto sind keine Zusage für andere Konten oder spätere Zeitpunkte.

Mit **Auswahl als Vorlage speichern** und **Vorlage laden** lassen sich Einstellungen wiederverwenden. Prüfe vor dem Start insbesondere Zeitraum, Konto, Zielordner und Datenquelle. Vorlagen sind keine Datensicherung.

## Felder und Expertenabfragen

Unter **Felder** kannst du die Ausgabe auf bestimmte Pfade beschränken. Leer bedeutet alle Felder. **Felder laden** liest den Starttag der ersten gewählten Kategorie; eine leere Antwort zeigt deshalb möglicherweise keine nutzbaren Felder. Übernimm markierte Felder oder trage je Zeile ein Pfadmuster ein, beispielsweise `/totalSteps` oder `/heartRateValues/*/*`.

Die Filter gelten für CSV/Excel und für alle gewählten Kategorien. Ein Muster, das zu einer Kategorie nicht passt, kann deren sichtbare Ausgabe stark reduzieren. Rohdaten-JSON, Cache und Originaldateien bleiben vollständig. Beginne bei unerwartet leeren Tabellen mit einer leeren Feldauswahl.

**Experten** erlaubt zusätzliche freigegebene Leseabfragen der Garmin-Bibliothek. Lies die eingeblendete Methodendokumentation und verwende gültige JSON-Parameter. Platzhalter sind `{date}`, `{start}` und `{end}`. **Pro Tag ausführen** ist für Tagesmethoden gedacht; bei Bereichsabfragen muss es passend ausgeschaltet werden. Pflichtparameter und Paginierung übernimmt die App nicht beliebig automatisch. Für normale Aktivitätslisten brauchst du diesen Reiter nicht.

## Lokale Daten ansehen und Karten verwenden

1. Öffne **Daten**, wähle die SQLite-Datei und klicke **Daten laden**.
2. Filtere nach Suchtext, Sportart, Zeitraum und Mindestdistanz. Der Datumsfilter kann Aktivitäten ausblenden, die bereits gespeichert sind.
3. Klicke eine Aktivität an. Die Karte rechts zeigt die lokal verfügbare Strecke.
4. Mit **Strg** wählst du einzelne zusätzliche Zeilen; mit **Shift** einen zusammenhängenden Bereich. Das Auswahlmenü kann alle gefilterten Zeilen markieren.
5. Aktiviere bei Bedarf die Heatmap oder exportiere eine Auswahl. Spalten und Filtervorlagen erleichtern wiederkehrende Ansichten.

Eine Aktivitätenübersicht enthält nicht zwingend einen Streckenverlauf. Für Karten werden lokal vorhandene Tracks aus unterstützten Details oder importierten Originaldateien benötigt. Fehlen Tracks, ist eine leere Karte kein Beleg dafür, dass die Aktivität fehlt. Indoor- und manuelle Aktivitäten können grundsätzlich ohne GPS sein.

Standardmäßig funktioniert die Streckenansicht ohne Online-Kartenhintergrund. Eine eingeschaltete Onlinekarte lädt Kartenkacheln von einem externen Anbieter. Deren Bildfarben ändern sich nicht automatisch mit dem dunklen App-Schema. Die Google-Maps-Ansicht benötigt einen eigenen API-Schlüssel und kann nach Googles Bedingungen Kosten verursachen. Für **Google My Maps** exportierst du KML, importierst es dort und erstellst die Freigabe auf der Google-Seite. Die lokale Heatmap wird dabei nicht als Heatmap übertragen. Prüfe vor einer Freigabe private Start-/Zielpunkte.

## Sichern, importieren und auf einen anderen PC umziehen

Im Reiter Daten findest du unter **Werkzeuge** Dateiimport, Datenbanksicherung, Prüfung und Ergänzung fehlender Daten. Unterstützte FIT-, GPX- und TCX-Dateien können auch aus ZIP-Archiven importiert werden. Ein Import erzeugt nur Daten, die sich aus dem jeweiligen Dateiformat lesen lassen; er stellt keine vollständige Garmin-Gesundheitshistorie her.

Mit **Sicherung erstellen** erzeugst du eine Datenbanksicherung. Diese kannst du später über **Datei öffnen** auswählen. Schließe laufende Schreibvorgänge ab, bevor du Dateien manuell kopierst. Zum Umzug richte die App auf dem neuen Computer ein, übertrage die Sicherung und öffne sie dort. Eine Garmin-Anmeldung ist für reine Offline-Auswertungen nicht nötig.

**Exportcache übernehmen** hilft, vorhandene ältere Antwort-Caches in den lokalen Bestand zu übernehmen. Eine beliebige bearbeitete CSV- oder Excel-Datei ist dagegen kein vollständiges Datenbankbackup und lässt sich nicht allgemein verlustfrei zurückimportieren. Originaldateien und Datenbank sichern, wenn du später weitere Auswertungen erstellen möchtest. Anmeldeschlüssel musst du dafür nicht mitnehmen.

## Fortschritt, Protokolle und Fehlerhilfe

Die Download-Restzeit wird aus dem beobachteten Durchsatz geschätzt. Zu Beginn, bei Cache-Treffern, Wiederholungen oder wechselnden Datenarten kann sie schwanken. Nach dem Download beschreibt der Status lokale Verarbeitungsschritte. Die Download-Restzeit ist keine verbindliche Gesamtdauer einschließlich aller Excel-Dateien.

**Log öffnen** öffnet die gespeicherte Protokolldatei. **Log der heutigen Sitzung exportieren** sichert das Protokoll der aktuellen App-Sitzung zum Weitergeben. Die Anzeige im Fenster ist begrenzt; die Datei enthält mehr Verlauf. Prüfe Logs vor einer öffentlichen Veröffentlichung auf persönliche Angaben und lokale Pfade.

| Problem | Was du prüfen kannst |
| --- | --- |
| Datenansicht leer | Richtige SQLite-Datei geöffnet? Aktivitätenübersicht tatsächlich geladen? Zeitraum/Sportfilter passend? Gegebenenfalls alten Exportcache übernehmen. |
| CSV enthält nicht die erwartete Liste | Vorgabe „Nur Aktivitätsliste (CSV)“ verwenden, Sportart prüfen und Feldfilter leeren. |
| Keine Strecke auf der Karte | Trackdaten lokal vorhanden? Aktivität mit GPS aufgezeichnet? Übersicht allein reicht nicht immer. |
| `GarminConnectConnectionError` | Verbindung und Garmin-Erreichbarkeit prüfen; bereits gespeicherte Daten behalten und später denselben Lauf fortsetzen. |
| `GarminConnectTooManyRequestsError` / HTTP 429 | Angezeigte Abrufpause abwarten. Der Lauf stoppt; später manuell fortsetzen. Bereits gestartete Anfragen können noch fertig werden. |
| Ständig neue Anmeldung | Sitzung merken aktivieren, Hinweise zur Speicherung prüfen; bei ungültigen Schlüsseln lokale Sitzung entfernen und neu anmelden. |
| Download fertig, App arbeitet weiter | Status und Log auf Umwandlung, Excel-Komprimierung und Prüfsummen prüfen. Beim nächsten Mal gegebenenfalls „Nur herunterladen“ oder weniger Formate verwenden. |
| Nach Fortsetzung neue Anfragen | Aktualisierung der letzten Tage, andere Kategorien/Detailgrade oder fehlende Antworten können neue Abrufe erfordern. |
| Schreiben schlägt fehl | Freien Speicher, Schreibrechte und in Excel geöffnete Ergebnisdateien prüfen. Ein Speicherfehler bedeutet nicht automatisch, dass der Download verloren ist. |

Bei einem Fehlerbericht sind App-Version, Aktion, Zeitraum, gewählte Kategorien/Formate und Fehlerklasse hilfreich. Keine Passwörter, Tokens oder privaten Datenbanken veröffentlichen. Tests und Demo-Daten belegen Programmverhalten, aber keine lückenlose Erreichbarkeit aller Garmin-Daten.

## Begriffe und Grenzen

- **Download:** Daten von Garmin abrufen.
- **Offline-Bestand:** Lokal gespeicherte Antworten und unterstützte Aktivitätsdateien in einer SQLite-Datenbank.
- **Export:** Aus dem Bestand oder neu geladenen Daten Ausgabedateien erzeugen.
- **Vorschau:** Kleine Stichprobe der erwarteten Ausgabe, kein vollständiger Bestandskatalog.
- **Leere Antwort:** Garmin hat geantwortet, aber keine entsprechenden Werte geliefert.
- **Ungeprüft übersprungen:** Eine experimentelle Regel hat den Abruf ausgelassen. Vorhandensein von Details bleibt offen.

Eine allgemeine **Online-Bestandsübersicht vor dem Download** ist geplant, aber noch nicht enthalten. Sie soll Aktivitäten zunächst als Metadatenliste zeigen, ohne einzelne FIT-/GPX-Dateien oder Messverläufe abzurufen. Für Gesundheitsdaten gibt es damit noch keinen verlässlichen Nachweis aller verfügbaren Tage. Weitere Planung: [Roadmap](../ROADMAP.md).

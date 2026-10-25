# TTN Activity Export – Anleitung

Für den Quellstand **0.6.1-preview**. [English](USER_GUIDE.md) · [Projektübersicht](../README.md) · [Geplante Funktionen](../ROADMAP.md)

Die App arbeitet lokal auf deinem Computer. Sie kann unterstützte Garmin-Connect-Daten herunterladen, in einer lokalen Datenbank aufbewahren und daraus Dateien erstellen. Du entscheidest über Zeitraum, Datenarten und Ausgabeformat. Strava ist ausschließlich eine lokale Importquelle; Komoot ist noch nicht online integriert. Ältere Downloads der App können weniger Funktionen enthalten als hier beschrieben.

## Einstieg in die Testversion 0.6

Diese Anleitung beschreibt die neue Oberfläche. **Garmin ist nutzbar. Strava dient ausschließlich zum lokalen Import selbst heruntergeladener Dateien. Komoot hat noch keinen Onlinezugriff.** Eine Strava-Anmeldung und automatische Strava-Abfragen sind nicht vorgesehen. Automatische App-Updates folgen separat.

Die vier Hauptreiter sind **Konten**, **Download**, **Daten** und **Anleitung**. Die Detailreferenz unten bleibt gültig; ihre Bereiche Export/Ausgabe, Optionen, Felder, Experten und Offline-Daten findest du nun gesammelt über **Download → Optionen …**. Übernehmen behält deine Änderungen für neue Aufträge, Abbrechen stellt die vorherige Auswahl wieder her. Bereits vorgemerkte Aufträge ändern sich dadurch nicht. Mit **Als Kontovorgabe speichern** speicherst du die aktuelle Auswahl ausdrücklich für dieses Konto.

### Schnellstart mit einer CSV-Liste

1. Unter **Konten → Konto hinzufügen** Garmin und deine E-Mail-Adresse wählen. Bereits gemerkte Garmin-Konten werden übernommen. Über **Anmelden / Einstellungen** anmelden. Passwort und Zwei-Faktor-Code werden weiterhin nur beim Anmelden benötigt.
2. Unter **Download** das Konto, Von/Bis und die Vorgabe **Aktivitätenliste** wählen.
3. Für eine CSV-Datei die Aktion **Download und Dateien exportieren** auswählen und CSV einschalten. Die Standardaktion **Nur herunterladen** speichert ausschließlich die Quelldaten in der Datenbank. **Nur lokal exportieren** erzeugt Dateien aus der vorhandenen Datenbank ohne Anmeldung und ohne Netzabruf.
4. Optional **Online-Bestand anzeigen** drücken. Die App lädt zunächst höchstens zehn Listenseiten mit je bis zu 100 Einträgen. Sie fragt keine einzelnen Aktivitätsdateien, Messverläufe, Fotos oder Karten ab.
5. In der Übersicht nach Name/Datum oder Sportart filtern. Mit Strg einzelne Zeilen ergänzen, mit Shift einen Bereich markieren. **Alle sichtbaren auswählen** bezieht sich auf die sichtbaren, bereits geladenen Treffer. **Auswahl übernehmen** setzt die gewählten IDs und leert einen möglicherweise widersprechenden Sportartenfilter. Ohne spezielle Auswahl gelten alle zum Zeitraum und Sportfilter passenden Aktivitäten.
6. **Zur Auftragsliste hinzufügen** drücken. Du kannst weitere Aufträge mit anderen Einstellungen oder Garmin-Konten ergänzen und per Nach oben/Nach unten sortieren.
7. **Aufträge prüfen und starten** zeigt die endgültigen Einstellungen pro Auftrag. Erst **Download / Export starten** führt sie aus. Zurück startet nichts. Zum Ändern eines vorgemerkten Auftrags diesen entfernen und mit geänderter Auswahl neu hinzufügen.
8. Nach dem Dateiexport den Ergebnisordner öffnen. Für lokale Tabellen und Karten die passende Datenbank unter Daten laden.

### Bestandsübersicht richtig lesen

Die Übersicht gehört zu genau einem Konto und Zeitraum. Datum oder Konto wechseln setzt die aktuelle Auswahl zurück. **Übersicht aktualisieren** beginnt neu; **Weitere Seiten laden** setzt die Paginierung fort. Der Zeitstempel zeigt den Stand der Liste. Ein wiederholter, fehlerhafter oder unterbrochener Abruf bleibt **teilweise geladen**. Erst eine abschließende leere Listenseite bestätigt, dass dieser Zeitraum vollständig aufgelistet wurde. Eine gespeicherte Übersicht kann beim erneuten Öffnen ohne weitere Anfrage angezeigt werden.

Diese Liste ist kein vollständiger Gesundheitsdatenkatalog und kein Nachweis lokal gespeicherter FIT-Dateien. Für den Download kann die Aktivitätenliste erneut abgefragt werden; zusätzliche Details und Dateien werden nur für die gewählten IDs angefordert. Ein fehlender ausgewählter Eintrag wird als unvollständiger Lauf gemeldet. Die begrenzte Ausgabevorschau ist bei einer ID-Auswahl deaktiviert, weil die gewählten IDs außerhalb der Stichprobe liegen können. Lade die Auswahl zuerst herunter und exportiere sie danach lokal.

### Aufträge, Neustart und Aufwand

Konto, Zeitraum, Auswahl, Formate und Abrufoptionen werden beim Hinzufügen als Kopie gespeichert. Spätere Änderungen wirken nur auf neue Aufträge. Nach einem Neustart bleibt ein unterbrochener Auftrag sichtbar; ohne erneute Prüfung und Startbestätigung läuft nichts automatisch. Bei fehlender Anmeldung oder aktiver Garmin-Abrufpause erhält der Auftrag einen Wartestatus. Andere bereite Aufträge können weiterlaufen. Abbrechen stoppt den aktuellen Download und die weitere Abarbeitung dieser Liste; erfolgreich gespeicherte Antworten bleiben erhalten.

Die Zusammenfassung prüft vorhandene passende Grundantworten in der SQLite-Datei lokal und schätzt offene Grundabfragen. Zusätzliche Listenseiten, Details, ältere Datei-Caches, Bereichs-Fallbacks und Wiederholungen können den tatsächlichen Aufwand ändern. Eine aus dem Mindestabstand berechnete Zeit ist keine vollständige Downloadprognose. Ohne verlässliche Messgrundlage bleibt die Dauer ausdrücklich unbekannt. Während des Downloads wird die Restzeit gemessen. Excel-Erzeugung braucht zusätzliche Zeit nach dem Download.

Mehrere Exporte desselben Kontos können im gemeinsamen `exports/current` spätere Ergebnisse ersetzen. Wenn du jeden Auftrag separat behalten möchtest, vor dem Hinzufügen unter Optionen **Separate Exportordner behalten** aktivieren. Aufträge sind keine Datensicherung.

### Konten, Ordner und Bedienhilfen

Neue Konten verwenden `Downloads\TTN Activity Export\Garmin`, `Komoot` oder `Strava`, darunter getrennte Kontobereiche. Ein vorhandenes gemerktes Garmin-Konto übernimmt den bisherigen Ausgabeordner; alte Daten werden nicht verschoben. Wähle beim Fortsetzen deine bisherige SQLite-Datei über Optionen → Offline-Bestand. Mehrere Garmin-Konten können in einer Sitzung nacheinander angemeldet werden. Für die automatische Anmeldung beim Programmstart bleibt zunächst das zuletzt ausdrücklich gemerkte Garmin-Konto maßgeblich. Weitere Konten bei Bedarf über deren Anmeldung verbinden.

Unter Optionen lassen sich **Hilfetexte beim Darüberfahren** global an-/ausschalten. Wichtige Status- und Fehlermeldungen bleiben sichtbar. **Protokoll …** öffnet das Protokollfenster mit **Log öffnen** und **Log der heutigen Sitzung exportieren**. Sprache und Farbschema bleiben oben erreichbar. Die neue Oberfläche kann pro Benutzerprofil nur einmal gleichzeitig laufen; schließe vor dem Test auch die alte App.

## Detailreferenz

Die folgenden Erklärungen beziehen sich auf die weiterhin verfügbaren Detailbereiche im Optionen-Fenster. Der frühere direkte Export-Start wird in der neuen Oberfläche durch Hinzufügen, Prüfen und Starten des Auftrags ersetzt.

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

Die Reiter heißen derzeit **Konto**, **Export**, **Optionen**, **Felder**, **Experten**, **Offline-Daten**, **Daten** und zuletzt **Anleitung**. Für den Einstieg brauchst du normalerweise nur Konto, Export und gegebenenfalls Optionen. Diese früheren Bereiche liegen jetzt im Optionen-Fenster; die vier Hauptreiter sind oben beschrieben.

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
7. Wähle **Download und Dateien exportieren**, füge den Auftrag hinzu und starte ihn nach der Prüfung. Anschließend **Ergebnisordner öffnen**.

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

Die **Online-Bestandsübersicht vor dem Download** ist für Garmin-Aktivitäten enthalten und oben beschrieben. Sie zeigt zunächst Metadaten, ohne einzelne FIT-/GPX-Dateien oder Messverläufe abzurufen. Für Gesundheitsdaten gibt es damit noch keinen verlässlichen Nachweis aller verfügbaren Tage. Weitere Planung: [Roadmap](../ROADMAP.md).

## Experimentelles Überspringen

Die Überspringen-Option bleibt standardmäßig aus. Leere Tageskennzahlen beweisen nicht, dass detaillierte Daten fehlen. Ausgelassene Abfragen bleiben ungeprüft und lassen sich über die Offline-Verwaltung ausdrücklich nachladen.

Vorlagen speichern die Daten-/Ausgabeoptionen, keine kontoabhängige ID-Auswahl aus der Bestandsliste. Nach dem Laden einer Vorlage die gewünschten Aktivitäten erneut auswählen.

## Strava als lokale Importquelle

Für Strava gibt es in der App keine Anmeldung, API-Schlüssel, API-Budgetanzeige und keinen automatischen Website-Abruf.

1. Lade dein Konto-ZIP selbst auf der Strava-Website unter Einstellungen → Mein Konto → Konto herunterladen herunter. Warte auf die E-Mail mit dem Downloadlink. Die App fordert das Paket nicht automatisch an.
2. Unter **Konten → Konto hinzufügen → Strava** einen lokalen Namen oder deine E-Mail-Adresse und einen Zielordner festlegen. Diese Bezeichnung dient nur der lokalen Trennung, nicht der Anmeldung bei Strava.
3. **Import / Einstellungen → Strava-Datenpaket importieren …** wählen. Alternativ findest du den Importbutton im Reiter Download, sobald Strava ausgewählt ist.
4. Das vollständige ZIP auswählen; nicht vorher entpacken. Unterstützt werden die Aktivitätenliste `activities.csv` mit den üblichen englischen Exportspalten und darin referenzierte FIT-, GPX- oder TCX-Dateien, auch gzip-komprimiert. Die App liest das Paket ohne Netzverbindung.
5. Nach dem Import öffnet sich **Daten**. Nach Sportart, Datum oder Suchtext filtern und Zeilen mit Strg/Shift markieren. Unter **Auswahl → Auswahl exportieren** die gewünschte Tabelle als CSV, Excel oder JSON speichern. Karten funktionieren nur, wenn eine unterstützte Aufzeichnung GPS enthält.

Die Daten liegen in einer getrennten `strava-offline.sqlite` im lokalen Strava-Kontobereich. **Lokale Strava-Daten öffnen** lädt diesen Bestand später erneut. Bereits importierte Strava-IDs werden beim erneuten Paketimport aktualisiert, statt zusätzliche Zeilen anzulegen. Eine Aktivität ohne referenzierte Datei bleibt als Tabellenzeile erhalten. Defekte oder fehlende Aufzeichnungen werden gemeldet; sie erzeugen keine erfundene GPS-Strecke.

Es wird die Aktivitätshistorie importiert, nicht das gesamte Strava-Konto: Fotos, Kommentare, Kontakte und andere Kontoinhalte bleiben außen vor. Bewahre das Original-ZIP selbst als Sicherung auf. Die App verändert oder löscht es nicht. Sie kann nur Daten lesen, die im Paket vorhanden sind.

Doppelte CSV-Spalten werden in den Rohmetadaten erhalten. Beim vollständigen Strava-CSV wird die metrische Distanzspalte genutzt; bei abweichenden/eindeutigen Spalten ohne belegte Einheit wird keine Distanz geraten. CSV-Zeitstempel ohne Zeitzonenangabe werden als nicht näher spezifizierte Exportzeit übernommen, nicht automatisch als deutsche Ortszeit umgerechnet. Das kann für Aktivitäten um Mitternacht relevant sein.

Grenzen dieses ersten Importers: eine passende `activities.csv`, höchstens 30.000 ZIP-Einträge, 32 MiB CSV, 128 MiB je entpackter Aufzeichnung und 8 GiB insgesamt verarbeitete Aktivitätsdaten. Größenfehler, ungültige Zeilen und fehlende Dateien erscheinen im Importbericht. Bei Abbruch bleiben bereits importierte Einträge erhalten. Das Format wurde mit synthetischen Beispielen geprüft; ein echtes Nutzerpaket muss im Praxistest bestätigt werden.

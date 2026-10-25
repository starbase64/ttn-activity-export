"""Allowlisted local import diagnostics; never display arbitrary exception/response text."""
IMPORT_MESSAGES={
 'strava_csv_missing':('Im Paket wurde keine eindeutige activities.csv gefunden. Bitte das vollständige Strava-Kontopaket oder dessen entpackten Ordner auswählen.','No unique activities.csv was found. Select the complete Strava account package or its extracted folder.'),
 'strava_csv_headers':('Die Spalten der Aktivitätenliste werden nicht erkannt. Unterstützt sind deutsche und englische Strava-Kontoexporte. Für die Diagnose genügt die erste Zeile der activities.csv; Aktivitätsdaten sind dafür nicht nötig.','Activity-list columns were not recognized. German and English Strava account exports are supported. Only the first activities.csv line is needed for diagnosis, not activity data.'),
 'strava_csv_encoding':('Die Aktivitätenliste ist nicht als UTF-8 lesbar. Bitte das unveränderte Strava-Originalpaket verwenden.','The activity list is not readable as UTF-8. Use the unchanged original Strava package.'),
 'strava_csv_size':('Die Aktivitätenliste überschreitet das Importlimit von 32 MiB.','The activity list exceeds the 32 MiB import limit.'),
 'strava_member_limit':('Das Paket enthält mehr als 30.000 Einträge. Bitte einen Ordner mit activities.csv und den referenzierten Aktivitätsdateien verwenden; Fotos werden für den Aktivitätsimport nicht benötigt.','The package contains over 30,000 entries. Use a folder containing activities.csv and referenced activity files; photos are not needed for activity import.'),
 'strava_copy_nested':('Der Zielordner liegt innerhalb des Quellordners. Bitte Quelle am bisherigen Ort nutzen oder einen Zielordner außerhalb der Quelle wählen.','The destination is inside the source folder. Use the source in place or choose a destination outside it.'),
 'strava_copy_limit':('Die vollständige Quellkopie überschreitet 8 GiB. Bitte Quelle am bisherigen Ort nutzen; es wird dann keine vollständige Zusatzkopie angelegt.','The complete source copy exceeds 8 GiB. Use the source in place to avoid an additional full copy.'),
 'strava_zip_invalid':('Die ZIP-Datei ist beschädigt oder kein unterstütztes ZIP. Download abschließen oder das Paket erneut von Strava herunterladen.','The file is damaged or is not a supported ZIP. Finish the download or download the package from Strava again.'),
 'strava_source_missing':('Die ausgewählte Quelldatei oder der Quellordner ist nicht mehr vorhanden. Bitte erneut auswählen.','The selected source file or folder no longer exists. Select it again.'),
 'strava_date':('Das Datumsformat dieser Aktivitätenzeile wird nicht erkannt.','The date format in this activity row is not recognized.'),
}

class ImportProblem(ValueError):
    def __init__(self,code):
        if code not in IMPORT_MESSAGES:raise ValueError('Unknown import code')
        self.import_code=code
        super().__init__(code)

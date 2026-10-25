"""Package the app with a Windows self-setup launcher, excluding user data."""
import argparse
import hashlib
from pathlib import Path
import zipfile


def build(output):
    source=Path(__file__).resolve().parent;output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    prefix='TTN-Activity-Export/'
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as archive:
        for name in ('Start-TTN-Activity-Export.cmd','bootstrap.ps1','windows_bootstrap.py','windows-dependencies.lock.json','LICENSE','THIRD_PARTY_NOTICES.md','README.md','CHANGELOG.md','RELEASE_NOTES.md','ROADMAP.md'):
            archive.write(source/name,prefix+name)
        excluded={'build_portable_bundle.py','build_starter.py','generate_windows_lock.py','windows_bootstrap.py','generate_help.py'}
        for path in sorted(source.glob('*.py')):
            if path.name not in excluded:archive.write(path,prefix+'app/'+path.name)
        for name in ('ANLEITUNG.md','USER_GUIDE.md'):
            archive.write(source/'docs'/name,prefix+'app/docs/'+name)
        for lang in ('de','en'):
            archive.write(source/'docs'/('guide-'+lang+'.html'),prefix+'app/docs/guide-'+lang+'.html')
        archive.writestr(prefix+'BITTE-ZUERST-LESEN.txt',
            'TTN Activity Export - Windows 10/11 x64\n\n'
            'ZIP vollstaendig in einen beschreibbaren Ordner entpacken.\n'
            'Start-TTN-Activity-Export.cmd doppelklicken.\n'
            'Beim ersten Start werden Python und fehlende Pakete von python.org und PyPI geladen.\n'
            'Keine Administratorrechte und keine eigene Python-Installation erforderlich.\n'
            'Laufzeit und Downloadcache bleiben im Programmordner. Spaeterer Start offline moeglich.\n'
            'Die Garmin-Anmeldung und Online-Downloads benoetigen Internet.\n'
            'Einrichtungsfehler: Konsolenmeldung und setup.log pruefen. Nicht parallel starten.\n'
            'Windows kann bei heruntergeladenen unsignierten Skripten einen Hinweis anzeigen.\n'
            'Bisherigen Ausgabeordner/dieselbe Datenbank waehlen, um alte Downloads fortzusetzen.\n'
            'Neue Konten: Downloads\\TTN_Activity_Export\\Garmin. Alte Daten werden nicht verschoben.\n'
            'Vier Reiter: Konten, Download, Daten, Anleitung. Standardaktion: Nur herunterladen.\n'
            'Fuer CSV/Excel Download und Dateien exportieren waehlen, Auftrag hinzufuegen und pruefen/starten.\n'
            'Garmin ist nutzbar. Strava: nur lokaler ZIP-/Ordner-Import. Komoot: experimenteller Online-Zugriff.\n\n'
            'English: extract everything to a writable folder and double-click the CMD file.\n'
            'First-time setup downloads a private Python runtime and pinned dependencies.\n'
            'No admin rights, system Python changes or Garmin login during setup.\n'
            'Prepared under Linux; see GitHub Actions for Windows validation. Live Garmin testing remains account-specific.\n')
    with zipfile.ZipFile(output) as archive:
        if archive.testzip():raise ValueError('Invalid starter archive')
    output.with_suffix(output.suffix+'.sha256').write_text(hashlib.sha256(output.read_bytes()).hexdigest()+'  '+output.name+'\n',encoding='ascii')
    return output


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('output');args=parser.parse_args();print(build(args.output))

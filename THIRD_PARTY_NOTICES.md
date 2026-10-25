# Third-party software

TTN Activity Export is independent of Garmin. Garmin and Garmin Connect are trademarks of Garmin Ltd. or its subsidiaries.

The project source is MIT licensed. Dependencies have their own licenses. The Windows build collects installed distribution license texts into `THIRD_PARTY_LICENSES.txt` and copies the Python license. Check the actual build before distribution; this short file does not replace the full licenses.

Main dependencies:

- python-garminconnect: MIT — https://github.com/cyberjunky/python-garminconnect
- PySide6 / Qt: LGPLv3 option (some components may have additional terms) — https://doc.qt.io/qtforpython-6/licenses.html
- openpyxl: MIT — https://openpyxl.readthedocs.io/
- fitdecode: MIT — https://github.com/polyvertex/fitdecode
- Optional online basemap: © OpenStreetMap contributors, ODbL data — https://www.openstreetmap.org/copyright . Raster tiles follow https://operations.osmfoundation.org/policies/tiles/ . No bulk tile download is offered.
- Optional Google Maps view: Google Maps Platform requires a user-supplied API key and is subject to Google's terms and billing. Google is not affiliated with this project.
- curl_cffi and bundled native libraries, requests, ua-generator, tzdata and other transitive dependencies: consult bundled license texts.
- Python: PSF license — https://docs.python.org/3/license.html
- PyInstaller: GPL with an exception allowing distribution of bundled applications — https://pyinstaller.org/en/stable/license.html

The portable application uses the one-directory build to keep Qt shared libraries replaceable. Preserve library files and notices when distributing. Corresponding Qt/PySide sources and license information are available from https://download.qt.io/official_releases/QtForPython/ and https://download.qt.io/official_releases/qt/ . Check LGPL obligations for your exact distribution, including the ability to replace libraries for debugging modifications. No restriction in this project's MIT license removes rights granted by dependencies' licenses.

## Research acknowledgement

[GarminDB](https://github.com/tcgoetz/GarminDB) informed research into reusable offline archives and daily wellness FIT downloads. GarminDB code is not bundled and GarminDB is not a runtime dependency. The Garmin Connect client used by this app is python-garminconnect, credited above.

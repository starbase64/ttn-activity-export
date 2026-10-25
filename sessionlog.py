"""A bounded UI log with an independent, append-only session file."""
from datetime import datetime
from pathlib import Path
import uuid
from PySide6.QtWidgets import QPlainTextEdit

class SessionLog(QPlainTextEdit):
    def __init__(self,directory,parent=None):
        super().__init__(parent);self.setReadOnly(True);self.setMaximumBlockCount(500)
        directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
        self.path=directory/('activity-'+datetime.now().strftime('%Y-%m-%d_%H-%M-%S')+'-'+uuid.uuid4().hex[:6]+'.log')
        self.write_error=False
        self.appendPlainText('TTN Activity Export · session started')
    def appendPlainText(self,text):
        stamp=datetime.now().astimezone().isoformat(timespec='seconds')
        line=stamp+' · '+str(text)
        try:
            with self.path.open('a',encoding='utf-8') as f:f.write(line+'\n');f.flush()
        except OSError:
            if not self.write_error:
                super().appendPlainText('Logdatei nicht schreibbar / Cannot write log file')
            self.write_error=True;self.setToolTip('Logdatei nicht schreibbar / Cannot write log file')
        super().appendPlainText(line)

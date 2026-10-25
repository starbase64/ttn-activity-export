"""Confirmation, preparation and Windows helper handoff for starter updates."""
import os
from pathlib import Path
import subprocess
import sys
import threading
from urllib.error import URLError
from PySide6.QtCore import QThread,QTimer,Signal,Qt
from PySide6.QtWidgets import QApplication,QMessageBox,QProgressDialog
from updater import installation_context,prepare_update,discard_prepared,UpdateError,UpdateCancelled


class Preparation(QThread):
    progress=Signal(int,int)
    def __init__(self,context,asset,language,parent=None):
        super().__init__(parent);self.context=context;self.asset=dict(asset);self.language=language
        self.cancel=threading.Event();self.plan=None;self.error=None
    def run(self):
        try:self.plan=prepare_update(self.context,self.asset,self.language,self.cancel,lambda a,b:self.progress.emit(a,b))
        except UpdateCancelled:self.error='cancelled'
        except UpdateError as exc:self.error=str(exc)
        except URLError:self.error='connection'
        except OSError:self.error='files'
        except Exception:self.error='package'


def start_helper(plan_path):
    plan=Path(plan_path);helper=plan.parent/'windows_update.ps1'
    with (plan.parent/'helper-output.log').open('ab') as output:
        return subprocess.Popen(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(helper),
                          '-PlanPath',str(plan),'-ParentProcessId',str(os.getpid())],cwd=str(plan.parent),
                         stdin=subprocess.DEVNULL,stdout=output,stderr=subprocess.STDOUT,close_fds=True,
                         creationflags=subprocess.CREATE_NEW_PROCESS_GROUP|subprocess.DETACHED_PROCESS)


class UpdateInstallMixin:
    def init_installer(self,app_file,current):
        self.install_worker=None;self.install_dialog=None;self._offered_updates=set();self._close_after_preparation=False
        self._install_context=installation_context(app_file,current) if not self.demo else None
        self._install_version=current;self._offer_timer=QTimer(self);self._offer_timer.setSingleShot(True);self._offer_timer.timeout.connect(self.offer_update)

    def can_install_update(self):
        return bool(self._install_context and (self.update_info or {}).get('installer') and not self.demo)

    def update_install_busy(self):
        return bool((self.worker and self.worker.isRunning()) or
                    (self.data_page.track_worker and self.data_page.track_worker.isRunning()) or
                    self.data_page.pending_tracks or getattr(self,'_queue_active',False) or self._restore_pending or self._restoring)

    def offer_update(self):
        if self._closing or not self.can_install_update() or self.install_worker:return
        version=self.update_info['installer']['version']
        if version in self._offered_updates:return
        if self.update_install_busy():self._offer_timer.start(1000);return
        self.confirm_update()

    def _ask_install_confirmation(self,text):
        buttons=QMessageBox.StandardButton.Ok|QMessageBox.StandardButton.Cancel
        box=QMessageBox(QMessageBox.Icon.Question,'TTN Activity Export',text,buttons,self)
        box.button(QMessageBox.StandardButton.Ok).setText('OK')
        box.button(QMessageBox.StandardButton.Cancel).setText(self.tr('Abbrechen','Cancel'))
        box.setDefaultButton(QMessageBox.StandardButton.Cancel)
        result=box.exec();box.deleteLater();return result

    def confirm_update(self):
        if not self.can_install_update() or self.install_worker:return
        if self.update_install_busy():
            self.update_status.setText(self.tr('Update bereit. Installation nach Ende des laufenden Vorgangs.','Update ready. Installation waits for the current operation.'))
            self._offer_timer.start(1000);return
        asset=dict(self.update_info['installer']);self._offered_updates.add(asset['version'])
        text=self.tr(f"Update auf Version {asset['version']} jetzt installieren?\n\nDie App wird geschlossen, die neue Version geprüft und automatisch gestartet. Konten, Einstellungen und heruntergeladene Daten bleiben erhalten.",
                     f"Install update {asset['version']} now?\n\nThe app will close, check the new version and restart automatically. Accounts, settings and downloaded data are retained.")
        if self._ask_install_confirmation(text)!=QMessageBox.StandardButton.Ok:return
        if self.update_install_busy():self._offered_updates.discard(asset['version']);self._offer_timer.start(1000);return
        self._begin_install(asset)

    def _begin_install(self,asset):
        worker=Preparation(self._install_context,asset,self.lang,self);self.install_worker=worker
        dialog=QProgressDialog(self.tr('Update wird heruntergeladen …','Downloading update …'),self.tr('Abbrechen','Cancel'),0,100,self)
        dialog.setWindowTitle('TTN Activity Export');dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        dialog.setAutoClose(False);dialog.setAutoReset(False);dialog.setMinimumDuration(0);self.install_dialog=dialog
        dialog.canceled.connect(worker.cancel.set)
        worker.progress.connect(self._install_progress);worker.finished.connect(self._installation_prepared)
        self.update_button.setEnabled(False);self.update_download.setEnabled(False);dialog.show();worker.start()

    def _install_progress(self,received,total):
        if self.install_dialog:
            self.install_dialog.setValue(int(received*100/max(1,total)))
            if received==total:self.install_dialog.setLabelText(self.tr('Update wird geprüft …','Verifying update …'))

    def _installation_prepared(self):
        worker=self.install_worker;self.install_worker=None
        cancelled=worker.cancel.is_set() or bool(self.install_dialog and self.install_dialog.wasCanceled())
        if self.install_dialog:
            self.install_dialog.blockSignals(True);self.install_dialog.close();self.install_dialog.deleteLater();self.install_dialog=None
        self.update_button.setEnabled(True);self.update_download.setEnabled(True)
        plan=worker.plan;error=worker.error;worker.deleteLater()
        if cancelled or error=='cancelled':
            if plan:discard_prepared(plan)
            self.update_status.setText(self.tr('Update abgebrochen. Die bisherige Version bleibt aktiv.','Update cancelled. The current version remains active.'))
            if self._close_after_preparation:QTimer.singleShot(0,self.close)
            return
        if error:
            messages={'space':('Nicht genügend freier Speicher für das Update.','Not enough free disk space for the update.'),
                      'connection':('Update konnte nicht heruntergeladen werden. Internetverbindung prüfen.','Could not download the update. Check your internet connection.'),
                      'files':('Update-Dateien konnten nicht gespeichert werden. Schreibrechte und Speicherplatz prüfen.','Could not save update files. Check write permissions and free space.')}
            text=self.tr(*messages.get(error,('Update-Prüfung fehlgeschlagen. Die bisherige Version bleibt unverändert.','Update verification failed. The current version is unchanged.')))
            self.log.appendPlainText(text+' · '+error);self.message(text,text);return
        try:
            remember=getattr(self,'remember_active_archive',None)
            if remember:remember()
            if hasattr(self,'workspace') and not self.save_workspace():raise OSError('preferences')
            if self.update_install_busy():raise OSError('busy')
            helper=start_helper(plan)
        except OSError:
            discard_prepared(plan);self.message('Der Update-Helfer konnte nicht gestartet werden. Die bisherige Version bleibt aktiv.','Could not start the update helper. The current version remains active.');return
        self.log.appendPlainText(self.tr('Update-Helfer gestartet; App wird beendet und neu gestartet.','Update helper started; closing and restarting the app.'))
        if self.close():QTimer.singleShot(0,QApplication.instance().quit)
        else:helper.terminate()

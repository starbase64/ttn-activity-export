"""Compact desktop shell over the tested Garmin engine and detailed option widgets."""
from copy import deepcopy
from dataclasses import replace
from datetime import date
from pathlib import Path
import json
import tempfile

from PySide6.QtCore import Qt,QTimer,QDate,QEvent,QObject,QStandardPaths
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QFormLayout,QLabel,QPushButton,
    QComboBox,QLineEdit,QCheckBox,QListWidget,QTableWidget,QTableWidgetItem,QDialog,QDateEdit,
    QDialogButtonBox,QTabWidget,QAbstractItemView,QHeaderView,QApplication,QFileDialog,QGroupBox,QScrollArea,QLayout,QMessageBox)
from engine import Plan,account_key,atomic_json
from catalog import DATASETS,ACTIVITY_DETAILS
from archive import Archive
from offline import ArchiveSync,ArchiveExporter,OfflineExporter
from workspace_state import Workspace,now
from inventory import read_inventory
from activity_table import table_row

class TooltipFilter(QObject):
    def __init__(self,host):super().__init__(host);self.host=host
    def eventFilter(self,obj,event):
        if event.type()==QEvent.Type.ToolTip and not self.host.workspace.data.get('tooltips',True):return True
        return False

class StudioMixin:
    def bind(self,widget,de,en,setter='setText'):
        result=super().bind(widget,de,en,setter)
        key=id(widget)
        widget.destroyed.connect(lambda _=None:self.bindings.__setitem__(slice(None),[b for b in self.bindings if id(b[0])!=key]))
        return result
    def __init__(self,*args,**kwargs):
        self._studio_ready=False;self._job=None;self._queue_active=False;self._queue_stop=False
        self.clients={};self.komoot_clients={};self.selected_activity_ids=[];self.inventory_result=None
        super().__init__(*args,**kwargs)
        self._demo_workspace=tempfile.TemporaryDirectory(prefix='ttn-demo-') if self.demo else None
        state_path=Path(self._demo_workspace.name)/'workspace.json' if self.demo else self.data_dir/'workspace.json'
        try:self.workspace=Workspace(state_path)
        except (OSError,ValueError,TypeError,KeyError):
            # Never silently overwrite damaged account/job metadata.
            recovered=state_path.with_name('workspace-recovery.json')
            self.workspace=Workspace(recovered)
            self.log.appendPlainText(self.tr('Konten-/Auftragsdatei konnte nicht gelesen werden. Original bleibt erhalten; separate Wiederherstellungsdatei wird verwendet.',
                                            'Could not read account/job metadata. Original preserved; using a separate recovery file.'))
        if self.demo:
            record=self.workspace.add_account('garmin','demo@example.invalid',Path(self._demo_workspace.name)/'Garmin')
            self.clients[record['id']]=self.api
        elif self.email.text().strip():
            ident=account_key(self.email.text().strip(),self.china.isChecked())
            if not any(a['id']==ident for a in self.workspace.accounts):
                self.workspace.add_account('garmin',self.email.text().strip(),self.output.text(),self.china.isChecked())
        self.active_account=None
        self._dialogs={}
        self._compose()
        self._tooltip_filter=TooltipFilter(self);QApplication.instance().installEventFilter(self._tooltip_filter)
        self._studio_ready=True
        preferred=next((a for a in self.workspace.accounts if a['provider']=='garmin' and a['email'].casefold()==self.email.text().strip().casefold() and a['china']==self.china.isChecked()),None)
        self.refresh_accounts((preferred or (self.workspace.accounts[0] if self.workspace.accounts else {})).get('id'))
        self.render_jobs()
        if not self.workspace.accounts:self.tabs.setCurrentIndex(0)
        self.refresh_selection_summary()

    def _compose(self):
        self.option_tabs=QTabWidget()
        for page,de,en in ((self.export_scroll,'Daten und Ausgabe','Data and output'),(self.advanced_widget,'Abrufoptionen','Retrieval'),
                (self.fields_widget,'Felder','Fields'),(self.expert_widget,'Experten','Expert'),(self.offline_widget,'Offline-Bestand','Offline archive')):
            self.tabs.removeTab(self.tabs.indexOf(page));self.option_tabs.addTab(page,self.tr(de,en))
        self.option_labels=[('Daten und Ausgabe','Data and output'),('Abrufoptionen','Retrieval'),('Felder','Fields'),('Experten','Expert'),('Offline-Bestand','Offline archive')]
        self.options_dialog=QDialog(self);self.options_dialog.setWindowTitle(self.tr('Download- und Exportoptionen','Download and export options'))
        self.options_dialog.resize(1080,760);self.options_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        ov=QVBoxLayout(self.options_dialog);ov.addWidget(self.option_tabs)
        self.options_notice=self.label('Änderungen gelten für den nächsten Auftrag. Bereits vorgemerkte Aufträge behalten ihre Einstellungen.',
                                       'Changes apply to the next job. Queued jobs retain their settings.');ov.addWidget(self.options_notice)
        ov.addWidget(self.button('Als Kontovorgabe speichern','Save as account defaults',self.save_account_defaults))
        buttons=QHBoxLayout();buttons.addWidget(self.button('Abbrechen','Cancel',self.options_dialog.reject));buttons.addStretch();buttons.addWidget(self.button('Übernehmen','Apply',self.options_dialog.accept,primary=True));ov.addLayout(buttons)
        self.options_dialog.rejected.connect(self.restore_option_snapshot)
        self.options_dialog.accepted.connect(lambda:setattr(self,'_option_snapshot',None))
        self.account_dialog=QDialog(self);self.account_dialog.resize(650,470);self.account_dialog.setWindowTitle(self.tr('Garmin-Anmeldung','Garmin sign-in'))
        self.tabs.removeTab(self.tabs.indexOf(self.account_widget));QVBoxLayout(self.account_dialog).addWidget(self.account_widget)
        close=self.button('Schließen','Close',self.account_dialog.close);self.account_dialog.layout().addWidget(close)
        self.accounts_page=QWidget();av=QVBoxLayout(self.accounts_page)
        av.addWidget(self.label('Deine Konten','Your accounts'))
        av.addWidget(self.label('Füge ein Konto hinzu. Dateien und Einstellungen bleiben pro Konto getrennt.',
                                'Add an account. Files and settings are kept separate for each account.'))
        self.account_list=QListWidget();self.account_list.currentRowChanged.connect(self.account_row_changed);av.addWidget(self.account_list,1)
        actions=QHBoxLayout();actions.addWidget(self.button('Konto hinzufügen','Add account',self.add_account_dialog,primary=True))
        self.account_settings_button=self.button('Anmelden / Einstellungen','Sign in / settings',self.open_account);actions.addWidget(self.account_settings_button)
        actions.addWidget(self.button('Konto entfernen','Remove account',self.remove_account));actions.addStretch();av.addLayout(actions)
        self.account_hint=self.label('Noch kein Konto hinzugefügt.','No account added yet.');av.addWidget(self.account_hint)
        self.download_page=QWidget();dv=QVBoxLayout(self.download_page)
        row=QHBoxLayout();row.addWidget(self.label('Konto','Account'));self.account_picker=QComboBox();self.account_picker.currentIndexChanged.connect(self.picker_changed);row.addWidget(self.account_picker,1)
        row.addWidget(self.button('Optionen …','Options …',lambda:self.show_options()));dv.addLayout(row)
        self.strava_panel=QWidget();sv=QVBoxLayout(self.strava_panel)
        sv.addWidget(self.label('Strava · lokaler Import','Strava · local import'))
        sv.addWidget(self.label('Lade dein Datenpaket selbst auf der Strava-Website herunter. Hier kannst du es lokal importieren; eine Strava-Anmeldung, ein API-Schlüssel oder ein Abo werden in der App nicht benötigt.',
                               'Download your data package yourself on the Strava website. Import it locally here; no Strava sign-in, API key or subscription is needed in this app.'))
        sr=QHBoxLayout();sr.addWidget(self.button('Strava-Datenpaket importieren …','Import Strava data package …',self.import_strava_dialog,primary=True))
        sr.addWidget(self.button('Lokale Strava-Daten öffnen','Open local Strava data',self.open_strava_data));sv.addLayout(sr)
        dv.addWidget(self.strava_panel)
        self.komoot_panel=QWidget();kv=QVBoxLayout(self.komoot_panel)
        kv.addWidget(self.label('Komoot · experimenteller Online-Zugriff','Komoot · experimental online access'))
        kv.addWidget(self.label('Erst die Tourenübersicht abrufen, dann Touren auswählen. GPX nur über die Exportfunktion; erforderliche Regionen müssen freigeschaltet sein. Anmeldung gilt nur bis zum Beenden der App.',
                               'Fetch the tour list first, then select tours. GPX uses the export endpoint; required regions must be unlocked. Sign-in lasts only until the app closes.'))
        kr=QHBoxLayout();self.komoot_from=QDateEdit(QDate(1990,1,1));self.komoot_to=QDateEdit(QDate.currentDate())
        for de,en,field in [('Von','From',self.komoot_from),('Bis','Through',self.komoot_to)]:
            field.setCalendarPopup(True);field.setDisplayFormat('yyyy-MM-dd');kr.addWidget(self.label(de,en));kr.addWidget(field)
        self.komoot_kind=QComboBox()
        for de,en,key in [('Aufgezeichnet','Recorded','tour_recorded'),('Geplant','Planned','tour_planned'),('Alle Touren','All tours','')]:self.komoot_kind.addItem(self.tr(de,en),key)
        kr.addWidget(self.komoot_kind);kv.addLayout(kr)
        kr=QHBoxLayout();kr.addWidget(self.button('Online-Bestand abrufen','Fetch online inventory',self.fetch_komoot_inventory,primary=True))
        kr.addWidget(self.button('Lokale Komoot-Daten öffnen','Open local Komoot data',self.open_komoot_data));kv.addLayout(kr);dv.addWidget(self.komoot_panel)
        self.garmin_controls=QWidget();settings_layout=QVBoxLayout(self.garmin_controls);settings_layout.setContentsMargins(0,0,0,0);dv.addWidget(self.garmin_controls)
        dates=QHBoxLayout();dates.addWidget(self.label('Von','From'));dates.addWidget(self.start_date);dates.addWidget(self.label('Bis einschließlich','Through'));dates.addWidget(self.end_date)
        dates.addWidget(self.reset_start_button);dates.addStretch();settings_layout.addLayout(dates)
        row=QHBoxLayout();row.addWidget(self.label('Auswahl','Selection'));self.simple_preset=QComboBox()
        for de,en,key in [('Aktivitätenliste','Activity list','activities'),('Gesundheit: Tageskennzahlen','Health: daily statistics','daily'),
                           ('Alle unterstützten Daten','All supported datasets','all'),('Eigene Auswahl unter Optionen','Custom selection in Options','custom')]:
            self.simple_preset.addItem(self.tr(de,en),key)
        self.simple_preset.currentIndexChanged.connect(self.apply_simple_preset);row.addWidget(self.simple_preset,1)
        row.addWidget(self.button('Online-Bestand anzeigen','Show online inventory',self.show_inventory));settings_layout.addLayout(row)
        self.selection_summary=self.label('','');settings_layout.addWidget(self.selection_summary)
        row=QHBoxLayout();row.addWidget(self.label('Ziel','Destination'));row.addWidget(self.output,1);row.addWidget(self.button('Ordner wählen','Choose folder',self.choose_folder));settings_layout.addLayout(row)
        row=QHBoxLayout();self.job_action=QComboBox()
        for de,en,key in [('Nur herunterladen','Download only','download'),('Download und Dateien exportieren','Download and export files','export'),('Nur lokal exportieren','Export offline only','offline')]:self.job_action.addItem(self.tr(de,en),key)
        row.addWidget(self.job_action)
        for check in self.format_checks.values():row.addWidget(check)
        row.addStretch();row.addWidget(self.button('Auswahl zurücksetzen','Clear activity selection',self.clear_activity_selection));settings_layout.addLayout(row)
        row=QHBoxLayout();row.addWidget(self.button('Zur Auftragsliste hinzufügen','Add to job list',self.enqueue_current,primary=True))
        row.addWidget(self.button('Vorschau','Preview',self.show_export_preview));settings_layout.addLayout(row)
        dv.addWidget(self.label('Auftragsliste','Job list'))
        self.jobs_table=QTableWidget(0,4);self.jobs_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.jobs_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers);self.jobs_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.jobs_table.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeMode.Stretch)
        self.jobs_table.setColumnWidth(1,210);self.jobs_table.setColumnWidth(2,115);self.jobs_table.setColumnWidth(3,170);dv.addWidget(self.jobs_table,1)
        row=QHBoxLayout();row.addWidget(self.button('Nach oben','Move up',lambda:self.move_job(-1)));row.addWidget(self.button('Nach unten','Move down',lambda:self.move_job(1)))
        row.addWidget(self.button('Entfernen','Remove',self.remove_job));row.addStretch();row.addWidget(self.button('Aufträge prüfen und starten','Review and start jobs',self.review_jobs,primary=True));dv.addLayout(row)
        self.queue_notice=self.label('Aufträge werden gespeichert. Nach einem Neustart werden sie erst nach deiner Bestätigung fortgesetzt.',
                                     'Jobs are saved. After restarting, they resume only after your confirmation.');dv.addWidget(self.queue_notice)
        while self.tabs.count():self.tabs.removeTab(0)
        self.config_tabs=[]
        self.download_scroll=QScrollArea();self.download_scroll.setWidgetResizable(True);self.download_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        dv.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize);self.jobs_table.setMinimumHeight(130);self.download_scroll.setWidget(self.download_page)
        self.add_tab(self.accounts_page,'Konten','Accounts');self.add_tab(self.download_scroll,'Download','Download');self.add_tab(self.data_page,'Daten','Data');self.add_tab(self.help,'Anleitung','User guide')
        for w in (self.start_button,self.download_only_button,self.export_preview_button):w.hide()
        # Move verbose log controls to a dialog, preserving the same session logger.
        outer=self.centralWidget().layout();log_actions=None;bottom=None
        for i in range(outer.count()):
            layout=outer.itemAt(i).layout()
            if not layout:continue
            widgets=[layout.itemAt(k).widget() for k in range(layout.count())]
            if self.stop_button in widgets:bottom=layout
            if any(w and isinstance(w,QPushButton) and w.text() in ('Log öffnen','Open log') for w in widgets):log_actions=layout
        self.log_dialog=QDialog(self);self.log_dialog.resize(850,550);self.log_dialog.setWindowTitle(self.tr('Sitzungsprotokoll','Session log'))
        log_layout=QVBoxLayout(self.log_dialog);outer.removeWidget(self.log);log_layout.addWidget(self.log);self.log.show()
        if log_actions:outer.removeItem(log_actions);log_layout.addLayout(log_actions)
        if bottom:bottom.insertWidget(2,self.button('Protokoll …','Log …',self.log_dialog.show))
        self.source_label.hide();self.subtitle.setMinimumWidth(470)
        for label in self.export_widget.findChildren(QLabel):
            if label.text() in ('Von','Bis einschließlich','Zielordner','Formate'):label.hide()
        for button in self.export_widget.findChildren(QPushButton):
            if button.text()=='Ordner wählen':button.hide()
        self.job_action.currentIndexChanged.connect(self.update_format_controls);self.update_format_controls()
        self.tooltip_checkbox=self.check('Hilfetexte beim Darüberfahren anzeigen','Show hover tooltips',self.workspace.data.get('tooltips',True))
        self.tooltip_checkbox.toggled.connect(self.save_tooltips);ov.insertWidget(1,self.tooltip_checkbox)
        self.bind(self.simple_preset,'Wähle eine Vorgabe oder passe Datenarten und Ausgabe unter Optionen an.','Choose a preset or customize datasets and output in Options.',setter='setToolTip')
        self.bind(self.account_picker,'Wählt das Konto für neue Aufträge. Vorgemerkte Aufträge bleiben unverändert.','Select the account for new jobs. Queued jobs stay unchanged.',setter='setToolTip')
        for cb in self.dataset_checks.values():cb.toggled.connect(self.refresh_selection_summary)
        self.start_date.dateChanged.connect(self.invalidate_inventory);self.end_date.dateChanged.connect(self.invalidate_inventory)

    def save_tooltips(self,value):self.workspace.data['tooltips']=bool(value);self.save_workspace()
    def save_workspace(self):
        try:self.workspace.save();return True
        except OSError:
            self.log.appendPlainText(self.tr('Konten/Aufträge konnten nicht gespeichert werden. Schreibrechte prüfen.','Could not save accounts/jobs. Check write permissions.'));return False
    def default_provider_folder(self,provider):
        downloads=QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation)
        return (Path(downloads) if downloads else Path.home()/'Downloads')/'TTN_Activity_Export'/provider.capitalize()
    def refresh_accounts(self,ident=None):
        ident=ident or (self.active_account or {}).get('id')
        self.account_list.blockSignals(True);self.account_picker.blockSignals(True)
        self.account_list.clear();self.account_picker.clear()
        for a in self.workspace.accounts:
            connected=a['id'] in self.clients or (a['provider']=='garmin' and self.identity==a['id'] and bool(self.api))
            status=self.tr('angemeldet','connected') if connected else self.tr('nicht angemeldet','not connected')
            if a['provider']=='strava':status=self.tr('Lokale Importquelle','Local import source')
            elif a['provider']=='komoot':status=self.tr('angemeldet · experimentell','connected · experimental') if a['id'] in self.komoot_clients else self.tr('nicht angemeldet · experimentell','not connected · experimental')
            self.account_list.addItem(a['provider'].capitalize()+' · '+a['email']+'\n'+status)
            self.account_picker.addItem(a['provider'].capitalize()+' · '+a['email'],a['id'])
        idx=next((i for i,a in enumerate(self.workspace.accounts) if a['id']==ident),0 if self.workspace.accounts else -1)
        self.account_list.setCurrentRow(idx);self.account_picker.setCurrentIndex(idx)
        self.account_list.blockSignals(False);self.account_picker.blockSignals(False)
        self.activate_account(self.workspace.accounts[idx] if idx>=0 else None)
        is_strava=bool(self.active_account and self.active_account['provider']=='strava')
        is_komoot=bool(self.active_account and self.active_account['provider']=='komoot')
        self.strava_panel.setVisible(is_strava);self.komoot_panel.setVisible(is_komoot);self.garmin_controls.setVisible(not is_strava and not is_komoot)
        self.account_settings_button.setText(self.tr('Import / Einstellungen','Import / settings') if is_strava else self.tr('Anmelden / Einstellungen','Sign in / settings'))
    def account_row_changed(self,index):
        if 0<=index<len(self.workspace.accounts):self.refresh_accounts(self.workspace.accounts[index]['id'])
    def picker_changed(self,index):
        if 0<=index<len(self.workspace.accounts):self.refresh_accounts(self.workspace.accounts[index]['id'])
    def activate_account(self,account):
        previous=self.active_account
        if previous and (not account or previous['id']!=account['id']) and self.data_page.data.get('account')==previous['id']:
            previous['archive_path']=self.data_page.source.text();self.save_workspace()
        if previous and previous['provider']=='garmin' and self.api and self.identity==previous['id']:self.clients[previous['id']]=self.api
        self.active_account=account
        changed=not previous or not account or previous['id']!=account['id']
        if not account:
            self.api=None;self.identity=None;self.data_page.select_account_archive(None,'');self.account_hint.setText(self.tr('Noch kein Konto hinzugefügt.','No account added yet.'));return
        if previous and previous['id']!=account['id']:self.invalidate_inventory()
        if not changed:
            self.update_connection();return
        self.output.setText(account['output'])
        if account['provider']=='garmin':
            self.email.setText(account['email']);self.china.setChecked(account['china']);self.password.clear()
            self.api=self.clients.get(account['id'])
            self.identity=account['id'] if self.api else None
            self._signed_email=account['email'];self.activate_date_account(account['id'])
            self.use_offline.setChecked(False)
            self.archive_path.setText(account.get('archive_path',''));self.ensure_archive_path()
            self.apply_account_defaults(account)
        else:self.api=None;self.identity=None
        from engine import account_root
        path=account.get('archive_path') or str(account_root(account['output'],account['id'])/(account['provider']+'-offline.sqlite'))
        self.data_page.select_account_archive(account['id'],path)
        self.update_connection()
        text=account['provider'].capitalize()+' · '+account['email']+'\n'+account['output']
        if account['provider']!='garmin':text+='\n'+self.provider_note(account['provider'])
        self.account_hint.setText(text)
    def provider_note(self,provider):
        if provider=='strava':return self.tr('Strava ist eine lokale Importquelle. Lade das Konto-ZIP selbst auf strava.com unter Einstellungen → Mein Konto → Konto herunterladen herunter und wähle es hier aus. Keine Anmeldung und kein automatischer Strava-Abruf in der App.',
                                            'Strava is a local import source. Download your account ZIP yourself on strava.com under Settings → My Account → Download your account, then select it here. The app does not sign in to or automatically retrieve data from Strava.')
        return self.tr('Experimentelle Komoot-Anbindung ohne öffentlich unterstützte API. Eigenes Konto per E-Mail/Passwort anmelden, Übersicht laden und Touren auswählen. Keine Google-/Apple-Anmeldung oder CAPTCHA-Umgehung. Passwort und Sitzung werden nicht auf Datenträger gespeichert.',
                       'Experimental Komoot connector without a publicly supported API. Sign in to your own account with email/password, list tours and select them. No Google/Apple sign-in or CAPTCHA bypass. Password and session are not stored on disk.')
    def add_account_dialog(self):
        if self.worker and self.worker.isRunning():return
        dialog=QDialog(self);dialog.setWindowTitle(self.tr('Konto hinzufügen','Add account'));f=QFormLayout(dialog)
        provider=QComboBox();provider.addItems(['Garmin','Komoot','Strava']);email=QLineEdit();china=self.check('China-Konto','China account')
        folder=QLineEdit(str(self.default_provider_folder('garmin')))
        provider.currentIndexChanged.connect(lambda:folder.setText(str(self.default_provider_folder(provider.currentText().lower()))))
        provider.currentIndexChanged.connect(lambda:china.setVisible(provider.currentText()=='Garmin'))
        f.addRow(self.tr('Anbieter','Provider'),provider);f.addRow(self.tr('Konto / E-Mail','Account / email'),email);f.addRow(china)
        row=QHBoxLayout();row.addWidget(folder);choose=self.button('Wählen','Choose',lambda:self.pick_account_folder(folder));row.addWidget(choose);f.addRow(self.tr('Zielordner','Destination'),row)
        hint=self.label('Garmin ist nutzbar. Strava ist eine lokale Importquelle ohne Online-Anmeldung. Komoot bietet eine experimentelle Online-Anmeldung.',
                        'Garmin is available. Strava is a local import source without online sign-in. Komoot offers experimental online sign-in.');f.addRow(hint)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel);f.addRow(buttons)
        buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject)
        if dialog.exec()!=QDialog.DialogCode.Accepted:return
        try:
            if not folder.text().strip():raise ValueError()
            account=self.workspace.add_account(provider.currentText().lower(),email.text(),folder.text(),china.isChecked());self.refresh_accounts(account['id'])
        except (OSError,ValueError):self.message('Konto konnte nicht angelegt werden. E-Mail, Ordner und Schreibrechte prüfen.','Could not add account. Check email, folder and permissions.');return
        self.open_account()
    def pick_account_folder(self,field):
        chosen=QFileDialog.getExistingDirectory(self,self.tr('Zielordner','Destination'),field.text())
        if chosen:field.setText(chosen)
    def remove_account(self):
        a=self.active_account
        if not a or self._queue_active:return
        if any(j['account']==a['id'] and j['status'] not in ('complete','cancelled') for j in self.workspace.jobs):
            self.message('Zuerst die offenen Aufträge dieses Kontos entfernen.','Remove this account’s pending jobs first.');return
        dialog=QDialog(self);v=QVBoxLayout(dialog);v.addWidget(self.label('Nur den Kontoeintrag entfernen? Dateien und gespeicherte Garmin-Sitzung bleiben erhalten. Sitzungsschlüssel lassen sich über die Garmin-Anmeldung entfernen.',
                                                                                     'Remove only the account entry? Files and the saved Garmin session are retained. Session tokens can be removed in Garmin sign-in settings.'))
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel);v.addWidget(buttons);buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject)
        if dialog.exec()!=QDialog.DialogCode.Accepted:return
        self.workspace.data['accounts']=[x for x in self.workspace.accounts if x['id']!=a['id']];self.clients.pop(a['id'],None);self.active_account=None;self.api=None;self.identity=None;self.save_workspace();self.refresh_accounts()
    def open_account(self):
        if not self.active_account:return
        if self.active_account['provider']=='garmin':self.account_dialog.show();self.account_dialog.raise_();return
        if self.active_account['provider']=='komoot':self.open_komoot_account();return
        a=self.active_account;dialog=QDialog(self);dialog.setWindowTitle(a['provider'].capitalize());v=QVBoxLayout(dialog)
        note=QLabel(self.provider_note(a['provider']));note.setWordWrap(True);v.addWidget(note)
        field=QLineEdit(a['output']);row=QHBoxLayout();row.addWidget(field);row.addWidget(self.button('Ordner wählen','Choose folder',lambda:self.pick_account_folder(field)));v.addLayout(row)
        if a['provider']=='strava':
            v.addWidget(self.button('Strava-Datenpaket importieren …','Import Strava data package …',lambda:(dialog.accept(),QTimer.singleShot(0,self.import_strava_dialog))))
            v.addWidget(self.button('Lokale Strava-Daten öffnen','Open local Strava data',lambda:(dialog.accept(),QTimer.singleShot(0,self.open_strava_data))))
        else:v.addWidget(self.button('Lokale Dateien importieren','Import local files',lambda:self.data_page.import_dialog()))
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel);v.addWidget(buttons);buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject)
        if dialog.exec()==QDialog.DialogCode.Accepted and field.text().strip():a['output']=field.text();self.save_workspace();self.refresh_accounts(a['id'])
    def login_done(self,result):
        super().login_done(result)
        if not self._studio_ready:return
        account=next((a for a in self.workspace.accounts if a['id']==self.identity),None)
        if not account:account=self.workspace.add_account('garmin',result[2],self.output.text(),self.china.isChecked())
        self.clients[account['id']]=self.api;self.active_account=account;self.refresh_accounts(account['id']);self.account_dialog.close()
    def forget(self):
        ident=self.identity or (self.active_account or {}).get('id');super().forget()
        if self._studio_ready:
            self.clients.pop(ident,None);self.active_account=None;self.refresh_accounts(ident)
    def show_options(self,index=0):
        if self.active_account and self.active_account['provider']!='garmin':self.open_account();return
        if not self.options_dialog.isVisible():
            self._option_snapshot=(deepcopy(self.make_plan(for_sync=True)),list(self.selected_activity_ids),self.output.text(),self.archive_path.text(),self.use_offline.isChecked(),self.simple_preset.currentIndex())
            self._options_extras=(self.expert_enable.isChecked(),self.method.currentText(),self.kwargs.toPlainText(),self.expert_daily.isChecked(),self.archive_details.isChecked(),self.archive_original.isChecked(),[k for k,c in self.archive_format_checks.items() if c.isChecked()])
        self.option_tabs.setCurrentIndex(index);self.options_dialog.show();self.options_dialog.raise_();self.simple_preset.setCurrentIndex(3)
    def apply_simple_preset(self,index):
        key=self.simple_preset.currentData()
        if key=='activities':self.activity_list_preset()
        elif key=='daily':
            self.select_all(False)
            for key in ('summary','heart_rate','sleep','steps','stress'):self.dataset_checks[key].setChecked(True)
            self.health_detail.setCurrentIndex(self.health_detail.findData('daily'))
        elif key=='all':
            self.select_all(True);self.dataset_checks['wellness_fit'].setChecked(False)
            self.health_detail.setCurrentIndex(self.health_detail.findData('full'))
        self.refresh_selection_summary()
    def refresh_selection_summary(self,*args):
        if not hasattr(self,'selection_summary'):return
        count=sum(c.isChecked() for c in self.dataset_checks.values());n=len(self.selected_activity_ids)
        self.selection_summary.setText(self.tr(f'{count} Datenarten · '+(f'{n} ausgewählte Aktivitäten' if n else 'alle passenden Aktivitäten im Zeitraum'),
                                               f'{count} datasets · '+(f'{n} selected activities' if n else 'all matching activities in date range')))
    def clear_activity_selection(self):self.selected_activity_ids=[];self.refresh_selection_summary()
    def invalidate_inventory(self,*args):self.inventory_result=None;self.selected_activity_ids=[];self.refresh_selection_summary()
    def make_plan(self,*args,**kwargs):
        plan=super().make_plan(*args,**kwargs)
        return replace(plan,activity_ids=list(self.selected_activity_ids))
    def show_export_preview(self):
        if self.active_account and self.active_account['provider']!='garmin':self.message(self.provider_note(self.active_account['provider']),self.provider_note(self.active_account['provider']));return
        if self.selected_activity_ids:
            self.message('Die Ausgabevorschau ist eine begrenzte Stichprobe und prüft gewählte IDs außerhalb der ersten Listenseiten nicht zuverlässig. Für die Auswahl zuerst Nur herunterladen starten und anschließend lokal exportieren.',
                         'Output preview is a bounded sample and cannot reliably check selected IDs beyond the first list pages. Download the selection first, then export offline.');return
        super().show_export_preview()

    def preview_done(self,payload):
        super().preview_done(payload)
        if self._studio_ready:self.tabs.setCurrentIndex(1);self.show_options(2)
    def toggle_language(self):
        super().toggle_language()
        if not self._studio_ready:return
        for i,(de,en) in enumerate(self.option_labels):self.option_tabs.setTabText(i,self.tr(de,en))
        for i,(de,en) in enumerate([('Aktivitätenliste','Activity list'),('Gesundheit: Tageskennzahlen','Health: daily statistics'),('Alle unterstützten Daten','All supported datasets'),('Eigene Auswahl unter Optionen','Custom selection in Options')]):self.simple_preset.setItemText(i,self.tr(de,en))
        self.options_dialog.setWindowTitle(self.tr('Download- und Exportoptionen','Download and export options'));self.account_dialog.setWindowTitle(self.tr('Garmin-Anmeldung','Garmin sign-in'))
        for i,(de,en) in enumerate([('Nur herunterladen','Download only'),('Download und Dateien exportieren','Download and export files'),('Nur lokal exportieren','Export offline only')]):self.job_action.setItemText(i,self.tr(de,en))
        for i,(de,en) in enumerate([('Aufgezeichnet','Recorded'),('Geplant','Planned'),('Alle Touren','All tours')]):self.komoot_kind.setItemText(i,self.tr(de,en))
        self.refresh_accounts();self.render_jobs();self.refresh_selection_summary()
    def on_event(self,args):
        if args[0]=='komoot_inventory':
            text=self.tr(f'Komoot-Bestand: {args[1]} Touren aufgelistet',f'Komoot inventory: {args[1]} tours listed');self.status.setText(text);self.log.appendPlainText(text)
        elif args[0]=='komoot_download':
            self.progress.setRange(0,args[2]);self.progress.setValue(args[1])
            text=self.tr(f'Komoot: {args[1]} / {args[2]} Touren verarbeitet',f'Komoot: {args[1]} / {args[2]} tours processed');self.status.setText(text);self.log.appendPlainText(text)
        else:super().on_event(args)
    def set_busy(self,busy):
        super().set_busy(busy)
        if self._studio_ready:
            self.accounts_page.setEnabled(not busy);self.download_page.setEnabled(not busy);self.option_tabs.setEnabled(not busy)
    def message(self,de,en):
        if self._job:
            self.log.appendPlainText(self.tr(de,en));return
        super().message(de,en)

    def show_inventory(self):
        a=self.active_account
        if not a or a['provider']!='garmin':
            self.message('Die Online-Bestandsübersicht ist zunächst für Garmin verfügbar.','Online inventory is initially available for Garmin.');return
        if not self.api:
            self.open_account();return
        start=self.start_date.date().toString('yyyy-MM-dd');end=self.end_date.date().toString('yyyy-MM-dd')
        if start>end:self.message('Zeitraum prüfen.','Check date range.');return
        path=self.workspace.path.parent/'inventories'/(a['id']+'.json')
        result=self.inventory_result
        if not result:
            try:
                saved=json.loads(path.read_text())
                if saved.get('account')==a['id'] and saved.get('start')==start and saved.get('end')==end and isinstance(saved.get('items'),list):result=saved
            except (OSError,ValueError,TypeError):pass
        if result:self.open_inventory_dialog(result)
        else:self.fetch_inventory()

    def fetch_inventory(self,more=False):
        if not self.active_account or not self.api:return
        if self.worker and self.worker.isRunning():return
        a=deepcopy(self.active_account);api=self.api
        start=self.start_date.date().toString('yyyy-MM-dd');end=self.end_date.date().toString('yyyy-MM-dd')
        previous=deepcopy(self.inventory_result) if more else None
        interval=self.delay.value()
        if hasattr(self,'inventory_dialog'):self.inventory_dialog.close()
        def op(w):
            result=read_inventory(api,start,end,previous=previous,pages=10,interval=interval,cancel=w.cancel,event=lambda *x:w.event.emit(x))
            result['account']=a['id']
            try:atomic_json(self.workspace.path.parent/'inventories'/(a['id']+'.json'),result)
            except OSError:result['cache_error']=True
            return result
        self.run_worker(op,self.open_inventory_dialog)

    def open_inventory_dialog(self,result):
        self.inventory_result=result
        dialog=QDialog(self);self.inventory_dialog=dialog
        dialog.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint,True)
        dialog.setWindowTitle(self.tr('Online-Bestand · nur Aktivitäten-Metadaten','Online inventory · activity metadata only'));dialog.resize(1000,650)
        v=QVBoxLayout(dialog)
        from datetime import datetime
        checked=datetime.fromtimestamp(result.get('checked_at',0)).astimezone().strftime('%Y-%m-%d %H:%M')
        complete=self.tr('Zeitraum vollständig aufgelistet','Date range fully listed') if result.get('complete') else self.tr('Teilweise geladen – weitere Seiten können vorhanden sein','Partially loaded – more pages may exist')
        note=QLabel(f"{result['start']} – {result['end']} · {len(result['items'])} · {complete}\n"+self.tr('Stand: ','Checked: ')+checked+'\n'+self.tr('Keine Aktivitätsdateien oder Messverläufe geladen. Diese Liste sagt nichts über verfügbare Gesundheitsdaten aus.',
                                 'No activity files or measurement streams downloaded. This list does not establish health-data availability.'))
        note.setWordWrap(True);v.addWidget(note)
        if result.get('error'):
            detail=result['error'];label=QLabel(self.error_description(detail));label.setWordWrap(True);label.setObjectName('warningText');v.addWidget(label)
            self.register_rate_limit(detail)
        if result.get('cache_error'):v.addWidget(self.label('Die Übersicht konnte nicht lokal gespeichert werden.','Could not save this inventory locally.'))
        row=QHBoxLayout();search=QLineEdit();search.setPlaceholderText(self.tr('Name oder Datum suchen','Search name or date'));sport=QComboBox();sport.addItem(self.tr('Alle Sportarten','All sports'),'')
        kinds=sorted({str((a.get('activityType') or {}).get('typeKey','')) for a in result['items'] if isinstance(a.get('activityType'),dict)})
        from sports import sport_label
        for key in kinds:sport.addItem(sport_label(key,self.lang),key)
        row.addWidget(search,2);row.addWidget(sport,1);v.addLayout(row)
        table=QTableWidget(0,6);table.setHorizontalHeaderLabels([self.tr('Datum','Date'),self.tr('Aktivität','Activity'),self.tr('Sportart','Sport'),self.tr('Distanz (km)','Distance (km)'),self.tr('Dauer','Duration'),'ID'])
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows);table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        header=table.horizontalHeader();header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive);header.setSectionsMovable(True)
        header.setStretchLastSection(False);header.setResizeContentsPrecision(-1)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel);v.addWidget(table,1)
        def populate():
            table.setRowCount(0)
            for item in result['items']:
                key=(item.get('activityType') or {}).get('typeKey','') if isinstance(item.get('activityType'),dict) else ''
                text=str(item.get('activityName',''))+' '+str(item.get('startTimeLocal',''))
                if search.text().casefold() not in text.casefold() or (sport.currentData() and sport.currentData()!=key):continue
                r=table.rowCount();table.insertRow(r)
                distance=item.get('distance');duration=item.get('duration')
                values=[str(item.get('startTimeLocal',''))[:19],str(item.get('activityName','')),sport_label(key,self.lang),
                        f'{distance/1000:.2f}' if isinstance(distance,(int,float)) else '',
                        f'{int(duration)//3600:02}:{int(duration)%3600//60:02}:{int(duration)%60:02}' if isinstance(duration,(int,float)) else '',str(item['activityId'])]
                for c,value in enumerate(values):table.setItem(r,c,QTableWidgetItem(value))
                if str(item['activityId']) in self.selected_activity_ids:
                    from PySide6.QtCore import QItemSelectionModel
                    table.selectionModel().select(table.model().index(r,0),QItemSelectionModel.SelectionFlag.Select|QItemSelectionModel.SelectionFlag.Rows)
        search.textChanged.connect(populate);sport.currentIndexChanged.connect(populate);populate()
        table.resizeColumnsToContents()
        v.addWidget(self.label('Strg: einzelne Zeilen ergänzen · Shift: Bereich auswählen. Die Auswahl gilt nur für Aktivitäten; Gesundheitskategorien bleiben separat gewählt.',
                              'Ctrl: add individual rows · Shift: select a range. Selection only affects activities; health datasets remain separately selected.'))
        komoot=result.get('provider')=='komoot'
        refresh=self.fetch_komoot_inventory if komoot else self.fetch_inventory
        row=QHBoxLayout();row.addWidget(self.button('Übersicht aktualisieren','Refresh inventory',lambda:refresh(False)))
        more=self.button('Weitere Seiten laden','Load more pages',lambda:refresh(True));more.setEnabled(not result.get('complete'));row.addWidget(more)
        row.addWidget(self.button('Alle sichtbaren auswählen','Select all visible',table.selectAll));row.addStretch()
        def apply():
            selected=sorted({table.item(i.row(),5).text() for i in table.selectionModel().selectedRows()})
            if not selected:self.message('Bitte mindestens eine Aktivität auswählen. Für den gesamten Zeitraum Auswahl zurücksetzen verwenden.',
                                         'Select at least one activity. Use Clear activity selection for the whole date range.');return
            if komoot:
                if not self.active_account or self.active_account['id']!=result.get('account'):
                    self.message('Konto wurde gewechselt. Übersicht erneut öffnen.','Account changed. Reopen inventory.');return
                items=[i for i in result['items'] if str(i['activityId']) in selected]
                dialog.close();QTimer.singleShot(0,lambda:self.review_komoot_download(items));return
            self.selected_activity_ids=selected;self.set_sport('');self.dataset_checks['activities'].setChecked(True);self.refresh_selection_summary();dialog.accept()
        row.addWidget(self.button('Auswahl herunterladen …' if komoot else 'Auswahl übernehmen','Download selection …' if komoot else 'Use selection',apply,primary=True));v.addLayout(row)
        dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose,True);dialog.show();dialog.raise_()

    def enqueue_current(self,checked=False,action=None):
        a=self.active_account
        if not a:
            self.tabs.setCurrentIndex(0);self.message('Zuerst ein Konto hinzufügen.','Add an account first.');return
        if a['provider']!='garmin':self.message(self.provider_note(a['provider']),self.provider_note(a['provider']));return
        mode=self.job_action.currentData() if action is None else action
        try:
            if mode=='offline':
                if not self.archive_path.text().strip():raise ValueError('Archive required')
                with Archive(self.archive_path.text(),readonly=True) as db:
                    if db.account!=a['id']:raise ValueError('Account mismatch')
                plan=replace(self.make_plan(for_sync=True),source='offline',account=a['id'])
            else:
                if not self.api:self.open_account();return
                self.ensure_archive_path();plan=replace(self.make_plan(for_sync=True),source='online',account=a['id'])
            if not self.output.text().strip():raise ValueError('Destination required')
            if self.expert_enable.isChecked():
                if mode in ('download','offline'):raise ValueError('Expert queries need online export')
                from engine import read_methods,substitute
                from garminconnect import Garmin
                import inspect
                method=self.method.currentText();parameters=json.loads(self.kwargs.toPlainText())
                if method not in read_methods(Garmin):raise ValueError('Invalid method')
                inspect.signature(getattr(self.api,method)).bind(**substitute(parameters,plan.start,plan.start,plan.end))
                plan=replace(plan,expert_method=method,expert_kwargs=parameters,expert_daily=self.expert_daily.isChecked())
            if mode=='download':plan=replace(plan,formats=['json'])
            plan.validate()
            self.workspace.enqueue(a,plan,'download' if mode=='download' else 'export')
        except (ValueError,OSError,TypeError,AttributeError) as exc:
            self.message('Auftrag konnte nicht angelegt werden. Zeitraum, Auswahl, Ausgabe und passende Datenbank prüfen.',
                         'Could not add job. Check dates, selection, output and matching archive.');return
        self.render_jobs();self.tabs.setCurrentIndex(1)
    def start_download_only(self):self.enqueue_current(action='download');self.review_jobs()
    def start_export(self):self.enqueue_current(action='export');self.review_jobs()
    def render_jobs(self):
        if not hasattr(self,'jobs_table'):return
        self.jobs_table.setHorizontalHeaderLabels([self.tr('Konto / Zeitraum','Account / dates'),self.tr('Aktion','Action'),self.tr('Aktivitäten','Activities'),self.tr('Status','Status')])
        self.jobs_table.setRowCount(len(self.workspace.jobs))
        states={'queued':('Vorgemerkt','Queued'),'running':('Läuft','Running'),'complete':('Fertig','Complete'),
                'failed':('Mit Fehlern','Failed'),'interrupted':('Unterbrochen','Interrupted'),'cancelled':('Abgebrochen','Stopped'),
                'waiting':('Wartet auf Anmeldung / Freigabe','Waiting for sign-in / availability')}
        for r,j in enumerate(self.workspace.jobs):
            p=j['plan'];state=states.get(j['status'],(j['status'],j['status']))
            mode=self.tr('Nur herunterladen','Download only') if j['action']=='download' else self.tr('Offline-Export','Offline export') if p['source']=='offline' else self.tr('Download + Export','Download + export')
            values=[j['provider'].capitalize()+' · '+j['email']+'\n'+p['start']+' – '+p['end'],mode,str(len(p.get('activity_ids',[]))) if p.get('activity_ids') else self.tr('Zeitraum','Date range'),self.tr(*state)]
            for c,text in enumerate(values):self.jobs_table.setItem(r,c,QTableWidgetItem(text))
        self.jobs_table.resizeRowsToContents()
    def move_job(self,delta):
        if self._queue_active:return
        row=self.jobs_table.currentRow();other=row+delta
        if row<0 or not 0<=other<len(self.workspace.jobs):return
        jobs=self.workspace.jobs;jobs[row],jobs[other]=jobs[other],jobs[row];self.save_workspace();self.render_jobs();self.jobs_table.selectRow(other)
    def remove_job(self):
        if self._queue_active:return
        row=self.jobs_table.currentRow()
        if 0<=row<len(self.workspace.jobs):self.workspace.jobs.pop(row);self.save_workspace();self.render_jobs()
    def pending_jobs(self):return [j for j in self.workspace.jobs if j['status'] in ('queued','interrupted','failed','waiting')]
    def job_description(self,j):
        p=j['plan'];names={d.key:(d.de if self.lang=='de' else d.en) for d in DATASETS}
        from preflight import inspect_plan
        analysis=inspect_plan(Plan(**p),self.clients.get(j['account']))
        kind=self.tr('Nur herunterladen – keine Ausgabedateien','Download only – no output files') if j['action']=='download' else ', '.join(x.upper() for x in p['formats'])
        selected=str(len(p.get('activity_ids',[]))) if p.get('activity_ids') else self.tr('alle passenden im Zeitraum','all matching in date range')
        text=f"{j['provider'].capitalize()} · {j['email']}\n{p['start']} – {p['end']}\n"+', '.join(names.get(k,k) for k in p['datasets'])+'\n'+self.tr('Aktivitäten: ','Activities: ')+selected+'\n'+kind+'\n'+self.tr('Ziel: ','Destination: ')+p['output']+'\n'+self.tr('Datenbank: ','Archive: ')+p['archive_path']
        if analysis.get('note')=='sqlite_only':
            text+='\n'+self.tr(f'Lokale Planung: {analysis["cached"]} passende gespeicherte Grundantworten · ungefähr {analysis["pending"]} offene Grundabfragen.',
                                f'Local planning: {analysis["cached"]} matching saved base responses · approximately {analysis["pending"]} pending base requests.')
            text+='\n'+self.tr('Zusätzliche Listenseiten, Detaildaten, Wiederholungen und Bereichs-Fallbacks sind darin nicht vollständig enthalten. Ältere Datei-Caches werden erst bei der Ausführung berücksichtigt.',
                               'Additional list pages, detail data, retries and range fallbacks are not fully included. Older file caches are considered during execution.')
            spacing=analysis.get('minimum_spacing_seconds',0)
            if spacing>=60:text+='\n'+self.tr(f'Allein aus dem Anfrageabstand ergeben sich für diese Planung ungefähr {spacing/60:.0f} Minuten; Server- und Dateiverarbeitungszeit kommen hinzu.',
                                                f'The request interval alone accounts for roughly {spacing/60:.0f} minutes for this plan; server and file-processing time add to this.')
        if p['source']=='offline':text+='\n'+self.tr('Keine Netzabrufe. Dauer abhängig von Datenmenge und Dateiformaten.','No network requests. Duration depends on data volume and formats.')
        else:
            n=(date.fromisoformat(p['end'])-date.fromisoformat(p['start'])).days+1
            text+='\n'+self.tr(f'{n} Kalendertage · {p["workers"]} parallele Abfragen · {p["delay"]} s gemeinsamer Mindestabstand.',
                               f'{n} calendar days · {p["workers"]} parallel requests · {p["delay"]} s shared minimum interval.')
            text+='\n'+self.tr('Restaufwand und Dauer vorab unbekannt: abhängig von gespeicherten Antworten, Aktivitätsdetails, Antwortzeiten und Wiederholungen. Die Download-Restzeit wird im Lauf gemessen.',
                               'Remaining work and duration unknown before starting: depend on stored responses, activity extras, response times and retries. Download ETA is measured during the run.')
        if 'activities' in p['datasets']:text+='\n'+self.tr('Aktivitätszusätze: ','Activity extras: ')+str(len(p['activity_details']))+' · '+', '.join(p['activity_files'])
        if p['health_detail']=='full' and any(k not in ('activities','devices','records','goals') for k in p['datasets']):
            text+='\n'+self.tr('Vollständige Gesundheitsverläufe können viele tägliche Einzelabfragen erfordern. Tageskennzahlen sind weniger detailliert und häufig schneller.',
                               'Full health timelines can require many daily requests. Daily statistics are less detailed and often faster.')
        if j['action']=='export' and 'xlsx' in p['formats']:text+='\n'+self.tr('Excel-Dateien müssen nach dem Download erstellt und komprimiert werden. Auch ohne neue Downloads kann dies dauern.',
                                                                                                           'Excel files must be generated and compressed after retrieval. This can take time even without new downloads.')
        if p.get('activity_ids') and 'activities' in p['datasets']:text+='\n'+self.tr('Die Aktivitätenliste wird für die Ausführung gegebenenfalls erneut abgerufen; Details/Dateien werden nur für die gewählten IDs angefordert.',
                                                                                                                  'The activity list may be fetched again when executing; details/files are requested only for selected IDs.')
        return text
    def review_jobs(self):
        jobs=self.pending_jobs()
        if not jobs:self.message('Keine offenen Aufträge. Erst Auswahl zur Auftragsliste hinzufügen.','No pending jobs. Add a selection to the job list first.');return
        if self._queue_active:return
        dialog=QDialog(self);dialog.setWindowTitle(self.tr('Aufträge prüfen und starten','Review and start jobs'));dialog.resize(850,650);v=QVBoxLayout(dialog)
        from PySide6.QtWidgets import QTextBrowser
        text=QTextBrowser();text.setPlainText(('\n\n'+'─'*36+'\n\n').join(self.job_description(j) for j in jobs));v.addWidget(text)
        v.addWidget(self.label('Es wurde noch kein Auftrag gestartet. Einstellungen ändern: zurückgehen, den vorgemerkten Auftrag entfernen und mit der neuen Auswahl hinzufügen.',
                              'No job has started yet. To change settings, go back, remove the queued job and add the revised selection.'))
        row=QHBoxLayout();back=self.button('Zurück zu den Einstellungen','Back to settings',dialog.reject);start=self.button('Download / Export starten','Start download / export',dialog.accept,primary=True)
        row.addWidget(back);row.addStretch();row.addWidget(start);v.addLayout(row)
        if dialog.exec()!=QDialog.DialogCode.Accepted:return
        self._queue_active=True;self._queue_stop=False;self._run_ids=[j['id'] for j in jobs];self.queue_next()
    def queue_next(self):
        if not self._queue_active or self._queue_stop:
            self._queue_active=False;self._job=None;self.render_jobs();return
        while self._run_ids:
            ident=self._run_ids.pop(0);j=next((x for x in self.workspace.jobs if x['id']==ident),None)
            if not j:continue
            p=Plan(**deepcopy(j['plan']))
            if p.source=='online' and (j['account'] not in self.clients or self.rate_pause.remaining()):
                j['status']='waiting';self.save_workspace();continue
            try:p.validate()
            except ValueError:j['status']='failed';self.save_workspace();continue
            self._job=j;j['status']='running'
            if not self.save_workspace():self._queue_active=False;self._job=None;j['status']='failed';self.render_jobs();return
            self.render_jobs();self.completed=0
            api=self.clients.get(j['account'])
            def operation(w):
                event=lambda *a:w.event.emit(a)
                if j['action']=='download':return ArchiveSync(api,p,w.cancel,event).run_sync()
                return (OfflineExporter(p,w.cancel,event) if p.source=='offline' else ArchiveExporter(api,p,w.cancel,event)).run()
            self.run_worker(operation,self.queue_done,network=p.source!='offline');return
        self._queue_active=False;self._job=None;self.render_jobs()
        self.status.setText(self.tr('Auftragsliste abgearbeitet. Status und Protokoll prüfen.','Job list processed. Check status and log.'))
    def queue_done(self,result):
        j=self._job
        if not j:return
        report=result['report'] if j['action']=='download' else result[1]
        j['status']='cancelled' if report.get('cancelled') else 'complete' if report.get('completed') else 'failed'
        j['finished']=now();j['requests']=report.get('transfer',{}).get('requests',0);j['timings']=report.get('timings',{});self.save_workspace()
        if j['action']=='export':super().export_done(result)
        else:
            self.register_rate_limit(report.get('fatal_diagnostic') or {})
            self.log.appendPlainText(self.tr('Gesichert: ','Archived: ')+result['path'])
        self.render_jobs()
    def worker_failed(self,detail):
        if self._job:self._job['status']='failed';self._job['error']=detail;self.save_workspace()
        super().worker_failed(detail)
    def worker_finished(self):
        super().worker_finished()
        if self._studio_ready and self._queue_active:
            self._job=None
            QTimer.singleShot(0,self.queue_next)
    def stop(self):
        if self._queue_active:self._queue_stop=True
        super().stop()
    def closeEvent(self,event):
        if (self.worker and self.worker.isRunning()) or (self.data_page.track_worker and self.data_page.track_worker.isRunning()):super().closeEvent(event);return
        self._queue_active=False
        if self._studio_ready:
            self.save_workspace()
            QApplication.instance().removeEventFilter(self._tooltip_filter)
            for dialog in (self.options_dialog,self.account_dialog,self.log_dialog):dialog.close()
        super().closeEvent(event)

    def save_account_defaults(self):
        a=self.active_account
        if not a or a['provider']!='garmin':return
        try:
            plan=self.make_plan(for_sync=True);plan.validate()
            settings=vars(plan).copy()
            for key in ('account','start','end','activity_ids','output','archive_path'):settings.pop(key,None)
            a['settings']=settings;a['output']=self.output.text();a['archive_path']=self.archive_path.text()
            if self.save_workspace():self.status.setText(self.tr('Kontovorgabe gespeichert.','Account defaults saved.'))
        except (ValueError,TypeError):self.message('Auswahl prüfen.','Check selection.')

    def apply_account_defaults(self,account):
        base=dict(start=self.start_date.date().toString('yyyy-MM-dd'),end=self.end_date.date().toString('yyyy-MM-dd'),
                  account=account['id'],output=account['output'],datasets=['activities'],delay=.5,workers=3,split_year=False)
        try:
            settings=account.get('settings',{})
            if not isinstance(settings,dict):raise ValueError()
            allowed=set(Plan.__dataclass_fields__)-{'account','start','end','output','activity_ids','archive_path'}
            p=Plan(**(base|{k:v for k,v in settings.items() if k in allowed}));p.validate()
        except (ValueError,TypeError):p=Plan(**base)
        self.apply_plan_controls(p)
        self.simple_preset.blockSignals(True);self.simple_preset.setCurrentIndex(3 if settings else 0);self.simple_preset.blockSignals(False)

    def apply_plan_controls(self,p):
        for checks,selected in ((self.dataset_checks,p.datasets),(self.detail_checks,p.activity_details),(self.file_checks,p.activity_files),(self.format_checks,p.formats)):
            for key,check in checks.items():check.setChecked(key in selected)
        for widget,value in ((self.layout_combo,p.layout),(self.delimiter,p.delimiter),(self.health_detail,p.health_detail)):
            widget.setCurrentIndex(widget.findData(value))
        for widget,value in ((self.delay,p.delay),(self.workers,p.workers),(self.retries,p.retries),(self.refresh,p.refresh_days),
                             (self.activity_batch_days,p.activity_batch_days),(self.health_batch_days,p.health_batch_days),
                             (self.preview_rows,p.preview_rows),(self.preview_requests,p.preview_requests)):
            widget.setValue(value)
        for widget,value in ((self.split,p.split_year),(self.reuse_exports,p.reuse_exports),(self.export_history,p.export_history),
                             (self.optimize,p.optimize),(self.skip_empty,p.skip_empty),(self.activity_summary,p.activity_summary)):
            widget.setChecked(value)
        self.set_sport(p.activity_type);self.selectors.setPlainText('\n'.join(p.selectors));self.expert_enable.setChecked(False)
        self.refresh_selection_summary()

    def restore_option_snapshot(self):
        snapshot=getattr(self,'_option_snapshot',None)
        if not snapshot:return
        plan,ids,output,archive,offline,preset=snapshot
        self.apply_plan_controls(plan);self.selected_activity_ids=ids;self.output.setText(output);self.archive_path.setText(archive);self.use_offline.setChecked(offline)
        self.simple_preset.blockSignals(True);self.simple_preset.setCurrentIndex(preset);self.simple_preset.blockSignals(False)
        if hasattr(self,'_options_extras'):
            enabled,method,kwargs,daily,details,original,formats=self._options_extras
            self.expert_enable.setChecked(enabled);self.method.setCurrentText(method);self.kwargs.setPlainText(kwargs);self.expert_daily.setChecked(daily)
            self.archive_details.setChecked(details);self.archive_original.setChecked(original)
            for key,c in self.archive_format_checks.items():c.setChecked(key in formats)
        self._option_snapshot=None;self.refresh_selection_summary()

    def start_archive_sync(self,checked=False,selected_only=False):
        from app import MIN_SYNC_INTERVAL
        a=self.active_account
        if not a or a['provider']!='garmin' or not self.api:self.open_account();return
        try:
            self.ensure_archive_path();base=self.make_plan(for_sync=True)
            plan=replace(base,source='online',account=a['id'],datasets=base.datasets if selected_only else [d.key for d in DATASETS if d.full_sync],
                health_detail=base.health_detail if selected_only else 'full',activity_ids=base.activity_ids if selected_only else [],activity_type='',selectors=[],formats=['json'],
                activity_details=list(ACTIVITY_DETAILS) if self.archive_details.isChecked() else [],
                activity_files=(['ORIGINAL'] if self.archive_original.isChecked() else [])+[k for k,c in self.archive_format_checks.items() if c.isChecked()],
                delay=max(MIN_SYNC_INTERVAL,base.delay),retries=max(1,base.retries))
            if 'activities' not in plan.datasets:plan=replace(plan,activity_details=[],activity_files=[])
            plan.validate();self.workspace.enqueue(a,plan,'download')
        except (ValueError,OSError,TypeError):self.message('Einstellungen und Datenbank prüfen.','Check settings and database.');return
        self.options_dialog.accept();self.render_jobs();self.tabs.setCurrentIndex(1);self.review_jobs()

    def update_format_controls(self):
        enabled=self.job_action.currentData()!='download'
        for control in self.format_checks.values():control.setEnabled(enabled)

    def update_connection(self):
        if getattr(self,'_studio_ready',False) and (self.active_account or {}).get('provider')=='komoot':
            signed=self.active_account['id'] in self.komoot_clients
            self.connection.setText(self.tr('Komoot · experimentell · ','Komoot · experimental · ')+self.tr('angemeldet' if signed else 'nicht angemeldet','connected' if signed else 'not connected'));return
        if getattr(self,'_studio_ready',False) and (self.active_account or {}).get('provider')=='strava':
            self.connection.setText(self.tr('Strava · lokale Importquelle · keine Anmeldung erforderlich','Strava · local import source · no sign-in required'));return
        super().update_connection()

    def komoot_database(self,account):
        from engine import account_root
        return str(account_root(account['output'],account['id'])/'komoot-offline.sqlite')

    def open_komoot_account(self):
        if self.worker and self.worker.isRunning():return
        a=self.active_account;dialog=QDialog(self);dialog.setWindowTitle('Komoot · '+self.tr('Anmeldung','Sign-in'));v=QVBoxLayout(dialog)
        note=QLabel(self.provider_note('komoot'));note.setWordWrap(True);v.addWidget(note)
        password=QLineEdit();password.setEchoMode(QLineEdit.EchoMode.Password)
        password.setPlaceholderText(self.tr('Komoot-Passwort','Komoot password'));v.addWidget(QLabel(a['email']));v.addWidget(password)
        field=QLineEdit(a['output']);r=QHBoxLayout();r.addWidget(field);r.addWidget(self.button('Zielordner','Destination',lambda:self.pick_account_folder(field)));v.addLayout(r)
        def sign_in():
            secret=password.text();password.clear()
            if not secret or not field.text().strip():return
            a['output']=field.text()
            if not self.save_workspace():return
            dialog.accept();self.start_komoot_login(deepcopy(a),secret)
        v.addWidget(self.button('Anmelden','Sign in',sign_in,primary=True))
        def disconnect():self.komoot_clients.pop(a['id'],None);self.refresh_accounts(a['id']);dialog.reject()
        v.addWidget(self.button('Abmelden','Sign out',disconnect));v.addWidget(self.button('Schließen','Close',dialog.reject));dialog.exec()

    def start_komoot_login(self,account,password):
        from komoot_client import KomootClient
        from failures import diagnostic
        client=KomootClient(self.data_dir/'komoot-pauses'/(account['id']+'.json'))
        def operation(w):
            try:return {'account':account,'client':client.login(account['email'],password,w.cancel)}
            except Exception as exc:return {'account':account,'error':diagnostic(exc)}
        def done(result):
            if result.get('error'):self.komoot_error(result['error']);return
            self.komoot_clients[account['id']]=result['client'];self.refresh_accounts(account['id']);self.tabs.setCurrentIndex(1)
        self.run_worker(operation,done,network=False)

    def komoot_error(self,detail):
        if detail.get('http_status')==401 and self.active_account:self.komoot_clients.pop(self.active_account['id'],None);self.update_connection()
        text=self.tr('Komoot-Abruf fehlgeschlagen: ','Komoot request failed: ')+str(detail.get('http_status') or detail.get('error_type','Error'))
        if detail.get('http_status')==429:text+='\n'+self.tr('Komoot begrenzt die Anfragen. Die Abrufpause bleibt auch nach einem Neustart erhalten.','Komoot rate limit reached. The request pause is retained across restarts.')
        if detail.get('http_status') in (401,403):text+='\n'+self.tr('Anmeldung oder Exportberechtigung prüfen. Bei einer gesperrten Region wird kein GPX-Zugriff erzwungen.','Check sign-in or export permission. Locked regions are not bypassed.')
        self.log.appendPlainText(text);self.message(text,text)

    def fetch_komoot_inventory(self,more=False):
        if self.worker and self.worker.isRunning():return
        a=deepcopy(self.active_account)
        if not a or a['provider']!='komoot':return
        client=self.komoot_clients.get(a['id'])
        if not client:self.open_komoot_account();return
        start=self.komoot_from.date().toString('yyyy-MM-dd');end=self.komoot_to.date().toString('yyyy-MM-dd');kind=self.komoot_kind.currentData()
        if start>end:self.message('Zeitraum prüfen.','Check date range.');return
        previous=deepcopy(self.inventory_result) if more and (self.inventory_result or {}).get('account')==a['id'] else None
        if previous and (previous.get('start'),previous.get('end'),previous.get('kind'))!=(start,end,kind):previous=None
        if hasattr(self,'inventory_dialog'):self.inventory_dialog.close()
        def operation(w):
            result=client.inventory(start,end,kind,previous,w.cancel,lambda *x:w.event.emit(x));result['account']=a['id']
            try:atomic_json(self.workspace.path.parent/'inventories'/(a['id']+'.json'),result)
            except OSError:result['cache_error']=True
            return result
        def done(result):
            if result.get('error'):self.komoot_error(result['error'])
            self.open_inventory_dialog(result)
        self.run_worker(operation,done,network=False)

    def review_komoot_download(self,items):
        a=deepcopy(self.active_account)
        if not a or a['provider']!='komoot':return
        dialog=QDialog(self);dialog.setWindowTitle(self.tr('Komoot-Download prüfen','Review Komoot download'));v=QVBoxLayout(dialog)
        note=QLabel(self.tr(f"{len(items)} ausgewählte Touren werden in den lokalen Kontobestand übernommen.\nZiel: {self.komoot_database(a)}\nDie Übersicht ist eventuell noch unvollständig. Eine verlässliche Restzeit ist vor dem ersten Abruf nicht bekannt. GPX-Anfragen erfolgen nacheinander mit mindestens 0,5 s Abstand.",
                           f"{len(items)} selected tours will be stored in the local account archive.\nDestination: {self.komoot_database(a)}\nThe inventory may still be partial. Remaining time is unknown before the first request. GPX requests run sequentially, at least 0.5 s apart."));note.setWordWrap(True);v.addWidget(note)
        gpx=self.check('GPX-Dateien zusätzlich herunterladen','Also download GPX files',True);v.addWidget(gpx)
        v.addWidget(self.label('Ohne GPX wird nur die Aktivitätenübersicht gespeichert; die Karte enthält dann keine Strecke. Vorhandene GPX-Dateien im Cache werden wiederverwendet.',
                              'Without GPX, only activity metadata is saved; no route appears on the map. Existing cached GPX files are reused.'))
        r=QHBoxLayout();r.addWidget(self.button('Abbrechen','Cancel',dialog.reject));r.addWidget(self.button('Download starten','Start download',dialog.accept,primary=True));v.addLayout(r)
        if dialog.exec()==QDialog.DialogCode.Accepted:self.start_komoot_download(a,items,gpx.isChecked())

    def start_komoot_download(self,account,items,gpx=True):
        from komoot_client import download_tours
        from datahub import load_archive
        client=self.komoot_clients.get(account['id'])
        if not client:self.open_komoot_account();return
        path=self.komoot_database(account)
        def operation(w):
            report=download_tours(client,path,account['id'],items,gpx,w.cancel,lambda *x:w.event.emit(x))
            return {'report':report,'data':load_archive(path,with_tracks=False),'path':path}
        def done(result):
            self.archive_path.setText(result['path']);self.data_page.filter_initialized=False;self.data_page.loaded(result['data']);self.tabs.setCurrentIndex(2)
            self.last_output=str(Path(result['path']).parent);self.open_button.setEnabled(True)
            report=result['report'];text=self.tr(f"Komoot: {report['imported']} Touren gespeichert · {report['files']} GPX geladen · {report['cached']} aus Cache.",f"Komoot: {report['imported']} tours saved · {report['files']} GPX downloaded · {report['cached']} cached.")
            if report['cancelled']:text+=' '+self.tr('Abgebrochen.','Stopped.')
            self.log.appendPlainText(text)
            if report['error']:self.komoot_error(report['error'])
        self.run_worker(operation,done,network=False)

    def open_komoot_data(self):
        if not self.active_account or self.active_account['provider']!='komoot':return
        path=self.komoot_database(self.active_account)
        if not Path(path).is_file():self.message('Noch keine Komoot-Touren gespeichert.','No Komoot tours stored yet.');return
        self.archive_path.setText(path);self.data_page.filter_initialized=False;self.tabs.setCurrentIndex(2);self.data_page.reload()

    def strava_database(self,account):
        from engine import account_root
        return str(account_root(account['output'],account['id'])/'strava-offline.sqlite')

    def import_strava_dialog(self):
        account=deepcopy(self.active_account)
        if not account or account['provider']!='strava' or (self.worker and self.worker.isRunning()):return
        choice=QMessageBox(self);choice.setWindowTitle(self.tr('Strava-Quelle auswählen','Select Strava source'))
        choice.setText(self.tr('Ist dein Strava-Datenpaket eine ZIP-Datei oder bereits ein entpackter Ordner?',
                               'Is your Strava data package a ZIP file or an extracted folder?'))
        zip_button=choice.addButton(self.tr('ZIP-Datei','ZIP file'),QMessageBox.ButtonRole.ActionRole)
        folder_button=choice.addButton(self.tr('Ordner','Folder'),QMessageBox.ButtonRole.ActionRole)
        choice.addButton(QMessageBox.StandardButton.Cancel);choice.exec()
        if choice.clickedButton()==zip_button:
            source,_=QFileDialog.getOpenFileName(self,self.tr('Strava-Datenpaket auswählen','Select Strava data package'),'', 'ZIP (*.zip)')
        elif choice.clickedButton()==folder_button:
            source=QFileDialog.getExistingDirectory(self,self.tr('Entpackten Strava-Datenordner auswählen','Select extracted Strava data folder'))
        else:return
        if not source:return
        policy=QMessageBox(self);policy.setWindowTitle(self.tr('Strava-Quelle speichern','Store Strava source'))
        policy.setText(self.tr('Die App erkennt und prüft die Quelle beim Import. Soll die vollständige Quelle am bisherigen Ort bleiben oder zusätzlich im Datenordner dieses Kontos gesichert werden?',
                              'The app detects and validates the source during import. Keep the complete source in its current location or also back it up in this account’s data folder?'))
        policy.setInformativeText(self.tr('In beiden Fällen erstellt die App ihre lokale Aktivitätsdatenbank einschließlich der importierten Aufzeichnungen. Die Quelle wird nicht verändert. Eine vollständige Kopie benötigt zusätzlichen Speicherplatz (höchstens 8 GiB pro Import).',
                                         'In both cases the app creates its local activity database including imported recordings. The source is unchanged. A complete copy needs additional disk space (up to 8 GiB per import).'))
        use=policy.addButton(self.tr('Quelle am bisherigen Ort nutzen','Use source in current location'),QMessageBox.ButtonRole.AcceptRole)
        copy=policy.addButton(self.tr('In App-Ordner kopieren','Copy into app folder'),QMessageBox.ButtonRole.ActionRole)
        policy.addButton(QMessageBox.StandardButton.Cancel);policy.exec()
        if policy.clickedButton() not in (use,copy):return
        path=self.strava_database(account)
        self.start_strava_import(account,source,path,copy_source=policy.clickedButton()==copy)

    def start_strava_import(self,account,source,path,copy_source=False):
        from strava_import import import_strava_archive,prepare_source
        from datahub import load_archive
        # Account identity is derived locally; a Garmin database cannot be overwritten accidentally.
        def operation(w):
            retained=prepare_source(source,Path(path).parent/'sources',copy_source,w.cancel)
            report=import_strava_archive(path,retained,account['id'],w.cancel,lambda *a:w.event.emit(a))
            report.update(source_path=str(retained),source_copied=copy_source,source_type='folder' if retained.is_dir() else 'zip')
            try:atomic_json(Path(path).parent/'strava-import-report.json',report)
            except OSError:report['report_write_error']=True
            return {'report':report,'data':load_archive(path,w.cancel if not w.cancel.is_set() else None,with_tracks=False),'path':path,'account':account}
        self.run_worker(operation,self.strava_import_done,network=False)

    def strava_import_done(self,result):
        report=result['report'];self.archive_path.setText(result['path']);self.data_page.filter_initialized=False
        account=next((a for a in self.workspace.accounts if a['id']==result['account']['id']),None)
        if account and report.get('source_path'):
            account['import_source']={k:report[k] for k in ('source_path','source_copied','source_type')};self.save_workspace()
        self.data_page.loaded(result['data']);self.tabs.setCurrentIndex(2)
        text=self.tr(f"Strava-Import: {report['imported']} neue Aktivitäten · {report['duplicates']} bereits bekannt/aktualisiert · {report['files']} Aktivitätsdateien · {report['failed']} Fehler.",
                     f"Strava import: {report['imported']} new activities · {report['duplicates']} already known/updated · {report['files']} activity files · {report['failed']} errors.")
        if report['cancelled']:text+='\n'+self.tr('Abgebrochen; bereits importierte Daten bleiben erhalten.','Stopped; imported data is retained.')
        if report.get('limited'):text+='\n'+self.tr('Größenlimit erreicht. Der Import ist nur teilweise erfolgt.','Import size limit reached. Only part of the archive was processed.')
        self.last_output=str(Path(result['path']).parent);self.open_button.setEnabled(True)
        for error in report.get('errors',[]):
            self.log.appendPlainText(self.tr('Strava-Importfehler: Zeile ','Strava import error: row ')+str(error.get('row','?'))+' · '+error.get('stage','')+' · '+error.get('error_type','Error'))
        codes={e.get('import_code') for e in report.get('errors',[]) if e.get('import_code')}
        for code in sorted(codes):
            detail=self.error_description({'import_code':code})
            self.log.appendPlainText(detail);text+='\n'+detail
        if report.get('report_write_error'):text+='\n'+self.tr('Importbericht konnte nicht als Datei gespeichert werden.','Could not save the import report file.')
        self.log.appendPlainText(text);self.message(text,text)

    def open_strava_data(self):
        account=self.active_account
        if not account or account['provider']!='strava':return
        path=self.strava_database(account)
        if not Path(path).is_file():self.message('Noch keine Strava-Daten importiert. Zuerst ein selbst heruntergeladenes Konto-ZIP oder einen entpackten Ordner auswählen.',
                                              'No Strava data imported yet. Select your downloaded account ZIP or extracted folder first.');return
        self.archive_path.setText(path);self.data_page.filter_initialized=False;self.tabs.setCurrentIndex(2);self.data_page.reload()

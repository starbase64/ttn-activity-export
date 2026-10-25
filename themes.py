"""Accessible light/dark palettes shared by widgets, popups and painted maps."""
import json
from pathlib import Path
from PySide6.QtGui import QColor,QPalette

LIGHT=dict(bg='#f4f7fb',panel='#ffffff',text='#192b43',muted='#53677f',border='#a6b8cb',button='#e3ebf4',hover='#d1e3f1',tab='#e7edf5',accent='#087eaa',accent_text='#f1f6fa',link='#076fa0',selection='#c4e5f4',selection_text='#102b40',disabled='#63748a',disabled_bg='#e4e9ee',warning='#815000',warning_bg='#fff1d0',error='#a23535',grid='#d3e0e6',alternate='#edf3f9')
DARK=dict(bg='#171e28',panel='#202a37',text='#e2e8f0',muted='#b2c0d1',border='#6d829a',button='#304155',hover='#405872',tab='#253344',accent='#126d89',accent_text='#f0f5fa',link='#7dd3fc',selection='#375571',selection_text='#f0f5fa',disabled='#9aabbd',disabled_bg='#293441',warning='#f7cf80',warning_bg='#44371f',error='#ffb4b4',grid='#35465b',alternate='#263344')


def load_theme(path):
    try:
        value=json.loads(Path(path).read_text(encoding='utf-8')).get('theme')
        return value if value in ('light','dark') else 'light'
    except (OSError,ValueError,TypeError,AttributeError):return 'light'


def colors(mode):return DARK if mode=='dark' else LIGHT


def palette(mode):
    c=colors(mode);p=QPalette()
    for role,key in {'Window':'bg','WindowText':'text','Base':'panel','AlternateBase':'alternate','ToolTipBase':'panel','ToolTipText':'text','Text':'text','Button':'button','ButtonText':'text','BrightText':'accent_text','Highlight':'selection','HighlightedText':'selection_text','Link':'link','LinkVisited':'link','PlaceholderText':'muted','Mid':'grid','Light':'hover','Dark':'bg'}.items():
        p.setColor(getattr(QPalette.ColorRole,role),QColor(c[key]))
    for role in ('WindowText','Text','ButtonText','PlaceholderText'):
        p.setColor(QPalette.ColorGroup.Disabled,getattr(QPalette.ColorRole,role),QColor(c['disabled']))
    return p


def stylesheet(mode):
    c=colors(mode)
    return '''
QWidget { background: %(bg)s; color: %(text)s; font-size:14px; }
QLabel#title { font-size:27px; font-weight:700; }
QLabel#subtitle { color:%(muted)s; }
QLabel#warningBanner { background:%(warning_bg)s; color:%(warning)s; padding:8px; font-weight:bold; }
QLabel#warningText { color:%(warning)s; }
QLabel#errorText { color:%(error)s; }
QLabel#etaText { color:%(link)s; font-weight:600; }
QTabWidget::pane { border:1px solid %(border)s; border-radius:8px; background:%(panel)s; }
QTabBar::tab { padding:12px 20px; background:%(tab)s; color:%(text)s; }
QTabBar::tab:selected { background:%(panel)s; color:%(link)s; font-weight:bold; }
QTabBar::tab:hover { background:%(hover)s; }
QGroupBox { border:1px solid %(border)s; border-radius:8px; margin-top:18px; padding:16px; font-weight:600; }
QGroupBox::title { subcontrol-origin:margin; left:14px; padding:0 5px; }
QLineEdit, QDateEdit, QComboBox, QSpinBox, QDoubleSpinBox, QPlainTextEdit, QListWidget, QTextBrowser, QTableView, QTreeView {
 background:%(panel)s; color:%(text)s; border:1px solid %(border)s; border-radius:5px; padding:6px;
 selection-background-color:%(selection)s; selection-color:%(selection_text)s; alternate-background-color:%(alternate)s;
}
QAbstractItemView { background:%(panel)s; color:%(text)s; selection-background-color:%(selection)s; selection-color:%(selection_text)s; alternate-background-color:%(alternate)s; }
QAbstractItemView::item:selected { background:%(selection)s; color:%(selection_text)s; }
QHeaderView::section, QTableCornerButton::section { background:%(tab)s; color:%(text)s; border:1px solid %(grid)s; padding:7px; }
QPushButton, QToolButton { background:%(button)s; color:%(text)s; border:1px solid transparent; border-radius:6px; padding:9px 15px; }
QPushButton:hover, QToolButton:hover { background:%(hover)s; }
QPushButton#primary { background:%(accent)s; color:%(accent_text)s; font-weight:bold; }
QPushButton:disabled, QToolButton:disabled { background:%(disabled_bg)s; color:%(disabled)s; }
QLineEdit:disabled, QDateEdit:disabled, QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled { background:%(disabled_bg)s; color:%(disabled)s; }
QCheckBox { spacing:8px; padding:3px; }
QCheckBox:disabled { color:%(disabled)s; }
QCheckBox::indicator, QAbstractItemView::indicator { width:24px; height:24px; border:2px solid %(border)s; border-radius:4px; background:%(panel)s; }
QCheckBox::indicator:checked, QAbstractItemView::indicator:checked { background:%(accent)s; border-color:%(link)s; }
QCheckBox::indicator:unchecked:hover, QAbstractItemView::indicator:unchecked:hover { background:%(hover)s; border-color:%(link)s; }
QCheckBox::indicator:disabled, QAbstractItemView::indicator:disabled { border-color:%(disabled)s; background:%(disabled_bg)s; }
QCheckBox::indicator:checked:disabled, QAbstractItemView::indicator:checked:disabled { background:%(accent)s; border-color:%(disabled)s; }
QCheckBox:focus, QPushButton:focus, QToolButton:focus { border:1px dashed %(link)s; border-radius:4px; }
QLineEdit:focus, QDateEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus { border:1px solid %(link)s; }
QProgressBar { border:1px solid %(border)s; border-radius:5px; background:%(tab)s; color:%(text)s; text-align:center; }
QProgressBar::chunk { background:%(accent)s; border-radius:4px; }
QMenu { background:%(panel)s; color:%(text)s; border:1px solid %(border)s; padding:4px; }
QMenu::item { padding:7px 18px; background:transparent; }
QMenu::item:selected { background:%(selection)s; color:%(selection_text)s; }
QMenu::item:disabled { color:%(disabled)s; }
QToolTip { background:%(panel)s; color:%(text)s; border:1px solid %(border)s; padding:6px; }
QScrollBar { background:%(bg)s; }
QScrollBar::handle { background:%(border)s; border-radius:4px; min-height:24px; min-width:24px; }
QSplitter::handle { background:%(grid)s; }
QCalendarWidget QToolButton { background:%(button)s; color:%(text)s; }
''' % c


def apply_theme(app,mode,tick_style=''):
    app.setPalette(palette(mode))
    app.setStyleSheet(stylesheet(mode)+tick_style)

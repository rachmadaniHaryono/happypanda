"""sort menu."""
import functools
import logging

from PyQt5.QtCore import (
    pyqtSignal,
    Qt,
)
from PyQt5.QtWidgets import (
    QAction,
    QActionGroup,
    QMenu,
)

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class SortMenu(QMenu):
    """SortMenu."""

    new_sort = pyqtSignal(str)

    def __init__(self, app_inst, parent=None):
        """__init__."""
        super().__init__(parent)
        self.parent_widget = app_inst

        self.sort_actions = QActionGroup(self, exclusive=True)
        asc_desc_act = QAction("Asc/Desc", self)
        asc_desc_act.triggered.connect(self.asc_desc)
        s_title = self.sort_actions.addAction(
            QAction("Title", self.sort_actions, checkable=True))
        s_title.triggered.connect(
            functools.partial(self.new_sort.emit, 'title'))
        s_artist = self.sort_actions.addAction(
            QAction("Author", self.sort_actions, checkable=True))
        s_artist.triggered.connect(
            functools.partial(self.new_sort.emit, 'artist'))
        s_date = self.sort_actions.addAction(
            QAction("Date Added", self.sort_actions, checkable=True))
        s_date.triggered.connect(functools.partial(
            self.new_sort.emit, 'date_added'))
        s_pub_d = self.sort_actions.addAction(
            QAction("Date Published", self.sort_actions, checkable=True))
        s_pub_d.triggered.connect(
            functools.partial(self.new_sort.emit, 'pub_date'))
        s_times_read = self.sort_actions.addAction(
            QAction("Read Count", self.sort_actions, checkable=True))
        s_times_read.triggered.connect(
            functools.partial(self.new_sort.emit, 'times_read'))
        s_last_read = self.sort_actions.addAction(
            QAction("Last Read", self.sort_actions, checkable=True))
        s_last_read.triggered.connect(
            functools.partial(self.new_sort.emit, 'last_read'))

        self.addAction(asc_desc_act)
        self.addSeparator()
        self.addAction(s_title)
        self.addAction(s_artist)
        self.addAction(s_date)
        self.addAction(s_pub_d)
        self.addAction(s_times_read)
        self.addAction(s_last_read)

        self.set_current_sort()

    def set_current_sort(self):
        """set_current_sort."""
        def check_key(act, key):
            if self.parent_widget.current_manga_view.list_view.current_sort == key:
                act.setChecked(True)

        for act in self.sort_actions.actions():
            if act.text() == 'Title':
                check_key(act, 'title')
            elif act.text() == 'Artist':
                check_key(act, 'artist')
            elif act.text() == 'Date Added':
                check_key(act, 'date_added')
            elif act.text() == 'Date Published':
                check_key(act, 'pub_date')
            elif act.text() == 'Read Count':
                check_key(act, 'times_read')
            elif act.text() == 'Last Read':
                check_key(act, 'last_read')

    def asc_desc(self):
        """asc_desc."""
        if self.parent_widget.current_manga_view.sort_model.sortOrder() == Qt.AscendingOrder:
            self.parent_widget.current_manga_view.sort_model.sort(
                0, Qt.DescendingOrder)
        else:
            self.parent_widget.current_manga_view.sort_model.sort(
                0, Qt.AscendingOrder)

    def showEvent(self, event):  # NOQA
        """showEvent."""
        self.set_current_sort()
        super().showEvent(event)

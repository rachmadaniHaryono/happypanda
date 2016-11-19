"""manga table view."""
import logging

from PyQt5.QtCore import (
    pyqtSignal,
    QSize,
    Qt,
)
from PyQt5.QtGui import (
    QColor,
)
from PyQt5.QtWidgets import (
    QHeaderView,
    QScroller,
    QTableView,
)
try:
    from common_view import CommonView
except ImportError:
    from .common_view import CommonView

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class MangaTableView(QTableView):
    """manga table view."""

    STATUS_BAR_MSG = pyqtSignal(str)

    def __init__(self, v_type, parent=None):
        """init func."""
        super().__init__(parent)
        self.view_type = v_type

        # options
        self.parent_widget = parent
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.viewport().setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(self.DragDrop)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setSelectionBehavior(self.SelectRows)
        self.setSelectionMode(self.ExtendedSelection)
        self.setShowGrid(True)
        self.setSortingEnabled(True)
        h_header = self.horizontalHeader()
        h_header.setSortIndicatorShown(True)
        v_header = self.verticalHeader()
        v_header.sectionResizeMode(QHeaderView.Fixed)
        v_header.setDefaultSectionSize(24)
        v_header.hide()
        palette = self.palette()
        palette.setColor(palette.Highlight, QColor(88, 88, 88, 70))
        palette.setColor(palette.HighlightedText, QColor('black'))
        self.setPalette(palette)
        self.setIconSize(QSize(0, 0))
        self.doubleClicked.connect(lambda idx: idx.data(Qt.UserRole + 1).chapters[0].open())
        self.grabGesture(Qt.SwipeGesture)
        self.k_scroller = QScroller.scroller(self)

    # display tooltip only for elided text
    # def viewportEvent(self, event):
    #   if event.type() == QEvent.ToolTip:
    #       h_event = QHelpEvent(event)
    #       index = self.indexAt(h_event.pos())
    #       if index.isValid():
    #           size_hint = self.itemDelegate(index).sizeHint(self.viewOptions(),
    #                                             index)
    #           rect = QRect(0, 0, size_hint.width(), size_hint.height())
    #           rect_visual = self.visualRect(index)
    #           if rect.width() <= rect_visual.width():
    #               QToolTip.hideText()
    #               return True
    #   return super().viewportEvent(event)

    def keyPressEvent(self, event):
        """keypress event."""
        if event.key() == Qt.Key_Return:
            s_idx = self.selectionModel().selectedRows()
            if s_idx:
                for idx in s_idx:
                    self.doubleClicked.emit(idx)
        elif event.modifiers() == Qt.ShiftModifier and event.key() == Qt.Key_Delete:
            CommonView.remove_selected(self, True)
        elif event.key() == Qt.Key_Delete:
            CommonView.remove_selected(self)
        return super().keyPressEvent(event)

    def contextMenuEvent(self, event):
        """context menu event."""
        CommonView.contextMenuEvent(self, event)

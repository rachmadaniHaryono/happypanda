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
    from misc import (
        handle_keypress_event_on_manga_view,
        open_idx_data_first_chapter_when_double_clicked,
    )
except ImportError:
    from .common_view import CommonView
    from .misc import (
        handle_keypress_event_on_manga_view,
        open_idx_data_first_chapter_when_double_clicked,
    )

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
        self.doubleClicked.connect(open_idx_data_first_chapter_when_double_clicked)
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
        handle_keypress_event_on_manga_view(
            view_obj=self, event=event, selected_idx=self.selectionModel().selectedRows())
        return super().keyPressEvent(event)

    def contextMenuEvent(self, event):
        """context menu event."""
        CommonView.contextMenuEvent(self, event)

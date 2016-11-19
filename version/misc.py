"""misc module."""
# """
# This file is part of Happypanda.
# Happypanda is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# any later version.
# Happypanda is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with Happypanda.  If not, see <http://www.gnu.org/licenses/>.
# """
import functools
import logging
import math
import os
import scandir
import threading
import time

from PyQt5.QtCore import (
    pyqtSignal,
    QByteArray,
    QFileInfo,
    QPoint,
    QPointF,
    QPropertyAnimation,
    QRect,
    QRectF,
    QSize,
    QSizeF,
    Qt,
    QTimer,
)
from PyQt5.QtGui import (
    QBrush,
    QColor,
    QCursor,
    QFont,
    QFontMetrics,
    QIcon,
    QPainter,
    QPaintEvent,
    QPalette,
    QPen,
    QPixmap,
    QPolygonF,
    QTextCursor,
    QTextLayout,
    QTextOption,
)
from PyQt5.QtWidgets import (
    QAction,
    QActionGroup,
    QCommonStyle,
    QCompleter,
    QDesktopWidget,
    QDialog,
    QFileIconProvider,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QListWidget,
    QMenu,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedLayout,
    QStyleOption,
    QSystemTrayIcon,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

try:
    from utils import (
        ARCHIVE_FILES,
        ArchiveFile,
        IMG_FILES
    )
    from custom_list_item import CustomListItem
    from line_frame import LineFrame
    import app_constants
    import gallerydb
    import utils
except ImportError:
    from .utils import (
        ARCHIVE_FILES,
        ArchiveFile,
        IMG_FILES
    )
    from .custom_list_item import CustomListItem
    from .line_frame import LineFrame
    from . import (
        app_constants,
        gallerydb,
        utils,
    )

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


def text_layout(text, width, font, font_metrics, alignment=Qt.AlignCenter):
    """Lay out wrapped text."""
    text_option = QTextOption(alignment)
    text_option.setUseDesignMetrics(True)
    text_option.setWrapMode(QTextOption.WordWrap)
    layout = QTextLayout(text, font)
    layout.setTextOption(text_option)
    leading = font_metrics.leading()
    height = 0
    layout.setCacheEnabled(True)
    layout.beginLayout()
    while True:
        line = layout.createLine()
        if not line.isValid():
            break
        line.setLineWidth(width)
        height += leading
        line.setPosition(QPointF(0, height))
        height += line.height()
    layout.endLayout()
    return layout


def centerWidget(widget, parent_widget=None):
    """centerWidget."""
    if parent_widget:
        r = parent_widget.rect()
    else:
        r = QDesktopWidget().availableGeometry()

    widget.setGeometry(QCommonStyle.alignedRect(
        Qt.LeftToRight, Qt.AlignCenter, widget.size(), r))


def clearLayout(layout):  # NOQA
    """clearLayout."""
    if layout is not None:
        while layout.count():
            child = layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()
            elif child.layout() is not None:
                clearLayout(child.layout())


def create_animation(parent, prop):
    """create_animation."""
    p_array = QByteArray().append(prop)
    return QPropertyAnimation(parent, p_array)


class ElidedLabel(QLabel):
    """ElidedLabel."""

    def __init__(self, *args, **kwargs):
        """init func."""
        super().__init__(*args, **kwargs)

    def paintEvent(self, event):  # NOQA
        """paintEvent."""
        painter = QPainter(self)
        metrics = QFontMetrics(self.font())
        elided = metrics.elidedText(self.text(), Qt.ElideRight, self.width())
        painter.drawText(self.rect(), self.alignment(), elided)


class BaseMoveWidget(QWidget):
    """BaseMoveWidget."""

    def __init__(self, parent=None, **kwargs):
        """__init__."""
        move_listener = kwargs.pop('move_listener', True)
        super().__init__(parent, **kwargs)
        self.parent_widget = parent
        self.setAttribute(Qt.WA_DeleteOnClose)
        if parent and move_listener:
            try:
                parent.move_listener.connect(self.update_move)
            except AttributeError:
                pass

    def update_move(self, new_size=None):
        """update_move."""
        if new_size:
            self.move(new_size)
            return
        if self.parent_widget:
            self.move(
                self.parent_widget.window().frameGeometry().center() -
                self.window().rect().center())


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


class ToolbarButton(QPushButton):
    """ToolbarButton."""

    select = pyqtSignal(object)
    close_tab = pyqtSignal(object)

    def __init__(self, parent=None, txt=''):
        """__init__."""
        super().__init__(parent)
        self._text = txt
        self._font_metrics = self.fontMetrics()
        if txt:
            self.setText(txt)
        self._selected = False
        self.clicked.connect(lambda: self.select.emit(self))
        self._enable_contextmenu = True

    @property
    def selected(self):
        """selected."""
        return self._selected

    @selected.setter
    def selected(self, b):
        """selected."""
        self._selected = b
        self.update()

    def contextMenuEvent(self, event):  # NOQA
        """contextMenuEvent."""
        if self._enable_contextmenu:
            m = QMenu(self)
            m.addAction("Close Tab").triggered.connect(
                lambda: self.close_tab.emit(self))
            m.exec_(event.globalPos())
            event.accept()
        else:
            event.ignore()

    def paintEvent(self, event):  # NOQA
        """paintEvent."""
        assert isinstance(event, QPaintEvent)
        painter = QPainter(self)
        opt = QStyleOption()
        opt.initFrom(self)
        # self.style().drawPrimitive(self.style().PE_FrameButtonTool, opt, painter, self)

        # painter.setPen(QColor(164,164,164,120))
        # painter.setBrush(Qt.NoBrush)
        if self._selected:
            painter.setPen(QColor("#d64933"))
        # painter.setPen(Qt.NoPen)
        painter.setRenderHint(painter.Antialiasing)
        ch_width = self._font_metrics.averageCharWidth() / 4
        ch_height = self._font_metrics.height()
        but_rect = QRectF(
            ch_width, ch_width, self.width() - ch_width * 2, self.height() - ch_width * 2)
        select_rect = QRectF(0, 0, self.width(), self.height())

        painter.drawRoundedRect(but_rect, ch_width, ch_width)
        txt_to_draw = self._font_metrics.elidedText(
            self._text, Qt.ElideRight, but_rect.width())

        but_center = (but_rect.height() - ch_height) / 2
        text_rect = QRectF(
            but_rect.x() + ch_width * 2,
            but_rect.y() + but_center, but_rect.width(), but_rect.height())
        # painter.setPen(QColor('white'))
        painter.drawText(text_rect, txt_to_draw)

        if self.underMouse():
            painter.save()
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(164, 164, 164, 90)))
            painter.drawRoundedRect(select_rect, 2, 2)
            painter.restore()

    def setText(self, txt):  # NOQA
        """setText."""
        self._text = txt
        self.update()
        super().setText(txt)

    def text(self):
        """text."""
        return self._text


class TransparentWidget(BaseMoveWidget):
    """TransparentWidget."""

    def __init__(self, parent=None, **kwargs):
        """__init__."""
        super().__init__(parent, **kwargs)
        self.setAttribute(Qt.WA_TranslucentBackground)


class ArrowWindow(TransparentWidget):
    """ArrowWindow."""

    LEFT, RIGHT, TOP, BOTTOM = range(4)

    def __init__(self, parent):
        """__init__."""
        super().__init__(parent, flags=Qt.Window |
                         Qt.FramelessWindowHint, move_listener=False)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.resize(550, 300)
        self.direction = self.LEFT
        self._arrow_size = QSizeF(30, 30)
        self.content_margin = 0

    @property
    def arrow_size(self):
        """arrow_size."""
        return self._arrow_size

    @arrow_size.setter
    def arrow_size(self, w_h_tuple):
        """arrow_size."""
        "a tuple of width and height"
        if not isinstance(w_h_tuple, (tuple, list)) or len(w_h_tuple) != 2:
            return

        if self.direction in (self.LEFT, self.RIGHT):
            s = QSizeF(w_h_tuple[1], w_h_tuple[0])
        else:
            s = QSizeF(w_h_tuple[0], w_h_tuple[1])

        self._arrow_size = s
        self.update()

    def paintEvent(self, event):  # NOQA
        """paintEvent."""
        assert isinstance(event, QPaintEvent)

        opt = QStyleOption()
        opt.initFrom(self)

        painter = QPainter(self)
        painter.setRenderHint(painter.Antialiasing)

        size = self.size()
        if self.direction in (self.LEFT, self.RIGHT):
            actual_size = QSizeF(
                size.width() - self.arrow_size.width(), size.height())
        else:
            actual_size = QSizeF(
                size.width(), size.height() - self.arrow_size.height())

        starting_point = QPointF(0, 0)
        if self.direction == self.LEFT:
            starting_point = QPointF(self.arrow_size.width(), 0)
        elif self.direction == self.TOP:
            starting_point = QPointF(0, self.arrow_size.height())

        # painter.save()
        # painter.translate(starting_point)
        self.style().drawPrimitive(QCommonStyle.PE_Widget, opt, painter, self)
        # painter.restore()
        painter.setBrush(QBrush(painter.pen().color()))

        # draw background
        # background_rect = QRectF(starting_point, actual_size)
        QRectF(starting_point, actual_size)
        # painter.drawRoundedRect(background_rect, 5, 5)

        # calculate the arrow
        arrow_points = []
        if self.direction == self.LEFT:
            middle_point = QPointF(0, actual_size.height() / 2)
            arrow_1 = QPointF(
                self.arrow_size.width(), middle_point.y() - self.arrow_size.height() / 2)
            arrow_2 = QPointF(
                self.arrow_size.width(), middle_point.y() + self.arrow_size.height() / 2)
            arrow_points.append(arrow_1)
            arrow_points.append(middle_point)
            arrow_points.append(arrow_2)
        elif self.direction == self.RIGHT:
            middle_point = QPointF(
                actual_size.width() + self.arrow_size.width(), actual_size.height() / 2)
            arrow_1 = QPointF(actual_size.width(),
                              middle_point.y() + self.arrow_size.height() / 2)
            arrow_2 = QPointF(actual_size.width(),
                              middle_point.y() - self.arrow_size.height() / 2)
            arrow_points.append(arrow_1)
            arrow_points.append(middle_point)
            arrow_points.append(arrow_2)
        elif self.direction == self.TOP:
            middle_point = QPointF(actual_size.width() / 2, 0)
            arrow_1 = QPointF(
                actual_size.width() / 2 + self.arrow_size.width() / 2, self.arrow_size.height())
            arrow_2 = QPointF(
                actual_size.width() / 2 - self.arrow_size.width() / 2, self.arrow_size.height())
            arrow_points.append(arrow_1)
            arrow_points.append(middle_point)
            arrow_points.append(arrow_2)
        elif self.direction == self.BOTTOM:
            middle_point = QPointF(
                actual_size.width() / 2, actual_size.height() + self.arrow_size.height())
            arrow_1 = QPointF(
                actual_size.width() / 2 - self.arrow_size.width() / 2, actual_size.height())
            arrow_2 = QPointF(
                actual_size.width() / 2 + self.arrow_size.width() / 2, actual_size.height())
            arrow_points.append(arrow_1)
            arrow_points.append(middle_point)
            arrow_points.append(arrow_2)

        # draw it!
        painter.drawPolygon(QPolygonF(arrow_points))


class GalleryMetaWindow(ArrowWindow):
    """GalleryMetaWindow."""

    def __init__(self, parent):
        """__init__."""
        super().__init__(parent)
        # gallery data stuff

        self.content_margin = 10
        self.current_gallery = None
        self.g_widget = self.GalleryLayout(self, parent)
        self.hide_timer = QTimer()
        self.hide_timer.timeout.connect(self.delayed_hide)
        self.hide_timer.setSingleShot(True)
        self.hide_animation = create_animation(self, 'windowOpacity')
        self.hide_animation.setDuration(250)
        self.hide_animation.setStartValue(1.0)
        self.hide_animation.setEndValue(0.0)
        self.hide_animation.finished.connect(self.hide)
        self.show_animation = create_animation(self, 'windowOpacity')
        self.show_animation.setDuration(350)
        self.show_animation.setStartValue(0.0)
        self.show_animation.setEndValue(1.0)
        self.setFocusPolicy(Qt.NoFocus)

    def show(self):
        """show."""
        if not self.hide_animation.Running:
            self.setWindowOpacity(0)
            super().show()
            self.show_animation.start()
        else:
            self.hide_animation.stop()
            super().show()
            self.show_animation.setStartValue(self.windowOpacity())
            self.show_animation.start()

    def focusOutEvent(self, event):
        """focusOutEvent."""
        self.delayed_hide()
        return super().focusOutEvent(event)

    def _mouse_in_gallery(self):
        """_mouse_in_gallery."""
        mouse_p = QCursor.pos()
        h = self.idx_top_l.x() <= mouse_p.x() <= self.idx_top_r.x()
        v = self.idx_top_l.y() <= mouse_p.y() <= self.idx_btm_l.y()
        if h and v:
            return True
        return False

    def mouseMoveEvent(self, event):
        """mouseMoveEvent."""
        if self.isVisible():
            if not self._mouse_in_gallery():
                if not self.hide_timer.isActive():
                    self.hide_timer.start(300)
        return super().mouseMoveEvent(event)

    def delayed_hide(self):
        """delayed_hide."""
        if not self.underMouse() and not self._mouse_in_gallery():
            self.hide_animation.start()

    def show_gallery(self, index, view):  # NOQA
        """show_gallery."""
        self.resize(app_constants.POPUP_WIDTH, app_constants.POPUP_HEIGHT)
        self.view = view
        desktop_w = QDesktopWidget().width()
        desktop_h = QDesktopWidget().height()

        margin_offset = 20  # should be higher than gallery_touch_offset
        gallery_touch_offset = 10  # How far away the window is from touching gallery

        index_rect = view.visualRect(index)
        self.idx_top_l = index_top_left = view.mapToGlobal(
            index_rect.topLeft())
        self.idx_top_r = index_top_right = view.mapToGlobal(
            index_rect.topRight())
        self.idx_btm_l = index_btm_left = view.mapToGlobal(
            index_rect.bottomLeft())
        index_btm_right = view.mapToGlobal(index_rect.bottomRight())

        if app_constants.DEBUG:
            for idx in (index_top_left, index_top_right, index_btm_left, index_btm_right):
                print(idx.x(), idx.y())

        # adjust placement

        def check_left():
            """check_left."""
            middle = (
                index_top_left.y() + index_btm_left.y()) / 2  # middle of gallery left side
            left = (
                index_top_left.x() - self.width() - margin_offset) > 0  # if the width can be there
            # if the top half of window can be there
            top = (middle - (self.height() / 2) - margin_offset) > 0
            # same as above, just for the bottom
            btm = (middle + (self.height() / 2) + margin_offset) < desktop_h
            if left and top and btm:
                self.direction = self.RIGHT
                x = index_top_left.x() - gallery_touch_offset - self.width()
                y = middle - (self.height() / 2)
                appear_point = QPoint(int(x), int(y))
                self.move(appear_point)
                return True
            return False

        def check_right():
            """check_right."""
            middle = (
                index_top_right.y() + index_btm_right.y()) / 2  # middle of gallery right side
            # if the width can be there
            right = (index_top_right.x() + self.width() +
                     margin_offset) < desktop_w
            # if the top half of window can be there
            top = (middle - (self.height() / 2) - margin_offset) > 0
            # same as above, just for the bottom
            btm = (middle + (self.height() / 2) + margin_offset) < desktop_h

            if right and top and btm:
                self.direction = self.LEFT
                x = index_top_right.x() + gallery_touch_offset
                y = middle - (self.height() / 2)
                appear_point = QPoint(int(x), int(y))
                self.move(appear_point)
                return True
            return False

        def check_top():
            """check_top."""
            # middle of gallery top side
            middle = (index_top_left.x() + index_top_right.x()) / 2
            # if the height can be there
            top = (index_top_right.y() - self.height() - margin_offset) > 0
            # if the left half of window can be there
            left = (middle - (self.width() / 2) - margin_offset) > 0
            # same as above, just for the right
            right = (middle + (self.width() / 2) + margin_offset) < desktop_w

            if top and left and right:
                self.direction = self.BOTTOM
                x = middle - (self.width() / 2)
                y = index_top_left.y() - gallery_touch_offset - self.height()
                appear_point = QPoint(int(x), int(y))
                self.move(appear_point)
                return True
            return False

        def check_bottom(override=False):
            """check_bottom."""
            # middle of gallery bottom side
            middle = (index_btm_left.x() + index_btm_right.x()) / 2
            # if the height can be there
            btm = (index_btm_right.y() + self.height() +
                   margin_offset) < desktop_h
            # if the left half of window can be there
            left = (middle - (self.width() / 2) - margin_offset) > 0
            # same as above, just for the right
            right = (middle + (self.width() / 2) + margin_offset) < desktop_w

            if (btm and left and right) or override:
                self.direction = self.TOP
                x = middle - (self.width() / 2)
                y = index_btm_left.y() + gallery_touch_offset
                appear_point = QPoint(int(x), int(y))
                self.move(appear_point)
                return True
            return False

        for pos in (check_bottom, check_right, check_left, check_top):
            if pos():
                break
        else:  # default pos is bottom
            check_bottom(True)

        self._set_gallery(index.data(Qt.UserRole + 1))
        self.show()

    def closeEvent(self, ev):
        """closeEvent."""
        ev.ignore()
        self.delayed_hide()

    def _set_gallery(self, gallery):
        """_set_gallery."""
        self.current_gallery = gallery
        self.g_widget.apply_gallery(gallery)
        self.g_widget.resize(
            self.width() - self.content_margin, self.height() - self.content_margin)
        if self.direction == self.LEFT:
            start_point = QPoint(self.arrow_size.width(), 0)
        elif self.direction == self.TOP:
            start_point = QPoint(0, self.arrow_size.height())
        else:
            start_point = QPoint(0, 0)
        # title
        # title_region = QRegion(0, 0, self.g_title_lbl.width(),
        # self.g_title_lbl.height())
        self.g_widget.move(start_point)

    class GalleryLayout(QFrame):
        """GalleryLayout."""

        class ChapterList(QTableWidget):
            """ChapterList."""

            def __init__(self, parent):
                """__init__."""
                super().__init__(parent)
                self.setColumnCount(3)
                self.setEditTriggers(self.NoEditTriggers)
                self.setFocusPolicy(Qt.NoFocus)
                self.verticalHeader().setSectionResizeMode(
                    self.verticalHeader().ResizeToContents)
                self.horizontalHeader().setSectionResizeMode(
                    0, self.horizontalHeader().ResizeToContents)
                self.horizontalHeader().setSectionResizeMode(
                    1, self.horizontalHeader().Stretch)
                self.horizontalHeader().setSectionResizeMode(
                    2, self.horizontalHeader().ResizeToContents)
                self.horizontalHeader().hide()
                self.verticalHeader().hide()
                self.setSelectionMode(self.SingleSelection)
                self.setSelectionBehavior(self.SelectRows)
                self.setShowGrid(False)
                self.viewport().setBackgroundRole(self.palette().Dark)
                palette = self.viewport().palette()
                palette.setColor(palette.Highlight, QColor(88, 88, 88, 70))
                palette.setColor(palette.HighlightedText, QColor('black'))
                self.viewport().setPalette(palette)
                self.setWordWrap(False)
                self.setTextElideMode(Qt.ElideRight)
                self.doubleClicked.connect(
                    lambda idx: self._get_chap(idx).open())

            def set_chapters(self, chapter_container):
                """set_chapters."""
                for r in range(self.rowCount()):
                    self.removeRow(0)

                def t_item(txt=''):
                    """t_item."""
                    t = QTableWidgetItem(txt)
                    t.setBackground(QBrush(QColor('#585858')))
                    return t

                for chap in chapter_container:
                    c_row = self.rowCount() + 1
                    self.setRowCount(c_row)
                    c_row -= 1
                    n = t_item()
                    n.setData(Qt.DisplayRole, chap.number + 1)
                    n.setData(Qt.UserRole + 1, chap)
                    self.setItem(c_row, 0, n)
                    title = chap.title
                    if not title:
                        title = chap.gallery.title
                    t = t_item(title)
                    self.setItem(c_row, 1, t)
                    p = t_item(str(chap.pages))
                    self.setItem(c_row, 2, p)
                self.sortItems(0)

            def _get_chap(self, idx):
                """_get_chap."""
                r = idx.row()
                t = self.item(r, 0)
                return t.data(Qt.UserRole + 1)

            def contextMenuEvent(self, event):
                """contextMenuEvent."""
                idx = self.indexAt(event.pos())
                if idx.isValid():
                    chap = self._get_chap(idx)
                    menu = QMenu(self)
                    # F841: assigned but never used.
                    # open = menu.addAction('Open', lambda: chap.open())
                    menu.addAction('Open', lambda: chap.open())

                    def open_source():
                        """open_source."""
                        text = 'Opening archive...' if chap.in_archive else 'Opening folder...'
                        app_constants.STAT_MSG_METHOD(text)
                        path = chap.gallery.path if chap.in_archive else chap.path
                        utils.open_path(path)
                    t = "Open archive" if chap.in_archive else "Open folder"
                    # F841: assigned but never used.
                    # open_path = menu.addAction(t, open_source)
                    menu.addAction(t, open_source)
                    menu.exec_(event.globalPos())
                    event.accept()
                    del menu
                else:
                    event.ignore()

        def __init__(self, parent, appwindow):
            """__init__."""
            super().__init__(parent)
            self.appwindow = appwindow
            self.setStyleSheet('color:white;')
            main_layout = QHBoxLayout(self)
            self.stacked_l = stacked_l = QStackedLayout()
            general_info = QWidget(self)
            chapter_info = QWidget(self)
            chapter_layout = QVBoxLayout(chapter_info)
            self.general_index = stacked_l.addWidget(general_info)
            self.chap_index = stacked_l.addWidget(chapter_info)
            self.chapter_list = self.ChapterList(self)
            back_btn = TagText('Back')
            back_btn.clicked.connect(
                lambda: stacked_l.setCurrentIndex(self.general_index))
            chapter_layout.addWidget(back_btn, 0, Qt.AlignCenter)
            chapter_layout.addWidget(self.chapter_list)
            self.left_layout = QFormLayout()
            self.main_left_layout = QVBoxLayout(general_info)
            self.main_left_layout.addLayout(self.left_layout)
            self.right_layout = QFormLayout()
            main_layout.addLayout(stacked_l, 1)
            main_layout.addWidget(LineFrame('v'))
            main_layout.addLayout(self.right_layout)

            def get_label(txt):
                """get_label."""
                lbl = QLabel(txt)
                lbl.setWordWrap(True)
                return lbl
            self.g_title_lbl = get_label('')
            self.g_title_lbl.setStyleSheet('color:white;font-weight:bold;')
            self.left_layout.addRow(self.g_title_lbl)
            self.g_artist_lbl = ClickedLabel()
            self.g_artist_lbl.setWordWrap(True)
            self.g_artist_lbl.clicked.connect(
                lambda a: appwindow.search("artist:{}".format(a)))
            self.g_artist_lbl.setStyleSheet('color:#bdc3c7;')
            self.g_artist_lbl.setToolTip("Click to see more from this artist")
            self.left_layout.addRow(self.g_artist_lbl)
            for lbl in (self.g_title_lbl, self.g_artist_lbl):
                lbl.setAlignment(Qt.AlignCenter)
            self.left_layout.addRow(LineFrame('h'))

            first_layout = QHBoxLayout()
            self.g_type_lbl = ClickedLabel()
            self.g_type_lbl.setStyleSheet('text-decoration: underline')
            self.g_type_lbl.clicked.connect(
                lambda a: appwindow.search("type:{}".format(a)))
            self.g_lang_lbl = ClickedLabel()
            self.g_lang_lbl.setStyleSheet('text-decoration: underline')
            self.g_lang_lbl.clicked.connect(
                lambda a: appwindow.search("language:{}".format(a)))
            self.g_chapters_lbl = TagText('Chapters')
            self.g_chapters_lbl.clicked.connect(
                lambda: stacked_l.setCurrentIndex(self.chap_index))
            self.g_chap_count_lbl = QLabel()
            self.right_layout.addRow(self.g_type_lbl)
            self.right_layout.addRow(self.g_lang_lbl)
            self.right_layout.addRow(self.g_chap_count_lbl)
            # first_layout.addWidget(self.g_lang_lbl, 0, Qt.AlignLeft)
            first_layout.addWidget(self.g_chapters_lbl, 0, Qt.AlignCenter)
            # first_layout.addWidget(self.g_type_lbl, 0, Qt.AlignRight)
            self.left_layout.addRow(first_layout)

            self.g_status_lbl = QLabel()
            self.g_d_added_lbl = QLabel()
            self.g_pub_lbl = QLabel()
            self.g_last_read_lbl = QLabel()
            self.g_read_count_lbl = QLabel()
            self.g_pages_total_lbl = QLabel()
            self.right_layout.addRow(self.g_read_count_lbl)
            self.right_layout.addRow('Pages:', self.g_pages_total_lbl)
            self.right_layout.addRow('Status:', self.g_status_lbl)
            self.right_layout.addRow('Added:', self.g_d_added_lbl)
            self.right_layout.addRow('Published:', self.g_pub_lbl)
            self.right_layout.addRow('Last read:', self.g_last_read_lbl)

            self.g_info_lbl = get_label('')
            self.left_layout.addRow(self.g_info_lbl)

            self.g_url_lbl = ClickedLabel()
            self.g_url_lbl.clicked.connect(
                lambda: utils.open_web_link(self.g_url_lbl.text()))
            self.g_url_lbl.setWordWrap(True)
            self.left_layout.addRow('URL:', self.g_url_lbl)
            # self.left_layout.addRow(Line('h'))

            self.tags_scroll = QScrollArea(self)
            self.tags_widget = QWidget(self.tags_scroll)
            self.tags_widget.setSizePolicy(
                QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.tags_layout = QFormLayout(self.tags_widget)
            self.tags_layout.setSizeConstraint(self.tags_layout.SetMaximumSize)
            self.tags_scroll.setWidget(self.tags_widget)
            self.tags_scroll.setWidgetResizable(True)
            self.tags_scroll.setFrameShape(QFrame.NoFrame)
            self.main_left_layout.addWidget(self.tags_scroll)

        def has_tags(self, tags):
            """has_tags."""
            t_len = len(tags)
            if not t_len:
                return False
            if t_len == 1:
                if 'default' in tags:
                    if not tags['default']:
                        return False
            return True

        def apply_gallery(self, gallery):
            """apply_gallery."""
            self.stacked_l.setCurrentIndex(self.general_index)
            self.chapter_list.set_chapters(gallery.chapters)
            self.g_title_lbl.setText(gallery.title)
            self.g_artist_lbl.setText(gallery.artist)
            self.g_lang_lbl.setText(gallery.language)
            chap_txt = "chapters" if gallery.chapters.count() > 1 else "chapter"
            self.g_chap_count_lbl.setText(
                '{} {}'.format(gallery.chapters.count(), chap_txt))
            self.g_type_lbl.setText(gallery.type)
            pages = gallery.chapters.pages()
            self.g_pages_total_lbl.setText('{}'.format(pages))
            self.g_status_lbl.setText(gallery.status)
            self.g_d_added_lbl.setText(gallery.date_added.strftime('%d %b %Y'))
            if gallery.pub_date:
                self.g_pub_lbl.setText(gallery.pub_date.strftime('%d %b %Y'))
            else:
                self.g_pub_lbl.setText('Unknown')
            last_read_txt = '{} ago'.format(
                utils.get_date_age(gallery.last_read)) if gallery.last_read else "Never!"
            self.g_last_read_lbl.setText(last_read_txt)
            self.g_read_count_lbl.setText(
                'Read {} times'.format(gallery.times_read))
            self.g_info_lbl.setText(gallery.info)
            if gallery.link:
                self.g_url_lbl.setText(gallery.link)
                self.g_url_lbl.show()
            else:
                self.g_url_lbl.hide()

            clearLayout(self.tags_layout)
            if self.has_tags(gallery.tags):
                ns_layout = QFormLayout()
                self.tags_layout.addRow(ns_layout)
                for namespace in sorted(gallery.tags):
                    tags_lbls = FlowLayout()
                    if namespace == 'default':
                        self.tags_layout.insertRow(0, tags_lbls)
                    else:
                        self.tags_layout.addRow(namespace, tags_lbls)

                    for n, tag in enumerate(sorted(gallery.tags[namespace]), 1):
                        if namespace == 'default':
                            t = TagText(search_widget=self.appwindow)
                        else:
                            t = TagText(search_widget=self.appwindow,
                                        namespace=namespace)
                        t.setText(tag)
                        tags_lbls.addWidget(t)
                        t.setAutoFillBackground(True)
            self.tags_widget.adjustSize()


class Spinner(TransparentWidget):
    """Spinner widget."""
    activated = pyqtSignal()
    deactivated = pyqtSignal()
    about_to_show, about_to_hide = range(2)
    _OFFSET_X_TOPRIGHT = [0]

    def __init__(self, parent, position='topright'):
        """Position can be: 'center', 'topright' or QPoint"""
        super().__init__(parent, flags=Qt.Window |
                         Qt.FramelessWindowHint, move_listener=False)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.fps = 21
        self.border = 2
        self.line_width = 5
        self.arc_length = 100
        self.seconds_per_spin = 1
        self.text_layout = None

        self.text = ''
        self._text_margin = 5

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_timer_timeout)

        # keep track of the current start angle to avoid
        # unnecessary repaints
        self._start_angle = 0

        self._offset_x_topright = self._OFFSET_X_TOPRIGHT[0]
        self.margin = 10
        self._position = position
        self._min_size = 0

        self.state_timer = QTimer()
        self.current_state = self.about_to_show
        self.state_timer.timeout.connect(super().hide)
        self.state_timer.setSingleShot(True)

        # animation
        self.fade_animation = create_animation(self, 'windowOpacity')
        self.fade_animation.setDuration(800)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.setWindowOpacity(0.0)
        self._update_layout()
        self.set_size(50)
        self._set_position(position)

    def _update_layout(self):
        """_update_layout."""
        self.text_layout = text_layout(
            self.text, self.width() - self._text_margin, self.font(), self.fontMetrics())
        self.setFixedHeight(
            self._min_size + self.text_layout.boundingRect().height())

    def set_size(self, w):
        """set_size."""
        self.setFixedWidth(w)
        self._min_size = w
        self._update_layout()
        self.update()

    def set_text(self, txt):
        """set_text."""
        self.text = txt
        self._update_layout()
        self.update()

    def _set_position(self, new_pos):
        """_set_position.

        'center', 'topright' or QPoint"""
        p = self.parent_widget

        # topleft
        if new_pos == "topright":

            def topright():
                return QPoint(
                    p.pos().x() + p.width() - 65 - self._offset_x_topright,
                    p.pos().y() + p.toolbar.height() + 55
                )
            self.move(topright())
            p.move_listener.connect(lambda: self.update_move(topright()))

        elif new_pos == "center":
            p.move_listener.connect(
                lambda: self.update_move(
                    QPoint(p.pos().x() + p.width() // 2,
                           p.pos().y() + p.height() // 2)
                )
            )

        elif isinstance(new_pos, QPoint):
            p.move_listener.connect(lambda: self.update_move(new_pos))

    def paintEvent(self, event):
        """paintEvent."""
        # call the base paint event:
        super().paintEvent(event)

        painter = QPainter()
        painter.begin(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)

            txt_rect = QRectF(0, 0, 0, 0)
            if not self.text:
                txt_rect.setHeight(self.fontMetrics().height())

            painter.save()
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(88, 88, 88, 180)))
            painter.drawRoundedRect(
                QRect(0, 0, self.width(), self.height() - txt_rect.height()), 5, 5)
            painter.restore()

            pen = QPen(QColor('#F2F2F2'))
            pen.setWidth(self.line_width)
            painter.setPen(pen)

            border = self.border + int(math.ceil(self.line_width / 2.0))
            r = QRectF(
                (txt_rect.height()) / 2, (txt_rect.height() /
                                          2), self.width() - txt_rect.height(),
                self.width() - txt_rect.height()
            )
            r.adjust(border, border, -border, -border)

            # draw the arc:
            painter.drawArc(r, -self._start_angle * 16, self.arc_length * 16)

            # draw text if there is
            if self.text:
                txt_rect = self.text_layout.boundingRect()
                self.text_layout.draw(
                    painter,
                    QPointF(
                        self._text_margin,
                        self.height() - txt_rect.height() - self._text_margin / 2
                    )
                )

            r = None

        finally:
            painter.end()
            painter = None

    def showEvent(self, event):
        """showEvent."""
        if self._position == "topright":
            self._OFFSET_X_TOPRIGHT[0] += + self.width() + self.margin
        if not self._timer.isActive():
            self.fade_animation.start()
            self.current_state = self.about_to_show
            self.state_timer.stop()
            self.activated.emit()
            self._timer.start(1000 / max(1, self.fps))
        super().showEvent(event)

    def hideEvent(self, event):
        """hideEvent."""
        self._timer.stop()
        self.deactivated.emit()
        super().hideEvent(event)

    def before_hide(self):
        """before_hide."""
        if self.current_state == self.about_to_hide:
            return
        self.current_state = self.about_to_hide
        if self._position == "topright":
            self._OFFSET_X_TOPRIGHT[0] -= self.width() + self.margin
        self.state_timer.start(5000)

    def closeEvent(self, event):
        """closeEvent."""
        self._timer.stop()
        super().closeEvent(event)

    def _on_timer_timeout(self):
        """_on_timer_timeout."""
        if not self.isVisible():
            return

        # calculate the spin angle as a function of the current time so that all
        # spinners appear in sync!
        t = time.time()
        whole_seconds = int(t)
        p = (whole_seconds % self.seconds_per_spin) + (t - whole_seconds)
        angle = int((360 * p) / self.seconds_per_spin)

        if angle == self._start_angle:
            return

        self._start_angle = angle
        self.update()


class SystemTray(QSystemTrayIcon):
    """SystemTray.

    Pass True to minimized arg in showMessage method to only
    show message if application is minimized.
    """

    def __init__(self, icon, parent=None):
        """__init__."""
        super().__init__(icon, parent=None)
        self.parent_widget = parent

    def showMessage(self, title, msg, icon=QSystemTrayIcon.Information,
                    msecs=10000, minimized=False):
        """showMessage."""
        # NOTE: Crashes on linux
        # TODO: Fix this!!
        if not app_constants.OS_NAME == "linux":
            if minimized:
                if self.parent_widget.isMinimized() or not self.parent_widget.isActiveWindow():
                    return super().showMessage(title, msg, icon, msecs)
            else:
                return super().showMessage(title, msg, icon, msecs)


class ClickedLabel(QLabel):
    """ClickedLabel.

    A QLabel which emits clicked signal on click
    """
    clicked = pyqtSignal(str)

    def __init__(self, s="", **kwargs):
        """__init__."""
        super().__init__(s, **kwargs)
        self.setTextInteractionFlags(
            Qt.LinksAccessibleByMouse | Qt.LinksAccessibleByKeyboard)

    def enterEvent(self, event):
        """enterEvent."""
        if self.text():
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
        return super().enterEvent(event)

    def mousePressEvent(self, event):
        """mousePressEvent."""
        self.clicked.emit(self.text())
        return super().mousePressEvent(event)


class TagText(QPushButton):
    """TagText."""

    def __init__(self, *args, **kwargs):
        """__init__."""
        self.search_widget = kwargs.pop('search_widget', None)
        self.namespace = kwargs.pop('namespace', None)
        super().__init__(*args, **kwargs)
        if self.search_widget:
            if self.namespace:
                self.clicked.connect(lambda: self.search_widget.search(
                    '{}:{}'.format(self.namespace, self.text())))
            else:
                self.clicked.connect(
                    lambda: self.search_widget.search('{}'.format(self.text())))

    def enterEvent(self, event):
        """enterEvent."""
        if self.text():
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
        return super().enterEvent(event)


class BasePopup(TransparentWidget):
    """BasePopup."""

    graphics_blur = None

    def __init__(self, parent=None, **kwargs):
        """__init__."""
        blur = True
        if kwargs:
            blur = kwargs.pop('blur', True)
            super().__init__(parent, **kwargs)
        else:
            super().__init__(parent, flags=Qt.Dialog | Qt.FramelessWindowHint)
        main_layout = QVBoxLayout()
        self.main_widget = QFrame()
        self.main_widget.setFrameStyle(QFrame.StyledPanel)
        self.setLayout(main_layout)
        main_layout.addWidget(self.main_widget)
        self.generic_buttons = QHBoxLayout()
        self.generic_buttons.addWidget(Spacer('h'))
        self.yes_button = QPushButton('Yes')
        self.no_button = QPushButton('No')
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.addWidget(Spacer('h'), 3)
        self.generic_buttons.addWidget(self.yes_button)
        self.generic_buttons.addWidget(self.no_button)
        self.setMaximumWidth(500)
        self.resize(500, 350)
        self.curr_pos = QPoint()
        if parent and blur:
            try:
                self.graphics_blur = parent.graphics_blur
                parent.setGraphicsEffect(self.graphics_blur)
            except AttributeError:
                pass

        # animation
        self.fade_animation = create_animation(self, 'windowOpacity')
        self.fade_animation.setDuration(800)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.setWindowOpacity(0.0)

    def mousePressEvent(self, event):
        """mousePressEvent."""
        self.curr_pos = event.pos()
        return super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """mouseMoveEvent."""
        if event.buttons() == Qt.LeftButton:
            diff = event.pos() - self.curr_pos
            newpos = self.pos() + diff
            self.move(newpos)
        return super().mouseMoveEvent(event)

    def showEvent(self, event):
        """showEvent."""
        self.activateWindow()
        self.fade_animation.start()
        if self.graphics_blur:
            self.graphics_blur.setEnabled(True)
        return super().showEvent(event)

    def closeEvent(self, event):
        """closeEvent."""
        if self.graphics_blur:
            self.graphics_blur.setEnabled(False)
        return super().closeEvent(event)

    def hideEvent(self, event):
        """hideEvent."""
        if self.graphics_blur:
            self.graphics_blur.setEnabled(False)
        return super().hideEvent(event)

    def add_buttons(self, *args):
        """add_buttons.

        Pass names of buttons, from right to left.
        Returns list of buttons in same order as they came in.
        Note: Remember to add buttons_layout to main layout!
        """
        b = []
        for name in args:
            button = QPushButton(name)
            self.buttons_layout.addWidget(button)
            b.append(button)
        return b


class AppBubble(BasePopup):
    """For application notifications."""

    def __init__(self, parent):
        """__init__."""
        super().__init__(parent, flags=Qt.Window | Qt.FramelessWindowHint, blur=False)
        self.hide_timer = QTimer(self)
        self.hide_timer.timeout.connect(self.hide)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        main_layout = QVBoxLayout(self.main_widget)
        self.title = QLabel()
        self.title.setTextFormat(Qt.RichText)
        main_layout.addWidget(self.title)
        self.content = QLabel()
        self.content.setWordWrap(True)
        self.content.setTextFormat(Qt.RichText)
        self.content.setOpenExternalLinks(True)
        main_layout.addWidget(self.content)
        self.adjustSize()

    def update_text(self, title, txt='', duration=20):
        """update_text."""
        "Duration in seconds!"
        if self.hide_timer.isActive():
            self.hide_timer.stop()
        self.title.setText('<h3>{}</h3>'.format(title))
        self.content.setText(txt)
        self.hide_timer.start(duration * 1000)
        self.show()
        self.adjustSize()
        self.update_move()

    def update_move(self):
        """update_move."""
        if self.parent_widget:
            tl = self.parent_widget.geometry().topLeft()
            x = tl.x() + self.parent_widget.width() - self.width() - 10
            y = tl.y() + self.parent_widget.height() - self.height() - \
                self.parent_widget.statusBar().height()
            self.move(x, y)

    def mousePressEvent(self, event):
        """mousePressEvent."""
        if event.button() == Qt.RightButton:
            self.close()
        super().mousePressEvent(event)


class AppDialog(BasePopup):
    """AppDialog."""

    # modes
    PROGRESS, MESSAGE = range(2)
    closing_down = pyqtSignal()

    def __init__(self, parent, mode=PROGRESS):
        """__init__."""
        self.mode = mode
        if mode == self.MESSAGE:
            super().__init__(parent, flags=Qt.Dialog)
        else:
            super().__init__(parent)
        self.parent_widget = parent
        main_layout = QVBoxLayout()

        self.info_lbl = QLabel()
        self.info_lbl.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.info_lbl)
        if mode == self.PROGRESS:
            self.info_lbl.setText(
                "Updating your galleries to newest version...")
            self.info_lbl.setWordWrap(True)

            class progress(QProgressBar):
                """progress."""
                reached_maximum = pyqtSignal()

                def __init__(self, parent=None):
                    """__init__."""
                    super().__init__(parent)

                def setValue(self, v):
                    """setValue."""
                    if v == self.maximum():
                        self.reached_maximum.emit()
                    return super().setValue(v)

            self.prog = progress(self)

            self.prog.reached_maximum.connect(self.close)
            main_layout.addWidget(self.prog)
            self.note_info = QLabel(
                "Note: This popup will close itself when everything is ready")
            self.note_info.setAlignment(Qt.AlignCenter)
            self.restart_info = QLabel(
                "Please wait.. It is safe to restart if there is no sign of progress.")
            self.restart_info.setAlignment(Qt.AlignCenter)
            main_layout.addWidget(self.note_info)
            main_layout.addWidget(self.restart_info)
        elif mode == self.MESSAGE:
            self.info_lbl.setText(
                "<font color='red'>An exception has ben encountered.\n"
                "Contact the developer to get this fixed.\n"
                "Stability from this point onward cannot be guaranteed.</font>"
            )
            self.setWindowTitle("It was too big!")

        self.main_widget.setLayout(main_layout)
        self.adjustSize()

    def closeEvent(self, event):
        """closeEvent."""
        self.parent_widget.setEnabled(True)
        if self.mode == self.MESSAGE:
            self.closing_down.emit()
            return super().closeEvent(event)
        else:
            return super().closeEvent(event)

    def showEvent(self, event):
        """showEvent."""
        self.parent_widget.setEnabled(False)
        return super().showEvent(event)

    def init_restart(self):
        """init_restart."""
        if self.mode == self.PROGRESS:
            self.prog.hide()
            self.note_info.hide()
            self.restart_info.hide()
            log_i('Application requires restart')
            self.note_info.setText("Application requires restart!")


class NotificationOverlay(QWidget):
    """A notifaction bar """

    clicked = pyqtSignal()
    _show_signal = pyqtSignal()
    _hide_signal = pyqtSignal()
    _unset_cursor = pyqtSignal()
    _set_cursor = pyqtSignal(object)

    def __init__(self, parent=None):
        """__init__."""
        super().__init__(parent)
        self._main_layout = QHBoxLayout(self)
        self._default_height = 20
        self._dynamic_height = 0
        self._lbl = QLabel()
        self._main_layout.addWidget(self._lbl)
        self._lbl.setAlignment(Qt.AlignCenter)
        self.setContentsMargins(-10, -10, -10, -10)
        self._click = False
        self._override_hide = False
        self.text_queue = []

        self.slide_animation = create_animation(self, 'minimumHeight')
        self.slide_animation.setDuration(500)
        self.slide_animation.setStartValue(0)
        self.slide_animation.setEndValue(self._default_height)
        self.slide_animation.valueChanged.connect(self.set_dynamic_height)
        self._show_signal.connect(self.show)
        self._hide_signal.connect(self.hide)
        self._unset_cursor.connect(self.unsetCursor)
        self._set_cursor.connect(self.setCursor)

    def set_dynamic_height(self, h):
        """set_dynamic_height."""
        self._dynamic_height = h

    def mousePressEvent(self, event):
        """mousePressEvent."""
        if self._click:
            self.clicked.emit()
        return super().mousePressEvent(event)

    def set_clickable(self, d=True):
        """set_clickable."""
        self._click = d
        self._set_cursor.emit(Qt.PointingHandCursor)

    def resize(self, x, y=0):
        """resize."""
        return super().resize(x, self._dynamic_height)

    def add_text(self, text, autohide=True):
        """add_text.

        Add new text to the bar, deleting the previous one
        """
        try:
            self._reset()
        except TypeError:
            pass
        if not self.isVisible():
            self._show_signal.emit()
        self._lbl.setText(text)
        if autohide:
            if not self._override_hide:
                threading.Timer(10, self._hide_signal.emit).start()

    def begin_show(self):
        """ Control how long you will show notification bar.

        end_show() must be called to hide the bar.
        """
        self._override_hide = True
        self._show_signal.emit()

    def end_show(self):
        """end_show."""
        self._override_hide = False
        QTimer.singleShot(5000, self._hide_signal.emit)

    def _reset(self):
        """_reset."""
        self._unset_cursor.emit()
        self._click = False
        self.clicked.disconnect()

    def showEvent(self, event):
        """showEvent."""
        self.slide_animation.start()
        return super().showEvent(event)


class GalleryShowcaseWidget(QWidget):
    """Pass a gallery or set a gallery via -> set_gallery."""

    double_clicked = pyqtSignal(gallerydb.Gallery)

    def __init__(self, gallery=None, parent=None, menu=None):
        """__init__."""
        super().__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.main_layout = QVBoxLayout(self)
        self.parent_widget = parent
        if menu:
            menu.gallery_widget = self
        self._menu = menu
        self.gallery = gallery
        self.extra_text = QLabel()
        self.profile = QLabel(self)
        self.profile.setAlignment(Qt.AlignCenter)
        self.text = QLabel(self)
        self.font_M = self.text.fontMetrics()
        self.main_layout.addWidget(self.extra_text)
        self.extra_text.hide()
        self.main_layout.addWidget(self.profile)
        self.main_layout.addWidget(self.text)
        self.h = 0
        self.w = 0
        if gallery:
            self.h = 220
            self.w = 143
            self.set_gallery(gallery, (self.w, self.h))

        self.resize(self.w, self.h)
        self.setMouseTracking(True)

    @property
    def menu(self):
        """menu."""
        return self._menu

    @menu.setter
    def contextmenu(self, new_menu):
        """contextmenu."""
        new_menu.gallery_widget = self
        self._menu = new_menu

    def set_pixmap(self, gallery, img):
        """set_pixmap."""
        self.profile.setPixmap(QPixmap.fromImage(img))

    def set_gallery(self, gallery, size=app_constants.THUMB_SMALL):
        """set_gallery."""
        assert isinstance(size, (list, tuple))
        self.w = size[0]
        self.h = size[1]
        self.gallery = gallery
        img = gallery.get_profile(
            app_constants.ProfileType.Small, self.set_pixmap)
        if img:
            self.profile.setPixmap(QPixmap.fromImage(img))
        title = self.font_M.elidedText(gallery.title, Qt.ElideRight, self.w)
        artist = self.font_M.elidedText(gallery.artist, Qt.ElideRight, self.w)
        self.text.setText("{}\n{}".format(title, artist))
        self.setToolTip("{}\n{}".format(gallery.title, gallery.artist))
        self.resize(self.w, self.h + 50)

    def paintEvent(self, event):
        """paintEvent."""
        painter = QPainter(self)
        if self.underMouse():
            painter.setBrush(QBrush(QColor(164, 164, 164, 120)))
            painter.drawRect(
                self.text.pos().x() - 2, self.profile.pos().y() - 5,
                self.text.width() + 2, self.profile.height() + self.text.height() + 12
            )
        super().paintEvent(event)

    def enterEvent(self, event):
        """enterEvent."""
        self.update()
        return super().enterEvent(event)

    def leaveEvent(self, event):
        """leaveEvent."""
        self.update()
        return super().leaveEvent(event)

    def mouseDoubleClickEvent(self, event):
        """mouseDoubleClickEvent."""
        self.double_clicked.emit(self.gallery)
        return super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event):
        """contextMenuEvent."""
        if self._menu:
            self._menu.exec_(event.globalPos())
            event.accept()
        else:
            event.ignore()


class SingleGalleryChoices(BasePopup):
    """SingleGalleryChoices.

    Represent a single gallery with a list of choices below.
    Pass a gallery and a list of tuple/list where the first index is a string in each
    if text is passed, the text will be shown alongside gallery, else gallery be centered
    """
    USER_CHOICE = pyqtSignal(object)

    def __init__(self, gallery, tuple_first_idx, text=None, parent=None):
        """__init__."""
        super().__init__(parent, flags=Qt.Dialog | Qt.FramelessWindowHint)
        main_layout = QVBoxLayout()
        self.main_widget.setLayout(main_layout)
        g_showcase = GalleryShowcaseWidget()
        g_showcase.set_gallery(gallery, (170 // 1.40, 170))
        if text:
            t_layout = QHBoxLayout()
            main_layout.addLayout(t_layout)
            t_layout.addWidget(g_showcase, 1)
            info = QLabel(text)
            info.setWordWrap(True)
            t_layout.addWidget(info)
        else:
            main_layout.addWidget(g_showcase, 0, Qt.AlignCenter)
        self.list_w = QListWidget(self)
        self.list_w.setAlternatingRowColors(True)
        self.list_w.setWordWrap(True)
        self.list_w.setTextElideMode(Qt.ElideNone)
        main_layout.addWidget(self.list_w, 3)
        main_layout.addLayout(self.buttons_layout)
        for t in tuple_first_idx:
            item = CustomListItem(t)
            item.setText(t[0])
            self.list_w.addItem(item)
        self.buttons = self.add_buttons('Skip All', 'Skip', 'Choose',)
        self.buttons[2].clicked.connect(self.finish)
        self.buttons[1].clicked.connect(self.skip)
        self.buttons[0].clicked.connect(self.skipall)
        self.resize(400, 400)
        self.show()

    def finish(self):
        """finish."""
        item = self.list_w.selectedItems()
        if item:
            item = item[0]
            self.USER_CHOICE.emit(item.item)
            self.close()

    def skip(self):
        """skip."""
        self.USER_CHOICE.emit(())
        self.close()

    def skipall(self):
        """skipall."""
        self.USER_CHOICE.emit(None)
        self.close()


class BaseUserChoice(QDialog):
    """BaseUserChoice."""

    USER_CHOICE = pyqtSignal(object)

    def __init__(self, parent, **kwargs):
        """__init__."""
        super().__init__(parent, **kwargs)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setAttribute(Qt.WA_TranslucentBackground)
        main_widget = QFrame(self)
        layout = QVBoxLayout(self)
        layout.addWidget(main_widget)
        self.main_layout = QFormLayout(main_widget)

    def accept(self, choice):
        """accept."""
        self.USER_CHOICE.emit(choice)
        super().accept()


class TorrentItem:
    """TorrentItem."""

    def __init__(self, url, name="", date=None, size=None, seeds=None, peers=None, uploader=None):
        """__init__."""
        self.url = url
        self.name = name
        self.date = date
        self.size = size
        self.seeds = seeds
        self.peers = peers
        self.uploader = uploader


class TorrentUserChoice(BaseUserChoice):
    """TorrentUserChoice."""

    def __init__(self, parent, torrentitems=[], **kwargs):
        """__init__."""
        super().__init__(parent, **kwargs)
        title = QLabel('Torrents')
        title.setAlignment(Qt.AlignCenter)
        self.main_layout.addRow(title)
        self._list_w = QListWidget(self)
        self.main_layout.addRow(self._list_w)
        for t in torrentitems:
            self.add_torrent_item(t)

        btn_layout = QHBoxLayout()
        choose_btn = QPushButton('Choose')
        choose_btn.clicked.connect(self.accept)
        btn_layout.addWidget(Spacer('h'))
        btn_layout.addWidget(choose_btn)
        self.main_layout.addRow(btn_layout)

    def add_torrent_item(self, item):
        """add_torrent_item."""
        list_item = CustomListItem(item)
        list_item.setText("{}\nSeeds:{}\tPeers:{}\tSize:{}\tDate:{}\tUploader:{}".format(
            item.name, item.seeds, item.peers, item.size, item.date, item.uploader))
        self._list_w.addItem(list_item)

    def accept(self):
        """accept."""
        items = self._list_w.selectedItems()
        if items:
            item = items[0]
            super().accept(item.item)


class LoadingOverlay(QWidget):
    """LoadingOverlay."""

    def __init__(self, parent=None):
        """__init__."""
        super().__init__(parent)
        palette = QPalette(self.palette())
        palette.setColor(palette.Background, Qt.transparent)
        self.setPalette(palette)

    def paintEngine(self, event):
        """paintEngine."""
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(event.rect(),
                         QBrush(QColor(255, 255, 255, 127)))
        painter.setPen(QPen(Qt.NoPen))
        for i in range(6):
            if (self.counter / 5) % 6 == i:
                painter.setBrush(
                    QBrush(QColor(127 + (self.counter % 5) * 32, 127, 127)))
            else:
                painter.setBrush(QBrush(QColor(127, 127, 127)))
                painter.drawEllipse(self.width() / 2 + 30 * math.cos(2 * math.pi * i / 6.0) - 10,
                                    self.height() / 2 + 30 * math.sin(2 * math.pi * i / 6.0) - 10,
                                    20, 20)

        painter.end()

    def showEvent(self, event):
        """showEvent."""
        self.timer = self.startTimer(50)
        self.counter = 0
        super().showEvent(event)

    def timerEvent(self, event):
        """timerEvent."""
        self.counter += 1
        self.update()
        if self.counter == 60:
            self.killTimer(self.timer)
            self.hide()


class FileIcon:
    """FileIcon."""

    def __init__(self):
        """__init__."""
        self.ico_types = {}

    def get_file_icon(self, path):
        """get_file_icon."""
        if os.path.isdir(path):
            if 'dir' not in self.ico_types:
                self.ico_types['dir'] = QFileIconProvider().icon(
                    QFileInfo(path))
            return self.ico_types['dir']
        elif path.endswith(utils.ARCHIVE_FILES):
            suff = ''
            for s in utils.ARCHIVE_FILES:
                if path.endswith(s):
                    suff = s
            if suff not in self.ico_types:
                self.ico_types[suff] = QFileIconProvider().icon(
                    QFileInfo(path))
            return self.ico_types[suff]

    @staticmethod
    def get_external_file_icon():
        """get_external_file_icon."""
        if app_constants._REFRESH_EXTERNAL_VIEWER:
            if os.path.exists(app_constants.GALLERY_EXT_ICO_PATH):
                os.remove(app_constants.GALLERY_EXT_ICO_PATH)
            info = QFileInfo(app_constants.EXTERNAL_VIEWER_PATH)
            icon = QFileIconProvider().icon(info)
            pixmap = icon.pixmap(QSize(32, 32))
            pixmap.save(app_constants.GALLERY_EXT_ICO_PATH, quality=100)
            app_constants._REFRESH_EXTERNAL_VIEWER = False

        return QIcon(app_constants.GALLERY_EXT_ICO_PATH)

    @staticmethod  # NOQA
    def refresh_default_icon():
        """refresh_default_icon."""
        if os.path.exists(app_constants.GALLERY_DEF_ICO_PATH):
            os.remove(app_constants.GALLERY_DEF_ICO_PATH)

        def get_file(n):
            """get_file."""
            gallery = gallerydb.GalleryDB.get_gallery_by_id(n)
            if not gallery:
                return False
            file = ""
            if gallery.path.endswith(tuple(ARCHIVE_FILES)):
                try:
                    zip = ArchiveFile(gallery.path)
                except utils.app_constants.CreateArchiveFail:
                    return False
                for name in zip.namelist():
                    if name.lower().endswith(tuple(IMG_FILES)):
                        folder = os.path.join(app_constants.temp_dir,
                                              '{}{}'.format(name, n))
                        zip.extract(name, folder)
                        file = os.path.join(folder, name)
                        break
            else:
                for p in scandir.scandir(gallery.chapters[0].path):
                    if p.name.lower().endswith(tuple(IMG_FILES)):
                        file = p.path
                        break
            return file

        # TODO: fix this!  (When there are no ids below 300?  (because they go
        # deleted))
        for x in range(1, 300):
            try:
                file = get_file(x)
                break
            except FileNotFoundError:  # NOQA
                continue
            except app_constants.CreateArchiveFail:
                continue

        if not file:
            return None
        icon = QFileIconProvider().icon(QFileInfo(file))
        pixmap = icon.pixmap(QSize(32, 32))
        pixmap.save(app_constants.GALLERY_DEF_ICO_PATH, quality=100)
        return True

    @staticmethod
    def get_default_file_icon():
        """get_default_file_icon."""
        s = True
        if not os.path.isfile(app_constants.GALLERY_DEF_ICO_PATH):
            s = FileIcon.refresh_default_icon()
        if s:
            return QIcon(app_constants.GALLERY_DEF_ICO_PATH)
        else:
            return None

# def center_parent(parent, child):
#   "centers child window in parent"
#   centerparent = QPoint(
#   		parent.x() + (parent.frameGeometry().width() -
#   				 child.frameGeometry().width())//2,
#   				parent.y() + (parent.frameGeometry().width() -
#   				   child.frameGeometry().width())//2)
#   desktop = QApplication.desktop()
#   sg_rect = desktop.screenGeometry(desktop.screenNumber(parent))
#   child_frame = child.frameGeometry()
#
#   if centerparent.x() < sg_rect.left():
#   	centerparent.setX(sg_rect.left())
#   elif (centerparent.x() + child_frame.width()) > sg_rect.right():
#   	centerparent.setX(sg_rect.right() - child_frame.width())
#
#   if centerparent.y() < sg_rect.top():
#   	centerparent.setY(sg_rect.top())
#   elif (centerparent.y() + child_frame.height()) > sg_rect.bottom():
#   	centerparent.setY(sg_rect.bottom() - child_frame.height())
#
#   child.move(centerparent)


class Spacer(QWidget):
    """To be used as a spacer.

    Default mode is both. Specify mode with string: v, h or both
    """

    def __init__(self, mode='both', parent=None):
        """__init__."""
        super().__init__(parent)
        if mode == 'h':
            self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        elif mode == 'v':
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        else:
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)


class FlowLayout(QLayout):
    """FlowLayout."""

    def __init__(self, parent=None, margin=0, spacing=-1):
        """__init__."""
        super(FlowLayout, self).__init__(parent)

        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)

        self.setSpacing(spacing)

        self.itemList = []

    def __del__(self):
        """__del__."""
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        """addItem."""
        self.itemList.append(item)

    def count(self):
        """count."""
        return len(self.itemList)

    # to keep it in style with the others..
    def rowCount(self):
        """rowCount."""
        return self.count()

    def itemAt(self, index):
        """itemAt."""
        if index >= 0 and index < len(self.itemList):
            return self.itemList[index]

        return None

    def takeAt(self, index):
        """takeAt."""
        if index >= 0 and index < len(self.itemList):
            return self.itemList.pop(index)

        return None

    def expandingDirections(self):
        """expandingDirections."""
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self):
        """hasHeightForWidth."""
        return True

    def heightForWidth(self, width):
        """heightForWidth."""
        height = self.doLayout(QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        """setGeometry."""
        super(FlowLayout, self).setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        """sizeHint."""
        return self.minimumSize()

    def minimumSize(self):
        """minimumSize."""
        size = QSize()

        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())

        margin, _, _, _ = self.getContentsMargins()

        size += QSize(2 * margin, 2 * margin)
        return size

    def doLayout(self, rect, testOnly):
        """doLayout."""
        x = rect.x()
        y = rect.y()
        lineHeight = 0

        for item in self.itemList:
            wid = item.widget()
            spaceX = self.spacing() + wid.style().layoutSpacing(
                QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Horizontal)
            spaceY = self.spacing() + wid.style().layoutSpacing(
                QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Vertical)
            nextX = x + item.sizeHint().width() + spaceX
            if nextX - spaceX > rect.right() and lineHeight > 0:
                x = rect.x()
                y = y + lineHeight + spaceY
                nextX = x + item.sizeHint().width() + spaceX
                lineHeight = 0

            if not testOnly:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = nextX
            lineHeight = max(lineHeight, item.sizeHint().height())

        return y + lineHeight - rect.y()


class LineEdit(QLineEdit):
    """
    Custom Line Edit which sacrifices contextmenu for selectAll
    """

    def __init__(self, parent=None):
        """__init__."""
        super().__init__(parent)

    def mousePressEvent(self, event):
        """mousePressEvent."""
        if event.button() == Qt.RightButton:
            self.selectAll()
        else:
            super().mousePressEvent(event)

    def contextMenuEvent(self, QContextMenuEvent):
        """contextMenuEvent."""
        pass


class CustomTableItem(QTableWidgetItem):
    """CustomTableItem."""

    def __init__(self, item=None, txt='', type=QTableWidgetItem.Type):
        """__init__."""
        super().__init__(txt, type)
        self.item = item

class Loading(BasePopup):
    """Loading."""

    ON = False  # to prevent multiple instances

    def __init__(self, parent=None):
        """__init__."""
        super().__init__(parent)
        self.progress = QProgressBar()
        self.progress.setStyleSheet("color:white")
        self.text = QLabel()
        self.text.setAlignment(Qt.AlignCenter)
        self.text.setStyleSheet("color:white;background-color:transparent;")
        inner_layout_ = QVBoxLayout()
        inner_layout_.addWidget(self.text, 0, Qt.AlignHCenter)
        inner_layout_.addWidget(self.progress)
        self.main_widget.setLayout(inner_layout_)
        self.resize(300, 100)
        # frect = self.frameGeometry()
        #  frect.moveCenter(QDesktopWidget().availableGeometry().center())
        #  self.move(parent.window().frameGeometry().topLeft() +
        # 	parent.window().rect().center() -
        # 	self.rect().center() - QPoint(self.rect().width(),0))
        #  self.setAttribute(Qt.WA_DeleteOnClose)
        # self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

    def setText(self, string):
        """setText."""
        if string != self.text.text():
            self.text.setText(string)


class CompleterTextEdit(QTextEdit):
    """A textedit with autocomplete."""

    def __init__(self, **kwargs):
        """__init__."""
        super().__init__(**kwargs)
        self._completer = None
        log_d('Instantiate CompleterTextEdit: OK')

    def setCompleter(self, c):
        """setCompleter."""
        if self._completer is not None:
            self._completer.activated.disconnect()

        self._completer = c

        c.setWidget(self)
        c.setCompletionMode(QCompleter.PopupCompletion)
        c.setCaseSensitivity(Qt.CaseInsensitive)
        c.activated.connect(self.insertCompletion)

    def completer(self):
        """completer."""
        return self._completer

    def insertCompletion(self, completion):
        """insertCompletion."""
        if self._completer.widget() is not self:
            return

        tc = self.textCursor()
        extra = len(completion) - len(self._completer.completionPrefix())
        tc.movePosition(QTextCursor.Left)
        tc.movePosition(QTextCursor.EndOfWord)
        tc.insertText(completion[-extra:])
        self.setTextCursor(tc)

    def textUnderCursor(self):
        """textUnderCursor."""
        tc = self.textCursor()
        tc.select(QTextCursor.WordUnderCursor)

        return tc.selectedText()

    def focusInEvent(self, e):
        """focusInEvent."""
        if self._completer is not None:
            self._completer.setWidget(self)

        super().focusInEvent(e)

    def keyPressEvent(self, e):
        """keyPressEvent."""
        if self._completer is not None and self._completer.popup().isVisible():
            # The following keys are forwarded by the completer to the widget.
            if e.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Escape, Qt.Key_Tab, Qt.Key_Backtab):
                e.ignore()
                # Let the completer do default behavior.
                return

        isShortcut = e.modifiers() == Qt.ControlModifier and e.key() == Qt.Key_E
        if self._completer is None or not isShortcut:
            # Do not process the shortcut when we have a completer.
            super().keyPressEvent(e)

        ctrlOrShift = e.modifiers() & (Qt.ControlModifier | Qt.ShiftModifier)
        if self._completer is None or (ctrlOrShift and len(e.text()) == 0):
            return

        eow = "~!@#$%^&*()_+{}|:\"<>?,./;'[]\\-="
        hasModifier = (e.modifiers() != Qt.NoModifier) and not ctrlOrShift
        completionPrefix = self.textUnderCursor()

        hide_completer_popup = not isShortcut and (
            hasModifier or len(e.text()) == 0 or len(
                completionPrefix) < 3 or e.text()[-1] in eow
        )
        if hide_completer_popup:
            self._completer.popup().hide()
            return

        if completionPrefix != self._completer.completionPrefix():
            self._completer.setCompletionPrefix(completionPrefix)
            self._completer.popup().setCurrentIndex(
                self._completer.completionModel().index(0, 0))

        cr = self.cursorRect()
        cr.setWidth(self._completer.popup().sizeHintForColumn(
            0) + self._completer.popup().verticalScrollBar().sizeHint().width())
        if self._completer:
            self._completer.complete(cr)


class GCompleter(QCompleter):
    """GCompleter."""

    def __init__(self, parent=None, title=True, artist=True, tags=True):
        """__init__."""
        self.all_data = []
        d = set()
        for g in app_constants.GALLERY_DATA:
            if title:
                d.add(g.title)
            if artist:
                d.add(g.artist)
            if tags:
                for ns in g.tags:
                    d.add(ns)
                    for t in g.tags[ns]:
                        d.add(t)

        self.all_data.extend(d)
        super().__init__(self.all_data, parent)
        self.setCaseSensitivity(Qt.CaseInsensitive)


class ChapterListItem(QFrame):
    """ChapterListItem."""

    move_pos = pyqtSignal(int, object)

    def __init__(self, chapter, parent=None):
        """__init__."""
        super().__init__(parent)
        main_layout = QHBoxLayout(self)
        chapter_layout = QFormLayout()
        self.number_lbl = QLabel(str(chapter.number + 1), self)
        self.number_lbl.adjustSize()
        self.number_lbl.setFixedSize(self.number_lbl.size())
        self.chapter_lbl = ElidedLabel(self)
        self.set_chapter_title(chapter)
        main_layout.addWidget(self.number_lbl)
        chapter_layout.addRow(self.chapter_lbl)
        g_title = ''
        if chapter.gallery:
            g_title = chapter.gallery.title
        self.gallery_lbl = ElidedLabel(g_title, self)
        g_lbl_font = QFont(self.gallery_lbl.font())
        g_lbl_font.setPixelSize(g_lbl_font.pixelSize() - 2)
        g_lbl_font.setItalic(True)
        self.gallery_lbl.setFont(g_lbl_font)
        chapter_layout.addRow(self.gallery_lbl)
        self.chapter = chapter
        main_layout.addLayout(chapter_layout)
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(0)
        up_btn = QPushButton('▲')
        up_btn.adjustSize()
        up_btn.setFixedSize(up_btn.size())
        up_btn.clicked.connect(lambda: self.move_pos.emit(0, self))
        down_btn = QPushButton('▼')
        down_btn.adjustSize()
        down_btn.setFixedSize(down_btn.size())
        down_btn.clicked.connect(lambda: self.move_pos.emit(1, self))
        buttons_layout.addWidget(up_btn)
        buttons_layout.addWidget(down_btn)
        main_layout.addLayout(buttons_layout)

    def set_chapter_title(self, chapter):
        """set_chapter_title."""
        if chapter.title:
            self.chapter_lbl.setText(chapter.title)
        else:
            self.chapter_lbl.setText("Chapter " + str(chapter.number + 1))

﻿# This file is part of Happypanda.
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
from __future__ import annotations
import functools
import logging
import math
import os
import threading
import time
from typing import ClassVar, TYPE_CHECKING

import scandir
from PyQt5.QtCore import (Qt, QPoint, pyqtSignal, QTimer, QSize, QRect, QFileInfo,
                          QRectF,
                          QPropertyAnimation, QByteArray,
                          QPointF, QSizeF, pyqtBoundSignal)
from PyQt5.QtGui import (QTextCursor, QIcon, QMouseEvent, QFont,
                         QPainter, QBrush,
                         QColor, QPen, QPixmap, QPaintEvent, QFontMetrics,
                         QPolygonF, QCursor, QTextOption, QTextLayout,
                         QPalette)
from PyQt5.QtWidgets import (QWidget, QProgressBar, QLabel,
                             QVBoxLayout, QHBoxLayout,
                             QDialog, QLineEdit,
                             QFormLayout, QPushButton, QTextEdit,
                             QDesktopWidget, QMessageBox, QFileDialog,
                             QCompleter, QListWidgetItem,
                             QListWidget, QSizePolicy,
                             QCheckBox, QFrame, QListView,
                             QAbstractItemView, QTreeView, QSpinBox,
                             QAction, QStackedLayout, QLayout, QFileIconProvider, QScrollArea, QSystemTrayIcon,
                             QMenu, QActionGroup,
                             QCommonStyle, QTableWidget,
                             QTableWidgetItem, QTableView, QStyleOption)

from .utils import (tag_to_string, tag_to_dict, title_parser, ARCHIVE_FILES,
                    ArchiveFile, IMG_FILES)
from .executors import Executors
from . import utils, gallerydb
from . import app_constants
from . import gallerydb
from . import fetch
from . import settings


log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


def text_layout(text, width, font, font_metrics, alignment=Qt.AlignCenter):
    """Lays out wrapped text"""
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
    if parent_widget:
        r = parent_widget.rect()
    else:
        r = QDesktopWidget().availableGeometry()

    widget.setGeometry(QCommonStyle.alignedRect(Qt.LeftToRight,
                                                Qt.AlignCenter,
                                                widget.size(),
                                                r))


def clearLayout(layout):
    if layout is not None:
        while layout.count():
            child = layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()
            elif child.layout() is not None:
                clearLayout(child.layout())


def create_animation(parent, prop):
    p_array = QByteArray().append(prop)
    return QPropertyAnimation(parent, p_array)


class ArrowHandle(QWidget):
    """Arrow Handle"""
    IN: ClassVar[int] = 0
    OUT: ClassVar[int] = 1
    CLICKED: pyqtBoundSignal = pyqtSignal(int)

    def __init__(self, parent):
        super().__init__(parent)
        self.parent_widget = parent
        self.current_arrow = self.IN
        self.arrow_height = 20
        self.setFixedWidth(10)
        self.setCursor(Qt.PointingHandCursor)

    def paintEvent(self, event):
        rect = self.rect()
        x, y, w, h = rect.getRect()
        painter = QPainter(self)
        painter.setPen(QColor("white"))
        painter.setBrush(QBrush(QColor(0, 0, 0, 100)))
        painter.fillRect(rect, QColor(0, 0, 0, 100))

        arrow_points = []

        # for horizontal
        if self.current_arrow == self.IN:
            arrow_1 = QPointF(x + w, h / 2 - self.arrow_height / 2)
            middle_point = QPointF(x, h / 2)
            arrow_2 = QPointF(x + w, h / 2 + self.arrow_height / 2)
        else:
            arrow_1 = QPointF(x, h / 2 - self.arrow_height / 2)
            middle_point = QPointF(x + w, h / 2)
            arrow_2 = QPointF(x, h / 2 + self.arrow_height / 2)

        arrow_points.append(arrow_1)
        arrow_points.append(middle_point)
        arrow_points.append(arrow_2)
        painter.drawPolygon(QPolygonF(arrow_points))

    def click(self):
        if self.current_arrow == self.IN:
            self.current_arrow = self.OUT
            self.CLICKED.emit(1)
        else:
            self.current_arrow = self.IN
            self.CLICKED.emit(0)
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.click()
        return super().mousePressEvent(event)


class Line(QFrame):
    """'v' for vertical line or 'h' for horizontail line, color is hex string"""

    def __init__(self, orentiation, parent=None):
        super().__init__(parent)
        self.setFrameStyle(self.StyledPanel)
        if orentiation == 'v':
            self.setFrameShape(self.VLine)
        else:
            self.setFrameShape(self.HLine)
        self.setFrameShadow(self.Sunken)


class CompleterPopupView(QListView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _setup(self):
        self.fade_animation = create_animation(self, 'windowOpacity')
        self.fade_animation.setDuration(200)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFrameStyle(self.StyledPanel)

    def showEvent(self, event):
        self.setWindowOpacity(0)
        self.fade_animation.start()
        super().showEvent(event)


class ElidedLabel(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def paintEvent(self, event):
        painter = QPainter(self)
        metrics = QFontMetrics(self.font())
        elided = metrics.elidedText(self.text(), Qt.ElideRight, self.width())
        painter.drawText(self.rect(), self.alignment(), elided)


class BaseMoveWidget(QWidget):
    def __init__(self, parent=None, **kwargs):
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
        if new_size:
            self.move(new_size)
            return
        if self.parent_widget:
            self.move(self.parent_widget.window().frameGeometry().center()
                      - self.window().rect().center())


class SortMenu(QMenu):
    new_sort: pyqtBoundSignal = pyqtSignal(str)

    def __init__(self, app_inst, parent=None, toolbutton=None):
        super().__init__(parent)
        self.parent_widget = app_inst
        self.toolbutton = toolbutton
        self.sort_actions = QActionGroup(self)
        self.sort_actions.setExclusive(True)
        asc_desc_act = QAction("Asc/Desc", self)
        asc_desc_act.triggered.connect(self.asc_desc)
        q_action_s_title = QAction("Title", self.sort_actions)
        q_action_s_title.setCheckable(True)
        s_title = self.sort_actions.addAction(q_action_s_title)
        s_title.triggered.connect(functools.partial(self.new_sort.emit, 'title'))
        q_action_s_artist = QAction("Author", self.sort_actions)
        q_action_s_artist.setCheckable(True)
        s_artist = self.sort_actions.addAction(q_action_s_artist)
        s_artist.triggered.connect(functools.partial(self.new_sort.emit, 'artist'))
<<<<<<< HEAD
        q_action_s_date = QAction("Date Added", self.sort_actions)
        q_action_s_date.setCheckable(True)
        s_date = self.sort_actions.addAction(q_action_s_date)
=======
        s_group = self.sort_actions.addAction(QAction("Group", self.sort_actions, checkable=True))
        s_group.triggered.connect(functools.partial(self.new_sort.emit, 'group'))
        s_date = self.sort_actions.addAction(QAction("Date Added", self.sort_actions, checkable=True))
>>>>>>> Kramoule/develop
        s_date.triggered.connect(functools.partial(self.new_sort.emit, 'date_added'))
        q_action_pub_d = QAction("Date Published", self.sort_actions)
        q_action_pub_d.setCheckable(True)
        s_pub_d = self.sort_actions.addAction(q_action_pub_d)
        s_pub_d.triggered.connect(functools.partial(self.new_sort.emit, 'pub_date'))
        q_action_s_times_read = QAction("Read Count", self.sort_actions)
        q_action_s_times_read.setCheckable(True)
        s_times_read = self.sort_actions.addAction(q_action_s_times_read)
        s_times_read.triggered.connect(functools.partial(self.new_sort.emit, 'times_read'))
        q_action_s_last_read = QAction("Last Read", self.sort_actions)
        q_action_s_last_read.setCheckable(True)
        s_last_read = self.sort_actions.addAction(q_action_s_last_read)
        s_last_read.triggered.connect(functools.partial(self.new_sort.emit, 'last_read'))
        q_action_s_rating = QAction("Rating", self.sort_actions)
        q_action_s_rating.setCheckable(True)
        s_rating = self.sort_actions.addAction(q_action_s_rating)
        s_rating.triggered.connect(functools.partial(self.new_sort.emit, 'rating'))

        self.addAction(asc_desc_act)
        self.addSeparator()
        self.addAction(s_artist)
        self.addAction(s_group)
        self.addAction(s_date)
        self.addAction(s_pub_d)
        self.addAction(s_last_read)
        self.addAction(s_title)
        self.addAction(s_rating)
        self.addAction(s_times_read)

        self.set_current_sort()

    def set_toolbutton_text(self):
        act = self.sort_actions.checkedAction()
        if self.toolbutton:
            self.toolbutton.setText(act.text())

    def set_current_sort(self):
        def check_key(act, key):
            if self.parent_widget.current_manga_view.list_view.current_sort == key:
                act.setChecked(True)

        for act in self.sort_actions.actions():
            if act.text() == 'Title':
                check_key(act, 'title')
            elif act.text() == 'Author':
                check_key(act, 'artist')
            elif act.text() == 'Group':
                check_key(act, 'group')
            elif act.text() == 'Date Added':
                check_key(act, 'date_added')
            elif act.text() == 'Date Published':
                check_key(act, 'pub_date')
            elif act.text() == 'Read Count':
                check_key(act, 'times_read')
            elif act.text() == 'Last Read':
                check_key(act, 'last_read')
            elif act.text() == 'Rating':
                check_key(act, 'rating')

    def asc_desc(self):
        if self.parent_widget.current_manga_view.sort_model.sortOrder() == Qt.AscendingOrder:
            if self.toolbutton:
                self.toolbutton.setIcon(app_constants.SORT_ICON_DESC)
            self.parent_widget.current_manga_view.sort_model.sort(0, Qt.DescendingOrder)
        else:
            if self.toolbutton:
                self.toolbutton.setIcon(app_constants.SORT_ICON_ASC)
            self.parent_widget.current_manga_view.sort_model.sort(0, Qt.AscendingOrder)

    def showEvent(self, event):
        self.set_current_sort()
        super().showEvent(event)


class ToolbarButton(QPushButton):
    select: pyqtBoundSignal = pyqtSignal(object)
    close_tab: pyqtBoundSignal = pyqtSignal(object)

    def __init__(self, parent=None, txt=''):
        super().__init__(parent)
        self.setText(txt)
        self._selected = False
        self.clicked.connect(lambda: self.select.emit(self))
        self._enable_contextmenu = True

    @property
    def selected(self):
        return self._selected

    @selected.setter
    def selected(self, b):
        self._selected = b

    def contextMenuEvent(self, event):
        if self._enable_contextmenu:
            m = QMenu(self)
            m.addAction("Close Tab").triggered.connect(lambda: self.close_tab.emit(self))
            m.exec_(event.globalPos())
            event.accept()
        else:
            event.ignore()


class TransparentWidget(BaseMoveWidget):
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.setAttribute(Qt.WA_TranslucentBackground)


class ArrowWindow(TransparentWidget):
    LEFT, RIGHT, TOP, BOTTOM = range(4)

    def __init__(self, parent):
        super().__init__(parent, flags=Qt.Window | Qt.FramelessWindowHint, move_listener=False)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.resize(550, 300)
        self.direction = self.LEFT
        self._arrow_size = QSizeF(30, 30)
        self.content_margin = 0

    @property
    def arrow_size(self):
        return self._arrow_size

    @arrow_size.setter
    def arrow_size(self, w_h_tuple):
        """a tuple of width and height"""
        if not isinstance(w_h_tuple, (tuple, list)) or len(w_h_tuple) != 2:
            return

        if self.direction in (self.LEFT, self.RIGHT):
            s = QSizeF(w_h_tuple[1], w_h_tuple[0])
        else:
            s = QSizeF(w_h_tuple[0], w_h_tuple[1])

        self._arrow_size = s
        self.update()

    def paintEvent(self, event):
        assert isinstance(event, QPaintEvent)

        opt = QStyleOption()
        opt.initFrom(self)

        painter = QPainter(self)
        painter.setRenderHint(painter.Antialiasing)

        size = self.size()
        if self.direction in (self.LEFT, self.RIGHT):
            actual_size = QSizeF(size.width() - self.arrow_size.width(), size.height())
        else:
            actual_size = QSizeF(size.width(), size.height() - self.arrow_size.height())

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
        background_rect = QRectF(starting_point, actual_size)
        # painter.drawRoundedRect(background_rect, 5, 5)

        # calculate the arrow
        arrow_points = []
        if self.direction == self.LEFT:
            middle_point = QPointF(0, actual_size.height() / 2)
            arrow_1 = QPointF(self.arrow_size.width(), middle_point.y() - self.arrow_size.height() / 2)
            arrow_2 = QPointF(self.arrow_size.width(), middle_point.y() + self.arrow_size.height() / 2)
            arrow_points.append(arrow_1)
            arrow_points.append(middle_point)
            arrow_points.append(arrow_2)
        elif self.direction == self.RIGHT:
            middle_point = QPointF(actual_size.width() + self.arrow_size.width(), actual_size.height() / 2)
            arrow_1 = QPointF(actual_size.width(), middle_point.y() + self.arrow_size.height() / 2)
            arrow_2 = QPointF(actual_size.width(), middle_point.y() - self.arrow_size.height() / 2)
            arrow_points.append(arrow_1)
            arrow_points.append(middle_point)
            arrow_points.append(arrow_2)
        elif self.direction == self.TOP:
            middle_point = QPointF(actual_size.width() / 2, 0)
            arrow_1 = QPointF(actual_size.width() / 2 + self.arrow_size.width() / 2, self.arrow_size.height())
            arrow_2 = QPointF(actual_size.width() / 2 - self.arrow_size.width() / 2, self.arrow_size.height())
            arrow_points.append(arrow_1)
            arrow_points.append(middle_point)
            arrow_points.append(arrow_2)
        elif self.direction == self.BOTTOM:
            middle_point = QPointF(actual_size.width() / 2, actual_size.height() + self.arrow_size.height())
            arrow_1 = QPointF(actual_size.width() / 2 - self.arrow_size.width() / 2, actual_size.height())
            arrow_2 = QPointF(actual_size.width() / 2 + self.arrow_size.width() / 2, actual_size.height())
            arrow_points.append(arrow_1)
            arrow_points.append(middle_point)
            arrow_points.append(arrow_2)

        # draw it!
        painter.drawPolygon(QPolygonF(arrow_points))


class GalleryMetaWindow(ArrowWindow):

    def __init__(self, parent):
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
        self.setAttribute(Qt.WA_ShowWithoutActivating)

    def show(self):
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
        self.delayed_hide()
        return super().focusOutEvent(event)

    def _mouse_in_gallery(self):
        mouse_p = QCursor.pos()
        h = self.idx_top_l.x() <= mouse_p.x() <= self.idx_top_r.x()
        v = self.idx_top_l.y() <= mouse_p.y() <= self.idx_btm_l.y()
        if h and v:
            return True
        return False

    def mouseMoveEvent(self, event):
        if self.isVisible():
            if not self._mouse_in_gallery():
                if not self.hide_timer.isActive():
                    self.hide_timer.start(300)
        return super().mouseMoveEvent(event)

    def delayed_hide(self):
        if not self.underMouse() and not self._mouse_in_gallery():
            self.hide_animation.start()

    def show_gallery(self, index, view):
        self.resize(app_constants.POPUP_WIDTH, app_constants.POPUP_HEIGHT)
        self.view = view
        desktop_w = QDesktopWidget().width()
        desktop_h = QDesktopWidget().height()

        margin_offset = 20  # should be higher than gallery_touch_offset
        gallery_touch_offset = 10  # How far away the window is from touching gallery

        index_rect = view.visualRect(index)
        self.idx_top_l = index_top_left = view.mapToGlobal(index_rect.topLeft())
        self.idx_top_r = index_top_right = view.mapToGlobal(index_rect.topRight())
        self.idx_btm_l = index_btm_left = view.mapToGlobal(index_rect.bottomLeft())
        index_btm_right = view.mapToGlobal(index_rect.bottomRight())

        if app_constants.DEBUG:
            for idx in (index_top_left, index_top_right, index_btm_left, index_btm_right):
                print(idx.x(), idx.y())

        # adjust placement

        def check_left():
            middle = (index_top_left.y() + index_btm_left.y()) / 2  # middle of gallery left side
            left = (index_top_left.x() - self.width() - margin_offset) > 0  # if the width can be there
            top = (middle - (self.height() / 2) - margin_offset) > 0  # if the top half of window can be there
            btm = (middle + (self.height() / 2) + margin_offset) < desktop_h  # same as above, just for the bottom
            if left and top and btm:
                self.direction = self.RIGHT
                x = index_top_left.x() - gallery_touch_offset - self.width()
                y = middle - (self.height() / 2)
                appear_point = QPoint(int(x), int(y))
                self.move(appear_point)
                return True
            return False

        def check_right():
            middle = (index_top_right.y() + index_btm_right.y()) / 2  # middle of gallery right side
            right = (index_top_right.x() + self.width() + margin_offset) < desktop_w  # if the width can be there
            top = (middle - (self.height() / 2) - margin_offset) > 0  # if the top half of window can be there
            btm = (middle + (self.height() / 2) + margin_offset) < desktop_h  # same as above, just for the bottom

            if right and top and btm:
                self.direction = self.LEFT
                x = index_top_right.x() + gallery_touch_offset
                y = middle - (self.height() / 2)
                appear_point = QPoint(int(x), int(y))
                self.move(appear_point)
                return True
            return False

        def check_top():
            middle = (index_top_left.x() + index_top_right.x()) / 2  # middle of gallery top side
            top = (index_top_right.y() - self.height() - margin_offset) > 0  # if the height can be there
            left = (middle - (self.width() / 2) - margin_offset) > 0  # if the left half of window can be there
            right = (middle + (self.width() / 2) + margin_offset) < desktop_w  # same as above, just for the right

            if top and left and right:
                self.direction = self.BOTTOM
                x = middle - (self.width() / 2)
                y = index_top_left.y() - gallery_touch_offset - self.height()
                appear_point = QPoint(int(x), int(y))
                self.move(appear_point)
                return True
            return False

        def check_bottom(override=False):
            middle = (index_btm_left.x() + index_btm_right.x()) / 2  # middle of gallery bottom side
            btm = (index_btm_right.y() + self.height() + margin_offset) < desktop_h  # if the height can be there
            left = (middle - (self.width() / 2) - margin_offset) > 0  # if the left half of window can be there
            right = (middle + (self.width() / 2) + margin_offset) < desktop_w  # same as above, just for the right

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
        ev.ignore()
        self.delayed_hide()

    def _set_gallery(self, gallery):
        self.current_gallery = gallery
        self.g_widget.apply_gallery(gallery)
        self.g_widget.resize(self.width() - self.content_margin,
                             self.height() - self.content_margin)
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
        class ChapterList(QTableWidget):
            def __init__(self, parent):
                super().__init__(parent)
                self.setColumnCount(3)
                self.setEditTriggers(self.NoEditTriggers)
                self.setFocusPolicy(Qt.NoFocus)
                self.verticalHeader().setSectionResizeMode(self.verticalHeader().ResizeToContents)
                self.horizontalHeader().setSectionResizeMode(0, self.horizontalHeader().ResizeToContents)
                self.horizontalHeader().setSectionResizeMode(1, self.horizontalHeader().Stretch)
                self.horizontalHeader().setSectionResizeMode(2, self.horizontalHeader().ResizeToContents)
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
                self.doubleClicked.connect(lambda idx: self._get_chap(idx).open())

            def set_chapters(self, chapter_container):
                for r in range(self.rowCount()):
                    self.removeRow(0)

                def t_item(txt=''):
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
                r = idx.row()
                t = self.item(r, 0)
                return t.data(Qt.UserRole + 1)

            def contextMenuEvent(self, event):
                idx = self.indexAt(event.pos())
                if idx.isValid():
                    chap = self._get_chap(idx)
                    menu = QMenu(self)
                    open = menu.addAction('Open', lambda: chap.open())

                    def open_source():
                        text = 'Opening archive...' if chap.in_archive else 'Opening folder...'
                        app_constants.STAT_MSG_METHOD(text)
                        path = chap.gallery.path if chap.in_archive else chap.path
                        utils.open_path(path)

                    t = "Open archive" if chap.in_archive else "Open folder"
                    open_path = menu.addAction(t, open_source)
                    menu.exec_(event.globalPos())
                    event.accept()
                    del menu
                else:
                    event.ignore()

        def __init__(self, parent, appwindow):
            super().__init__(parent)
            self.setFocusPolicy(Qt.NoFocus)
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
            back_btn.clicked.connect(lambda: stacked_l.setCurrentIndex(self.general_index))
            chapter_layout.addWidget(back_btn, 0, Qt.AlignCenter)
            chapter_layout.addWidget(self.chapter_list)
            self.left_layout = QFormLayout()
            self.main_left_layout = QVBoxLayout(general_info)
            self.main_left_layout.addLayout(self.left_layout)
            self.right_layout = QFormLayout()
            main_layout.addLayout(stacked_l, 1)
            main_layout.addWidget(Line('v'))
            main_layout.addLayout(self.right_layout)

            def get_label(txt):
                lbl = QLabel(txt)
                lbl.setWordWrap(True)
                return lbl

            self.g_title_lbl = get_label('')
            self.g_title_lbl.setStyleSheet('color:white;font-weight:bold;')
            self.left_layout.addRow(self.g_title_lbl)
            self.g_artist_lbl = ClickedLabel()
            self.g_artist_lbl.setWordWrap(True)
            self.g_artist_lbl.clicked.connect(lambda a: appwindow.search('artist:"{}"'.format(a)))
            self.g_artist_lbl.setStyleSheet('color:#bdc3c7;')
            self.g_artist_lbl.setToolTip("Click to see more from this artist")
            self.left_layout.addRow(self.g_artist_lbl)
            for lbl in (self.g_title_lbl, self.g_artist_lbl):
                lbl.setAlignment(Qt.AlignCenter)
            self.left_layout.addRow(Line('h'))

            first_layout = QHBoxLayout()
            self.g_type_lbl = ClickedLabel()
            self.g_type_lbl.setStyleSheet('text-decoration: underline')
            self.g_type_lbl.clicked.connect(lambda a: appwindow.search('type:"{}"'.format(a)))
            self.g_lang_lbl = ClickedLabel()
            self.g_lang_lbl.setStyleSheet('text-decoration: underline')
            self.g_lang_lbl.clicked.connect(lambda a: appwindow.search('language:"{}"'.format(a)))
            self.g_chapters_lbl = TagText('Chapters')
            self.g_chapters_lbl.clicked.connect(lambda: stacked_l.setCurrentIndex(self.chap_index))
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
            self.g_url_lbl.clicked.connect(lambda: utils.open_web_link(self.g_url_lbl.text()))
            self.g_url_lbl.setWordWrap(True)
            self.left_layout.addRow('URL:', self.g_url_lbl)
            # self.left_layout.addRow(Line('h'))

            self.tags_scroll = QScrollArea(self)
            self.tags_widget = QWidget(self.tags_scroll)
            self.tags_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.tags_layout = QFormLayout(self.tags_widget)
            self.tags_layout.setSizeConstraint(self.tags_layout.SetMaximumSize)
            self.tags_scroll.setWidget(self.tags_widget)
            self.tags_scroll.setWidgetResizable(True)
            self.tags_scroll.setFrameShape(QFrame.NoFrame)
            self.main_left_layout.addWidget(self.tags_scroll)

        def has_tags(self, tags):
            t_len = len(tags)
            if not t_len:
                return False
            if t_len == 1:
                if 'default' in tags:
                    if not tags['default']:
                        return False
            return True

        def apply_gallery(self, gallery):
            self.stacked_l.setCurrentIndex(self.general_index)
            self.chapter_list.set_chapters(gallery.chapters)
            self.g_title_lbl.setText(gallery.title)
            self.g_artist_lbl.setText(gallery.artist)
            self.g_lang_lbl.setText(gallery.language)
            chap_txt = "chapters" if gallery.chapters.count() > 1 else "chapter"
            self.g_chap_count_lbl.setText('{} {}'.format(gallery.chapters.count(), chap_txt))
            self.g_type_lbl.setText(gallery.type)
            pages = gallery.chapters.pages()
            self.g_pages_total_lbl.setText('{}'.format(pages))
            self.g_status_lbl.setText(gallery.status)
            self.g_d_added_lbl.setText(gallery.date_added.strftime('%d %b %Y'))
            if gallery.pub_date:
                self.g_pub_lbl.setText(gallery.pub_date.strftime('%d %b %Y'))
            else:
                self.g_pub_lbl.setText('Unknown')
            last_read_txt = '{} ago'.format(utils.get_date_age(gallery.last_read)) if gallery.last_read else "Unknown"
            self.g_last_read_lbl.setText(last_read_txt)
            self.g_read_count_lbl.setText('Read {} times'.format(gallery.times_read))
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
                            t = TagText(search_widget=self.appwindow, namespace=namespace)
                        t.setText(tag)
                        tags_lbls.addWidget(t)
                        t.setAutoFillBackground(True)
            self.tags_widget.adjustSize()


class Spinner(TransparentWidget):
    """
    Spinner widget
    """
    activated: pyqtBoundSignal = pyqtSignal()
    deactivated: pyqtBoundSignal = pyqtSignal()
    about_to_show: ClassVar[int] = 0
    about_to_hide: ClassVar[int] = 1
    _OFFSET_X_TOPRIGHT = [0]

    def __init__(self, parent, position='topright'):
        """Position can be: 'center', 'topright' or QPoint"""
        super().__init__(parent, flags=Qt.Window | Qt.FramelessWindowHint, move_listener=False)
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
        self.text_layout = text_layout(self.text, self.width() - self._text_margin, self.font(), self.fontMetrics())
        self.setFixedHeight(self._min_size + self.text_layout.boundingRect().height())

    def set_size(self, w):
        self.setFixedWidth(w)
        self._min_size = w
        self._update_layout()
        self.update()

    def set_text(self, txt):
        self.text = txt
        self._update_layout()
        self.update()

    def _set_position(self, new_pos):
        """'center', 'topright' or QPoint"""
        p = self.parent_widget

        # topleft
        if new_pos == "topright":
            def topright():
                return QPoint(p.pos().x() + p.width() - 65 - self._offset_x_topright,
                              p.pos().y() + p.toolbar.height() + 55)

            self.move(topright())
            p.move_listener.connect(lambda: self.update_move(topright()))

        elif new_pos == "center":
            p.move_listener.connect(lambda: self.update_move(QPoint(p.pos().x() + p.width() // 2,
                                                                    p.pos().y() + p.height() // 2)))

        elif isinstance(new_pos, QPoint):
            p.move_listener.connect(lambda: self.update_move(new_pos))

    def paintEvent(self, event):
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
            painter.drawRoundedRect(QRect(0, 0, self.width(), self.height() - txt_rect.height()), 5, 5)
            painter.restore()

            pen = QPen(QColor('#F2F2F2'))
            pen.setWidth(self.line_width)
            painter.setPen(pen)

            border = self.border + int(math.ceil(self.line_width / 2.0))
            r = QRectF((txt_rect.height()) / 2, (txt_rect.height() / 2),
                       self.width() - txt_rect.height(), self.width() - txt_rect.height())
            r.adjust(border, border, -border, -border)

            # draw the arc:
            painter.drawArc(r, -self._start_angle * 16, self.arc_length * 16)

            # draw text if there is
            if self.text:
                txt_rect = self.text_layout.boundingRect()
                self.text_layout.draw(painter, QPointF(self._text_margin,
                                                       self.height() - txt_rect.height() - self._text_margin / 2))

            r = None

        finally:
            painter.end()
            painter = None

    def showEvent(self, event):
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
        self._timer.stop()
        self.deactivated.emit()
        super().hideEvent(event)

    def before_hide(self):
        if self.current_state == self.about_to_hide:
            return
        self.current_state = self.about_to_hide
        if self._position == "topright":
            self._OFFSET_X_TOPRIGHT[0] -= self.width() + self.margin
        self.state_timer.start(5000)

    def closeEvent(self, event):
        self._timer.stop()
        super().closeEvent(event)

    def _on_timer_timeout(self):
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


class GalleryMenu(QMenu):
    delete_galleries: pyqtBoundSignal = pyqtSignal(bool)
    edit_gallery: pyqtBoundSignal = pyqtSignal(object, object)

    gallery: gallerydb.Gallery

    def __init__(self, view, index, sort_model, app_window, selected_indexes=None):
        super().__init__(app_window)
        self.parent_widget = app_window
        self.view = view
        self.sort_model = sort_model
        self.index = index
        self.gallery = index.data(Qt.UserRole + 1)
        self.selected = selected_indexes
        if self.view.view_type == app_constants.ViewType.Default:
            if not self.selected:
                favourite_act = self.addAction('Favorite',
                                               lambda: self.parent_widget.manga_list_view.favorite(self.index))
                favourite_act.setCheckable(True)
                if self.gallery.fav:
                    favourite_act.setChecked(True)
                    favourite_act.setText('Unfavorite')
                else:
                    favourite_act.setChecked(False)
            else:
                favourite_act = self.addAction('Favorite selected', self.favourite_select)
                favourite_act.setCheckable(True)
                f = []
                for idx in self.selected:
                    g: gallerydb.Gallery = idx.data(Qt.UserRole + 1)
                    if g.fav:
                        f.append(True)
                    else:
                        f.append(False)
                if all(f):
                    favourite_act.setChecked(True)
                    favourite_act.setText('Unfavorite selected')
                else:
                    favourite_act.setChecked(False)
        elif self.view.view_type == app_constants.ViewType.Addition:

            send_to_lib = self.addAction('Send to library',
                                         self.send_to_lib)
            add_to_ignore = self.addAction('Ignore and remove',
                                           self.add_to_ignore)
        self.addSeparator()
        rating = self.addAction('Set rating')
        rating_menu = QMenu(self)
        rating.setMenu(rating_menu)
        for x in range(0, 6):
            rating_menu.addAction('{}'.format(x), functools.partial(self.set_rating, x))
        self.addSeparator()
        if not self.selected and isinstance(view, QTableView):
            chapters_menu = self.addAction('Chapters')
            open_chapters = QMenu(self)
            chapters_menu.setMenu(open_chapters)
            for number, chap in enumerate(self.gallery.chapters, 1):
                chap_action = QAction("Open chapter {}".format(number), open_chapters)
                chap_action.triggered.connect(functools.partial(chap.open))
                open_chapters.addAction(chap_action)
        if self.selected:
            open_f_chapters = self.addAction('Open first chapters', self.open_first_chapters)

        if self.view.view_type != app_constants.ViewType.Duplicate:
            if not self.selected:
                add_chapters = self.addAction('Add chapters', self.add_chapters)
            if self.view.view_type == app_constants.ViewType.Default:
                add_to_list_txt = "Add selected to list" if self.selected else "Add to list"
                add_to_list = self.addAction(add_to_list_txt)
                add_to_list_menu = QMenu(self)
                add_to_list.setMenu(add_to_list_menu)
                for g_list in sorted(app_constants.GALLERY_LISTS):
                    add_to_list_menu.addAction(g_list.name, functools.partial(self.add_to_list, g_list))
        self.addSeparator()
        web_menu_act = self.addAction('Web')
        web_menu = QMenu(self)
        web_menu_act.setMenu(web_menu)

        if not self.selected:
            get_metadata = web_menu.addAction('Fetch metadata',
                                              lambda: self.parent_widget.get_metadata(index.data(Qt.UserRole + 1)))
        else:
            gals = []
            for idx in self.selected:
                gals.append(idx.data(Qt.UserRole + 1))
            get_select_metadata = web_menu.addAction('Fetch metadata for selected',
                                                     lambda: self.parent_widget.get_metadata(gals))

        web_menu.addSeparator()

        if self.index.data(Qt.UserRole + 1).link and not self.selected:
            op_link = web_menu.addAction('Open URL', self.op_link)
            web_menu.addSeparator()
        if self.selected and all([idx.data(Qt.UserRole + 1).link for idx in self.selected]):
            op_links = web_menu.addAction('Open URLs', lambda: self.op_link(True))
            web_menu.addSeparator()

        artist_lookup = web_menu.addAction("Lookup Artists" if self.selected else "Lookup Artist",
                                           lambda: self.lookup_web("artist"))

        self.addSeparator()

        edit = self.addAction('Edit', lambda: self.edit_gallery.emit(self.parent_widget,
                                                                     self.index.data(
                                                                         Qt.UserRole + 1) if not self.selected else [
                                                                         idx.data(Qt.UserRole + 1) for idx in
                                                                         self.selected]))

        self.addSeparator()

        if not self.selected:
            text = 'folder' if not self.index.data(Qt.UserRole + 1).is_archive else 'archive'
            op_folder_act = self.addAction('Open {}'.format(text), self.op_folder)
            op_cont_folder_act = self.addAction('Show in folder', lambda: self.op_folder(containing=True))
        else:
            text = 'folders' if not self.index.data(Qt.UserRole + 1).is_archive else 'archives'
            op_folder_select = self.addAction('Open {}'.format(text), lambda: self.op_folder(True))
            op_cont_folder_select = self.addAction('Show in folders', lambda: self.op_folder(True, True))

        remove_act = self.addAction('Remove')
        remove_menu = QMenu(self)
        remove_act.setMenu(remove_menu)
        if self.view.view_type == app_constants.ViewType.Default:
            if self.sort_model.current_gallery_list:
                remove_f_g_list_txt = "Remove selected from list" if self.selected else "Remove from list"
                remove_f_g_list = remove_menu.addAction(remove_f_g_list_txt, self.remove_from_list)
        if not self.selected:
            remove_g = remove_menu.addAction('Remove gallery',
                                             lambda: self.delete_galleries.emit(False))
            remove_ch = remove_menu.addAction('Remove chapter')
            remove_ch_menu = QMenu(self)
            remove_ch.setMenu(remove_ch_menu)
            for number, chap_number in enumerate(range(len(self.index.data(Qt.UserRole + 1).chapters)), 1):
                chap_action = QAction("Remove chapter {}".format(number),
                                      remove_ch_menu,
                                      triggered=functools.partial(self.parent_widget.manga_list_view.del_chapter,
                                                                  index,
                                                                  chap_number))
                remove_ch_menu.addAction(chap_action)
        else:
            remove_select_g = remove_menu.addAction('Remove selected', lambda: self.delete_galleries.emit(False))
        remove_menu.addSeparator()
        if not self.selected:
            remove_source_g = remove_menu.addAction('Remove and delete files',
                                                    lambda: self.delete_galleries.emit(True))
        else:
            remove_source_select_g = remove_menu.addAction('Remove selected and delete files',
                                                           lambda: self.delete_galleries.emit(True))
        self.addSeparator()
        advanced = self.addAction('Advanced')
        adv_menu = QMenu(self)
        advanced.setMenu(adv_menu)
        if not self.selected:
            change_cover = adv_menu.addAction('Change cover...', self.change_cover)

        if self.selected:
            allow_metadata_count = 0
            for i in self.selected:
                if i.data(Qt.UserRole + 1).exed:
                    allow_metadata_count += 1
            self.allow_metadata_exed = allow_metadata_count >= len(self.selected) // 2
        else:
            self.allow_metadata_exed = False if not self.gallery.exed else True

        if self.selected:
            allow_metadata_txt = "Include selected in auto metadata fetch" if self.allow_metadata_exed else "Exclude selected in auto metadata fetch"
        else:
            allow_metadata_txt = "Include in 'Fetch all metadata'" if self.allow_metadata_exed else "Exclude in 'Fetch all metadata'"
        adv_menu.addAction(allow_metadata_txt, self.allow_metadata_fetch)
        adv_menu.addAction("Reset read count", self.reset_read_count)

    def lookup_web(self, txt):
        tag = []
        if txt == 'artist':
            if self.selected:
                for i in self.selected:
                    tag.append('artist:' + i.data(Qt.UserRole + 2).strip())
            else:
                tag.append('artist:' + self.index.data(Qt.UserRole + 2).strip())

        for t in tag:
            utils.lookup_tag(t)

    def set_rating(self, x):
        if self.selected:
            for idx in self.selected:
                g = idx.data(Qt.UserRole + 1)
                g.rating = x
                modifier = gallerydb.GalleryDB.new_gallery_modifier_based_on(g).inherit_rating()
                gallerydb.execute(modifier.execute, True)
        else:
            self.gallery.rating = x
            modifier = gallerydb.GalleryDB.new_gallery_modifier_based_on(self.gallery).inherit_rating()
            gallerydb.execute(modifier.execute, True)

    def add_to_ignore(self):
        if self.selected:
            gs = self.selected
        else:
            gs = [self.index]
        galleries = [idx.data(Qt.UserRole + 1) for idx in gs]

        paths = set()
        for g in galleries:
            for chap in g.chapters:
                if not chap.in_archive:
                    paths.add(chap.path)
                else:
                    paths.add(g.path)
        app_constants.IGNORE_PATHS.extend(paths)

        settings.set(app_constants.IGNORE_PATHS, 'Application', 'ignore paths')
        self.delete_galleries.emit(False)

    def send_to_lib(self):
        if self.selected:
            gs = self.selected
        else:
            gs = [self.index]
        galleries = [idx.data(Qt.UserRole + 1) for idx in gs]
        rows = len(galleries)
        self.view.gallery_model._gallery_to_remove.extend(galleries)
        self.view.gallery_model.removeRows(self.view.gallery_model.rowCount() - rows, rows)
        self.parent_widget.default_manga_view.add_gallery(galleries)
        for g in galleries:
            modifier = gallerydb.GalleryDB.new_gallery_modifier_based_on(g).inherit_view()
            gallerydb.execute(modifier.execute, True)
        self.view.sort_model.refresh()
        self.view.clearSelection()

    def allow_metadata_fetch(self):
        exed = 0 if self.allow_metadata_exed else 1
        if self.selected:
            for idx in self.selected:
                g = idx.data(Qt.UserRole + 1)
                g.exed = exed
                modifier = gallerydb.GalleryDB.new_gallery_modifier_based_on(g).inherit_exed()
                gallerydb.execute(modifier.execute, True)
        else:
            self.gallery.exed = exed
            modifier = gallerydb.GalleryDB.new_gallery_modifier_based_on(self.gallery).inherit_exed()
            gallerydb.execute(modifier.execute, True)

    def reset_read_count(self):
        if self.selected:
            for idx in self.selected:
                g = idx.data(Qt.UserRole + 1)
                g.times_read = 0
                modifier = gallerydb.GalleryDB.new_gallery_modifier_based_on(g).inherit_times_read()
                gallerydb.execute(modifier.execute, True)
        else:
            self.gallery.times_read = 0
            modifier = gallerydb.GalleryDB.new_gallery_modifier_based_on(self.gallery).inherit_times_read()
            gallerydb.execute(modifier.execute, True)

    def add_to_list(self, g_list):
        galleries = []
        if self.selected:
            for idx in self.selected:
                galleries.append(idx.data(Qt.UserRole + 1))
        else:
            galleries.append(self.gallery)
        g_list.add_gallery(galleries)

    def remove_from_list(self):
        g_list = self.sort_model.current_gallery_list
        if self.selected:
            g_ids = []
            for idx in self.selected:
                g_ids.append(idx.data(Qt.UserRole + 1).id)
        else:
            g_ids = self.gallery.id
        self.sort_model.current_gallery_list.remove_gallery(g_ids)
        self.sort_model.init_search(self.sort_model.current_term)

    def favourite_select(self):
        for idx in self.selected:
            self.parent_widget.manga_list_view.favorite(idx)

    def change_cover(self):
        gallery = self.index.data(Qt.UserRole + 1)
        log_i('Attempting to change cover of {}'.format(gallery.title.encode(errors='ignore')))
        if gallery.is_archive:
            try:
                zip = utils.ArchiveFile(gallery.path)
            except utils.app_constants.CreateArchiveFail:
                app_constants.NOTIF_BAR.add_text('Attempt to change cover failed. Could not create archive.')
                return
            path = zip.extract_all()
        else:
            path = gallery.path

        new_cover = QFileDialog.getOpenFileName(self,
                                                'Select a new gallery cover',
                                                filter='Image {}'.format(utils.IMG_FILTER),
                                                directory=path)[0]
        if new_cover and new_cover.lower().endswith(utils.IMG_FILES):
            gallerydb.GalleryDB.clear_thumb(gallery.profile)
            Executors.generate_thumbnail(gallery, img=new_cover, on_method=gallery.set_profile)
            gallery.reset_profile()
            log_i('Changed cover successfully!')

    def open_first_chapters(self):
        txt = "Opening first chapters of selected galleries"
        app_constants.STAT_MSG_METHOD(txt)
        for idx in self.selected:
            idx.data(Qt.UserRole + 1).chapters[0].open(False)

    def op_link(self, select=False):
        if select:
            for x in self.selected:
                gal = x.data(Qt.UserRole + 1)
                utils.open_web_link(gal.link)
        else:
            utils.open_web_link(self.index.data(Qt.UserRole + 1).link)

    def op_folder(self, select=False, containing=False):
        if select:
            for x in self.selected:
                text = 'Opening archives...' if self.index.data(Qt.UserRole + 1).is_archive else 'Opening folders...'
                text = 'Opening containing folders...' if containing else text
                self.view.STATUS_BAR_MSG.emit(text)
                gal = x.data(Qt.UserRole + 1)
                path = os.path.split(gal.path)[0] if containing else gal.path
                if containing:
                    utils.open_path(path, gal.path)
                else:
                    utils.open_path(path)
        else:
            text = 'Opening archive...' if self.index.data(Qt.UserRole + 1).is_archive else 'Opening folder...'
            text = 'Opening containing folder...' if containing else text
            self.view.STATUS_BAR_MSG.emit(text)
            gal = self.index.data(Qt.UserRole + 1)
            path = os.path.split(gal.path)[0] if containing else gal.path
            if containing:
                utils.open_path(path, gal.path)
            else:
                utils.open_path(path)

    def add_chapters(self):
        def add_chdb(chaps_container):
            gallery = self.index.data(Qt.UserRole + 1)
            log_i('Adding new chapter for {}'.format(gallery.title.encode(errors='ignore')))
            gallerydb.execute(gallerydb.ChapterDB.add_chapters_raw, False, gallery.id, chaps_container)

        ch_widget = ChapterAddWidget(self.index.data(Qt.UserRole + 1), self.parent_widget)
        ch_widget.CHAPTERS.connect(add_chdb)
        ch_widget.show()


class SystemTray(QSystemTrayIcon):
    """
    Pass True to minimized arg in showMessage method to only
    show message if application is minimized.
    """

    def __init__(self, icon, parent=None):
        super().__init__(icon, parent=None)
        self.parent_widget = parent

    def showMessage(self, title, msg, icon=QSystemTrayIcon.Information,
                    msecs=10000, minimized=False):
        # NOTE: Crashes on linux
        # TODO: Fix this!!
        if not app_constants.OS_NAME == "linux":
            if minimized:
                if self.parent_widget.isMinimized() or not self.parent_widget.isActiveWindow():
                    return super().showMessage(title, msg, icon, msecs)
            else:
                return super().showMessage(title, msg, icon, msecs)


class ClickedLabel(QLabel):
    """
    A QLabel which emits clicked signal on click
    """
    clicked: pyqtBoundSignal = pyqtSignal(str)

    def __init__(self, s="", **kwargs):
        super().__init__(s, **kwargs)
        self.setTextInteractionFlags(Qt.LinksAccessibleByMouse | Qt.LinksAccessibleByKeyboard)

    def enterEvent(self, event):
        if self.text():
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
        return super().enterEvent(event)

    def mousePressEvent(self, event):
        self.clicked.emit(self.text())
        return super().mousePressEvent(event)


class TagText(QPushButton):
    def __init__(self, *args, **kwargs):
        self.search_widget = kwargs.pop('search_widget', None)
        self.namespace = kwargs.pop('namespace', None)
        super().__init__(*args, **kwargs)
        if self.search_widget:
            if self.namespace:
                self.clicked.connect(lambda: self.search_widget.search('"{}":"{}"'.format(self.namespace, self.text())))
            else:
                self.clicked.connect(lambda: self.search_widget.search('"{}"'.format(self.text())))

    def mousePressEvent(self, ev):
        assert isinstance(ev, QMouseEvent)
        if ev.button() == Qt.RightButton:
            if self.search_widget:
                menu = QMenu(self)
                menu.addAction("Lookup tag",
                               lambda: utils.lookup_tag(
                                   self.text() if not self.namespace else '{}:{}'.format(self.namespace, self.text())))
                menu.exec(ev.globalPos())

        return super().mousePressEvent(ev)

    def enterEvent(self, event):
        if self.text():
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
        return super().enterEvent(event)


class BasePopup(TransparentWidget):
    graphics_blur = None

    def __init__(self, parent=None, **kwargs):
        blur = True
        if kwargs:
            blur = kwargs.pop('blur', True)
            if kwargs:
                super().__init__(parent, **kwargs)
            else:
                super().__init__(parent, flags=Qt.Dialog | Qt.FramelessWindowHint)
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
        self.curr_pos = event.pos()
        return super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            diff = event.pos() - self.curr_pos
            newpos = self.pos() + diff
            self.move(newpos)
        return super().mouseMoveEvent(event)

    def showEvent(self, event):
        self.activateWindow()
        self.fade_animation.start()
        if self.graphics_blur:
            self.graphics_blur.setEnabled(True)
        return super().showEvent(event)

    def closeEvent(self, event):
        if self.graphics_blur:
            self.graphics_blur.setEnabled(False)
        return super().closeEvent(event)

    def hideEvent(self, event):
        if self.graphics_blur:
            self.graphics_blur.setEnabled(False)
        return super().hideEvent(event)

    def add_buttons(self, *args):
        """
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
    """For application notifications"""

    def __init__(self, parent):
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
        """Duration in seconds!"""
        if self.hide_timer.isActive():
            self.hide_timer.stop()
        self.title.setText('<h3>{}</h3>'.format(title))
        self.content.setText(txt)
        self.hide_timer.start(duration * 1000)
        self.show()
        self.adjustSize()
        self.update_move()

    def update_move(self):
        if self.parent_widget:
            tl = self.parent_widget.geometry().topLeft()
            x = tl.x() + self.parent_widget.width() - self.width() - 10
            y = tl.y() + self.parent_widget.height() - self.height() - self.parent_widget.statusBar().height()
            self.move(x, y)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.close()
        super().mousePressEvent(event)


class AppDialog(BasePopup):
    # modes
    PROGRESS: ClassVar[int] = 0
    MESSAGE: ClassVar[int] = 1
    closing_down: pyqtBoundSignal = pyqtSignal()

    def __init__(self, parent, mode=PROGRESS):
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
            self.info_lbl.setText("Updating your galleries to newest version...")
            self.info_lbl.setWordWrap(True)

            class progress(QProgressBar):
                reached_maximum: pyqtBoundSignal = pyqtSignal()

                def __init__(self, parent=None):
                    super().__init__(parent)

                def setValue(self, v):
                    if v == self.maximum():
                        self.reached_maximum.emit()
                    return super().setValue(v)

            self.prog = progress(self)

            self.prog.reached_maximum.connect(self.close)
            main_layout.addWidget(self.prog)
            self.note_info = QLabel("Note: This popup will close itself when everything is ready")
            self.note_info.setAlignment(Qt.AlignCenter)
            self.restart_info = QLabel("Please wait.. It is safe to restart if there is no sign of progress.")
            self.restart_info.setAlignment(Qt.AlignCenter)
            main_layout.addWidget(self.note_info)
            main_layout.addWidget(self.restart_info)
        elif mode == self.MESSAGE:
            self.info_lbl.setText(
                "<font color='red'>An exception has ben encountered.\nContact the developer to get this fixed." + "\nStability from this point onward cannot be guaranteed.</font>")
            self.setWindowTitle("It was too big!")

        self.main_widget.setLayout(main_layout)
        self.adjustSize()

    def closeEvent(self, event):
        self.parent_widget.setEnabled(True)
        if self.mode == self.MESSAGE:
            self.closing_down.emit()
            return super().closeEvent(event)
        else:
            return super().closeEvent(event)

    def showEvent(self, event):
        self.parent_widget.setEnabled(False)
        return super().showEvent(event)

    def init_restart(self):
        if self.mode == self.PROGRESS:
            self.prog.hide()
            self.note_info.hide()
            self.restart_info.hide()
            log_i('Application requires restart')
            self.note_info.setText("Application requires restart!")


class NotificationOverlay(QWidget):
    """
    A notifaction bar
    """
    clicked: pyqtBoundSignal = pyqtSignal()
    _show_signal: pyqtBoundSignal = pyqtSignal()
    _hide_signal: pyqtBoundSignal = pyqtSignal()
    _unset_cursor: pyqtBoundSignal = pyqtSignal()
    _set_cursor: pyqtBoundSignal = pyqtSignal(object)

    def __init__(self, parent=None):
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
        self._dynamic_height = h

    def mousePressEvent(self, event):
        if self._click:
            self.clicked.emit()
        return super().mousePressEvent(event)

    def set_clickable(self, d=True):
        self._click = d
        self._set_cursor.emit(Qt.PointingHandCursor)

    def resize(self, x, y=0):
        return super().resize(x, self._dynamic_height)

    def add_text(self, text, autohide=True):
        """
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
        """
        Control how long you will show notification bar.
        end_show() must be called to hide the bar.
        """
        self._override_hide = True
        self._show_signal.emit()

    def end_show(self):
        self._override_hide = False
        QTimer.singleShot(5000, self._hide_signal.emit)

    def _reset(self):
        self._unset_cursor.emit()
        self._click = False
        self.clicked.disconnect()

    def showEvent(self, event):
        self.slide_animation.start()
        return super().showEvent(event)


class GalleryShowcaseWidget(QWidget):
    """
    Pass a gallery or set a gallery via -> set_gallery
    """

    double_clicked: pyqtBoundSignal = pyqtSignal(gallerydb.Gallery)

    def __init__(self, gallery=None, parent=None, menu=None):
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
        return self._menu

    @menu.setter
    def contextmenu(self, new_menu):
        new_menu.gallery_widget = self
        self._menu = new_menu

    def set_pixmap(self, gallery, img):
        self.profile.setPixmap(QPixmap.fromImage(img))

    def set_gallery(self, gallery, size=app_constants.THUMB_SMALL):
        assert isinstance(size, (list, tuple))
        self.w = size[0]
        self.h = size[1]
        self.gallery = gallery
        img = gallery.get_profile(app_constants.ProfileType.Small, self.set_pixmap)
        if img:
            self.profile.setPixmap(QPixmap.fromImage(img))
        title = self.font_M.elidedText(gallery.title, Qt.ElideRight, self.w)
        artist = self.font_M.elidedText(gallery.artist, Qt.ElideRight, self.w)
        self.text.setText("{}\n{}".format(title, artist))
        self.setToolTip("{}\n{}".format(gallery.title, gallery.artist))
        self.resize(self.w, self.h + 50)

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.underMouse():
            painter.setBrush(QBrush(QColor(164, 164, 164, 120)))
            painter.drawRect(self.text.pos().x() - 2, self.profile.pos().y() - 5,
                             self.text.width() + 2, self.profile.height() + self.text.height() + 12)
        super().paintEvent(event)

    def enterEvent(self, event):
        self.update()
        return super().enterEvent(event)

    def leaveEvent(self, event):
        self.update()
        return super().leaveEvent(event)

    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit(self.gallery)
        return super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event):
        if self._menu:
            self._menu.exec_(event.globalPos())
            event.accept()
        else:
            event.ignore()


class SingleGalleryChoices(BasePopup):
    """
    Represent a single gallery with a list of choices below.
    Pass a gallery and a list of tuple/list where the first index is a string in each
    if text is passed, the text will be shown alongside gallery, else gallery be centered
    """
    USER_CHOICE: pyqtBoundSignal = pyqtSignal(object)

    def __init__(self, gallery, tuple_first_idx, text=None, parent=None):
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
        self.buttons = self.add_buttons('Skip All', 'Skip', 'Choose', )
        self.buttons[2].clicked.connect(self.finish)
        self.buttons[1].clicked.connect(self.skip)
        self.buttons[0].clicked.connect(self.skipall)
        self.resize(400, 400)
        self.show()

    def finish(self):
        item = self.list_w.selectedItems()
        if item:
            item = item[0]
            self.USER_CHOICE.emit(item.item)
            self.close()

    def skip(self):
        self.USER_CHOICE.emit(())
        self.close()

    def skipall(self):
        self.USER_CHOICE.emit(None)
        self.close()


class BaseUserChoice(QDialog):
    USER_CHOICE: pyqtBoundSignal = pyqtSignal(object)

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setAttribute(Qt.WA_TranslucentBackground)
        main_widget = QFrame(self)
        layout = QVBoxLayout(self)
        layout.addWidget(main_widget)
        self.main_layout = QFormLayout(main_widget)

    def accept(self, choice):
        self.USER_CHOICE.emit(choice)
        super().accept()


class TorrentItem:
    def __init__(self, url, name="", date=None, size=None, seeds=None, peers=None, uploader=None):
        self.url = url
        self.name = name
        self.date = date
        self.size = size
        self.seeds = seeds
        self.peers = peers
        self.uploader = uploader


class TorrentUserChoice(BaseUserChoice):
    def __init__(self, parent, torrentitems=[], **kwargs):
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
        list_item = CustomListItem(item)
        list_item.setText(
            "{}\nSeeds:{}\tPeers:{}\tSize:{}\tDate:{}\tUploader:{}".format(item.name, item.seeds, item.peers, item.size,
                                                                           item.date, item.uploader))
        self._list_w.addItem(list_item)

    def accept(self):
        items = self._list_w.selectedItems()
        if items:
            item = items[0]
            super().accept(item.item)


class LoadingOverlay(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        palette = QPalette(self.palette())
        palette.setColor(palette.Background, Qt.transparent)
        self.setPalette(palette)

    def paintEngine(self, event):
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(event.rect(),
                         QBrush(QColor(255, 255, 255, 127)))
        painter.setPen(QPen(Qt.NoPen))
        for i in range(6):
            if (self.counter / 5) % 6 == i:
                painter.setBrush(QBrush(QColor(127 + (self.counter % 5) * 32, 127, 127)))
            else:
                painter.setBrush(QBrush(QColor(127, 127, 127)))
                painter.drawEllipse(self.width() / 2 + 30 * math.cos(2 * math.pi * i / 6.0) - 10,
                                    self.height() / 2 + 30 * math.sin(2 * math.pi * i / 6.0) - 10,
                                    20, 20)

        painter.end()

    def showEvent(self, event):
        self.timer = self.startTimer(50)
        self.counter = 0
        super().showEvent(event)

    def timerEvent(self, event):
        self.counter += 1
        self.update()
        if self.counter == 60:
            self.killTimer(self.timer)
            self.hide()


class FileIcon:

    def __init__(self):
        self.ico_types = {}

    def get_file_icon(self, path):
        if os.path.isdir(path):
            if not 'dir' in self.ico_types:
                self.ico_types['dir'] = QFileIconProvider().icon(QFileInfo(path))
            return self.ico_types['dir']
        elif path.endswith(utils.ARCHIVE_FILES):
            suff = ''
            for s in utils.ARCHIVE_FILES:
                if path.endswith(s):
                    suff = s
            if not suff in self.ico_types:
                self.ico_types[suff] = QFileIconProvider().icon(QFileInfo(path))
            return self.ico_types[suff]

    @staticmethod
    def get_external_file_icon():
        if app_constants._REFRESH_EXTERNAL_VIEWER:
            if os.path.exists(app_constants.GALLERY_EXT_ICO_PATH):
                os.remove(app_constants.GALLERY_EXT_ICO_PATH)
            info = QFileInfo(app_constants.EXTERNAL_VIEWER_PATH)
            icon = QFileIconProvider().icon(info)
            pixmap = icon.pixmap(QSize(32, 32))
            pixmap.save(app_constants.GALLERY_EXT_ICO_PATH, quality=100)
            app_constants._REFRESH_EXTERNAL_VIEWER = False

        return QIcon(app_constants.GALLERY_EXT_ICO_PATH)

    @staticmethod
    def refresh_default_icon():

        if os.path.exists(app_constants.GALLERY_DEF_ICO_PATH):
            os.remove(app_constants.GALLERY_DEF_ICO_PATH)

        def get_file(n):
            gallery = gallerydb.GalleryDB.get_gallery_by_id(n)
            if not gallery:
                return False
            file = ""
            if gallery.path.endswith(tuple(ARCHIVE_FILES)):
                try:
                    f_zip = ArchiveFile(gallery.path)
                except utils.app_constants.CreateArchiveFail:
                    return False
                for name in f_zip.namelist():
                    if name.lower().endswith(tuple(IMG_FILES)):
                        folder = os.path.join(app_constants.temp_dir,
                                              '{}{}'.format(name, n))
                        f_zip.extract(name, folder)
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
            except FileNotFoundError:
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
        s = True
        if not os.path.isfile(app_constants.GALLERY_DEF_ICO_PATH):
            s = FileIcon.refresh_default_icon()
        if s:
            return QIcon(app_constants.GALLERY_DEF_ICO_PATH)
        else:
            return None


# def center_parent(parent, child):
#	"centers child window in parent"
#	centerparent = QPoint(
#			parent.x() + (parent.frameGeometry().width() -
#					 child.frameGeometry().width())//2,
#					parent.y() + (parent.frameGeometry().width() -
#					   child.frameGeometry().width())//2)
#	desktop = QApplication.desktop()
#	sg_rect = desktop.screenGeometry(desktop.screenNumber(parent))
#	child_frame = child.frameGeometry()

#	if centerparent.x() < sg_rect.left():
#		centerparent.setX(sg_rect.left())
#	elif (centerparent.x() + child_frame.width()) > sg_rect.right():
#		centerparent.setX(sg_rect.right() - child_frame.width())

#	if centerparent.y() < sg_rect.top():
#		centerparent.setY(sg_rect.top())
#	elif (centerparent.y() + child_frame.height()) > sg_rect.bottom():
#		centerparent.setY(sg_rect.bottom() - child_frame.height())

#	child.move(centerparent)
class Spacer(QWidget):
    """
    To be used as a spacer.
    Default mode is both. Specify mode with string: v, h or both
    """

    def __init__(self, mode='both', parent=None):
        super().__init__(parent)
        if mode == 'h':
            self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        elif mode == 'v':
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        else:
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)


class FlowLayout(QLayout):

    def __init__(self, parent=None, margin=0, spacing=-1):
        super(FlowLayout, self).__init__(parent)

        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)

        self.setSpacing(spacing)

        self.itemList = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self.itemList.append(item)

    def count(self):
        return len(self.itemList)

    # to keep it in style with the others..
    def rowCount(self):
        return self.count()

    def itemAt(self, index):
        if index >= 0 and index < len(self.itemList):
            return self.itemList[index]

        return None

    def takeAt(self, index):
        if index >= 0 and index < len(self.itemList):
            return self.itemList.pop(index)

        return None

    def expandingDirections(self):
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self.doLayout(QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super(FlowLayout, self).setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()

        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())

        margin, _, _, _ = self.getContentsMargins()

        size += QSize(2 * margin, 2 * margin)
        return size

    def doLayout(self, rect, test_only):
        x = rect.x()
        y = rect.y()
        line_height = 0

        for item in self.itemList:
            wid = item.widget()
            space_x = self.spacing() + wid.style().layoutSpacing(QSizePolicy.PushButton, QSizePolicy.PushButton,
                                                                 Qt.Horizontal)
            spaceY = self.spacing() + wid.style().layoutSpacing(QSizePolicy.PushButton, QSizePolicy.PushButton,
                                                                Qt.Vertical)
            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > rect.right() and line_height > 0:
                x = rect.x()
                y = y + line_height + spaceY
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y()


class LineEdit(QLineEdit):
    """
    Custom Line Edit which sacrifices contextmenu for selectAll
    """

    def __init__(self, parent=None):
        super().__init__(parent)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.selectAll()
        else:
            super().mousePressEvent(event)

    def contextMenuEvent(self, q_context_menu_event):
        pass

    def sizeHint(self):
        s = super().sizeHint()
        return QSize(400, s.height())


class PathLineEdit(QLineEdit):
    """
    A lineedit which open a filedialog on right/left click
    Set dir to false if you want files.
    """

    def __init__(self, parent=None, dir=True, filters=utils.FILE_FILTER):
        super().__init__(parent)
        self.folder = dir
        self.filters = filters
        self.setPlaceholderText('Right/Left-click to open folder explorer.')
        self.setToolTip('Right/Left-click to open folder explorer.')

    def openExplorer(self):
        if self.folder:
            path = QFileDialog.getExistingDirectory(self,
                                                    'Choose folder')
        else:
            path = QFileDialog.getOpenFileName(self,
                                               'Choose file', filter=self.filters)
            path = path[0]
        if len(path) != 0:
            self.setText(path)

    def mousePressEvent(self, event):
        assert isinstance(event, QMouseEvent)
        if len(self.text()) == 0:
            if event.button() == Qt.LeftButton:
                self.openExplorer()
            else:
                return super().mousePressEvent(event)
        if event.button() == Qt.RightButton:
            self.openExplorer()

        super().mousePressEvent(event)


class ChapterAddWidget(QWidget):
    CHAPTERS: pyqtBoundSignal = pyqtSignal(gallerydb.ChaptersContainer)

    def __init__(self, gallery, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.current_chapters = gallery.chapters.count()
        self.added_chaps = 0
        self.gallery = gallery

        layout = QFormLayout()
        self.setLayout(layout)
        lbl = QLabel('{} by {}'.format(gallery.title, gallery.artist))
        layout.addRow('Gallery:', lbl)
        layout.addRow('Current chapters:', QLabel('{}'.format(self.current_chapters)))

        new_btn = QPushButton('Add directory')
        new_btn.clicked.connect(lambda: self.add_new_chapter('f'))
        new_btn.adjustSize()
        new_btn_a = QPushButton('Add archive')
        new_btn_a.clicked.connect(lambda: self.add_new_chapter('a'))
        new_btn_a.adjustSize()
        add_btn = QPushButton('Finish')
        add_btn.clicked.connect(self.finish)
        add_btn.adjustSize()
        new_l = QHBoxLayout()
        new_l.addWidget(add_btn, 1, alignment=Qt.AlignLeft)
        new_l.addWidget(Spacer('h'))
        new_l.addWidget(new_btn, alignment=Qt.AlignRight)
        new_l.addWidget(new_btn_a, alignment=Qt.AlignRight)
        layout.addRow(new_l)

        frame = QFrame()
        frame.setFrameShape(frame.StyledPanel)
        layout.addRow(frame)

        self.chapter_l = QVBoxLayout()
        frame.setLayout(self.chapter_l)

        self.setMaximumHeight(550)
        self.setFixedWidth(500)
        if parent:
            self.move(
                parent.window().frameGeometry().topLeft() + parent.window().rect().center() - self.rect().center())
        else:
            frect = self.frameGeometry()
            frect.moveCenter(QDesktopWidget().availableGeometry().center())
            self.move(frect.topLeft())
        self.setWindowTitle('Add Chapters')

    def add_new_chapter(self, mode):
        chap_layout = QHBoxLayout()
        self.added_chaps += 1
        curr_chap = self.current_chapters + self.added_chaps

        chp_numb = QSpinBox(self)
        chp_numb.setMinimum(curr_chap - 1)
        chp_numb.setMaximum(curr_chap + 1)
        chp_numb.setValue(curr_chap)
        curr_chap_lbl = QLabel('Chapter {}'.format(curr_chap))

        def ch_lbl(n):
            curr_chap_lbl.setText('Chapter {}'.format(n))

        chp_numb.valueChanged[int].connect(ch_lbl)
        if mode == 'f':
            chp_path = PathLineEdit()
            chp_path.setPlaceholderText('Right/Left-click to open folder explorer.' + ' Leave empty to not add.')
        elif mode == 'a':
            chp_path = PathLineEdit(dir=False)
            chp_path.setPlaceholderText('Right/Left-click to open folder explorer.' + ' Leave empty to not add.')

        chp_path.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        if mode == 'f':
            chap_layout.addWidget(QLabel('D'))
        elif mode == 'a':
            chap_layout.addWidget(QLabel('A'))
        chap_layout.addWidget(chp_path, 3)
        chap_layout.addWidget(chp_numb, 0)
        self.chapter_l.addWidget(curr_chap_lbl,
                                 alignment=Qt.AlignLeft)
        self.chapter_l.addLayout(chap_layout)

    def finish(self):
        chapters = self.gallery.chapters
        widgets = []
        x = True
        while x:
            x = self.chapter_l.takeAt(0)
            if x:
                widgets.append(x)
        for l in range(1, len(widgets), 1):
            layout = widgets[l]
            try:
                line_edit = layout.itemAt(1).widget()
                spin_box = layout.itemAt(2).widget()
            except AttributeError:
                continue
            p = line_edit.text()
            c = spin_box.value() - 1  # because of 0-based index
            if os.path.exists(p):
                chap = chapters.create_chapter(c)
                chap.title = utils.title_parser(os.path.split(p)[1])['title']
                chap.path = p
                if os.path.isdir(p):
                    chap.pages = len(list(scandir.scandir(p)))
                elif p.endswith(utils.ARCHIVE_FILES):
                    chap.in_archive = 1
                    arch = utils.ArchiveFile(p)
                    chap.pages = len(arch.dir_contents(''))
                    arch.close()

        self.CHAPTERS.emit(chapters)
        self.close()


class CustomListItem(QListWidgetItem):
    def __init__(self, item=None, parent=None, txt='', type=QListWidgetItem.Type):
        super().__init__(txt, parent, type)
        self.item = item


class CustomTableItem(QTableWidgetItem):
    def __init__(self, item=None, txt='', type=QTableWidgetItem.Type):
        super().__init__(txt, type)
        self.item = item


class GalleryListView(QWidget):
    SERIES: pyqtBoundSignal = pyqtSignal(list)

    def __init__(self, parent=None, modal=False):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog)
        self.setAttribute(Qt.WA_DeleteOnClose)
        layout = QVBoxLayout()
        self.setLayout(layout)

        if modal:
            frame = QFrame()
            frame.setFrameShape(frame.StyledPanel)
            modal_layout = QHBoxLayout()
            frame.setLayout(modal_layout)
            layout.addWidget(frame)
            info = QLabel('This mode let\'s you add galleries from ' + 'different folders.')
            f_folder = QPushButton('Add directories')
            f_folder.clicked.connect(self.from_folder)
            f_files = QPushButton('Add archives')
            f_files.clicked.connect(self.from_files)
            modal_layout.addWidget(info, 3, Qt.AlignLeft)
            modal_layout.addWidget(f_folder, 0, Qt.AlignRight)
            modal_layout.addWidget(f_files, 0, Qt.AlignRight)

        check_layout = QHBoxLayout()
        layout.addLayout(check_layout)
        if modal:
            check_layout.addWidget(
                QLabel('Please uncheck galleries you do' + ' not want to add. (Exisiting galleries won\'t be added'),
                3)
        else:
            check_layout.addWidget(
                QLabel('Please uncheck galleries you do' + ' not want to add. (Existing galleries are hidden)'),
                3)
        self.check_all = QCheckBox('Check/Uncheck All', self)
        self.check_all.setChecked(True)
        self.check_all.stateChanged.connect(self.all_check_state)

        check_layout.addWidget(self.check_all)
        self.view_list = QListWidget()
        self.view_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.view_list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.view_list.setAlternatingRowColors(True)
        self.view_list.setEditTriggers(self.view_list.NoEditTriggers)
        layout.addWidget(self.view_list)

        add_btn = QPushButton('Add checked')
        add_btn.clicked.connect(self.return_gallery)

        cancel_btn = QPushButton('Cancel')
        cancel_btn.clicked.connect(self.close_window)
        btn_layout = QHBoxLayout()

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        btn_layout.addWidget(spacer)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.resize(500, 550)
        frect = self.frameGeometry()
        frect.moveCenter(QDesktopWidget().availableGeometry().center())
        self.move(frect.topLeft())
        self.setWindowTitle('Gallery List')
        self.count = 0

    def all_check_state(self, new_state):
        row = 0
        done = False
        while not done:
            item = self.view_list.item(row)
            if item:
                row += 1
                if new_state == Qt.Unchecked:
                    item.setCheckState(Qt.Unchecked)
                else:
                    item.setCheckState(Qt.Checked)
            else:
                done = True

    def add_gallery(self, item, name):
        """
        Constructs an widgetitem to hold the provided item,
        and adds it to the view_list
        """
        assert isinstance(name, str)
        gallery_item = CustomListItem(item)
        gallery_item.setText(name)
        gallery_item.setFlags(gallery_item.flags() | Qt.ItemIsUserCheckable)
        gallery_item.setCheckState(Qt.Checked)
        self.view_list.addItem(gallery_item)
        self.count += 1

    def update_count(self):
        self.setWindowTitle('Gallery List ({})'.format(self.count))

    def return_gallery(self):
        gallery_list = []
        row = 0
        done = False
        while not done:
            item = self.view_list.item(row)
            if not item:
                done = True
            else:
                if item.checkState() == Qt.Checked:
                    gallery_list.append(item.item)
                row += 1

        self.SERIES.emit(gallery_list)
        self.close()

    def from_folder(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.DirectoryOnly)
        file_dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        file_view = file_dialog.findChild(QListView, 'listView')
        if file_view:
            file_view.setSelectionMode(QAbstractItemView.MultiSelection)
        f_tree_view = file_dialog.findChild(QTreeView)
        if f_tree_view:
            f_tree_view.setSelectionMode(QAbstractItemView.MultiSelection)

        if file_dialog.exec():
            for path in file_dialog.selectedFiles():
                self.add_gallery(path, os.path.split(path)[1])

    def from_files(self):
        gallery_list = QFileDialog.getOpenFileNames(self,
                                                    'Select 1 or more gallery to add',
                                                    filter='Archives ({})'.format(utils.FILE_FILTER))
        for path in gallery_list[0]:
            # Warning: will break when you add more filters
            if len(path) != 0:
                self.add_gallery(path, os.path.split(path)[1])

    def close_window(self):
        msgbox = QMessageBox()
        msgbox.setText('Are you sure you want to cancel?')
        msgbox.setStandardButtons(msgbox.Yes | msgbox.No)
        msgbox.setDefaultButton(msgbox.No)
        msgbox.setIcon(msgbox.Question)
        if msgbox.exec() == QMessageBox.Yes:
            self.close()


class Loading(BasePopup):
    ON = False  # to prevent multiple instances

    def __init__(self, parent=None):
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
        # frect.moveCenter(QDesktopWidget().availableGeometry().center())
        # self.move(parent.window().frameGeometry().topLeft() +
        #	parent.window().rect().center() -
        #	self.rect().center() - QPoint(self.rect().width(),0))
        # self.setAttribute(Qt.WA_DeleteOnClose)
        # self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

    def mousePressEvent(self, q_mouse_event: QMouseEvent):
        pass

    def setText(self, string):
        if string != self.text.text():
            self.text.setText(string)


class CompleterTextEdit(QTextEdit):
    """
    A textedit with autocomplete
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._completer = None
        log_d('Instantiate CompleterTextEdit: OK')

    def setCompleter(self, c):
        if self._completer is not None:
            self._completer.activated.disconnect()

        self._completer = c

        c.setWidget(self)
        c.setCompletionMode(QCompleter.PopupCompletion)
        c.setCaseSensitivity(Qt.CaseInsensitive)
        c.activated.connect(self.insertCompletion)

    def completer(self):
        return self._completer

    def insertCompletion(self, completion):
        if self._completer.widget() is not self:
            return

        tc = self.textCursor()
        extra = len(completion) - len(self._completer.completionPrefix())
        tc.movePosition(QTextCursor.Left)
        tc.movePosition(QTextCursor.EndOfWord)
        tc.insertText(completion[-extra:])
        self.setTextCursor(tc)

    def textUnderCursor(self):
        tc = self.textCursor()
        tc.select(QTextCursor.WordUnderCursor)

        return tc.selectedText()

    def focusInEvent(self, e):
        if self._completer is not None:
            self._completer.setWidget(self)

        super().focusInEvent(e)

    def keyPressEvent(self, e):
        if self._completer is not None and self._completer.popup().isVisible():
            # The following keys are forwarded by the completer to the widget.
            if e.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Escape, Qt.Key_Tab, Qt.Key_Backtab):
                e.ignore()
                # Let the completer do default behavior.
                return

        is_shortcut = e.modifiers() == Qt.ControlModifier and e.key() == Qt.Key_E
        if self._completer is None or not is_shortcut:
            # Do not process the shortcut when we have a completer.
            super().keyPressEvent(e)

        ctrl_or_shift = e.modifiers() & (Qt.ControlModifier | Qt.ShiftModifier)
        if self._completer is None or (ctrl_or_shift and len(e.text()) == 0):
            return

        eow = "~!@#$%^&*()_+{}|:\"<>?,./;'[]\\-="
        has_modifier = (e.modifiers() != Qt.NoModifier) and not ctrl_or_shift
        completionPrefix = self.textUnderCursor()

        if not is_shortcut and (has_modifier or len(e.text()) == 0 or len(completionPrefix) < 3 or e.text()[-1] in eow):
            self._completer.popup().hide()
            return

        if completionPrefix != self._completer.completionPrefix():
            self._completer.setCompletionPrefix(completionPrefix)
            self._completer.popup().setCurrentIndex(self._completer.completionModel().index(0, 0))

        cr = self.cursorRect()
        cr.setWidth(self._completer.popup().sizeHintForColumn(
            0) + self._completer.popup().verticalScrollBar().sizeHint().width())
        if self._completer:
            self._completer.complete(cr)


class GCompleter(QCompleter):
    def __init__(self, parent=None, title=True, artist=True, tags=True):
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
    move_pos: pyqtBoundSignal = pyqtSignal(int, object)

    def __init__(self, chapter, parent=None):
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
        if chapter.title:
            self.chapter_lbl.setText(chapter.title)
        else:
            self.chapter_lbl.setText("Chapter " + str(chapter.number + 1))

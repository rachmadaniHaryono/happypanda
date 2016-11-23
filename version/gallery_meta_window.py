"""gallery meta window."""
import logging

from PyQt5.QtCore import (
    QPoint,
    Qt,
    QTimer,
)
from PyQt5.QtGui import (
    QBrush,
    QColor,
    QCursor,
)
from PyQt5.QtWidgets import (
    QDesktopWidget,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QScrollArea,
    QSizePolicy,
    QStackedLayout,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

try:
    from arrow_window import ArrowWindow
    from clicked_label import ClickedLabel
    from flow_layout import FlowLayout
    from line_frame import LineFrame
    from misc import create_animation
    from tag_text_button import TagTextButton
    import app_constants
    import utils
except ImportError:
    from .arrow_window import ArrowWindow
    from .clicked_label import ClickedLabel
    from .flow_layout import FlowLayout
    from .line_frame import LineFrame
    from .tag_text_button import TagTextButton
    from .misc import (
        create_animation,
        clearLayout,
    )
    from . import (
        app_constants,
        utils,
    )

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


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
            back_btn = TagTextButton('Back')
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
            self.g_chapters_lbl = TagTextButton('Chapters')
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
                            t = TagTextButton(search_widget=self.appwindow)
                        else:
                            t = TagTextButton(search_widget=self.appwindow, namespace=namespace)
                        t.setText(tag)
                        tags_lbls.addWidget(t)
                        t.setAutoFillBackground(True)
            self.tags_widget.adjustSize()

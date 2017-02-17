"""sidebar widget frame.

taken from misc_db.py.
"""
import logging

from PyQt5.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
    QStackedLayout,
    QVBoxLayout,
    QWidget,
)
from PyQt5.QtCore import (
    QEasingCurve,
    QSize,
)
from PyQt5.QtGui import (
    QIcon,
)

from . import app_constants
from .arrow_handle_widget import ArrowHandleWidget
from .gallery_artists_list_view import GalleryArtistsListView
from .gallery_lists_widget import GalleryListsWidget
from .misc import create_animation
from .tags_tree_view_widget import TagsTreeViewWidget

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class SideBarWidgetFrame(QFrame):
    """sidebar widget."""

    def __init__(self, parent):
        """init func."""
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.parent_widget = parent
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.MinimumExpanding)
        self.parent_widget
        self._widget_layout = QHBoxLayout(self)

        # widget stuff
        self._d_widget = QWidget(self)
        self._widget_layout.addWidget(self._d_widget)
        self.main_layout = QVBoxLayout(self._d_widget)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.arrow_handle = ArrowHandleWidget(self)
        self.arrow_handle.CLICKED.connect(self.slide)

        self._widget_layout.addWidget(self.arrow_handle)
        self.setContentsMargins(0, 0, -self.arrow_handle.width(), 0)

        self.show_all_galleries_btn = QPushButton("Show all galleries")
        self.show_all_galleries_btn.clicked.connect(
            lambda: parent.manga_list_view.sort_model.set_gallery_list())
        self.show_all_galleries_btn.clicked.connect(
            self.show_all_galleries_btn.hide)
        self.show_all_galleries_btn.hide()
        self.main_layout.addWidget(self.show_all_galleries_btn)
        self.main_buttons_layout = QHBoxLayout()
        self.main_layout.addLayout(self.main_buttons_layout)

        # buttons
        bgroup = QButtonGroup(self)
        bgroup.setExclusive(True)
        self.lists_btn = QPushButton("Lists")
        self.lists_btn.setCheckable(True)
        bgroup.addButton(self.lists_btn)
        self.artist_btn = QPushButton("Artists")
        self.artist_btn.setCheckable(True)
        bgroup.addButton(self.artist_btn)
        self.ns_tags_btn = QPushButton("NS && Tags")
        self.ns_tags_btn.setCheckable(True)
        bgroup.addButton(self.ns_tags_btn)
        self.lists_btn.setChecked(True)

        self.main_buttons_layout.addWidget(self.lists_btn)
        self.main_buttons_layout.addWidget(self.artist_btn)
        self.main_buttons_layout.addWidget(self.ns_tags_btn)

        # buttons contents
        self.stacked_layout = QStackedLayout()
        self.main_layout.addLayout(self.stacked_layout)

        # lists
        gallery_lists_dummy = QWidget(self)
        self.lists = GalleryListsWidget(self)
        create_new_list_btn = QPushButton()
        create_new_list_btn.setIcon(QIcon(app_constants.PLUS_ICON))
        create_new_list_btn.setIconSize(QSize(15, 15))
        create_new_list_btn.clicked.connect(
            lambda: self.lists.create_new_list())
        create_new_list_btn.adjustSize()
        create_new_list_btn.setFixedSize(
            create_new_list_btn.width(), create_new_list_btn.height())
        create_new_list_btn.setToolTip("Create a new list!")
        lists_l = QVBoxLayout(gallery_lists_dummy)
        lists_l.setContentsMargins(0, 0, 0, 0)
        lists_l.setSpacing(0)
        lists_l.addWidget(self.lists)
        lists_l.addWidget(create_new_list_btn)
        lists_index = self.stacked_layout.addWidget(gallery_lists_dummy)
        self.lists.GALLERY_LIST_CLICKED.connect(
            parent.manga_list_view.sort_model.set_gallery_list)
        self.lists.GALLERY_LIST_CLICKED.connect(
            self.show_all_galleries_btn.show)
        self.lists.GALLERY_LIST_REMOVED.connect(
            self.show_all_galleries_btn.click)
        self.lists_btn.clicked.connect(
            lambda: self.stacked_layout.setCurrentIndex(lists_index))
        self.show_all_galleries_btn.clicked.connect(self.lists.clearSelection)
        self.show_all_galleries_btn.clicked.connect(self.lists._reset_selected)

        # artists
        self.artists_list = GalleryArtistsListView(
            parent.manga_list_view.gallery_model, self)
        self.artists_list.artist_clicked.connect(
            lambda a: parent.search('artist:"{}"'.format(a)))
        artists_list_index = self.stacked_layout.addWidget(self.artists_list)
        self.artist_btn.clicked.connect(
            lambda: self.stacked_layout.setCurrentIndex(artists_list_index))
        self.show_all_galleries_btn.clicked.connect(
            self.artists_list.clearSelection)

        # ns_tags
        self.tags_tree = TagsTreeViewWidget(self)
        self.tags_tree.TAG_SEARCH.connect(parent.search)
        self.tags_tree.NEW_LIST.connect(self.lists.create_new_list)
        self.tags_tree.setHeaderHidden(True)
        self.show_all_galleries_btn.clicked.connect(
            self.tags_tree.clearSelection)
        self.tags_layout = QVBoxLayout(self.tags_tree)
        ns_tags_index = self.stacked_layout.addWidget(self.tags_tree)
        self.ns_tags_btn.clicked.connect(
            lambda: self.stacked_layout.setCurrentIndex(ns_tags_index))

        self.slide_animation = create_animation(self, "maximumSize")
        self.slide_animation.stateChanged.connect(self._slide_hide)
        self.slide_animation.setEasingCurve(QEasingCurve.InOutQuad)

    def _slide_hide(self, state):
        """slide hide."""
        self.sizeHint()
        if state == self.slide_animation.Stopped:
            if self.arrow_handle.current_arrow == self.arrow_handle.OUT:
                self._d_widget.hide()
        elif self.slide_animation.Running:
            if self.arrow_handle.current_arrow == self.arrow_handle.IN:
                if not self.parent_widget.current_manga_view.allow_sidebarwidget:
                    self.arrow_handle.current_arrow = self.arrow_handle.OUT
                    self.arrow_handle.update()
                else:
                    self._d_widget.show()

    def slide(self, state):
        """slide."""
        self.slide_animation.setEndValue(
            QSize(self.arrow_handle.width() * 2, self.height()))

        if state:
            self.slide_animation.setDirection(self.slide_animation.Forward)
            self.slide_animation.start()
        else:
            self.slide_animation.setDirection(self.slide_animation.Backward)
            self.slide_animation.start()

    def showEvent(self, event):  # NOQA
        """show event."""
        super().showEvent(event)
        if not app_constants.SHOW_SIDEBAR_WIDGET:
            self.arrow_handle.click()

    def _init_size(self, event=None):
        """init func."""
        h = self.parent_widget.height()
        self._max_width = 200
        self.updateGeometry()
        self.setMaximumWidth(self._max_width)
        self.slide_animation.setStartValue(QSize(self._max_width, h))

    def resizeEvent(self, event):  # NOQA
        """resize event."""
        self._init_size(event)
        return super().resizeEvent(event)

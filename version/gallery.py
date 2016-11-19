"""gallery module."""
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

import enum
import logging

from PyQt5.QtCore import (
    pyqtSignal,
    QModelIndex,
    QPoint,
    QSize,
    Qt,
    QTime,
    QTimer,
)
from PyQt5.QtWidgets import (
    QListView,
    QMessageBox,
    QScroller,
    QStackedLayout,
)

try:
    import app_constants
    import gallerydb
    import misc
    from common_view import CommonView
    from executors import Executors
    from gallery_model import GalleryModel
    from grid_delegate import GridDelegate
    from manga_table_view import MangaTableView
    from sort_filter_model import SortFilterModel
except ImportError:
    from . import (
        gallerydb,
        app_constants,
        misc,
    )
    from .common_view import CommonView
    from .executors import Executors
    from .gallery_model import GalleryModel
    from .grid_delegate import GridDelegate
    from .manga_table_view import MangaTableView
    from .sort_filter_model import SortFilterModel

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical

# attempt at implementing treemodel
# class TreeNode:
#   def __init__(self, parent, row):
#       self.parent = parent
#       self.row = row
#       self.subnodes = self._get_children()

#   def _get_children(self):
#       raise NotImplementedError()

# class GalleryInfoModel(QAbstractItemModel):
#   def __init__(self, parent=None):
#       super().__init__(parent)
#       self.root_nodes = self._get_root_nodes()

#   def _get_root_nodes(self):
#       raise NotImplementedError()

#   def index(self, row, column, parent):
#       if not parent.isValid():
#           return self.createIndex(row, column, self.root_nodes[row])
#       parent_node = parent.internalPointer()
#       return self.createIndex(row, column, parent_node[row])

#   def parent(self, index):
#       if not index.isValid():
#           return QModelIndex()

#       node = index.internalPointer()
#       if not node.parent:
#           return QModelIndex()
#       else:
#           return self.createIndex(node.parent.row, 0, node.parent)

#   def reset(self):
#       self.root_nodes = self._get_root_nodes()
#       super().resetInternalData()

#   def rowCount(self, parent = QModelIndex()):
#       if not parent.isValid():
#           return len(self.root_nodes)
#       node = parent.internalPointer()
#       return len(node.subnodes)


class MangaView(QListView):
    """Grid View."""

    STATUS_BAR_MSG = pyqtSignal(str)

    def __init__(self, model, v_type, filter_model=None, parent=None):
        """init func."""
        super().__init__(parent)
        self.parent_widget = parent
        self.view_type = v_type
        self.setViewMode(self.IconMode)
        self.setResizeMode(self.Adjust)
        self.setWrapping(True)
        # all items have the same size (perfomance)
        self.setUniformItemSizes(True)
        # improve scrolling
        self.setAutoScroll(True)
        self.setVerticalScrollMode(self.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setLayoutMode(self.Batched)
        self.setMouseTracking(True)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.viewport().setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(self.DragDrop)
        self.sort_model = filter_model if filter_model else SortFilterModel(self)
        self.manga_delegate = GridDelegate(parent, self)
        self.setItemDelegate(self.manga_delegate)
        self.setSpacing(app_constants.GRID_SPACING)
        self.setFlow(QListView.LeftToRight)
        self.setIconSize(QSize(self.manga_delegate.W, self.manga_delegate.H))
        self.setSelectionBehavior(self.SelectItems)
        self.setSelectionMode(self.ExtendedSelection)
        self.gallery_model = model
        self.sort_model.change_model(self.gallery_model)
        self.sort_model.sort(0)
        self.setModel(self.sort_model)
        self.doubleClicked.connect(lambda idx: idx.data(Qt.UserRole + 1).chapters[0].open())
        self.setViewportMargins(0, 0, 0, 0)

        self.gallery_window = misc.GalleryMetaWindow(parent if parent else self)
        self.gallery_window.arrow_size = (10, 10,)
        self.clicked.connect(lambda idx: self.gallery_window.show_gallery(idx, self))

        self.current_sort = app_constants.CURRENT_SORT
        if self.view_type == app_constants.ViewType.Duplicate:
            self.sort_model.setSortRole(GalleryModel.TIME_ROLE)
        else:
            self.sort(self.current_sort)
        if app_constants.DEBUG:
            def debug_print(a):
                g = a.data(Qt.UserRole + 1)
                try:
                    print(g)
                except:
                    print("{}".format(g).encode(errors='ignore'))
                # log_d(gallerydb.HashDB.gen_gallery_hash(g, 0, 'mid')['mid'])

            self.clicked.connect(debug_print)

        self.k_scroller = QScroller.scroller(self)
        self._scroll_speed_timer = QTimer(self)
        self._scroll_speed_timer.timeout.connect(self._calculate_scroll_speed)
        self._scroll_speed_timer.setInterval(500)  # ms
        self._old_scroll_value = 0
        self._scroll_zero_once = True
        self._scroll_speed = 0
        self._scroll_speed_timer.start()

    @property
    def scroll_speed(self):
        """scroll speed."""
        return self._scroll_speed

    def _calculate_scroll_speed(self):
        new_value = self.verticalScrollBar().value()
        self._scroll_speed = abs(self._old_scroll_value - new_value)
        self._old_scroll_value = new_value

        if self.verticalScrollBar().value() in (0, self.verticalScrollBar().maximum()):
            self._scroll_zero_once = True

        if self._scroll_zero_once:
            self.update()
            self._scroll_zero_once = False

        # update view if not scrolling
        if new_value < 400 and self._old_scroll_value > 400:
            self.update()

    def get_visible_indexes(self, column=0):
        """find all galleries in viewport."""
        gridW = self.manga_delegate.W + app_constants.GRID_SPACING * 2
        gridH = self.manga_delegate.H + app_constants.GRID_SPACING * 2
        region = self.viewport().visibleRegion()
        idx_found = []

        def idx_is_visible(idx):
            idx_rect = self.visualRect(idx)
            return region.contains(idx_rect) or region.intersects(idx_rect)

        # get first index
        first_idx = self.indexAt(QPoint(gridW // 2, 0))  # to get indexes on the way out of view
        if not first_idx.isValid():
            first_idx = self.indexAt(QPoint(gridW // 2, gridH // 2))

        if first_idx.isValid():
            nxt_idx = first_idx
            # now traverse items until index isn't visible
            while(idx_is_visible(nxt_idx)):
                idx_found.append(nxt_idx)
                nxt_idx = nxt_idx.sibling(nxt_idx.row() + 1, column)

        return idx_found

    def wheelEvent(self, event):
        """wheel event."""
        if self.gallery_window.isVisible():
            self.gallery_window.hide_animation.start()
        return super().wheelEvent(event)

    def mouseMoveEvent(self, event):
        """mouse move event."""
        self.gallery_window.mouseMoveEvent(event)
        return super().mouseMoveEvent(event)

    def keyPressEvent(self, event):
        """key press event."""
        if event.key() == Qt.Key_Return:
            s_idx = self.selectedIndexes()
            if s_idx:
                for idx in s_idx:
                    self.doubleClicked.emit(idx)
        elif event.modifiers() == Qt.ShiftModifier and event.key() == Qt.Key_Delete:
            CommonView.remove_selected(self, True)
        elif event.key() == Qt.Key_Delete:
            CommonView.remove_selected(self)
        return super().keyPressEvent(event)

    def favorite(self, index):
        """favorite."""
        assert isinstance(index, QModelIndex)
        gallery = index.data(Qt.UserRole + 1)
        if gallery.fav == 1:
            gallery.fav = 0
            # self.model().replaceRows([gallery], index.row(), 1, index)
            gallerydb.execute(gallerydb.GalleryDB.modify_gallery, True, gallery.id, {'fav': 0})
            self.gallery_model.CUSTOM_STATUS_MSG.emit("Unfavorited")
        else:
            gallery.fav = 1
            # self.model().replaceRows([gallery], index.row(), 1, index)
            gallerydb.execute(gallerydb.GalleryDB.modify_gallery, True, gallery.id, {'fav': 1})
            self.gallery_model.CUSTOM_STATUS_MSG.emit("Favorited")

    def del_chapter(self, index, chap_numb):
        """delete chapter."""
        gallery = index.data(Qt.UserRole + 1)
        if len(gallery.chapters) < 2:
            CommonView.remove_gallery(self, [index])
        else:
            msgbox = QMessageBox(self)
            msgbox.setText('Are you sure you want to delete:')
            msgbox.setIcon(msgbox.Question)
            msgbox.setInformativeText('Chapter {} of {}'.format(chap_numb + 1, gallery.title))
            msgbox.setStandardButtons(msgbox.Yes | msgbox.No)
            if msgbox.exec_() == msgbox.Yes:
                gallery.chapters.pop(chap_numb, None)
                self.gallery_model.replaceRows([gallery], index.row())
                gallerydb.execute(gallerydb.ChapterDB.del_chapter, True, gallery.id, chap_numb)

    def sort(self, name):
        """sort."""
        if not self.view_type == app_constants.ViewType.Duplicate:
            if name == 'title':
                self.sort_model.setSortRole(Qt.DisplayRole)
                self.sort_model.sort(0, Qt.AscendingOrder)
                self.current_sort = 'title'
            elif name == 'artist':
                self.sort_model.setSortRole(GalleryModel.ARTIST_ROLE)
                self.sort_model.sort(0, Qt.AscendingOrder)
                self.current_sort = 'artist'
            elif name == 'date_added':
                self.sort_model.setSortRole(GalleryModel.DATE_ADDED_ROLE)
                self.sort_model.sort(0, Qt.DescendingOrder)
                self.current_sort = 'date_added'
            elif name == 'pub_date':
                self.sort_model.setSortRole(GalleryModel.PUB_DATE_ROLE)
                self.sort_model.sort(0, Qt.DescendingOrder)
                self.current_sort = 'pub_date'
            elif name == 'times_read':
                self.sort_model.setSortRole(GalleryModel.TIMES_READ_ROLE)
                self.sort_model.sort(0, Qt.DescendingOrder)
                self.current_sort = 'times_read'
            elif name == 'last_read':
                self.sort_model.setSortRole(GalleryModel.LAST_READ_ROLE)
                self.sort_model.sort(0, Qt.DescendingOrder)
                self.current_sort = 'last_read'

    def contextMenuEvent(self, event):
        """context menu event."""
        CommonView.contextMenuEvent(self, event)

    def updateGeometries(self):
        """update geometries."""
        super().updateGeometries()
        self.verticalScrollBar().setSingleStep(app_constants.SCROLL_SPEED)


class MangaViews:
    """manga views."""

    manga_views = []

    @enum.unique
    class View(enum.Enum):
        List = 1
        Table = 2

    def __init__(self, v_type, parent, allow_sidebarwidget=False):
        """init func."""
        self.allow_sidebarwidget = allow_sidebarwidget
        self._delete_proxy_model = None

        self.view_type = v_type

        if v_type == app_constants.ViewType.Default:
            model = GalleryModel(app_constants.GALLERY_DATA, parent)
        elif v_type == app_constants.ViewType.Addition:
            model = GalleryModel(app_constants.GALLERY_ADDITION_DATA, parent)
        elif v_type == app_constants.ViewType.Duplicate:
            model = GalleryModel([], parent)

        # list view
        self.list_view = MangaView(model, v_type, parent=parent)
        self.list_view.sort_model.setup_search()
        self.sort_model = self.list_view.sort_model
        self.gallery_model = self.list_view.gallery_model
        # table view
        self.table_view = MangaTableView(v_type, parent)
        self.table_view.gallery_model = self.gallery_model
        self.table_view.sort_model = self.sort_model
        self.table_view.setModel(self.sort_model)
        self.table_view.setColumnWidth(app_constants.FAV, 20)
        self.table_view.setColumnWidth(app_constants.ARTIST, 200)
        self.table_view.setColumnWidth(app_constants.TITLE, 400)
        self.table_view.setColumnWidth(app_constants.TAGS, 300)
        self.table_view.setColumnWidth(app_constants.TYPE, 60)
        self.table_view.setColumnWidth(app_constants.CHAPTERS, 60)
        self.table_view.setColumnWidth(app_constants.LANGUAGE, 100)
        self.table_view.setColumnWidth(app_constants.LINK, 400)

        self.view_layout = QStackedLayout()
        # init the chapter view variables
        self.m_l_view_index = self.view_layout.addWidget(self.list_view)
        self.m_t_view_index = self.view_layout.addWidget(self.table_view)

        self.current_view = self.View.List
        self.manga_views.append(self)

        if v_type in (app_constants.ViewType.Default, app_constants.ViewType.Addition):
            self.sort_model.enable_drag = True

    def _delegate_delete(self):
        if self._delete_proxy_model:
            gs = [g for g in self.gallery_model._gallery_to_remove]
            self._delete_proxy_model._gallery_to_remove = gs
            self._delete_proxy_model.removeRows(
                self._delete_proxy_model.rowCount() - len(gs), len(gs))

    def set_delete_proxy(self, other_model):
        """set delete proxy."""
        self._delete_proxy_model = other_model
        self.gallery_model.rowsAboutToBeRemoved.connect(
            self._delegate_delete, Qt.DirectConnection)

    def add_gallery(self, gallery, db=False, record_time=False):  # NOQA
        if isinstance(gallery, (list, tuple)):
            for g in gallery:
                g.view = self.view_type
                if self.view_type != app_constants.ViewType.Duplicate:
                    g.state = app_constants.GalleryState.New
                if db:
                    gallerydb.execute(gallerydb.GalleryDB.add_gallery, True, g)
                else:
                    if not g.profile:
                        Executors.generate_thumbnail(g, on_method=g.set_profile)
            rows = len(gallery)
            self.list_view.gallery_model._gallery_to_add.extend(gallery)
            if record_time:
                g.qtime = QTime.currentTime()
        else:
            gallery.view = self.view_type
            if self.view_type != app_constants.ViewType.Duplicate:
                gallery.state = app_constants.GalleryState.New
            rows = 1
            self.list_view.gallery_model._gallery_to_add.append(gallery)
            if record_time:
                g.qtime = QTime.currentTime()
            if db:
                gallerydb.execute(gallerydb.GalleryDB.add_gallery, True, gallery)
            else:
                if not gallery.profile:
                    Executors.generate_thumbnail(gallery, on_method=gallery.set_profile)
        self.list_view.gallery_model.insertRows(self.list_view.gallery_model.rowCount(), rows)

    def replace_gallery(self, list_of_gallery, db_optimize=True):
        """Replace the view and DB with given list of gallery, at given position."""
        assert isinstance(
            list_of_gallery, (list, gallerydb.Gallery)), "Please pass a gallery to replace with"
        if isinstance(list_of_gallery, gallerydb.Gallery):
            list_of_gallery = [list_of_gallery]
        log_d('Replacing {} galleries'.format(len(list_of_gallery)))
        if db_optimize:
            gallerydb.execute(gallerydb.GalleryDB.begin, True)
        for gallery in list_of_gallery:
            kwdict = {
                'title': gallery.title,
                'profile': gallery.profile,
                'artist': gallery.artist,
                'info': gallery.info,
                'type': gallery.type,
                'language': gallery.language,
                'rating': gallery.rating,
                'status': gallery.status,
                'pub_date': gallery.pub_date,
                'tags': gallery.tags,
                'link': gallery.link,
                'series_path': gallery.path,
                'chapters': gallery.chapters,
                'exed': gallery.exed
            }

            gallerydb.execute(gallerydb.GalleryDB.modify_gallery, True, gallery.id, **kwdict)
        if db_optimize:
            gallerydb.execute(gallerydb.GalleryDB.end, True)

    def changeTo(self, idx):
        """change view."""
        self.view_layout.setCurrentIndex(idx)
        if idx == self.m_l_view_index:
            self.current_view = self.View.List
        elif idx == self.m_t_view_index:
            self.current_view = self.View.Table

    def get_current_view(self):
        """get current view."""
        if self.current_view == self.View.List:
            return self.list_view
        else:
            return self.table_view

    def fav_is_current(self):
        """fav is current."""
        if self.table_view.sort_model.current_view == self.table_view.sort_model.CAT_VIEW:
            return False
        return True

    def hide(self):
        """hide."""
        self.view_layout.currentWidget().hide()

    def show(self):
        """show."""
        self.view_layout.currentWidget().show()

if __name__ == '__main__':
    raise NotImplementedError("Unit testing not yet implemented")

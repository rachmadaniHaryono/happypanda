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
    Qt,
    QTime,
)
from PyQt5.QtWidgets import (
    QStackedLayout,
)

try:
    import app_constants
    import gallerydb
    from executors import Executors
    from gallery_model import GalleryModel
    from manga_table_view import MangaTableView
    from single_manga_view import SingleMangaView
except ImportError:
    from . import (
        gallerydb,
        app_constants,
    )
    from .executors import Executors
    from .gallery_model import GalleryModel
    from .manga_table_view import MangaTableView
    from .single_manga_view import SingleMangaView

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
        self.list_view = SingleMangaView(model, v_type, parent=parent)
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

"""single manga view."""
import logging

from PyQt5.QtCore import (
    pyqtSignal,
    QModelIndex,
    QPoint,
    QSize,
    Qt,
    QTimer,
)
from PyQt5.QtWidgets import (
    QListView,
    QMessageBox,
    QScroller,
)

try:
    import app_constants
    import gallerydb
    from common_view import CommonView, handle_keypress_event_on_manga_view
    from gallery_meta_window import GalleryMetaWindow
    from gallery_model import GalleryModel
    from grid_delegate import GridDelegate
    from sort_filter_model import SortFilterModel
    from utils import delegate_event
    from misc import (
        open_idx_data_first_chapter_when_double_clicked,
    )
except ImportError:
    from . import (
        gallerydb,
        app_constants,
    )
    from .common_view import CommonView, handle_keypress_event_on_manga_view
    from .gallery_meta_window import GalleryMetaWindow
    from .gallery_model import GalleryModel
    from .grid_delegate import GridDelegate
    from .sort_filter_model import SortFilterModel
    from .utils import delegate_event
    from .misc import (
        open_idx_data_first_chapter_when_double_clicked,
    )

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class SingleMangaView(QListView):
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
        self.doubleClicked.connect(open_idx_data_first_chapter_when_double_clicked)
        self.setViewportMargins(0, 0, 0, 0)

        self.gallery_window = GalleryMetaWindow(parent if parent else self)
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
        # mouseMoveEvent
        self.mouseMoveEvent = lambda event: delegate_event(
            attr=self.gallery_window.mouseMoveEvent, value=event, super_attr='mouseMoveEvent',
            event=event
        )

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

    def keyPressEvent(self, event):
        """key press event."""
        handle_keypress_event_on_manga_view(
            view_obj=self, event=event, selected_idx=self.selectedIndexes())
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

    @classmethod
    def _set_sort(cls, name, exp_name, role, sort_arg):
        """set sort variable.

        Args:
            name: Name.
            exp_name(str): Expected name.
            role: Sort role.
            sort_arg: Argument for sort func.

        Returns:
            bool: True if name is equal expected name.
        """
        if name == exp_name:
            cls.sort_model.setSortRole(role)
            cls.sort_model.sort(0, sort_arg)
            cls.current_sort = name
            return True
        return False

    def sort(self, name):
        """sort."""
        if self.view_type == app_constants.ViewType.Duplicate:
            return
        #
        kwargs = [
            {
                'name': name, 'exp_name': 'title', 'role': Qt.DisplayRole,
                'sort_arg': Qt.AscendingOrder
            },
            {
                'name': name, 'exp_name': 'artist', 'role': GalleryModel.ARTIST_ROLE,
                'sort_arg': Qt.AscendingOrder
            },
            {
                'name': name, 'exp_name': 'date_added', 'role': GalleryModel.DATE_ADDED_ROLE,
                'sort_arg': Qt.DescendingOrder
            },
            {
                'name': name, 'exp_name': 'pub_date', 'role': GalleryModel.PUB_DATE_ROLE,
                'sort_arg': Qt.DescendingOrder
            },
            {
                'name': name, 'exp_name': 'pub_date', 'role': GalleryModel.PUB_DATE_ROLE,
                'sort_arg': Qt.DescendingOrder
            },
            {
                'name': name, 'exp_name': 'times_read', 'role': GalleryModel.TIMES_READ_ROLE,
                'sort_arg': Qt.DescendingOrder
            },
            {
                'name': name, 'exp_name': 'last_read', 'role': GalleryModel.LAST_READ_ROLE,
                'sort_arg': Qt.DescendingOrder
            }
        ]
        for kwarg in kwargs:
            if self._set_sort(**kwarg):
                return
        log_i('Unknown name [{}]'.format(name))

    def contextMenuEvent(self, event):
        """context menu event."""
        CommonView.contextMenuEvent(self, event)

    def updateGeometries(self):
        """update geometries."""
        super().updateGeometries()
        self.verticalScrollBar().setSingleStep(app_constants.SCROLL_SPEED)

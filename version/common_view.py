"""common view module."""
import logging
import random

from PyQt5.QtCore import (
    Qt,
    QRectF,
)
from PyQt5.QtWidgets import (
    QListView,
    QMessageBox,
    QTableView,
)

try:
    import app_constants
    import gallerydb
    import misc
    from gallery_dialog_widget import GalleryDialogWidget
    from gallery_menu import GalleryMenu
except ImportError:
    from . import (
        gallerydb,
        app_constants,
        misc,
    )
    from .gallery_dialog_widget import GalleryDialogWidget
    from .gallery_menu import GalleryMenu

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


def handle_keypress_event_on_manga_view(view_obj, event, selected_idx):
    """handle key event on manga view.

    it will be used on:

    - SingleMangaView
    - MangaTableView
    """
    s_idx = selected_idx
    if event.key() == Qt.Key_Return and s_idx:
        list(map(view_obj.doubleClicked.emit, s_idx))
    elif event.key() == Qt.Key_Delete:
        if event.modifiers() == Qt.ShiftModifier:
            source = True
        else:
            source = False
        CommonView.remove_selected(view_obj, source=source)


class CommonView:
    """Contains identical view implentations."""

    @staticmethod
    def remove_selected(view_cls, source=False):
        """remove selected."""
        s_indexes = []
        if isinstance(view_cls, QListView):
            s_indexes = view_cls.selectedIndexes()
        elif isinstance(view_cls, QTableView):
            s_indexes = view_cls.selectionModel().selectedRows()

        CommonView.remove_gallery(view_cls, s_indexes, source)

    @staticmethod
    def remove_gallery(view_cls, index_list, local=False):
        """remove gallery."""
        # view_cls.sort_model.setDynamicSortFilter(False)
        msgbox = QMessageBox(view_cls)
        msgbox.setIcon(msgbox.Question)
        msgbox.setStandardButtons(msgbox.Yes | msgbox.No)
        if len(index_list) > 1:
            if not local:
                msg = 'Are you sure you want to remove {} selected galleries?'.format(
                    len(index_list))
            else:
                msg = (
                    'Are you sure you want to remove {} selected galleries and '
                    'their files/directories?'.format(len(index_list))
                )

            msgbox.setText(msg)
        else:
            if not local:
                msg = 'Are you sure you want to remove this gallery?'
            else:
                msg = 'Are you sure you want to remove this gallery and its file/directory?'
            msgbox.setText(msg)

        if msgbox.exec_() == msgbox.Yes:
            # view_cls.setUpdatesEnabled(False)
            gallery_list = []
            gallery_db_list = []
            log_i('Removing {} galleries'.format(len(index_list)))
            for index in index_list:
                gallery = index.data(Qt.UserRole + 1)
                gallery_list.append(gallery)
                log_i('Attempt to remove: {} by {}'.format(
                    gallery.title.encode(errors="ignore"), gallery.artist.encode(errors="ignore"))
                )
                if gallery.id:
                    gallery_db_list.append(gallery)
            gallerydb.execute(
                gallerydb.GalleryDB.del_gallery, True, gallery_db_list, local=local, priority=0)

            rows = len(gallery_list)
            view_cls.gallery_model._gallery_to_remove.extend(gallery_list)
            view_cls.gallery_model.removeRows(view_cls.gallery_model.rowCount() - rows, rows)

            # view_cls.STATUS_BAR_MSG.emit('Gallery removed!')
            # view_cls.setUpdatesEnabled(True)
        # view_cls.sort_model.setDynamicSortFilter(True)

    @staticmethod
    def find_index(view_cls, gallery_id, sort_model=False):
        """Find and returns the index associated with the gallery id."""
        index = None
        model = view_cls.sort_model if sort_model else view_cls.gallery_model
        rows = model.rowCount()
        for r in range(rows):
            indx = model.index(r, 0)
            m_gallery = indx.data(Qt.UserRole + 1)
            if m_gallery.id == gallery_id:
                index = indx
                break
        return index

    @staticmethod
    def open_random_gallery(view_cls):
        """open random gallery."""
        try:
            g = random.randint(0, view_cls.sort_model.rowCount() - 1)
        except ValueError:
            return
        indx = view_cls.sort_model.index(g, 1)
        chap_numb = 0
        if app_constants.OPEN_RANDOM_GALLERY_CHAPTERS:
            gallery = indx.data(Qt.UserRole + 1)
            b = len(gallery.chapters)
            if b > 1:
                chap_numb = random.randint(0, b - 1)

        CommonView.scroll_to_index(view_cls, view_cls.sort_model.index(indx.row(), 0))
        indx.data(Qt.UserRole + 1).chapters[chap_numb].open()

    @staticmethod
    def scroll_to_index(view_cls, idx, select=True):
        """scroll to index."""
        old_value = view_cls.verticalScrollBar().value()
        view_cls.setAutoScroll(False)
        view_cls.setUpdatesEnabled(False)
        view_cls.verticalScrollBar().setValue(0)
        idx_rect = view_cls.visualRect(idx)
        view_cls.verticalScrollBar().setValue(old_value)
        view_cls.setUpdatesEnabled(True)
        rect = QRectF(idx_rect)
        if app_constants.DEBUG:
            print("Scrolling to index:", rect.getRect())
        view_cls.k_scroller.ensureVisible(rect, 0, 0)
        if select:
            view_cls.setCurrentIndex(idx)
        view_cls.setAutoScroll(True)
        view_cls.update()

    @staticmethod  # NOQA
    def contextMenuEvent(view_cls, event):
        """context menu event."""
        grid_view = False
        table_view = False
        if isinstance(view_cls, QListView):
            grid_view = True
        elif isinstance(view_cls, QTableView):
            table_view = True

        handled = False
        index = view_cls.indexAt(event.pos())
        index = view_cls.sort_model.mapToSource(index)

        selected = False
        if table_view:
            s_indexes = view_cls.selectionModel().selectedRows()
        else:
            s_indexes = view_cls.selectedIndexes()
        select_indexes = []
        for idx in s_indexes:
            if idx.isValid() and idx.column() == 0:
                select_indexes.append(view_cls.sort_model.mapToSource(idx))
        if len(select_indexes) > 1:
            selected = True

        if index.isValid():
            if grid_view:
                if view_cls.gallery_window.isVisible():
                    view_cls.gallery_window.hide_animation.start()
                view_cls.manga_delegate.CONTEXT_ON = True
            if selected:
                menu = GalleryMenu(
                    view_cls, index, view_cls.sort_model, view_cls.parent_widget, select_indexes)
            else:
                menu = GalleryMenu(
                    view_cls, index, view_cls.sort_model, view_cls.parent_widget)
            menu.delete_galleries.connect(
                lambda s: CommonView.remove_gallery(view_cls, select_indexes, s))
            menu.edit_gallery.connect(CommonView.spawn_dialog)
            handled = True

        if handled:
            menu.exec_(event.globalPos())
            if grid_view:
                view_cls.manga_delegate.CONTEXT_ON = False
            event.accept()
            del menu
        else:
            event.ignore()

    @staticmethod
    def spawn_dialog(app_inst, gallery=None):
        """spawn dialog."""
        dialog = GalleryDialogWidget(app_inst, gallery)
        dialog.show()

"""gallery lists widget."""
import pickle
import logging

from PyQt5.QtWidgets import (
    QListWidget,
)
from PyQt5.QtCore import (
    Qt,
    pyqtSignal,
)
from PyQt5.QtGui import (
    QFont,
    QIcon,
)

try:
    import gallerydb
    import app_constants
    from custom_list_item import CustomListItem
    from gallery_list_context_menu import GalleryListContextMenu
    from gallery_list_edit import GalleryListEdit
    from list_delegate import ListDelegate
except ImportError:
    from .custom_list_item import CustomListItem
    from .gallery_list_context_menu import GalleryListContextMenu
    from .gallery_list_edit import GalleryListEdit
    from .list_delegate import ListDelegate
    from . import (
        app_constants,
        gallerydb,
    )

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class GalleryListsWidget(QListWidget):
    """gallery list."""

    CREATE_LIST_TYPE = CustomListItem.UserType + 1
    GALLERY_LIST_CLICKED = pyqtSignal(gallerydb.GalleryList)
    GALLERY_LIST_REMOVED = pyqtSignal()

    def __init__(self, parent):
        """init func."""
        super().__init__(parent)
        self.gallery_list_edit = GalleryListEdit(parent)
        self.gallery_list_edit.hide()
        self._g_list_icon = QIcon(app_constants.GLIST_PATH)
        self._font_selected = QFont(self.font())
        self._font_selected.setBold(True)
        self._font_selected.setUnderline(True)
        self.itemDoubleClicked.connect(self._item_double_clicked)
        self.setItemDelegate(ListDelegate(self))
        self.itemDelegate().closeEditor.connect(self._add_new_list)
        self.setEditTriggers(self.NoEditTriggers)
        self.viewport().setAcceptDrops(True)
        self._in_proccess_item = None
        self.current_selected = None
        self.gallery_list_edit.apply.connect(
            lambda: self._item_double_clicked(self.current_selected))
        self.setup_lists()

    def dragEnterEvent(self, event):  # NOQA
        """drag enter event."""
        if event.mimeData().hasFormat("list/gallery"):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):  # NOQA
        """drag move event."""
        item = self.itemAt(event.pos())
        self.clearSelection()
        if item:
            item.setSelected(True)
        event.accept()

    def dropEvent(self, event):  # NOQA
        """drop event."""
        galleries = []

        galleries = pickle.loads(event.mimeData().data("list/gallery").data())

        g_list_item = self.itemAt(event.pos())
        if galleries and g_list_item:
            txt = "galleries" if len(galleries) > 1 else "gallery"
            app_constants.NOTIF_BUBBLE.update_text(
                g_list_item.item.name, 'Added {} to list...'.format(txt), 5)
            log_i('Adding gallery to list')
            g_list_item.item.add_gallery(galleries)

        super().dropEvent(event)

    def _add_new_list(self, lineedit=None, hint=None, gallery_list=None):
        """add new list."""
        if not self._in_proccess_item.text():
            self.takeItem(self.row(self._in_proccess_item))
            return
        new_item = self._in_proccess_item
        if not gallery_list:
            new_list = gallerydb.GalleryList(new_item.text())
            new_list.add_to_db()
        else:
            new_list = gallery_list
        new_item.item = new_list
        new_item.setIcon(self._g_list_icon)
        self.sortItems()

    def create_new_list(self, name=None, gallery_list=None):
        """create new list."""
        new_item = CustomListItem()
        self._in_proccess_item = new_item
        new_item.setFlags(new_item.flags() | Qt.ItemIsEditable)
        new_item.setIcon(QIcon(app_constants.LIST_PATH))
        self.insertItem(0, new_item)
        if name:
            new_item.setText(name)
            self._add_new_list(gallery_list=gallery_list)
        else:
            self.editItem(new_item)

    def _item_double_clicked(self, item):
        """item double clicked."""
        if item:
            self._reset_selected()
            if item.item.filter:
                app_constants.NOTIF_BUBBLE.update_text(
                    item.item.name, "Updating list..", 5)
                gallerydb.execute(item.item.scan, True)
            self.GALLERY_LIST_CLICKED.emit(item.item)
            item.setFont(self._font_selected)
            self.current_selected = item

    def _reset_selected(self):
        """reset selected."""
        if self.current_selected:
            self.current_selected.setFont(self.font())

    def setup_lists(self):
        """setup list."""
        for g_l in app_constants.GALLERY_LISTS:
            if g_l.type == gallerydb.GalleryList.REGULAR:
                self.create_new_list(g_l.name, g_l)

    def contextMenuEvent(self, event):  # NOQA
        """context menu event."""
        item = self.itemAt(event.pos())
        if item and item.type() != self.CREATE_LIST_TYPE:
            menu = GalleryListContextMenu(item, self)
            menu.exec_(event.globalPos())
            event.accept()
            return
        event.ignore()

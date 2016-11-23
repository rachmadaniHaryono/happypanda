"""tags tree view widget."""
import logging

from PyQt5.QtWidgets import (
    QApplication,
    QMenu,
    QTreeWidget,
    QTreeWidgetItem,
)
from PyQt5.QtCore import (
    Qt,
    pyqtSignal,
)

try:
    import gallerydb
    import utils
except ImportError:
    from . import (
        gallerydb,
        utils,
    )

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class TagsTreeViewWidget(QTreeWidget):
    """tags tree view."""

    TAG_SEARCH = pyqtSignal(str)
    NEW_LIST = pyqtSignal(str, gallerydb.GalleryList)

    def __init__(self, parent):
        """init func."""
        super().__init__(parent)
        self.setSelectionBehavior(self.SelectItems)
        self.setSelectionMode(self.ExtendedSelection)
        self.clipboard = QApplication.clipboard()
        self.itemDoubleClicked.connect(
            lambda i: self.search_tags([i]) if i.parent() else None)

    def _convert_to_str(self, items):
        """convert to str."""
        tags = {}
        d_tags = []
        for item in items:
            ns_item = item.parent()
            if ns_item.text(0) == 'No namespace':
                d_tags.append(item.text(0))
                continue
            if ns_item.text(0) in tags:
                tags[ns_item.text(0)].append(item.text(0))
            else:
                tags[ns_item.text(0)] = [item.text(0)]

        search_txt = utils.tag_to_string(tags)
        d_search_txt = ''
        for x, d_t in enumerate(d_tags, 1):
            if x == len(d_tags):
                d_search_txt += '{}'.format(d_t)
            else:
                d_search_txt += '{}, '.format(d_t)
        final_txt = search_txt + ', ' + d_search_txt if search_txt else d_search_txt
        return final_txt

    def search_tags(self, items):
        """search tags."""
        self.TAG_SEARCH.emit(self._convert_to_str(items))

    def create_list(self, items):
        """create list."""
        g_list = gallerydb.GalleryList(
            "New List", filter=self._convert_to_str(items))
        g_list.add_to_db()

        self.NEW_LIST.emit(g_list.name, g_list)

    def contextMenuEvent(self, event):  # NOQA
        """context menu event."""
        handled = False
        selected = False
        s_items = self.selectedItems()

        if len(s_items) > 1:
            selected = True

        ns_count = 0
        for item in s_items:
            if not item.text(0).islower():
                ns_count += 1
        contains_ns = True if ns_count > 0 else False

        def copy(with_ns=False):
            if with_ns:
                ns_item = s_items[0].parent()
                ns = ns_item.text(0)
                tag = s_items[0].text(0)
                txt = "{}:{}".format(ns, tag)
                self.clipboard.setText(txt)
            else:
                item = s_items[0]
                self.clipboard.setText(item.text(0))

        if s_items:
            menu = QMenu(self)
            if not selected:
                copy_act = menu.addAction('Copy')
                copy_act.triggered.connect(copy)
                if not contains_ns:
                    if s_items[0].parent().text(0) != 'No namespace':
                        copy_ns_act = menu.addAction('Copy with namespace')
                        copy_ns_act.triggered.connect(lambda: copy(True))
            if not contains_ns:
                search_act = menu.addAction('Search')
                search_act.triggered.connect(lambda: self.search_tags(s_items))
                create_list_filter_act = menu.addAction(
                    'Create list with selected')
                create_list_filter_act.triggered.connect(
                    lambda: self.create_list(s_items))
            handled = True

        if handled:
            menu.exec_(event.globalPos())
            event.accept()
            del menu
        else:
            event.ignore()

    def setup_tags(self):
        """setup tags."""
        self.clear()
        tags = gallerydb.execute(gallerydb.TagDB.get_ns_tags, False)
        for ns in tags:
            top_item = QTreeWidgetItem(self)
            if ns == 'default':
                top_item.setText(0, 'No namespace')
            else:
                top_item.setText(0, ns)
            for tag in tags[ns]:
                child_item = QTreeWidgetItem(top_item)
                child_item.setText(0, tag)
        self.sortItems(0, Qt.AscendingOrder)

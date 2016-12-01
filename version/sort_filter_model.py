"""sort filter model."""
import logging
import pickle

from PyQt5.QtCore import (
    pyqtSignal,
    QByteArray,
    QMimeData,
    QSortFilterProxyModel,
    Qt,
)
from PyQt5.QtWidgets import (
    QMessageBox,
)

try:
    import app_constants
    from gallery_model import GalleryModel
    from gallery_search_obj import GallerySearchObject
except ImportError:
    from . import (
        app_constants,
    )
    from .gallery_model import GalleryModel
    from .gallery_search_obj import GallerySearchObject

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class SortFilterModel(QSortFilterProxyModel):
    """sort filter model."""

    ROWCOUNT_CHANGE = pyqtSignal()
    _DO_SEARCH = pyqtSignal(str, object)
    _CHANGE_SEARCH_DATA = pyqtSignal(list)
    _CHANGE_FAV = pyqtSignal(bool)
    _SET_GALLERY_LIST = pyqtSignal(object)

    HISTORY_SEARCH_TERM = pyqtSignal(str)
    # Navigate terms
    NEXT, PREV = range(2)
    # Views
    CAT_VIEW, FAV_VIEW = range(2)

    def __init__(self, parent):
        """init func."""
        super().__init__(parent)
        self.parent_widget = parent
        self._data = app_constants.GALLERY_DATA
        self._search_ready = False
        self.current_term = ''
        self.terms_history = []
        self.current_term_history = 0
        self.current_gallery_list = None
        self.current_args = []
        self.current_view = self.CAT_VIEW
        self.setDynamicSortFilter(True)
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.setSortLocaleAware(True)
        self.setSortCaseSensitivity(Qt.CaseInsensitive)
        self.enable_drag = False

    def navigate_history(self, direction=PREV):
        """navigate history."""
        new_term = ''
        if self.terms_history:
            if direction == self.NEXT:
                if self.current_term_history < len(self.terms_history) - 1:
                    self.current_term_history += 1
            elif direction == self.PREV:
                if self.current_term_history > 0:
                    self.current_term_history -= 1
            new_term = self.terms_history[self.current_term_history]
            if new_term != self.current_term:
                self.init_search(new_term, history=False)
        return new_term

    def set_gallery_list(self, g_list=None):
        """set gallery list."""
        self.current_gallery_list = g_list
        self._SET_GALLERY_LIST.emit(g_list)
        self.refresh()

    def _change_view(self, emit_value, current_view):
        """change view."""
        self._CHANGE_FAV.emit(emit_value)
        self.refresh()
        self.current_view = current_view

    def fav_view(self):
        """fav view."""
        self._change_view(emit_value=True, current_view=self.FAV_VIEW)

    def catalog_view(self):
        """catalog view."""
        self._change_view(emit_value=False, current_view=self.CAT_VIEW)

    def setup_search(self):
        """setup search."""
        if not self._search_ready:
            self.gallery_search = GallerySearchObject(self.sourceModel()._data)
            self.gallery_search.FINISHED.connect(self.invalidateFilter)
            self.gallery_search.FINISHED.connect(lambda: self.ROWCOUNT_CHANGE.emit())
            self.gallery_search.moveToThread(app_constants.GENERAL_THREAD)
            self._DO_SEARCH.connect(self.gallery_search.search)
            self._SET_GALLERY_LIST.connect(self.gallery_search.set_gallery_list)
            self._CHANGE_SEARCH_DATA.connect(self.gallery_search.set_data)
            self._CHANGE_FAV.connect(self.gallery_search.set_fav)
            self.sourceModel().rowsInserted.connect(self.refresh)
            self._search_ready = True

    def refresh(self):
        """refresh."""
        self._DO_SEARCH.emit(self.current_term, self.current_args)

    def init_search(self, term, args=None, **kwargs):
        """Receive a search term and initiates a search.

        args should be a list of Search enums
        """
        if not args:
            args = self.current_args
        history = kwargs.pop('history', True)
        if history:
            if len(self.terms_history) > 10:
                self.terms_history = self.terms_history[-10:]
            self.terms_history.append(term)

            self.current_term_history = len(self.terms_history) - 1
            if self.current_term_history < 0:
                self.current_term_history = 0

        self.current_term = term
        if not history:
            self.HISTORY_SEARCH_TERM.emit(term)
        self.current_args = args
        self._DO_SEARCH.emit(term, args)

    def filterAcceptsRow(self, source_row, parent_index):
        """filter acceprt row."""
        if self.sourceModel():
            index = self.sourceModel().index(source_row, 0, parent_index)
            if index.isValid():
                if self._search_ready:
                    gallery = index.data(Qt.UserRole + 1)
                    try:
                        return self.gallery_search.result[gallery.id]
                    except KeyError:
                        pass
                else:
                    return True
        return False

    def change_model(self, model):
        """change model."""
        self.setSourceModel(model)
        self._data = self.sourceModel()._data
        self._CHANGE_SEARCH_DATA.emit(self._data)
        self.refresh()

    def change_data(self, data):
        """change data."""
        self._CHANGE_SEARCH_DATA.emit(data)

    def status_b_msg(self, msg):
        """set status b message."""
        self.sourceModel().status_b_msg(msg)

    def canDropMimeData(self, data, action, row, coloumn, index):
        """can drop mime data."""
        return False
        if not data.hasFormat("list/gallery"):
            return False
        return True

    def dropMimeData(self, data, action, row, coloumn, index):
        """drop mime data."""
        if not self.canDropMimeData(data, action, row, coloumn, index):
            return False
        if action == Qt.IgnoreAction:
            return True

        # if the drop occured on an item
        if not index.isValid():
            return False

        g_list = pickle.loads(data.data("list/gallery").data())
        item_g = index.data(GalleryModel.GALLERY_ROLE)
        # ignore false positive
        for g in g_list:
            if g.id == item_g.id:
                return False

        txt = 'galleries' if len(g_list) > 1 else 'gallery'
        msg = QMessageBox(self.parent_widget)
        msg.setText(
            "Are you sure you want to merge the galleries into this gallery as chapter(s)?".format(
                txt
            )
        )
        msg.setStandardButtons(msg.Yes | msg.No)
        if msg.exec_() == msg.No:
            return False

        # TODO: finish this

        return True

    def mimeTypes(self):
        """mime type."""
        return ['list/gallery'] + super().mimeTypes()

    def mimeData(self, index_list):
        """mime data."""
        data = QMimeData()
        g_list = []
        for idx in index_list:
            g = idx.data(GalleryModel.GALLERY_ROLE)
            if g is not None:
                g_list.append(g)
        data.setData("list/gallery", QByteArray(pickle.dumps(g_list)))
        return data

    def flags(self, index):
        """flags."""
        default_flags = super().flags(index)

        if self.enable_drag:
            if (index.isValid()):
                return Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled | default_flags
            else:
                return Qt.ItemIsDropEnabled | default_flags
        return default_flags

    def supportedDragActions(self):
        """suported drag actions."""
        return Qt.ActionMask

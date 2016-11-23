"""gallery artits list view."""
import logging

from PyQt5.QtWidgets import (
    QListView,
)
from PyQt5.QtCore import (
    pyqtSignal,
)

try:
    import app_constants
    from unique_info_model import UniqueInfoModel
except ImportError:
    from .unique_info_model import UniqueInfoModel
    from . import app_constants

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class GalleryArtistsListView(QListView):
    """gallery artists list."""

    artist_clicked = pyqtSignal(str)

    def __init__(self, gallerymodel, parent=None):
        """init func."""
        super().__init__(parent)
        self.g_artists_model = UniqueInfoModel(
            gallerymodel, gallerymodel.ARTIST_ROLE, self)
        self.setModel(self.g_artists_model)
        self.setModelColumn(app_constants.ARTIST)
        self.g_artists_model.setSortRole(gallerymodel.ARTIST_ROLE)
        self.g_artists_model.sort(0)
        self.doubleClicked.connect(self._artist_clicked)
        self.ARTIST_ROLE = gallerymodel.ARTIST_ROLE

    def _artist_clicked(self, idx):
        """artist clicked."""
        if idx.isValid():
            self.artist_clicked.emit(idx.data(self.ARTIST_ROLE))

    def set_current_glist(self, g_list=None):
        """set current gallery list."""
        if g_list:
            self.g_artists_model.custom_filter = g_list
        else:
            self.g_artists_model.custom_filter = None
        self.g_artists_model.invalidate()

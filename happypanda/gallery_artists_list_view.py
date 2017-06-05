"""gallery artits list view."""
import structlog

from PyQt5.QtWidgets import (
    QListView,
)
from PyQt5.QtCore import (
    pyqtSignal,
    QIdentityProxyModel,
    QSortFilterProxyModel,
    Qt,
)

try:
    import app_constants
except ImportError:
    from . import app_constants

log = structlog.getLogger(__name__)


class NoTooltipModel(QIdentityProxyModel):
    """no tooltip model."""

    def __init__(self, model, parent=None):
        """init func."""
        super().__init__(parent)
        self.setSourceModel(model)

    def data(self, index, role=Qt.DisplayRole):
        """data."""
        if role == Qt.ToolTipRole:
            return None
        if role == Qt.DecorationRole:
            return app_constants.ARTIST_ICON
        return self.sourceModel().data(index, role)


class UniqueInfoModel(QSortFilterProxyModel):
    """unique info model.

    Args:
        gallerymodel: Gallery model.
        role: Role.
        parent (QtWidgets.QWidget): Parent widget.

    Attributes:
        _unique: Unique list.
        _unique_role: Unique role.
        custom_filter: Custom filter.
    """

    def __init__(self, gallerymodel, role, parent=None):
        """init."""
        super().__init__(parent)
        self.setSourceModel(NoTooltipModel(gallerymodel, parent))
        self._unique = set()
        self._unique_role = role
        self.custom_filter = None
        self.setDynamicSortFilter(True)

    def filterAcceptsRow(self, source_row, parent_index):  # NOQA
        """filter accepted row.

        Args:
            source_row (int): Source row.
            parent_index (QModelIndex): Parent index.
        """
        if self.sourceModel():
            idx = self.sourceModel().index(source_row, 0, parent_index)
            if idx.isValid():
                unique = idx.data(self._unique_role)
                if unique:
                    if unique not in self._unique:
                        if self.custom_filter is not None:
                            if not idx.data(Qt.UserRole + 1) in self.custom_filter:
                                return False
                        self._unique.add(unique)
                        return True
        return False

    def invalidate(self):
        """Invalidate."""
        self._unique.clear()
        super().invalidate()


class GalleryArtistsListView(QListView):
    """gallery artists list."""

    artist_clicked = pyqtSignal(str)

    def __init__(self, gallerymodel, parent=None):
        """init func."""
        super().__init__(parent)
        self.g_artists_model = UniqueInfoModel(gallerymodel, gallerymodel.ARTIST_ROLE, self)
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

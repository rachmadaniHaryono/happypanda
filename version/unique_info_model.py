"""unique info model."""
import logging

from PyQt5.QtCore import (
    QSortFilterProxyModel,
    Qt,
)

try:
    from no_tooltip_model import NoTooltipModel
except ImportError:
    from .no_tooltip_model import NoTooltipModel

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class UniqueInfoModel(QSortFilterProxyModel):
    """unique info model."""

    def __init__(self, gallerymodel, role, parent=None):
        """init func."""
        super().__init__(parent)
        self.setSourceModel(NoTooltipModel(gallerymodel, parent))
        self._unique = set()
        self._unique_role = role
        self.custom_filter = None
        self.setDynamicSortFilter(True)

    def filterAcceptsRow(self, source_row, parent_index):  # NOQA
        """filter accepted row."""
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
        """invalidate."""
        self._unique.clear()
        super().invalidate()

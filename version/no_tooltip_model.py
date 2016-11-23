"""no tooltip model."""
import logging

from PyQt5.QtCore import (
    QIdentityProxyModel,
    Qt,
)
from PyQt5.QtGui import (
    QPixmap,
)

try:
    import app_constants
except ImportError:
    from . import app_constants

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


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
            return QPixmap(app_constants.GARTIST_PATH)
        return self.sourceModel().data(index, role)

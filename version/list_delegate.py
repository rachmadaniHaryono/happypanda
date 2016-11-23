"""list delegate."""
import logging

from PyQt5.QtWidgets import (
    QStyledItemDelegate,
)
from PyQt5.QtCore import (
    QSize,
    Qt,
)

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class ListDelegate(QStyledItemDelegate):
    """list delegate."""

    def __init__(self, parent=None):
        """init func."""
        self.parent_widget = parent
        super().__init__(parent)
        self.create_new_list_txt = 'Create new list...'

    def sizeHint(self, option, index):  # NOQA
        """size hint."""
        size = super().sizeHint(option, index)
        if index.data(Qt.DisplayRole) == self.create_new_list_txt:
            return size
        return QSize(size.width(), size.height() * 2)

"""custom list item."""
import logging

from PyQt5.QtWidgets import (
    QListWidgetItem,
)

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class CustomListItem(QListWidgetItem):
    """CustomListItem."""

    def __init__(self, item=None, parent=None, txt='', type=QListWidgetItem.Type):
        """__init__."""
        super().__init__(txt, parent, type)
        self.item = item

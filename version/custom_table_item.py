"""custom table item."""
import logging

from PyQt5.QtWidgets import (
    QTableWidgetItem,
)

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class CustomTableItem(QTableWidgetItem):
    """CustomTableItem."""

    def __init__(self, item=None, txt='', type=QTableWidgetItem.Type):
        """__init__."""
        super().__init__(txt, type)
        self.item = item

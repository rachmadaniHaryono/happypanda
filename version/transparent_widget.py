"""transparent widget."""
import logging

from PyQt5.QtCore import (
    Qt,
)

try:
    from base_move_widget import BaseMoveWidget
except ImportError:
    from .base_move_widget import BaseMoveWidget

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class TransparentWidget(BaseMoveWidget):
    """TransparentWidget."""

    def __init__(self, parent=None, **kwargs):
        """__init__."""
        super().__init__(parent, **kwargs)
        self.setAttribute(Qt.WA_TranslucentBackground)

"""spacer widget."""
import logging

from PyQt5.QtWidgets import (
    QSizePolicy,
    QWidget,
)

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class SpacerWidget(QWidget):
    """To be used as a spacer.

    Default mode is both. Specify mode with string: v, h or both
    """

    def __init__(self, mode='both', parent=None):
        """__init__."""
        super().__init__(parent)
        if mode == 'h':
            self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        elif mode == 'v':
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        else:
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

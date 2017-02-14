"""line frame."""
import logging

from PyQt5.QtWidgets import QFrame


log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class LineFrame(QFrame):
    """'v' for vertical line or 'h' for horizontail line, color is hex string."""

    def __init__(self, orentiation, parent=None):
        """__init__."""
        super().__init__(parent)
        self.setFrameStyle(self.StyledPanel)
        if orentiation == 'v':
            self.setFrameShape(self.VLine)
        else:
            self.setFrameShape(self.HLine)
        self.setFrameShadow(self.Sunken)

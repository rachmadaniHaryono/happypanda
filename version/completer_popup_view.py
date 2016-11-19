"""completer popup view."""
import logging

from PyQt5.QtCore import (
    Qt,
)
from PyQt5.QtWidgets import (
    QListView,
)

try:
    from misc import create_animation
except ImportError:
    from .misc import create_animation

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class CompleterPopupView(QListView):
    """CompleterPopupView."""

    def __init__(self, *args, **kwargs):
        """__init__."""
        super().__init__(*args, **kwargs)

    def _setup(self):
        """_setup."""
        self.fade_animation = create_animation(self, 'windowOpacity')
        self.fade_animation.setDuration(200)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFrameStyle(self.StyledPanel)

    def showEvent(self, event):  # NOQA
        """showEvent."""
        self.setWindowOpacity(0)
        self.fade_animation.start()
        super().showEvent(event)

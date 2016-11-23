"""tag text button."""
import logging

from PyQt5.QtCore import (
    Qt,
)
from PyQt5.QtWidgets import (
    QPushButton,
)

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class TagTextButton(QPushButton):
    """TagText."""

    def __init__(self, *args, **kwargs):
        """__init__."""
        self.search_widget = kwargs.pop('search_widget', None)
        self.namespace = kwargs.pop('namespace', None)
        super().__init__(*args, **kwargs)
        if self.search_widget:
            if self.namespace:
                self.clicked.connect(lambda: self.search_widget.search(
                    '{}:{}'.format(self.namespace, self.text())))
            else:
                self.clicked.connect(
                    lambda: self.search_widget.search('{}'.format(self.text())))

    def enterEvent(self, event):
        """enterEvent."""
        if self.text():
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
        return super().enterEvent(event)

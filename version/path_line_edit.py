"""path line edit module."""
import logging

from PyQt5.QtCore import (
    Qt,
)
from PyQt5.QtGui import (
    QMouseEvent,
)
from PyQt5.QtWidgets import (
    QFileDialog,
    QLineEdit,
)

try:
    from app_constants import FILE_FILTER
except ImportError:
    from .app_constants import FILE_FILTER

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class PathLineEdit(QLineEdit):
    """A lineedit which open a filedialog on right/left click.

    Set dir to false if you want files.
    """

    def __init__(self, parent=None, dir=True, filters=FILE_FILTER):
        """__init__."""
        super().__init__(parent)
        self.folder = dir
        self.filters = filters
        self.setPlaceholderText('Right/Left-click to open folder explorer.')
        self.setToolTip('Right/Left-click to open folder explorer.')

    def openExplorer(self):
        """openExplorer."""
        if self.folder:
            path = QFileDialog.getExistingDirectory(self,
                                                    'Choose folder')
        else:
            path = QFileDialog.getOpenFileName(self,
                                               'Choose file', filter=self.filters)
            path = path[0]
        if len(path) != 0:
            self.setText(path)

    def mousePressEvent(self, event):
        """mousePressEvent."""
        assert isinstance(event, QMouseEvent)
        if len(self.text()) == 0:
            if event.button() == Qt.LeftButton:
                self.openExplorer()
            else:
                return super().mousePressEvent(event)
        if event.button() == Qt.RightButton:
            self.openExplorer()

        super().mousePressEvent(event)

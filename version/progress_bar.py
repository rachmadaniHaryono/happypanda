"""custom progress bar."""
from PyQt5.QtCore import (
    pyqtSignal,
)
from PyQt5.QtWidgets import (
    QProgressBar,
)


class ProgressBar(QProgressBar):
    """custom progress bar."""

    reached_maximum = pyqtSignal()

    def __init__(self, parent=None):
        """__init__."""
        super().__init__(parent)

    def setValue(self, v):
        """set value.

        Args:
            value: Value.
        """
        if v == self.maximum():
            self.reached_maximum.emit()
        return super().setValue(v)

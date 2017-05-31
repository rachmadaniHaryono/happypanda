"""line edit."""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLineEdit


class LineEdit(QLineEdit):
    """Custom Line Edit which sacrifices contextmenu for selectAll."""

    def __init__(self, parent=None):
        """__init__."""
        super().__init__(parent)

    def mousePressEvent(self, event):
        """mousePressEvent."""
        if event.button() == Qt.RightButton:
            self.selectAll()
        else:
            super().mousePressEvent(event)

    def contextMenuEvent(self, QContextMenuEvent):
        """contextMenuEvent."""
        pass

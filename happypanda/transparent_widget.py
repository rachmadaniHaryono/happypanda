"""transparent widget."""
from PyQt5.QtCore import Qt

try:
    from base_move_widget import BaseMoveWidget
except ImportError:
    from .base_move_widget import BaseMoveWidget


class TransparentWidget(BaseMoveWidget):
    """TransparentWidget.

    Args:
        parent (QtWidgets.QWidget): Parent widget.
    """

    def __init__(self, parent=None, **kwargs):
        """__init__."""
        super().__init__(parent, **kwargs)
        self.setAttribute(Qt.WA_TranslucentBackground)

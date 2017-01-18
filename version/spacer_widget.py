"""spacer widget."""
from PyQt5.QtWidgets import (
    QSizePolicy,
    QWidget,
)


class SpacerWidget(QWidget):
    """To be used as a spacer.

    Default mode is both. Specify mode with string: v, h or both

    Attributes:
        mode: Mode used for this widget.
        parent (QtWidgets.QWidget): Parent widget.
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

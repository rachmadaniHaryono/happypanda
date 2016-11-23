"""base user choice."""
import logging

from PyQt5.QtCore import (
    pyqtSignal,
    Qt,
)
from PyQt5.QtWidgets import (
    QDialog,
    QFormLayout,
    QFrame,
    QVBoxLayout,
)

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class BaseUserChoice(QDialog):
    """BaseUserChoice."""

    USER_CHOICE = pyqtSignal(object)

    def __init__(self, parent, **kwargs):
        """__init__."""
        super().__init__(parent, **kwargs)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setAttribute(Qt.WA_TranslucentBackground)
        main_widget = QFrame(self)
        layout = QVBoxLayout(self)
        layout.addWidget(main_widget)
        self.main_layout = QFormLayout(main_widget)

    def accept(self, choice):
        """accept."""
        self.USER_CHOICE.emit(choice)
        super().accept()

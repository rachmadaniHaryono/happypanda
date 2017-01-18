"""base user choice."""
import sys
import logging

from PyQt5 import QtWidgets
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
    """BaseUserChoice.

    Attributes:
        USER_CHOICE (pyqtSignal): Signal for user choice.
    """

    USER_CHOICE = pyqtSignal(object)

    def __init__(self, parent, **kwargs):
        """init."""
        super().__init__(parent, **kwargs)

        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setAttribute(Qt.WA_TranslucentBackground)

        main_widget = QFrame(self)
        layout = QVBoxLayout(self)
        layout.addWidget(main_widget)
        self.main_layout = QFormLayout(main_widget)

    def accept(self, choice):
        """accept.

        Args:
            choice: Accepted choice.
        """
        self.USER_CHOICE.emit(choice)
        super().accept()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    parent_widget = QtWidgets.QWidget()
    dialog = BaseUserChoice(parent=parent_widget)
    dialog.show()

    sys.exit(app.exec_())

"""app dialog."""
import logging

from PyQt5.QtCore import (
    pyqtSignal,
    Qt,
)
from PyQt5.QtWidgets import (
    QLabel,
    QProgressBar,
    QVBoxLayout,
)

try:
    from base_popup import BasePopup
    from utils import delegate_event
except ImportError:
    from .base_popup import BasePopup
    from .utils import delegate_event

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class AppDialog(BasePopup):
    """AppDialog."""

    # modes
    PROGRESS, MESSAGE = range(2)
    closing_down = pyqtSignal()

    def __init__(self, parent, mode=PROGRESS):
        """__init__."""
        self.mode = mode
        if mode == self.MESSAGE:
            super().__init__(parent, flags=Qt.Dialog)
        else:
            super().__init__(parent)
        self.parent_widget = parent
        main_layout = QVBoxLayout()

        self.info_lbl = QLabel()
        self.info_lbl.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.info_lbl)
        if mode == self.PROGRESS:
            self.info_lbl.setText(
                "Updating your galleries to newest version...")
            self.info_lbl.setWordWrap(True)

            class progress(QProgressBar):
                """progress."""

                reached_maximum = pyqtSignal()

                def __init__(self, parent=None):
                    """__init__."""
                    super().__init__(parent)

                def setValue(self, v):
                    """setValue."""
                    if v == self.maximum():
                        self.reached_maximum.emit()
                    return super().setValue(v)

            self.prog = progress(self)

            self.prog.reached_maximum.connect(self.close)
            main_layout.addWidget(self.prog)
            self.note_info = QLabel(
                "Note: This popup will close itself when everything is ready")
            self.note_info.setAlignment(Qt.AlignCenter)
            self.restart_info = QLabel(
                "Please wait.. It is safe to restart if there is no sign of progress.")
            self.restart_info.setAlignment(Qt.AlignCenter)
            main_layout.addWidget(self.note_info)
            main_layout.addWidget(self.restart_info)
        elif mode == self.MESSAGE:
            self.info_lbl.setText(
                "<font color='red'>An exception has ben encountered.\n"
                "Contact the developer to get this fixed.\n"
                "Stability from this point onward cannot be guaranteed.</font>"
            )
            self.setWindowTitle("It was too big!")

        self.main_widget.setLayout(main_layout)
        self.adjustSize()
        # showEvent
        self.showEvent = lambda event: delegate_event(
            attr=self.parent_widget.setEnabled, value=False, super_attr='showEvent', event=event)

    def closeEvent(self, event):
        """closeEvent."""
        self.parent_widget.setEnabled(True)
        if self.mode == self.MESSAGE:
            self.closing_down.emit()
            return super().closeEvent(event)
        else:
            return super().closeEvent(event)

    def init_restart(self):
        """init_restart."""
        if self.mode == self.PROGRESS:
            self.prog.hide()
            self.note_info.hide()
            self.restart_info.hide()
            log_i('Application requires restart')
            self.note_info.setText("Application requires restart!")

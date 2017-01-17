"""app dialog."""
import sys
import logging

import click
from PyQt5 import QtWidgets
from PyQt5.QtCore import (
    pyqtSignal,
    Qt,
)
from PyQt5.QtWidgets import (
    QLabel,
    QVBoxLayout,
)

try:
    from base_popup import BasePopup
    from progress_bar import ProgressBar
except ImportError:
    from .base_popup import BasePopup
    from .progress_bar import ProgressBar

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class AppDialog(BasePopup):
    """AppDialog.

    Args:
        parent (QtWidgets.QWidget): Parent widget.
        mode: Mode of Popup, use class attribute, e.g. PROGRESS, MESSAGE.
    """

    # modes
    PROGRESS, MESSAGE = range(2)
    closing_down = pyqtSignal()

    def __init__(self, parent, mode=PROGRESS):
        """__init__."""
        if mode == self.MESSAGE:
            super().__init__(parent, flags=Qt.Dialog)
        else:
            super().__init__(parent)
        self.mode = mode
        self.parent_widget = parent

        main_layout = QVBoxLayout()
        self.info_lbl = QLabel()
        self.info_lbl.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.info_lbl)

        if mode == self.PROGRESS:
            self.info_lbl.setText(
                "Updating your galleries to newest version...")
            self.info_lbl.setWordWrap(True)

            self.prog = ProgressBar(parent=self)
            self.prog.reached_maximum.connect(self.close)
            main_layout.addWidget(self.prog)

            self.note_info = QLabel(
                "Note: This popup will close itself when everything is ready")
            self.note_info.setAlignment(Qt.AlignCenter)
            main_layout.addWidget(self.note_info)

            self.restart_info = QLabel(
                "Please wait.. It is safe to restart if there is no sign of progress.")
            self.restart_info.setAlignment(Qt.AlignCenter)
            main_layout.addWidget(self.restart_info)

        elif mode == self.MESSAGE:
            self.info_lbl.setText(
                "<font color='red'>An exception has ben encountered.<br>"
                "Contact the developer to get this fixed.<br>"
                "Stability from this point onward cannot be guaranteed.</font>"
            )
            self.setWindowTitle("It was too big!")

        self.main_widget.setLayout(main_layout)
        self.adjustSize()

    def closeEvent(self, event):
        """close event.

        Args:
            event (QtGui.QCloseEvent): Close event.
        """
        self.parent_widget.setEnabled(True)
        if self.mode == self.MESSAGE:
            self.closing_down.emit()
        return super().closeEvent(event)

    def showEvent(self, event):
        """show event.

        Args:
            event (QtGui.QShowEvent): Show event.
        """
        self.parent_widget.setEnabled(False)
        return super().showEvent(event)

    def init_restart(self):
        """init restart."""
        if self.mode == self.PROGRESS:
            self.prog.hide()
            self.note_info.hide()
            self.restart_info.hide()
            self.note_info.setText("Application requires restart!")
            log_i('Application requires restart')


@click.command()
@click.option('--mode', type=click.Choice(['progress', 'message']))
def main(mode):
    """main func."""
    app = QtWidgets.QApplication(sys.argv)

    widget = QtWidgets.QWidget()
    if mode == 'progress':
        dialog = AppDialog(parent=widget, mode=AppDialog.PROGRESS)
    elif mode == 'message':
        dialog = AppDialog(parent=widget, mode=AppDialog.MESSAGE)
    dialog.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

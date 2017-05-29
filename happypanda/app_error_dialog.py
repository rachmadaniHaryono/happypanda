#!/usr/bin/python3
"""Widget to show error."""

import sys
from PyQt5.QtGui import (
    QGuiApplication
)
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


class AppErrorDialog(QWidget):
    """Error dialog widget."""

    def __init__(self, parent=None, traceback_info=None):
        """init method."""
        if parent is not None:
            super().__init__(parent)
        else:
            super().__init__()

        self.init_ui(traceback_info)

    def init_ui(self, traceback_info):
        """init ui method."""
        layout = QVBoxLayout()
        self.general_err_msg = QLabel(
            "An exception has ben encountered.<br>"
            "Contact the developer to get this fixed.<br>"
            "Stability from this point onward cannot be guaranteed."
        )
        self.stacked_widget = QStackedWidget()
        subwidget = QWidget()
        subwidget_layout = QVBoxLayout()
        self.show_btn = QPushButton('Show text', self)
        self.hide_btn = QPushButton('Hide text', self)
        self.msg = QLabel(traceback_info)
        self.copy_btn = QPushButton('Copy to clipboard', self)
        self.clipboard = QGuiApplication.clipboard()

        subwidget_layout.addWidget(self.hide_btn)
        subwidget_layout.addWidget(self.msg)
        subwidget.setLayout(subwidget_layout)
        self.stacked_widget.addWidget(self.show_btn)
        self.stacked_widget.addWidget(subwidget)

        layout.addWidget(self.general_err_msg)
        layout.addWidget(self.stacked_widget)
        layout.addWidget(self.copy_btn)
        self.setLayout(layout)

        self.show_btn.clicked.connect(self.toggle_stacked_widget)
        self.hide_btn.clicked.connect(self.toggle_stacked_widget)
        self.copy_btn.clicked.connect(lambda: self.clipboard.setText(traceback_info))

    def toggle_stacked_widget(self):
        """toggle stacked widget."""
        current_idx = self.stacked_widget.currentIndex()
        if int(current_idx) == 0:
            self.stacked_widget.setCurrentIndex(1)
        else:
            self.stacked_widget.setCurrentIndex(0)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = AppErrorDialog(traceback_info='test')
    ex.show()
    sys.exit(app.exec_())

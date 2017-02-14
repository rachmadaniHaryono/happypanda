"""db Overview widget."""
from PyQt5.QtWidgets import (
    QListWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from PyQt5.QtCore import (
    Qt,
    pyqtSignal,
)
from PyQt5.QtGui import QIcon

try:
    import app_constants
except ImportError:
    from . import (
        app_constants,
    )


class DBOverview(QWidget):
    """db overview.

    Args:
        parent (QtWidgets.QWidget): Parent widget.
        window (bool): Use window.

    Attributes:
        about_to_close (pyqtSignal): Signal when widget is about to close.
        parent (QtWidgets.QWidget): Parent widget.
        tags_stats (QListWidget): Tags status.
        about_db (QWidget):  Widget about database.
    """

    about_to_close = pyqtSignal()

    def __init__(self, parent, window=False):
        """init func."""
        if window:
            super().__init__(None, Qt.Window)
        else:
            super().__init__(parent)

        self.setAttribute(Qt.WA_DeleteOnClose)

        self.parent_widget = parent

        main_layout = QVBoxLayout(self)
        tabbar = QTabWidget(self)
        main_layout.addWidget(tabbar)

        # Tags stats
        self.tags_stats = QListWidget(self)
        tabbar.addTab(self.tags_stats, 'Statistics')
        tabbar.setTabEnabled(1, False)

        # About AD
        self.about_db = QWidget(self)
        tabbar.addTab(self.about_db, 'DB Info')
        tabbar.setTabEnabled(2, False)

        self.resize(300, 600)
        self.setWindowTitle('DB Overview')
        self.setWindowIcon(QIcon(app_constants.APP_ICO_PATH))

    def setup_stats(self):
        """setup stats."""
        pass

    def setup_about_db(self):
        """setup about db."""
        pass

    def closeEvent(self, event):  # NOQA
        """close event."""
        self.about_to_close.emit()
        return super().closeEvent(event)

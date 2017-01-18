"""system tray."""
from PyQt5.QtWidgets import QSystemTrayIcon

try:
    import app_constants
except ImportError:
    from . import app_constants


class SystemTray(QSystemTrayIcon):
    """SystemTray.

    Pass True to minimized arg in showMessage method to only
    show message if application is minimized.

    Args:
        parent (QtWidgets.QWidget): Parent widget.
        icon: Icon.

    Attributes:
        parent (QtWidgets.QWidget): Parent widget.
    """

    def __init__(self, icon, parent=None):
        """__init__."""
        super().__init__(icon, parent=None)
        self.parent_widget = parent

    def showMessage(self, title, msg, icon=QSystemTrayIcon.Information,
                    msecs=10000, minimized=False):
        """show message.

        Args:
            title: Title.
            msg: Message.
            icon: Icon.
            msecs (int): Duration to show message in milliseconds
            minimized (bool): Minimize.
        """
        # NOTE: Crashes on linux
        # TODO: Fix this!!
        if not app_constants.OS_NAME == "linux":
            if minimized:
                if self.parent_widget.isMinimized() or not self.parent_widget.isActiveWindow():
                    return super().showMessage(title, msg, icon, msecs)
            else:
                return super().showMessage(title, msg, icon, msecs)

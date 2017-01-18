"""tag text button."""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QPushButton


class TagTextButton(QPushButton):
    """Tags text button.

    Args:
        search_widget: Search widget.
        namespace: Tag's namespace.

    Attributes:
        search_widget: Search widget.
        namespace: Tag's namespace.

    """

    def __init__(self, *args, **kwargs):
        """init method."""
        self.search_widget = kwargs.pop('search_widget', None)
        self.namespace = kwargs.pop('namespace', None)
        super().__init__(*args, **kwargs)
        if self.search_widget:
            if self.namespace:
                self.clicked.connect(lambda: self.search_widget.search(
                    '{}:{}'.format(self.namespace, self.text())))
            else:
                self.clicked.connect(
                    lambda: self.search_widget.search('{}'.format(self.text())))

    def enterEvent(self, event):
        """Enter event.

        Args:
            event (QtGui.QEnterEvent): Enter event.
        """
        if self.text():
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
        return super().enterEvent(event)

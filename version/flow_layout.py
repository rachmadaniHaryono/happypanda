"""flow layout."""
import logging

from PyQt5.QtCore import (
    QPoint,
    QRect,
    QSize,
    Qt,
)
from PyQt5.QtWidgets import (
    QLayout,
    QSizePolicy,
)

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class FlowLayout(QLayout):
    """FlowLayout."""

    def __init__(self, parent=None, margin=0, spacing=-1):
        """__init__."""
        super(FlowLayout, self).__init__(parent)

        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)

        self.setSpacing(spacing)

        self.itemList = []

    def __del__(self):
        """__del__."""
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        """addItem."""
        self.itemList.append(item)

    def count(self):
        """count."""
        return len(self.itemList)

    # to keep it in style with the others..
    def rowCount(self):
        """rowCount."""
        return self.count()

    def itemAt(self, index):
        """itemAt."""
        if index >= 0 and index < len(self.itemList):
            return self.itemList[index]

        return None

    def takeAt(self, index):
        """takeAt."""
        if index >= 0 and index < len(self.itemList):
            return self.itemList.pop(index)

        return None

    def expandingDirections(self):
        """expandingDirections."""
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self):
        """hasHeightForWidth."""
        return True

    def heightForWidth(self, width):
        """heightForWidth."""
        height = self.doLayout(QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        """setGeometry."""
        super(FlowLayout, self).setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        """sizeHint."""
        return self.minimumSize()

    def minimumSize(self):
        """minimumSize."""
        size = QSize()

        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())

        margin, _, _, _ = self.getContentsMargins()

        size += QSize(2 * margin, 2 * margin)
        return size

    def doLayout(self, rect, testOnly):
        """doLayout."""
        x = rect.x()
        y = rect.y()
        lineHeight = 0

        for item in self.itemList:
            wid = item.widget()
            spaceX = self.spacing() + wid.style().layoutSpacing(
                QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Horizontal)
            spaceY = self.spacing() + wid.style().layoutSpacing(
                QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Vertical)
            nextX = x + item.sizeHint().width() + spaceX
            if nextX - spaceX > rect.right() and lineHeight > 0:
                x = rect.x()
                y = y + lineHeight + spaceY
                nextX = x + item.sizeHint().width() + spaceX
                lineHeight = 0

            if not testOnly:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = nextX
            lineHeight = max(lineHeight, item.sizeHint().height())

        return y + lineHeight - rect.y()

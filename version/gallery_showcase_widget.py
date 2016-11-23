"""gallery showcase widget."""
import logging

from PyQt5.QtCore import (
    pyqtSignal,
    Qt,
)
from PyQt5.QtGui import (
    QBrush,
    QColor,
    QPainter,
    QPixmap,
)
from PyQt5.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QWidget,
)

try:
    import app_constants
    import gallerydb
except ImportError:
    from . import (
        app_constants,
        gallerydb,
    )

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class GalleryShowcaseWidget(QWidget):
    """Pass a gallery or set a gallery via -> set_gallery."""

    double_clicked = pyqtSignal(gallerydb.Gallery)

    def __init__(self, gallery=None, parent=None, menu=None):
        """__init__."""
        super().__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.main_layout = QVBoxLayout(self)
        self.parent_widget = parent
        if menu:
            menu.gallery_widget = self
        self._menu = menu
        self.gallery = gallery
        self.extra_text = QLabel()
        self.profile = QLabel(self)
        self.profile.setAlignment(Qt.AlignCenter)
        self.text = QLabel(self)
        self.font_M = self.text.fontMetrics()
        self.main_layout.addWidget(self.extra_text)
        self.extra_text.hide()
        self.main_layout.addWidget(self.profile)
        self.main_layout.addWidget(self.text)
        self.h = 0
        self.w = 0
        if gallery:
            self.h = 220
            self.w = 143
            self.set_gallery(gallery, (self.w, self.h))

        self.resize(self.w, self.h)
        self.setMouseTracking(True)

    @property
    def menu(self):
        """menu."""
        return self._menu

    @menu.setter
    def contextmenu(self, new_menu):
        """contextmenu."""
        new_menu.gallery_widget = self
        self._menu = new_menu

    def set_pixmap(self, gallery, img):
        """set_pixmap."""
        self.profile.setPixmap(QPixmap.fromImage(img))

    def set_gallery(self, gallery, size=app_constants.THUMB_SMALL):
        """set_gallery."""
        assert isinstance(size, (list, tuple))
        self.w = size[0]
        self.h = size[1]
        self.gallery = gallery
        img = gallery.get_profile(
            app_constants.ProfileType.Small, self.set_pixmap)
        if img:
            self.profile.setPixmap(QPixmap.fromImage(img))
        title = self.font_M.elidedText(gallery.title, Qt.ElideRight, self.w)
        artist = self.font_M.elidedText(gallery.artist, Qt.ElideRight, self.w)
        self.text.setText("{}\n{}".format(title, artist))
        self.setToolTip("{}\n{}".format(gallery.title, gallery.artist))
        self.resize(self.w, self.h + 50)

    def paintEvent(self, event):
        """paintEvent."""
        painter = QPainter(self)
        if self.underMouse():
            painter.setBrush(QBrush(QColor(164, 164, 164, 120)))
            painter.drawRect(
                self.text.pos().x() - 2, self.profile.pos().y() - 5,
                self.text.width() + 2, self.profile.height() + self.text.height() + 12
            )
        super().paintEvent(event)

    def enterEvent(self, event):
        """enterEvent."""
        self.update()
        return super().enterEvent(event)

    def leaveEvent(self, event):
        """leaveEvent."""
        self.update()
        return super().leaveEvent(event)

    def mouseDoubleClickEvent(self, event):
        """mouseDoubleClickEvent."""
        self.double_clicked.emit(self.gallery)
        return super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event):
        """contextMenuEvent."""
        if self._menu:
            self._menu.exec_(event.globalPos())
            event.accept()
        else:
            event.ignore()

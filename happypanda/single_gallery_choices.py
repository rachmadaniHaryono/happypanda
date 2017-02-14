"""single gallery choices."""
import logging

from PyQt5.QtCore import (
    pyqtSignal,
    Qt,
)
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QVBoxLayout,
)

try:
    from base_popup import BasePopup
    from custom_list_item import CustomListItem
    from gallery_showcase_widget import GalleryShowcaseWidget
except ImportError:
    from .base_popup import BasePopup
    from .custom_list_item import CustomListItem
    from .gallery_showcase_widget import GalleryShowcaseWidget

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class SingleGalleryChoices(BasePopup):
    """SingleGalleryChoices.

    Represent a single gallery with a list of choices below.
    Pass a gallery and a list of tuple/list where the first index is a string in each
    if text is passed, the text will be shown alongside gallery, else gallery be centered
    """

    USER_CHOICE = pyqtSignal(object)

    def __init__(self, gallery, tuple_first_idx, text=None, parent=None):
        """__init__."""
        super().__init__(parent, flags=Qt.Dialog | Qt.FramelessWindowHint)
        main_layout = QVBoxLayout()
        self.main_widget.setLayout(main_layout)
        g_showcase = GalleryShowcaseWidget()
        g_showcase.set_gallery(gallery, (170 // 1.40, 170))
        if text:
            t_layout = QHBoxLayout()
            main_layout.addLayout(t_layout)
            t_layout.addWidget(g_showcase, 1)
            info = QLabel(text)
            info.setWordWrap(True)
            t_layout.addWidget(info)
        else:
            main_layout.addWidget(g_showcase, 0, Qt.AlignCenter)
        self.list_w = QListWidget(self)
        self.list_w.setAlternatingRowColors(True)
        self.list_w.setWordWrap(True)
        self.list_w.setTextElideMode(Qt.ElideNone)
        main_layout.addWidget(self.list_w, 3)
        main_layout.addLayout(self.buttons_layout)
        for t in tuple_first_idx:
            item = CustomListItem(t)
            item.setText(t[0])
            self.list_w.addItem(item)
        self.buttons = self.add_buttons('Skip All', 'Skip', 'Choose',)
        self.buttons[2].clicked.connect(self.finish)
        self.buttons[1].clicked.connect(self.skip)
        self.buttons[0].clicked.connect(self.skipall)
        self.resize(400, 400)
        self.show()

    def finish(self):
        """finish."""
        item = self.list_w.selectedItems()
        if item:
            item = item[0]
            self.USER_CHOICE.emit(item.item)
            self.close()

    def skip(self):
        """skip."""
        self.USER_CHOICE.emit(())
        self.close()

    def skipall(self):
        """skipall."""
        self.USER_CHOICE.emit(None)
        self.close()

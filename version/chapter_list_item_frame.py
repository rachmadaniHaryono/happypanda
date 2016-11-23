"""chapter list item widget."""
import logging

from PyQt5.QtCore import (
    pyqtSignal,
)
from PyQt5.QtGui import (
    QFont,
)
from PyQt5.QtWidgets import (
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

try:
    from elided_label import ElidedLabel
except ImportError:
    from .elided_label import ElidedLabel

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class ChapterListItemFrame(QFrame):
    """ChapterListItem."""

    move_pos = pyqtSignal(int, object)

    def __init__(self, chapter, parent=None):
        """__init__."""
        super().__init__(parent)
        main_layout = QHBoxLayout(self)
        chapter_layout = QFormLayout()
        self.number_lbl = QLabel(str(chapter.number + 1), self)
        self.number_lbl.adjustSize()
        self.number_lbl.setFixedSize(self.number_lbl.size())
        self.chapter_lbl = ElidedLabel(self)
        self.set_chapter_title(chapter)
        main_layout.addWidget(self.number_lbl)
        chapter_layout.addRow(self.chapter_lbl)
        g_title = ''
        if chapter.gallery:
            g_title = chapter.gallery.title
        self.gallery_lbl = ElidedLabel(g_title, self)
        g_lbl_font = QFont(self.gallery_lbl.font())
        g_lbl_font.setPixelSize(g_lbl_font.pixelSize() - 2)
        g_lbl_font.setItalic(True)
        self.gallery_lbl.setFont(g_lbl_font)
        chapter_layout.addRow(self.gallery_lbl)
        self.chapter = chapter
        main_layout.addLayout(chapter_layout)
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(0)
        up_btn = QPushButton('▲')
        up_btn.adjustSize()
        up_btn.setFixedSize(up_btn.size())
        up_btn.clicked.connect(lambda: self.move_pos.emit(0, self))
        down_btn = QPushButton('▼')
        down_btn.adjustSize()
        down_btn.setFixedSize(down_btn.size())
        down_btn.clicked.connect(lambda: self.move_pos.emit(1, self))
        buttons_layout.addWidget(up_btn)
        buttons_layout.addWidget(down_btn)
        main_layout.addLayout(buttons_layout)

    def set_chapter_title(self, chapter):
        """set_chapter_title."""
        if chapter.title:
            self.chapter_lbl.setText(chapter.title)
        else:
            self.chapter_lbl.setText("Chapter " + str(chapter.number + 1))

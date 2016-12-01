"""chapter add widget."""
import logging
import os
import scandir

from PyQt5.QtCore import (
    pyqtSignal,
    Qt,
)
from PyQt5.QtWidgets import (
    QDesktopWidget,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

try:
    import gallerydb
    from archive_file import ArchiveFile
    from path_line_edit import PathLineEdit
    from spacer_widget import SpacerWidget
    from utils import get_chapter_title, ARCHIVE_FILES
except ImportError:
    from .archive_file import ArchiveFile
    from .path_line_edit import PathLineEdit
    from .spacer_widget import SpacerWidget
    from .utils import get_chapter_title, ARCHIVE_FILES
    from . import (
        gallerydb,
    )

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class ChapterAddWidget(QWidget):
    """ChapterAddWidget."""

    CHAPTERS = pyqtSignal(gallerydb.ChaptersContainer)

    def __init__(self, gallery, parent=None):
        """__init__."""
        super().__init__(parent)
        self.setWindowFlags(Qt.Window)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.current_chapters = gallery.chapters.count()
        self.added_chaps = 0
        self.gallery = gallery

        layout = QFormLayout()
        self.setLayout(layout)
        lbl = QLabel('{} by {}'.format(gallery.title, gallery.artist))
        layout.addRow('Gallery:', lbl)
        layout.addRow('Current chapters:', QLabel(
            '{}'.format(self.current_chapters)))

        new_btn = QPushButton('Add directory')
        new_btn.clicked.connect(lambda: self.add_new_chapter('f'))
        new_btn.adjustSize()
        new_btn_a = QPushButton('Add archive')
        new_btn_a.clicked.connect(lambda: self.add_new_chapter('a'))
        new_btn_a.adjustSize()
        add_btn = QPushButton('Finish')
        add_btn.clicked.connect(self.finish)
        add_btn.adjustSize()
        new_l = QHBoxLayout()
        new_l.addWidget(add_btn, 1, alignment=Qt.AlignLeft)
        new_l.addWidget(SpacerWidget('h'))
        new_l.addWidget(new_btn, alignment=Qt.AlignRight)
        new_l.addWidget(new_btn_a, alignment=Qt.AlignRight)
        layout.addRow(new_l)

        frame = QFrame()
        frame.setFrameShape(frame.StyledPanel)
        layout.addRow(frame)

        self.chapter_l = QVBoxLayout()
        frame.setLayout(self.chapter_l)

        self.setMaximumHeight(550)
        self.setFixedWidth(500)
        if parent:
            self.move(parent.window().frameGeometry().topLeft() +
                      parent.window().rect().center() - self.rect().center())
        else:
            frect = self.frameGeometry()
            frect.moveCenter(QDesktopWidget().availableGeometry().center())
            self.move(frect.topLeft())
        self.setWindowTitle('Add Chapters')

    def add_new_chapter(self, mode):
        """add_new_chapter."""
        chap_layout = QHBoxLayout()
        self.added_chaps += 1
        curr_chap = self.current_chapters + self.added_chaps

        chp_numb = QSpinBox(self)
        chp_numb.setMinimum(curr_chap - 1)
        chp_numb.setMaximum(curr_chap + 1)
        chp_numb.setValue(curr_chap)
        curr_chap_lbl = QLabel('Chapter {}'.format(curr_chap))

        def ch_lbl(n):
            curr_chap_lbl.setText('Chapter {}'.format(n))
        chp_numb.valueChanged[int].connect(ch_lbl)
        if mode == 'f':
            chp_path = PathLineEdit()
            chp_path.setPlaceholderText(
                'Right/Left-click to open folder explorer.' + ' Leave empty to not add.')
        elif mode == 'a':
            chp_path = PathLineEdit(dir=False)
            chp_path.setPlaceholderText(
                'Right/Left-click to open folder explorer.' + ' Leave empty to not add.')

        chp_path.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        if mode == 'f':
            chap_layout.addWidget(QLabel('D'))
        elif mode == 'a':
            chap_layout.addWidget(QLabel('A'))
        chap_layout.addWidget(chp_path, 3)
        chap_layout.addWidget(chp_numb, 0)
        self.chapter_l.addWidget(curr_chap_lbl,
                                 alignment=Qt.AlignLeft)
        self.chapter_l.addLayout(chap_layout)

    def finish(self):
        """finish."""
        chapters = self.gallery.chapters
        widgets = []
        x = True
        while x:
            x = self.chapter_l.takeAt(0)
            if x:
                widgets.append(x)
        for l in range(1, len(widgets), 1):
            layout = widgets[l]
            try:
                line_edit = layout.itemAt(1).widget()
                spin_box = layout.itemAt(2).widget()
            except AttributeError:
                continue
            p = line_edit.text()
            c = spin_box.value() - 1  # because of 0-based index
            if os.path.exists(p):
                chap = chapters.create_chapter(c)
                chap.title = get_chapter_title(path=p)
                chap.path = p
                if os.path.isdir(p):
                    chap.pages = len(list(scandir.scandir(p)))
                elif p.endswith(ARCHIVE_FILES):
                    chap.in_archive = 1
                    arch = ArchiveFile(p)
                    chap.pages = len(arch.dir_contents(''))
                    arch.close()

        self.CHAPTERS.emit(chapters)
        self.close()

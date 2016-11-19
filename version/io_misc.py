"""contain widget for misc IO."""
# """
# This file is part of Happypanda.
# Happypanda is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# any later version.
# Happypanda is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with Happypanda.  If not, see <http://www.gnu.org/licenses/>.
# """
import logging
import os

from PyQt5.QtCore import (
    Qt,
    pyqtSignal,
)
from PyQt5.QtGui import (
    QPixmap,
)
from PyQt5.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

try:
    import misc
    import gallerydb
    import utils
except ImportError:
    from . import (
        misc,
        gallerydb,
        utils,
    )

log = logging.getLogger(__name__)
""":class:`logging.Logger`: Logger for module."""
log_i = log.info
""":meth:`logging.Logger.info`: Info logger func"""
log_d = log.debug
""":meth:`logging.Logger.debug`: Debug logger func"""
log_w = log.warning
""":meth:`logging.Logger.warning`: Warning logger func"""
log_e = log.error
""":meth:`logging.Logger.error`: Error logger func"""
log_c = log.critical
""":meth:`logging.Logger.critical`: Critical logger func"""


class GalleryPopup(misc.BasePopup):
    """gallery popup.

    Pass a tuple with text and a list of galleries
    gallery profiles won't be scaled if scale is set to false

    Args:
        tup_gallery(tupple):Tupple of gallery data.
        parent:Parent.
        menu:Menu.
        app_instance:Application instance.
    Attributes:
        gallery_doubleclicked(:class:`PyQt5.QtCore.pyqtSignal`):Signal  when gallery double
            clicked.
    """

    gallery_doubleclicked = pyqtSignal(gallerydb.Gallery)

    def __init__(self, tup_gallery, parent=None, menu=None, app_instance=None):
        """init func."""
        if app_instance is None:
            raise NotImplementedError
        super().__init__(parent)
        self.setMaximumWidth(16777215)
        assert isinstance(
            tup_gallery, tuple), "Incorrect type received, expected tuple"
        assert isinstance(tup_gallery[0], str) and isinstance(
            tup_gallery[1], list)
        main_layout = QVBoxLayout()
        # todo make it scroll
        dummy = QWidget()
        self.gallery_layout = misc.FlowLayout(dummy)
        # scroll_area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(400)
        scroll_area.setMidLineWidth(620)
        scroll_area.setBackgroundRole(scroll_area.palette().Shadow)
        scroll_area.setFrameStyle(scroll_area.NoFrame)
        scroll_area.setWidget(dummy)
        main_layout.addWidget(scroll_area, 3)
        #
        text = tup_gallery[0]
        galleries = tup_gallery[1]
        for g in galleries:
            gall_w = misc.GalleryShowcaseWidget(
                parent=self, menu=menu(app_instance=app_instance))
            gall_w.set_gallery(g, (170 // 1.40, 170))
            gall_w.double_clicked.connect(self.gallery_doubleclicked.emit)
            self.gallery_layout.addWidget(gall_w)
        # text_lbl
        text_lbl = QLabel(text)
        text_lbl.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(text_lbl)
        #
        main_layout.addLayout(self.buttons_layout)
        self.main_widget.setLayout(main_layout)
        #
        self.setMaximumHeight(500)
        self.setMaximumWidth(620)
        self.resize(620, 500)
        self.show()

    def get_all_items(self):
        """get all items.

        Returns:
            items(list):List of items.
        """
        n = self.gallery_layout.rowCount()
        items = []
        for x in range(n):
            item = self.gallery_layout.itemAt(x)
            items.append(item.widget())
        return items


class ModifiedPopup(misc.BasePopup):
    """popup when modified.

    Args:
        path:Path
        gallery:Gallery.
        parent:Parent.
    """

    def __init__(self, path, gallery_id, parent=None):
        """init func."""
        super().__init__(parent)
        main_layout = QVBoxLayout()
        main_layout.addWidget(
            QLabel("Modified:\npath: {}\nID:{}".format(path, gallery_id)))
        self.main_widget.setLayout(main_layout)
        self.show()


class MovedPopup(misc.BasePopup):
    """popup when moved.

    Args:
        new_path:New path.
        gallery:Gallery.
        parent:Parent.
    Attributes:
        UPDATE_SIGNAL:Signal when updated.
        _new_path:New path.
        _gallery:Gallery.
    """

    UPDATE_SIGNAL = pyqtSignal(object)

    def __init__(self, new_path, gallery, parent=None):
        """init func."""
        super().__init__(parent)
        self._new_path = new_path
        self._gallery = gallery
        #
        main_layout = QVBoxLayout()
        inner_layout = QHBoxLayout()
        # title
        title = QLabel(gallery.title)
        title.setWordWrap(True)
        title.setAlignment(Qt.AlignCenter)
        title.adjustSize()
        main_layout.addWidget(title)
        # cover
        cover = QLabel()
        img = QPixmap(gallery.profile)
        cover.setPixmap(img)
        inner_layout.addWidget(cover)
        # text_label
        text = QLabel(
            "The path to this gallery has been renamed\n\n{}\n{}\n{}".format(
                os.path.basename(gallery.path),
                u'\u2192',
                os.path.basename(new_path)
            )
        )
        text.setWordWrap(True)
        text.setAlignment(Qt.AlignCenter)
        inner_layout.addWidget(text)
        #
        button_layout = QHBoxLayout()
        # update_btn
        update_btn = QPushButton('Update')
        update_btn.clicked.connect(self.commit_when_update_btn_clicked)
        button_layout.addWidget(update_btn)
        # close_btn
        close_btn = QPushButton('Close')
        close_btn.clicked.connect(self.cancel_when_close_btn_clicked)
        button_layout.addWidget(close_btn)
        #
        main_layout.addLayout(inner_layout)
        main_layout.addLayout(button_layout)
        self.main_widget.setLayout(main_layout)
        #
        self.show()

    def commit_when_update_btn_clicked(self):
        """commit when update buttton clicked."""
        g = utils.update_gallery_path(self._new_path, self._gallery)
        self.UPDATE_SIGNAL.emit(g)
        self.close()

    def cancel_when_close_btn_clicked(self):
        """Cancel when close button clicked."""
        self._gallery.dead_link = True
        self.close()


class DeletedPopup(misc.BasePopup):
    """deleted popup.

    Args:
        path:Path
        parent:Parent
        gallery:Gallery
    Attributes:
        REMOVE_SIGNAL(:class:`PyQt5.QtCore.pyqtSignal`):Remove signal.
        UPDATE_SIGNAL(:class:`PyQt5.QtCore.pyqtSignal`):Update signal.
        gallery:Gallery.
    """

    REMOVE_SIGNAL = pyqtSignal(object)
    UPDATE_SIGNAL = pyqtSignal(object)

    def __init__(self, path, gallery, parent=None):
        """init func."""
        super().__init__(parent)
        gallery.dead_link = True
        self._gallery = gallery
        #
        main_layout = QVBoxLayout()
        inner_layout = QHBoxLayout()
        # cover
        cover = QLabel()
        img = QPixmap(gallery.profile)
        cover.setPixmap(img)
        inner_layout.addWidget(cover)
        # title label
        title_lbl = QLabel(gallery.title)
        title_lbl.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_lbl)
        # info label
        info_lbl = QLabel(
            "The path to this gallery has been removed\nWhat do you want to do?")
        info_lbl.setAlignment(Qt.AlignCenter)
        inner_layout.addWidget(info_lbl)
        # path label
        path_lbl = QLabel(path)
        path_lbl.setWordWrap(True)
        main_layout.addWidget(path_lbl)
        #
        main_layout.addLayout(inner_layout)
        buttons_layout = QHBoxLayout()
        # close btn
        close_btn = QPushButton('Close')
        close_btn.clicked.connect(self.close)
        buttons_layout.addWidget(close_btn)
        # update btn
        update_btn = QPushButton('Update path...')
        update_btn.clicked.connect(self.commit_when_update_btn_clicked)
        buttons_layout.addWidget(update_btn)
        # remove btn
        remove_btn = QPushButton('Remove')
        remove_btn.clicked.connect(self.remove_commit_when_remove_btn_clicked)
        buttons_layout.addWidget(remove_btn)
        #
        main_layout.addLayout(buttons_layout)
        self.main_widget.setLayout(main_layout)
        #
        self.adjustSize()
        self.show()

    def commit_when_update_btn_clicked(self):
        """Commit when update button  clicked."""
        msgbox = QMessageBox(self)
        msgbox.setIcon(QMessageBox.Question)
        msgbox.setWindowTitle('Type of gallery source')
        msgbox.setInformativeText('What type of gallery source is it?')
        dir = msgbox.addButton('Directory', QMessageBox.YesRole)
        archive = msgbox.addButton('Archive', QMessageBox.NoRole)
        msgbox.exec_()
        new_path = ''
        if msgbox.clickedButton() == dir:
            new_path = QFileDialog.getExistingDirectory(
                self, 'Choose directory')
        elif msgbox.clickedButton() == archive:
            new_path = QFileDialog.getOpenFileName(
                self, 'Choose archive', filter=utils.FILE_FILTER)
            new_path = new_path[0]
        else:
            return None
        if new_path:
            g = utils.update_gallery_path(new_path, self._gallery)
            self.UPDATE_SIGNAL.emit(g)
            self.close()

    def remove_commit_when_remove_btn_clicked(self):
        """Remove commit when remove button clicked."""
        self.REMOVE_SIGNAL.emit(self._gallery)
        self.close()

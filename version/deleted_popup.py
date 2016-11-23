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
    QVBoxLayout,
)

try:
    import utils
    from base_popup import BasePopup
except ImportError:
    from .base_popup import BasePopup
    from . import utils

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


class DeletedPopup(BasePopup):
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

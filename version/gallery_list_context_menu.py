"""misc obj/class/function for db."""
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
import logging

from PyQt5.QtWidgets import (
    QMenu,
)

try:
    import gallerydb
except ImportError:
    from . import (
        gallerydb,
    )

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class GalleryListContextMenu(QMenu):
    """gallery llist context menu."""

    def __init__(self, item, parent):
        """init func."""
        super().__init__(parent)
        self.parent_widget = parent
        self.item = item
        self.gallery_list = item.item
        self.addAction("Edit", self.edit_list)
        self.addAction("Clear", self.clear_list)
        self.addAction("Delete", self.remove_list)

    def edit_list(self):
        """edit list."""
        self.parent_widget.gallery_list_edit.set_list(
            self.gallery_list, self.item)
        self.parent_widget.gallery_list_edit.show()

    def remove_list(self):
        """remove list."""
        self.parent_widget.takeItem(self.parent_widget.row(self.item))
        gallerydb.execute(gallerydb.ListDB.remove_list,
                          True, self.gallery_list)
        self.parent_widget.GALLERY_LIST_REMOVED.emit()

    def clear_list(self):
        """clear list."""
        self.gallery_list.clear()
        self.parent_widget.GALLERY_LIST_CLICKED.emit(self.gallery_list)

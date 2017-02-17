"""gallery context menu."""
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
from .common_view import CommonView

from PyQt5.QtWidgets import (
    QMenu,
)


class GalleryContextMenu(QMenu):
    """gallery context menu."""

    def __init__(self, parent=None, app_instance=None):
        """init func."""
        if app_instance is not None:
            self.app_instance = app_instance
        else:
            raise NotImplementedError
        super().__init__(parent)
        show_in_library_act = self.addAction('Show in library')
        show_in_library_act.triggered.connect(self.show_in_library)

    def show_in_library(self):
        """show in library."""
        index = CommonView.find_index(
            self.app_instance.get_current_view(),
            self.gallery_widget.gallery.id, True)
        if index:
            CommonView.scroll_to_index(
                self.app_instance.get_current_view(), index)

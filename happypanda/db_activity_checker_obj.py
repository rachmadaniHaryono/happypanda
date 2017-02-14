"""check db activity."""
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
from PyQt5.QtCore import (
    QObject,
    pyqtSignal,
)
try:
    import gallerydb
except ImportError:
    from . import gallerydb


class DBActivityCheckerObject(QObject):
    """db activity checker."""

    FINISHED = pyqtSignal()

    def __init__(self, **kwargs):
        """init func."""
        super().__init__(**kwargs)

    def check(self):
        """check func."""
        gallerydb.method_queue.join()
        self.FINISHED.emit()
        self.deleteLater()

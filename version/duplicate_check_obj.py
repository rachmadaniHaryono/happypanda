"""check duplicate."""
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
import os
import logging

from PyQt5.QtCore import (
    QObject,
    pyqtSignal,
)


log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class DuplicateCheckObject(QObject):
    """duplicate checker."""

    found_duplicates = pyqtSignal(tuple)
    finished = pyqtSignal()

    def __init__(self, notifbar=None):
        """init func."""
        super().__init__()
        self._notifbar = notifbar

    def check_simple(self, model):
        """check simple."""
        galleries = model._data

        duplicates = []
        for n, g in enumerate(galleries, 1):
            self._notifbar.add_text('Checking gallery {}'.format(n))
            log_d('Checking gallery {}'.format(g.title.encode(errors="ignore")))
            for y in galleries:
                title = g.title.strip().lower() == y.title.strip().lower()
                path = os.path.normcase(g.path) == os.path.normcase(y.path)
                if g.id != y.id and (title or path) and g not in duplicates:
                    duplicates.append(y)
                    duplicates.append(g)
                    self.found_duplicates.emit((g, y))
        self.finished.emit()

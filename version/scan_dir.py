"""scan dir."""
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
import scandir

from PyQt5.QtCore import (
    QObject,
    pyqtSignal,
)

try:
    import fetch
    import app_constants
except ImportError:
    from . import (
        fetch,
        app_constants
    )


log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class ScanDir(QObject):
    """dir scanner Qobj."""

    finished = pyqtSignal()

    def __init__(self, addition_view, addition_tab, parent=None, app_window=None):
        """init func."""
        if app_window is not None:
            self.fetch_inst = fetch.Fetch(app_window)
        else:
            raise NotImplementedError
        super().__init__(parent)
        self.addition_view = addition_view
        self.addition_tab = addition_tab
        self._switched = False

    def switch_tab(self):
        """switch tab."""
        if not self._switched:
            self.addition_tab.click()
            self._switched = True

    def scan_dirs(self):
        """scan dirs func."""
        paths = []
        for p in app_constants.MONITOR_PATHS:
            if os.path.exists(p):
                dir_content = scandir.scandir(p)
                for d in dir_content:
                    paths.append(d.path)
            else:
                log_e("Monitored path does not exists: {}".format(p.encode(errors='ignore')))

        self.fetch_inst.series_path = paths
        self.fetch_inst.LOCAL_EMITTER.connect(
            lambda g: self.addition_view.add_gallery(g, app_constants.KEEP_ADDED_GALLERIES)
        )
        self.fetch_inst.LOCAL_EMITTER.connect(self.switch_tab)
        self.fetch_inst.local()
        self.finished.emit()
        self.deleteLater()

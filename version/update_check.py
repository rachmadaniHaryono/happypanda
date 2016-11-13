"""check update."""
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
    QObject,
    pyqtSignal,
)


log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class UpdateChecker(QObject):
    """update checker class."""

    UPDATE_CHECK = pyqtSignal(str)

    def __init__(self, **kwargs):
        """init func."""
        super().__init__(**kwargs)

    def fetch_vs(self):
        """fetch version."""
        import requests
        import time
        log_d('Checking Update')
        time.sleep(1.5)
        try:
            r = requests.get("https://raw.githubusercontent.com/Pewpews/happypanda/master/VS.txt")
            a = r.text
            vs = a.strip()
            self.UPDATE_CHECK.emit(vs)
        except:
            log.exception('Checking Update: FAIL')
            self.UPDATE_CHECK.emit('this is a very long text which is sure to be over limit')

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
import time

import requests
import structlog
from PyQt5.QtCore import (
    QObject,
    pyqtSignal,
)


class UpdateCheckerObject(QObject):
    """update checker class.

    Args:
        UPDATE_CHECK (pyqtSignal): Signal for update check.
    """

    UPDATE_CHECK = pyqtSignal(str)

    def __init__(self, **kwargs):
        """init func."""
        self.default_url = \
            'https://github.com/rachmadaniHaryono/happypanda/raw/dev/happypanda/__init__.py'
        self.update_url = self.default_url  # TODO change it based on config
        super().__init__(**kwargs)

    def fetch_vs(self):
        """fetch version."""
        log = structlog.getLogger(__name__)
        log.debug('Checking Update')
        time.sleep(1.5)
        try:
            r = requests.get(self.url)
            a = r.text
            vs = a.strip()
            self.UPDATE_CHECK.emit(vs)
        except:
            log.exception('Checking Update: FAIL')

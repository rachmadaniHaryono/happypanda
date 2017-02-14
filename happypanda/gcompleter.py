"""gcompleter."""
import logging

from PyQt5.QtCore import (
    Qt,
)
from PyQt5.QtWidgets import (
    QCompleter,
)

try:
    import app_constants
except ImportError:
    from . import (
        app_constants,
    )

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class GCompleter(QCompleter):
    """GCompleter."""

    def __init__(self, parent=None, title=True, artist=True, tags=True):
        """__init__."""
        self.all_data = []
        d = set()
        for g in app_constants.GALLERY_DATA:
            if title:
                d.add(g.title)
            if artist:
                d.add(g.artist)
            if tags:
                for ns in g.tags:
                    d.add(ns)
                    for t in g.tags[ns]:
                        d.add(t)

        self.all_data.extend(d)
        super().__init__(self.all_data, parent)
        self.setCaseSensitivity(Qt.CaseInsensitive)

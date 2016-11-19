"""gallery search object."""

import logging

from PyQt5.QtCore import (
    QObject,
    pyqtSignal,
)
try:
    import utils
except ImportError:
    from . import (
        utils,
    )

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class GallerySearchObject(QObject):
    """gallery search."""

    FINISHED = pyqtSignal()

    def __init__(self, data):
        """init func."""
        super().__init__()
        self._data = data
        self.result = {}

        # filtering
        self.fav = False
        self._gallery_list = None

    def set_gallery_list(self, g_list):
        """set gallery list."""
        self._gallery_list = g_list

    def set_data(self, new_data):
        """set data."""
        self._data = new_data
        self.result = {g.id: True for g in self._data}

    def set_fav(self, new_fav):
        """set fav."""
        self.fav = new_fav

    def search(self, term, args):
        """search."""
        term = ' '.join(term.split())
        search_pieces = utils.get_terms(term)

        self._filter(search_pieces, args)
        self.FINISHED.emit()

    def _filter(self, terms, args):
        self.result.clear()
        for gallery in self._data:
            if self.fav:
                if not gallery.fav:
                    continue
            if self._gallery_list:
                if gallery not in self._gallery_list:
                    continue
            all_terms = {t: False for t in terms}
            allow = False
            if utils.all_opposite(terms):
                self.result[gallery.id] = True
                continue

            for t in terms:
                if gallery.contains(t, args):
                    all_terms[t] = True

            if all(all_terms.values()):
                allow = True

            self.result[gallery.id] = allow

"""import export object module."""
import logging
import json

from PyQt5.QtCore import (
    QObject,
    pyqtSignal,
)

try:
    import app_constants
    import gallerydb
    from import_export_data import ImportExportData
except ImportError:
    from .import_export_data import ImportExportData
    from . import (
        app_constants,
        gallerydb,
    )

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


class ImportExportObject(QObject):
    """import export.

    finished(:class:`PyQt5.QtCore.pyqtSignal`):Signal when finished.
    imported_g(:class:`PyQt5.QtCore.pyqtSignal`):Signal when gallery imported.
    progress(:class:`PyQt5.QtCore.pyqtSignal`):Signal for progress.
    amount(:class:`PyQt5.QtCore.pyqtSignal`):Signal amount.
    """

    finished = pyqtSignal()
    imported_g = pyqtSignal(str)
    progress = pyqtSignal(int)
    amount = pyqtSignal(int)

    def __init__(self):
        """init func."""
        super().__init__()

    def import_data(self, path):
        """import data.

        Args:
            path:Path.
        """
        with open(path, 'r', encoding='utf-8') as fp:
            data = json.load(fp)
            data_count = len(data)
            self.amount.emit(data_count)
            pairs_found = []
            for prog, g_id in enumerate(data, 1):
                g_data = ImportExportData()
                g_data.structure.update(data[g_id])
                g = g_data.find_pair(pairs_found)
                if g:
                    pairs_found.append(g)
                self.imported_g.emit(
                    "Importing database file... ({}/{} imported)".format(
                        len(pairs_found), data_count
                    )
                )
                self.progress.emit(prog)
            self.finished.emit()

    def export_data(self, gallery=None):
        """export data.

        Args:
            gallery:Gallery.
        """
        galleries = []
        if gallery:
            galleries.append(gallery)
        else:
            galleries = app_constants.GALLERY_DATA

        amount = len(galleries)
        log_i("Exporting {} galleries".format(amount))
        data = ImportExportData(app_constants.EXPORT_FORMAT)
        self.amount.emit(amount)
        for prog, g in enumerate(galleries, 1):
            log_d("Exporting {} out of {} galleries".format(prog, amount))
            g_data = {}
            g_data['title'] = g.title
            g_data['artist'] = g.artist
            g_data['info'] = g.info
            g_data['fav'] = g.fav
            g_data['type'] = g.type
            g_data['link'] = g.link
            g_data['language'] = g.language
            g_data['status'] = g.status
            g_data['pub_date'] = "{}".format(g.pub_date)
            g_data['last_read'] = "{}".format(g.last_read)
            g_data['times_read'] = g.times_read
            g_data['exed'] = g.exed
            g_data['db_v'] = g._db_v
            g_data['tags'] = g.tags.copy()
            g_data['identifier'] = {'pages': g.chapters[0].pages}
            pages = data.get_pages(g.chapters[0].pages)
            try:
                h_list = gallerydb.HashDB.gen_gallery_hash(g, 0, pages)
            except app_constants.InternalPagesMismatch:
                if g.chapters.update_chapter_pages(0):
                    pages = data.get_pages(g.chapters[0].pages)
                    h_list = gallerydb.HashDB.gen_gallery_hash(g, 0, pages)
                else:
                    h_list = {}
            if not h_list:
                log_e("Failed to export gallery: {}".format(
                    g.title.encode(errors='ignore')))
                continue
            for n in pages:
                g_data['identifier'][n] = h_list[n]

            data.add_data(str(g.id), g_data)
            self.progress.emit(prog)

        log_i("Finished exporting galleries!")
        data.save(app_constants.EXPORT_PATH)
        self.finished.emit()

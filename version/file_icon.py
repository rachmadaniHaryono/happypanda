"""file icon."""
import logging
import os
import scandir

from PyQt5.QtCore import (
    QFileInfo,
    QSize,
)
from PyQt5.QtGui import (
    QIcon,
)
from PyQt5.QtWidgets import (
    QFileIconProvider,
)

try:
    from archive_file import ArchiveFile
    from utils import (
        ARCHIVE_FILES,
        IMG_FILES
    )
    import app_constants
    import gallerydb
    import utils
except ImportError:
    from .archive_file import ArchiveFile
    from .utils import (
        ARCHIVE_FILES,
        IMG_FILES
    )
    from . import (
        app_constants,
        gallerydb,
        utils,
    )

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class FileIcon:
    """FileIcon."""

    def __init__(self):
        """__init__."""
        self.ico_types = {}

    def get_file_icon(self, path):
        """get_file_icon."""
        if os.path.isdir(path):
            if 'dir' not in self.ico_types:
                self.ico_types['dir'] = QFileIconProvider().icon(
                    QFileInfo(path))
            return self.ico_types['dir']
        elif path.endswith(utils.ARCHIVE_FILES):
            suff = ''
            for s in utils.ARCHIVE_FILES:
                if path.endswith(s):
                    suff = s
            if suff not in self.ico_types:
                self.ico_types[suff] = QFileIconProvider().icon(
                    QFileInfo(path))
            return self.ico_types[suff]

    @staticmethod
    def get_external_file_icon():
        """get_external_file_icon."""
        if app_constants._REFRESH_EXTERNAL_VIEWER:
            if os.path.exists(app_constants.GALLERY_EXT_ICO_PATH):
                os.remove(app_constants.GALLERY_EXT_ICO_PATH)
            info = QFileInfo(app_constants.EXTERNAL_VIEWER_PATH)
            icon = QFileIconProvider().icon(info)
            pixmap = icon.pixmap(QSize(32, 32))
            pixmap.save(app_constants.GALLERY_EXT_ICO_PATH, quality=100)
            app_constants._REFRESH_EXTERNAL_VIEWER = False

        return QIcon(app_constants.GALLERY_EXT_ICO_PATH)

    @staticmethod  # NOQA
    def refresh_default_icon():
        """refresh_default_icon."""
        if os.path.exists(app_constants.GALLERY_DEF_ICO_PATH):
            os.remove(app_constants.GALLERY_DEF_ICO_PATH)

        def get_file(n):
            """get_file."""
            gallery = gallerydb.GalleryDB.get_gallery_by_id(n)
            if not gallery:
                return False
            file = ""
            if gallery.path.endswith(tuple(ARCHIVE_FILES)):
                try:
                    zip = ArchiveFile(gallery.path)
                except utils.app_constants.CreateArchiveFail:
                    return False
                for name in zip.namelist():
                    if name.lower().endswith(tuple(IMG_FILES)):
                        folder = os.path.join(app_constants.temp_dir,
                                              '{}{}'.format(name, n))
                        zip.extract(name, folder)
                        file = os.path.join(folder, name)
                        break
            else:
                for p in scandir.scandir(gallery.chapters[0].path):
                    if p.name.lower().endswith(tuple(IMG_FILES)):
                        file = p.path
                        break
            return file

        # TODO: fix this!  (When there are no ids below 300?  (because they go
        # deleted))
        for x in range(1, 300):
            try:
                file = get_file(x)
                break
            except FileNotFoundError:  # NOQA
                continue
            except app_constants.CreateArchiveFail:
                continue

        if not file:
            return None
        icon = QFileIconProvider().icon(QFileInfo(file))
        pixmap = icon.pixmap(QSize(32, 32))
        pixmap.save(app_constants.GALLERY_DEF_ICO_PATH, quality=100)
        return True

    @staticmethod
    def get_default_file_icon():
        """get_default_file_icon."""
        s = True
        if not os.path.isfile(app_constants.GALLERY_DEF_ICO_PATH):
            s = FileIcon.refresh_default_icon()
        if s:
            return QIcon(app_constants.GALLERY_DEF_ICO_PATH)
        else:
            return None

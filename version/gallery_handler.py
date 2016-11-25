"""gallery handler obj."""
import logging
import os

from watchdog.events import FileSystemEventHandler
from PyQt5.QtCore import (
    QObject,
    pyqtSignal,
)

try:
    import app_constants
    from gallerydb import GalleryDB
    import utils
except ImportError:
    from .gallerydb import GalleryDB
    from . import (
        app_constants,
        utils,
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


class GalleryHandler(FileSystemEventHandler, QObject):
    """gallery handler.

    Attributes:
        CREATE_SIGNAL(:class:`PyQt5.QtCore.pyqtSignal`):Create signal.
        MODIFIED_SIGNAL(:class:`PyQt5.QtCore.pyqtSignal`):Modified signal.
        DELETED_SIGNAL(:class:`PyQt5.QtCore.pyqtSignal`):Deleted signal
        MOVED_SIGNAL(:class:`PyQt5.QtCore.pyqtSignal`):Moved signal.
    """

    CREATE_SIGNAL = pyqtSignal(str)
    MODIFIED_SIGNAL = pyqtSignal(str, int)
    DELETED_SIGNAL = pyqtSignal(str, object)
    MOVED_SIGNAL = pyqtSignal(str, object)

    def __init__(self):
        """init func."""
        super().__init__()

    def file_filter(self, event):
        """file_filter."""
        if os.path.normcase(event.src_path) in app_constants.TEMP_PATH_IGNORE:
            app_constants.TEMP_PATH_IGNORE.remove(
                os.path.normcase(event.src_path))
            return False
        # TODO: use utils.check_ignore_list?
        _, ext = os.path.splitext(event.src_path)
        if event.is_directory or ext in utils.ARCHIVE_FILES:
            if event.is_directory and "Folder" in app_constants.IGNORE_EXTS:
                return False
            if ext[1:].upper() in app_constants.IGNORE_EXTS:
                return False
            return True
        return False

    def _is_condition_match(self, event):
        """condition to match before any method run.

        this method may calso have side effect.
        """
        if not app_constants.OVERRIDE_MONITOR:
            if self.file_filter(event):
                return True
        else:
            app_constants.OVERRIDE_MONITOR = False
        return False

    def on_created(self, event):
        """Run the function when file created.

        Args:
            event:Event
        """
        if self._is_condition_match(event):
            gs = 0
            if event.src_path.endswith(utils.ARCHIVE_FILES):
                gs = len(utils.check_archive(event.src_path))
            elif event.is_directory:
                g_dirs, g_archs = utils.recursive_gallery_check(event.src_path)
                gs = len(g_dirs) + len(g_archs)
            if gs:
                self.CREATE_SIGNAL.emit(event.src_path)

    def on_deleted(self, event):
        """Run the function when file deleted.

        Args:
            event:Event.
        """
        if self._is_condition_match(event):
            path = event.src_path
            gallery = GalleryDB.get_gallery_by_path(path)
            if gallery:
                self.DELETED_SIGNAL.emit(path, gallery)

    def on_moved(self, event):
        """Run the function when file moved."""
        if self._is_condition_match(event):
            old_path = event.src_path
            gallery = GalleryDB.get_gallery_by_path(old_path)
            if gallery:
                self.MOVED_SIGNAL.emit(event.dest_path, gallery)

"""watchers module."""
import logging

from watchdog.observers import Observer

try:
    import app_constants
    from gallery_handler import GalleryHandler
except ImportError:
    from . import (
        app_constants,
    )
    from .gallery_handler import GalleryHandler

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


class Watchers:
    """watchers.

    Attributes:
        gallery_handler(:class:`.GalleryHandler`):Gallery handler.
        watchers(list of :class:`watchdogs.observers.Observer`)
    """

    def __init__(self):
        """init func."""
        self.gallery_handler = GalleryHandler()
        self.watchers = []
        for path in app_constants.MONITOR_PATHS:
            gallery_observer = Observer()
            try:
                gallery_observer.schedule(self.gallery_handler, path, True)
                gallery_observer.start()
                self.watchers.append(gallery_observer)
            except:
                log.exception('Could not monitor: {}'.format(
                    path.encode(errors='ignore')))

    def stop_all(self):
        """stop all watcher."""
        for watcher in self.watchers:
            watcher.stop()

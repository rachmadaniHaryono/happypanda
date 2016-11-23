"""downloader_obj."""

import requests
import logging
import threading
import uuid
import os

from queue import Queue

from PyQt5.QtCore import QObject, pyqtSignal

try:
    import app_constants
    from downloader_item_obj import DownloaderItemObject
except ImportError:
    from . import (
        app_constants,
    )
    from .downloader_item_obj import DownloaderItemObject

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class DownloaderObject(QObject):
    """A download manager.

    Emits signal item_finished with tuple of url and path to file when a download finishes
    """

    _inc_queue = Queue()
    _browser_session = None
    _threads = []
    item_finished = pyqtSignal(object)
    active_items = []

    def __init__(self):
        """init func."""
        super().__init__()
        # download dir
        self.base = os.path.abspath(app_constants.DOWNLOAD_DIRECTORY)
        if not os.path.exists(self.base):
            os.mkdir(self.base)

    @staticmethod
    def add_to_queue(item, session=None, dir=None):
        """Add a DownloaderItemObject or url.

        An optional requests.Session object can be specified
        A temp dir to be used can be specified

        Returns:
            a downloader item
        """
        if isinstance(item, str):
            item = DownloaderItemObject(item)

        log_i("Adding item to download queue: {}".format(item.download_url))
        if dir:
            DownloaderObject._inc_queue.put({'dir': dir, 'item': item})
        else:
            DownloaderObject._inc_queue.put(item)
        DownloaderObject._session = session

        return item

    def _downloading(self):  # NOQA
        "The downloader. Put in a thread."
        while True:
            log_d("Download items in queue: {}".format(self._inc_queue.qsize()))
            interrupt = False
            item = self._inc_queue.get()
            temp_base = None
            if isinstance(item, dict):
                temp_base = item['dir']
                item = item['item']

            log_d("Stating item download")
            item.current_state = item.DOWNLOADING
            file_name = item.name if item.name else str(uuid.uuid4())

            invalid_chars = '\\/:*?"<>|'
            for x in invalid_chars:
                file_name = file_name.replace(x, '')

            file_name = os.path.join(self.base, file_name) if not temp_base else \
                os.path.join(temp_base, file_name)
            file_name_part = file_name + '.part'

            download_url = item.download_url
            log_d("Download url:{}".format(download_url))

            self.active_items.append(item)

            if self._browser_session:
                r = self._browser_session.get(download_url, stream=True)
            else:
                r = requests.get(download_url, stream=True)
            try:
                item.total_size = int(r.headers['content-length'])
            except KeyError:
                item.total_size = 0

            with open(file_name_part, 'wb') as f:
                for data in r.iter_content(chunk_size=1024):
                    if item.current_state == item.CANCELLED:
                        interrupt = True
                        break
                    if data:
                        item.current_size += len(data)
                        f.write(data)
                        f.flush()
            if not interrupt:
                try:
                    os.rename(file_name_part, file_name)
                except OSError:
                    n = 0
                    file_split = os.path.split(file_name)
                    while n < 100:
                        try:
                            if file_split[1]:
                                os.rename(
                                    file_name_part, os.path.join(
                                        file_split[0], "({}){}".format(n, file_split[1])
                                    )
                                )
                            else:
                                os.rename(file_name_part, "({}){}".format(n, file_name))
                            break
                        except:
                            n += 1
                    if n > 100:
                        file_name = file_name_part

                item.file = file_name
                item.current_state = item.FINISHED
                item.file_rdy.emit(item)
                self.item_finished.emit(item)
            else:
                try:
                    os.remove(file_name_part)
                except:
                    pass
            log_d("Items in queue {}".format(self._inc_queue.empty()))
            log_d("Finished downloading: {}".format(download_url))
            self.active_items.remove(item)
            self._inc_queue.task_done()

    def start_manager(self, max_tasks):
        """Start download manager where max simultaneous is mask_tasks."""
        log_i("Starting download manager with {} jobs".format(max_tasks))
        for x in range(max_tasks):
            thread = threading.Thread(
                target=self._downloading,
                name='Downloader {}'.format(x),
                daemon=True)
            thread.start()
            self._threads.append(thread)

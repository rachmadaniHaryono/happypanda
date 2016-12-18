"""downloader_obj."""

import requests
import logging
import threading
import uuid
import os

from queue import Queue

from PyQt5.QtCore import QObject, pyqtSignal

try:  # pragma: no cover
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
        self._set_base()

    def _set_base(self):
        """set base attribute, which will be used as download directory.

        helper function for init method.
        """
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

    @staticmethod
    def remove_file(filename):
        """remove file and ignore any error when doing it."""
        try:
            os.remove(filename)
        except:
            pass

    @staticmethod
    def _get_total_size(response):
        """get total size from requests response."""
        try:
            return int(response.headers['content-length'])
        except KeyError:
            return 0

    def _get_response(self, url):
        """get response from url."""
        if self._browser_session:
            r = self._browser_session.get(url, stream=True)
        else:
            r = requests.get(url, stream=True)
        return r

    def _get_item_and_temp_base(self):
        """get item and temporary folder if specified."""
        item = self._inc_queue.get()
        temp_base = None
        if isinstance(item, dict):
            temp_base = item['dir']
            item = item['item']
        return item, temp_base

    def _get_filename(self, item, temp_base=None):
        """get filename based on input."""
        file_name = item.name if item.name else str(uuid.uuid4())
        invalid_chars = '\\/:*?"<>|'
        for x in invalid_chars:
            file_name = file_name.replace(x, '')
        file_name = os.path.join(self.base, file_name) if not temp_base else \
            os.path.join(temp_base, file_name)
        return file_name

    @staticmethod
    def _download_single_file(target_file, response, item, interrupt_state):
        """download single file from url response and return changed item and interrupt state."""
        with open(target_file, 'wb') as f:
            for data in response.iter_content(chunk_size=1024):
                if item.current_state == item.CANCELLED:
                    interrupt_state = True
                    break
                if data:
                    item.current_size += len(data)
                    f.write(data)
                    f.flush()
        return item, interrupt_state

    @staticmethod
    def _rename_file(filename, filename_part, max_loop=100):
        """Custom rename file method."""
        # compatibility
        file_name = filename
        file_name_part = filename_part

        n = 0
        file_split = os.path.split(file_name)
        while n < max_loop:
            try:
                if file_split[1]:
                    src_file = file_split[0]
                    target_file = "({}){}".format(n, file_split[1])
                else:
                    src_file = file_name_part
                    target_file = "({}){}".format(n, file_name)
                os.rename(src_file, target_file)
                break
            except:
                n += 1
        if n > max_loop:
            file_name = file_name_part
        return file_name

    def _downloading(self):  # NOQA
        """The downloader. Put in a thread.

        TODO:

        - customize it for multiple urls.
        """
        while True:
            log_d("Download items in queue: {}".format(self._inc_queue.qsize()))
            interrupt = False
            item, temp_base = self._get_item_and_temp_base()

            log_d("Starting item download")
            item.current_state = item.DOWNLOADING

            # filename
            file_name = self._get_filename(item=item, temp_base=temp_base)
            file_name_part = file_name + '.part'

            download_url = item.download_url
            log_d("Download url:{}".format(download_url))
            self.active_items.append(item)

            # response
            r = self._get_response(url=download_url)
            # get total size
            item.total_size = self._get_total_size(response=r)

            # downloading to temp file (file_name_part)
            item, interrupt = self._download_single_file(
                target_file=file_name_part, response=r, item=item, interrupt_state=interrupt)

            if not interrupt:
                # post operation when no interrupt
                try:
                    os.rename(file_name_part, file_name)
                except OSError:
                    file_name = self._rename_file(
                        filename=file_name, filename_part=file_name_part)

                item.file = file_name
                item.current_state = item.FINISHED
                # emit
                item.file_rdy.emit(item)
                self.item_finished.emit(item)
            else:
                self.remove_file(filename=file_name_part)
            log_d("Items in queue {}".format(self._inc_queue.empty()))
            log_d("Finished downloading: {}".format(download_url))

            # remove recently added item from list
            self.active_items.remove(item)
            # task finished
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

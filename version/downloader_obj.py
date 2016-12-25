"""downloader_obj."""

import logging
import os
import requests
import threading
import uuid
from pprint import pformat
from queue import Queue

from PyQt5.QtCore import QObject, pyqtSignal

try:  # pragma: no cover
    import app_constants
    from downloader_item_obj import DownloaderItemObject
    from utils import makedirs_if_not_exists
except ImportError:
    from . import (
        app_constants,
    )
    from .downloader_item_obj import DownloaderItemObject
    from .utils import makedirs_if_not_exists

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class DownloaderObject(QObject):
    """A download manager.

    Emits signal item_finished with tuple of url and path to file when a download finishes

    Attributes:
        _inc_queue (Queue): Queue object contain item or dict of item and directory if defined.
        _browser_session: Robobrowser session if defined.
        _threads (list): List contain thread.
        item_finished (PyQt5.QtCore.pyqtSignal): signal when item finished.
        active_items (list): List of currently processed item.
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

        Args:
            item: Item to be added to queue.
            session: Optional robobrowser session.
            dir: Optional directory for item.

        Returns:
            A downloader item.
        """
        if isinstance(item, str):
            item = DownloaderItemObject(item)

        log_i("Adding item to download queue:\n{}".format(pformat(item.download_url)))
        if dir:
            DownloaderObject._inc_queue.put({'dir': dir, 'item': item})
        else:
            DownloaderObject._inc_queue.put(item)
        DownloaderObject._session = session

        return item

    @staticmethod
    def remove_file(filename):
        """Remove file and ignore any error when doing it.

        Args:
            filename: filename to be removed.
        """
        try:
            os.remove(filename)
        except:
            pass

    @staticmethod
    def _get_total_size(response):
        """get total size from requests response.

        Args:
            response (requests.Response): Response from request.
        """
        try:
            return int(response.headers['content-length'])
        except KeyError:
            return 0

    def _get_response(self, url):
        """get response from url.

        Args:
            url : Url of the response

        Returns:
            requests.Response: Response from url
        """
        if self._browser_session:
            r = self._browser_session.get(url, stream=True)
        else:
            r = requests.get(url, stream=True)
        return r

    def _get_item_and_temp_base(self):
        """get item and temporary folder if specified.

        Returns:
            tuple: (item, temp_base), where temp_base is the temporary folder.
        """
        item = self._inc_queue.get()
        temp_base = None
        if isinstance(item, dict):
            temp_base = item['dir']
            item = item['item']
        return item, temp_base

    def _get_filename(self, item, temp_base=None):
        """get filename based on input.

        Args:
            item: Download item
            temp_base: Optional temporary folder

        Returns:
            str: Edited filename
        """
        file_name = item.name if item.name else str(uuid.uuid4())
        invalid_chars = '\\/:*?"<>|'
        for x in invalid_chars:
            file_name = file_name.replace(x, '')
        file_name = os.path.join(self.base, file_name) if not temp_base else \
            os.path.join(temp_base, file_name)
        return file_name

    @staticmethod
    def _download_single_file(target_file, response, item, interrupt_state):
        """Download single file from url response and return changed item and interrupt state.

        Args:
            target_file: Target filename where url will be downloaded.
            response (requests.Response): Response from url.
            item: Download item.
            interrupt_state (bool): Interrupt state.

        Returns:
            tuple: (item, interrupt_state) where both variables
                is the changed variables from input.
        """
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
        """Custom rename file method.

        Args:
            filename: Target filename.
            filename_part: Temporary filename
            max_loop (int): Maximal loop  on error when renaming the file.

        Returns:
            str: Filename or filename_part
        """
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

    @staticmethod
    def _get_total_size_prediction(known_filesize, urls_len):
        """get total size prediction.

        Args:
            known_filesize (list): List of known filesize.
            urls_len (int): Number of urls_len

        Returns:
            int: Total size predictions.
        """
        if not known_filesize:  # empty list
            return 0
        if len(known_filesize) == urls_len:
            return int(sum(known_filesize))
        return int(sum(known_filesize) * urls_len / len(known_filesize))

    @staticmethod
    def _get_local_filesize(path):
        """Get local filesize.

        Args:
            path: Path of the file.

        Returns:
            filesize of the file or zero.
        """
        try:
            return os.path.getsize(path)
        except OSError:
            return 0

    def _download_item_with_multiple_dl_url(self, item, folder, interrupt_state):
        """download item with multiple download url.

        This method is modified from _download_item_with_single_dl_url method.
        Important changes::

        - Create new folder for download.
        - Method to calculate total size

        Args:
            item: Item with single download url.
            folder (str): Folder for downloaded file.
            interrupt_state (bool): Interrupt state

        Returns:
            Modified item
        """
        download_url = item.download_url
        total_known_filesize = []
        download_url_len = len(download_url)

        makedirs_if_not_exists(folder)
        for single_url in download_url:
            # response
            r = self._get_response(url=single_url)

            # get total size
            current_response_filesize = self._get_total_size(response=r)
            total_known_filesize.append(current_response_filesize)
            item.total_size = self._get_total_size_prediction(
                known_filesize=total_known_filesize, urls_len=download_url_len)

            url_basename = os.path.basename(single_url)
            target_file = os.path.join(folder, url_basename)
            target_filesize = self._get_local_filesize(path=target_file)
            if target_filesize == current_response_filesize and target_filesize != 0:
                item.current_size += current_response_filesize
                log_d('File is already downloaded.\n{}'.format(target_file))
            else:
                # downloading to temp file (file_name_part)
                item, interrupt_state = self._download_single_file(
                    target_file=target_file, response=r, item=item,
                    interrupt_state=interrupt_state
                )

        if not interrupt_state:
            item.current_state = item.FINISHED
            # emit
            item.file_rdy.emit(item)
            self.item_finished.emit(item)
        return item

    def _download_item_with_single_dl_url(self, item, filename, interrupt_state):
        """download item with single download url.

        Args:
            item: Item with single download url.
            filename (str): Filename for downloaded file.
            interrupt_state (bool): Interrupt state

        Returns:
            Modified item
        """
        # compatibility
        file_name = filename
        interrupt = interrupt_state
        download_url = item.download_url
        file_name_part = file_name + '.part'

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
        return item

    def _downloading(self):  # NOQA
        """The downloader.

        Put in a thread.
        """
        while True:
            log_d("Download items in queue: {}".format(self._inc_queue.qsize()))
            interrupt = False
            item, temp_base = self._get_item_and_temp_base()

            log_d("Starting item download")
            item.current_state = item.DOWNLOADING

            # filename
            file_name = self._get_filename(item=item, temp_base=temp_base)

            download_url = item.download_url
            log_d("Download url:\n{}".format(pformat(download_url)))
            self.active_items.append(item)

            if isinstance(item.download_url, list):
                # NOTE: file_name will be used as folder name when multiple url.
                item = self._download_item_with_multiple_dl_url(
                    item=item, folder=file_name, interrupt_state=interrupt)
            else:
                item = self._download_item_with_single_dl_url(
                    item=item, filename=file_name, interrupt_state=interrupt)
            log_d("Items in queue {}".format(self._inc_queue.empty()))
            log_d("Finished downloading:\n{}".format(pformat(download_url)))

            # remove recently added item from list
            self.active_items.remove(item)
            # task finished
            self._inc_queue.task_done()

    def start_manager(self, max_tasks):
        """Start download manager where max simultaneous is mask_tasks.

        Args:
            max_tasks (int): Maximal threading used.
        """
        log_i("Starting download manager with {} jobs".format(max_tasks))
        for x in range(max_tasks):
            thread = threading.Thread(
                target=self._downloading,
                name='Downloader {}'.format(x),
                daemon=True)
            thread.start()
            self._threads.append(thread)

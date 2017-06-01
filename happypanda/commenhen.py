"""commenhen module."""
import requests
import random
import time
import threading

from robobrowser import RoboBrowser
from structlog import getLogger
from fake_useragent import UserAgent

from . import app_constants

log = getLogger(__name__)
ua = UserAgent()


class CommenHen:
    """Contains common methods."""

    LOCK = threading.Lock()
    TIME_RAND = app_constants.GLOBAL_EHEN_TIME
    QUEUE = []
    COOKIES = {}
    LAST_USED = time.time()
    HEADERS = {'user-agent': ua.firefox}
    _QUEUE_LIMIT = 25
    _browser = RoboBrowser(user_agent=HEADERS['user-agent'], parser='html.parser')

    def begin_lock(self):
        """begin lock."""
        log.debug('locked')
        self.LOCK.acquire()
        t1 = time.time()
        while int(time.time() - self.LAST_USED) < self.TIME_RAND:
            t = random.randint(3, self.TIME_RAND)
            time.sleep(t)
        t2 = time.time() - t1
        log.debug("Slept for {}".format(t2))

    def end_lock(self):
        """end lock."""
        log.debug('unlocked')
        self.LAST_USED = time.time()
        self.LOCK.release()

    def add_to_queue(self, url='', proc=False, parse=True):
        """Add url the the queue.

        when the queue has reached _QUEUE_LIMIT entries will auto process
        :proc -> proccess queue
        :parse -> return parsed metadata
        """
        if url:
            self.QUEUE.append(url)
            log.info("Status on queue: {}/{}".format(len(self.QUEUE), self._QUEUE_LIMIT))
        try:
            if proc and parse:
                return self.parse_metadata(*self.process_queue())
            elif proc:
                return self.process_queue()

            if len(self.QUEUE) >= self._QUEUE_LIMIT and parse:
                return self.parse_metadata(*self.process_queue())
            elif len(self.QUEUE) >= self._QUEUE_LIMIT:
                return self.process_queue()
            else:
                return 1
        except TypeError:
            return None

    def process_queue(self):
        """Process the queue if entries exists, deletes entries.

        Note: Will only process _QUEUE_LIMIT entries (first come first out) while
            additional entries will get deleted.
        """
        log.info("Processing queue...")
        if len(self.QUEUE) < 1:
            return None

        try:
            if len(self.QUEUE) >= self._QUEUE_LIMIT:
                api_data, galleryid_dict = self.get_metadata(self.QUEUE[:self._QUEUE_LIMIT])
            else:
                api_data, galleryid_dict = self.get_metadata(self.QUEUE)
        except TypeError:
            return None
        finally:
            log.info("Flushing queue...")
            self.QUEUE.clear()
        return api_data, galleryid_dict

    @classmethod
    def login(cls, user, password):
        """login."""
        pass

    @classmethod
    def check_login(cls, cookies):
        """check login."""
        pass

    def check_existing_cookies(self, exprops):
        """check existing cookies and return.

        return None if nothing found.
        """
        if self.COOKIES:
            if self.check_login(self.COOKIES):
                return self.COOKIES
        elif exprops.cookies:
            if self.check_login(exprops.cookies):
                self.COOKIES.update(exprops.cookies)
                return self.COOKIES

    def check_cookie(self, cookie):
        """check cookie."""
        cookies = self.COOKIES.keys()
        present = []
        for c in cookie:
            if c in cookies:
                present.append(True)
            else:
                present.append(False)
        if not all(present):
            log.info("Updating cookies...")
            try:
                self.COOKIES.update(cookie)
            except requests.cookies.CookieConflictError:
                pass

    def handle_error(self, response):
        """handle error."""
        pass

    @classmethod
    def parse_metadata(cls, metadata_json, dict_metadata):
        """parse metadata.

        :metadata_json <- raw data provided by site
        :dict_metadata <- a dict with gallery id's as keys and url as value

        returns a dict with url as key and gallery metadata as value
        """
        pass

    def get_metadata(self, list_of_urls, cookies=None):
        """Fetch the metadata from the provided list of urls.

        Returns:
            raw api data and a dict with gallery id as key and url as value
        """
        pass

    @classmethod
    def apply_metadata(cls, gallery, data, append=True):
        """Appl fetched metadata to gallery."""
        pass

    def search(self, search_string, **kwargs):
        """Search for the provided string or list of hashes.

        Returns:
            a dict with search_string:[list of title & url tuples] of hits found or emtpy dict
            if no hits are found.
        """
        pass

"""chaika manager."""
import requests
import logging
import os

try:
    from dl_manager_obj import DLManagerObject
    from downloader_obj import DownloaderObject
    from hen_item import HenItem
except ImportError:
    from .dl_manager_obj import DLManagerObject
    from .downloader_obj import DownloaderObject
    from .hen_item import HenItem

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class ChaikaManager(DLManagerObject):
    """panda.chaika.moe manager."""

    def __init__(self):
        """init func."""
        super().__init__()
        self.url = "http://panda.chaika.moe/"
        self.api = "http://panda.chaika.moe/jsearch/?"

    def from_gallery_url(self, url):
        """from gallery url."""
        h_item = HenItem(self._browser.session)
        h_item.download_type = 0
        chaika_id = os.path.split(url)
        if chaika_id[1]:
            chaika_id = chaika_id[1]
        else:
            chaika_id = os.path.split(chaika_id[0])[1]

        if '/gallery/' in url:
            a_id = self._gallery_page(chaika_id, h_item)
            if not a_id:
                return
            self._archive_page(a_id, h_item)
        elif '/archive' in url:
            g_id = self._archive_page(chaika_id, h_item)
            if not g_id:
                return
            self._gallery_page(g_id, h_item)
        else:
            return
        h_item.commit_metadata()
        h_item.name = h_item.gallery_name + '.zip'
        DownloaderObject.add_to_queue(h_item, self._browser.session)
        return h_item

    def _gallery_page(self, g_id, h_item):
        """Return url to archive and updates h_item metadata from the /gallery/g_id page."""
        g_url = self.api + "gallery={}".format(g_id)
        r = requests.get(g_url)
        try:
            r.raise_for_status()
            chaika = r.json()

            h_item.update_metadata('title', chaika['title'])
            h_item.update_metadata('title_jpn', chaika['title_jpn'])
            h_item.update_metadata('category', chaika['category'])
            h_item.update_metadata('rating', chaika['rating'])
            h_item.update_metadata('filecount', chaika['filecount'])
            h_item.update_metadata('filesize', chaika['filesize'])
            h_item.update_metadata('posted', chaika['posted'])

            h_item.gallery_name = chaika['title']
            h_item.gallery_url = self.url + "gallery/{}".format(g_id)
            h_item.size = "{0:.2f} MB".format(chaika['filesize'] / 1048576)
            tags = []
            for t in chaika['tags']:
                tag = t.replace('_', ' ')
                tags.append(tag)
            h_item.update_metadata('tags', tags)

            if chaika['archives']:
                h_item.download_url = self.url + chaika['archives'][0]['download'][1:]
                return chaika['archives'][0]['id']
        except:
            log.exception("Error parsing chaika")

    def _archive_page(self, a_id, h_item):
        """Return url to gallery and updates h_item metadata from the /archive/a_id page."""
        a_url = self.api + "archive={}".format(a_id)
        r = requests.get(a_url)
        try:
            r.raise_for_status()
            chaika = r.json()
            return chaika['gallery']
        except:
            log.exception('Error parsing chaika')

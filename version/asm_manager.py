"""asmhentai module."""
import logging

from robobrowser.exceptions import RoboError

try:
    from app_constants import DOWNLOAD_TYPE_OTHER, VALID_GALLERY_CATEGORY
    from dl_manager_obj import DLManagerObject
    from downloader_obj import DownloaderObject
    from hen_item import HenItem
except ImportError:
    from .app_constants import DOWNLOAD_TYPE_OTHER, VALID_GALLERY_CATEGORY
    from .dl_manager_obj import DLManagerObject
    from .downloader_obj import DownloaderObject
    from .hen_item import HenItem

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


class AsmManager(DLManagerObject):
    """asmhentai manager.

    Attributes:
        url (str): Base url for manager.
    """

    url = 'http://asmhentai.com/'

    def ensure_browser_on_url(self, url):
        """open browser on input url if not already.

        url: Url where browser to open (or alreadery opened)
        """
        open_url = False  # assume not opening the url
        try:
            current_url = self._browser.url
            if current_url != url:
                open_url = True
        except RoboError:
            open_url = True
        if open_url:
            self._browser.open(url)

    @staticmethod
    def _find_tags(browser):
        """find tags from browser.

        Args:
            browser: Robobrowser instance.

        Returns:
            list: List of doujin/manga tags on the page.
        """
        sibling_tags = browser.select('.tags h3')
        tags = list(map(
            lambda x: (
                x.text.split(':')[0],
                x.parent.select('span')
            ),
            sibling_tags
        ))
        res = []
        for tag in tags:
            for span_tag in tag[1]:
                res.append('{}:{}'.format(tag[0], span_tag.text))
        return res

    def _get_metadata(self, g_url):
        """get metadata.

        for key to fill see HenItem class.

        Args:
            g_url: Gallery url.

        Returns:
            dict: Metadata from gallery url.
        """
        self.ensure_browser_on_url(url=g_url)
        html_soup = self._browser
        res = {}
        res['title'] = html_soup.select('.info h1')[0].text
        res['title_jpn'] = html_soup.select('.info h2')[0].text
        res['filecount'] = html_soup.select('.pages')[0].text.split('Pages:')[1].strip()
        res['tags'] = self._find_tags(browser=self._browser)
        if any('Category:' in x for x in res['tags']):
            res['category'] = [tag.split(':')[1] for tag in res['tags'] if 'Category:' in tag][0]
        return res

    def _get_dl_urls(self, g_url):
        """get image urls from gallery url.

        Args:
            g_url: Gallery url.

        Returns:
            list: Image from gallery url.
        """
        # ensure the url
        self.ensure_browser_on_url(url=g_url)
        links = self._browser.select('.preview_thumb a')
        links = [x.get('href') for x in links]
        # link = '/gallery/168260/22/'
        links = [(x.split('/')[2], x.split('/')[-2]) for x in links]
        imgs = list(map(
            lambda x:
            'http://images.asmhentai.com/006/{}/{}.jpg'.format(x[0], x[1]),
            links
        ))
        return imgs

    @staticmethod
    def _set_metadata(h_item, dict_metadata):
        """set metadata on item from dict_metadata."""
        keys = ['title_jpn', 'title', 'filecount', "tags"]
        for key in keys:
            value = dict_metadata.get(key, None)
            if value:
                h_item.update_metadata(key=key, value=value)
        # for hitem gallery value
        catg_val = dict_metadata.get('category', None)
        category_dict = {vcatg.lower(): vcatg for vcatg in VALID_GALLERY_CATEGORY}
        category_value = category_dict.get(catg_val, catg_val)
        if category_value and category_value in VALID_GALLERY_CATEGORY:
            h_item.update_metadata(key='category', value=category_value)
        elif category_value:
            log_w('Unknown manga category:{}'.format(category_value))

        return h_item

    def from_gallery_url(self, g_url):
        """Find gallery download url and puts it in download queue.

        Args:
            g_url: Gallery url.

        Returns:
            Download item
        """
        h_item = HenItem(self._browser.session)
        h_item.download_type = DOWNLOAD_TYPE_OTHER
        h_item.gallery_url = g_url
        # ex/g.e
        log_d("Opening {}".format(g_url))
        dict_metadata = self._get_metadata(g_url=g_url)
        h_item.thumb_url = 'http:' + self._browser.select('.cover img')[0].get('src')
        h_item.fetch_thumb()

        # name
        h_item.gallery_name = dict_metadata['title']
        # name is the name folder
        h_item.name = dict_metadata['title']

        # get dl link
        log_d("Getting download URL!")
        h_item.download_url = self._get_dl_urls(g_url=g_url)

        h_item = self._set_metadata(h_item=h_item, dict_metadata=dict_metadata)

        DownloaderObject.add_to_queue(h_item, self._browser.session)
        return h_item

    @classmethod
    def apply_metadata(cls, gallery, data):
        """Apply metadata to gallery.

        This is this module's method for ehen module.

        Args:
            gallery: Gallery.
            data: Metatadata of the gallery.

        Returns:
            Edited gallery.
        """
        pass

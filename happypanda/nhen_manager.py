"""nhentai module."""
import logging
import os

try:
    from app_constants import DOWNLOAD_TYPE_OTHER
    from dl_manager_obj import DLManagerObject
    from downloader_obj import DownloaderObject
    from hen_item import HenItem
    from asm_manager import AsmManager
except ImportError:
    from .app_constants import DOWNLOAD_TYPE_OTHER
    from .dl_manager_obj import DLManagerObject
    from .downloader_obj import DownloaderObject
    from .hen_item import HenItem
    from .asm_manager import AsmManager

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


class NhenManager(DLManagerObject):
    """asmhentai manager.

    Attributes:
        url (str): Base url for manager.
    """

    url = 'https://nhentai.net/'

    @staticmethod
    def _get_filecount(html_soup):
        info_divs = [x for x in html_soup.select('#info div') if ' pages' in x.text]
        filecount_div_text = info_divs[0].text
        return filecount_div_text.split(' pages')[0].strip()

    @staticmethod
    def _get_tag_dict(html_soup):
        """get tag dict from html soup.

        Args:
            html_soup: HTML as BeautifulSoup obj.
        Returns:
            dict: Tags in dict format.
        """
        tag_dict = {}
        tags_divs = html_soup.select('.tag-container')
        for tags_div in tags_divs:
            contents = tags_div.contents
            key = contents[0].strip().split(':')[0]
            value_divs = contents[1].contents
            value = []
            for val_div in value_divs:
                value.append(val_div.text.rsplit('(', 1)[0].strip())
            if value:
                tag_dict[key] = value
        return tag_dict

    @staticmethod
    def _find_tags(browser):
        """find tags from browser.

        Args:
            browser: Robobrowser instance.

        Returns:
            List of doujin/manga tags on the page.
        """
        html_soup = browser
        tag_dict = NhenManager._get_tag_dict(html_soup=html_soup)
        res = []
        for key in tag_dict:
            for value in tag_dict[key]:
                res.append('{}:{}'.format(key, value))
        return res

    @staticmethod
    def _get_category(tags):
        category = None
        if any('Categories:' in x for x in tags):
            category = [tag.split(':')[1] for tag in tags if 'Categories:' in tag][0]
            category = category.title()
        return category

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
        res['title'] = html_soup.select('h1')[0].text
        res['title_jpn'] = html_soup.select('h2')[0].text
        res['filecount'] = self._get_filecount(html_soup=html_soup)
        res['tags'] = self._find_tags(browser=self._browser)
        category = self._get_category(tags=res['tags'])
        if category:
            res['category'] = category
        return res

    def _get_first_image_data(self, link_parts):
        """get server id.

        Args:
            link_parts (tuple): Tuple of (gallery_id, url_basename)

        Returns:
            dict: Info about extension and server id
        """
        gallery_id, url_basename = link_parts
        url = 'https://nhentai.net/g/{gallery_id}/{url_basename}/'.format(
            gallery_id=gallery_id, url_basename=url_basename)
        self._browser.open(url)
        link_tags = self._browser.select('#image-container img')
        # e.g.
        # link_tag_src = '//i.nhentai.net/galleries/1018135/1.png'
        link_tag_src = link_tags[0].get('src')
        return {
            "server_id": link_tag_src.split('/galleries/')[1].split('/')[0],
            'ext': os.path.splitext(link_tag_src)[1]
        }

    def _get_dl_urls(self, g_url):
        """get image urls from gallery url.

        Args:
            g_url: Gallery url.

        Returns:
            Image from gallery url.
        """
        # ensure the url
        self.ensure_browser_on_url(url=g_url)
        links = self._browser.select('.thumb-container a.gallerythumb')
        links = [x.get('href') for x in links]
        # link = '/g/168260/22/'  # example
        links_parts = AsmManager._split_href_links_to_parts(links)
        image1_data = self._get_first_image_data(links_parts[0])
        image_ext = image1_data['ext']
        server_id = image1_data['server_id']
        imgs = list(map(
            lambda x:
            'https://i.nhentai.net/galleries/{}/{}{}'.format(server_id, x[1], image_ext),
            links_parts
        ))
        return imgs

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
        h_item.thumb_url = 'https:{}'.format(self._browser.select('#cover img')[0].get('src'))
        h_item.fetch_thumb()

        # name
        h_item.gallery_name = dict_metadata['title']
        # name is the name folder
        h_item.name = dict_metadata['title']

        # get dl link
        log_d("Getting download URL!")
        h_item.download_url = self._get_dl_urls(g_url=g_url)

        h_item = AsmManager._set_ehen_metadata(h_item=h_item, dict_metadata=dict_metadata)

        DownloaderObject.add_to_queue(h_item, self._browser.session)
        return h_item

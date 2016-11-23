"""hen manager."""
import logging

try:
    import app_constants
    import settings
    from dl_manager_obj import DLManagerObject
    from downloader_obj import DownloaderObject
    from ehen import EHen
    from exhen import ExHen
    from hen_item import HenItem
except ImportError:
    from . import (
        app_constants,
        settings,
    )
    from .dl_manager_obj import DLManagerObject
    from .downloader_obj import DownloaderObject
    from .ehen import EHen
    from .exhen import ExHen
    from .hen_item import HenItem

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class HenManager(DLManagerObject):
    """G.e or Ex gallery manager."""

    def __init__(self):
        """init func."""
        super().__init__()
        self.e_url = 'http://g.e-hentai.org/'

        exprops = settings.ExProperties()
        cookies = exprops.cookies
        if not cookies:
            if exprops.username and exprops.password:
                cookies = EHen.login(exprops.username, exprops.password)
            else:
                raise app_constants.NeedLogin

        self._browser.session.cookies.update(cookies)

    def _archive_url_d(self, gid, token, key):
        """Return the archiver download url."""
        base = self.e_url + 'archiver.php?'
        d_url = base + 'gid=' + str(gid) + '&token=' + token + '&or=' + key
        return d_url

    def _torrent_url_d(self, gid, token):
        """Return the torrent download url and filename."""
        base = self.e_url + 'gallerytorrents.php?'
        torrent_page = base + 'gid=' + str(gid) + '&t=' + token
        self._browser.open(torrent_page)
        torrents = self._browser.find_all('table')
        if not torrents:
            return
        torrent = None  # [seeds, url, name]
        for t in torrents:
            parts = t.find_all('tr')
            # url & name
            url = parts[2].td.a.get('href')
            name = parts[2].td.a.text + '.torrent'

            # seeds peers etc... NOT uploader
            meta = [x.text for x in parts[0].find_all('td')]
            seed_txt = meta[3]
            # extract number
            seeds = int(seed_txt.split(' ')[1])

            if not torrent:
                torrent = [seeds, url, name]
            else:
                if seeds > torrent[0]:
                    torrent = [seeds, url, name]

        _, url, name = torrent  # just get download url

        # TODO: make user choose?
        return url, name

    def from_gallery_url(self, g_url):  # NOQA
        """Find gallery download url and puts it in download queue."""
        if 'exhentai' in g_url:
            hen = ExHen(settings.ExProperties().cookies)
        else:
            hen = EHen()
        log_d("Using {}".format(hen.__repr__()))
        api_metadata, gallery_gid_dict = hen.add_to_queue(g_url, True, False)
        gallery = api_metadata['gmetadata'][0]

        h_item = HenItem(self._browser.session)
        h_item.gallery_url = g_url
        h_item.metadata = EHen.parse_metadata(api_metadata, gallery_gid_dict)
        try:
            h_item.metadata = h_item.metadata[g_url]
        except KeyError:
            raise app_constants.WrongURL
        h_item.thumb_url = gallery['thumb']
        h_item.gallery_name = gallery['title']
        h_item.size = "{0:.2f} MB".format(gallery['filesize'] / 1048576)

        if self.ARCHIVE:
            h_item.download_type = 0
            d_url = self._archive_url_d(gallery['gid'], gallery['token'], gallery['archiver_key'])

            # ex/g.e
            self._browser.open(d_url)
            log_d("Opening {}".format(d_url))
            download_btn = self._browser.get_form()
            if download_btn:
                log_d("Parsing download button!")
                f_div = self._browser.find('div', id='db')
                divs = f_div.find_all('div')
                h_item.cost = divs[0].find('strong').text
                h_item.cost = divs[0].find('strong').text
                h_item.size = divs[1].find('strong').text
                self._browser.submit_form(download_btn)
                log_d("Submitted download button!")

            if self._browser.response.status_code == 302:
                self._browser.open(self._browser.response.headers['location'], "post")

            # get dl link
            log_d("Getting download URL!")
            continue_p = self._browser.find("p", id="continue")
            if continue_p:
                dl = continue_p.a.get('href')
            else:
                dl_a = self._browser.find('a')
                dl = dl_a.get('href')
            self._browser.open(dl)
            succes_test = self._browser.find('p')
            if succes_test and 'successfully' in succes_test.text:
                gallery_dl = self._browser.find('a').get('href')
                gallery_dl = self._browser.url.split('/archive')[0] + gallery_dl
                f_name = succes_test.find('strong').text
                h_item.download_url = gallery_dl
                h_item.fetch_thumb()
                h_item.name = f_name
                DownloaderObject.add_to_queue(h_item, self._browser.session)
                return h_item

        elif self.TORRENT:
            h_item.download_type = 1
            h_item.torrents_found = int(gallery['torrentcount'])
            h_item.fetch_thumb()
            if h_item.torrents_found > 0:
                g_id_token = EHen.parse_url(g_url)
                if g_id_token:
                    url_and_file = self._torrent_url_d(g_id_token[0], g_id_token[1])
                    if url_and_file:
                        h_item.download_url = url_and_file[0]
                        h_item.name = url_and_file[1]
                        DownloaderObject.add_to_queue(h_item, self._browser.session)
                        return h_item
            else:
                return h_item
        return False

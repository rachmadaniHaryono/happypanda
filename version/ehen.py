"""ehen module."""
import requests
import logging
import random
import time
import html
import re as regex

from bs4 import BeautifulSoup
from datetime import datetime

try:
    import app_constants
    import utils
    from commenhen import CommenHen
    from settings import ExProperties
except ImportError:
    from . import (
        app_constants,
        utils,
    )
    from .settings import ExProperties
    from .commenhen import CommenHen

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class EHen(CommenHen):
    """Fetches galleries from ehen."""

    def __init__(self, cookies=None):
        """init func."""
        self.cookies = cookies
        self.e_url = "http://g.e-hentai.org/api.php"
        self.e_url_o = "http://g.e-hentai.org/"

    @classmethod  # NOQA
    def apply_metadata(cls, g, data, append=True):
        """Apply metadata to gallery, returns gallery."""
        if app_constants.USE_JPN_TITLE:
            try:
                title = data['title']['jpn']
            except KeyError:
                title = data['title']['def']
        else:
            title = data['title']['def']

        if 'Language' in data['tags']:
            try:
                lang = [
                    x for x in data['tags']['Language'] if not x == 'translated'
                ][0].capitalize()
            except IndexError:
                lang = ""
        else:
            lang = ""

        title_artist_dict = utils.title_parser(title)
        if not append:
            g.title = title_artist_dict['title']
            if title_artist_dict['artist']:
                g.artist = title_artist_dict['artist']
            g.language = title_artist_dict['language'].capitalize()
            if 'Artist' in data['tags']:
                g.artist = data['tags']['Artist'][0].capitalize()
            if lang:
                g.language = lang
            g.type = data['type']
            g.pub_date = data['pub_date']
            g.tags = data['tags']
            if 'url' in data:
                g.link = data['url']
            else:
                g.link = g.temp_url
        else:
            if not g.title:
                g.title = title_artist_dict['title']
            if not g.artist:
                g.artist = title_artist_dict['artist']
                if 'Artist' in data['tags']:
                    g.artist = data['tags']['Artist'][0].capitalize()
            if not g.language:
                g.language = title_artist_dict['language'].capitalize()
                if lang:
                    g.language = lang
            if not g.type or g.type == 'Other':
                g.type = data['type']
            if not g.pub_date:
                g.pub_date = data['pub_date']
            if not g.tags:
                g.tags = data['tags']
            else:
                for ns in data['tags']:
                    if ns in g.tags:
                        for tag in data['tags'][ns]:
                            if tag not in g.tags[ns]:
                                g.tags[ns].append(tag)
                    else:
                        g.tags[ns] = data['tags'][ns]
            if 'url' in data:
                if not g.link:
                    g.link = data['url']
            else:
                if not g.link:
                    g.link = g.temp_url
        return g

    @classmethod
    def check_login(cls, cookies):
        """Check if user is logged in."""
        if cookies.get('ipb_member_id') and cookies.get('ipb_pass_hash'):
            return 2
        elif cookies.get('ipb_session_id'):
            return 1
        else:
            return 0

    def handle_error(self, response):
        """handle error."""
        content_type = response.headers['content-type']
        text = response.text
        if 'image/gif' in content_type:
            err_msg = 'Provided exhentai credentials are incorrect!'
            try:
                app_constants.NOTIF_BAR.add_text(err_msg)
            except AttributeError:
                print(err_msg)
                if app_constants.NOTIF_BAR is not None:
                    print('Unrcognized app_constants.NOTIF_BAR.')
                    raise NotImplementedError
            log_e('Provided exhentai credentials are incorrect!')
            time.sleep(5)
            return False
        elif 'text/html' and 'Your IP address has been' in text:
            app_constants.NOTIF_BAR.add_text(
                "Your IP address has been temporarily banned from g.e-/exhentai")
            log_e('Your IP address has been temp banned from g.e- and ex-hentai')
            time.sleep(5)
            return False
        elif 'text/html' in content_type and 'You are opening' in text:
            time.sleep(random.randint(10, 50))
        return True

    @classmethod
    def parse_url(cls, url):
        """Parse url into a list of gallery id and token."""
        gallery_id_token = regex.search('(?<=g/)([0-9]+)/([a-zA-Z0-9]+)', url)
        if not gallery_id_token:
            log_e("Error extracting g_id and g_token from url: {}".format(url))
            return None
        gallery_id_token = gallery_id_token.group()
        gallery_id, gallery_token = gallery_id_token.split('/')
        parsed_url = [int(gallery_id), gallery_token]
        return parsed_url

    def get_metadata(self, list_of_urls, cookies=None):  # NOQA
        """Fetches the metadata from the provided list of urls through the official API.

        Returns:
            raw api data and a dict with gallery id as key and url as value
        """
        assert isinstance(list_of_urls, list)
        if len(list_of_urls) > 25:
            log_e('More than 25 urls are provided. Aborting.')
            return None

        payload = {"method": "gdata", "gidlist": [], "namespace": 1}
        dict_metadata = {}
        for url in list_of_urls:
            parsed_url = EHen.parse_url(url.strip())
            if parsed_url:
                dict_metadata[parsed_url[0]] = url  # gallery id
                payload['gidlist'].append(parsed_url)

        if payload['gidlist']:
            self.begin_lock()
            try:
                if cookies:
                    self.check_cookie(cookies)
                    r = requests.post(
                        self.e_url, json=payload, timeout=30, headers=self.HEADERS,
                        cookies=self.COOKIES)
                else:
                    r = requests.post(self.e_url, json=payload, timeout=30, headers=self.HEADERS)
            except requests.ConnectionError as err:
                self.end_lock()
                log_e("Could not fetch metadata: {}".format(err))
                raise app_constants.MetadataFetchFail("connection error")
            self.end_lock()
            if not self.handle_error(r):
                return 'error'
        else:
            return None
        try:
            r.raise_for_status()
        except:
            log.exception('Could not fetch metadata: status error')
            return None
        return r.json(), dict_metadata

    @classmethod  # NOQA
    def parse_metadata(cls, metadata_json, dict_metadata):
        """Parse metadata.

        :metadata_json <- raw data provided by E-H API
        :dict_metadata <- a dict with gallery id's as keys and url as value

        returns a dict with url as key and gallery metadata as value
        """
        def invalid_token_check(g_dict):
            if 'error' in g_dict:
                return False
            else:
                return True

        parsed_metadata = {}
        for gallery in metadata_json['gmetadata']:
            url = dict_metadata[gallery['gid']]
            if invalid_token_check(gallery):
                new_gallery = {}

                def fix_titles(text):
                    t = html.unescape(text)
                    t = " ".join(t.split())
                    return t
                try:
                    gallery['title_jpn'] = fix_titles(gallery['title_jpn'])
                    gallery['title'] = fix_titles(gallery['title'])
                    new_gallery['title'] = {'def': gallery['title'], 'jpn': gallery['title_jpn']}
                except KeyError:
                    gallery['title'] = fix_titles(gallery['title'])
                    new_gallery['title'] = {'def': gallery['title']}

                new_gallery['type'] = gallery['category']
                new_gallery['pub_date'] = datetime.fromtimestamp(int(gallery['posted']))
                tags = {'default': []}
                for t in gallery['tags']:
                    if ':' in t:
                        ns_tag = t.split(':')
                        namespace = ns_tag[0].capitalize()
                        tag = ns_tag[1].lower().replace('_', ' ')
                        if namespace not in tags:
                            tags[namespace] = []
                        tags[namespace].append(tag)
                    else:
                        tags['default'].append(t.lower().replace('_', ' '))
                new_gallery['tags'] = tags
                parsed_metadata[url] = new_gallery
            else:
                log_e("Error in received response with URL: {}".format(url))

        return parsed_metadata

    @classmethod
    def login(cls, user, password):
        """Log into g.e-h."""
        log_i("Attempting EH Login")
        eh_c = {}
        exprops = ExProperties()
        if cls.COOKIES:
            if cls.check_login(cls.COOKIES):
                return cls.COOKIES
        elif exprops.cookies:
            if cls.check_login(exprops.cookies):
                cls.COOKIES.update(exprops.cookies)
                return cls.COOKIES

        p = {
            'CookieDate': '1',
            'b': 'd',
            'bt': '1-1',
            'UserName': user,
            'PassWord': password
        }

        eh_c = requests.post(
            'https://forums.e-hentai.org/index.php?act=Login&CODE=01', data=p).cookies.get_dict()
        exh_c = requests.get('http://exhentai.org', cookies=eh_c).cookies.get_dict()

        eh_c.update(exh_c)

        if not cls.check_login(eh_c):
            log_w("EH login failed")
            raise app_constants.WrongLogin

        log_i("EH login succes")
        exprops.cookies = eh_c
        exprops.username = user
        exprops.password = password
        exprops.save()
        cls.COOKIES.update(eh_c)

        return eh_c

    def search(self, search_string, **kwargs):  # NOQA
        """Search ehentai for the provided string or list of hashes.

        Returns:
            a dict with search_string:[list of title & url tuples] of hits found or emtpy dict
            if no hits are found.
        """
        assert isinstance(search_string, (str, list))
        if isinstance(search_string, str):
            search_string = [search_string]

        cookies = kwargs.pop('cookies', {})

        def no_hits_found_check(soup):
            """return true if hits are found."""
            if not soup:
                log_e("There is no soup!")
            f_div = soup.body.find_all('div')
            for d in f_div:
                if 'No hits found' in d.text:
                    return False
            return True

        def do_filesearch(filepath):
            file_search_delay = 5
            if "exhentai" in self.e_url_o:
                f_url = "http://ul.exhentai.org/image_lookup.php/"
            else:
                f_url = "https://upload.e-hentai.org/image_lookup.php/"
            if cookies:
                self.check_cookie(cookies)
                self._browser.session.cookies.update(self.COOKIES)
            log_d("searching with color img: {}".format(filepath))
            files = {'sfile': open(filepath, 'rb')}
            values = {'fs_similar': '1'}
            if app_constants.INCLUDE_EH_EXPUNGED:
                values['fs_exp'] = '1'
            try:
                r = self._browser.session.post(f_url, files=files, data=values)
            except requests.ConnectionError:
                time.sleep(file_search_delay + 3)
                r = self._browser.session.post(f_url, files=files, data=values)

            s = BeautifulSoup(r.text, "html.parser")
            if "Please wait a bit longer between each file search." in "{}".format(s):
                log_e("Retrying filesearch due to interval response with delay: {}".format(
                    file_search_delay))
                time.sleep(file_search_delay)
                s = do_filesearch(filepath)
            return s

        found_galleries = {}
        log_i('Initiating hash search on ehentai')
        log_d("search strings: ".format(search_string))
        for h in search_string:
            log_d('Hash search: {}'.format(h))
            self.begin_lock()
            try:
                if 'color' in kwargs:
                    soup = do_filesearch(h)
                else:
                    hash_url = self.e_url_o + '?f_shash='
                    hash_search = hash_url + h
                    if app_constants.INCLUDE_EH_EXPUNGED:
                        hash_search + '&fs_exp=1'
                    if cookies:
                        self.check_cookie(cookies)
                        r = requests.get(
                            hash_search, timeout=30, headers=self.HEADERS, cookies=self.COOKIES)
                    else:
                        r = requests.get(hash_search, timeout=30, headers=self.HEADERS)
                    log_d("searching with greyscale img: {}".format(hash_search))
                    if not self.handle_error(r):
                        return 'error'
                    soup = BeautifulSoup(r.text, "html.parser")
            except requests.ConnectionError as err:
                self.end_lock()
                log.exception("Could not search for gallery: {}".format(err))
                raise app_constants.MetadataFetchFail("connection error")
            self.end_lock()

            if not no_hits_found_check(soup):
                log_e('No hits found with hash/image: {}'.format(h))
                continue
            log_i('Parsing html')
            try:
                if soup.body:
                    found_galleries[h] = []
                    # list view or grid view
                    type = soup.find(attrs={'class': 'itg'}).name
                    if type == 'div':
                        visible_galleries = soup.find_all('div', attrs={'class': 'id1'})
                    elif type == 'table':
                        visible_galleries = soup.find_all('div', attrs={'class': 'it5'})

                    log_i('Found {} visible galleries'.format(len(visible_galleries)))
                    for gallery in visible_galleries:
                        title = gallery.text
                        g_url = gallery.a.attrs['href']
                        found_galleries[h].append((title, g_url))
            except AttributeError:
                log.exception('Unparseable html')
                log_d("\n{}\n".format(soup.prettify()))
                continue

        if found_galleries:
            log_i('Found {} out of {} galleries'.format(len(found_galleries), len(search_string)))
            return found_galleries
        else:
            log_w('Could not find any galleries')
            return {}

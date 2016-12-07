"""chaika hen."""
import requests
import logging
import re as regex
from json import JSONDecodeError


try:
    import app_constants
    from commenhen import CommenHen
    from ehen import EHen
except ImportError:
    from . import (
        app_constants,
    )
    from .commenhen import CommenHen
    from .ehen import EHen

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class ChaikaHen(CommenHen):
    """Fetches gallery metadata from panda.chaika.moe."""

    g_url = "http://panda.chaika.moe/gallery/"
    g_api_url = "http://panda.chaika.moe/jsearch?gallery="
    a_api_url = "http://panda.chaika.moe/jsearch?archive="

    def __init__(self):
        """init func."""
        self.url = "http://panda.chaika.moe/jsearch?sha1="
        self._QUEUE_LIMIT = 1

    def search(self, search_string, **kwargs):
        """search.

        search_string should be a list of hashes
        will actually just put urls together
        return search_string:[list of title & url tuples]
        """
        if not isinstance(search_string, (list, tuple)):
            search_string = [search_string]
        x = {}
        for h in search_string:
            x[h] = [("", self.url + h)]
        return x

    @staticmethod
    def _get_json_response(response):
        """get json response."""
        try:
            return response.json()
        except JSONDecodeError:
            log_w('Error decoding json for following url:\n{}'.format(response.url))

    def get_metadata(self, list_of_urls):  # NOQA
        """Fetch the metadata from the provided list of urls through the official API.

        Returns:
            raw api data and a dict with gallery id as key and url as value
        """
        data = []
        g_id_data = {}
        g_id = 1
        for url in list_of_urls:
            hash_search = True
            chaika_g_id = None
            old_url = url
            re_string = (
                "^(http\:\/\/|https\:\/\/)?(www\.)?([^\.]?)"
                "(panda\.chaika\.moe\/(archive|gallery)\/[0-9]+)"  # to validate chaika urls
            )
            if regex.match(re_string, url):
                g_or_a_id = regex.search("([0-9]+)", url).group()
                if 'gallery' in url:
                    url = self.g_api_url + g_or_a_id
                    chaika_g_id = g_or_a_id
                else:
                    url = self.a_api_url + g_or_a_id
                hash_search = False
            try:
                try:
                    r = requests.get(url)
                except requests.ConnectionError as err:
                    log_e("Could not fetch metadata: {}".format(err))
                    raise app_constants.MetadataFetchFail("connection error")
                r.raise_for_status()
                if not self._get_json_response(response=r):
                    return None
                if hash_search:
                    g_data = r.json()[0]  # TODO: multiple archives can be returned! Please fix!
                else:
                    g_data = r.json()
                if chaika_g_id:
                    g_data['gallery'] = chaika_g_id
                g_data['gid'] = g_id
                data.append(g_data)
                if hash_search:
                    g_id_data[g_id] = url
                else:
                    g_id_data[g_id] = old_url
                g_id += 1
            except requests.RequestException:
                log_e("Could not fetch metadata: status error")
                return None
        return data, g_id_data

    @classmethod
    def parse_metadata(cls, data, dict_metadata):
        """parse metadata.

        :data <- raw data provided by site
        :dict_metadata <- a dict with gallery id's as keys and url as value

        returns a dict with url as key and gallery metadata as value
        """
        eh_api_data = {"gmetadata": []}
        g_urls = {}
        for d in data:
            eh_api_data['gmetadata'].append(d)
            # to get correct gallery urls
            g_urls[dict_metadata[d['gid']]] = cls.g_url + str(d['gallery']) + '/'
        p_metadata = EHen.parse_metadata(eh_api_data, dict_metadata)
        # to get correct gallery urls instead of .....jsearch?sha1=----long-hash----
        for url in g_urls:
            p_metadata[url]['url'] = g_urls[url]
        return p_metadata

    @classmethod
    def apply_metadata(cls, g, data, append=True):
        """Apply metadata to gallery, returns gallery."""
        return EHen.apply_metadata(g, data, append)

"""exhen module."""
import logging

try:
    from ehen import EHen
except ImportError:
    from .ehen import EHen

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class ExHen(EHen):
    """Fetch gallery metadata from exhen."""

    def __init__(self, cookies=None):
        """init func."""
        super().__init__(cookies)
        self.e_url = "http://exhentai.org/api.php"
        self.e_url_o = "http://exhentai.org/"

    def get_metadata(self, list_of_urls):
        """get metadata."""
        return super().get_metadata(list_of_urls, self.cookies)

    def search(self, hash_string, **kwargs):
        """search."""
        return super().search(hash_string, cookies=self.cookies, **kwargs)

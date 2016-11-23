"""exhen manager."""
import logging

try:
    from hen_manager import HenManager
except ImportError:
    from .hen_manager import HenManager

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class ExHenManager(HenManager):
    """ExHentai Manager."""

    def __init__(self):
        """init func."""
        super().__init__()
        self.e_url = "http://exhentai.org/"

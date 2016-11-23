"""torrent item."""
import logging

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class TorrentItem:
    """TorrentItem."""

    def __init__(self, url, name="", date=None, size=None, seeds=None, peers=None, uploader=None):
        """__init__."""
        self.url = url
        self.name = name
        self.date = date
        self.size = size
        self.seeds = seeds
        self.peers = peers
        self.uploader = uploader

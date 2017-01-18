"""torrent item."""


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

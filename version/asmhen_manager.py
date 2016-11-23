"""asmhentai module."""
try:
    from dl_manager import DLManager
    from pewnet import (
        DOWNLOAD_TYPE_OTHER,
        HenItem,
    )
except ImportError:
    from .dl_manager import DLManager
    from .pewnet import (
        DOWNLOAD_TYPE_OTHER,
        HenItem,
    )


class AsmManager(DLManager):
    """asmhentai manager."""

    url = 'http://asmhentai.com/'

    def from_gallery_url(self, url):
        """get obj from gallery url."""
        h_item = HenItem(self._browser.session)
        h_item.download_type = DOWNLOAD_TYPE_OTHER

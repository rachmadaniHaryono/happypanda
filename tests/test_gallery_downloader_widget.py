"""test module."""
from itertools import product
from unittest import mock

import pytest


@pytest.mark.parametrize(
    'url_and_exp_res, url_inserter_text',
    product(
        [
            ('', None),
            ('www.example.com', 'www.example.com'),
            ('WWW.EXAMPLE.COM', 'www.example.com'),
            (None, None),
            (mock.Mock(), None)
        ],
        [mock.Mock(), None]
    )
)
def test_get_url(url_and_exp_res, url_inserter_text):
    """test method."""
    url, exp_res = url_and_exp_res
    url_inserter = mock.Mock()
    url_inserter.text.return_value = url_inserter_text
    #
    if not url or url is None:
        if hasattr(url_inserter_text, 'lower'):
            exp_res = url_inserter.text.return_value.lower.return_value
        else:
            exp_res = None
    elif isinstance(url, mock.Mock):
        exp_res = url.lower.return_value
    #
    with mock.patch(
            'happypanda.gallery_downloader_widget.GalleryDownloaderWidget.__init__',
            return_value=None):
        from happypanda.gallery_downloader_widget import GalleryDownloaderWidget
        obj = GalleryDownloaderWidget()
        obj.url_inserter = url_inserter
        res = obj._get_url(url=url)
        assert res == exp_res
        if not url and not url_inserter_text:
            url_inserter.assert_has_calls([
                mock.call.text()
            ])
        elif not url:
            url_inserter.assert_has_calls([
                mock.call.text(),
                mock.call.clear(),
            ])
            if url_inserter_text:
                url_inserter_text.lowerassert_called_once_with()

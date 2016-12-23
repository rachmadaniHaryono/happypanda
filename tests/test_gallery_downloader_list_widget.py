"""test module."""
from unittest import mock

import pytest


@pytest.mark.parametrize(
    'text, exp_arg',
    [
        ('url1', 'url1'),
        (['url1', 'url2'], 'url1\nurl2'),

    ]
)
def test_set_clipboard_text(text, exp_arg):
    clipboard = mock.Mock()
    from version.gallery_downloader_list_widget import GalleryDownloaderListWidget
    GalleryDownloaderListWidget.set_clipboard_text(clipboard=clipboard, text=text)
    clipboard.setText.assert_called_once_with(exp_arg)

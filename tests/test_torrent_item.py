"""test module."""
from unittest import mock


def test_init():
    """test init."""
    kwargs = {
        'url': mock.Mock(),
        'name': mock.Mock(),
        'date': mock.Mock(),
        'size': mock.Mock(),
        'peers': mock.Mock(),
        'uploader': mock.Mock(),
    }
    from version.torrent_item import TorrentItem
    obj = TorrentItem(**kwargs)
    for key in kwargs:
        assert getattr(obj, key) == kwargs[key]

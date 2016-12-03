"""test module."""
from unittest import mock

import pytest


@pytest.mark.parametrize('hen_download_type', [0, 1])
def test_init(hen_download_type):
    """test init."""
    with mock.patch('version.dl_manager_obj.app_constants') as m_ac:
        m_ac.HEN_DOWNLOAD_TYPE = hen_download_type
        from version.dl_manager_obj import DLManagerObject
        obj = DLManagerObject()
        if hen_download_type == 0:
            assert obj.ARCHIVE
            assert not obj.TORRENT
        elif hen_download_type == 1:
            assert not obj.ARCHIVE
            assert obj.TORRENT


def test_error():
    """test method."""
    from version.dl_manager_obj import DLManagerObject
    obj = DLManagerObject()
    obj._error()


def test_from_gallery_url():
    """test method."""
    from version.dl_manager_obj import DLManagerObject
    obj = DLManagerObject()
    with pytest.raises(NotImplementedError):
        obj.from_gallery_url(url=mock.Mock())

"""test module."""
from unittest import mock

import pytest


@pytest.mark.parametrize('constant_dl_type', ['archive', 'torrent', 'other'])
def test_init(constant_dl_type):
    """test init."""
    with mock.patch('version.dl_manager_obj.app_constants') as m_ac:
        if constant_dl_type == 'archive':
            m_ac.HEN_DOWNLOAD_TYPE = m_ac.DOWNLOAD_TYPE_ARCHIVE
        elif constant_dl_type == 'torrent':
            m_ac.HEN_DOWNLOAD_TYPE = m_ac.DOWNLOAD_TYPE_TORRENT
        else:
            m_ac.HEN_DOWNLOAD_TYPE = m_ac.DOWNLOAD_TYPE_OTHER
        from version.dl_manager_obj import DLManagerObject
        obj = DLManagerObject()
        if constant_dl_type == 'archive':
            assert obj.ARCHIVE
            assert not obj.TORRENT
        elif constant_dl_type == 'torrent':
            assert not obj.ARCHIVE
            assert obj.TORRENT
        else:
            assert not obj.ARCHIVE
            assert not obj.TORRENT


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

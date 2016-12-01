"""test module."""
from itertools import product
from unittest import mock

import pytest


@pytest.mark.parametrize('db, gallery_profile', product([True, False], repeat=2))
def test_add_single_gallery(db, gallery_profile):
    """test method."""
    s_gallery = mock.Mock()
    s_gallery.profile = gallery_profile
    method = mock.Mock()
    with mock.patch('version.manga_views.gallerydb') as m_gdb, \
            mock.patch('version.manga_views.Executors') as m_exec:
        from version.manga_views import MangaViews
        MangaViews._add_single_gallery(db=db, s_gallery=s_gallery, on_method=method)
        if db:
            m_gdb.execute.assert_called_once_with(
                m_gdb.GalleryDB.add_gallery, True, s_gallery)
        elif not gallery_profile:
            m_exec.generate_thumbnail.assert_called_once_with(s_gallery, on_method=method)
        else:
            assert not m_gdb.mock_calls
            assert not m_exec.generate_thumbnail.mock_calls

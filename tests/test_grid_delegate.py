"""test module."""
from unittest import mock

import pytest


@pytest.mark.parametrize(
    'artist_len, exp_size',
    [(0, 2), (20, 2), (25, 2), (30, 1), (35, 1), (40, 0), (50, 0)]
)
def test_get_adjusted_font_size_for_artist_size(artist_len, exp_size):
    """test func."""
    font_size = 2
    obj = [mock.Mock()] * artist_len
    limit_list = [21, 30, 40]
    from version.grid_delegate import _get_adjusted_font_size
    res = _get_adjusted_font_size(obj=obj, font_size=font_size, limit_list=limit_list)
    assert res == exp_size


@pytest.mark.parametrize(
    'artist_len, exp_size',
    [
        (0, 4), (15, 4), (16, 4), (17, 4), (20, 4),
        (21, 3), (25, 3),
        (30, 2), (35, 2),
        (40, 1), (45, 1),
        (50, 0), (60, 0),
    ]
)
def test_get_adjusted_font_size_for_title_size(artist_len, exp_size):
    """test func."""
    font_size = 4
    obj = [mock.Mock()] * artist_len
    limit_list = [16, 21, 30, 40, 50]
    from version.grid_delegate import _get_adjusted_font_size
    res = _get_adjusted_font_size(obj=obj, font_size=font_size, limit_list=limit_list)
    assert res == exp_size


@pytest.mark.parametrize('use_external_viewer', [True, False])
def test_set_external_icon(use_external_viewer):
    """test method."""
    file_icons = mock.Mock()
    with mock.patch('version.grid_delegate.app_constants') as m_ac:
        m_ac.USE_EXTERNAL_VIEWER = use_external_viewer
        from version.grid_delegate import GridDelegate
        GridDelegate._set_external_icon(file_icons=file_icons)
        if use_external_viewer:
            file_icons.get_external_file_icon.assert_called_once_with()
            assert GridDelegate.external_icon == file_icons.get_external_file_icon.return_value
        else:
            file_icons.get_default_file_icon.assert_called_once_with()
            assert GridDelegate.external_icon == file_icons.get_default_file_icon.return_value


def test_get_type_rect():
    type_p = mock.Mock()
    type_p.x.return_value = 0
    type_p.y.return_value = 0
    #
    type_w = 0
    type_h = 0
    with mock.patch('version.grid_delegate.QRect') as m_qr:
        from version.grid_delegate import GridDelegate
        res = GridDelegate._get_type_rect(type_p=type_p, type_w=type_w, type_h=type_h)
        assert res == m_qr.return_value
        m_qr.assert_called_once_with(-2, -1, 4, 1)

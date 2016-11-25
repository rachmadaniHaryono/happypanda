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

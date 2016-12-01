"""test module."""
from unittest import mock
from itertools import product

import pytest


@pytest.mark.parametrize('cond, is_idx_end', product([True, False], repeat=2))
def test_check_single_gallery(cond, is_idx_end):
    """test method."""
    gallery = mock.Mock()
    fetch_metadata_func = mock.Mock()
    hen_item = mock.Mock()
    #
    checked_pre_url_galleries = []
    #
    from version.fetch_obj import FetchObject
    FetchObject.fetch_metadata = fetch_metadata_func
    # run
    res = FetchObject._check_single_gallery(
        cond=cond, gallery=gallery, hen_item=hen_item, is_idx_end=is_idx_end,
        checked_pre_url_galleries=checked_pre_url_galleries
    )
    # test
    if cond and is_idx_end:
        fetch_metadata_func.assert_called_once_with(hen=hen_item)
    else:
        fetch_metadata_func.assert_not_called()
    if cond:
        assert res[2].temp_url == gallery._g_dialog_url
        assert res[0]
    else:
        assert res[2].temp_url != gallery._g_dialog_url
        assert not res[0]

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
    gallery_temp_url = mock.Mock()
    #
    checked_pre_url_galleries = []
    #
    from version.fetch_obj import FetchObject
    FetchObject.fetch_metadata = fetch_metadata_func
    # run
    obj = FetchObject()
    res = obj._check_single_gallery(
        cond=cond, gallery=gallery, hen_item=hen_item, is_idx_end=is_idx_end,
        checked_pre_url_galleries=checked_pre_url_galleries,
        gallery_temp_url=gallery_temp_url
    )
    # test
    if cond and is_idx_end:
        fetch_metadata_func.assert_called_once_with(hen=hen_item)
    else:
        fetch_metadata_func.assert_not_called()
    if cond:
        assert res[2].temp_url == gallery_temp_url
        assert res[0]
    else:
        assert res[2].temp_url != gallery._g_dialog_url
        assert not res[0]


@pytest.mark.parametrize('raise_type_error', [False, True])
def test_get_gallery_list_and_status(raise_type_error):
    """test func."""
    series_path = mock.Mock()
    #
    name = mock.Mock()
    path = mock.Mock()
    path.name = name
    #
    with mock.patch('version.fetch_obj.scandir') as m_sd:
        if raise_type_error:
            m_sd.scandir.side_effect = TypeError
        else:
            m_sd.scandir.return_value = [path]
        from version.fetch_obj import FetchObject
        res = FetchObject._get_gallery_list_and_status(series_path=series_path)
        if raise_type_error:
            assert res[0] == series_path
            assert res[1]
        else:
            assert res[0] == [name]
            assert not res[1]


@pytest.mark.parametrize('skipped_paths', [[], [mock.Mock()]])
def test_after_local_search(skipped_paths):
    """test method."""
    finish_signal = mock.Mock()
    skipped_signal = mock.Mock()
    data = mock.Mock()
    from version.fetch_obj import FetchObject
    obj = FetchObject()
    obj.FINISHED = finish_signal
    obj.SKIPPED = skipped_signal
    obj.skipped_paths = skipped_paths
    obj.data = [data]
    # run
    obj._after_local_search()
    finish_signal.emit.assert_called_once_with([data])
    if skipped_paths:
        skipped_signal.emit.assert_called_once_with(skipped_paths)
    else:
        assert not skipped_signal.mock_calls

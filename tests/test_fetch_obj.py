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


@pytest.mark.parametrize(
    'path_is_dir, scandir_return_list, path_ext',
    product(
        [True, False],
        [True, False],
        [None, '.zip', '.cbz']
    )
)
def test_create_gallery_from_path_as_chapter(path_is_dir, scandir_return_list, path_ext):
    """test method."""
    create_gallery_func = mock.Mock()
    path = 'random_path'
    if path_ext is not None:
        path += path_ext
    folder_name = mock.Mock()
    with mock.patch('version.fetch_obj.os') as m_os, \
            mock.patch('version.fetch_obj.scandir') as m_scandir, \
            mock.patch('version.fetch_obj.app_constants') as m_app_constants:
        m_app_constants.ARCHIVE_FILES = ('.zip', '.cbz')
        m_os.path.isdir.return_value = path_is_dir
        if scandir_return_list:
            m_scandir.scandir.return_value = [mock.Mock()]
        else:
            m_scandir.scandir.return_value = []
        from version.fetch_obj import FetchObject
        obj = FetchObject()
        obj.create_gallery = create_gallery_func
        # run
        obj._create_gallery_from_path_as_chapter(path=path, folder_name=folder_name)
        # test
        if path_is_dir and scandir_return_list and \
                path.endswith(m_app_constants.ARCHIVE_FILES):
            create_gallery_func.assert_called_once_with(path, folder_name, do_chapters=True)


@pytest.mark.parametrize('path_type', ['folder', 'archive'])
def test_create_gallery_from_path_with_subfolder_as_gallery(path_type):
    """test method."""
    create_gallery_func = mock.Mock()
    arg_folder_name = mock.Mock()
    # utils module result when path type is folder
    g_folder = mock.Mock()
    g_dirpath_path = mock.Mock()
    g_dirpath_archive = mock.Mock()
    # utils module result when path type is archive
    g_archive = mock.Mock()

    if path_type == 'folder':
        path = mock.Mock()
    elif path_type == 'archive':
        path = 'path_archive.zip'
    with mock.patch('version.fetch_obj.os') as m_os, \
            mock.patch('version.fetch_obj.app_constants') as m_app_constants, \
            mock.patch('version.fetch_obj.utils') as m_utils:
        m_app_constants.ARCHIVE_FILES = ('.zip', '.cbz')
        m_utils.recursive_gallery_check.return_value = (
            [g_folder], [(g_dirpath_path, g_dirpath_archive)])
        m_utils.check_archive.return_value = [g_archive]
        m_os.path.isdir.return_value = True if path_type == 'folder' else False
        m_os.path.split.return_value = [None, arg_folder_name]
        from version.fetch_obj import FetchObject
        obj = FetchObject()
        obj.create_gallery = create_gallery_func
        # run
        obj._create_gallery_from_path_with_subfolder_as_gallery(path=path)
        # test
        if path_type == 'folder':
            m_os.assert_has_calls([
                mock.call.path.isdir(path),
                mock.call.path.split(g_folder),
                mock.call.path.split(g_dirpath_path)
            ])
            create_gallery_func.assert_has_calls([
                mock.call(g_folder, arg_folder_name, False),
                mock.call(g_dirpath_path, arg_folder_name, False, archive=g_dirpath_archive)
            ])
        elif path_type == 'archive':
            m_os.assert_has_calls([
                mock.call.path.isdir(path),
                mock.call.path.split(g_archive)
            ])
            create_gallery_func.assert_called_once_with(
                g_archive, arg_folder_name, False, archive=path
            )

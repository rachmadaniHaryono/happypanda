"""test module."""
from unittest import mock
from itertools import product

import pytest


@pytest.mark.parametrize(
    'use_mock_as_input, is_src_path_in_path_ignore, is_event_directory, '
    'is_ext_in_utils_archive_files, is_folder_in_ignore_exts, is_ext_in_ignore_exts',
    product([True, False], repeat=6)
)
def test_file_filter(
        use_mock_as_input, is_src_path_in_path_ignore, is_event_directory,
        is_ext_in_utils_archive_files, is_folder_in_ignore_exts, is_ext_in_ignore_exts
):
    """test method."""
    m_input = mock.Mock()
    src_path_ext = 'some_ext'
    m_input.src_path = 'src_path.{}'.format(src_path_ext)
    m_input.is_directory = is_event_directory
    default_path_ignore = ['default_path_ignore']
    # mock
    temp_path_ignore = default_path_ignore
    utils_archive_files = []
    ignore_exts = []
    if is_src_path_in_path_ignore:
        temp_path_ignore.append(m_input.src_path)
    if is_ext_in_utils_archive_files:
        utils_archive_files.append(src_path_ext)
    if is_folder_in_ignore_exts:
        ignore_exts.append("Folder")
    if is_ext_in_ignore_exts:
        ignore_exts.append(src_path_ext.upper())
    with mock.patch('happypanda.gallery_handler.app_constants') as m_ac, \
            mock.patch('happypanda.gallery_handler.utils') as m_utils:
        # pre run
        m_ac.TEMP_PATH_IGNORE = temp_path_ignore
        m_ac.IGNORE_EXTS = ignore_exts
        m_utils.ARCHIVE_FILES = utils_archive_files
        # run
        from happypanda.gallery_handler import GalleryHandler
        obj = GalleryHandler()
        if use_mock_as_input:
            with pytest.raises(TypeError):
                obj.file_filter(mock.Mock())
            return
        else:
            res = obj.file_filter(m_input)
        # test
        if is_src_path_in_path_ignore:
            assert not res
            assert m_ac.TEMP_PATH_IGNORE == default_path_ignore
            return
        #
        assert m_ac.TEMP_PATH_IGNORE == temp_path_ignore
        if is_event_directory and (is_ext_in_ignore_exts != is_folder_in_ignore_exts):
            assert not res
        elif not(is_folder_in_ignore_exts and is_ext_in_ignore_exts) and is_event_directory:
            assert res
        else:
            assert not res
        # NOTE: there may be better logic condition to check if result True or False


@pytest.mark.parametrize(
    'override_monitor, file_filter_result, is_event_directory, is_zip_file, '
    'check_archive_result, g_dirs_found, g_archs_found',
    product(
        [True, False],
        repeat=7
    )
)
def test_on_created(
        override_monitor, file_filter_result, is_event_directory, is_zip_file,
        check_archive_result, g_dirs_found, g_archs_found):
    """test method."""
    m_input = mock.Mock()
    src_path_ext = 'zip' if is_zip_file else 'some_ext'
    m_input.src_path = 'src_path.{}'.format(src_path_ext)
    m_input.is_directory = is_event_directory
    # mock gallery dirs
    m_g_dirs = [mock.Mock()] if g_dirs_found else []
    # mock gallery archives
    m_g_archs = [mock.Mock()] if g_archs_found else []
    recursive_gallery_check_result = m_g_dirs, m_g_archs
    # run
    with mock.patch('happypanda.gallery_handler.app_constants') as m_ac, \
            mock.patch('happypanda.gallery_handler.utils') as m_utils:
        from happypanda.gallery_handler import GalleryHandler
        from happypanda.utils import ARCHIVE_FILES
        m_ac.OVERRIDE_MONITOR = override_monitor
        #
        m_utils.ARCHIVE_FILES = ARCHIVE_FILES
        m_utils.check_archive.return_value = [mock.Mock()] if check_archive_result else []
        m_utils.recursive_gallery_check.return_value = recursive_gallery_check_result
        #
        obj = GalleryHandler()
        obj.CREATE_SIGNAL = mock.Mock()
        obj.file_filter = mock.Mock(return_value=file_filter_result)
        # run
        obj.on_created(m_input)
        # test
        assert not m_ac.OVERRIDE_MONITOR
        if override_monitor:
            obj.file_filter.assert_not_called()
            obj.CREATE_SIGNAL.emit.assert_not_called()
        elif not override_monitor and file_filter_result:
            obj.file_filter.assert_called_once_with(m_input)
            if is_zip_file:
                if check_archive_result:
                    obj.CREATE_SIGNAL.emit.assert_called_once_with(m_input.src_path)
                else:
                    obj.CREATE_SIGNAL.emit.assert_not_called()
            elif is_event_directory and (g_dirs_found or g_archs_found):
                obj.CREATE_SIGNAL.emit.assert_called_once_with(m_input.src_path)
            else:
                obj.CREATE_SIGNAL.emit.assert_not_called()
        else:
            obj.file_filter.assert_called_once_with(m_input)
            obj.CREATE_SIGNAL.emit.assert_not_called()


@pytest.mark.parametrize(
    'filetype',
    product(
        ['zip', 'cbz', 'rar', 'cbr', 'random_ext'],
        [True, False]
    )
)
def test_on_created_with_different_filetype(filetype):
    """test method."""
    unrar_tool_path = True
    filetype = 'zip'
    if filetype in ('zip', 'cbz'):
        is_signal_emitted = True
    elif filetype in ('rar', 'cbr') and unrar_tool_path:
        is_signal_emitted = True
    else:
        is_signal_emitted = False
    m_input = mock.Mock()
    m_input.src_path = 'src_path.{}'.format(filetype)
    m_input.is_directory = False
    with mock.patch('happypanda.gallery_handler.app_constants') as m_ac, \
            mock.patch('happypanda.gallery_handler.utils') as m_utils:
        from happypanda import app_constants
        app_constants.unrar_tool_path = unrar_tool_path
        from happypanda.utils import ARCHIVE_FILES
        from happypanda.gallery_handler import GalleryHandler
        m_ac.OVERRIDE_MONITOR = False
        #
        m_utils.ARCHIVE_FILES = ARCHIVE_FILES
        m_utils.check_archive.return_value = [mock.Mock()]
        #
        obj = GalleryHandler()
        obj.CREATE_SIGNAL = mock.Mock()
        obj.file_filter = mock.Mock(return_value=True)
        # run
        obj.on_created(m_input)
        # test
        if is_signal_emitted:
            obj.CREATE_SIGNAL.emit.assert_called_once_with(m_input.src_path)
        else:
            obj.CREATE_SIGNAL.emit.assert_not_called()


@pytest.mark.parametrize(
    'get_gallery_result, signal_pack',
    product(
        [True, False],
        [('DELETED_SIGNAL', 'on_deleted'), ('MOVED_SIGNAL', 'on_moved')],
    )
)
def test_on_deleted_and_on_moved(get_gallery_result, signal_pack):
    """test method."""
    signal_name, signal_func_name = signal_pack
    m_input = mock.Mock()
    if signal_func_name == 'on_deleted':
        emit_first_arg = m_input.src_path
    elif signal_func_name == 'on_moved':
        emit_first_arg = m_input.dest_path
    else:
        raise ValueError('Unknown signal func name.')
    with mock.patch('happypanda.gallery_handler.GalleryDB') as m_gallery_db:
        from happypanda.gallery_handler import GalleryHandler
        obj = GalleryHandler()
        obj._is_condition_match = mock.Mock(return_value=True)
        setattr(obj, signal_name, mock.Mock())
        m_gallery_db.get_gallery_by_path.return_value = mock.Mock if get_gallery_result else None
        # run
        getattr(obj, signal_func_name)(m_input)
        # test
        if get_gallery_result:
            getattr(obj, signal_name).emit.assert_called_once_with(
                emit_first_arg, m_gallery_db.get_gallery_by_path.return_value)
        else:
            getattr(obj, signal_name).emit.assert_not_called()


@pytest.mark.parametrize(
    'override_monitor, file_filter_result',
    product([True, False], repeat=2)
)
def test_is_condition_match(override_monitor, file_filter_result):
    """test method."""
    exp_res = True if not override_monitor and file_filter_result else False
    m_input = mock.Mock()
    with mock.patch('happypanda.gallery_handler.app_constants') as m_ac:
        m_ac.OVERRIDE_MONITOR = override_monitor
        #
        from happypanda.gallery_handler import GalleryHandler
        obj = GalleryHandler()
        obj.file_filter = mock.Mock(return_value=file_filter_result)
        # run
        res = obj._is_condition_match(m_input)
        # test
        assert res == exp_res
        assert not m_ac.OVERRIDE_MONITOR
        if not override_monitor:
            obj.file_filter.assert_called_once_with(m_input)
        else:
            obj.file_filter.assert_not_called()

"""test module."""
from unittest import mock
from itertools import product

import pytest


@pytest.mark.parametrize(
    'item, session, dir_',
    product(
        ['www.example.com', mock.Mock()],
        [None, mock.Mock()],
        [None, mock.Mock()]
    )
)
def test_add_to_queue(item, session, dir_):
    """test method."""
    from version.downloader_obj import DownloaderObject, DownloaderItemObject
    # ru
    res = DownloaderObject.add_to_queue(item=item, session=session, dir=dir_)
    # test
    if isinstance(item, str):
        assert isinstance(res, DownloaderItemObject)
    if dir_:
        assert DownloaderObject._inc_queue.get() == {'dir': dir_, 'item': res}
    else:
        assert DownloaderObject._inc_queue.get() == res
    assert DownloaderObject._session == session


@pytest.mark.parametrize('path_exists_retval', [True, False])
def test_init(path_exists_retval):
    """test init."""
    base_path = mock.Mock()
    with mock.patch('version.downloader_obj.os') as m_os, \
            mock.patch('version.downloader_obj.app_constants') as m_ac:
        m_os.path.exists.return_value = path_exists_retval
        m_os.path.abspath.return_value = base_path
        from version.downloader_obj import DownloaderObject
        # run
        res = DownloaderObject()
        # test
        os_calls = [
            mock.call.path.abspath(m_ac.DOWNLOAD_DIRECTORY),
            mock.call.path.exists(base_path)
        ]
        if not path_exists_retval:
            os_calls.append(mock.call.mkdir(base_path))
        m_os.assert_has_calls(os_calls)
        assert res.base == m_os.path.abspath.return_value


@pytest.mark.parametrize('raise_os_error', [True, False])
def test_remove_file(raise_os_error):
    """test method."""
    filename = mock.Mock()
    with mock.patch('version.downloader_obj.os') as m_os:
        if raise_os_error:
            m_os.remove.side_effect = OSError
        from version.downloader_obj import DownloaderObject
        # run
        DownloaderObject.remove_file(filename=filename)
        # test
        m_os.remove.assert_called_once_with(filename)


@pytest.mark.parametrize(
    'headers, exp_res',
    [
        ({}, 0),
        ({'content-length': '10'}, 10),
        ({'content-length': 10}, 10),
    ]
)
def test_get_total_size(headers, exp_res):
    """test method."""
    response = mock.Mock()
    response.headers = headers
    from version.downloader_obj import DownloaderObject
    res = DownloaderObject._get_total_size(response=response)
    assert res == exp_res


@pytest.mark.parametrize('browser_session', [True, False])
def test_get_response(browser_session):
    bs = mock.Mock()
    url = mock.Mock()
    with mock.patch('version.downloader_obj.DownloaderObject.__init__', return_value=None), \
            mock.patch('version.downloader_obj.requests') as m_r:
        from version.downloader_obj import DownloaderObject
        obj = DownloaderObject()
        if browser_session:
            obj._browser_session = bs
        # run
        res = obj._get_response(url=url)
        # test
        if browser_session:
            bs.get.assert_called_once_with(url, stream=True)
            assert res == bs.get.return_value
        else:
            m_r.get.assert_called_once_with(url, stream=True)
            assert res == m_r.get.return_value


@pytest.mark.parametrize(
    'queue_item, exp_item, exp_temp_base',
    [
        ('mock', 'mock', None),
        ('dict', 'mock', 'mock'),
    ]
)
def test_get_item_and_temp_base(queue_item, exp_item, exp_temp_base):
    """test method"""
    if queue_item == 'mock' and exp_item == 'mock':
        queue_item = mock.Mock()
        exp_item = queue_item
        exp_temp_base = None
    elif queue_item == 'dict' and exp_item == 'mock' and exp_temp_base == 'mock':
        exp_item = mock.Mock()
        exp_temp_base = mock.Mock()
        queue_item = {'dir': exp_temp_base, 'item': exp_item}
    else:
        raise ValueError('Input Error')
    with mock.patch('version.downloader_obj.DownloaderObject.__init__', return_value=None):
        from version.downloader_obj import DownloaderObject
        obj = DownloaderObject()
        obj._inc_queue.put(queue_item)
        # run
        item, temp_base = obj._get_item_and_temp_base()
        # test
        assert item == exp_item
        assert temp_base == exp_temp_base


@pytest.mark.parametrize(
    'item_name_and_exp_basename, temp_base',
    product(
        [
            ('filename', 'filename'),
            ('\\/:*?"<>|', ''),
            (None, None)
        ],
        [None, mock.Mock()]
    )
)
def test_get_filename(item_name_and_exp_basename, temp_base):
    """test method."""
    uuid4_retval = 'd481adf4-90fa-4005-88de-ade1301c0fa5'
    item = mock.Mock()
    item.name, exp_basename = item_name_and_exp_basename
    if not item.name:
        exp_basename = uuid4_retval
    obj_base = mock.Mock()
    if temp_base:
        exp_dirname = temp_base
    else:
        exp_dirname = obj_base
    with mock.patch('version.downloader_obj.os') as m_os, \
            mock.patch('version.downloader_obj.uuid') as m_uuid, \
            mock.patch('version.downloader_obj.DownloaderObject.__init__', return_value=None):
        m_uuid.uuid4.return_value = uuid4_retval
        from version.downloader_obj import DownloaderObject
        obj = DownloaderObject()
        obj.base = obj_base
        # run
        res = obj._get_filename(item=item, temp_base=temp_base)
        # test
        m_os.path.join.assert_called_once_with(exp_dirname, exp_basename)
        assert res == m_os.path.join.return_value


@pytest.mark.parametrize('current_state_is_cancelled', [True, False])
def test_download_single_file(current_state_is_cancelled):
    item = mock.Mock()
    item.current_state = 0
    if current_state_is_cancelled:
        item.CANCELLED = item.current_state
    else:
        item.CANCELLED = 1
    item.current_size = 0

    subdata = mock.Mock()
    response = mock.Mock()
    response.iter_content.return_value = [[subdata]]

    target_file = mock.Mock()
    interrupt_state = False
    m_open = mock.mock_open()
    with mock.patch('version.downloader_obj.open', m_open, create=True):
        from version.downloader_obj import DownloaderObject
        result_item, result_interrupt_state = DownloaderObject._download_single_file(
            target_file=target_file, response=response, item=item, interrupt_state=interrupt_state)
        if current_state_is_cancelled:
            assert result_interrupt_state
            m_open.assert_has_calls([
                mock.call(target_file, 'wb'),
                mock.call().__enter__(),
                mock.call().__exit__(None, None, None)
            ])
        else:
            assert result_interrupt_state == interrupt_state
            assert result_item.current_size == 1
            m_open.assert_has_calls([
                mock.call(target_file, 'wb'),
                mock.call().__enter__(),
                mock.call().write([subdata]),
                mock.call().flush(),
                mock.call().__exit__(None, None, None)
            ])


@pytest.mark.parametrize(
    'max_loop_reached, filename_is_splittable, raise_error_once',
    product([True, False], repeat=3)
)
def test_rename_file(max_loop_reached, filename_is_splittable, raise_error_once):
    """test method."""
    filename = mock.Mock()
    filename_part = mock.Mock()
    #
    file_split0 = mock.Mock()
    file_split1 = mock.Mock()
    if filename_is_splittable:
        file_split = [file_split0, file_split1]
        # rename src and target filename
        target_filename = file_split1
        src_filename = file_split0
    else:
        file_split = [file_split0, '']
        # rename src and target filename
        target_filename = filename
        src_filename = filename_part
    with mock.patch('version.downloader_obj.os') as m_os:
        from version.downloader_obj import DownloaderObject
        if raise_error_once:
            m_os.rename.side_effect = [OSError, None]
        m_os.path.split.return_value = file_split
        # run
        if max_loop_reached:
            res = DownloaderObject._rename_file(
                filename=filename, filename_part=filename_part, max_loop=-1)
        else:
            res = DownloaderObject._rename_file(filename=filename, filename_part=filename_part)
        # test
        if not max_loop_reached:
            assert res == filename
        if max_loop_reached:
            assert res == filename_part
        elif raise_error_once:
            m_os.rename.assert_has_calls([
                mock.call(src_filename, '(0){}'.format(target_filename)),
                mock.call(src_filename, '(1){}'.format(target_filename)),
            ])
        else:
            m_os.rename.assert_called_once_with(src_filename, '(0){}'.format(target_filename))

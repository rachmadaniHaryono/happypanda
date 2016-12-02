"""test module."""
from unittest import mock

import pytest


@pytest.mark.parametrize('exp_res', ['darwin', 'windows', 'linux'])
def test_get_os_name(exp_res):
    """test func."""
    with mock.patch('version.app_constants.sys') as m_sys, \
            mock.patch('version.app_constants.os') as m_os:
        m_sys.platform = 'darwin' if exp_res == 'darwin' else 'linux'
        m_os.name = 'posix' if exp_res == 'linux' else 'nt'
        from version.app_constants import _get_os_name
        assert exp_res == _get_os_name()


@pytest.mark.parametrize('os_name', ['posix', 'nt'])
def test_get_dirs(os_name):
    """test func."""
    with mock.patch('version.app_constants.os') as m_os, \
            mock.patch('version.app_constants.__file__') as m_file:
        m_os.name = os_name
        from version.app_constants import _get_dirs
        assert (
            m_os.path.dirname.return_value,
            m_os.path.join.return_value, m_os.path.join.return_value, m_os.path.join.return_value
        ) == _get_dirs()
        if os_name != 'posix':
            m_os.getcwd.assert_called_once_with()
            m_os.path.assert_has_calls([
                mock.call.realpath(m_file),
                mock.call.dirname(m_os.path.realpath.return_value),
                mock.call.join(m_os.getcwd.return_value, 'bin'),
                mock.call.join(m_os.getcwd.return_value, 'res'),
                mock.call.join('temp'),
            ])
        else:
            m_os.path.assert_has_calls([
                mock.call.realpath(m_file),
                mock.call.dirname(m_os.path.realpath.return_value),
                mock.call.join(m_os.path.dirname.return_value, 'bin'),
                mock.call.join(m_os.path.dirname.return_value, '../res'),
                mock.call.join(m_os.path.dirname.return_value, 'temp')
            ])


@pytest.mark.parametrize(
    'unrar_tool, exp_res',
    [
        [True, (('.zip', '.cbz', '.rar', '.cbr'), '*.zip *.cbz *.rar *.cbr')],
        [False, (('.zip', '.cbz'), '*.zip *.cbz')]
    ]
)
def test_get_archive_files_and_file_filter(unrar_tool, exp_res):
    """test get archive_file and file filter."""
    from version.app_constants import _get_archive_files_and_file_filter
    res = _get_archive_files_and_file_filter(unrar_tool=unrar_tool)
    assert res == exp_res

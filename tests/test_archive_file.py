"""test module."""
from unittest import mock

import pytest


@pytest.mark.parametrize('path', [None, mock.Mock()])
def test_make_temp_dir(path):
    """test method."""
    with mock.patch('version.archive_file.os') as m_os, \
            mock.patch('version.archive_file.app_constants') as m_ac, \
            mock.patch('version.archive_file.uuid') as m_uuid:
        from version.archive_file import ArchiveFile
        res = ArchiveFile._make_temp_dir(path=path)
        if not path:
            m_os.assert_has_calls([
                mock.call.path.join(m_ac.temp_dir, str(m_uuid.uuid4.return_value)),
                mock.call.mkdir(m_os.path.join())
            ])
            assert res == m_os.path.join.return_value
            m_uuid.uuid4.assert_called_once_with()
        else:
            assert res == path
            assert not m_os.mock_calls
            assert not m_uuid.mock_calls

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


@pytest.mark.parametrize(
    'ext',
    ['.zip', '.cbz', '.cbr', '.rar', '.random']
)
def test_check_archive(ext):
    """test method."""
    filepath = 'filename{}'.format(ext)
    with mock.patch('version.archive_file.os') as m_os, \
            mock.patch('version.archive_file.rarfile') as m_rf, \
            mock.patch('version.archive_file.zipfile') as m_zf:
        from version import archive_file
        archive_file.ARCHIVE_FILES = ('.zip', '.cbz', '.rar', '.cbr')
        # run
        res = archive_file.ArchiveFile._check_archive(filepath=filepath)
        # test
        if filepath.endswith(archive_file.ARCHIVE_FILES):
            m_os.path.normcase.assert_called_once_with(filepath)
        else:
            m_os.path.normcase.assert_not_called()
            assert res
        if ext in ('.zip', '.cbz'):
            m_zf.assert_has_calls([
                mock.call.ZipFile(m_os.path.normcase.return_value),
                mock.call.ZipFile().testzip()
            ])
            assert res == m_zf.ZipFile.return_value.testzip.return_value
        elif ext in ('.rar', '.cbr'):
            m_rf.assert_has_calls([
                mock.call.RarFile(m_os.path.normcase.return_value),
                mock.call.RarFile().testrar()
            ])
            assert res == m_rf.RarFile.return_value.testrar.return_value

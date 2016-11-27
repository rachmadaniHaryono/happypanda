"""test module."""
from unittest import mock

import pytest

from version.utils import IMG_FILES


@pytest.mark.parametrize(
    'ext',
    list(IMG_FILES) + [x.upper() for x in IMG_FILES] + [x.title() for x in IMG_FILES]
)
def test_find_filepath(ext):
    """test func."""
    path = mock.Mock()
    filename = 'file1.{}'.format(ext)
    scandir_res = mock.Mock()
    scandir_res.name = filename
    scandir_result = [scandir_res]
    with mock.patch('version.utils.scandir') as m_scandir, \
            mock.patch('version.utils.os') as m_os:
        m_scandir.scandir.return_value = scandir_result
        from version.utils import _find_filepath
        # run
        res = _find_filepath(path)
        # test
        m_scandir.scandir.assert_called_once_with(path)
        m_os.path.join.assert_called_once_with(path, filename)
        assert res == m_os.path.join.return_value

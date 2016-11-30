"""test module."""
from unittest import mock


def test_get_qdatetime_from_string():
    """test func."""
    value = mock.Mock()
    with mock.patch('version.gallery_model.QDateTime') as m_qdt:
        from version.gallery_model import GalleryModel
        # run
        res = GalleryModel._get_qdatetime_from_string(value=value)
        # test
        m_qdt.fromString.assert_called_once_with('{}'.format(value), 'yyyy-MM-dd HH:mm:ss')
        assert res == m_qdt.fromString.return_value

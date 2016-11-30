"""test module."""
from unittest import mock


def test_open_idx_data_first_chapter_when_double_clicked():
    """test fun."""
    idx = mock.Mock()
    chapter = mock.Mock()
    idx.data.return_value.chapters = [chapter]
    with mock.patch('version.misc.Qt') as m_qt:
        from version.misc import open_idx_data_first_chapter_when_double_clicked
        open_idx_data_first_chapter_when_double_clicked(idx)
        idx.data.assert_called_once_with(m_qt.UserRole + 1)
        chapter.open.assert_called_once_with()

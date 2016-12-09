"""test module."""
from unittest import mock

import pytest


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


@pytest.mark.parametrize('use_parent', [True, False])
def test_show_widget(use_parent):
    """test func."""
    widget_obj = mock.Mock()
    with mock.patch('version.misc.QtWidgets') as m_qw, \
            mock.patch('version.misc.sys') as m_sys:
        from version.misc import show_widget
        if not use_parent:
            with pytest.raises(NotImplementedError):
                show_widget(widget_obj=widget_obj, use_parent=use_parent)
            return
        show_widget(widget_obj=widget_obj, use_parent=use_parent)
        m_qw.assert_has_calls([
            mock.call.QApplication(m_sys.argv),
            mock.call.QWidget(),
            mock.call.QApplication().exec_()
        ])
        m_sys.exit.assert_called_once_with(m_qw.QApplication.return_value.exec_.return_value)
        widget_obj.assert_has_calls([
            mock.call(parent=m_qw.QWidget.return_value),
            mock.call().show()
        ])

"""test module."""
from unittest import mock
from itertools import product

import pytest


version_0_31_0_only = pytest.mark.skipif(True, reason="For v.0.31.0 only.")


@version_0_31_0_only
@pytest.mark.parametrize('is_archive, selected', product([True, False], repeat=2))
def test_add_op_folder_actions(is_archive, selected):
    """test method."""
    op_folder_func = mock.Mock()
    add_action_func = mock.Mock()
    index = mock.Mock()
    index.data.return_value.is_archive = is_archive
    with mock.patch('version.gallery_menu.Qt') as m_qt:
        m_qt.UserRole = 0
        #
        from version.gallery_menu import GalleryMenu
        GalleryMenu.addAction = add_action_func
        GalleryMenu.index = index
        GalleryMenu.op_folder = op_folder_func
        GalleryMenu.selected = selected
        # run
        GalleryMenu._add_op_folder_actions()
        # test
        text = 'folder' if not is_archive else 'archive'
        show_in_folder_info = 'Show in folder'
        if selected:
            text += 's'
            show_in_folder_info += 's'
        add_action_func.assert_has_calls([
            mock.call('Open {}'.format(text), mock.ANY),
            mock.call(show_in_folder_info, mock.ANY),
        ])

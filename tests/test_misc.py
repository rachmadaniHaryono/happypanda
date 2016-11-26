"""test module."""
from unittest import mock
from itertools import product

import pytest


@pytest.mark.parametrize(
    'event_key, selected_idx',
    product(
        ['return_key', 'shift-delete', 'delete'],
        [
            [],
            [mock.Mock()],
            [mock.Mock(), mock.Mock()],
            [mock.Mock(), mock.Mock(), mock.Mock()],
        ]
    )
)
def test_handle_keypress_event_on_manga_view(event_key, selected_idx):
    """test func."""
    view_obj = mock.Mock()
    key = mock.Mock()
    with mock.patch('version.misc.CommonView') as m_cw:
        from version.misc import handle_keypress_event_on_manga_view
        from version.misc import Qt
        event = mock.Mock()
        if event_key == 'return_key':
            event.key.return_value = Qt.Key_Return
        elif event_key == 'shift-delete':
            event.key.return_value = Qt.Key_Delete
            event.modifiers.return_value = Qt.ShiftModifier
        elif event_key == 'delete':
            event.key.return_value = Qt.Key_Delete
        else:
            event.key.return_value = key
        # run
        handle_keypress_event_on_manga_view(view_obj, event, selected_idx)
        # test
        if event_key == 'return_key':
            if len(selected_idx) == 1:
                view_obj.doubleClicked.emit.assert_called_once_with(selected_idx[0])
            elif len(selected_idx) > 1:
                emit_calls = []
                for idx in selected_idx:
                    emit_calls.append(mock.call(idx))
                view_obj.doubleClicked.emit.assert_has_calls(emit_calls)
            else:
                view_obj.doubleClicked.emit.assert_not_called()
        elif event_key == 'shift-delete':
            m_cw.remove_selected.assert_called_once_with(view_obj, source=True)
        elif event_key == 'delete':
            m_cw.remove_selected.assert_called_once_with(view_obj, source=False)

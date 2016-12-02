"""test module."""
from unittest import mock


def test_change_view():
    """test method."""
    cview = mock.Mock()
    emit_value = mock.Mock()
    #
    refresh_func = mock.Mock()
    change_fav_func = mock.Mock()
    #
    from version.sort_filter_model import SortFilterModel
    SortFilterModel.refresh = refresh_func
    SortFilterModel._CHANGE_FAV = change_fav_func
    # run
    obj = SortFilterModel(parent=None)
    obj._change_view(emit_value=emit_value, current_view=cview)
    # test
    change_fav_func.emit.assert_called_once_with(emit_value)
    refresh_func.assert_called_once_with()
    assert obj.current_view == cview

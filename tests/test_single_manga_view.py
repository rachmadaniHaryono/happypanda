"""test module."""
from unittest import mock

import pytest


@pytest.mark.parametrize("name_is_as_expected", [True, False])
def test_set_sor(name_is_as_expected):
    """test func."""
    set_sort_role_func = mock.Mock()
    sort_func = mock.Mock()
    #
    name = 'name'
    if name_is_as_expected:
        exp_name = name
    else:
        exp_name = 'exp_name'
    #
    role = mock.Mock()
    sort_arg = mock.Mock()
    #
    from version.single_manga_view import SingleMangaView
    SingleMangaView.current_sort = None
    SingleMangaView.sort_model = mock.Mock()
    SingleMangaView.sort_model.setSortRole = set_sort_role_func
    SingleMangaView.sort_model.sort = sort_func
    # run
    res = SingleMangaView._set_sort(name=name, exp_name=exp_name, role=role, sort_arg=sort_arg)
    # test
    if name_is_as_expected:
        assert res
        set_sort_role_func.assert_called_once_with(role)
        sort_func.assert_called_once_with(0, sort_arg)
        assert SingleMangaView.current_sort == name
    else:
        assert not res
        set_sort_role_func.assert_not_called()
        sort_func.assert_not_called()
        assert SingleMangaView.current_sort != name

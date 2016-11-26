"""test module."""
from unittest import mock

import pytest


@pytest.mark.parametrize(
    'mode', ['correct_result', 'raise_type_error', 'raise_index_error']
)
def test_fetchone_from_cursor(mode):
    """test func."""
    cls = mock.Mock()
    key = mock.Mock()
    value = mock.Mock()
    if mode == 'correct_result':
        cls.execute.return_value.fetchone.return_value = {key: value}
    elif mode == 'raise_type_error':
        cls.execute.return_value.fetchone.side_effects = TypeError
    elif mode == 'raise_index_error':
        cls.execute.return_value.fetchone.side_effects = IndexError
    else:
        raise ValueError('Unknown mode.')
    #
    cmd = mock.Mock()
    exec_last_arg = mock.Mock()
    #
    from version.gallerydb import _fetchone_from_cursor
    # run
    res = _fetchone_from_cursor(cls, cmd, exec_last_arg, key)
    # test
    if mode == 'correct_result':
        assert res == value
    elif mode in ('raise_type_error', 'raise_index_error'):
        assert res is None
    cls.assert_has_calls([
        mock.call.execute(cls, cmd, exec_last_arg),
        mock.call.execute().fetchone()
    ])

"""test module."""
from itertools import product
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


@pytest.mark.parametrize(
    'is_value_none, is_cmd_value_arg_none, is_value_type_none, isinstance_result',
    product([True, False], repeat=4)
)
def test_get_db_cmd(is_value_none, is_cmd_value_arg_none, is_value_type_none, isinstance_result):
    """test method."""
    is_value_none = False
    is_cmd_value_arg_none = True
    is_value_type_none = True
    isinstance_result = True
    if is_value_none:
        value = None
    else:
        value = mock.Mock()
    if is_value_type_none:
        value_type = None
    else:
        value_type = mock.Mock()
    if is_cmd_value_arg_none:
        cmd_value_arg = None
        exp_cmd_value_arg = value
    else:
        exp_cmd_value_arg = cmd_value_arg = mock.Mock()
    series_id = mock.Mock()
    value_name = 'value_name'
    with mock.patch('version.gallerydb.isinstance', return_value=isinstance_result) as m_is_inst:
        from version.gallerydb import GalleryDB
        # run
        if not isinstance_result and not is_value_type_none:
            with pytest.raises(AssertionError):
                GalleryDB._get_db_cmd(
                    db_cmds=[], value=value, value_name=value_name, series_id=series_id,
                    value_type=value_type, cmd_value_arg=cmd_value_arg
                )
            return
        #
        res = GalleryDB._get_db_cmd(
            db_cmds=[], value=value, value_name=value_name, series_id=series_id,
            value_type=value_type, cmd_value_arg=cmd_value_arg
        )
        # Test
        if value_type is not None:
            m_is_inst.assert_called_once_with(value, value_type)
        else:
            m_is_inst.assert_not_called()
        if value is not None:
            assert res[0] == [
                'UPDATE series SET {}=? WHERE series_id=?'.format(value_name),
                (exp_cmd_value_arg, series_id)
            ]
        else:
            assert res == []


def test_get_db_cmd_with_encoded_value():
    """test method."""
    key = 'key'
    key_value = mock.Mock()
    value = 'value'
    kwargs = {key: key_value, 'value': value}
    exp_kwargs = kwargs
    exp_kwargs.update({'cmd_value_arg': str.encode(value)})
    #
    m_get_db_cmd = mock.Mock()
    from version.gallerydb import GalleryDB
    GalleryDB._get_db_cmd = m_get_db_cmd
    # run
    res = GalleryDB._get_db_cmd_with_encoded_value(**kwargs)
    # test
    m_get_db_cmd.assert_called_once_with(**exp_kwargs)
    assert res == m_get_db_cmd.return_value


@pytest.mark.parametrize('exist_result', [True, False])
def test_get_existing_gallery(exist_result):
    """test method."""
    func_name = 'func_name'
    galleries = mock.Mock()
    unchecked_gallery = mock.Mock()
    with mock.patch('version.gallerydb.os') as m_os:
        m_os.path.exists.return_value = exist_result
        from version.gallerydb import AdminDB
        # run
        res = AdminDB._get_existing_gallery(
            galleries=galleries, unchecked_gallery=unchecked_gallery, func_name=func_name)
        assert res == galleries
        if exist_result:
            getattr(galleries, func_name).assert_called_once_with(unchecked_gallery)
        else:
            getattr(galleries, func_name).assert_not_called()


def test_look_exists_when_add_tags():
    """test method."""
    tag_or_ns = mock.Mock()
    #
    arg = 'what_arg'
    value = mock.Mock()
    key = '{}_id'.format(arg)
    fetchone_result = {key: value}
    execute_func = mock.Mock()
    execute_func.return_value.fetchone.return_value = fetchone_result
    #
    from version.gallerydb import TagDB
    TagDB.execute = execute_func
    res = TagDB._look_exists_when_add_tags(tag_or_ns=tag_or_ns, what=arg)
    assert res == value
    execute_func.assert_has_calls([
        mock.call(
            TagDB, 'SELECT {} FROM {}s WHERE {} = ?'.format(key, arg, arg),
            (tag_or_ns,)
        ),
        mock.call().fetchone()]
    )

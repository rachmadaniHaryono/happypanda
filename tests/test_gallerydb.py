"""test module."""
from itertools import product
from unittest import mock

import pytest


version_0_31_0_only = pytest.mark.skipif(True, reason="For v.0.31.0 only.")


@version_0_31_0_only
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


@version_0_31_0_only
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


@version_0_31_0_only
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


@version_0_31_0_only
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


@version_0_31_0_only
@pytest.mark.parametrize(
    'raise_error, error_raised',
    product([True, False], [TypeError, IndexError])
)
def test_look_exists_when_add_tags(raise_error, error_raised):
    """test method."""
    tag_or_ns = mock.Mock()
    #
    arg = 'what_arg'
    value = mock.Mock()
    key = '{}_id'.format(arg)
    fetchone_result = {key: value}
    execute_func = mock.Mock()
    if not raise_error:
        execute_func.return_value.fetchone.return_value = fetchone_result
    else:
        execute_func.return_value.fetchone.side_effects = [error_raised]

    #
    from version.gallerydb import TagDB
    TagDB.execute = execute_func
    res = TagDB._look_exists_when_add_tags(tag_or_ns=tag_or_ns, what=arg)
    if not raise_error:
        assert res == value
    else:
        assert res is None
    execute_func.assert_has_calls([
        mock.call(
            TagDB, 'SELECT {} FROM {}s WHERE {} = ?'.format(key, arg, arg),
            (tag_or_ns,)
        ),
        mock.call().fetchone()]
    )


@version_0_31_0_only
@pytest.mark.parametrize('func_result', [None, mock.Mock()])
def test_get_id(func_result):
    """test method."""
    m_func = mock.Mock(return_value=func_result)
    exec_func = mock.Mock()
    ton = mock.Mock()
    ton_name = mock.Mock()
    from version.gallerydb import TagDB
    TagDB._look_exists_when_add_tags = m_func
    TagDB.execute = exec_func
    # run
    res = TagDB._get_id(tag_or_ns=ton, ton_name=ton_name)
    # test
    m_func.assert_called_once_with(tag_or_ns=ton, what=ton_name)
    if func_result is None:
        assert res == exec_func.return_value.lastrowid
        exec_func.assert_called_once_with(
            TagDB, "INSERT INTO {name}s({name}) VALUES(?)".format(name=ton_name), (ton,))
    elif isinstance(func_result, mock.Mock):
        assert res == func_result
        exec_func.assert_not_called()


@version_0_31_0_only
@pytest.mark.parametrize("value_name", ['tag', 'namespace'])
def test_get_all_value(value_name):
    """test method."""
    value = mock.Mock()
    exec_func = mock.Mock()
    exec_func.return_value.fetchall.return_value = [{value_name: value}]
    from version.gallerydb import TagDB
    TagDB.execute = exec_func
    # run
    res = TagDB._get_all_value(value_name=value_name)
    # test
    assert res == [value]
    exec_func.assert_has_calls([
        mock.call(TagDB, 'SELECT {value_name} FROM {value_name}s'.format(value_name=value_name)),
        mock.call().fetchall()
    ])


@version_0_31_0_only
@pytest.mark.parametrize('search_func_result', [True, False])
def test_return_is_exclude(search_func_result):
    """test method."""
    search_func = mock.Mock()
    search_func.return_value = search_func_result
    #
    key = mock.Mock()
    subkey = mock.Mock()
    value = mock.Mock()
    #
    tag = mock.Mock()
    args = mock.Mock()
    from version.gallerydb import Gallery
    Gallery.tags = {key: {subkey: value}}
    # run
    res = Gallery._return_is_exclude(search_func=search_func, tag=tag, args=args)
    # test
    if search_func_result:
        assert res
    else:
        assert not res
    search_func.assert_called_once_with(tag, subkey, True, args=args)


@version_0_31_0_only
@pytest.mark.parametrize('search_func_result, cond', product([True, False], repeat=2))
def test_return_is_exclude_on_simple_tag(search_func_result, cond):
    """test method."""
    tag = mock.Mock()
    args = mock.Mock()
    #
    search_func = mock.Mock()
    search_func.return_value = search_func_result
    #
    key = mock.Mock()
    value = mock.Mock()
    from version.gallerydb import Gallery
    Gallery.tags = {key: [value]}
    # run
    res = Gallery._return_is_exclude_on_simple_tag(
        cond=cond, key=key, search_func=search_func, tag=tag, args=args)
    # test
    if search_func_result and cond:
        assert res
    else:
        assert not res

"""test module."""
from unittest import mock
import itertools

import pytest


M_OBJ = mock.Mock()


@pytest.mark.parametrize(
    'm_os_name',
    [mock.Mock(), "posix"]
)
def test_get_path(m_os_name):
    """test func."""
    with mock.patch('version.settings.os') as m_os, \
            mock.patch('version.settings.__file__') as m_file:
        m_os.name = m_os_name
        if m_os_name == 'posix':
            exp_res = (m_os.path.join.return_value, m_os.path.join.return_value)
        else:
            exp_res = ('settings.ini', '.happypanda')
        from version import settings
        res = settings._get_path()
        assert res == exp_res
        if m_os_name == 'posix':
            m_os.assert_has_calls([
                mock.call.path.realpath(m_file),
                mock.call.path.dirname(m_os.path.realpath.return_value),
                mock.call.path.join(m_os.path.dirname.return_value, 'settings.ini'),
                mock.call.path.realpath(m_file),
                mock.call.path.dirname(m_os.path.realpath.return_value),
                mock.call.path.join(m_os.path.dirname.return_value, '.happypanda')
            ])
        else:
            assert not m_os.mock_calls


@pytest.mark.parametrize(
    'isfile_retval',
    [True, False]
)
def test_open_settings_path(isfile_retval):
    """test func."""
    m_open = mock.mock_open()
    m_path = mock.Mock()
    with mock.patch('version.settings.os') as m_os, \
            mock.patch('version.settings.open', m_open, create=True):
        from version import settings
        m_os.path.isfile.return_value = isfile_retval
        settings._open_settings_path(m_path)
        # test
        m_os.path.isfile.assert_called_once_with(m_path)
        if isfile_retval:
            assert not m_open.mock_calls
        else:
            m_open.assert_called_once_with(m_path, 'x')


def test_config_class_init():
    """test init func."""
    with mock.patch('version.settings.super') as m_super:
        from version import settings
        settings.Config()
        m_super.assert_called_once_with()


@pytest.mark.parametrize('m_encoding', [M_OBJ, None])
def test_config_class_read(m_encoding):
    """test func."""
    m_filenames = mock.Mock()
    with mock.patch('version.settings.super') as m_super:
        # pre run
        from version import settings
        # run
        conf = settings.Config()
        conf.read(m_filenames, m_encoding)
        # test
        m_super.assert_has_calls([
            mock.call(),
            mock.call(),
        ])
        assert conf.custom_cls_file == m_filenames


@pytest.mark.parametrize(
    (
        'm_encoding, '
        'm_space_around_delimeters, '
        'hasattr_retval, '
        'isinstance_retval, '
        'set_custom_cls_file, '
        'm_custom_cls_file'
    ),
    itertools.product(
        ['utf8', None, M_OBJ],
        [True, False, M_OBJ, None],
        [True, False],
        [True, False],
        [True, False],
        [[M_OBJ], [], None],
    )
)
def test_config_class_save(
    m_encoding,
    m_space_around_delimeters,
    hasattr_retval,
    isinstance_retval,
    set_custom_cls_file,
    m_custom_cls_file
):
    """test func."""
    m_space_around_delimeters = None
    save_kwargs = {}
    if m_encoding is not None:
        save_kwargs['encoding'] = m_encoding
    if m_space_around_delimeters is not None:
        save_kwargs['space_around_delimeters'] = m_space_around_delimeters
    m_open = mock.mock_open()
    write_method_second_arg = \
        m_space_around_delimeters if m_space_around_delimeters is not None else True
    open_func_third_arg = m_encoding if m_encoding is not None else 'utf-8'
    if m_custom_cls_file == [M_OBJ] and not isinstance_retval and hasattr_retval:
        open_func_first_arg = M_OBJ
    else:
        open_func_first_arg = m_custom_cls_file
    if not isinstance_retval and hasattr_retval:
        m_open_first_call = mock.call(open_func_first_arg, 'w', encoding=open_func_third_arg)
    else:
        m_open_first_call = mock.call(open_func_first_arg, 'w')
    if m_custom_cls_file in ([], None) and not isinstance_retval and hasattr_retval:
        m_open_calls = None
    else:
        m_open_calls = [
            m_open_first_call,
            mock.call().__enter__(),
            mock.call().__exit__(None, None, None)
        ]
    with mock.patch('version.settings.log') as m_log, \
            mock.patch('version.settings.isinstance') as m_isinstance, \
            mock.patch('version.settings.hasattr') as m_hasattr, \
            mock.patch('version.settings.open', m_open, create=True), \
            mock.patch('version.settings.Config.write') as m_write:
        # pre run
        from version import settings
        m_isinstance.return_value = isinstance_retval
        m_hasattr.return_value = hasattr_retval
        conf = settings.Config()
        if set_custom_cls_file:
            conf.custom_cls_file = m_custom_cls_file
        # run
        conf.save(**save_kwargs)
        # test
        if not set_custom_cls_file:
            # exception reached because AttributeError raised
            # when testing class attr custom_cls_file
            m_log.exception.assert_called_once_with('Could not save settings')
        else:
            m_isinstance.assert_called_once_with(conf.custom_cls_file, str)
            if isinstance_retval:
                assert not m_hasattr.mock_calls
            else:
                m_hasattr.assert_called_once_with(conf.custom_cls_file, '__iter__')
            if m_open_calls is not None:
                m_open.assert_has_calls(m_open_calls)
                m_write.assert_called_once_with(m_open.return_value, write_method_second_arg)
            else:
                assert not m_open.mock_calls
                m_write.assert_not_called()


def test_config_class_save_raise_permission_error():
    """test config class save method when raise PermissionError."""
    m_open = mock.mock_open()
    m_custom_cls_file = mock.Mock()
    with mock.patch('version.settings.open', m_open, create=True), \
            mock.patch('version.settings.log_e') as m_log_e:
        # pre run
        m_open.side_effect = PermissionError  # NOQA
        from version import settings
        obj = settings.Config()
        obj.custom_cls_file = m_custom_cls_file
        # run
        obj.save()
        # test
        m_log_e.assert_called_once_with('Could not save settings: PermissionError')


def test_save():
    """test func."""
    m_config = mock.Mock()
    with mock.patch('version.settings.ExProperties') as m_ex_properties:
        # pre run
        from version import settings
        settings.config = m_config
        # run
        settings.save()
        # test
        m_config.save.assert_called_once_with()
        m_ex_properties.save.assert_called_once_with()


def assert_dict(v1, v2):
    """assert 1d two dict.

    it can't handle if there is iter on value.
    """
    for key in v1:
        assert key in v2
        assert v1[key] == v2[key]
    assert len(v1) == len(v2)


@pytest.mark.parametrize(
    'm_key, m_config_var',
    itertools.product(
        ['key', '', 100],
        [
            {},
            {'section': 'section_value'},
            {'section': {'key': 'key_value'}}
        ]
    )
)
def test_get_value(m_key, m_config_var):
    """test func."""
    m_key_value = 'key_value'
    m_default = mock.Mock()
    m_section = 'section'
    m_section_value = 'section_value'
    m_section_dict_value = {'key': 'key_value'}
    from version import settings
    if m_key == 'key' and m_config_var == {'section': 'section_value'}:
        with pytest.raises(TypeError):
            settings._get_value(m_key, m_section, m_default, m_config_var)
    elif m_key == 100 and m_config_var == {'section': 'section_value'}:
        with pytest.raises(IndexError):
            settings._get_value(m_key, m_section, m_default, m_config_var)
    else:
        res = settings._get_value(m_key, m_section, m_default, m_config_var)
        # only assert once
        assert_success = False
        if m_key:
            if m_section in m_config_var:
                if m_key in m_config_var[m_section]:
                    assert res == m_key_value
                    assert_success = True
            if not assert_success:
                assert res == m_default
            assert_success = True
        else:
            if m_section in m_config_var:
                if isinstance(res, dict):
                    assert_dict(res, m_section_dict_value)
                else:
                    assert res == m_section_value
            else:
                assert res == m_default
            assert_success = True
        assert assert_success


@pytest.mark.parametrize(
    'm_value, exp_value',
    [
        ('FALSE', False),
        ('False', False),
        ('false', False),
        ('TRUE', True),
        ('True', True),
        ('true', True),
        ('NONE', None),
        ('None', None),
        ('none', None),
        ('va1>|<va2>|<va3', 'va1>|<va2>|<va3'),
        ('va1>|<>|<va3', 'va1>|<>|<va3'),
        ('va1>|<', 'va1>|<'),
        ('>|<va1', '>|<va1'),
        ('', ''),
        ('adfsjklasjdfskdfj', 'adfsjklasjdfskdfj'),
        ('23423423423432', '23423423423432'),
        (23423423423432, None),
        (M_OBJ, str(M_OBJ)),
    ]
)
def test_normalize_value(m_value, exp_value):
    """test func."""
    # pre run
    from version import settings
    # test and run
    if not hasattr(m_value, "lower"):
        with pytest.raises(AttributeError):
            settings._normalize_value(m_value)
    elif exp_value is not None:
        assert exp_value == settings._normalize_value(m_value)
    else:
        assert settings._normalize_value(m_value) is None


def _get_exp_res_for_test_normalize_value(
    m_value,
    m_type_class,
    m_subtype_class,
):
    """get expected result for test_normalize_value_with_different_class."""
    try:
        exp_res = m_type_class(m_value)
    except (IndexError, TypeError):
        if isinstance(m_subtype_class, mock.Mock) and m_type_class is None:
            exp_res = str(m_value)
        elif isinstance(m_subtype_class, mock.Mock):
            exp_res = m_subtype_class.return_value
        else:
            exp_res = m_subtype_class(m_value)
    return exp_res


def _get_normalize_value_parametrize_args():
    """parametrize args for normalize_value_parametrize_args func."""
    return (
        'm_value, m_type_class, m_subtype_class, type_class_raise_error',
        itertools.product(
            ['', 'adf', mock.Mock()],
            [str, list, tuple, mock.Mock(), None],
            [mock.Mock(), None],
            [True, False],
        )
    )


@pytest.mark.parametrize(
    *_get_normalize_value_parametrize_args()
)
def test_normalize_value_with_different_class(
    m_value,
    m_type_class,
    m_subtype_class,
    type_class_raise_error
):
    """test func."""
    type_class_retval = mock.Mock()
    input_kwargs = {'value': m_value}
    if m_type_class is not None:
        input_kwargs['type_class'] = m_type_class
    if m_subtype_class is not None:
        input_kwargs['subtype_class'] = m_subtype_class
    # pre run
    from version import settings
    # run and test
    # test which raise error.
    if isinstance(m_value, mock.Mock) and m_type_class in (list, tuple):
        with pytest.raises(TypeError):
            settings._normalize_value(**input_kwargs)
    else:
        # set to raise error or not
        if type_class_raise_error and isinstance(m_type_class, mock.Mock):
            m_type_class.side_effect = IndexError
        elif isinstance(m_type_class, mock.Mock):
            m_type_class.side_effect = None
            m_type_class.return_value = type_class_retval
        # test
        if \
                type_class_raise_error and \
                isinstance(m_type_class, mock.Mock) and \
                (m_subtype_class is None):
            with pytest.raises(IndexError):
                settings._normalize_value(**input_kwargs)
        else:
            res = settings._normalize_value(**input_kwargs)
            if m_type_class in (list, tuple):
                assert res == m_type_class([x for x in m_value.split('>|<') if x])
            elif m_subtype_class:
                exp_res = _get_exp_res_for_test_normalize_value(
                    m_value,
                    m_type_class,
                    m_subtype_class,
                )
                assert res == exp_res
            elif m_type_class is None:
                assert res == str(m_value)
            else:
                assert res == m_type_class(m_value)


@pytest.mark.parametrize(
    'get_value_raise_error, normalize_value_side_effect, m_type_class, m_key, m_subtype_class',
    itertools.product(
        [False, True],
        [None, AttributeError, IndexError],
        [str, None],
        [None, mock.Mock()],
        [None, mock.Mock()]
    )
)
def test_get(
    get_value_raise_error,
    normalize_value_side_effect,
    m_type_class,
    m_key,
    m_subtype_class
):
    """test get func."""
    m_default = mock.Mock()
    m_section = mock.Mock()
    m_config = mock.Mock()
    normalize_retval = mock.Mock()
    input_kwargs = {'default': m_default, 'section': m_section}
    if m_type_class is not None:
        input_kwargs['type_class'] = m_type_class
        type_class_in_func = m_type_class
    else:
        type_class_in_func = str
    if m_key is not None:
        input_kwargs['key'] = m_key
    if m_subtype_class is not None:
        input_kwargs['subtype_class'] = m_subtype_class
    with mock.patch('version.settings._get_value') as m_get_value, \
            mock.patch('version.settings._normalize_value') as m_normalize_value:
        # pre run
        m_normalize_value.return_value = normalize_retval
        if normalize_value_side_effect is not None:
            m_normalize_value.side_effect = normalize_value_side_effect
        if get_value_raise_error:
            m_get_value.side_effect = ValueError
        from version import settings
        settings.config = m_config
        # run
        res = settings.get(**input_kwargs)
        # test
        m_get_value.assert_called_once_with(m_key, m_section, m_default, config_var=m_config)
        if not get_value_raise_error:
            m_normalize_value.assert_called_once_with(
                m_get_value.return_value,
                type_class=type_class_in_func,
                subtype_class=m_subtype_class)
            if normalize_value_side_effect == AttributeError:
                assert res == m_get_value.return_value
            elif normalize_value_side_effect is not None:
                assert res == m_default
            else:
                assert res == m_normalize_value.return_value
        else:
            assert not m_normalize_value.mock_calls
            assert res == m_default


@pytest.mark.parametrize(
    'm_config, m_key, m_section, m_value',
    itertools.product(
        [mock.Mock(), {}],
        [None, mock.Mock()],
        [mock.Mock(), 'm_section'],
        [mock.Mock(), 'm_key', ['v1'], ['v1', 'v2']]
    )
)
def test_set(m_config, m_key, m_section, m_value):
    """test func."""
    input_kwargs = {'value': m_value, 'section': m_section}
    if m_key is not None:
        input_kwargs['key'] = m_key
    from version import settings
    settings.config = m_config
    if isinstance(m_config, mock.Mock) or isinstance(m_key, mock.Mock):
        with pytest.raises(TypeError):
            settings.set(**input_kwargs)
    else:
        settings.set(**input_kwargs)
        if m_key:
            assert {m_section: {m_key: str(m_value)}} == m_config
        else:
            assert m_section in m_config
        if not m_key and isinstance(m_value, (list, tuple)):
            if m_value == ['v1']:
                assert m_config[m_section] == 'v1'
            elif m_value == ['v1', 'v2']:
                assert m_config[m_section] == 'v1>|<v2'
            else:
                raise NotImplementedError
        elif not m_key:
            assert m_config[m_section] == str(m_value)


@pytest.mark.parametrize(
    'm_site, os_path_exists_retval, m_info',
    itertools.product(
        [None, mock.Mock()],
        [True, False],
        [{}, False, {'key': "value"}]
    )
)
def test_ex_properties_class_init(m_site, os_path_exists_retval, m_info):
    """test class init func."""
    m_open = mock.mock_open()
    m_phappypanda_path = mock.Mock()
    with mock.patch('version.settings.open', m_open, create=True), \
            mock.patch('version.settings.os') as m_os, \
            mock.patch('version.settings.pickle') as m_pickle:
        # pre run
        from version import settings
        m_os.path.exists.return_value = os_path_exists_retval
        settings.phappypanda_path = m_phappypanda_path
        settings.ExProperties._INFO = m_info
        # run
        if m_site is None:
            prop = settings.ExProperties()
        else:
            prop = settings.ExProperties(site=m_site)
        # test
        if not m_info:
            m_os.path.exists.assert_called_once_with(m_phappypanda_path)
            if os_path_exists_retval:
                m_open.assert_has_calls([
                    mock.call(m_phappypanda_path, 'rb'),
                    mock.call().__enter__(),
                    mock.call().__exit__(None, None, None)
                ])
                m_pickle.load.assert_called_once_with(m_open.return_value)
                assert prop.__class__._INFO == m_pickle.load.return_value
            else:
                assert not m_open.mock_calls
                assert not m_pickle.mock_calls
                assert prop.__class__._INFO == m_info
        else:
            assert not m_open.mock_calls
            assert not m_pickle.mock_calls
            assert prop.__class__._INFO == m_info
        if m_site is None:
            assert prop.site == prop.EHENTAI
        else:
            assert prop.site == m_site


@pytest.mark.parametrize(
    'm_info',
    [{}, False, True]
)
def test_ex_properties_class_save_method(m_info):
    """test class func."""
    m_open = mock.mock_open()
    m_phappypanda_path = mock.Mock()
    m_phappypanda_path = mock.Mock()
    with mock.patch('version.settings.open', m_open, create=True), \
            mock.patch('version.settings.pickle') as m_pickle:
        # pre run
        from version import settings
        settings.ExProperties._INFO = m_info
        settings.phappypanda_path = m_phappypanda_path
        # run
        settings.ExProperties.save()
        # test
        if settings.ExProperties._INFO:
            m_pickle.dump.assert_called_once_with(m_info, m_open.return_value, 4)
            m_open.assert_has_calls([
                mock.call(m_phappypanda_path, 'wb'),
                mock.call().__enter__(),
                mock.call().__exit__(None, None, None)
            ])
        else:
            assert not m_pickle.mock_calls
            assert not m_open.mock_calls


@pytest.mark.parametrize(
    'prop, is_info_empty_dict',
    itertools.product(
        ['cookies', 'username', 'password'],
        [True, False]
    )
)
def test_ex_properties_class_property_setter(prop, is_info_empty_dict):
    """test property."""
    m_site = 0
    if is_info_empty_dict:
        m_info = {}
    else:
        m_info = []
    m_value = mock.Mock()
    with mock.patch('version.settings.ExProperties.__init__', return_value=None):
        # pre run
        from version import settings
        settings.ExProperties._INFO = m_info
        obj = settings.ExProperties()
        obj.site = m_site
        # run and test
        if is_info_empty_dict:
            setattr(obj, prop, m_value)
            assert obj._INFO[m_site][prop] == m_value
        elif not is_info_empty_dict and m_info == []:
            with pytest.raises(IndexError):
                setattr(obj, prop, m_value)
        else:
            raise NotImplementedError


@pytest.mark.parametrize(
    'prop, value_exist, is_site_in_info',
    itertools.product(
        ['cookies', 'username', 'password'],
        [False, True],
        [False, True]
    )
)
def test_ex_properties_class_property(prop, value_exist, is_site_in_info):
    """test property."""
    m_site = 0
    m_info = {}
    m_value = mock.Mock()
    if value_exist:
        m_info[m_site] = {}
        m_info[m_site][prop] = m_value
        exp_res = m_value
    else:
        if is_site_in_info:
            m_info[m_site] = {}
        exp_res = None if prop != 'cookies' else {}
    with mock.patch('version.settings.ExProperties.__init__', return_value=None):
        # pre run
        from version import settings
        obj = settings.ExProperties()
        obj._INFO = m_info
        obj.site = m_site
        # run
        if is_site_in_info and not value_exist:
            with pytest.raises(KeyError):
                getattr(obj, prop)
        else:
            assert getattr(obj, prop) == exp_res


@pytest.mark.parametrize(
    "m_site, m_cookies",
    itertools.product(
        [None, 'ehentai', 'nhentai', 3],
        [
            {},
            {'sessionid': None},
            {'ipb_session_id': None},
            {'ipb_session_id': None, 'ipb_pass_hash': None}
        ],
    )
)
def test_ex_properties_class_check_method(m_site, m_cookies):
    """check class method."""
    exp_res = True
    m_info = {}
    if m_site == 'ehentai' and 'ipb_session_id' not in m_cookies:
        exp_res = 0
    elif \
            (m_site == 'ehentai') and \
            ('ipb_session_id' in m_cookies) and \
            ('ipb_pass_hash' in m_cookies):
        exp_res = 2
    elif m_site == 'ehentai' and 'ipb_session_id' in m_cookies:
        exp_res = 1
    elif m_site == 'nhentai' and 'sessionid' not in m_cookies:
        exp_res = False
    with mock.patch('version.settings.ExProperties.__init__', return_value=None):
        # pre run
        from version import settings
        if m_site == 'ehentai':
            m_site = settings.ExProperties.EHENTAI
        elif m_site == 'nhentai':
            m_site = settings.ExProperties.NHENTAI
        settings.ExProperties._INFO = m_info
        obj = settings.ExProperties()
        obj.site = m_site
        obj.cookies = m_cookies
        # run
        res = obj.check()
        assert res == exp_res and type(res) == type(exp_res)


@pytest.mark.parametrize(
    'prop, m_value',
    itertools.product(
        ['resize', 'pos'],
        [(0, 0), [0, 0], 1]
    )
)
def test_win_properties_class(prop, m_value):
    """test class."""
    # pre run
    property_raise_error = False
    if type(m_value) in (list, tuple):
        exp_res = tuple(m_value)
    elif prop == 'pos':
        exp_res = (0, 0)
        property_raise_error = True
    elif prop == 'resize':
        exp_res = None
        property_raise_error = True
    from version import settings
    obj = settings.WinProperties()
    # run and test
    assert obj._resize is None
    assert obj._pos == (0, 0)
    if not property_raise_error:
        setattr(obj, prop, m_value)
        assert getattr(obj, prop) == exp_res
        assert getattr(obj, '_' + prop) == exp_res
    else:
        with pytest.raises(AssertionError):
            setattr(obj, prop, m_value)
        if exp_res is not None:
            assert getattr(obj, prop) == exp_res
            assert getattr(obj, '_' + prop) == exp_res
        else:
            assert getattr(obj, prop) is None
            assert getattr(obj, '_' + prop) is None


@pytest.mark.parametrize(
    'm_name, m_config',
    itertools.product(
        ['m_name', 1],
        [
            {},
            {'m_name': None},
            {'m_name': {}},
            {'m_name': {'resize.w': 0, 'resize.h': 1}},
            {'m_name': {'resize.w': '0', 'resize.h': '1'}},
            {'m_name': {'pos.x': 2, 'pos.y': 3}},
            {'m_name': {'pos.x': '2', 'pos.y': '3'}},
            {'m_name': {'pos.x': 4, 'pos.y': 5, 'resize.w': 6, 'resize.h': 7}},
            {'m_name': {'pos.x': '4', 'pos.y': '5', 'resize.w': '6', 'resize.h': '7'}},
        ]
    )
)
def test_win_read(m_name, m_config):
    """test func."""
    cls = 'm_cls'
    winprop_retval = mock.Mock()
    exp_resize = winprop_retval.resize
    exp_pos = winprop_retval.pos
    type_error_raised = False
    if m_name in m_config:
        try:
            exp_resize = (int(m_config[m_name]['resize.w']), int(m_config[m_name]['resize.h']))
            exp_pos = (int(m_config[m_name]['pos.x']), int(m_config[m_name]['pos.y']))
        except TypeError:
            type_error_raised = True
        except KeyError:
            pass
    with mock.patch('version.settings.WinProperties') as m_winprop:
        m_winprop.return_value = winprop_retval
        from version import settings
        settings.config = m_config
        if not isinstance(m_name, str):
            with pytest.raises(AssertionError):
                settings.win_read(cls, m_name)
        elif type_error_raised:
            with pytest.raises(TypeError):
                settings.win_read(cls, m_name)
        else:
            res = settings.win_read(cls, m_name)
            assert res == winprop_retval
            assert res.resize == exp_resize
            assert res.pos == exp_pos
            m_winprop.assert_called_once_with()
            assert len(m_winprop.mock_calls) == 1


@pytest.mark.parametrize(
    "winprops_arg",
    [None, 'winprop', mock.Mock()]
)
def test_win_save(winprops_arg):
    """test func."""
    m_cls = mock.Mock()
    m_name = "m_name"
    m_save = mock.Mock()
    import configparser
    m_config = configparser.ConfigParser()
    m_config.save = m_save
    exp_dict_config = {
        'pos.x': str(m_cls.pos.return_value.x.return_value),
        'pos.y': str(m_cls.pos.return_value.y.return_value),
        'resize.h': str(m_cls.size.return_value.height.return_value),
        'resize.w': str(m_cls.size.return_value.width.return_value),
    }
    # pre run
    from version import settings
    if winprops_arg == 'winprop':
        winprops_arg = settings.WinProperties()
    settings.config = m_config
    winprops_arg_is_winprop =  isinstance(winprops_arg, settings.WinProperties)
    # run
    if winprops_arg is None:
        settings.win_save(m_cls, m_name)
    elif not winprops_arg_is_winprop:
        with pytest.raises(AssertionError):
            settings.win_save(m_cls, m_name, winprops_arg)
    else:
        settings.win_save(m_cls, m_name, winprops_arg)
    # test
    if not winprops_arg_is_winprop:
        pass
    else:
        m_save.assert_called_once_with()
    if not winprops_arg:
        m_name_dict_config = dict(m_config[m_name])
        assert m_name_dict_config == exp_dict_config

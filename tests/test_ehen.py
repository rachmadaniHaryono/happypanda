"""test ehen module."""
from unittest import mock

import pytest


@pytest.mark.parametrize('cookies', [None, mock.Mock()])
def test_init(cookies):
    """test init."""
    from version.ehen import EHen
    eh = EHen(cookies)

    assert eh.e_url == "http://g.e-hentai.org/api.php"
    assert eh.e_url_o == "http://g.e-hentai.org/"
    if cookies is None:
        assert eh.cookies is None
    else:
        eh.cookies == cookies


def test_login_with_exprops_cookies():
    """test method."""
    check_login_result = True
    key = mock.Mock()
    value = mock.Mock()
    m_exp_cookies = {key: value}
    from version.ehen import EHen
    with mock.patch('version.ehen.ExProperties') as m_ex_prop, \
            mock.patch.object(EHen, 'check_login', return_value=check_login_result) \
            as m_check_login:
        m_ex_prop.return_value.cookies = m_exp_cookies
        obj = EHen()
        assert obj.COOKIES == {}
        # run
        res = obj.login(mock.Mock(), mock.Mock())
        # test
        assert res == m_exp_cookies
        m_check_login.assert_called_once_with(m_exp_cookies)
        m_ex_prop.assert_called_once_with()


@pytest.mark.parametrize('check_login_result', [True, False])
def test_login_with_invalid_exprops_cookies(check_login_result):
    """test method."""
    key = mock.Mock()
    value = mock.Mock()
    m_exp_cookies = {key: value}
    m_eh_c = {mock.Mock(): mock.Mock()}
    m_exh_c = {mock.Mock(): mock.Mock()}
    username = mock.Mock()
    password = mock.Mock()
    from version.ehen import EHen
    from version.ehen import app_constants
    with mock.patch('version.ehen.ExProperties') as m_ex_prop, \
            mock.patch.object(
                EHen, 'check_login',
                side_effect=lambda arg: check_login_result if arg == m_eh_c else False), \
            mock.patch('version.ehen.requests') as m_req:
        m_ex_prop.return_value.cookies = m_exp_cookies
        m_req.post.return_value.cookies.get_dict.return_value = m_eh_c
        m_req.get.return_value.cookies.get_dict.return_value = m_exh_c
        #
        obj = EHen()
        # run
        if not check_login_result:
            with pytest.raises(app_constants.WrongLogin):
                obj.login(username, password)
            return
        res = obj.login(username, password)
        # test
        # m_eh_c in res
        assert m_eh_c.items() <= res.items()
        # m_exh_c in res
        assert m_exh_c.items() <= res.items()
        #
        m_ex_prop.assert_has_calls([mock.call(), mock.call().save()])
        m_req.assert_has_calls([
            mock.call.post(
                'https://forums.e-hentai.org/index.php?act=Login&CODE=01',
                data={
                    'UserName': m_ex_prop.return_value.username, 'b': 'd',
                    'PassWord': m_ex_prop.return_value.password, 'bt': '1-1',
                    'CookieDate': '1'
                }
            ),
            mock.call.post().cookies.get_dict(),
            mock.call.get('http://exhentai.org', cookies=m_eh_c),
            mock.call.get().cookies.get_dict()
        ])


def test_login_with_existing_cookies():
    """test method."""
    check_login_result = True
    m_check_login = mock.Mock(return_value=check_login_result)
    m_cookies = mock.Mock()
    from version.ehen import EHen
    with mock.patch('version.ehen.ExProperties') as m_ex_prop, \
            mock.patch.object(EHen, 'check_login', return_value=check_login_result) \
            as m_check_login, \
            mock.patch.object(EHen, 'COOKIES', m_cookies):
        obj = EHen()
        # run
        res = obj.login(mock.Mock(), mock.Mock())
        # test
        assert res == m_cookies
        m_check_login.assert_called_once_with(m_cookies)
        m_ex_prop.assert_called_once_with()


@pytest.mark.parametrize('artist_in_tags', [False, True])
def test_set_g_artist(artist_in_tags):
    """test method."""
    artist = mock.Mock()
    if not artist_in_tags:
        data = {'tags': {}}
    else:
        data = {'tags': {'Artist': [artist]}}
    g_artist = mock.Mock()
    from version.ehen import EHen
    # run
    res = EHen._get_g_artist(g_artist, data)
    # test
    if not artist_in_tags:
        assert res == g_artist
    else:
        assert res == artist.capitalize.return_value

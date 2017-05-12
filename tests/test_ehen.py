"""test ehen module."""
from unittest import mock
from itertools import product

import pytest


@pytest.mark.parametrize('cookies', [None, mock.Mock()])
def test_init(cookies):
    """test init."""
    from happypanda.ehen import EHen
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
    from happypanda.ehen import EHen
    with mock.patch('happypanda.ehen.ExProperties') as m_ex_prop, \
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
    from happypanda.ehen import EHen
    from happypanda.ehen import app_constants
    with mock.patch('happypanda.ehen.ExProperties') as m_ex_prop, \
            mock.patch.object(
                EHen, 'check_login',
                side_effect=lambda arg: check_login_result if arg == m_eh_c else False), \
            mock.patch('happypanda.ehen.requests') as m_req:
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
    from happypanda.ehen import EHen
    with mock.patch('happypanda.ehen.ExProperties') as m_ex_prop, \
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
def test_get_g_artist(artist_in_tags):
    """test method."""
    artist = mock.Mock()
    if not artist_in_tags:
        data = {'tags': {}}
    else:
        data = {'tags': {'Artist': [artist]}}
    g_artist = mock.Mock()
    from happypanda.ehen import EHen
    # run
    res = EHen._get_g_artist(g_artist, data)
    # test
    if not artist_in_tags:
        assert res == g_artist
    else:
        assert res == artist.capitalize.return_value


@pytest.mark.parametrize(
    'temp_url_in_gallery, url_is_none, no_url_on_data',
    product([False, True], repeat=3)
)
def test_get_g_link(temp_url_in_gallery, url_is_none, no_url_on_data):
    """test method."""
    gallery = mock.Mock()
    url = mock.Mock()
    if no_url_on_data:
        data = {}
    elif url_is_none:
        data = {'url': None}
    else:
        data = {'url': url}
    with mock.patch('happypanda.ehen.hasattr') as m_ha:
        m_ha.return_value = True if temp_url_in_gallery else False
        from happypanda.ehen import EHen
        # run
        res = EHen._get_g_link(gallery=gallery, data=data)
        # test
        if temp_url_in_gallery and (url_is_none or no_url_on_data):
            assert res == gallery.temp_url
        elif not url_is_none and not no_url_on_data:
            assert res == url
        else:
            assert res is None


@pytest.mark.parametrize(
    'use_jpn_title, only_def_title_in_data, jpn_title_empty',
    product([True, False], repeat=3)
)
def test_title_get_title_from_data(use_jpn_title, only_def_title_in_data, jpn_title_empty):
    """test method."""
    if jpn_title_empty:
        jpn = ''
    else:
        jpn = mock.Mock()
    def_title = mock.Mock()
    if only_def_title_in_data:
        data = {'title': {'def': def_title}}
    else:
        data = {'title': {'jpn': jpn, 'def': def_title}}
    with mock.patch('happypanda.ehen.app_constants') as m_ac:
        m_ac.USE_JPN_TITLE = use_jpn_title
        from happypanda.ehen import EHen
        res = EHen._get_title_from_data(data)
        if use_jpn_title and not only_def_title_in_data and not jpn_title_empty:
            assert res == jpn
        else:
            assert res == def_title


@pytest.mark.parametrize('key_in_data, correct_lang_in_tags', product([True, False], repeat=2))
def test_get_lang_from_data(key_in_data, correct_lang_in_tags):
    """test method."""
    lang = 'english'
    lang_capitalized = lang.capitalize()
    if key_in_data and correct_lang_in_tags:
        data = {'tags': {'Language': ['translated', lang]}}
    elif key_in_data and not correct_lang_in_tags:
        data = {'tags': {'Language': ['translated']}}
    else:
        data = {'tags': []}
    from happypanda.ehen import EHen
    res = EHen._get_lang_from_data(data)
    if key_in_data and correct_lang_in_tags:
        assert res == lang_capitalized
    else:
        assert res == ''


@pytest.mark.parametrize(
    'lang, title, artist_in_parsed_title_result, url_in_data',
    product(
        ['', mock.Mock()],
        ['', mock.Mock()],
        [True, False],
        [True, False],
    )
)
def test_apply_metadata_by_replacing_it(
        lang, title, artist_in_parsed_title_result, url_in_data
):
    """test method."""
    append = False
    gallery = mock.Mock()
    g_artist = mock.Mock()
    #
    d_type = mock.Mock()
    d_pub_date = mock.Mock()
    d_tags = mock.Mock()
    d_url = mock.Mock()
    data = {'type': d_type, 'pub_date': d_pub_date, 'tags': d_tags}
    if url_in_data:
        data['url'] = d_url
    #
    tp_title = mock.Mock()
    tp_language = mock.Mock()
    tp_artist = mock.Mock()
    tp_result = {'title': tp_title, 'language': tp_language, 'artist': None}
    if artist_in_parsed_title_result:
        tp_result['artist'] = tp_artist
    #
    with mock.patch('happypanda.ehen.title_parser', return_value=tp_result) as m_tp:
        from happypanda.ehen import EHen
        #
        EHen._get_title_from_data = mock.Mock(return_value=title)
        EHen._get_lang_from_data = mock.Mock(return_value=lang)
        EHen._get_g_artist = mock.Mock(return_value=g_artist)
        # run
        res = EHen.apply_metadata(g=gallery, data=data, append=append)
        # test
        m_tp.assert_called_once_with(title)
        assert res.title == tp_title
        assert res.artist == g_artist
        if lang:
            assert res.language == lang
        else:
            assert res.language == tp_language.capitalize()
        #
        keys = ['type', 'pub_date', 'tags']
        for key in keys:
            assert getattr(gallery, key) == data[key]
        #
        if 'url' in data:
            assert res.link == data['url']
        else:
            assert res.link == res.temp_url


@pytest.mark.parametrize(  # NOQA
    'gallery_have_metadata, lang, title, url_in_data, g_type, tags_pack',
    product(
        [False, True],
        ['', mock.Mock()],
        ['', mock.Mock()],
        [True, False],
        [None, 'Other', mock.Mock()],
        [
            ({}, {}, {}),
            ({'ns': []}, {}, {'ns': []}),
            ({}, {'ns': []}, {'ns': []}),
            ({'ns': ['tag1']}, {'ns': ['tag2']}, {'ns': ['tag1', 'tag2']}),
            ({'ns1': ['tag1']}, {'ns2': ['tag2']}, {'ns1': ['tag1'], 'ns2': ['tag2']}),
            (
                {'ns1': ['tag1']},
                {'ns1': ['tag3'], 'ns2': ['tag2']},
                {'ns1': ['tag1', 'tag3'], 'ns2': ['tag2']}
            ),
            (
                {'ns1': ['tag3'], 'ns2': ['tag2']},
                {'ns1': ['tag1']},
                {'ns1': ['tag3', 'tag1'], 'ns2': ['tag2']}
            ),
        ]
    )
)
def test_apply_metadata(
        gallery_have_metadata, lang, title, url_in_data, g_type, tags_pack
):
    """test method."""
    append = True
    g_artist = mock.Mock()
    #
    # gallery metadata keys
    # not included: url and type
    gm_keys = ['title', 'artist', 'language', 'pub_date', 'tags', 'link']
    gallery = mock.Mock()
    if not gallery_have_metadata:
        for key in gm_keys:
            setattr(gallery, key, None)
        gallery.tags = {}
    gallery.type = g_type
    #
    d_type = mock.Mock()
    d_pub_date = mock.Mock()
    d_tag_value = mock.Mock()
    d_tags = {'tag_key': d_tag_value}
    d_url = mock.Mock()
    data = {'type': d_type, 'pub_date': d_pub_date, 'tags': d_tags}
    if url_in_data:
        data['url'] = d_url
    if gallery_have_metadata:
        data['tags'] = {}
        gallery.tags, data['tags'], exp_res_tags = tags_pack
    #
    tp_title = mock.Mock()
    tp_language = mock.Mock()
    tp_artist = mock.Mock()
    tp_result = {'title': tp_title, 'language': tp_language, 'artist': tp_artist}
    #
    with mock.patch('happypanda.ehen.title_parser', return_value=tp_result) as m_tp:
        from happypanda.ehen import EHen
        #
        EHen._get_title_from_data = mock.Mock(return_value=title)
        EHen._get_lang_from_data = mock.Mock(return_value=lang)
        EHen._get_g_artist = mock.Mock(return_value=g_artist)
        # run
        res = EHen.apply_metadata(g=gallery, data=data, append=append)
        # test
        m_tp.assert_called_once_with(title)

        if not g_type or g_type == 'Other':
            assert res.type == d_type
        else:
            assert res.type == gallery.type

        if gallery_have_metadata:
            for key in ['title', 'artist', 'language', 'type', 'pub_date', 'link']:
                assert getattr(res, key) == getattr(gallery, key)
            assert res.tags == exp_res_tags
            return

        if not gallery_have_metadata:
            assert res.title == tp_title
            assert res.artist == g_artist
            assert res.pub_date == d_pub_date
            assert res.tags == d_tags

            if lang:
                assert res.language == lang
            else:
                assert res.language == tp_language.capitalize()

            if data.get('url') is not None:
                assert res.link == data.get('url')
            else:
                assert res.link == res.temp_url


@pytest.mark.parametrize(
    "cookies, exp_res",
    [
        ({}, 0),
        ({'ipb_session_id': mock.Mock()}, 1),
        ({'ipb_member_id': mock.Mock(), 'ipb_pass_hash': mock.Mock()}, 2),
        ({'ipb_member_id': mock.Mock()}, 0),
        ({'ipb_pass_hash': mock.Mock()}, 0),
        (
            {
                'ipb_member_id': mock.Mock(), 'ipb_pass_hash': mock.Mock(),
                'ipb_session_id': mock.Mock()
            },
            2
        ),
        (
            {
                'ipb_member_id': mock.Mock(),
                'ipb_session_id': mock.Mock()
            },
            1
        ),
        (
            {
                'ipb_pass_hash': mock.Mock(),
                'ipb_session_id': mock.Mock()
            },
            1
        ),
    ]
)
def test_check_login(cookies, exp_res):
    """test method."""
    from happypanda.ehen import EHen
    assert exp_res == EHen.check_login(cookies)


@pytest.mark.parametrize(
    'content_type, text',
    product(
        ['image/gif', 'text/html' 'other'],
        ['Your IP address has been banned', '', 'You are opening']
    )
)
def test_handle_error(content_type, text):
    """test method."""
    response = mock.Mock()
    response.headers = {'content-type': content_type}
    response.text = text
    notif_bar_func = mock.Mock()
    with mock.patch('happypanda.ehen.time') as m_time, \
            mock.patch('happypanda.ehen.random') as m_random:
        from happypanda.ehen import EHen
        obj = EHen()
        obj._add_text_to_notif_bar = notif_bar_func
        # run
        res = obj.handle_error(response)
        # test
        if 'image/gif' in content_type:
            notif_bar_func.assert_called_once_with('Provided exhentai credentials are incorrect!')
            m_time.sleep.assert_called_once_with(5)
            assert not res
        elif 'text/html' in content_type and 'Your IP address has been' in text:
            notif_bar_func.assert_called_once_with(
                "Your IP address has been temporarily banned from g.e-/exhentai")
            m_time.sleep.assert_called_once_with(5)
            assert not res
        elif 'text/html' in content_type and 'You are opening' in text:
            assert res
            m_random.randint.assert_called_once_with(10, 50)
            m_time.sleep.assert_called_once_with(m_random.randint.return_value)
        else:
            assert res


@pytest.mark.parametrize(
    'raise_side_effect, notif_bar_is_unrecognized, notif_bar_is_none',
    product([True, False], repeat=3)
)
def test_add_text_to_notif_bar(raise_side_effect, notif_bar_is_unrecognized, notif_bar_is_none):
    """test method."""
    raise_side_effect = True
    text = mock.Mock()
    with mock.patch('happypanda.ehen.app_constants') as m_ac:
        if raise_side_effect:
            m_ac.NOTIF_BAR.add_text.side_effect = AttributeError
        elif notif_bar_is_unrecognized:
            m_ac.NOTIF_BAR = ''
        elif notif_bar_is_none:
            m_ac.NOTIF_BAR = None
        from happypanda.ehen import EHen
        # run
        if notif_bar_is_unrecognized or raise_side_effect:
            with pytest.raises(NotImplementedError):
                EHen._add_text_to_notif_bar(text)
            return
        #
        EHen._add_text_to_notif_bar(text)
        # test
        m_ac.NOTIF_BAR.add_text.assert_called_once_with(text)


@pytest.mark.parametrize(
    'url, exp_res',
    [
        ('https://exhentai.org/g/1002386/6b0c35a2d0/', [1002386, '6b0c35a2d0']),
        ('https://exhentai.org/g/a1002386/1002386/', None),
        ('https://exhentai.org/g/1002386/1002386/', [1002386, '1002386']),
        ('', None),
    ]
)
def test_parse_url(url, exp_res):
    """test method."""
    from happypanda.ehen import EHen
    assert exp_res == EHen.parse_url(url=url)


@pytest.mark.parametrize(
    'lot_of_urls, response_raise_error, handle_error_result, raise_error_on_response, '
    'gid_list_is_none',
    product([True, False], repeat=5)
)
def test_get_metadata(
        lot_of_urls, response_raise_error, handle_error_result, raise_error_on_response,
        gid_list_is_none):
    """test method."""
    if lot_of_urls:
        list_of_urls = [mock.Mock()] * 26
    else:
        url = mock.Mock()
        list_of_urls = [url]
    #
    cookies = mock.Mock()
    response = mock.Mock()
    if raise_error_on_response:
        response.raise_for_status.side_effect = ValueError
    gid_list = mock.Mock() if not gid_list_is_none else None
    #
    dict_metadata = {}
    get_dict_metadata_func = mock.Mock(return_value=dict_metadata)
    get_gallery_id_list_from_urls_func = mock.Mock(return_value=gid_list)
    get_response_func = mock.Mock(return_value=response)
    begin_lock_func = mock.Mock()
    end_lock_func = mock.Mock()
    handle_error_func = mock.Mock(return_value=handle_error_result)
    from happypanda.ehen import EHen
    obj = EHen()
    obj._get_dict_metadata = get_dict_metadata_func
    obj._get_gallery_id_list_from_urls = get_gallery_id_list_from_urls_func
    obj._get_response = get_response_func
    obj.handle_error = handle_error_func
    obj.begin_lock = begin_lock_func
    obj.end_lock = end_lock_func
    # run
    if lot_of_urls:
        assert obj.get_metadata(list_of_urls=list_of_urls, cookies=cookies) is None
        return
    res = obj.get_metadata(list_of_urls=list_of_urls, cookies=cookies)
    # test
    get_dict_metadata_func.assert_called_once_with(list_of_urls=[url])
    get_gallery_id_list_from_urls_func.assert_called_once_with(list_of_urls=[url])
    if gid_list_is_none:
        assert res is None
        return
    begin_lock_func.assert_called_once_with()
    get_response_func.assert_called_once_with(
        cookies=cookies, payload={'method': 'gdata', 'gidlist': gid_list, 'namespace': 1})
    end_lock_func.assert_called_once_with()
    if not handle_error_result:
        assert res == 'error'
    elif raise_error_on_response:
        assert res is None
    else:
        response.raise_for_status.assert_called_once_with()
        assert res == (response.json.return_value, dict_metadata)


def test_get_gallery_id_list_from_urls():
    """test method."""
    url1 = mock.Mock()
    url2 = mock.Mock()
    list_of_urls = [url1, url2]
    parsed_url = mock.Mock()
    with mock.patch('happypanda.ehen.EHen.parse_url') as parse_url_func:
        parse_url_func.side_effect = [parsed_url, None]
        from happypanda.ehen import EHen
        res = EHen._get_gallery_id_list_from_urls(list_of_urls=list_of_urls)
        assert res == [parsed_url]
        parse_url_func.assert_has_calls([
            mock.call(url1.strip.return_value), mock.call(url2.strip.return_value)])


def test_get_gallery_id_list_with_single_url():
    """test method."""
    url = 'http://g.e-hentai.org/g/1004208/ee717823cd/'
    exp_res = [[1004208, 'ee717823cd']]
    from happypanda.ehen import EHen
    obj = EHen()
    res = obj._get_gallery_id_list_from_urls([url])
    assert exp_res == res


def test_get_dict_metadata():
    """get method."""
    url1 = mock.Mock()
    url2 = mock.Mock()
    list_of_urls = [url1, url2]
    parsed_url_part = mock.Mock()
    parsed_url = (parsed_url_part, None)
    with mock.patch('happypanda.ehen.EHen.parse_url') as parse_url_func:
        parse_url_func.side_effect = [parsed_url, None]
        from happypanda.ehen import EHen
        obj = EHen()
        res = obj._get_dict_metadata(list_of_urls=list_of_urls)
        assert res == {parsed_url_part: url1}
        parse_url_func.assert_has_calls([
            mock.call(url1.strip.return_value), mock.call(url2.strip.return_value)])


def test_get_dict_metadata_with_single_url():
    """test method."""
    url = "http://g.e-hentai.org/g/1004208/ee717823cd/"
    exp_res = {1004208: 'http://g.e-hentai.org/g/1004208/ee717823cd/'}
    from happypanda.ehen import EHen
    obj = EHen()
    res = obj._get_dict_metadata(list_of_urls=[url])
    assert res == exp_res


@pytest.mark.parametrize(
    "cookies, raise_error_on_post", product([None, mock.Mock()], [True, False])
)
def test_get_response(cookies, raise_error_on_post):
    """test method."""
    fix_error_on_catching_exception = False  # change this when fixed.
    payload = mock.Mock()
    e_url = mock.Mock()
    obj_headers = mock.Mock()
    obj_cookies = mock.Mock()
    end_lock_func = mock.Mock()
    with mock.patch('happypanda.ehen.EHen.check_cookie') as check_cookie_func, \
            mock.patch('happypanda.ehen.requests') as m_requests:
        from happypanda.ehen import EHen
        from happypanda.app_constants import MetadataFetchFail
        from requests import ConnectionError
        obj = EHen()
        obj.e_url = e_url
        obj.HEADERS = obj_headers
        obj.COOKIES = obj_cookies
        obj.end_lock = end_lock_func
        # run
        if raise_error_on_post and fix_error_on_catching_exception:
            m_requests.post.side_effect = ConnectionError
            try:
                obj._get_response(payload=payload, cookies=cookies)
            except MetadataFetchFail:
                # this part fail because error below
                pass
            # Error.
            # ValueError: Unexpected Error:
            # Type:<class 'TypeError'>
            # Error:catching classes that do not inherit from BaseException is not allowed
            end_lock_func.assert_called_once_with()
        else:
            res = obj._get_response(payload=payload, cookies=cookies)
            assert res == m_requests.post.return_value
        # test
        if not cookies:
            m_requests.post.assert_called_once_with(
                e_url, headers=obj_headers, json=payload, timeout=30)
        else:
            check_cookie_func.assert_called_once_with(cookies)
            m_requests.post.assert_called_once_with(
                e_url, headers=obj_headers, timeout=30, json=payload, cookies=obj_cookies)


@pytest.mark.parametrize(
    'g_dict, exp_res',
    [
        ({}, True),
        ({'error': None}, False),
    ]
)
def test_invalid_token_check(g_dict, exp_res):
    """test method."""
    from happypanda.ehen import EHen
    assert exp_res == EHen._invalid_token_check(g_dict)


@pytest.mark.parametrize(
    'text, exp_res',
    [('&amp; &lt; &quot; &#x27; &gt;', """& < " ' >""")]
)
def test_fix_titles(text, exp_res):
    """test method."""
    from happypanda.ehen import EHen
    assert exp_res == EHen._fix_titles(text)


def test_get_metadata_single_url():
    """test method."""
    url = 'http://g.e-hentai.org/g/1004208/ee717823cd/'
    exp_dict_metadata = {1004208: 'http://g.e-hentai.org/g/1004208/ee717823cd/'}
    json_response = {
        'gmetadata': [
            {
                'title':
                    '(COMIC1☆10) [Yokoshimanchi. (Ash Yokoshima)] Bon-nou Seven [English] '
                    '[Tigoris Translates]',
                'rating': '3.72',
                'title_jpn': '(COMIC1☆10) [横島んち。 (Ash横島)] ぼんのうせぶん [英訳]',
                'tags': [
                    'language:english', 'language:translated', 'group:yokoshimanchi.',
                    'artist:ash yokoshima', 'female:dark skin', 'female:sex toys'
                ],
                'uploader': 'Spideyguy',
                'filecount': '18',
                'thumb': 'http://ehgt.org/0f/69/'
                '0f69fb9ff5711cc99d72f4d1280b623c4e8a6a0c-6982739-2858-4019-jpg_l.jpg',
                'gid': 1004208,
                'filesize': 61517759,
                'token': 'ee717823cd',
                'archiver_key': '411459--0732e06cb1094aed375a39f6c4d4e67cef73bf62',
                'expunged': False,
                'posted': '1481250175',
                'torrentcount': '1',
                'category': 'Doujinshi'
            }
        ]
    }
    with mock.patch('happypanda.ehen.EHen._get_response') as m_gr:
        m_gr.return_value.json.return_value = json_response
        from happypanda.ehen import EHen
        obj = EHen()
        json_res, dict_metadata_res = obj.get_metadata(list_of_urls=[url])
        assert json_res == json_response
        assert dict_metadata_res == exp_dict_metadata
        m_gr.assert_has_calls([
            mock.call(cookies=None, payload={
                'method': 'gdata', 'gidlist': [[1004208, 'ee717823cd']], 'namespace': 1}),
            mock.call().raise_for_status(),
            mock.call().json()
        ], any_order=True)

"""test module."""
from unittest import mock


def test_get_metadata():
    """test method."""
    exp_res = {
        'category': 'Doujinshi',
        'filecount': '5',
        'tags': [
            'Categories:doujinshi',
            'Artists:pepe',
            'Languages:translated',
            'Languages:english',
            'Tags:incest',
            'Tags:blowjob',
            'Tags:sole female',
            'Tags:sole male',
            'Tags:sister',
        ],
        'title': "[Pepe] Ruuko-san no Asa | Ruuko-san's Morning [English] [#Based Anons]",
        'title_jpn': '[ぺぺ] ルー子さんの朝 [英訳]'
    }
    url = 'https://nhentai.net/g/184812/'

    def select_side_effect(arg):
        """browser select method side effect."""
        val = mock.Mock()
        if arg == 'h1':
            val.text = exp_res['title']
            return [val]
        elif arg == 'h2':
            val.text = exp_res['title_jpn']
            return [val]
            return [val]
        else:
            raise ValueError('Unknown input:{}'.format(arg))

    browser = mock.Mock()
    browser.select.side_effect = select_side_effect
    find_tags_func = mock.Mock(return_value=exp_res['tags'])
    ensure_browser_on_url_func = mock.Mock()
    from happypanda.nhen_manager import NhenManager
    obj = NhenManager()
    obj._browser = browser
    obj.ensure_browser_on_url = ensure_browser_on_url_func
    obj._find_tags = find_tags_func
    obj._get_filecount = mock.Mock(return_value=exp_res['filecount'])
    # run
    res = obj._get_metadata(g_url=url)
    # test
    assert sorted(res.pop('tags')) == sorted(exp_res.pop('tags'))
    assert res == exp_res


def test_get_first_image_data():
    """test method."""
    exp_res = {'ext': '.png', 'server_id': '1018135'}
    link_parts = ('184812', '1')
    browser = mock.Mock()
    browser.select.return_value = [{'src': '//i.nhentai.net/galleries/1018135/1.png'}]
    from happypanda.nhen_manager import NhenManager
    obj = NhenManager()
    obj._browser = browser
    # run
    res = obj._get_first_image_data(link_parts)
    # test
    assert exp_res == res


def test_get_filecount():
    """test method."""
    filecount = '5'
    tag = mock.Mock()
    tag.text = '{} pages'.format(filecount)
    html_soup = mock.Mock()
    html_soup.select.return_value = [tag]
    from happypanda.nhen_manager import NhenManager
    res = NhenManager._get_filecount(html_soup)
    assert res == filecount


def test_get_tag_dict():
    """test method."""
    tag1 = mock.Mock()
    tag1.text = 'tag1 (10)'
    tag2 = mock.Mock()
    tag2.text = 'tag2 (10)'

    value_divs = mock.Mock()
    value_divs.contents = [tag1, tag2]

    tag_div = mock.Mock()
    tag_div.contents = ('category', value_divs)

    html_soup = mock.Mock()
    html_soup.select.return_value = [tag_div]
    from happypanda.nhen_manager import NhenManager
    # run
    res = NhenManager._get_tag_dict(html_soup)
    # test
    assert res == {'category': ['tag1', 'tag2']}


def test_find_tags():
    """test method."""
    tag_dict = {'category': ['tag1', 'tag2']}
    exp_res = ['category:tag1', 'category:tag2']
    html_soup = mock.Mock()
    from happypanda.nhen_manager import NhenManager
    NhenManager._get_tag_dict = mock.Mock(return_value=tag_dict)
    # run
    res = NhenManager._find_tags(html_soup)
    # test
    assert res == exp_res


def test_get_category():
    """test method."""
    tags = ['Categories:doujinshi']
    exp_res = 'Doujinshi'
    from happypanda.nhen_manager import NhenManager
    # run
    res = NhenManager._get_category(tags)
    # test
    assert res == exp_res


def test_get_dl_urls():
    """test method."""
    g_url = mock.Mock()
    link = mock.Mock()
    link_parts = [(mock.Mock(), mock.Mock())]
    browser = mock.Mock()
    browser.select.return_value = [{'href': link}]
    image1_data = {'ext': mock.Mock(), 'server_id': mock.Mock()}
    with mock.patch('happypanda.nhen_manager.AsmManager') as m_asm_manager:
        from happypanda.nhen_manager import NhenManager
        m_asm_manager._split_href_links_to_parts.return_value = link_parts
        exp_res = [
            "https://i.nhentai.net/galleries/{}/{}{}".format(
                image1_data['server_id'], link_parts[0][1], image1_data['ext']
            )
        ]
        obj = NhenManager()
        obj._browser = browser
        obj._get_first_image_data = mock.Mock(return_value=image1_data)
        res = obj._get_dl_urls(g_url)
        assert res == exp_res


def test_from_gallery_url():
    """test method."""
    g_url = mock.Mock()
    thumb_url = mock.Mock()
    title = mock.Mock()
    h_item = mock.Mock()

    browser = mock.Mock()
    browser.select.return_value = [{'src': thumb_url}]
    dict_metadata = {'title': title}
    with mock.patch('happypanda.nhen_manager.HenItem') as m_hi, \
            mock.patch('happypanda.nhen_manager.AsmManager') as m_asm_manager, \
            mock.patch('happypanda.nhen_manager.DownloaderObject'):
        m_hi.return_value = h_item
        from happypanda.nhen_manager import NhenManager
        obj = NhenManager()
        obj._browser = browser
        obj._get_dl_urls = mock.Mock()
        obj._get_metadata = mock.Mock()
        obj._get_metadata.return_value = dict_metadata
        # run
        res = obj.from_gallery_url(g_url)
        # test
        assert res == m_asm_manager._set_ehen_metadata.return_value

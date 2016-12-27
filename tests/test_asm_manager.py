"""test module."""
from itertools import product
from unittest import mock

import pytest
from bs4 import BeautifulSoup


def test_get_server_id():
    """test method."""
    link_parts = ('12623', 1)
    exp_res = '001'
    browser = mock.Mock()
    browser.select.return_value = [{'src': '//images.asmhentai.com/001/12623/1.jpg'}]
    from version.asm_manager import AsmManager
    obj = AsmManager()
    obj._browser = browser
    res = obj._get_server_id(link_parts=link_parts)
    assert res == exp_res


def test_get_dl_urls():
    """test method."""
    url = 'http://asmhentai.com/g/168260/'
    subset_list = [
        'http://images.asmhentai.com/006/168260/1.jpg',
        'http://images.asmhentai.com/006/168260/2.jpg',
        'http://images.asmhentai.com/006/168260/22.jpg',
    ]
    select_retval = [
        {'href': "/gallery/168260/1/"},
        {'href': "/gallery/168260/2/"},
        {'href': "/gallery/168260/22/"},
    ]
    browser = mock.Mock()
    browser.select.return_value = select_retval
    from version.asm_manager import AsmManager
    obj = AsmManager()
    browser.select.return_value = select_retval
    obj._browser = browser
    obj._get_server_id = mock.Mock()
    obj._get_server_id.return_value = ('006')
    # run
    res = obj._get_dl_urls(g_url=url)
    # test
    assert set(subset_list).issubset(res)


def test_get_metadata():
    """test method."""
    exp_res = {
        'category': 'doujinshi',
        'filecount': '23',
        'tags': [
            'Parody:granblue fantasy', 'Tags:stockings', 'Tags:sole female', 'Tags:sole male',
            'Characters:zeta', 'Characters:gran', 'Artists:nokin', 'Language:japanese',
            'Category:doujinshi'
        ],
        'title': '(SHT2016 Haru) '
        '[Hizadati Zekkouchou (Nokin)] Zeta to Issho de Yokatta ne (Granblue Fantasy)',
        'title_jpn': '(SHT2016春) '
        '[ひざだち絶好調 (のきん)] ゼタと一緒でよかったね (グランブルーファンタジー)'
    }
    url = 'http://asmhentai.com/g/154801/'

    def select_side_effect(arg):
        """browser select method side effect."""
        val = mock.Mock()
        if arg == '.info h1':
            val.text = exp_res['title']
            return [val]
        elif arg == '.info h2':
            val.text = exp_res['title_jpn']
            return [val]
        elif arg == '.pages':
            val.text = 'Pages:{}'.format(exp_res['filecount'])
            return [val]
        else:
            raise ValueError('Unknown input:{}'.format(arg))

    browser = mock.Mock()
    browser.select.side_effect = select_side_effect
    find_tags_func = mock.Mock(return_value=exp_res['tags'])
    ensure_browser_on_url_func = mock.Mock()
    from version.asm_manager import AsmManager
    obj = AsmManager()
    obj._browser = browser
    obj.ensure_browser_on_url = ensure_browser_on_url_func
    obj._find_tags = find_tags_func
    # run
    res = obj._get_metadata(g_url=url)
    # test
    assert res == exp_res


def test_find_tags():
    html_txt = \
        """
        <div class="tags">
        <h3>Tags:</h3>
        <div class="tag_list">
        <a href="/tags/name/sole-female/"><span class="badge tag">sole female</span></a>
        <a href="/tags/name/stockings/"><span class="badge tag">stockings</span></a>
        </div>
        </div>
        """
    exp_res = ['Tags:sole female', 'Tags:stockings']
    html_soup = BeautifulSoup(html_txt)
    browser = mock.Mock()
    browser.select.return_value = html_soup.select('.tags h3')
    from version.asm_manager import AsmManager
    res = AsmManager._find_tags(browser)
    assert res == exp_res


def test_from_gallery_url():
    """test method."""
    url = 'http://asmhentai.com/g/154801/'
    exp_download_type = 2
    title = mock.Mock()
    m_metadata = {'title': title}
    browser = mock.Mock()
    thumb_url = '//www.example.com/thumb.jpg'
    browser.select.return_value = [{'src': thumb_url}]
    set_metadata_func = mock.Mock()
    set_ehen_metadata_func = mock.Mock()
    with mock.patch('version.asm_manager.HenItem') as m_hi, \
            mock.patch('version.asm_manager.DownloaderObject') as m_do:
        from version.asm_manager import AsmManager
        obj = AsmManager()
        obj._browser = browser
        obj._get_metadata = mock.Mock(return_value=m_metadata)
        obj._get_dl_urls = mock.Mock()
        obj._set_metadata = set_metadata_func
        obj._set_ehen_metadata = set_ehen_metadata_func
        # run
        res = obj.from_gallery_url(g_url=url)
        # test
        assert res == set_ehen_metadata_func.return_value
        assert m_hi.return_value.download_type == exp_download_type
        assert m_hi.return_value.gallery_url == url
        assert m_hi.return_value.thumb_url == 'http:' + thumb_url
        m_hi.return_value.fetch_thumb.assert_called_once_with()
        assert m_hi.return_value.gallery_name == title
        assert m_hi.return_value.download_url == obj._get_dl_urls.return_value
        m_do.add_to_queue.assert_called_once_with(
            set_ehen_metadata_func.return_value, browser.session)
        #
        m_hi.assert_has_calls([
            mock.call(browser.session),
            mock.call().fetch_thumb()
        ])


@pytest.mark.parametrize(
    'key, catg_val',
    product(
        ['title_jpn', "title", "filecount", 'tags'],
        [None, 'manga', 'doujin']
    )
)
def test_set_metadata(key, catg_val):
    """test method."""
    h_item = mock.Mock()
    value = mock.Mock()
    dict_metadata = {}
    dict_metadata[key] = value
    dict_metadata['category'] = catg_val
    from version.asm_manager import AsmManager
    res = AsmManager._set_metadata(h_item=h_item, dict_metadata=dict_metadata)
    assert res == h_item
    h_item_calls = []
    h_item_calls.append(mock.call.update_metadata(key=key, value=value))
    if not catg_val:
        pass
    elif catg_val.lower() == 'manga':
        h_item_calls.append(mock.call.update_metadata(key='category', value='Manga'))
    elif catg_val.lower() == 'doujinshi':
        h_item_calls.append(mock.call.update_metadata(key='category', value='Doujinshi'))
    h_item.assert_has_calls(h_item_calls)


@pytest.mark.parametrize(
    'old_data_tags, new_data_tags',
    [
        ({}, {}),
        (['ns1:val1', 'ns1:val2'], {'ns1': ['val1', 'val2']}),
        (['ns1:val1:val1_part2', 'ns1:val2'], {'ns1': ['val1:val1_part2', 'val2']}),
        (['ns1:val1', 'ns2:val2'], {'ns1': ['val1'], 'ns2': ['val2']}),
    ]
)
def test_set_ehen_metadata(old_data_tags, new_data_tags):
    """test method."""
    h_item = mock.Mock()
    h_item.metadata = {}
    dict_metadata = {
        'category': mock.Mock(),
        'title_jpn': mock.Mock(),
        'title': mock.Mock(),
        'tags': old_data_tags,
    }
    exp_res = {
        'title': {
            'jpn': dict_metadata['title_jpn'],
            'def': dict_metadata['title'],

        },
        'tags': new_data_tags,
        'type': dict_metadata['category'],
        'pub_date': ''
    }
    from version.asm_manager import AsmManager
    res = AsmManager._set_ehen_metadata(h_item=h_item, dict_metadata=dict_metadata)
    assert res == h_item
    res == exp_res

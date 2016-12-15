"""test module."""
from unittest import mock

import pytest
from bs4 import BeautifulSoup

not_finished = pytest.mark.skip(reason='Not finished')


def test_get_dl_urls():
    """test method."""
    url = 'http://asmhentai.com/g/168260/'
    subset_list = [
        'https://images.asmhentai.com/006/168260/1.jpg',
        'https://images.asmhentai.com/006/168260/2.jpg',
        'https://images.asmhentai.com/006/168260/22.jpg',
    ]
    select_retval = [
        {'href': "/gallery/168260/1/"},
        {'href': "/gallery/168260/2/"},
        {'href': "/gallery/168260/22/"},
    ]
    browser = mock.Mock()
    browser.select.return_value = select_retval
    from version.asmhen_manager import AsmManager
    obj = AsmManager()
    browser.select.return_value = select_retval
    obj._browser = browser
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
    from version.asmhen_manager import AsmManager
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
    from version.asmhen_manager import AsmManager
    res = AsmManager._find_tags(browser)
    assert res == exp_res


def test_from_gallery_url():
    """test method."""
    url = 'http://asmhentai.com/g/154801/'
    title = mock.Mock()
    m_metadata = {'title': title}
    browser = mock.Mock()
    thumb_url = '//www.example.com/thumb.jpg'
    browser.select.return_value = [{'src': thumb_url}]
    with mock.patch('version.asmhen_manager.HenItem') as m_hi, \
            mock.patch('version.asmhen_manager.DownloaderObject') as m_do:
        from version.asmhen_manager import AsmManager, DOWNLOAD_TYPE_OTHER
        obj = AsmManager()
        obj._browser = browser
        obj._get_metadata = mock.Mock(return_value=m_metadata)
        obj._get_dl_urls = mock.Mock()
        # run
        res = obj.from_gallery_url(g_url=url)
        # test
        assert res.download_type == DOWNLOAD_TYPE_OTHER
        assert res.gallery_url == url
        assert res.thumb_url == 'https' + thumb_url
        res.fetch_thumb.assert_called_once_with()
        assert res.gallery_name == title
        assert res.download_url == obj._get_dl_urls.return_value
        m_do.add_to_queue.assert_called_once_with(res, browser.session)
        #
        m_hi.assert_has_calls([
            mock.call(browser.session),
            mock.call().fetch_thumb()
        ])

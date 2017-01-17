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
    from version.nhen_manager import NhenManager
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
    from version.nhen_manager import NhenManager
    obj = NhenManager()
    obj._browser = browser
    # run
    res = obj._get_first_image_data(link_parts)
    # test
    assert exp_res == res

"""test module."""
from unittest import mock

import pytest


@pytest.mark.parametrize('raise_decode_error', [True, False])
def test_get_json_response(raise_decode_error):
    """test method."""
    response = mock.Mock()
    from json import JSONDecodeError
    if raise_decode_error:
        response.json.side_effect = JSONDecodeError('', '', 0)
    from happypanda.chaika_hen import ChaikaHen
    # run
    res = ChaikaHen._get_json_response(response=response)
    # test
    response.json.assert_called_once_with()
    if not raise_decode_error:
        assert res == response.json.return_value
    else:
        assert res is None


def test_get_metadata_single_url():
    """teset method."""
    response_json_retval = {
        'category': 'Manga',
        'download': '/archive/19945/download/',
        'expunged': 'False',
        'filecount': 4,
        'filesize': 1348777,
        'fjord': False,
        'gallery': 16873,
        'posted': 1200956086,
        'rating': 4.73,
        'tags': [
            'language:english', 'language:translated', 'full_color', 'female:small_breasts',
            'reclass:manga', 'artist:naruko_hanaharu', 'female:schoolgirl_uniform'
        ],
        'title': '[Naruko Hanaharu] Dekoboko - Roughness [English]',
        'title_jpn': '[鳴子ハナハル] でこぼこ [英訳]',
        'uploader': 'RenRenRen'
    }
    url = 'https://panda.chaika.moe/archive/19945/'
    #
    exp_data = [{
        'category': 'Manga',
        'download': '/archive/19945/download/',
        'expunged': 'False',
        'filecount': 4,
        'filesize': 1348777,
        'fjord': False,
        'gallery': 16873,
        'gid': 1,
        'posted': 1200956086,
        'rating': 4.73,
        'tags': [
            'language:english', 'language:translated', 'full_color', 'female:small_breasts',
            'reclass:manga', 'artist:naruko_hanaharu', 'female:schoolgirl_uniform'
        ],
        'title': '[Naruko Hanaharu] Dekoboko - Roughness [English]',
        'title_jpn': '[鳴子ハナハル] でこぼこ [英訳]',
        'uploader': 'RenRenRen'
    }]
    exp_g_id_data = {1: 'https://panda.chaika.moe/archive/19945/'}
    #
    with mock.patch('happypanda.chaika_hen.requests') as m_req:
        m_req.get.return_value.json.return_value = response_json_retval
        from happypanda.chaika_hen import ChaikaHen
        obj = ChaikaHen()
        # ru
        data, g_id_data = obj.get_metadata([url])
        # test
        assert len(exp_data) == len(data)
        assert exp_data[0] == data[0]
        assert exp_g_id_data == g_id_data

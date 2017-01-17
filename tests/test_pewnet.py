"""test module."""
from itertools import product
from unittest import mock

import pytest


@pytest.mark.parametrize(
    'url, check_result',
    product(
        [
            'https://exhentai.org/g/a1002386/1002386/',
            'https://panda.chaika.moe/archive/19970/',
            'http://g.e-hentai.org/g/1003511/5f82a225fb/',
            "http://asmhentai.com/g/168735/",
            'http://example.com',
            'https://nhentai.net/g/184905/',
        ],
        [True, False]
    )
)
def test_website_validator(url, check_result):
    """test func."""
    with mock.patch('version.pewnet.HenManager') as m_hm, \
            mock.patch('version.pewnet.ExHenManager') as m_ehm, \
            mock.patch('version.pewnet.ChaikaManager') as m_cm, \
            mock.patch('version.pewnet.AsmManager') as m_am, \
            mock.patch('version.pewnet.NhenManager') as m_nm, \
            mock.patch('version.pewnet.settings') as m_settings:
        from version.pewnet import website_validator
        from version import app_constants
        m_settings.ExProperties.return_value.check.return_value = check_result
        exp_res_packs = [
            ('g.e-hentai', m_hm.return_value),
            ('exhentai', m_ehm.return_value),
            ('panda.chaika.moe', m_cm.return_value),
            ('asmhentai', m_am.return_value),
            ('nhentai.net', m_nm.return_value),
        ]
        # test
        if not all(x[0] in url for x in exp_res_packs):
            try:
                website_validator(url)
            except app_constants.WrongURL:
                pass
            return

        res = website_validator(url)
        # test
        # exception for exhentai which depend on exprops settings
        if 'exhentai' in url and not check_result:
            assert res is None
            return
        for keyword, exp_res in exp_res_packs:
            if keyword in res:
                assert res == exp_res

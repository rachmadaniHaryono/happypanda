"""test module."""
from itertools import product
from unittest import mock

import pytest


def test_get_qdatetime_from_string():
    """test func."""
    value = mock.Mock()
    with mock.patch('happypanda.gallery_model.QDateTime') as m_qdt:
        from happypanda.gallery_model import GalleryModel
        # run
        res = GalleryModel._get_qdatetime_from_string(value=value)
        # test
        m_qdt.fromString.assert_called_once_with('{}'.format(value), 'yyyy-MM-dd HH:mm:ss')
        assert res == m_qdt.fromString.return_value


@pytest.mark.parametrize(
    'pub_date_const, date_added_const',
    product([True, False], repeat=2)
)
def test_add_tips_and_bold_for_date_attr(pub_date_const, date_added_const):
    """test method."""
    add_bold = []
    add_tips = []
    current_gallery = mock.Mock()
    current_gallery.pub_date = "word1 word2"
    current_gallery.date_added = "word3 word4"
    with mock.patch('happypanda.gallery_model.app_constants') as m_ac:
        #
        m_ac.TOOLTIP_PUB_DATE = pub_date_const
        m_ac.TOOLTIP_DATE_ADDED = date_added_const
        #
        from happypanda.gallery_model import GalleryModel
        res = GalleryModel._add_tips_and_bold_for_date_attr(
            add_bold=add_bold, add_tips=add_tips, current_gallery=current_gallery)
        exp_res0 = []
        exp_res1 = []
        if pub_date_const:
            exp_res0.append('<b>Publication Date:</b>')
            exp_res1.append('word1')
        if date_added_const:
            exp_res0.append('<b>Date added:</b>')
            exp_res1.append('word3')
        assert res[0] == exp_res0
        assert res[1] == exp_res1

"""test module."""
from itertools import product
from unittest import mock

import pytest


@pytest.mark.parametrize(
    'val_pack, find_combobox_match_result',
    product(
        [
            ('language', 'lang_box', 'G_DEF_LANGUAGE', 1),
            ('type', 'type_box', 'G_DEF_TYPE', 0),
            ('status', 'status_box', 'G_DEF_STATUS', 0),
        ],
        [True, False]
    )
)
def test_set_gallery_specific_setting(val_pack, find_combobox_match_result):
    """test method."""
    attr, cls_attr, constant_attr, def_val = val_pack
    #
    attr_val = mock.Mock()
    m_g = mock.Mock()
    setattr(m_g, attr, attr_val)
    gallery = [m_g]
    m_cls = mock.Mock()
    from version.gallery_dialog_widget import _set_gallery_specific_setting
    from version.gallery_dialog_widget import app_constants
    m_cls._find_combobox_match.return_value = find_combobox_match_result
    # run
    _set_gallery_specific_setting(
        cls=m_cls,
        attr=attr, cls_attr=cls_attr, gallery=gallery, def_val=def_val,
        constant_attr=constant_attr
    )
    # test
    # _find_combobox_match function first call and second call
    getattr(m_cls, cls_attr).g_check.setChecked.assert_called_once_with(True)
    fcm_func_1call = getattr(m_cls, cls_attr), getattr(gallery[0], attr), def_val
    fcm_func_2call = getattr(m_cls, cls_attr), getattr(app_constants, constant_attr), def_val
    if find_combobox_match_result:
        m_cls._find_combobox_match.assert_called_once_with(*fcm_func_1call)
    else:
        m_cls._find_combobox_match.assert_has_calls([
            mock.call(*fcm_func_1call),
            mock.call(*fcm_func_2call)
        ])


def test_set_gallery_constant_setting():
    """test func."""
    widget = mock.Mock()
    widget_attr = mock.Mock()
    gallery_attr = mock.Mock()
    constant_attr = mock.Mock()
    def_val = mock.Mock()
    find_combobox_match_result = True
    widget._find_combobox_match.return_value = find_combobox_match_result
    fcm_func_1call = widget_attr, gallery_attr, def_val
    from version.gallery_dialog_widget import _set_gallery_constant_setting
    # run
    _set_gallery_constant_setting(
        widget, widget_attr, gallery_attr, constant_attr, def_val)
    # test
    if not find_combobox_match_result:
        widget._find_combobox_match.assert_has_calls([
            mock.call(*fcm_func_1call),
            mock.call(widget_attr, constant_attr, def_val)
        ])
    else:
        widget._find_combobox_match.assert_called_once_with(*fcm_func_1call)


def test_change_link():
    """test method."""
    pre_link = mock.Mock()
    main_link = mock.Mock()
    text = mock.Mock()
    link_btn1 = mock.Mock()
    link_btn2 = mock.Mock()
    from version.gallery_dialog_widget import GalleryDialogWidget
    # run
    GalleryDialogWidget._change_link(
        pre_link_item=pre_link,
        main_link_item=main_link, text=text,
        after_link_items=[link_btn1, link_btn2]
    )
    # test
    pre_link.hide.assert_called_once_with()
    main_link.show.assert_called_once_with()
    main_link.setText.assert_called_once_with(text)
    link_btn1.hide.assert_called_once_with()
    link_btn2.show.assert_called_once_with()


@pytest.mark.parametrize(
    'mode', ['none_given', 'both_given']
)
def test_set_form_raises_error(mode):
    """test method when raise error."""
    if mode not in ('none_given', 'both_given'):
        raise ValueError('Unknown mode.')
    exp_error = ValueError
    editor, box = (None, None) if mode == 'none_given' else (mock.Mock(), mock.Mock())
    from version.gallery_dialog_widget import GalleryDialogWidget
    # run
    with pytest.raises(exp_error):
        GalleryDialogWidget._set_form(
            gallery=mock.Mock(), attr=mock.Mock(), editor=editor, box=box)


@pytest.mark.parametrize(
    'mode, attr',
    product(
        ['box_given', 'editor_given'],
        ['name', "tags"],
    )
)
def test_set_form(mode, attr):
    """test method."""
    if mode not in ('box_given', 'editor_given'):
        raise ValueError('Unknown mode.')
    box, editor = (mock.Mock(), None) if mode == 'box_given' else (None, mock.Mock())
    with mock.patch('version.gallery_dialog_widget.tag_to_string') as m_tts:
        from version.gallery_dialog_widget import GalleryDialogWidget
        #
        g = mock.Mock()
        g_attr = getattr(g, attr)
        arg = g_attr if attr != 'tags' else m_tts(g_attr)
        gallery = [g]
        # run
        GalleryDialogWidget._set_form(gallery=gallery, attr=attr, editor=editor, box=box)
        if mode == 'box_given':
            form = box
            form_1call = mock.call.setValue(arg)
        elif mode == 'editor_given':
            form = editor
            form_1call = mock.call.setText(arg)
        form.assert_has_calls(
            [form_1call, mock.call.g_check.setChecked(True)]
        )


@pytest.mark.parametrize('raise_index_error', [False, True])
def test_get_gallery_date(raise_index_error):
    """test method."""
    m_time = mock.Mock()
    if raise_index_error:
        g_pub_date = [mock.Mock()]
    else:
        g_pub_date = [mock.Mock(), m_time]
    with mock.patch('version.gallery_dialog_widget.datetime') as m_dt:
        from version.gallery_dialog_widget import GalleryDialogWidget
        res = GalleryDialogWidget._get_gallery_date(g_pub_date=g_pub_date)
        if raise_index_error:
            m_dt.assert_not_called()
            assert res is None
        else:
            m_dt.assert_has_calls([
                mock.call.strptime(m_time, '%H:%M:%S'),
                mock.call.strptime().time()
            ])
            assert res == m_dt.strptime.return_value.time.return_value

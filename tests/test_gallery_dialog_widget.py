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
def test_set_gallery_specific_setting(val_pack, find_combobox_match_result, qtbot):
    """test method."""
    attr, cls_attr, constant_attr, def_val = val_pack
    #
    attr_val = mock.Mock()
    m_g = mock.Mock()
    setattr(m_g, attr, attr_val)
    gallery = [m_g]
    from version.gallery_dialog_widget import GalleryDialogWidget
    from version.gallery_dialog_widget import app_constants
    obj = GalleryDialogWidget(parent=None)
    obj._find_combobox_match = mock.Mock(return_value=find_combobox_match_result)
    # run
    obj._set_gallery_specific_setting(
        attr=attr, cls_attr=cls_attr, gallery=gallery, def_val=def_val,
        constant_attr=constant_attr
    )
    # test
    # _find_combobox_match function first call and second call
    fcm_func_1call = getattr(obj, cls_attr), getattr(gallery[0], attr), def_val
    fcm_func_2call = getattr(obj, cls_attr), getattr(app_constants, constant_attr), def_val
    if find_combobox_match_result:
        obj._find_combobox_match.assert_called_once_with(*fcm_func_1call)
    else:
        obj._find_combobox_match.assert_has_calls([
            mock.call(*fcm_func_1call),
            mock.call(*fcm_func_2call)
        ])

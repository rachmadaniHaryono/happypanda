"""test module."""
import pytest


@pytest.mark.parametrize(
    'margin_offset, desktop, exp_res',
    [
        (-2, -1, (True, False)),
        (-2, 0, (True, True)),
        (-1, 1, (False, True)),
        (-1, 0, (False, False)),
        (0, 0, (False, False)),
        (0, 1, (False, False)),
    ]
)
def test_calculate_sides(margin_offset, desktop, exp_res):
    """test method."""
    hw = 2
    middle = 0
    from happypanda.gallery_meta_window import GalleryMetaWindow
    res = GalleryMetaWindow._calculate_sides(
        middle=middle, hw=hw, margin_offset=margin_offset, desktop=desktop)
    assert res == exp_res

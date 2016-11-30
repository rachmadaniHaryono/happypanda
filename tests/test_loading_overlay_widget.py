"""test mdoule."""
import pytest


@pytest.mark.parametrize(
    'x, i, exp_res',
    [
        (2, 0, -9.0),
        (2, 1, 16.98),
        (2, 2, 16.98),
        (2, 3, -9.0),
        (2, 4, -34.98),
        (2, 5, -34.98),
    ]
)
def test_get_offset(x, i, exp_res):
    """test method."""
    from version.loading_overlay_widget import LoadingOverlayWidget
    res = LoadingOverlayWidget._get_offset(x, i)
    assert "{:.2f}".format(res) == "{:.2f}".format(exp_res)

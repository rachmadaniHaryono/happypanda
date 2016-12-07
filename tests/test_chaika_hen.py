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
    from version.chaika_hen import ChaikaHen
    # run
    res = ChaikaHen._get_json_response(response=response)
    # test
    response.json.assert_called_once_with()
    if not raise_decode_error:
        assert res == response.json.return_value
    else:
        assert res is None

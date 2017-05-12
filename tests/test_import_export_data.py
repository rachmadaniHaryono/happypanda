"""test module."""
from itertools import product
from unittest import mock

import pytest


@pytest.mark.parametrize(
    'cond, attr_name',
    product([True, False], ['last_read', 'pub_date'])
)
def test_get_date(cond, attr_name):
    """test method."""
    value = mock.Mock()
    gallery = mock.Mock()
    gallery_val = mock.Mock()
    setattr(gallery, attr_name, gallery_val)
    if cond:
        structure = {attr_name: value}
    else:
        structure = {attr_name: None}
    with mock.patch('happypanda.import_export_data.datetime') as m_dt:
        from happypanda.import_export_data import ImportExportData
        res = ImportExportData._get_date(attr_name=attr_name, structure=structure, gallery=gallery)
        if cond:
            m_dt.datetime.strptime.assert_called_once_with(value, "%Y-%m-%d %H:%M:%S")
            assert res == m_dt.datetime.strptime.return_value
        else:
            m_dt.assert_not_called()
            assert res == gallery_val

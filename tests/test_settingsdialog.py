"""test module."""
from unittest import mock

import pytest


@pytest.mark.parametrize('color_checker_result', [True, False])
def test_set_setting_with_color_check(color_checker_result):
    """test method."""
    color_check_func = mock.Mock(return_value=color_checker_result)
    #
    attr = mock.Mock()
    const = mock.Mock()
    key = mock.Mock()
    #
    with mock.patch('happypanda.settingsdialog.settings') as m_settings:
        from happypanda.settingsdialog import SettingsDialog
        SettingsDialog.color_checker = color_check_func
        # run
        SettingsDialog._set_setting_with_color_check(
            attr=attr, const=const, key=key, color_checker=color_check_func)
        # test
        attr.text.assert_called_once_with()
        if color_checker_result:
            m_settings.set.assert_called_once_with(
                key=key, section='Visual', value=attr.text.return_value)
        else:
            m_settings.set.assert_not_called()

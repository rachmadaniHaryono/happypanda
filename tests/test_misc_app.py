"""test module."""
import itertools
from unittest import mock

import pytest


m_obj = mock.Mock()


@pytest.mark.parametrize(
    'ext_viewer_args',
    [None, '{file}']
)
def test_invoke_first_time_level(ext_viewer_args):
    """test func."""
    with mock.patch('version.misc_app.app_constants') as m_app_constants, \
            mock.patch('version.misc_app.settings') as m_settings:
        # pre run
        from version import misc_app
        m_app_constants.EXTERNAL_VIEWER_ARGS = ext_viewer_args
        # run
        misc_app.invoke_first_time_level()
        # test
        assert m_app_constants.INTERNAL_LEVEL == 7
        if ext_viewer_args is None:
            assert m_app_constants.EXTERNAL_VIEWER_ARGS is None
            assert not m_settings.mock_calls
        elif ext_viewer_args == '{file}':
            assert m_app_constants.EXTERNAL_VIEWER_ARGS == '{$file}'
            m_settings.assert_has_calls([
                mock.call.set('{$file}', 'Advanced', 'external viewer args'),
                mock.call.save()
            ])


@pytest.mark.parametrize(
    'first_time_level, internal_level',
    [(0, 0), (0, 1)]
)
def test_normalize_first_time(first_time_level, internal_level):
    """test func."""
    with mock.patch('version.misc_app.app_constants') as m_app_constants, \
            mock.patch('version.misc_app.settings') as m_settings:
        # pre run
        from version import misc_app
        m_app_constants.FIRST_TIME_LEVEL = first_time_level
        m_app_constants.INTERNAL_LEVEL = internal_level
        # run
        misc_app.normalize_first_time()
        # test
        if first_time_level != internal_level:
            m_settings.assert_has_calls([
                mock.call.set(m_app_constants.INTERNAL_LEVEL, 'Application', 'first time level'),
                mock.call.save()
            ])
        else:
            m_settings.set.assert_called_once_with(m_app_constants.vs, 'Application', 'version')


@pytest.mark.parametrize(
    'update_version, vs_constant',
    [(0, 0), (0, 1)],
)
def test_get_finished_startup_update_text(update_version, vs_constant):
    """test func."""
    with mock.patch('version.misc_app.app_constants') as m_app_constants, \
            mock.patch('version.misc_app.random') as m_random:
        # pre run
        from version import misc_app
        m_app_constants.UPDATE_VERSION = update_version
        m_app_constants.vs = vs_constant
        # run
        res = misc_app.get_finished_startup_update_text()
        # test
        if update_version != vs_constant:
            assert res == (
                "Happypanda has been updated!",
                "Don't forget to check out what's new in this version "
                "<a href='https://github.com/Pewpews/happypanda/blob/master/CHANGELOG.md'>"
                "by clicking here!</a>"
            )
        else:
            hello_words = [
                "Hello!", "Hi!", "Onii-chan!", "Senpai!", "Hisashiburi!", "Welcome!",
                "Okaerinasai!", "Welcome back!", "Hajimemashite!"]
            m_random.choice.assert_called_once_with(hello_words)
            assert res == (
                "{}".format(m_random.choice.return_value),
                "Please don't hesitate to report any bugs you find.",
                10
            )


def test_set_search_case():
    """test func."""
    m_input = mock.Mock()
    with mock.patch('version.misc_app.app_constants') as m_app_constants, \
            mock.patch('version.misc_app.settings') as m_settings:
        # pre run
        from version import misc_app
        # run
        misc_app.set_search_case(m_input)
        # test
        m_app_constants.GALLERY_SEARCH_CASE == m_input
        m_settings.assert_has_calls([
            mock.call.set(
                m_app_constants.GALLERY_SEARCH_CASE,
                'Application',
                'gallery search case'),
            mock.call.save()
        ])


@pytest.mark.parametrize('raise_error', [False, True])
def test_clean_up_temp_dir(raise_error):
    """test func."""
    with mock.patch('version.misc_app.cleanup_dir') as m_cd:
        from version import misc_app
        if raise_error:
            m_cd.side_effect = ValueError
        # run
        misc_app.clean_up_temp_dir()
        # test
        m_cd.assert_called_once_with(path='temp')


@pytest.mark.parametrize('raise_error', [False, True])
def test_clean_up_db(raise_error):
    """test func."""
    with mock.patch('version.misc_app.log_i') as m_log_i, \
            mock.patch('version.misc_app.gallerydb') as m_gallerydb:
        # pre run
        from version import misc_app
        if raise_error:
            m_gallerydb.GalleryDB.analyze.side_effect = ValueError
        # run
        misc_app.clean_up_db()
        # test
        if not raise_error:
            m_log_i.assert_has_calls([
                mock.call('Analyzing database...'),
                mock.call('Closing database...')
            ])
            m_gallerydb.assert_has_calls([
                mock.call.GalleryDB.analyze(),
                mock.call.GalleryDB.close()
            ])
        else:
            m_log_i.assert_called_once_with('Analyzing database...')
            m_gallerydb.GalleryDB.analyze.assert_called_once_with()


@pytest.mark.parametrize(
    'm_popup_mode, m_menu, m_tooltip, m_text, m_icon, m_fixed_width, m_clicked_connect_func',
    itertools.product([m_obj, None], repeat=7)
)
def test_set_tool_button_attribute(
    m_popup_mode,
    m_menu,
    m_tooltip,
    m_text,
    m_icon,
    m_fixed_width,
    m_clicked_connect_func
):
    """test func."""
    m_tool_button = mock.Mock()
    m_shortcut = mock.Mock()
    # pre run
    from version import misc_app
    # run
    res = misc_app.set_tool_button_attribute(
        m_tool_button,
        m_shortcut,
        m_popup_mode,
        m_menu,
        m_tooltip,
        m_text,
        m_icon,
        m_fixed_width,
        m_clicked_connect_func
    )
    assert res == m_tool_button
    func_calls = [mock.call.setShortcut(m_shortcut)]
    if m_text is not None:
        func_calls.append(mock.call.setText(m_text))
    if m_popup_mode is not None:
        func_calls.append(mock.call.setPopupMode(m_popup_mode))
    if m_tooltip is not None:
        func_calls.append(mock.call.setToolTip(m_tooltip))
    if m_icon is not None:
        func_calls.append(mock.call.setIcon(m_icon))
    if m_fixed_width is not None:
        func_calls.append(mock.call.setFixedWidth(m_fixed_width))
    if m_clicked_connect_func is not None:
        func_calls.append(mock.call.clicked.connect(m_clicked_connect_func))
    if m_menu is not None:
        func_calls.append(mock.call.setMenu(m_menu))
    m_tool_button.assert_has_calls(func_calls)


@pytest.mark.parametrize(
    'm_shortcut, m_tool_tip, m_status_tip',
    itertools.product([m_obj, None], repeat=3)
)
def test_set_action_attribute(m_shortcut, m_tool_tip, m_status_tip):
    """test func."""
    m_action = mock.Mock()
    m_triggered_connect_function = mock.Mock()
    # pre run
    from version import misc_app
    # run
    res = misc_app.set_action_attribute(
        m_action,
        m_triggered_connect_function,
        m_shortcut,
        m_tool_tip,
        m_status_tip,
    )
    # test
    assert res == m_action
    func_calls = [mock.call.triggered.connect(m_triggered_connect_function)]
    if m_shortcut is not None:
        func_calls.append(mock.call.setShortcut(m_shortcut))
    if m_tool_tip is not None:
        func_calls.append(mock.call.setToolTip(m_tool_tip))
    if m_status_tip is not None:
        func_calls.append(mock.call.setStatusTip(m_status_tip))
    m_action.assert_has_calls(func_calls)

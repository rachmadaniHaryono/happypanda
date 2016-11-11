"""test module."""
from unittest import mock
import sys

from PyQt5.QtWidgets import QApplication
from PyQt5.QtTest import QTest  # NOQA
from PyQt5.QtCore import Qt  # NOQA

import pytest


non_travis = pytest.mark.non_travis


@non_travis
@pytest.mark.parametrize('disable_excepthook', [True, False])
def test_init(disable_excepthook):
    """test init."""
    with \
            mock.patch('version.app.app_constants'), \
            mock.patch('version.app.sys') as m_sys, \
            mock.patch('version.app.pyqtSignal'), \
            mock.patch('version.app.gallerydb') as m_gallerydb, \
            mock.patch('version.app.QMainWindow'), \
            mock.patch('version.app.QThread') as m_qthread, \
            mock.patch('version.app.QTimer') as m_qtimer, \
            mock.patch('version.app.Qt') as m_qt, \
            mock.patch('version.app.AppWindow._check_update') as m_check_update, \
            mock.patch('version.app.AppWindow.db_startup_invoker') as m_db_si, \
            mock.patch('version.app.AppWindow.excepthook') as m_excepthook, \
            mock.patch('version.app.AppWindow.graphics_blur') as m_graphics_blur, \
            mock.patch('version.app.AppWindow.init_ui') as m_init_ui, \
            mock.patch('version.app.AppWindow.set_shortcuts') as m_set_shortcuts, \
            mock.patch('version.app.AppWindow.setAcceptDrops') as m_set_ad, \
            mock.patch('version.app.AppWindow.setFocusPolicy') as m_set_fp, \
            mock.patch('version.app.AppWindow.startup') as m_start_up:
        from version import app
        # run
        q_app = QApplication(sys.argv)  # NOQA
        app_window = app.AppWindow(disable_excepthook)
        # test
        # test classs attr
        assert app_window._db_startup_thread == m_qthread.return_value
        assert app_window.db_startup == m_gallerydb.DatabaseStartup.return_value
        # 3rd party package
        if disable_excepthook:
            assert m_sys.excepthook != m_excepthook
        else:
            assert m_sys.excepthook == m_excepthook
        m_gallerydb.assert_has_calls([
            mock.call.DatabaseStartup(),
            mock.call.DatabaseStartup().moveToThread(m_qthread.return_value),
            mock.call.DatabaseStartup().DONE.connect(mock.ANY)
        ])
        m_qthread.assert_has_calls([
            mock.call(app_window),
            mock.call().finished.connect(m_qthread.return_value.deleteLater),
            mock.call().start(),
            mock.call(app_window),
            mock.call().finished.connect(m_qthread.return_value.deleteLater),
            mock.call().start()
        ])
        # in class attribute/method test
        m_check_update.assert_not_called()
        m_db_si.connect.assert_called_once_with(m_gallerydb.DatabaseStartup.return_value.startup)
        m_graphics_blur.setParent.assert_called_once_with(app_window)
        m_init_ui.assert_called_once_with()
        m_qtimer.singleShot.assert_called_once_with(3000, m_check_update)
        m_start_up.assert_called_once_with()
        m_set_shortcuts.assert_called_once_with()
        m_set_ad.assert_called_once_with(True)
        m_set_fp.assert_called_once_with(m_qt.NoFocus)
        m_start_up.asert_called_once_with()

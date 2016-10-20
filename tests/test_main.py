"""test main module."""
from unittest import mock
import argparse
import itertools
import os
import pprint

import pytest
import PyQt5

from version.main import (
    Program,
    _confirm_with_user,
    parse_args,
    start,
)
import version


non_travis = pytest.mark.non_travis


@non_travis
def test_run():
    """test run the func."""
    with pytest.raises(SystemExit):
        start(test=True)


def assert_argparse(mock_argparse):
    """assertion for arg parsing."""
    mock_argparse.assert_has_calls([
        mock.call.ArgumentParser(
            description='A manga/doujinshi manager with tagging support', prog='Happypanda'),
        mock.call.ArgumentParser().add_argument(
            '-d', '--debug', action='store_true',
            help='happypanda_debug_log.log will be created in main directory'),
        mock.call.ArgumentParser().add_argument(
            '-t', '--test', action='store_true',
            help='Run happypanda in test mode. 5000 gallery will be preadded in DB.'),
        mock.call.ArgumentParser().add_argument(
            '-v', '--version', action='version', version='Happypanda v0.30'),
        mock.call.ArgumentParser().add_argument(
            '-e', '--exceptions', action='store_true', help='Disable custom excepthook'),
        mock.call.ArgumentParser().add_argument(
            '-x', '--dev', action='store_true', help='Development Switch'),
        mock.call.ArgumentParser().parse_args(),
    ], any_order=True)


@non_travis
def test_run_mock_minimal():
    """test run and mock minimal."""
    with mock.patch('version.main.argparse') as mock_argparse, \
            mock.patch('version.main._confirm_with_user') as mock_cwu:
        mock_argparse.parse_args.return_value = argparse.Namespace(
            debug=False, dev=False, exceptions=False, test=False)
        mock_cwu.return_value = True
        Qapp, app_window = start(test=True)
    # test result
    assert isinstance(Qapp, PyQt5.QtWidgets.QApplication)
    assert isinstance(app_window, version.app.AppWindow)
    # test app_window
    assert len(vars(app_window)) == 33
    # test app_window attr
    assert isinstance(getattr(app_window, '_current_manga_view'), version.gallery.MangaViews)
    assert isinstance(getattr(app_window, '_db_startup_thread'), PyQt5.QtCore.QThread)
    assert isinstance(getattr(app_window, '_main_layout'), PyQt5.QtWidgets.QHBoxLayout)
    assert isinstance(getattr(app_window, 'addition_tab'), version.misc.ToolbarButton)
    assert isinstance(getattr(app_window, 'center'), PyQt5.QtWidgets.QWidget)
    assert isinstance(getattr(app_window, 'data_fetch_spinner'), version.misc.Spinner)
    assert isinstance(getattr(app_window, 'db_startup'), version.gallerydb.DatabaseStartup)
    assert isinstance(getattr(app_window, 'default_manga_view'), version.gallery.MangaViews)
    assert isinstance(getattr(app_window, 'download_window'), version.io_misc.GalleryDownloader)
    assert isinstance(getattr(app_window, 'grid_toggle'), PyQt5.QtWidgets.QToolButton)
    assert isinstance(getattr(app_window, 'grid_toggle_g_icon'), PyQt5.QtGui.QIcon)
    assert isinstance(getattr(app_window, 'grid_toggle_l_icon'), PyQt5.QtGui.QIcon)
    assert isinstance(getattr(app_window, 'manga_list_view'), version.gallery.MangaView)
    assert isinstance(getattr(app_window, 'manga_table_view'), version.gallery.MangaTableView)
    assert isinstance(getattr(app_window, 'notif_bubble'), version.misc.AppBubble)
    assert isinstance(getattr(app_window, 'notification_bar'), version.misc.NotificationOverlay)
    assert isinstance(getattr(app_window, 'search_backward'), PyQt5.QtWidgets.QWidgetAction)
    assert isinstance(getattr(app_window, 'search_bar'), version.misc.LineEdit)
    assert isinstance(getattr(app_window, 'search_forward'), PyQt5.QtWidgets.QWidgetAction)
    assert isinstance(getattr(app_window, 'search_timer'), PyQt5.QtCore.QTimer)
    assert isinstance(getattr(app_window, 'sidebar_list'), version.misc_db.SideBarWidget)
    assert isinstance(getattr(app_window, 'sort_main'), PyQt5.QtWidgets.QAction)
    assert isinstance(getattr(app_window, 'stat_info'), PyQt5.QtWidgets.QLabel)
    assert isinstance(getattr(app_window, 'status_bar'), PyQt5.QtWidgets.QStatusBar)
    assert isinstance(getattr(app_window, 'system_tray'), version.misc.SystemTray)
    assert isinstance(getattr(app_window, 'tab_manager'), version.misc_db.ToolbarTabManager)
    assert isinstance(getattr(app_window, 'temp_msg'), PyQt5.QtWidgets.QLabel)
    assert isinstance(getattr(app_window, 'temp_timer'), PyQt5.QtCore.QTimer)
    assert isinstance(getattr(app_window, 'toolbar'), PyQt5.QtWidgets.QToolBar)
    assert isinstance(getattr(app_window, 'watchers'), version.io_misc.Watchers)
    # test_appwindow attr which have simple value
    assert isinstance(getattr(app_window, '_search_cursor_pos'), list)
    assert getattr(app_window, '_search_cursor_pos') == [0, 0]
    assert isinstance(getattr(app_window, 'manga_views'), dict)
    assert getattr(app_window, 'manga_views') == {}
    # can't test the type
    """
    assert isinstance(getattr(app_window, 'scan_inst'),
        version.app.AppWindow.scan_for_new_galleries.<locals>.ScanDir)
    assert isinstance(getattr(app_window, 'update_instance'),
        version.app.AppWindow._check_update.<locals>.upd_chk)
    """

    # test argparse
    assert len(mock_argparse.mock_calls) == 13
    assert_argparse(mock_argparse)
    mock_argparse.assert_has_calls([
        mock.call.ArgumentParser().parse_args().dev.__bool__(),
        mock.call.ArgumentParser().parse_args().debug.__bool__(),
        mock.call.ArgumentParser().parse_args().exceptions.__bool__(),
        mock.call.ArgumentParser().parse_args().debug.__bool__(),
        mock.call.ArgumentParser().parse_args().test.__bool__(),
        mock.call.ArgumentParser().parse_args().exceptions.__bool__()
    ])
    # test _confirm_with_user func.
    mock_cwu.assert_any_call(
        informative_text='Do you want to create new database?',
        text='Invalid database'
    )
    mock_cwu.assert_any_call(
        informative_text=(
            "Do you want to upgrade to newest version? It shouldn't take more than a second. "
            "Don't start a new instance!"
        ),
        text='Incompatible database!'
    )


def test_program_init():
    """test program class init."""
    mock_args = mock.Mock()
    mock_test = mock.Mock()
    mock_logger_name = mock.Mock()
    with mock.patch('version.main.os') as mock_os:
        program = Program(mock_args, mock_test, mock_logger_name)

        assert program._logger_name == mock_logger_name
        assert program.args == mock_args
        assert program.debug_log_path == 'happypanda_debug.log'
        assert program.is_test == mock_test
        assert program.log_path == 'happypanda.log'

        assert len(mock_os.mock_calls) == 6
        os_calls = [
            mock.call.path.exists('cacert.pem'),
            mock.call.path.exists().__bool__(),
            mock.call.getcwd(),
            mock.call.path.join(mock_os.getcwd.return_value, 'cacert.pem'),
            mock.call.environ.__setitem__('REQUESTS_CA_BUNDLE', mock_os.path.join.return_value)
        ]
        mock_os.assert_has_calls(os_calls, any_order=True)

    with mock.patch('version.main.os') as mock_os:
        mock_os.name = 'posix'
        program = Program(mock_args, mock_test, mock_logger_name)

        assert program._logger_name == mock_logger_name
        assert program.args == mock_args
        assert program.debug_log_path == mock_os.path.join.return_value
        assert program.is_test == mock_test
        assert program.log_path == mock_os.path.join.return_value
        assert program.main_path == mock_os.path.dirname.return_value

        assert len(mock_os.mock_calls) == 12
        os_calls = [
            mock.call.path.dirname(mock_os.path.realpath.return_value),
            mock.call.path.join(mock_os.path.dirname.return_value, 'happypanda.log'),
            mock.call.path.join(mock_os.path.dirname.return_value, 'happypanda_debug.log'),
            mock.call.path.exists('cacert.pem'),
            mock.call.path.exists().__bool__(),
            mock.call.getcwd(),
            mock.call.path.join(mock_os.getcwd.return_value, 'cacert.pem'),
            mock.call.environ.__setitem__('REQUESTS_CA_BUNDLE', mock_os.path.join.return_value),
        ]
        assert os.path.join(
            'happypanda', 'version', 'main.py'
        ) in mock_os.path.realpath.call_args[0][0]
        mock_os.assert_has_calls(os_calls, any_order=True)


def test_program_set_logger():
    """test program's method set_logger."""
    val_pairs = set(list(
        itertools.combinations_with_replacement([True, False, True, False], 3)))
    for dev, debug, raise_file_exists_error in val_pairs:
        mock_args = argparse.Namespace(dev=dev, debug=debug)
        mock_test = mock.Mock()
        mock_logger_name = 'logger_name'
        mock_open = mock.mock_open()
        with mock.patch('version.main.os') as mock_os, \
                mock.patch('version.main.open', mock_open, create=True), \
                mock.patch('version.main.app_constants') as mock_app_constants, \
                mock.patch('version.main.logging') as mock_logging:
            program = Program(mock_args, mock_test, mock_logger_name)
            if raise_file_exists_error:
                mock_open.side_effect = FileExistsError  # NOQA
            program._set_logger()
            # test logging
            mock_logging_calls_count = 0
            log_calls = []
            log_handlers = []
            if dev:
                log_handlers.append(mock_logging.StreamHandler.return_value)
                mock_logging_calls_count += 1
            if debug:
                mock_logging_calls_count += 3
                log_handlers.append(mock_logging.FileHandler.return_value)
                log_calls.extend([
                    mock.call.FileHandler('happypanda_debug.log', 'w', 'utf-8'),
                    mock.call.basicConfig(
                        datefmt='%d-%m %H:%M',
                        format='%(asctime)-8s %(levelname)-6s %(name)-6s %(message)s',
                        handlers=tuple(log_handlers),
                        level=mock_logging.DEBUG,
                    ),
                ])
                assert mock_app_constants.DEBUG
            else:
                mock_logging_calls_count += 3
                log_handlers.append(mock_logging.handlers.RotatingFileHandler.return_value)
                log_calls.extend([
                    mock.call.handlers.RotatingFileHandler(
                        'happypanda.log', backupCount=2, encoding='utf-8', maxBytes=10000000),
                    mock.call.basicConfig(
                        datefmt='%d-%m %H:%M',
                        format='%(asctime)-8s %(levelname)-6s %(name)-6s %(message)s',
                        handlers=tuple(log_handlers),
                        level=mock_logging.INFO
                    ),
                ])
            assert len(mock_logging.mock_calls) == mock_logging_calls_count
            assert program.log == mock_logging.getLogger.return_value
            assert program.log_i == mock_logging.getLogger.return_value.info
            assert program.log_d == mock_logging.getLogger.return_value.debug
            log_calls.append(mock.call.getLogger(mock_logger_name))
            mock_logging.assert_has_calls(log_calls, any_order=True)
            # test os
            if debug:
                assert len(mock_os.mock_calls) == 8
            else:
                assert len(mock_os.mock_calls) == 6
            os_calls = [
                mock.call.path.exists('cacert.pem'),
                mock.call.path.exists().__bool__(),
                mock.call.getcwd(),
                mock.call.path.join(mock_os.getcwd.return_value, 'cacert.pem'),
                mock.call.environ.__setitem__('REQUESTS_CA_BUNDLE', mock_os.path.join.return_value),
            ]
            mock_os.assert_has_calls(os_calls, any_order=True)
            # test open
            if raise_file_exists_error:
                assert len(mock_open.mock_calls) == 1
            else:
                assert len(mock_open.mock_calls) == 3
            if debug:
                mock_open.assert_any_call('happypanda_debug.log', 'x')
            else:
                mock_open.assert_any_call('happypanda.log', 'x')


def test_program_handle_database():
    """test program's method set_logger."""
    costum_namespace = argparse.Namespace(test=False, dev=True, debug=True)
    mock_obj = mock.Mock()
    for mock_args in (mock_obj, costum_namespace):
        mock_test = mock.Mock()
        mock_logger_name = 'logger_name'
        mock_open = mock.mock_open()
        mock_application = mock.Mock()
        mock_log_debug = mock.Mock()
        mock_log_info = mock.Mock()
        with mock.patch('version.main.os'), \
                mock.patch('version.main.open', mock_open, create=True), \
                mock.patch('version.main.db') as mock_db, \
                mock.patch('version.main._confirm_with_user') as mock_cwu:
            program = Program(mock_args, mock_test, mock_logger_name)
            program.log_d = mock_log_debug
            program.log_i = mock_log_info
            res = program._handle_database(mock_application)
            if mock_args == mock_obj:
                mock_db.init_db.assert_called_once_with(True)
            else:
                mock_db.init_db.assert_called_once_with()
            assert not mock_cwu.called
            assert res == mock_db.init_db.return_value
            mock_log_debug.assert_called_once_with('Init DB Conn: OK')
            mock_log_info.assert_called_once_with('DB Version: 0.26')


def test_program_handle_database_with_error():
    """test handle database with error."""
    for user_confirm_result in (True, False):
        mock_args = mock.Mock()
        mock_test = mock.Mock()
        mock_logger_name = 'logger_name'
        mock_open = mock.mock_open()
        mock_application = mock.Mock()
        mock_log = mock.Mock()
        mock_log_debug = mock.Mock()
        mock_log_info = mock.Mock()
        mock_log_critical = mock.Mock()
        with mock.patch('version.main.os'), \
                mock.patch('version.main.open', mock_open, create=True), \
                mock.patch('version.main.db') as mock_db, \
                mock.patch('version.main._confirm_with_user') as mock_cwu:
            # pre-run
            mock_db.init_db.side_effect = KeyboardInterrupt
            mock_cwu.return_value = user_confirm_result
            # run the function needed
            program = Program(mock_args, mock_test, mock_logger_name)
            program.log = mock_log
            program.log_i = mock_log_info
            program.log_d = mock_log_debug
            program.log_c = mock_log_critical
            # prepare test data
            res = None
            # run the tested function.
            if user_confirm_result:
                res = program._handle_database(mock_application)
            else:
                with pytest.raises(SystemExit):
                    res = program._handle_database(mock_application)
                mock_log_critical.assert_called_once_with('Invalid database')
                mock_log.exception.assert_called_once_with('Database connection failed!')
                mock_application.exit.assert_called_once_with()
                mock_log_debug.assert_called_once_with('Normal Exit App: OK')
            # testing
            mock_cwu.assert_called_once_with(
                informative_text='Do you want to create new database?',
                text='Invalid database')
            assert res is None


def test_program_db_upgrade():
    """test db upgrade."""
    for user_confirm_result in (True, False):
        mock_args = mock.Mock()
        mock_test = mock.Mock()
        mock_logger_name = 'logger_name'
        mock_open = mock.mock_open()
        mock_application = mock.Mock()
        mock_log_debug = mock.Mock()
        with mock.patch('version.main.os'), \
                mock.patch('version.main.open', mock_open, create=True), \
                mock.patch('version.main.db') as mock_db, \
                mock.patch('version.main.utils') as mock_utils, \
                mock.patch('version.main._confirm_with_user') as mock_cwu, \
                mock.patch('version.main.Program._start_main_window') as mock_smw:
            # run the function needed
            program = Program(mock_args, mock_test, mock_logger_name)
            program.log_d = mock_log_debug
            mock_cwu.return_value = user_confirm_result
            res = program._db_upgrade(mock_application)
            # test data
            mock_cwu.assert_called_once_with(
                text='Incompatible database!',
                informative_text=(
                    "Do you want to upgrade to newest version? "
                    "It shouldn't take more than a second. "
                    "Don't start a new instance!")
            )
            log_debug_calls = [mock.call('Database connection failed')]
            if user_confirm_result:
                mock_smw.assert_called_once_with(
                    mock_db.init_db.return_value, application=mock_application
                )
                add_db_revisions_input = mock_db.add_db_revisions.call_args[0][0]
                assert os.path.join('..', 'db', 'happypanda.db') in add_db_revisions_input
                assert len(mock_db.mock_calls) == 2
                mock_db.init_db.assert_called_once_with()
                assert res == mock_smw.return_value
                mock_utils.backup_database.assert_called_once_with()
            else:
                log_debug_calls.append(mock.call('Normal Exit App: OK'))
                mock_application.exit.assert_called_once_with()
                assert res == 0
            mock_log_debug.assert_has_calls(log_debug_calls)


def test_program_start_main_window():
    """test program start_main_window method."""
    val_pairs = set(list(
        itertools.combinations_with_replacement([True, False, True, False], 3)))
    for mock_test, raise_file_exists_error , raise_scandir_walk_error in val_pairs:
        mock_log_debug = mock.Mock()
        mock_log_info = mock.Mock()
        mock_log = mock.Mock()
        mock_conn = mock.Mock()
        mock_application = mock.Mock()
        mock_args = mock.Mock()
        mock_logger_name = 'logger_name'
        mock_root = mock.Mock()
        mock_dir = mock.Mock()
        mock_file = mock.Mock()
        with mock.patch('version.main.os') as mock_os, \
                mock.patch('version.main.app') as mock_app, \
                mock.patch('version.main.app_constants') as mock_app_constants, \
                mock.patch('version.main.scandir') as mock_scandir, \
                mock.patch('version.main.Program._create_window_style') as mock_cws, \
                mock.patch('version.main.map') as mock_map, \
                mock.patch('version.main.db') as mock_db:
            program = Program(mock_args, mock_test, mock_logger_name)
            program.log_d = mock_log_debug
            program.log_i = mock_log_info
            program.log = mock_log

            if not raise_scandir_walk_error:
                mock_scandir.walk.return_value = [(mock_root, [mock_dir], [mock_file])]
            else:
                mock_scandir.walk.return_value = KeyboardInterrupt
            if raise_file_exists_error:
                mock_os.mkdir.side_effect = FileExistsError  # NOQA
            res = program._start_main_window(mock_conn, mock_application)
            # test
            assert mock_db.DBBase._DB_CONN == mock_conn
            mock_os.mkdir.assert_called_once_with(mock_app_constants.temp_dir)
            mock_app.AppWindow.assert_called_once_with(mock_args.exceptions)
            mock_log_debug.assert_called_once_with('Create temp: OK')
            # mock_application
            if raise_file_exists_error:
                mock_scandir.walk.assert_called_once_with('temp', topdown=False)
                if not raise_scandir_walk_error:
                    mock_map.assert_any_call(mock.ANY, [mock_file])
                    mock_map.assert_any_call(mock.ANY, [mock_dir])
            if raise_scandir_walk_error and raise_file_exists_error:
                mock_log.exception.assert_called_once_with('Empty temp: FAIL')
            mock_application.setStyleSheet.assert_called_once_with(mock_cws.return_value)
            if mock_test:
                assert res == (mock_application, mock_app.AppWindow.return_value)
            else:
                mock_application.exec_.assert_called_once_with()
                assert res == mock_application.exec_.return_value


def test_program_run():
    """test program run."""
    val_pairs = set(list(
            itertools.combinations_with_replacement([True, False, True, False, True], 4)))
    mock_log_info = mock.Mock()
    for args_exception, force_high_dpi_support, args_debug, handle_db_retval in val_pairs:
        costum_namespace = argparse.Namespace(exceptions=args_exception, debug=args_debug)
        with mock.patch('version.main.os') as mock_os, \
                mock.patch('version.main.Qt') as mock_qt, \
                mock.patch('version.main.QApplication') as mock_qapp, \
                mock.patch('version.main.sys') as mock_sys, \
                mock.patch('version.main.platform') as mock_platform, \
                mock.patch('version.main.app_constants') as mock_app_constants, \
                mock.patch('version.main.Program._change_sys_excepthook') \
                as mock_change_sys_excepthook, \
                mock.patch('version.main.Program._set_logger') as mock_set_logger, \
                mock.patch('version.main.Program._start_main_window') as mock_smw, \
                mock.patch('version.main.Program._db_upgrade') as mock_db_upgrade, \
                mock.patch('version.main.Program._handle_database') as mock_handle_database:
            program = Program(args=costum_namespace)
            mock_app_constants.FORCE_HIGH_DPI_SUPPORT.return_value = force_high_dpi_support
            mock_handle_database.return_value = handle_db_retval
            program.log_i = mock_log_info
            res = program.run()
            # testing
            mock_set_logger.assert_called_once_with()
            if not args_exception:
                mock_change_sys_excepthook.assert_called_once_with()
            else:
                assert not mock_change_sys_excepthook.called
            log_info_calls = []
            if force_high_dpi_support:
                log_info_calls.append(mock.call("Enabling high DPI display support"))
                mock_os.environ.putenv.assert_called_once_with('QT_DEVICE_PIXEL_RATIO', "auto")
            if args_debug:
                log_info_calls.append(mock.call('Running in debug mode'))
                assert mock_sys.displayhook == pprint.pprint
            if handle_db_retval:
                mock_smw.assert_called_once_with(
                    mock_handle_database.return_value,
                    application=mock_qapp.return_value
                )
                assert res == mock_smw.return_value
            else:
                mock_db_upgrade.assert_called_once_with(mock_qapp.return_value)
                assert res == mock_db_upgrade.return_value
            qapp_calls = [
                mock.call.setEffectEnabled(mock_qt.UI_AnimateCombo),
                mock.call.setEffectEnabled(mock_qt.UI_FadeMenu),
                mock.call.setEffectEnabled(mock_qt.UI_AnimateMenu),
                mock.call.setEffectEnabled(mock_qt.UI_AnimateTooltip),
                mock.call.setEffectEnabled(mock_qt.UI_FadeTooltip),
                mock.call(mock_sys.argv),
                mock.call().setOrganizationName('Pewpews'),
                mock.call().setOrganizationDomain('https://github.com/Pewpews/happypanda'),
                mock.call().setApplicationName('Happypanda'),
                mock.call().setApplicationDisplayName('Happypanda'),
                mock.call().setApplicationVersion("v{}".format(mock_app_constants.vs)),
                mock.call().setAttribute(mock_qt.AA_UseHighDpiPixmaps),
            ]
            assert len(mock_qapp.mock_calls) == 12
            mock_qapp.assert_has_calls(qapp_calls)
            log_info_calls.extend([
                mock.call('Happypanda Version {}'.format(mock_app_constants.vs)),
                mock.call('OS: {} {}\n'.format(
                    mock_platform.system.return_value,
                    mock_platform.release.return_value)),
            ])
            mock_log_info.assert_has_calls(log_info_calls, any_order=True)


def test_program_create_window_style():
    """test program create create_window_style."""
    mock_style = mock.Mock()
    style_file_string = 'mock_string'.encode('utf8')
    # check depend on app_constants.user_stylesheet_path
    for ac_usp in ([], [mock_style]):
        with mock.patch('version.main.app_constants') as mock_app_constants, \
                mock.patch('version.main.QFile') as mock_qfile:
            mock_log_info = mock.Mock()
            program = Program()
            program.log_i = mock_log_info
            mock_qfile.return_value.readAll.return_value = style_file_string
            mock_app_constants.user_stylesheet_path = ac_usp
            res = program._create_window_style()
            if ac_usp == []:
                used_style_path = mock_app_constants.default_stylesheet_path
                mock_log_info.assert_called_once_with('Select defaultstyle: OK')
            else:
                used_style_path = mock_app_constants.user_stylesheet_path
                mock_log_info.assert_called_once_with('Select userstyle: OK')
            qfile_calls = [
                mock.call(used_style_path),
                mock.call().open(mock_qfile.ReadOnly),
                mock.call().readAll()
            ]
            mock_qfile.assert_has_calls(qfile_calls, any_order=True)
            assert res == str(style_file_string, 'utf-8')


def test_program_create_window_style_with_error():
    """test program create create_window_style but with error.

    when loading user style, raise error and test the response.
    """
    mock_style = mock.Mock()
    style_file_string = 'mock_string'.encode('utf8')
    qfile_retval = mock.Mock()

    def qfile_side_effect(arg):
        """side effect for qfile."""
        if arg == mock_app_constants.user_stylesheet_path:
            raise KeyboardInterrupt
        qfile_retval.readAll.return_value = style_file_string
        retval = qfile_retval
        return retval
    with mock.patch('version.main.app_constants') as mock_app_constants, \
            mock.patch('version.main.QFile') as mock_qfile:
        mock_log_info = mock.Mock()
        program = Program()
        program.log_i = mock_log_info
        mock_app_constants.user_stylesheet_path = [mock_style]
        mock_qfile.side_effect = qfile_side_effect
        res = program._create_window_style()
        used_style_path = mock_app_constants.user_stylesheet_path
        mock_log_info.assert_called_once_with('Select defaultstyle: OK')
        qfile_calls = [
            mock.call(used_style_path),
            mock.call(mock_app_constants.default_stylesheet_path),
        ]
        mock_qfile.assert_has_calls(qfile_calls, any_order=True)
        assert res == str(style_file_string, 'utf-8')


def test_program_change_sys_excepthook():
    """test program method _change_sys_excepthook."""
    with mock.patch('version.main.Program._uncaught_exceptions') as mock_uncaught_exceptions, \
            mock.patch('version.main.sys') as mock_sys:
        program = Program()
        program._change_sys_excepthook()
        assert mock_sys.excepthook == mock_uncaught_exceptions


def test_program_uncaught_exceptions():
    """test program method uncaught_exceptions."""
    for mock_traceback_return_list in (False, True):
        mock_ex_type = mock.Mock()
        mock_ex = mock.Mock()
        mock_tb = mock.Mock()
        mock_log_critical = mock.Mock()
        mock_val = 'string_result'
        traceback_retval = [mock_val]
        with mock.patch('version.main.traceback') as mock_traceback:
            if mock_traceback_return_list:
                mock_traceback.format_tb.return_value = traceback_retval
            program = Program()
            program.log_c = mock_log_critical
            program._uncaught_exceptions(mock_ex_type, mock_ex, mock_tb)
            if mock_traceback_return_list:
                assert len(mock_traceback.mock_calls) == 2
                log_critical_first_input = mock_val
            else:
                log_critical_first_input = ''
                assert len(mock_traceback.mock_calls) == 3
            mock_traceback.assert_has_calls([
                mock.call.format_tb(mock_tb),
                mock.call.print_exception(mock_ex_type, mock_ex, mock_tb)
            ], any_order=True)
            assert len(mock_log_critical.mock_calls) == 2
            mock_log_critical.assert_has_calls([
                mock.call(log_critical_first_input),
                mock.call("{}: {}".format(mock_ex_type, mock_ex))
            ])


def test_start():
    """test start func."""
    for is_test in (True, False):
        with mock.patch('version.main.app_constants') as mock_app_constants, \
                mock.patch('version.main.parse_args') as mock_parse_args, \
                mock.patch('version.main.Program') as mock_program:
            res = start(is_test)
            mock_app_constants.APP_RESTART_CODE == -123456789
            mock_parse_args.assert_called_once_with()
            assert res == mock_program.return_value.run.return_value
            program_calls = [
                mock.call(
                    args=mock_parse_args.return_value,
                    logger_name='version.main',
                    test=is_test),
                mock.call().run()
            ]
            mock_program.assert_has_calls(program_calls)


def test_confirm_with_user():
    """test confirm with user."""
    mock_text = mock.Mock()
    mock_informative_text = mock.Mock()
    with mock.patch('version.main.QMessageBox') as mock_qmsg_box, \
            mock.patch('version.main.QIcon') as mock_qicon, \
            mock.patch('version.main.app_constants') as mock_app_constants:
        res = _confirm_with_user(mock_text, mock_informative_text)
        assert not res
        assert isinstance(res, bool)
        # test QMessageBox
        assert len(mock_qmsg_box.mock_calls) == 10
        qmsg_box_calls = [
            mock.call(),
            mock.call().setWindowIcon(mock_qicon.return_value),
            mock.call().setText(mock_text),
            mock.call().setInformativeText(mock_informative_text),
            mock.call().setIcon(mock_qmsg_box.Critical),
            mock.call().setStandardButtons(mock_qmsg_box.Yes.__or__.return_value),
            mock.call().setDefaultButton(mock_qmsg_box.Yes),
            mock.call().exec_(),
        ]
        mock_qmsg_box.assert_has_calls(qmsg_box_calls, any_order=True)
        # test QIcon
        mock_qicon.assert_called_once_with(mock_app_constants.APP_ICO_PATH)

    with mock.patch('version.main.QMessageBox') as mock_qmsg_box, \
            mock.patch('version.main.QIcon'), \
            mock.patch('version.main.app_constants'):
        mock_qmsg_box.return_value.exec_.return_value = mock_qmsg_box.Yes
        res = _confirm_with_user(mock_text, mock_informative_text)
        assert res
        assert isinstance(res, bool)


def test_parse_args():
    """test parse_args."""
    with mock.patch('version.main.argparse') as mock_argparse:
        res = parse_args()
        assert len(mock_argparse.mock_calls) == 7
        res == mock_argparse.ArgumentParser.return_value.parse_args.return_value
        assert_argparse(mock_argparse)

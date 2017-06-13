"""main module."""
# Happypanda is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with Happypanda.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import logging
import logging.handlers
import os
import platform
import pprint
import sys
import traceback
from structlog import getLogger

from PyQt5.QtCore import QFile, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMessageBox
import appdirs

from .app import AppWindow
from .database import db, db_constants
from .__init__ import (
    __app_name__ as app_name,
    __version__ as app_version,
    __author__ as app_author,
    __author_name__ as app_author_name,
)
from . import (
    app_constants,
    utils,
)


def confirm_with_user(text, informative_text):
    """confirm with user to create database.

    Args:
        text(str):Message box text.
        informative_text(str):Informative text for message box.
    Returns:
        bool:User confirmed or not.
    """
    msg_box = QMessageBox()
    msg_box.setWindowIcon(QIcon(app_constants.APP_ICO_PATH))
    msg_box.setText(text)
    msg_box.setInformativeText(informative_text)
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    msg_box.setDefaultButton(QMessageBox.Yes)
    return msg_box.exec_() == QMessageBox.Yes


def parse_args(argv):
    """parse application arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        prog=app_name, description='A manga/doujinshi manager with tagging support')
    parser.add_argument(
        '-d', '--debug', action='store_true',
        help='happypanda_debug_log.log will be created in main directory')
    parser.add_argument(
        '-t', '--test', action='store_true',
        help='Run happypanda in test mode. 5000 gallery will be preadded in DB.')
    parser.add_argument(
        '-v', '--version', action='version',
        version='%(prog)s {}'.format(app_version))
    parser.add_argument(
        '-e', '--exceptions', action='store_true', help='Disable custom excepthook')
    parser.add_argument(
        '-x', '--dev', action='store_true', help='Development Switch')

    return parser.parse_args(argv)


def init_logger(log_path, debug_log_path, dev, debug):
    """init logging.

    Args:
        log_path: Path for log file for normal logging.
        debug_log_path: Path for log file for debug logging.
        dev (bool): Set logging for dev mode.
        debug (bool: Set logging for debug mode.)
    """
    log_handlers = []
    log_level = logging.INFO
    file_logger = None
    if dev:
        log_handlers.append(logging.StreamHandler())
    if debug:
        print("{} created at \n{}".format(
            os.path.basename(debug_log_path),
            os.path.dirname(debug_log_path)
        ))
        os.makedirs(os.path.dirname(debug_log_path), exist_ok=True)

        file_logger = logging.FileHandler(debug_log_path, encoding='utf-8')
        log_handlers.append(file_logger)
        log_level = logging.DEBUG
        app_constants.DEBUG = True
    else:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        log_handlers.append(logging.handlers.RotatingFileHandler(
            log_path, maxBytes=1000000 * 10, encoding='utf-8', backupCount=2))

    # Fix for logging not working
    # clear the handlers first before adding these custom handler
    # http://stackoverflow.com/a/15167862
    logging.getLogger('').handlers = []
    logging.basicConfig(
        level=log_level,
        format='%(asctime)-8s %(levelname)-6s %(name)-6s %(message)s',
        datefmt='%d-%m %H:%M',
        handlers=log_handlers)
    log = getLogger()
    log.debug('logger initiated', logfile=file_logger, log_level=log_level)


def get_log_path():
    """get info level log path, and debug level path."""
    log_dir = appdirs.user_log_dir(app_name, app_author_name)
    log_path = os.path.join(log_dir, 'happypanda.log')
    debug_log_path = os.path.join(log_dir, 'happypanda_debug.log')
    return log_path, debug_log_path


def set_requests_certificate():
    """Set requests certificate, if exist by set environment variable."""
    log = getLogger()
    if os.path.exists('cacert.pem'):
        req_cert_file = os.path.join(os.getcwd(), "cacert.pem")
        os.environ["REQUESTS_CA_BUNDLE"] = req_cert_file
        log.debug('change REQUESTS_CA_BUNDLE environ', file=req_cert_file)


class Program:
    """Program class.

    TODO:
        * find log path from outer function.
        * set environment variable from outer function.

    Attributes:
        args(argparse.Namespace): Parsed argument used in program.
        is_test(bool): State of the program, if it is on test mode.
        log_path(str): Path of log file.
        log_debug_path(str): Path of log file in debug mode..
        log(logging.Logger): Logger Class.
    """

    def __init__(self, args=None, test=False):
        """init func."""
        self.args = args
        self.is_test = test
        self.log = getLogger(__name__)

    def get_window_stylesheet(self):
        """create window style.

        Returns:
            str:Style.
        """
        d_style = app_constants.default_stylesheet_path
        u_style = app_constants.user_stylesheet_path
        if len(u_style) is not 0:
            try:
                style_file = QFile(u_style)
                self.log.info('Select userstyle: OK')
            except:
                style_file = QFile(d_style)
                self.log.info('Select defaultstyle: OK')
        else:
            style_file = QFile(d_style)
            self.log.info('Select defaultstyle: OK')

        style_file.open(QFile.ReadOnly)
        style = str(style_file.readAll(), 'utf-8')
        return style

    def init_temp_dir(self):
        """init temp dir."""
        try:
            temp_dir_parent_dir = os.path.dirname(app_constants.temp_dir)
            temp_dir_parent_exists = os.path.isdir(temp_dir_parent_dir)
            if not temp_dir_parent_exists:
                os.mkdir(temp_dir_parent_dir)
            if not os.path.isdir(app_constants.temp_dir):
                os.mkdir(app_constants.temp_dir)
            else:
                self.log.debug('Tempdir exist, skip create')
        except OSError as e:
            self.log.exception('Create temp: Fail', exceptions=e)
            try:
                AppWindow.clean_up_temp_dir()
                os.mkdir(app_constants.temp_dir)
                self.log.debug('Temp dir created.')
            except Exception as e:
                self.log.exception("Empty temp: FAIL", exception=str(e))
        self.log.debug('Tempdir: OK')

    def start_main_window(self, conn, application):
        """start main window.

        Args:
            conn:Database connection.
            application(PyQt5.QtWidgets.QApplication):Application.
        Returns:
            int:Return code.
        """
        db.DBBase._DB_CONN = conn
        # create window
        window = AppWindow(self.args.exceptions)

        # styling
        style = self.get_window_stylesheet()
        application.setStyleSheet(style)

        self.init_temp_dir()

        if self.is_test:
            return application, window

        return application.exec_()

    def uncaught_exceptions(self, ex_type, ex, tb):
        """Uncaught exceptions.

        Args:
            ex_type:Exception type.
            Exception:Exception
            tb:traceback

        """
        self.log.critical(
            'Uncaught exception',
            formatted_tb=traceback.format_tb(tb),
            exception_type=ex_type,
            exception=ex,
            traceback=tb
        )
        traceback.print_exception(ex_type, ex, tb)

    def handle_database(self, application):
        """handle database.

        Args:
            application(PyQt5.QtWidgets.QApplication):Application.

        Returns:
            Database connection
        """
        conn = None
        try:
            if self.args.test:
                conn = db.init_db(True)
            else:
                conn = db.init_db()
            self.log.debug('Init DB Conn: OK')
            self.log.info("DB Version: {}".format(db_constants.REAL_DB_VERSION))
        except:
            self.log.critical('Invalid database')
            self.log.exception('Database connection failed!')
            text = 'Invalid database'
            info_text = "Do you want to create new database?"
            if not confirm_with_user(text=text, informative_text=info_text):
                application.exit()
                self.log.debug('Normal Exit App: OK')
                sys.exit()
        return conn

    def db_upgrade(self, application):
        """upgrade database.

        Args:
            application(PyQt5.QtWidgets.QApplication):Application.

        Returns:
            int:Returns code.
        """
        self.log.debug('Database connection failed')
        text = 'Incompatible database!'
        info_text = (
            "Do you want to upgrade to newest version? "
            "It shouldn't take more than a second. "
            "Don't start a new instance!"
        )
        if confirm_with_user(text=text, informative_text=info_text):
            utils.backup_database()

            db_p = db_constants.DB_PATH
            db.add_db_revisions(db_p)
            conn = db.init_db()

            return self.start_main_window(conn, application=application)
        else:
            application.exit()
            self.log.debug('Normal Exit App: OK')
            return app_constants.ExitCode.normal_code

    def run(self):
        """run the program.

        Returns:
            int: Return code.
        """
        if self.args.exceptions:
            sys.excepthook = self.uncaught_exceptions

        if app_constants.FORCE_HIGH_DPI_SUPPORT:
            self.log.info("Enabling high DPI display support")
            os.environ.putenv("QT_DEVICE_PIXEL_RATIO", "auto")

        # effects
        effects = [
            Qt.UI_AnimateCombo, Qt.UI_FadeMenu, Qt.UI_AnimateMenu,
            Qt.UI_AnimateTooltip, Qt.UI_FadeTooltip]
        list(map(QApplication.setEffectEnabled, effects))

        application = QApplication(sys.argv)
        # set application metadata
        application.setOrganizationName(app_author)
        application.setOrganizationDomain('https://github.com/Pewpews/happypanda')
        application.setApplicationName(app_name)
        application.setApplicationDisplayName(app_name)
        application.setApplicationVersion(app_version)
        application.setAttribute(Qt.AA_UseHighDpiPixmaps)

        self.log.info(
            'Starting', app_name=app_name, app_version=app_version, debug=self.args.debug)
        self.log.info(
            'Status', platform_system=platform.system(), platform_release=platform.release())

        if self.args.debug:
            sys.displayhook = pprint.pprint

        app_constants.load_icons()

        # start database and main window
        conn = self.handle_database(application)
        if conn:
            exit_code = self.start_main_window(conn=conn, application=application)
        else:
            exit_code = self.db_upgrade(application=application)
        self.log.info('Exit', exit_code=exit_code)
        return exit_code


def main():
    """main function."""
    exit_code = app_constants.ExitCode.restart_code
    args = parse_args(sys.argv[1:])

    # logging
    log_path, debug_log_path = get_log_path()
    logger_kwargs = {
        'log_path': log_path,
        'debug_log_path': debug_log_path,
        'dev': args.dev,
        "debug": args.debug}
    init_logger(**logger_kwargs)
    log = getLogger(__name__)
    log.debug('args', v=args)
    log.debug('logger', **logger_kwargs)

    set_requests_certificate()

    while exit_code == app_constants.ExitCode.restart_code:
        program = Program(args=args)
        exit_code = program.run()

if __name__ == '__main__':
    main()

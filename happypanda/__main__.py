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
import scandir
import sys
import traceback

from PyQt5.QtCore import QFile, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMessageBox
import appdirs

from .app import AppWindow
from .database import db, db_constants
from . import (
    app_constants,
    utils,
)


"""
metadata for this file.
this may be moved so it can be freely accessible to other module as well.
this follow https://www.python.org/dev/peps/pep-0345
"""
__author__ = 'Pewpews'


def _confirm_with_user(text, informative_text):
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
        prog='Happypanda', description='A manga/doujinshi manager with tagging support')
    parser.add_argument(
        '-d', '--debug', action='store_true',
        help='happypanda_debug_log.log will be created in main directory')
    parser.add_argument(
        '-t', '--test', action='store_true',
        help='Run happypanda in test mode. 5000 gallery will be preadded in DB.')
    parser.add_argument(
        '-v', '--version', action='version',
        version='Happypanda v{}'.format(app_constants.vs))
    parser.add_argument(
        '-e', '--exceptions', action='store_true', help='Disable custom excepthook')
    parser.add_argument(
        '-x', '--dev', action='store_true', help='Development Switch')

    return parser.parse_args(argv)


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
        log_i(logging.Logger.info): Info log function.
        log_d(logging.Logger.debug): Debug log function.
        log_c(logging.Logger.critical): Critical log function.
        log(logging.Logger): Logger Class.
    """

    def __init__(self, args=None, test=False):
        """init func."""
        self.args = args
        self.is_test = test
        # set log path
        log_dir = appdirs.user_log_dir('happypanda', __author__)
        self.log_path = os.path.join(log_dir, 'happypanda.log')
        self.debug_log_path = os.path.join(log_dir, 'happypanda_debug.log')

    @staticmethod
    def _set_requests_certificate():
        """Set requests certificate, if exist by set environment variable."""
        if os.path.exists('cacert.pem'):
            os.environ["REQUESTS_CA_BUNDLE"] = os.path.join(
                os.getcwd(), "cacert.pem")

    def _get_window_stylesheet(self):
        """create window style.

        Returns:
            str:Style.
        """
        d_style = app_constants.default_stylesheet_path
        u_style = app_constants.user_stylesheet_path
        if len(u_style) is not 0:
            try:
                style_file = QFile(u_style)
                self.log_i('Select userstyle: OK')
            except:
                style_file = QFile(d_style)
                self.log_i('Select defaultstyle: OK')
        else:
            style_file = QFile(d_style)
            self.log_i('Select defaultstyle: OK')

        style_file.open(QFile.ReadOnly)
        style = str(style_file.readAll(), 'utf-8')
        return style

    def _start_main_window(self, conn, application):
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
        style = self._get_window_stylesheet()
        application.setStyleSheet(style)

        # create temp dir.
        try:
            os.mkdir(app_constants.temp_dir)
            create_tempdir_succed = True
        except FileExistsError:  # NOQA
            create_tempdir_succed = False
        try:
            if not create_tempdir_succed:
                for root, dirs, files in scandir.walk('temp', topdown=False):
                    map(lambda x: os.remove(os.path.join(root, x)), files)
                    map(lambda x: os.rmdir(os.path.join(root, x)), dirs)
        except:
            self.log.exception("Empty temp: FAIL")
        self.log_d('Create temp: OK')

        if self.is_test:
            return application, window

        return application.exec_()

    @staticmethod
    def _init_logger(log_path, debug_log_path, dev, debug):
        """init logging.

        Args:
            log_path: Path for log file for normal logging.
            debug_log_path: Path for log file for debug logging.
            dev (bool): Set logging for dev mode.
            debug (bool: Set logging for debug mode.)
        """
        log_handlers = []
        log_level = logging.INFO
        if dev:
            log_handlers.append(logging.StreamHandler())
        if debug:
            print("{} created at \n{}".format(
                os.path.basename(debug_log_path),
                os.path.dirname(debug_log_path)
            ))
            file_logger = logging.FileHandler(debug_log_path, encoding='utf-8')
            log_handlers.append(file_logger)
            log_level = logging.DEBUG
            app_constants.DEBUG = True
        else:
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

    def _set_logger(self):
        """set the logger setting."""
        self._init_logging(
            log_path=self.log_path,
            debug_log_path=self.debug_log_path,
            dev=self.args.dev,
            debug=self.args.dev
        )
        # set logger for this file
        self.log = logging.getLogger(__name__)
        self.log_i = self.log.info
        self.log_d = self.log.debug
        # log_w = log.warning
        # log_e = log.error
        self.log_c = self.log.critical

    def _uncaught_exceptions(self, ex_type, ex, tb):
        """Uncaught exceptions.

        Args:
            ex_type:Exception type.
            Exception:Exception
            tb:traceback

        """
        self.log_c(''.join(traceback.format_tb(tb)))
        self.log_c('{}: {}'.format(ex_type, ex))
        traceback.print_exception(ex_type, ex, tb)

    def _disable_custom_excepthook(self, exceptions):
        """change system except hook."""
        if not exceptions:
            sys.excepthook = self._uncaught_exceptions

    def _handle_database(self, application):
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
            self.log_d('Init DB Conn: OK')
            self.log_i("DB Version: {}".format(db_constants.REAL_DB_VERSION))
        except:
            self.log_c('Invalid database')
            self.log.exception('Database connection failed!')
            text = 'Invalid database'
            info_text = "Do you want to create new database?"
            if _confirm_with_user(text=text, informative_text=info_text):
                pass
            else:
                application.exit()
                self.log_d('Normal Exit App: OK')
                sys.exit()
        return conn

    def _db_upgrade(self, application):
        """upgrade database.

        Args:
            application(PyQt5.QtWidgets.QApplication):Application.

        Returns:
            int:Returns code.
        """
        self.log_d('Database connection failed')
        text = 'Incompatible database!'
        info_text = (
            "Do you want to upgrade to newest version? "
            "It shouldn't take more than a second. "
            "Don't start a new instance!"
        )
        if _confirm_with_user(text=text, informative_text=info_text):
            utils.backup_database()

            db_p = db_constants.DB_PATH
            db.add_db_revisions(db_p)
            conn = db.init_db()

            return self._start_main_window(conn, application=application)
        else:
            application.exit()
            self.log_d('Normal Exit App: OK')
            return 0

    def run(self):
        """run the program.

        Returns:
            int: Return code.
        """
        self._set_requests_certificate()
        self._set_logger()
        self._disable_custom_excepthook(exceptions=self.args.exceptions)

        if app_constants.FORCE_HIGH_DPI_SUPPORT:
            self.log_i("Enabling high DPI display support")
            os.environ.putenv("QT_DEVICE_PIXEL_RATIO", "auto")

        effects = [
            Qt.UI_AnimateCombo, Qt.UI_FadeMenu, Qt.UI_AnimateMenu,
            Qt.UI_AnimateTooltip, Qt.UI_FadeTooltip]
        for effect in effects:
            QApplication.setEffectEnabled(effect)

        application = QApplication(sys.argv)
        application.setOrganizationName('Pewpews')
        application.setOrganizationDomain('https://github.com/Pewpews/happypanda')
        application.setApplicationName('Happypanda')
        application.setApplicationDisplayName('Happypanda')
        application.setApplicationVersion('v{}'.format(app_constants.vs))
        application.setAttribute(Qt.AA_UseHighDpiPixmaps)

        self.log_i('Starting Happypanda...'.format(app_constants.vs))
        if self.args.debug:
            self.log_i('Running in debug mode'.format(app_constants.vs))
            sys.displayhook = pprint.pprint
        app_constants.load_icons()
        self.log_i('Happypanda Version {}'.format(app_constants.vs))
        self.log_i('OS: {} {}\n'.format(platform.system(), platform.release()))

        conn = self._handle_database(application)
        if conn:
            return self._start_main_window(conn=conn, application=application)
        else:
            return self._db_upgrade(application=application)


def start(test=False):
    """start the program.

    Args:
        test(bool): Start program in test mode.
    Returns:
        int: Return code.
    """
    """
    NOTE: diff with origin/packaging

    General:

    - Import will be put on top.
    - unused will be removed.

    For this module.

    - app_constants.APP_RESTART_CODE is not set to hardcoded random number `-123456789`
    - body of start function is moved to Program Class
    - setting log and debug log is put into __init__ from Program class.
     - it is not using db_constants.CONTENT_DIR as used on origin/package, or using different place
       based on OS which used on the release before 1.0. It will be handled by package appdirs.
     - therefore there is module metadata (__author__), which will be temporary used
       - __name__ is not used as application name metadata, so it will not conflict with ifmain
         block. for hardcoded string will be used(`'happypanda'`).
       and maybe in the future will be moved so other module can use it as well.
    - setting request certificate is moved to _set_requests_certificate method of Program class,
      which run on Program class's run method.
    - __init__ method of Program class will be used to set variable without logic, other method
      which have side effect will be run on run method.
    - setting logging will be moved to _set_logger method of Program class and init_logging
      function from custom_logging module.
      - _set_logging is the entire logging initiation for this program.
      - init_logging set the basic log config for entire program.
      - the rest of the code on _set_logging is used only on this module.
    - disable custom excepthook has it's own method (_disable_custom_excepthook) and it's inner
      function is also moved to its own method (_uncaught_exceptions).
    - initiating the database handler is started at _handle_database method, which will return the
      connection if succes.
      - the message box is moved to make it usable for other (see _confirm_with_user function)
      method/function which will use it.
    - start_main_window inner function on start function on origin/packaging is moved to
      _start_main_window method of Program class.
      - application which used on that inner function is used as input argument.
      - WINDOW variable is changed to window for pep8
      - get style sheet code is moved to _get_window_stylesheet method of Program class.
      - create temp dir code is simplified.
        - double try except is flattened
        - when existing temp dir exists, the file and folder is not cleaned with double for-loop,
          instead use for-loop and map.
    - db_upgrade inner function on start function on origin/packaging is moved to
      _db_upgrade method of Program class.
      - becaues of _start_main_window which require application object as input, this method is
        also require application as input argument.
      - the modified message box which is used when starting window is also used here.
    """
    args = parse_args(sys.argv[1:])
    program = Program(args=args, test=test)
    return program.run()


def main():
    """main function."""
    """
    NOTE: diff with origin/packaging

    - current_exit_code is still `0` but it set as APP_RESTART_CODE.
    """
    current_exit_code = app_constants.APP_RESTART_CODE
    while current_exit_code == app_constants.APP_RESTART_CODE:
        current_exit_code = start()
    sys.exit(current_exit_code)

if __name__ == '__main__':
    main()

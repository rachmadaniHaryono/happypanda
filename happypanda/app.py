"""App module.

It contain app window.

NOTE: diff with origin/packaging

- import sorting
- one line per import
- use relative import.
- change in __init__ of AppWindow
  - add login_check_invoker attribute.
  - add check_site_logins method.
    - LoginCheck class is moved to its own file (check_login_obj).
      - the filename is based on convention (underscore splitted words and added obj for QObject)
      - the class also add `Object` for convention.
  - several method execution on __init__ is splitter for better viewing.
    - also reordering the execution, so it is grouped better (e.g. db_startup attribute is
      initiated after _db_startup_thread.start method executed.)
  - initUI method is changed to init_ui.
- change in set_shortcuts method
  - QShortcut is not set to a variable, as the variable will not be used anywhere and will raise
    pep8 error
  - change to apply pep8 (shorter line lengths)
- change in init_watchers method.
  - remove_gallery inner function is moved to class method (_remove_gallery)
  - update_gallery inner function is moved to class method (_update_gallery)
  - created inner function is moved using lambda
  - modified inner function is moved using lambda
  - moved inner function is moved to class method (_watcher_moved)
  - deleted inner function is moved to class method (_watcher_deleted)
- change in startup method
  - normalize_first_time inner function is moved to class method (normalize_first_time)
  - done inner function is moved to class method (_startup_done)
    - Abandomnent message removed.
  - old method when checkingapp_constants.FIRST_TIME_LEVEL is kept there.
- change in init_ui method
  - initUI method is changed to init_ui (stated on __init__ changes)
  - refresh_view inner function is moved using lambda
  - code between `Create statusbar: OK` and `Create system tray: OK` is moved to
    create_system_tray method.
    - tray_icon inner function is moved to class method (inner_function)
  - code between `Create system tray: OK` and `Show window: OK` is moved to
    show_window method.
    - the content is modified to follow the current commit.
- change in init_ui method
  - upd_chk inner class is moved to its own file (update_checker_obj)
    - the filename is based on convention (underscore splitted words and added obj for QObject)
    - the class name is changed from upd_chk to UpdateCheckerObject for convention
  - check_update inner_function is moved to class method (_check_update_func)
- change in get_metadata method.
  - code between fetch_instance variable initiation and setting fetch_instance's galleries
    attribute is move to get_metadata_gallery method.
    - if-else loop is simplified.
  - done inner function is moved to _get_metadata_done method.
    - added fetch_instance to link fetch_instance from function to method
    - GalleryContextMenu inner class on done function is moved to its own file
      (gallery_context_menu)
      - app_instance parameter is added to link app instance to class
- change in init_toolbar method.
  - inner function is moved to its own method.


"""
# """
# This file is part of Happypanda.
# Happypanda is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# any later version.
# Happypanda is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with Happypanda.  If not, see <http://www.gnu.org/licenses/>.
# """
import logging
import os
import random
import sys
import traceback

import requests
import qtawesome as qta
from PyQt5.QtCore import (
    QSize,
    QThread,
    QTimer,
    Qt,
    pyqtSignal,
)
from PyQt5.QtGui import (
    QIcon,
    QKeySequence,
)
from PyQt5.QtWidgets import (
    QAction,
    QCompleter,
    QFileDialog,
    QGraphicsBlurEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QShortcut,
    QSizePolicy,
    QSystemTrayIcon,
    QTableWidget,
    QTableWidgetItem,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from . import (
    app_constants,
    database,
    fetch_obj,
    gallerydb,
    settings,
    settingsdialog,
    utils,
)
#
from .app_bubble import AppBubble
from .app_dialog import AppDialog
from .common_view import CommonView
from .completer_popup_view import CompleterPopupView
from .gallery_model import GalleryModel
from .line_edit import LineEdit
from .manga_views import MangaViews
from .misc import center_widget
from .sidebar_widget_frame import SideBarWidgetFrame
from .single_gallery_choices import SingleGalleryChoices
from .system_tray import SystemTray
from .utils import cleanup_dir
from .watchers import Watchers
# menu
from .gallery_context_menu import GalleryContextMenu
from .sort_menu import SortMenu
# QObject
from .db_activity_checker_obj import DBActivityCheckerObject
from .downloader_obj import DownloaderObject
from .duplicate_check_obj import DuplicateCheckObject
from .login_check_obj import LoginCheckObject
from .scan_dir_obj import ScanDirObject
from .toolbar_tab_manager_obj import ToolbarTabManagerObject
from .update_checker_obj import UpdateCheckerObject
# widget
from .gallery_dialog_widget import GalleryDialogWidget
from .gallery_downloader_widget import GalleryDownloaderWidget
from .gallery_list_view_widget import GalleryListViewWidget
from .notification_overlay_widget import NotificationOverlayWidget
from .spinner_widget import SpinnerWidget
# popup
from .base_popup import BasePopup
from .deleted_popup import DeletedPopup
from .gallery_popup import GalleryPopup
from .modified_popup import ModifiedPopup
from .moved_popup import MovedPopup


log = logging.getLogger(__name__)
""":class:`logging.Logger`: Logger for module."""
log_i = log.info
""":meth:`logging.Logger.info`: Info logger func"""
log_d = log.debug
""":meth:`logging.Logger.debug`: Debug logger func"""
log_w = log.warning
""":meth:`logging.Logger.warning`: Warning logger func"""
log_e = log.error
""":meth:`logging.Logger.error`: Error logger func"""
log_c = log.critical
""":meth:`logging.Logger.critical`: Critical logger func"""


def get_window_size(main_window):
    """get main window size.

    Args:
        main_window(:class:`PyQt5.QtWidgets.QMainWindow`): Window.
    Returns:
        tuple: Tuple of int contain window size.
    """
    props = settings.win_read(main_window, 'AppWindow')
    if props.resize:
        return props.resize
    else:
        return(app_constants.MAIN_W, app_constants.MAIN_H)


class AppWindow(QMainWindow):
    """The application's main window.

    Args:
        disable_excepthook(bool):Disable default excepthook and use custom one.
    Attributes:
        _db_startup_thread(:class:`PyQt5.QtCore.QThread`):Thread for db startup.
        search_timer(:class:`PyQt5.QtCore.QTimer`):Search timeout
        db_activity_checker(:class:`PyQt5.QtCore.pyqtSignal`):Signal for db activity checker.
        duplicate_check_invoker(:class:`PyQt5.QtCore.pyqtSignal`):Signal when duplicate check run.
        admin_db_method_invoker(:class:`PyQt5.QtCore.pyqtSignal`): Signal when method for admin db
            invoked.
        move_listener(:class:`PyQt5.QtCore.pyqtSignal`):Signal when window moved.
        db_startup_invoker(:class:`PyQt5.QtCore.pyqtSignal`):Signal which will be invoked when
            db startup.
        grid_toggle_g_icon(:class:`PyQt5.QtGui.QIcon`):Icon for gallery grid toogle.
        grid_toggle_l_icon(:class:`PyQt5.QtGui.QIcon`):Icon for list grid toogle.
        graphics_blur(:class:`PyQt5.QtWidgets.QGraphicsBlurEffect`):Effect used on main window.
        grid_toggle(:class:`PyQt5.QtWidgets.QToolButton`):Toggle for grid.
        toolbar(:class:`PyQt5.widget.QToolBar`):Toolbar for window.
        get_metadata_fetch_instance(:class:`fetch_obj.FetchObject`):Fetch instance
        g_populate_inst(:class:`.fetch_obj.FetchObject`):Fetch instance to populate gallery.
        admin_db(:class:`.gallerydb.AdminDB`):Admin for db.
        db_startup(:class:`.gallerydb.DatabaseStartup`):Database startup instance.
        watchers(:class:`.watchers.Watchers`):Watcher for window.
        populate_msg_box(:class:`.base_popup.BasePopup`):Message box when populating gallery.
        search_bar(:class:`.line_edit.LineEdit`):Search bar
        notification_bar(:class:`.notification_overlay_widget.NotificationOverlayWidget`):
            Notification bar.
        system_tray(:class:`.system_tray.SystemTray`):Sytem tray for window.
        addition_tab(:class:`.toolbar_tab_manager_obj.ToolbarTabManagerObject`):Additional tab
            for window.
        tab_manager(:class:`.toolbar_tab_manager_obj.ToolbarTabManagerObject`):Tab manager
            for window.
        _g_populate_count(int):Amount of populated gallery.
    """

    move_listener = pyqtSignal()
    login_check_invoker = pyqtSignal()
    db_startup_invoker = pyqtSignal(list)
    duplicate_check_invoker = pyqtSignal(GalleryModel)
    admin_db_method_invoker = pyqtSignal(object)
    db_activity_checker = pyqtSignal()
    graphics_blur = QGraphicsBlurEffect()

    def __init__(self, disable_excepthook=False):
        """init func."""
        super().__init__()
        if not disable_excepthook:
            sys.excepthook = self.excepthook
        # app_constants
        app_constants.GENERAL_THREAD = QThread(self)
        app_constants.GENERAL_THREAD.finished.connect(app_constants.GENERAL_THREAD.deleteLater)
        app_constants.GENERAL_THREAD.start()
        #
        self.check_site_logins()
        # db_startup_thread
        self._db_startup_thread = QThread(self)
        self._db_startup_thread.finished.connect(self._db_startup_thread.deleteLater)
        self._db_startup_thread.start()
        # db_startup
        self.db_startup = gallerydb.DatabaseStartup()
        self.db_startup.moveToThread(self._db_startup_thread)
        self.db_startup.DONE.connect(
            lambda: self.scan_for_new_galleries()
            if app_constants.LOOK_NEW_GALLERY_STARTUP else None)
        self.db_startup_invoker.connect(self.db_startup.startup)
        #
        self.setAcceptDrops(True)
        #
        self.init_ui()
        self.startup()
        QTimer.singleShot(3000, self._check_update)
        self.setFocusPolicy(Qt.NoFocus)
        self.set_shortcuts()
        self.graphics_blur.setParent(self)

    def set_shortcuts(self):
        """Set Shortcut func."""
        # quit
        QShortcut(
            QKeySequence('Ctrl+Q'),
            self,
            self.close
        )
        # prev_view
        QShortcut(
            QKeySequence(QKeySequence.Find),
            self,
            lambda: self.search_bar.setFocus(Qt.ShortcutFocusReason)
        )
        # next_view
        QShortcut(
            QKeySequence(QKeySequence.NextChild),
            self,
            self.switch_display
        )
        # open help content
        QShortcut(
            QKeySequence(QKeySequence.HelpContents),
            self,
            lambda: self._open_web_link('https://github.com/Pewpews/happypanda/wiki')
        )

    def check_site_logins(self):
        """checking logins.

        Need to do this to avoid settings dialog locking up.
        """
        login_check = LoginCheckObject()
        self.login_check_invoker.connect(login_check.check)
        login_check.moveToThread(app_constants.GENERAL_THREAD)
        self.login_check_invoker.emit()

    def _remove_gallery(self, g):
        """remove gallery.

        Args:
            g(:class:`.gallery_model.GalleryMode`):Gallery to be removed.
        """
        index = CommonView.find_index(self.get_current_view(), g.id, True)
        if index:
            CommonView.remove_gallery(self.get_current_view(), [index])
        else:
            log_e('Could not find gallery to remove from watcher')

    def _update_gallery(self, g):
        """update the gallery.

        Args:
            g(:class:`.gallery_model.GalleryModel`):Updated gallery.
        """
        index = CommonView.find_index(self.get_current_view(), g.id)
        if index:
            gal = index.data(GalleryModel.GALLERY_ROLE)
            gal.path = g.path
            gal.chapters = g.chapters
        else:
            log_e('Could not find gallery to update from watcher')
        self.default_manga_view.replace_gallery(g, False)

    def _watcher_deleted(self, path, gallery):
        """function to run when watcher deleted.

        Args:
            path(str): Path of the gallery.
            gallery(:class:`.gallery_model.GalleryModel`): Object gallery.
        """
        d_popup = DeletedPopup(path, gallery, self)
        d_popup.UPDATE_SIGNAL.connect(self._update_gallery)
        d_popup.REMOVE_SIGNAL.connect(self._remove_gallery)

    def _watcher_moved(self, new_path, gallery):
        """watcher moved.

        Args:
            new_path(str): New path for the gallery.
            gallery(:class:`.gallery_model.GalleryModel`): Object gallery.
        """
        mov_popup = MovedPopup(new_path, gallery, self)
        mov_popup.UPDATE_SIGNAL.connect(self._update_gallery)

    def init_watchers(self):
        """init watchers."""
        self.watchers = Watchers()
        self.watchers.gallery_handler.CREATE_SIGNAL.connect(
            lambda path: self.gallery_populate([path]))
        self.watchers.gallery_handler.MODIFIED_SIGNAL.connect(
            lambda path, gallery:
            ModifiedPopup(path, gallery, self)
        )
        self.watchers.gallery_handler.MOVED_SIGNAL.connect(self._watcher_moved)
        self.watchers.gallery_handler.DELETED_SIGNAL.connect(self._watcher_deleted)

    @staticmethod
    def normalize_first_time():
        """normalize for first time."""
        settings.set(app_constants.INTERNAL_LEVEL, 'Application', 'first time level')
        settings.save()

    @staticmethod
    def get_finished_startup_update_text():
        """get update text when startup done."""
        if app_constants.UPDATE_VERSION != app_constants.vs:
            return (
                "Happypanda has been updated!",
                "Don't forget to check out what's new in this version "
                "<a href='https://github.com/Pewpews/happypanda/blob/master/CHANGELOG.md'>"
                "by clicking here!</a>")
        else:
            hello = [
                "Hello!", "Hi!", "Onii-chan!", "Senpai!", "Hisashiburi!", "Welcome!",
                "Okaerinasai!", "Welcome back!", "Hajimemashite!"]
            return (
                "{}".format(random.choice(hello)),
                "Please don't hesitate to report any bugs you find.",
                10
            )

    def _startup_done(self, status=True):
        """Function to run after startup done.

        Args:
            status(bool):Show status or not.
        """
        self.db_startup_invoker.emit(MangaViews.manga_views)

        if app_constants.FIRST_TIME_LEVEL != app_constants.INTERNAL_LEVEL:
            self.normalize_first_time()
        if app_constants.UPDATE_VERSION != app_constants.vs:
            settings.set(app_constants.vs, 'Application', 'version')

        finished_startup_update_text = self.get_finished_startup_update_text()
        self.notif_bubble.update_text(*finished_startup_update_text)

        # NOTE: Abandonment message removed

        if app_constants.ENABLE_MONITOR and \
                app_constants.MONITOR_PATHS and all(app_constants.MONITOR_PATHS):
            self.init_watchers()

        self.download_manager = DownloaderObject()
        app_constants.DOWNLOAD_MANAGER = self.download_manager
        self.download_manager.start_manager(4)

    @staticmethod
    def _reset_default_hen():
        """set default hen url."""
        eh_url = app_constants.DEFAULT_EHEN_URL
        if 'g.e-h' in eh_url or 'http://' in eh_url:
            eh_url_n = 'https://e-hentai.org/'
            settings.set(eh_url_n, 'Web', 'default ehen url')
            settings.save()
            app_constants.DEFAULT_EHEN_URL = eh_url_n

    @staticmethod
    def invoke_first_time_level():
        """invoke first time of certain level."""
        app_constants.INTERNAL_LEVEL = 7
        if app_constants.EXTERNAL_VIEWER_ARGS == '{file}':
            app_constants.EXTERNAL_VIEWER_ARGS = '{$file}'
            settings.set('{$file}', 'Advanced', 'external viewer args')
            settings.save()

    def startup(self):
        """startup func."""
        if app_constants.FIRST_TIME_LEVEL < 5:
            log_i('Invoking first time level {}'.format(5))
            app_constants.INTERNAL_LEVEL = 5
            app_widget = AppDialog(self)
            app_widget.note_info.setText(
                "<font color='red'>IMPORTANT:</font> Application restart is required when done")
            app_widget.restart_info.hide()
            self.admin_db = gallerydb.AdminDB()
            self.admin_db.moveToThread(app_constants.GENERAL_THREAD)
            self.admin_db.DONE.connect(self._startup_done)
            self.admin_db.DONE.connect(
                lambda: app_constants.NOTIF_BAR.add_text("Application requires a restart"))
            self.admin_db.DONE.connect(self.admin_db.deleteLater)
            self.admin_db.DATA_COUNT.connect(app_widget.prog.setMaximum)
            self.admin_db.PROGRESS.connect(app_widget.prog.setValue)
            self.admin_db_method_invoker.connect(self.admin_db.from_v021_to_v022)
            self.admin_db_method_invoker.connect(app_widget.show)
            app_widget.adjustSize()
            db_p = os.path.join(os.path.split(database.db_constants.DB_PATH)[0], 'sadpanda.db')
            self.admin_db_method_invoker.emit(db_p)
        elif app_constants.FIRST_TIME_LEVEL < 7:
            log_i('Invoking first time level {}'.format(7))
            self.invoke_first_time_level()

        self._reset_default_hen

        if not(app_constants.FIRST_TIME_LEVEL < 5):
            self._startup_done()

    def tray_activate(self, r=None):
        """activate tray.

        Args:
            r(:class:`PyQt5.QtWidgets.QSystemTrayIcon.Trigger`):Enabled or disabled trigger.
        """
        if not r or r == QSystemTrayIcon.Trigger:
            self.showNormal()
            self.activateWindow()

    def create_system_tray(self):
        """create system tray."""
        self.system_tray = SystemTray(QIcon(app_constants.APP_ICO_PATH), self)
        app_constants.SYSTEM_TRAY = self.system_tray
        tray_menu = QMenu(self)
        self.system_tray.setContextMenu(tray_menu)
        self.system_tray.setToolTip('Happypanda {}'.format(app_constants.vs))
        tray_quit = QAction('Quit', tray_menu)
        tray_update = tray_menu.addAction('Check for update')
        tray_update.triggered.connect(self._check_update)
        tray_menu.addAction(tray_quit)
        tray_quit.triggered.connect(self.close)
        self.system_tray.show()

        self.system_tray.messageClicked.connect(self.tray_activate)
        self.system_tray.activated.connect(self.tray_activate)

    def show_window(self):
        """show window."""
        self.setCentralWidget(self.center)
        self.setWindowIcon(QIcon(app_constants.APP_ICO_PATH))

        props = settings.win_read(self, 'AppWindow')
        if props.resize:
            x, y = props.resize
            self.resize(x, y)
        else:
            self.resize(app_constants.MAIN_W, app_constants.MAIN_H)

        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        center_widget(self)
        self.init_spinners()
        self.show()

    def create_notification_bar(self):
        """create notification bar."""
        self.notification_bar = NotificationOverlayWidget(self)
        p = self.toolbar.pos()
        self.notification_bar.move(p.x(), p.y() + self.toolbar.height())
        self.notification_bar.resize(self.width())
        self.notif_bubble = AppBubble(self)
        app_constants.NOTIF_BAR = self.notification_bar
        app_constants.NOTIF_BUBBLE = self.notif_bubble

    def init_ui(self):
        """init ui."""
        self.center = QWidget()
        self._main_layout = QHBoxLayout(self.center)
        self._main_layout.setSpacing(0)
        self._main_layout.setContentsMargins(0, 0, 0, 0)

        self.init_stat_bar()

        self.manga_views = {}
        self._current_manga_view = None
        self.default_manga_view = MangaViews(app_constants.ViewType.Default, self, True)
        # refresh view when db startup done.
        self.db_startup.DONE.connect(lambda: self.current_manga_view.sort_model.refresh())
        self.manga_list_view = self.default_manga_view.list_view
        self.manga_table_view = self.default_manga_view.table_view
        self.manga_list_view.gallery_model.STATUSBAR_MSG.connect(self.stat_temp_msg)
        self.manga_list_view.STATUS_BAR_MSG.connect(self.stat_temp_msg)
        self.manga_table_view.STATUS_BAR_MSG.connect(self.stat_temp_msg)

        self.sidebar_list = SideBarWidgetFrame(self)
        self.db_startup.DONE.connect(self.sidebar_list.tags_tree.setup_tags)
        self._main_layout.addWidget(self.sidebar_list)
        self.current_manga_view = self.default_manga_view

        self.download_window = GalleryDownloaderWidget(self)
        self.download_window.hide()

        self.init_toolbar()
        log_d('Create statusbar: OK')
        self.create_system_tray()
        log_d('Create system tray: OK')
        self.show_window()
        log_d('Show window: OK')
        self.create_notification_bar()
        log_d('Create notificationbar: OK')
        log_d('Window Create: OK')

    def _open_web_link(self, url):
        """open web link.

        Args:
            url(str):Url to opn.
        """
        try:
            utils.open_web_link(url)
        except requests.exceptions.ConnectionError:
            self.notification_bar.show()
            self.notification_bar.add_text("Connection error.")
            log_i('Connection error when opening following url:\n{}'.format(url))

    def _check_update_func(self, vs):
        """check update.

        Args:
            vs(str):Version of the program.
        """
        log_i('Received version: {}\nCurrent version: {}'.format(vs, app_constants.vs))
        if vs != app_constants.vs and len(vs) < 10:
            self.notification_bar.begin_show()
            self.notification_bar.add_text(
                "Version {} of Happypanda is available. Click here to update!".format(vs), False)
            self.notification_bar.clicked.connect(
                lambda: utils.open_web_link('https://github.com/Pewpews/happypanda/releases'))
            self.notification_bar.set_clickable(True)
        elif vs != app_constants.vs:
            self.notification_bar.add_text(
                "An error occurred while checking for new version")

    def _check_update(self):
        """check update."""
        self.update_instance = UpdateCheckerObject()
        thread = QThread(self)
        self.update_instance.moveToThread(thread)
        thread.started.connect(self.update_instance.fetch_vs)
        self.update_instance.UPDATE_CHECK.connect(self._check_update_func)
        self.update_instance.UPDATE_CHECK.connect(self.update_instance.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.start()

    def _web_metadata_picker(self, gallery, title_url_list, queue, parent=None):
        """web metadata picker.

        Args:
            gallery(:class:`gallery_model.GalleryModel`):Gallery object.
            title_url_list(list of str):List of title url.
            queue:Queue of the picker process.
            parent:Parent window.
        """
        if not parent:
            parent = self
        text = "Which gallery do you want to extract metadata from?"
        s_gallery_popup = SingleGalleryChoices(gallery, title_url_list, text, parent)
        s_gallery_popup.USER_CHOICE.connect(queue.put)

    def get_metadata_gallery(self, gal):
        """get metadata gallery.

        Args:
            gal(:class:`.gallery_model.GalleryModel`): Single or multiple gallery object.
        Return
            list of :class:`.gallery_model.GalleryModel`:Found metadata.
        """
        if gal and not isinstance(gal, list):
            galleries = [gal]
        elif gal:
            galleries = gal
        elif not gal and app_constants.CONTINUE_AUTO_METADATA_FETCHER:
            galleries = [g for g in self.current_manga_view.gallery_model._data if not g.exed]
        else:
            galleries = self.current_manga_view.gallery_model._data

        if not galleries:
            self.notification_bar.add_text('All galleries has already been processed!')
            return

        return galleries

    def _get_metadata_done(self, status, fetch_instance):
        """function run when get_metada func done.

        Args:
            status(bool or list of bool):Status.
        """
        self.notification_bar.end_show()
        gallerydb.execute(database.db.DBBase.end, True)
        try:
            fetch_instance.deleteLater()
        except RuntimeError:
            pass
        if not isinstance(status, bool):
            galleries = []
            for tup in status:
                galleries.append(tup[0])

            g_popup = GalleryPopup((
                'Fecthing metadata for these galleries failed.' +
                ' Check happypanda.log for details.', galleries
            ), self, menu=GalleryContextMenu, app_instance=self)
            errors = {g[0].id: g[1] for g in status}
            for g_item in g_popup.get_all_items():
                g_item.extra_text.setText(
                    "<font color='red'>{}</font>".format(errors[g_item.gallery.id]))
                g_item.extra_text.show()
            g_popup.graphics_blur.setEnabled(False)
            close_button = g_popup.add_buttons('Close')[0]
            close_button.clicked.connect(g_popup.close)

    def get_metadata(self, gal=None):
        """get metadata.

        Args:
            gal(:class:`.gallery_model.GalleryModel`):Gallery which require metadata.
        """
        if not app_constants.GLOBAL_EHEN_LOCK:
            metadata_spinner = SpinnerWidget(self)
            metadata_spinner.set_text("Metadata")
            metadata_spinner.set_size(55)
            #
            thread = QThread(self)
            thread.setObjectName('App.get_metadata')
            #
            fetch_instance = fetch_obj.FetchObject()
            #
            galleries = self.get_metadata_gallery(gal)
            if not galleries:
                log_d('Gallery is empty when getting metadata.')
                return
            #
            fetch_instance.galleries = galleries

            self.notification_bar.begin_show()
            fetch_instance.moveToThread(thread)

            database.db.DBBase.begin()
            fetch_instance.GALLERY_PICKER.connect(self._web_metadata_picker)
            fetch_instance.GALLERY_EMITTER.connect(
                self.default_manga_view.replace_gallery)
            fetch_instance.AUTO_METADATA_PROGRESS.connect(
                self.notification_bar.add_text)
            thread.started.connect(fetch_instance.auto_web_metadata)
            fetch_instance.FINISHED.connect(
                lambda status: self._get_metadata_done(status, fetch_instance))
            fetch_instance.FINISHED.connect(metadata_spinner.before_hide)
            thread.finished.connect(thread.deleteLater)
            thread.start()
            metadata_spinner.show()
        else:
            self.notif_bubble.update_text("Oops!", "Auto metadata fetcher is already running...")

    def init_stat_bar(self):
        """init status bar."""
        self.status_bar = self.statusBar()
        self.status_bar.setSizeGripEnabled(False)
        self.stat_info = QLabel()
        self.stat_info.setIndent(5)
        self.sort_main = QAction("Asc", self)
        sort_menu = QMenu()
        self.sort_main.setMenu(sort_menu)
        s_by_title = QAction("Title", sort_menu)
        s_by_artist = QAction("Artist", sort_menu)
        sort_menu.addAction(s_by_title)
        sort_menu.addAction(s_by_artist)
        self.status_bar.addPermanentWidget(self.stat_info)
        self.temp_msg = QLabel()
        self.temp_timer = QTimer()

        app_constants.STAT_MSG_METHOD = self.stat_temp_msg

    def stat_temp_msg(self, msg):
        """stat of temp msg.

        Args:
            msg(str):Message.
        """
        self.temp_timer.stop()
        self.temp_msg.setText(msg)
        self.status_bar.addWidget(self.temp_msg)
        self.temp_timer.timeout.connect(self.temp_msg.clear)
        self.temp_timer.setSingleShot(True)
        self.temp_timer.start(5000)

    def stat_row_info(self):
        """stat row info."""
        r = self.current_manga_view.get_current_view().sort_model.rowCount()
        t = self.current_manga_view.get_current_view().gallery_model.rowCount()
        g_l = self.get_current_view().sort_model.current_gallery_list
        if g_l:
            self.stat_info.setText("<b><i>{}</i></b> | Showing {} of {} ".format(g_l.name, r, t))
        else:
            self.stat_info.setText("Showing {} of {} ".format(r, t))

    def set_current_manga_view(self, v):
        """set current manga view."""
        self.current_manga_view = v

    @property
    def current_manga_view(self):
        """Current manga view."""
        return self._current_manga_view

    @current_manga_view.setter
    def current_manga_view(self, new_view):
        if self._current_manga_view:
            self._main_layout.takeAt(1)
        self._current_manga_view = new_view
        self._main_layout.insertLayout(1, new_view.view_layout, 1)
        self.stat_row_info()

    def init_spinners(self):
        """init spinner."""
        # fetching spinner
        self.data_fetch_spinner = SpinnerWidget(self, "center")
        self.data_fetch_spinner.set_size(80)

        self.manga_list_view.gallery_model.ADD_MORE.connect(self.data_fetch_spinner.show)
        self.db_startup.START.connect(self.data_fetch_spinner.show)
        self.db_startup.PROGRESS.connect(self.data_fetch_spinner.set_text)
        self.manga_list_view.gallery_model.ADDED_ROWS.connect(self.data_fetch_spinner.before_hide)
        self.db_startup.DONE.connect(self.data_fetch_spinner.before_hide)

    def search(self, srch_string):
        """search.

        Args:
            srch_string(str):Search string.
        """
        "Args should be Search Enums"
        self.search_bar.setText(srch_string)
        self.search_backward.setVisible(True)
        args = []
        if app_constants.GALLERY_SEARCH_REGEX:
            args.append(app_constants.Search.Regex)
        if app_constants.GALLERY_SEARCH_CASE:
            args.append(app_constants.Search.Case)
        if app_constants.GALLERY_SEARCH_STRICT:
            args.append(app_constants.Search.Strict)
        self.current_manga_view.get_current_view().sort_model.init_search(srch_string, args)
        old_cursor_pos = self._search_cursor_pos[0]
        self.search_bar.end(False)
        if self.search_bar.cursorPosition() != old_cursor_pos + 1:
            self.search_bar.setCursorPosition(old_cursor_pos)

    def switch_display(self):
        """Switch between fav and catalog display."""
        if self.current_manga_view.fav_is_current():
            self.tab_manager.library_btn.click()
        else:
            self.tab_manager.favorite_btn.click()

    def settings(self):
        """setting."""
        sett = settingsdialog.SettingsDialog(self)
        sett.scroll_speed_changed.connect(self.manga_list_view.updateGeometries)

    def _init_toolbar_switch_view(self, fav):
        """switch view.

        Args:
            fav(bool):Is window on fav tab or other.
        """
        if fav:
            self.default_manga_view.get_current_view().sort_model.fav_view()
        else:
            self.default_manga_view.get_current_view().sort_model.catalog_view()

    def _debug_func(self):
        """debug function."""
        print('Gallery model row count: {}'.format(
            self.current_manga_view.gallery_model.rowCount()
        ))
        print('sort model row count: {}'.format(
            self.current_manga_view.sort_model.rowCount()
        ))

    def set_cursor_pos(self, old, new):
        """set cursor post.

        Args:
            old(int):Old post
            new(int):New post
        """
        self._search_cursor_pos[0] = old
        self._search_cursor_pos[1] = new

    def init_toolbar(self):
        """init toolbar."""
        self.toolbar = QToolBar()
        self.toolbar.adjustSize()
        self.toolbar.setWindowTitle("Show")  # text for the contextmenu

        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toolbar.setIconSize(QSize(20, 20))

        spacer_start = QWidget()  # aligns the first actions properly
        spacer_start.setFixedSize(QSize(10, 1))
        self.toolbar.addWidget(spacer_start)

        self.tab_manager = ToolbarTabManagerObject(self.toolbar, self)
        self.tab_manager.favorite_btn.clicked.connect(lambda: self._init_toolbar_switch_view(True))
        self.tab_manager.library_btn.click()
        self.tab_manager.library_btn.clicked.connect(lambda: self._init_toolbar_switch_view(False))

        self.addition_tab = self.tab_manager.addTab(
            "Inbox", app_constants.ViewType.Addition, icon=app_constants.INBOX_ICON)

        gallery_k = QKeySequence('Alt+G')
        new_gallery_k = QKeySequence('Ctrl+N')
        new_galleries_k = QKeySequence('Ctrl+Shift+N')
        new_populate_k = QKeySequence('Ctrl+Alt+N')
        scan_galleries_k = QKeySequence('Ctrl+Alt+S')
        open_random_k = QKeySequence(QKeySequence.Open)
        get_all_metadata_k = QKeySequence('Ctrl+Alt+M')
        gallery_downloader_k = QKeySequence('Ctrl+Alt+D')

        gallery_menu = QMenu()

        # gallery k
        gallery_menu = QMenu()
        gallery_action = QToolButton()
        gallery_action.setIcon(app_constants.PLUS_ICON)
        gallery_action.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        gallery_action.setShortcut(gallery_k)
        gallery_action.setText('Gallery ')
        gallery_action.setPopupMode(QToolButton.InstantPopup)
        gallery_action.setToolTip('Contains various gallery related features')
        gallery_action.setMenu(gallery_menu)

        # new_gallery_k
        add_gallery_icon = QIcon(app_constants.PLUS_ICON)
        gallery_action_add = QAction(add_gallery_icon, "Add a gallery...", self)
        gallery_action_add.triggered.connect(lambda: CommonView.spawn_dialog(self))
        gallery_action_add.setToolTip('Add a single gallery thoroughly')
        gallery_action_add.setShortcut(new_gallery_k)
        gallery_menu.addAction(gallery_action_add)

        # new_galleries_k
        add_more_action = QAction(add_gallery_icon, "Add galleries...", self)
        add_more_action.setStatusTip('Add galleries from different folders')
        add_more_action.setShortcut(new_galleries_k)
        add_more_action.triggered.connect(lambda: self.populate(True))
        gallery_menu.addAction(add_more_action)

        # new_populate_k
        populate_action = QAction(add_gallery_icon, "Populate from directory/archive...", self)
        populate_action.setStatusTip(
            'Populates the DB with galleries from a single folder or archive')
        populate_action.triggered.connect(self.populate)
        populate_action.setShortcut(new_populate_k)
        gallery_menu.addAction(populate_action)

        # separator
        gallery_menu.addSeparator()

        # get_all_metadata_k
        scan_galleries_action = QAction('Scan for new galleries', self)
        scan_galleries_action.setIcon(app_constants.SPINNER_ICON)
        scan_galleries_action.triggered.connect(self.scan_for_new_galleries)
        scan_galleries_action.setStatusTip('Scan monitored folders for new galleries')
        scan_galleries_action.setShortcut(scan_galleries_k)
        gallery_menu.addAction(scan_galleries_action)

        duplicate_check_simple = QAction("Check for duplicate galleries", self)
        duplicate_check_simple.setIcon(app_constants.DUPLICATE_ICON)
        # triggered emits False
        duplicate_check_simple.triggered.connect(lambda: self.duplicate_check())
        gallery_menu.addAction(duplicate_check_simple)

        self.toolbar.addWidget(gallery_action)

        spacer_tool = QWidget()
        spacer_tool.setFixedSize(QSize(5, 1))
        self.toolbar.addWidget(spacer_tool)

        metadata_action = QToolButton()
        metadata_action.setText('Fetch all metadata')
        metadata_action.clicked.connect(self.get_metadata)
        metadata_action.setIcon(app_constants.DOWNLOAD_ICON)
        metadata_action.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        metadata_action.setShortcut(get_all_metadata_k)
        self.toolbar.addWidget(metadata_action)

        spacer_tool2 = QWidget()
        spacer_tool2.setFixedSize(QSize(1, 1))
        self.toolbar.addWidget(spacer_tool2)

        gallery_action_random = QToolButton()
        gallery_action_random.setText("Open random gallery")
        gallery_action_random.clicked.connect(
            lambda: CommonView.open_random_gallery(self.get_current_view()))
        gallery_action_random.setIcon(app_constants.RANDOM_ICON)
        gallery_action_random.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        gallery_action_random.setShortcut(open_random_k)
        self.toolbar.addWidget(gallery_action_random)

        spacer_tool3 = QWidget()
        spacer_tool3.setFixedSize(QSize(1, 1))
        self.toolbar.addWidget(spacer_tool3)

        gallery_downloader = QToolButton()
        gallery_downloader.setText("Downloader")
        gallery_downloader.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        gallery_downloader.clicked.connect(self.download_window.show)
        gallery_downloader.setShortcut(gallery_downloader_k)
        gallery_downloader.setIcon(app_constants.MANAGER_ICON)
        self.toolbar.addWidget(gallery_downloader)

        spacer_tool4 = QWidget()
        spacer_tool4.setFixedSize(QSize(5, 1))
        self.toolbar.addWidget(spacer_tool4)

        # debug specfic code
        if app_constants.DEBUG:
            debug_btn = QToolButton()
            debug_btn.setText("DEBUG BUTTON")
            self.toolbar.addWidget(debug_btn)
            debug_btn.clicked.connect(self._debug_func)

        spacer_middle = QWidget()  # aligns buttons to the right
        spacer_middle.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.toolbar.addWidget(spacer_middle)

        sort_k = QKeySequence('Alt+S')
        sort_action = QToolButton()
        sort_action.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        sort_action.setShortcut(sort_k)
        sort_action.setIcon(app_constants.SORT_ICON_DESC)
        sort_menu = SortMenu(self, self.toolbar, sort_action)
        sort_menu.set_toolbutton_text()
        sort_action.setMenu(sort_menu)
        sort_action.setPopupMode(QToolButton.InstantPopup)
        self.toolbar.addWidget(sort_action)

        sort_menu.new_sort.connect(lambda s: self.set_new_sort(s=s, sort_menu=sort_menu))

        spacer_tool4 = QWidget()
        spacer_tool4.setFixedSize(QSize(5, 1))
        self.toolbar.addWidget(spacer_tool4)

        togle_view_k = QKeySequence('Alt+Space')
        self.grid_toggle_g_icon = app_constants.GRID_ICON
        self.grid_toggle_l_icon = app_constants.LIST_ICON
        self.grid_toggle = QToolButton()
        self.grid_toggle.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.grid_toggle.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.grid_toggle.setShortcut(togle_view_k)
        if self.current_manga_view.current_view == MangaViews.View.List:
            self.grid_toggle.setIcon(self.grid_toggle_l_icon)
        else:
            self.grid_toggle.setIcon(self.grid_toggle_g_icon)
        self.grid_toggle.setObjectName('gridtoggle')
        self.grid_toggle.clicked.connect(self.toggle_view)
        self.toolbar.addWidget(self.grid_toggle)

        spacer_mid2 = QWidget()
        spacer_mid2.setFixedSize(QSize(5, 1))
        self.toolbar.addWidget(spacer_mid2)

        search_options = QToolButton()
        search_options.setIconSize(QSize(15, 15))
        search_options.setPopupMode(QToolButton.InstantPopup)
        self.toolbar.addWidget(search_options)
        search_options.setIcon(app_constants.SEARCH_ICON)
        search_options_menu = QMenu(self)
        search_options.setMenu(search_options_menu)
        case_search_option = search_options_menu.addAction('Case Sensitive')
        case_search_option.setCheckable(True)
        case_search_option.setChecked(app_constants.GALLERY_SEARCH_CASE)
        case_search_option.toggled.connect(self.set_search_case)

        search_options_menu.addSeparator()

        strict_search_option = search_options_menu.addAction('Match whole terms')
        strict_search_option.setCheckable(True)
        strict_search_option.setChecked(app_constants.GALLERY_SEARCH_STRICT)

        regex_search_option = search_options_menu.addAction('Regex')
        regex_search_option.setCheckable(True)
        regex_search_option.setChecked(app_constants.GALLERY_SEARCH_REGEX)

        strict_search_option.toggled.connect(
            lambda b: self.set_search_strict(b=b, regex_search_option=regex_search_option))

        regex_search_option.toggled.connect(
            lambda b: self.set_search_regex(b=b, strict_search_option=strict_search_option))

        self.search_bar = LineEdit()

        remove_txt = self.search_bar.addAction(app_constants.CROSS_ICON, QLineEdit.LeadingPosition)
        refresh_search = self.search_bar.addAction(
            app_constants.REFRESH_ICON, QLineEdit.TrailingPosition)
        refresh_search.triggered.connect(
            self.current_manga_view.get_current_view().sort_model.refresh)
        remove_txt.setVisible(False)
        remove_txt.triggered.connect(self.clear_txt)
        # hide cross
        self.search_bar.textChanged.connect(lambda txt: remove_txt.setVisible(bool(txt)))

        self.search_bar.setObjectName('search_bar')
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(lambda: self.search(self.search_bar.text()))
        self._search_cursor_pos = [0, 0]

        self.search_bar.cursorPositionChanged.connect(self.set_cursor_pos)

        if app_constants.SEARCH_AUTOCOMPLETE:
            completer = QCompleter(self)
            completer_view = CompleterPopupView()
            completer.setPopup(completer_view)
            completer_view._setup()
            completer.setModel(self.manga_list_view.gallery_model)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            completer.setCompletionMode(QCompleter.PopupCompletion)
            completer.setCompletionRole(Qt.DisplayRole)
            completer.setCompletionColumn(app_constants.TITLE)
            completer.setFilterMode(Qt.MatchContains)
            completer.activated[str].connect(lambda a: self.search(a))
            self.search_bar.setCompleter(completer)
            self.search_bar.returnPressed.connect(lambda: self.search(self.search_bar.text()))
        if not app_constants.SEARCH_ON_ENTER:
            self.search_bar.textEdited.connect(lambda: self.search_timer.start(800))
        self.search_bar.setPlaceholderText("Search title, artist, namespace & tags")
        self.search_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.manga_list_view.sort_model.HISTORY_SEARCH_TERM.connect(
            lambda a: self.search_bar.setText(a))
        self.toolbar.addWidget(self.search_bar)

        back_k = QKeySequence(QKeySequence.Back)
        forward_k = QKeySequence(QKeySequence.Forward)

        search_backbutton = QToolButton(self.toolbar)
        search_backbutton.setIcon(app_constants.ARROW_LEFT_ICON)
        search_backbutton.setFixedWidth(20)
        search_backbutton.clicked.connect(self.search_history)
        search_backbutton.setShortcut(back_k)
        self.search_backward = self.toolbar.addWidget(search_backbutton)
        self.search_backward.setVisible(False)
        search_forwardbutton = QToolButton(self.toolbar)
        search_forwardbutton.setIcon(app_constants.ARROW_RIGHT_ICON)
        search_forwardbutton.setFixedWidth(20)
        search_forwardbutton.clicked.connect(lambda: self.search_history(None, False))
        search_forwardbutton.setShortcut(forward_k)
        self.search_forward = self.toolbar.addWidget(search_forwardbutton)
        self.search_forward.setVisible(False)

        spacer_end = QWidget()  # aligns settings action properly
        spacer_end.setFixedSize(QSize(10, 1))
        self.toolbar.addWidget(spacer_end)

        settings_k = QKeySequence("Ctrl+P")

        settings_act = QToolButton(self.toolbar)
        settings_act.setShortcut(settings_k)
        settings_act.setIcon(qta.icon('fa.gear', color='white'))
        settings_act.clicked.connect(self.settings)
        self.toolbar.addWidget(settings_act)

        self.addToolBar(self.toolbar)

    def clear_txt(self):
        """clear text."""
        self.search_bar.setText("")
        self.search_bar.returnPressed.emit()

    @staticmethod
    def set_search_regex(b, strict_search_option):
        if b:
            if strict_search_option.isChecked():
                strict_search_option.toggle()
        app_constants.GALLERY_SEARCH_REGEX = b
        settings.set(b, 'Application', 'allow search regex')
        settings.save()

    @staticmethod
    def set_search_strict(b, regex_search_option):
        if b:
            if regex_search_option.isChecked():
                regex_search_option.toggle()
        app_constants.GALLERY_SEARCH_STRICT = b
        settings.set(b, 'Application', 'gallery search strict')
        settings.save()

    @staticmethod
    def set_search_case(b):
        """set search case.

        Args:
            b (bool): Set search case if True
        """
        app_constants.GALLERY_SEARCH_CASE = b
        settings.set(b, 'Application', 'gallery search case')
        settings.save()

    def set_new_sort(self, s, sort_menu):
        sort_menu.set_toolbutton_text()
        self.current_manga_view.list_view.sort(s)

    def get_current_view(self):
        """get current view."""
        return self.current_manga_view.get_current_view()

    def toggle_view(self):
        """Toggle the current display view."""
        if self.current_manga_view.current_view == MangaViews.View.Table:
            self.current_manga_view.changeTo(self.current_manga_view.m_l_view_index)
            self.grid_toggle.setIcon(self.grid_toggle_l_icon)
        else:
            self.current_manga_view.changeTo(self.current_manga_view.m_t_view_index)
            self.grid_toggle.setIcon(self.grid_toggle_g_icon)

    def search_history(self, _, back=True):  # clicked signal passes a bool
        """search history.

        Args:
            back(bool):Search history backward.
        """
        sort_model = self.manga_list_view.sort_model
        nav = sort_model.PREV if back else sort_model.NEXT
        sort_model.navigate_history(nav)
        if back:
            self.search_forward.setVisible(True)

    def _populate_from_dir(self, msg_box):
        """populate from dir."""
        path = QFileDialog.getExistingDirectory(
            self, "Choose a directory containing your galleries")
        if not path:
            return
        msg_box.close()
        app_constants.OVERRIDE_SUBFOLDER_AS_GALLERY = True
        self.gallery_populate(path, True)

    def _populate_from_arch(self, msg_box):
        """populate from archive."""
        path = QFileDialog.getOpenFileName(
            self, 'Choose an archive containing your galleries', filter=utils.FILE_FILTER)
        path = [path[0]]
        if not all(path) or not path:
            return
        msg_box.close()
        app_constants.OVERRIDE_SUBFOLDER_AS_GALLERY = True
        self.gallery_populate(path, True)

    # TODO: Improve this so that it adds to the gallery dialog,
    # so user can edit data before inserting (make it a choice)
    def populate(self, mixed=None):
        """Populate the database with gallery from local drive.

        Args:
            mixed(bool):Mix the gallery or not.
        """
        if mixed:
            gallery_view = GalleryListViewWidget(self, True)
            gallery_view.SERIES.connect(self.gallery_populate)
            gallery_view.show()
        else:
            msg_box = BasePopup(self)
            l = QVBoxLayout()
            msg_box.main_widget.setLayout(l)
            l.addWidget(QLabel('Directory or Archive?'))
            l.addLayout(msg_box.buttons_layout)

            buttons = msg_box.add_buttons('Directory', 'Archive', 'Close')
            buttons[2].clicked.connect(msg_box.close)
            buttons[0].clicked.connect(lambda: self._populate_from_dir(msg_box=msg_box))
            buttons[1].clicked.connect(lambda: self._populate_from_arch(msg_box=msg_box))
            msg_box.adjustSize()
            msg_box.show()

    def gallery_populate(self, path, validate=False):
        """Scan the given path for gallery to add into the DB.

        Args:
            path(str):Path to be scanned.
            validate(bool):Validate the file or not.
        """
        if len(path) is not 0:
            data_thread = QThread(self)
            data_thread.setObjectName('General gallery populate')
            self.addition_tab.click()
            self.g_populate_inst = fetch_obj.FetchObject()
            self.g_populate_inst.series_path = path
            self._g_populate_count = 0

            fetch_spinner = SpinnerWidget(self)
            fetch_spinner.set_size(60)
            fetch_spinner.set_text("Populating")
            fetch_spinner.show()

            def finished(status):
                """finished.

                Args:
                    status(str):Status to be show when it gallery_populate finished.
                """
                fetch_spinner.hide()
                if not status:
                    log_e('Populating DB from gallery folder: Nothing was added!')
                    self.notif_bubble.update_text(
                        "Gallery Populate",
                        "<font color='red'>Nothing was added. "
                        "Check happypanda_log for details..</font>")

            def skipped_gs(s_list):
                """Skipped galleries.

                Args:
                    s_list(:class:`.gallery_model.GalleryModel`):List of skipped gallery.
                """
                msg_box = QMessageBox(self)
                msg_box.setIcon(QMessageBox.Question)
                msg_box.setText('Do you want to view skipped paths?')
                msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                msg_box.setDefaultButton(QMessageBox.No)
                if msg_box.exec_() == QMessageBox.Yes:
                    list_wid = QTableWidget(self)
                    list_wid.setAttribute(Qt.WA_DeleteOnClose)
                    list_wid.setRowCount(len(s_list))
                    list_wid.setColumnCount(2)
                    list_wid.setAlternatingRowColors(True)
                    list_wid.setEditTriggers(list_wid.NoEditTriggers)
                    list_wid.setHorizontalHeaderLabels(['Reason', 'Path'])
                    list_wid.setSelectionBehavior(list_wid.SelectRows)
                    list_wid.setSelectionMode(list_wid.SingleSelection)
                    list_wid.setSortingEnabled(True)
                    list_wid.verticalHeader().hide()
                    list_wid.setAutoScroll(False)
                    for x, g in enumerate(s_list):
                        list_wid.setItem(x, 0, QTableWidgetItem(g[1]))
                        list_wid.setItem(x, 1, QTableWidgetItem(g[0]))
                    list_wid.resizeColumnsToContents()
                    list_wid.setWindowTitle('{} skipped paths'.format(len(s_list)))
                    list_wid.setWindowFlags(Qt.Window)
                    list_wid.resize(900, 400)

                    list_wid.doubleClicked.connect(
                        lambda i: utils.open_path(
                            list_wid.item(i.row(), 1).text(), list_wid.item(i.row(), 1).text())
                    )
                    list_wid.show()

            self.g_populate_inst.moveToThread(data_thread)
            # a_progress
            self.g_populate_inst.PROGRESS.connect(
                lambda prog:
                fetch_spinner.set_text("Populating... {}/{}".format(prog, self._g_populate_count))
            )
            # set_count
            self.g_populate_inst.DATA_COUNT.connect(
                lambda c:
                setattr(self, '_g_populate_count', c)
            )
            # add_to_model
            self.g_populate_inst.LOCAL_EMITTER.connect(
                lambda gallery:
                self.addition_tab.view.add_gallery(gallery, app_constants.KEEP_ADDED_GALLERIES)
            )
            self.g_populate_inst.FINISHED.connect(finished)
            self.g_populate_inst.FINISHED.connect(self.g_populate_inst.deleteLater)
            self.g_populate_inst.SKIPPED.connect(skipped_gs)
            data_thread.finished.connect(data_thread.deleteLater)
            data_thread.started.connect(self.g_populate_inst.local)
            data_thread.start()
            log_i('Populating DB from directory/archive')

    @staticmethod
    def _scan_finished():
        """scan finished."""
        log_d('Set [SCANNING_FOR_GALLERIES]:False')
        app_constants.SCANNING_FOR_GALLERIES = False

    def scan_for_new_galleries(self):
        """scan for new galleries."""
        available_folders = app_constants.ENABLE_MONITOR and \
            app_constants.MONITOR_PATHS and all(app_constants.MONITOR_PATHS)
        if available_folders and not app_constants.SCANNING_FOR_GALLERIES:
            app_constants.SCANNING_FOR_GALLERIES = True
            self.notification_bar.add_text("Scanning for new galleries...")
            log_i('Scanning for new galleries...')
            try:
                new_gall_spinner = SpinnerWidget(self)
                new_gall_spinner.set_text("Gallery Scan")
                new_gall_spinner.show()
                #
                thread = QThread(self)
                self.scan_inst = ScanDirObject(
                    self.addition_tab.view, self.addition_tab, app_window=self)
                self.scan_inst.moveToThread(thread)
                self.scan_inst.finished.connect(self._scan_finished)
                self.scan_inst.finished.connect(new_gall_spinner.before_hide)
                thread.started.connect(self.scan_inst.scan_dirs)
                thread.finished.connect(new_gall_spinner.before_hide)
                thread.start()
            except:
                self.notification_bar.add_text(
                    'An error occured while attempting to scan for new galleries. '
                    'Check happypanda.log.')
                log.exception('An error occured while attempting to scan for new galleries.')
                app_constants.SCANNING_FOR_GALLERIES = False
        else:
            self.notification_bar.add_text(
                "Please specify directory in settings to scan for new galleries!")

    def dragEnterEvent(self, event):  # NOQA
        """drag enter event.

        Args:
            event:Event"""

        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event):  # NOQA
        """drop event.

        Args:
            event:Event
        """
        acceptable = []
        unaccept = []
        for u in event.mimeData().urls():
            path = u.toLocalFile()
            if os.path.isdir(path) or path.endswith(utils.ARCHIVE_FILES):
                acceptable.append(path)
            else:
                unaccept.append(path)
        log_i('Acceptable dropped items: {}'.format(len(acceptable)))
        log_i('Unacceptable dropped items: {}'.format(len(unaccept)))
        log_d('Dropped items: {}\n{}'.format(acceptable, unaccept).encode(errors='ignore'))
        if acceptable:
            self.notification_bar.add_text('Adding dropped items...')
            log_i('Adding dropped items')
            l = len(acceptable) == 1
            f_item = acceptable[0]
            if f_item.endswith(utils.ARCHIVE_FILES):
                f_item = utils.check_archive(f_item)
            else:
                f_item = utils.recursive_gallery_check(f_item)
            f_item_l = len(f_item) < 2
            subfolder_as_c = not app_constants.SUBFOLDER_AS_GALLERY
            if l and subfolder_as_c or l and f_item_l:
                g_d = GalleryDialogWidget(self, acceptable[0])
                g_d.show()
            else:
                self.gallery_populate(acceptable, True)
            event.accept()
        else:
            text = 'File not supported' if len(unaccept) < 2 else 'Files not supported'
            self.notification_bar.add_text(text)

        if unaccept:
            self.notification_bar.add_text('Some unsupported files did not get added')
        super().dropEvent(event)

    def resizeEvent(self, event):  # NOQA
        """resize event.

        Args:
            event:Event"""
        try:
            self.notification_bar.resize(event.size().width())
        except AttributeError:
            pass
        self.move_listener.emit()
        return super().resizeEvent(event)

    def moveEvent(self, event):  # NOQA
        """move event.

        Args:
            event:Event"""
        self.move_listener.emit()
        return super().moveEvent(event)

    def showEvent(self, event):  # NOQA
        """show event.

        Args:
            event:Event"""

        return super().showEvent(event)

    @staticmethod
    def clean_up_db():
        """clean up db."""
        try:
            log_i("Analyzing database...")
            gallerydb.GalleryDB.analyze()
            log_i("Closing database...")
            gallerydb.GalleryDB.close()
        except:
            pass

    @staticmethod
    def clean_up_temp_dir():
        """clean temp up dir."""
        try:
            cleanup_dir(path='temp')
            log_d('Flush temp on exit: OK')
        except:
            log.exception('Flush temp on exit: FAIL')

    def cleanup_exit(self):
        """clean up when exit.

        Args:
            event:Event
        Returns:
            int:Return code.

        Return code are following::

            0:Clean up succes(normal exit).
            1:User close despite db activity detected(force exit).
            2:User don't want to close the window(ignore exit).
        """
        self.system_tray.hide()
        # watchers
        try:
            self.watchers.stop_all()
        except AttributeError:
            pass
        # settings
        settings.set(self.manga_list_view.current_sort, 'General', 'current sort')
        settings.set(app_constants.IGNORE_PATHS, 'Application', 'ignore paths')
        if not self.isMaximized():
            settings.win_save(self, 'AppWindow')
        # temp dir
        self.clean_up_temp_dir()
        # DB
        self.clean_up_db()
        self.download_window.close()

        # check if there is db activity
        if not gallerydb.method_queue.empty():
            db_activity = DBActivityCheckerObject()
            db_spinner = SpinnerWidget(self)
            self.db_activity_checker.connect(db_activity.check)
            db_activity.moveToThread(app_constants.GENERAL_THREAD)
            db_activity.FINISHED.connect(db_spinner.close)
            db_spinner.set_text('DB Activity')
            db_spinner.show()
            self.db_activity_checker.emit()
            msg_box = QMessageBox(self)
            msg_box.setText('Database activity detected!')
            msg_box.setInformativeText(
                "Closing now might result in data loss." +
                " Do you still want to close?\n"
                "(Wait for the activity spinner to hide before closing)")
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box.setDefaultButton(QMessageBox.No)
            if msg_box.exec_() == QMessageBox.Yes:
                return 1
            else:
                return 2
        else:
            return 0

    def duplicate_check(self, simple=True):
        """check duplicate.

        Args:
            simple(bool):Use simple duplicate check method.
        """
        try:
            self.duplicate_check_invoker.disconnect()
        except TypeError:
            pass
        mode = 'simple' if simple else 'advanced'
        log_i('Checking for duplicates in mode: {}'.format(mode))
        notifbar = app_constants.NOTIF_BAR
        notifbar.add_text('Checking for duplicates...')
        duplicate_spinner = SpinnerWidget(self)
        duplicate_spinner.set_text("Duplicate Check")
        duplicate_spinner.show()
        #
        dup_tab = self.tab_manager.addTab("Duplicate", app_constants.ViewType.Duplicate)
        dup_tab.view.set_delete_proxy(self.default_manga_view.gallery_model)
        #
        self._d_checker = DuplicateCheckObject(notifbar=notifbar)
        self._d_checker.moveToThread(app_constants.GENERAL_THREAD)
        self._d_checker.found_duplicates.connect(
            lambda t: dup_tab.view.add_gallery(t, record_time=True))
        self._d_checker.finished.connect(dup_tab.click)
        self._d_checker.finished.connect(self._d_checker.deleteLater)
        self._d_checker.finished.connect(duplicate_spinner.before_hide)
        if simple:
            self.duplicate_check_invoker.connect(self._d_checker.check_simple)
        self.duplicate_check_invoker.emit(self.default_manga_view.gallery_model)

    def excepthook(self, ex_type, ex, tb):
        """except hook.

        Args:
            ex_type:Exception type.
            ex:Exception.
            tb:Traceback.
        """
        w = AppDialog(self, AppDialog.MESSAGE)
        w.show()
        log_c(''.join(traceback.format_tb(tb)))
        log_c('{}: {}'.format(ex_type, ex))
        traceback.print_exception(ex_type, ex, tb)

    def closeEvent(self, event):  # NOQA
        """close event.

        Args:
            event:Event
        """

        r_code = self.cleanup_exit()
        if r_code == 1:
            log_d('Force Exit App: OK')
            super().closeEvent(event)
        elif r_code == 2:
            log_d('Ignore Exit App')
            event.ignore()
        else:
            log_d('Normal Exit App: OK')
            super().closeEvent(event)

if __name__ == '__main__':
    raise NotImplementedError("Unit testing not implemented yet!")

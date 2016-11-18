"""App module.

It contain app window.
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
import sys
import logging
import os
import traceback

import requests
from PyQt5.QtCore import (
    QSize,
    QThread,
    QTimer,
    Qt,
    pyqtSignal,
)
from PyQt5.QtGui import (
    QCursor,
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

try:
    import app_constants
    import misc
    import gallery
    import io_misc
    import settingsdialog
    import gallerydialog
    import fetch
    import gallerydb
    import settings
    import pewnet
    import utils
    import misc_db
    import database
    from duplicate_check import DuplicateCheck
    from update_check import UpdateChecker
    from db_activity_check import DBActivityChecker
    from scan_dir import ScanDir
    from gallery_context_menu import GalleryContextMenu
    from misc_app import (
        invoke_first_time_level,
        normalize_first_time,
        get_finished_startup_update_text,
        set_search_case,
        clean_up_temp_dir,
        clean_up_db,
        set_tool_button_attribute,
        set_action_attribute,
    )
except ImportError:
    from . import (
        app_constants,
        misc,
        gallery,
        io_misc,
        settingsdialog,
        gallerydialog,
        fetch,
        gallerydb,
        settings,
        pewnet,
        utils,
        misc_db,
        database,
    )
    from .duplicate_check import DuplicateCheck
    from .update_check import UpdateChecker
    from .db_activity_check import DBActivityChecker
    from .scan_dir import ScanDir
    from .gallery_context_menu import GalleryContextMenu
    from .misc_app import (
        invoke_first_time_level,
        normalize_first_time,
        get_finished_startup_update_text,
        set_search_case,
        clean_up_temp_dir,
        clean_up_db,
        set_tool_button_attribute,
        set_action_attribute,
    )

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
        get_metadata_fetch_instance(:class:`fetch.Fetch`):Fetch instance
        g_populate_inst(:class:`.fetch.Fetch`):Fetch instance to populate gallery.
        admin_db(:class:`.gallerydb.AdminDB`):Admin for db.
        db_startup(:class:`.gallerydb.DatabaseStartup`):Database startup instance.
        watchers(:class:`.io_misc.Watchers`):Watcher for window.
        populate_msg_box(:class:`.misc.BasePopup`):Message box when populating gallery.
        search_bar(:class:`.misc.LineEdit`):Search bar
        notification_bar(:class:`.misc.NotificationOverlay`):Notification bar.
        system_tray(:class:`.misc.SystemTray`):Sytem tray for window.
        addition_tab(:class:`.misc_db.ToolbarTabManager`):Additional tab for window.
        tab_manager(:class:`.misc_db.ToolbarTabManager`):Tab manager for window.
        _g_populate_count(int):Amount of populated gallery.
    """

    move_listener = pyqtSignal()
    db_startup_invoker = pyqtSignal(list)
    duplicate_check_invoker = pyqtSignal(gallery.GalleryModel)
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
        # in class function
        self.init_ui()
        self.startup()
        QTimer.singleShot(3000, self._check_update)
        self.setFocusPolicy(Qt.NoFocus)
        self.set_shortcuts()
        self.graphics_blur.setParent(self)

    def set_shortcuts(self):
        """Set Shortcut func."""
        shortcut_keys_data = [
            # quit
            [
                QKeySequence('Ctrl+Q'),
                self,
                self.close
            ],
            # prev_view
            [
                QKeySequence(QKeySequence.Find),
                self,
                lambda: self.search_bar.setFocus(Qt.ShortcutFocusReason)
            ],
            # next_view
            [
                QKeySequence(QKeySequence.NextChild),
                self,
                self.switch_display
            ],
            # open help content
            [
                QKeySequence(QKeySequence.HelpContents),
                self,
                lambda: self._open_web_link('https://github.com/Pewpews/happypanda/wiki')
            ],

        ]
        for data in shortcut_keys_data:
            QShortcut(*data)

    def _remove_gallery(self, g):
        """remove gallery.

        Args:
            g(:class:`.gallery.GalleryMode`):Gallery to be removed.
        """
        index = gallery.CommonView.find_index(self.get_current_view(), g.id, True)
        if index:
            gallery.CommonView.remove_gallery(self.get_current_view(), [index])
        else:
            log_e('Could not find gallery to remove from watcher')

    def _update_gallery(self, g):
        """update the gallery.

        Args:
            g(:class:`.gallery.GalleryModel`):Updated gallery.
        """
        index = gallery.CommonView.find_index(self.get_current_view(), g.id)
        if index:
            gal = index.data(gallery.GalleryModel.GALLERY_ROLE)
            gal.path = g.path
            gal.chapters = g.chapters
        else:
            log_e('Could not find gallery to update from watcher')
        self.default_manga_view.replace_gallery(g, False)

    def _watcher_deleted(self, path, gallery):
        """function to run when watcher deleted.

        Args:
            path(str): Path of the gallery.
            gallery(:class:`.gallery.GalleryModel`): Object gallery.
        """
        d_popup = io_misc.DeletedPopup(path, gallery, self)
        d_popup.UPDATE_SIGNAL.connect(self._update_gallery)
        d_popup.REMOVE_SIGNAL.connect(self._remove_gallery)

    def _watcher_moved(self, new_path, gallery):
        """watcher moved.

        Args:
            new_path(str): New path for the gallery.
            gallery(:class:`.gallery.GalleryModel`): Object gallery.
        """
        mov_popup = io_misc.MovedPopup(new_path, gallery, self)
        mov_popup.UPDATE_SIGNAL.connect(self._update_gallery)

    def init_watchers(self):
        """init watchers."""
        self.watchers = io_misc.Watchers()
        self.watchers.gallery_handler.CREATE_SIGNAL.connect(
            lambda path: self.gallery_populate([path]))
        self.watchers.gallery_handler.MODIFIED_SIGNAL.connect(
            lambda path, gallery:
            io_misc.ModifiedPopup(path, gallery, self)
        )
        self.watchers.gallery_handler.MOVED_SIGNAL.connect(self._watcher_moved)
        self.watchers.gallery_handler.DELETED_SIGNAL.connect(self._watcher_deleted)

    def _startup_done(self, status=True):
        """Function to run after startup done.

        Args:
            status(bool):Show status or not.
        """
        self.db_startup_invoker.emit(gallery.MangaViews.manga_views)
        normalize_first_time()
        finished_startup_update_text = get_finished_startup_update_text()
        self.notif_bubble.update_text(*finished_startup_update_text)
        if app_constants.ENABLE_MONITOR and \
                app_constants.MONITOR_PATHS and all(app_constants.MONITOR_PATHS):
            self.init_watchers()
        self.download_manager = pewnet.Downloader()
        app_constants.DOWNLOAD_MANAGER = self.download_manager
        self.download_manager.start_manager(4)

    def startup(self):
        """startup func."""
        if app_constants.FIRST_TIME_LEVEL < 5:
            log_i('Invoking first time level {}'.format(5))
            app_constants.INTERNAL_LEVEL = 5
            app_widget = misc.AppDialog(self)
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
            invoke_first_time_level()
            self._startup_done()
        else:
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
        self.system_tray = misc.SystemTray(QIcon(app_constants.APP_ICO_PATH), self)
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

        window_size = get_window_size(self)
        self.resize(*window_size)
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        misc.centerWidget(self)
        self.init_spinners()
        self.show()

    def create_notification_bar(self):
        """create notification bar."""
        self.notification_bar = misc.NotificationOverlay(self)
        p = self.toolbar.pos()
        self.notification_bar.move(p.x(), p.y() + self.toolbar.height())
        self.notification_bar.resize(self.width())
        self.notif_bubble = misc.AppBubble(self)
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
        self.default_manga_view = gallery.MangaViews(app_constants.ViewType.Default, self, True)
        self.db_startup.DONE.connect(lambda: self.current_manga_view.sort_model.refresh())
        self.manga_list_view = self.default_manga_view.list_view
        self.manga_table_view = self.default_manga_view.table_view
        self.manga_list_view.gallery_model.STATUSBAR_MSG.connect(self.stat_temp_msg)
        self.manga_list_view.STATUS_BAR_MSG.connect(self.stat_temp_msg)
        self.manga_table_view.STATUS_BAR_MSG.connect(self.stat_temp_msg)

        self.sidebar_list = misc_db.SideBarWidget(self)
        self.db_startup.DONE.connect(self.sidebar_list.tags_tree.setup_tags)
        self._main_layout.addWidget(self.sidebar_list)
        self.current_manga_view = self.default_manga_view

        self.download_window = io_misc.GalleryDownloaderWidget(self)
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
        self.update_instance = UpdateChecker()
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
            gallery(gallery.GalleryModel):Gallery object.
            title_url_list(list of str):List of title url.
            queue:Queue of the picker process.
            parent:Parent window.
        """
        if not parent:
            parent = self
        text = "Which gallery do you want to extract metadata from?"
        s_gallery_popup = misc.SingleGalleryChoices(gallery, title_url_list, text, parent)
        s_gallery_popup.USER_CHOICE.connect(queue.put)

    def get_metadata_gallery(self, gal):
        """get metadata gallery.

        Args:
            gal(:class:`.gallery.GalleryModel`): Single or multiple gallery object.
        Return
            list of :class:`.gallery.GalleryModel`:Found metadata.
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
            self.notification_bar.add_text('Looks like we\'ve already gone through all galleries!')
            return
        return galleries

    def _get_metadata_done(self, status):
        """function run when get_metada func done.

        Args:
            status(bool or list of bool):Status.
        """
        self.notification_bar.end_show()
        gallerydb.execute(database.db.DBBase.end, True)
        try:
            self.fetch_instance.deleteLater()
        except RuntimeError:
            pass
        if not isinstance(status, bool):
            galleries = []
            for tup in status:
                galleries.append(tup[0])

            g_popup = io_misc.GalleryPopup((
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
            gal(:class:`.gallery.GalleryModel`):Gallery which require metadata.
        """
        if not app_constants.GLOBAL_EHEN_LOCK:
            metadata_spinner = misc.Spinner(self)
            metadata_spinner.set_text("Metadata")
            metadata_spinner.set_size(55)
            thread = QThread(self)
            thread.setObjectName('App.get_metadata')
            self.get_metadata_fetch_instance = fetch.Fetch()
            galleries = self.get_metadata_gallery(gal)
            if not galleries:
                return
            self.get_metadata_fetch_instance.galleries = galleries

            self.notification_bar.begin_show()
            self.get_metadata_fetch_instance.moveToThread(thread)

            database.db.DBBase.begin()
            self.get_metadata_fetch_instance.GALLERY_PICKER.connect(self._web_metadata_picker)
            self.get_metadata_fetch_instance.GALLERY_EMITTER.connect(
                self.default_manga_view.replace_gallery)
            self.get_metadata_fetch_instance.AUTO_METADATA_PROGRESS.connect(
                self.notification_bar.add_text)
            thread.started.connect(self.get_metadata_fetch_instance.auto_web_metadata)
            self.get_metadata_fetch_instance.FINISHED.connect(self._get_metadata_done)
            self.get_metadata_fetch_instance.FINISHED.connect(metadata_spinner.before_hide)
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
        self.data_fetch_spinner = misc.Spinner(self, "center")
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

    def _switch_view(self, fav):
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
        print(self.current_manga_view.gallery_model.rowCount())
        print(self.current_manga_view.sort_model.rowCount())

    def _set_cursor_pos(self, old, new):
        """set cursor post.

        Args:
            old(int):Old pos
            new(int):New pos
        """
        self._search_cursor_pos[0] = old
        self._search_cursor_pos[1] = new

    def init_toolbar(self):
        """init toolbar."""
        self.toolbar = QToolBar()
        self.toolbar.adjustSize()
        self.toolbar.setWindowTitle("Show")  # text for the contextmenu
        # self.toolbar.setStyleSheet("QToolBar {border:0px}") # make it user defined?
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toolbar.setIconSize(QSize(20, 20))

        spacer_start = QWidget()  # aligns the first actions properly
        spacer_start.setFixedSize(QSize(10, 1))
        self.toolbar.addWidget(spacer_start)

        self.tab_manager = misc_db.ToolbarTabManager(self.toolbar, self)
        self.tab_manager.favorite_btn.clicked.connect(lambda: self._switch_view(True))
        self.tab_manager.library_btn.click()
        self.tab_manager.library_btn.clicked.connect(lambda: self._switch_view(False))

        self.addition_tab = self.tab_manager.addTab("Inbox", app_constants.ViewType.Addition)

        gallery_menu = QMenu()

        # gallery k
        gallery_action = set_tool_button_attribute(
            tool_button=QToolButton(),
            shortcut=QKeySequence('Alt+G'),
            text='Gallery',
            popup_mode=QToolButton.InstantPopup,
            tooltip='Contains various gallery related features',
            menu=gallery_menu
        )

        add_gallery_icon = QIcon(app_constants.PLUS_PATH)
        # new_gallery_k
        gallery_action_add = set_action_attribute(
            action=QAction(add_gallery_icon, "Add single gallery...", self),
            triggered_connect_function=lambda: gallery.CommonView.spawn_dialog(self),
            tool_tip='Add a single gallery thoroughly',
            shortcut=QKeySequence('Ctrl+N'),
        )
        gallery_menu.addAction(gallery_action_add)

        # new_galleries_k
        add_more_action = set_action_attribute(
            action=QAction(add_gallery_icon, "Add galleries...", self),
            triggered_connect_function=lambda: self.populate(True),
            shortcut=QKeySequence('Ctrl+Shift+N'),
            status_tip='Add galleries from different folders',
        )
        gallery_menu.addAction(add_more_action)

        # new_populate_k
        populate_action = set_action_attribute(
            action=QAction(add_gallery_icon, "Populate from directory/archive...", self),
            triggered_connect_function=self.populate,
            shortcut=QKeySequence('Ctrl+Alt+N'),
            status_tip='Populates the DB with galleries from a single folder or archive',
        )
        gallery_menu.addAction(populate_action)
        gallery_menu.addSeparator()

        # get_all_metadata_k
        metadata_action = set_action_attribute(
            action=QAction('Get metadata for all galleries', self),
            triggered_connect_function=self.get_metadata,
            shortcut=QKeySequence('Ctrl+Alt+M'),
        )
        gallery_menu.addAction(metadata_action)

        # scan_galleries_k
        scan_galleries_action = set_action_attribute(
            action=QAction('Scan for new galleries', self),
            triggered_connect_function=self.scan_for_new_galleries,
            shortcut=QKeySequence('Ctrl+Alt+S'),
            status_tip='Scan monitored folders for new galleries',
        )
        gallery_menu.addAction(scan_galleries_action)

        open_random_k = QKeySequence(QKeySequence.Open)
        gallery_action_random = gallery_menu.addAction("Open random gallery")
        gallery_action_random.triggered.connect(
            lambda: gallery.CommonView.open_random_gallery(self.get_current_view()))
        gallery_action_random.setShortcut(open_random_k)
        self.toolbar.addWidget(gallery_action)

        misc_action_menu = QMenu()

        # tools_k
        misc_action = set_tool_button_attribute(
            tool_button=QToolButton(),
            text='Tools',
            shortcut=QKeySequence('Alt+T'),
            popup_mode=QToolButton.InstantPopup,
            tooltip="Contains misc. features",
            menu=misc_action_menu
        )

        # gallery_downloader_k
        gallery_downloader = set_action_attribute(
            action=QAction("Gallery Downloader", misc_action_menu),
            triggered_connect_function=self.download_window.show,
            shortcut=QKeySequence('Ctrl+Alt+D'),
        )
        misc_action_menu.addAction(gallery_downloader)

        duplicate_check_simple = set_action_attribute(
            action=QAction("Simple Duplicate Finder", misc_action_menu),
            triggered_connect_function=lambda: self.duplicate_check(),  # triggered emits False
        )
        misc_action_menu.addAction(duplicate_check_simple)

        self.toolbar.addWidget(misc_action)

        # debug specfic code
        if app_constants.DEBUG:
            debug_btn = QToolButton()
            debug_btn.setText("DEBUG BUTTON")
            self.toolbar.addWidget(debug_btn)
            debug_btn.clicked.connect(self._debug_func)

        spacer_middle = QWidget()  # aligns buttons to the right
        spacer_middle.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.toolbar.addWidget(spacer_middle)

        sort_menu = misc.SortMenu(self, self.toolbar)
        sort_menu.new_sort.connect(lambda s: self.current_manga_view.list_view.sort(s))
        # sort_k
        sort_action = set_tool_button_attribute(
            tool_button=QToolButton(),
            shortcut=QKeySequence('Alt+S'),
            popup_mode=QToolButton.InstantPopup,
            icon=QIcon(app_constants.SORT_PATH),
            menu=sort_menu
        )
        self.toolbar.addWidget(sort_action)

        togle_view_k = QKeySequence('Alt+Space')
        self.grid_toggle_g_icon = QIcon(app_constants.GRID_PATH)
        self.grid_toggle_l_icon = QIcon(app_constants.LIST_PATH)
        self.grid_toggle = QToolButton()
        self.grid_toggle.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.grid_toggle.setShortcut(togle_view_k)
        if self.current_manga_view.current_view == gallery.MangaViews.View.List:
            self.grid_toggle.setIcon(self.grid_toggle_l_icon)
        else:
            self.grid_toggle.setIcon(self.grid_toggle_g_icon)
        self.grid_toggle.setObjectName('gridtoggle')
        self.grid_toggle.clicked.connect(self.toggle_view)
        self.toolbar.addWidget(self.grid_toggle)

        spacer_mid2 = QWidget()
        spacer_mid2.setFixedSize(QSize(5, 1))
        self.toolbar.addWidget(spacer_mid2)

        self.search_bar = misc.LineEdit()
        search_options = self.search_bar.addAction(
            QIcon(app_constants.SEARCH_OPTIONS_PATH), QLineEdit.TrailingPosition)
        search_options_menu = QMenu(self)
        search_options.triggered.connect(lambda: search_options_menu.popup(QCursor.pos()))
        search_options.setMenu(search_options_menu)
        case_search_option = search_options_menu.addAction('Case Sensitive')
        case_search_option.setCheckable(True)
        case_search_option.setChecked(app_constants.GALLERY_SEARCH_CASE)

        case_search_option.toggled.connect(set_search_case)

        strict_search_option = search_options_menu.addAction('Match whole terms')
        strict_search_option.setCheckable(True)
        strict_search_option.setChecked(app_constants.GALLERY_SEARCH_STRICT)

        regex_search_option = search_options_menu.addAction('Regex')
        regex_search_option.setCheckable(True)
        regex_search_option.setChecked(app_constants.GALLERY_SEARCH_REGEX)

        def set_search_strict(b):
            if b and regex_search_option.isChecked():
                regex_search_option.toggle()
            app_constants.GALLERY_SEARCH_STRICT = b
            settings.set(b, 'Application', 'gallery search strict')
            settings.save()

        strict_search_option.toggled.connect(set_search_strict)

        def set_search_regex(b):
            if b and strict_search_option.isChecked():
                strict_search_option.toggle()
            app_constants.GALLERY_SEARCH_REGEX = b
            settings.set(b, 'Application', 'allow search regex')
            settings.save()

        regex_search_option.toggled.connect(set_search_regex)

        self.search_bar.setObjectName('search_bar')
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(lambda: self.search(self.search_bar.text()))
        self._search_cursor_pos = [0, 0]

        self.search_bar.cursorPositionChanged.connect(self._set_cursor_pos)

        if app_constants.SEARCH_AUTOCOMPLETE:
            completer = QCompleter(self)
            completer_view = misc.CompleterPopupView()
            completer.setPopup(completer_view)
            completer_view._setup()
            completer.setModel(self.manga_list_view.gallery_model)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            completer.setCompletionMode(QCompleter.PopupCompletion)
            completer.setCompletionRole(Qt.DisplayRole)
            completer.setCompletionColumn(app_constants.TITLE)
            completer.setFilterMode(Qt.MatchContains)
            self.search_bar.setCompleter(completer)
            self.search_bar.returnPressed.connect(lambda: self.search(self.search_bar.text()))
        if not app_constants.SEARCH_ON_ENTER:
            self.search_bar.textEdited.connect(lambda: self.search_timer.start(800))
        self.search_bar.setPlaceholderText("Search title, artist, namespace & tags")
        self.search_bar.setMinimumWidth(400)
        self.search_bar.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.manga_list_view.sort_model.HISTORY_SEARCH_TERM.connect(
            lambda a: self.search_bar.setText(a))
        self.toolbar.addWidget(self.search_bar)

        # back_k
        search_backbutton = set_tool_button_attribute(
            tool_button=QToolButton(self.toolbar),
            shortcut=QKeySequence(QKeySequence.Back),
            text=u'\u25C0',
            fixed_width=15,
            clicked_connect_func=self._search_history
        )
        self.search_backward = self.toolbar.addWidget(search_backbutton)
        self.search_backward.setVisible(False)

        # forward_k
        search_forwardbutton = set_tool_button_attribute(
            tool_button=QToolButton(self.toolbar),
            shortcut=QKeySequence(QKeySequence.Forward),
            text=u'\u25B6',
            fixed_width=15,
            clicked_connect_func=lambda: self.search_history(None, False),
        )
        self.search_forward = self.toolbar.addWidget(search_forwardbutton)
        self.search_forward.setVisible(False)

        spacer_end = QWidget()  # aligns settings action properly
        spacer_end.setFixedSize(QSize(10, 1))
        self.toolbar.addWidget(spacer_end)

        settings_act = set_tool_button_attribute(
            tool_button=QToolButton(self.toolbar),
            shortcut=QKeySequence("Ctrl+P"),
            icon=QIcon(app_constants.SETTINGS_PATH),
            clicked_connect_func=self.settings
        )
        self.toolbar.addWidget(settings_act)

        spacer_end2 = QWidget()  # aligns About action properly
        spacer_end2.setFixedSize(QSize(5, 1))
        self.toolbar.addWidget(spacer_end2)
        self.addToolBar(self.toolbar)

    def get_current_view(self):
        """get current view."""
        return self.current_manga_view.get_current_view()

    def toggle_view(self):
        """Toggle the current display view."""
        if self.current_manga_view.current_view == gallery.MangaViews.View.Table:
            self.current_manga_view.changeTo(self.current_manga_view.m_l_view_index)
            self.grid_toggle.setIcon(self.grid_toggle_l_icon)
        else:
            self.current_manga_view.changeTo(self.current_manga_view.m_t_view_index)
            self.grid_toggle.setIcon(self.grid_toggle_g_icon)

    def _search_history(self, _, back=True):  # clicked signal passes a bool
        """search history.

        Args:
            back(bool):Search history backward.
        """
        sort_model = self.manga_list_view.sort_model
        nav = sort_model.PREV if back else sort_model.NEXT
        sort_model.navigate_history(nav)
        if back:
            self.search_forward.setVisible(True)

    def _populate_from_dir(self):
        """populate from dir."""
        path = QFileDialog.getExistingDirectory(
            self, "Choose a directory containing your galleries")
        if not path:
            return
        self.populate_msg_box.close()
        app_constants.OVERRIDE_SUBFOLDER_AS_GALLERY = True
        self.gallery_populate(path, True)

    def _populate_from_arch(self):
        """populate from archive."""
        path = QFileDialog.getOpenFileName(
            self, 'Choose an archive containing your galleries', filter=utils.FILE_FILTER)
        path = [path[0]]
        if not all(path) or not path:
            return
        self.populate_msg_box.close()
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
            gallery_view = misc.GalleryListView(self, True)
            gallery_view.SERIES.connect(self.gallery_populate)
            gallery_view.show()
        else:
            self.populate_msg_box = misc.BasePopup(self)
            l = QVBoxLayout()
            self.populate_msg_box.main_widget.setLayout(l)
            l.addWidget(QLabel('Directory or Archive?'))
            l.addLayout(self.populate_msg_box.buttons_layout)
            buttons = self.populate_msg_box.add_buttons('Directory', 'Archive', 'Close')
            buttons[2].clicked.connect(self.populate_msg_box.close)
            buttons[0].clicked.connect(self._populate_from_dir)
            buttons[1].clicked.connect(self._populate_from_arch)
            self.populate_msg_box.adjustSize()
            self.populate_msg_box.show()

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
            self.g_populate_inst = fetch.Fetch()
            self.g_populate_inst.series_path = path
            self._g_populate_count = 0

            fetch_spinner = misc.Spinner(self)
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
                    s_list(:class:`.gallery.GalleryModel`):List of skipped gallery.
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

    def scan_for_new_galleries(self):
        """scan for new galleries."""
        available_folders = app_constants.ENABLE_MONITOR and \
            app_constants.MONITOR_PATHS and all(app_constants.MONITOR_PATHS)
        if available_folders and not app_constants.SCANNING_FOR_GALLERIES:
            app_constants.SCANNING_FOR_GALLERIES = True
            self.notification_bar.add_text("Scanning for new galleries...")
            log_i('Scanning for new galleries...')
            try:
                new_gall_spinner = misc.Spinner(self)
                new_gall_spinner.set_text("Gallery Scan")
                new_gall_spinner.show()

                thread = QThread(self)
                scan_inst = ScanDir(
                    self.addition_tab.view, self.addition_tab, app_window=self)
                scan_inst.moveToThread(thread)

                scan_inst.finished.connect(
                    lambda:
                    setattr(app_constants, 'SCANNING_FOR_GALLERIES', False)
                )
                scan_inst.finished.connect(new_gall_spinner.before_hide)
                thread.started.connect(scan_inst.scan_dirs)
                thread.finished.connect(thread.deleteLater)
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
                g_d = gallerydialog.GalleryDialog(self, acceptable[0])
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
        clean_up_temp_dir()
        # DB
        clean_up_db()
        self.download_window.close()

        # check if there is db activity
        if not gallerydb.method_queue.empty():
            db_activity = DBActivityChecker()
            db_spinner = misc.Spinner(self)
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
        duplicate_spinner = misc.Spinner(self)
        duplicate_spinner.set_text("Duplicate Check")
        duplicate_spinner.show()
        dup_tab = self.tab_manager.addTab("Duplicate", app_constants.ViewType.Duplicate)
        dup_tab.view.set_delete_proxy(self.default_manga_view.gallery_model)

        self._d_checker = DuplicateCheck(notifbar=notifbar)
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
        w = misc.AppDialog(self, misc.AppDialog.MESSAGE)
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

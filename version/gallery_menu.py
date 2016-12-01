"""menu for gallery."""
import functools
import logging
import os

from PyQt5.QtCore import (
    Qt,
    pyqtSignal,
)
from PyQt5.QtWidgets import (
    QMenu,
    QTableView,
    QAction,
    QFileDialog,
)

try:
    from archive_file import ArchiveFile
    from chapter_add_widget import ChapterAddWidget
    from executors import Executors
    import app_constants
    import gallerydb
    import settings
    import utils
except ImportError:
    from .archive_file import ArchiveFile
    from .chapter_add_widget import ChapterAddWidget
    from .executors import Executors
    from . import (
        app_constants,
        gallerydb,
        settings,
        utils,
    )

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class GalleryMenu(QMenu):
    """GalleryMenu."""

    delete_galleries = pyqtSignal(bool)
    edit_gallery = pyqtSignal(object, object)

    def __init__(self, view, index, sort_model, app_window, selected_indexes=None):  # NOQA
        """__init__."""
        super().__init__(app_window)
        self.parent_widget = app_window
        self.view = view
        self.sort_model = sort_model
        self.index = index
        self.gallery = index.data(Qt.UserRole + 1)
        self.selected = selected_indexes
        if self.view.view_type == app_constants.ViewType.Default:
            if not self.selected:
                favourite_act = self.addAction(
                    'Favorite', lambda: self.parent_widget.manga_list_view.favorite(self.index))
                favourite_act.setCheckable(True)
                if self.gallery.fav:
                    favourite_act.setChecked(True)
                    favourite_act.setText('Unfavorite')
                else:
                    favourite_act.setChecked(False)
            else:
                favourite_act = self.addAction(
                    'Favorite selected', self.favourite_select)
                favourite_act.setCheckable(True)
                f = []
                for idx in self.selected:
                    if idx.data(Qt.UserRole + 1).fav:
                        f.append(True)
                    else:
                        f.append(False)
                if all(f):
                    favourite_act.setChecked(True)
                    favourite_act.setText('Unfavorite selected')
                else:
                    favourite_act.setChecked(False)
        elif self.view.view_type == app_constants.ViewType.Addition:

            # F841: assigned but never used.
            # send_to_lib = self.addAction('Send to library', self.send_to_lib)
            self.addAction('Send to library', self.send_to_lib)
            # F841: assigned but never used.
            # add_to_ignore = self.addAction( 'Ignore and remove', self.add_to_ignore)
            self.addAction('Ignore and remove', self.add_to_ignore)
        self.addSeparator()
        if not self.selected and isinstance(view, QTableView):
            chapters_menu = self.addAction('Chapters')
            open_chapters = QMenu(self)
            chapters_menu.setMenu(open_chapters)
            for number, chap in enumerate(self.gallery.chapters, 1):
                chap_action = QAction(
                    "Open chapter {}".format(number),
                    open_chapters,
                    triggered=functools.partial(chap.open)
                )
                open_chapters.addAction(chap_action)
        if self.selected:
            # F841: assigned but never used.
            # open_f_chapters = self.addAction( 'Open first chapters', self.open_first_chapters)
            self.addAction('Open first chapters', self.open_first_chapters)

        if self.view.view_type != app_constants.ViewType.Duplicate:
            if not self.selected:
                # F841: assigned but never used.
                # add_chapters = self.addAction('Add chapters', self.add_chapters)
                self.addAction('Add chapters', self.add_chapters)
            if self.view.view_type == app_constants.ViewType.Default:
                add_to_list_txt = "Add selected to list" if self.selected else "Add to list"
                add_to_list = self.addAction(add_to_list_txt)
                add_to_list_menu = QMenu(self)
                add_to_list.setMenu(add_to_list_menu)
                for g_list in sorted(app_constants.GALLERY_LISTS):
                    add_to_list_menu.addAction(
                        g_list.name, functools.partial(self.add_to_list, g_list))
        self.addSeparator()
        if not self.selected:
            # F841: assigned but never used.
            # get_metadata = self.addAction(
            # 'Get metadata',
            # lambda: self.parent_widget.get_metadata( index.data(Qt.UserRole + 1)))
            self.addAction(
                'Get metadata',
                lambda:
                self.parent_widget.get_metadata(index.data(Qt.UserRole + 1))
            )
        else:
            gals = []
            for idx in self.selected:
                gals.append(idx.data(Qt.UserRole + 1))
            self.addAction(
                'Get metadata for selected',
                lambda: self.parent_widget.get_metadata(gals)
            )
        self.addSeparator()
        self.addAction(
            'Edit',
            lambda: self.edit_gallery.emit(
                self.parent_widget, self.index.data(Qt.UserRole + 1)
                if not self.selected else [idx.data(Qt.UserRole + 1) for idx in self.selected]
            )
        )
        #
        self._add_op_folder_actions()
        #
        if self.index.data(Qt.UserRole + 1).link and not self.selected:
            self.addAction('Open URL', self.op_link)
        if self.selected and all([idx.data(Qt.UserRole + 1).link for idx in self.selected]):
            self.addAction('Open URLs', lambda: self.op_link(True))

        remove_act = self.addAction('Remove')
        remove_menu = QMenu(self)
        remove_act.setMenu(remove_menu)
        if self.view.view_type == app_constants.ViewType.Default:
            if self.sort_model.current_gallery_list:
                remove_f_g_list_txt = \
                    "Remove selected from list" if self.selected else "Remove from list"
                remove_menu.addAction(
                    remove_f_g_list_txt, self.remove_from_list)
        if not self.selected:
            remove_menu.addAction(
                'Remove gallery', lambda: self.delete_galleries.emit(False))
            remove_ch = remove_menu.addAction('Remove chapter')
            remove_ch_menu = QMenu(self)
            remove_ch.setMenu(remove_ch_menu)
            for number, chap_number in enumerate(range(len(
                    self.index.data(Qt.UserRole + 1).chapters)), 1):
                chap_action = QAction(
                    "Remove chapter {}".format(number),
                    remove_ch_menu,
                    triggered=functools.partial(
                        self.parent_widget.manga_list_view.del_chapter, index, chap_number
                    )
                )
                remove_ch_menu.addAction(chap_action)
        else:
            remove_menu.addAction(
                'Remove selected', lambda: self.delete_galleries.emit(False))
        remove_menu.addSeparator()
        if not self.selected:
            remove_menu.addAction(
                'Remove and delete files', lambda: self.delete_galleries.emit(True))
        else:
            remove_menu.addAction(
                'Remove selected and delete files', lambda: self.delete_galleries.emit(True))
        self.addSeparator()
        advanced = self.addAction('Advanced')
        adv_menu = QMenu(self)
        advanced.setMenu(adv_menu)
        if not self.selected:
            adv_menu.addAction(
                'Change cover...', self.change_cover)

        if self.selected:
            allow_metadata_count = 0
            for i in self.selected:
                if i.data(Qt.UserRole + 1).exed:
                    allow_metadata_count += 1
            self.allow_metadata_exed = allow_metadata_count >= len(
                self.selected) // 2
        else:
            self.allow_metadata_exed = False if not self.gallery.exed else True

        if self.selected:
            allow_metadata_txt = (
                "Include selected in auto metadata fetch"
                if self.allow_metadata_exed else "Exclude selected in auto metadata fetch"
            )
        else:
            allow_metadata_txt = (
                "Include in auto metadata fetch" if self.allow_metadata_exed
                else "Exclude in auto metadata fetch"
            )
        adv_menu.addAction(allow_metadata_txt, self.allow_metadata_fetch)

    @classmethod
    def _add_op_folder_actions(cls):
        """add op folder actions."""
        text = 'folder' if not cls.index.data(Qt.UserRole + 1).is_archive else 'archive'
        show_in_folder_info = 'Show in folder'
        if not cls.selected:
            cls.addAction('Open {}'.format(text), cls.op_folder)
            cls.addAction(show_in_folder_info, lambda: cls.op_folder(containing=True))
        else:
            text += 's'
            show_in_folder_info += 's'
            cls.addAction('Open {}'.format(text), lambda: cls.op_folder(True))
            cls.addAction(show_in_folder_info, lambda: cls.op_folder(True, True))

    def add_to_ignore(self):
        """add_to_ignore."""
        if self.selected:
            gs = self.selected
        else:
            gs = [self.index]
        galleries = [idx.data(Qt.UserRole + 1) for idx in gs]

        paths = set()
        for g in galleries:
            for chap in g.chapters:
                if not chap.in_archive:
                    paths.add(chap.path)
                else:
                    paths.add(g.path)
        app_constants.IGNORE_PATHS.extend(paths)

        settings.set(app_constants.IGNORE_PATHS, 'Application', 'ignore paths')
        self.delete_galleries.emit(False)

    def send_to_lib(self):
        """send_to_lib."""
        if self.selected:
            gs = self.selected
        else:
            gs = [self.index]
        galleries = [idx.data(Qt.UserRole + 1) for idx in gs]
        rows = len(galleries)
        self.view.gallery_model._gallery_to_remove.extend(galleries)
        self.view.gallery_model.removeRows(
            self.view.gallery_model.rowCount() - rows, rows)
        self.parent_widget.default_manga_view.add_gallery(galleries)
        for g in galleries:
            gallerydb.execute(
                gallerydb.GalleryDB.modify_gallery, True, g.id, view=g.view)

    def allow_metadata_fetch(self):
        """allow_metadata_fetch."""
        exed = 0 if self.allow_metadata_exed else 1
        if self.selected:
            for idx in self.selected:
                g = idx.data(Qt.UserRole + 1)
                g.exed = exed
                gallerydb.execute(
                    gallerydb.GalleryDB.modify_gallery, True, g.id, {'exed': exed})
        else:
            self.gallery.exed = exed
            gallerydb.execute(
                gallerydb.GalleryDB.modify_gallery, True, self.gallery.id, {'exed': exed})

    def add_to_list(self, g_list):
        """add_to_list."""
        galleries = []
        if self.selected:
            for idx in self.selected:
                galleries.append(idx.data(Qt.UserRole + 1))
        else:
            galleries.append(self.gallery)
        g_list.add_gallery(galleries)

    def remove_from_list(self):
        """remove_from_list."""
        self.sort_model.current_gallery_list
        if self.selected:
            g_ids = []
            for idx in self.selected:
                g_ids.append(idx.data(Qt.UserRole + 1).id)
        else:
            g_ids = self.gallery.id
        self.sort_model.current_gallery_list.remove_gallery(g_ids)
        self.sort_model.init_search(self.sort_model.current_term)

    def favourite_select(self):
        """favourite_select."""
        for idx in self.selected:
            self.parent_widget.manga_list_view.favorite(idx)

    def change_cover(self):
        """change_cover."""
        gallery = self.index.data(Qt.UserRole + 1)
        log_i('Attempting to change cover of {}'.format(
            gallery.title.encode(errors='ignore')))
        if gallery.is_archive:
            try:
                zip = ArchiveFile(gallery.path)
            except utils.app_constants.CreateArchiveFail:
                app_constants.NOTIF_BAR.add_text(
                    'Attempt to change cover failed. Could not create archive.')
                return
            path = zip.extract_all()
        else:
            path = gallery.path

        new_cover = QFileDialog.getOpenFileName(
            self, 'Select a new gallery cover',
            filter='Image {}'.format(utils.IMG_FILTER),
            directory=path
        )[0]
        if new_cover and new_cover.lower().endswith(utils.IMG_FILES):
            gallerydb.GalleryDB.clear_thumb(gallery.profile)
            Executors.generate_thumbnail(
                gallery, img=new_cover, on_method=gallery.set_profile)
            gallery.reset_profile()
            log_i('Changed cover successfully!')

    def open_first_chapters(self):
        """open_first_chapters."""
        txt = "Opening first chapters of selected galleries"
        app_constants.STAT_MSG_METHOD(txt)
        for idx in self.selected:
            idx.data(Qt.UserRole + 1).chapters[0].open(False)

    def op_link(self, select=False):
        """op_link."""
        if select:
            for x in self.selected:
                gal = x.data(Qt.UserRole + 1)
                utils.open_web_link(gal.link)
        else:
            utils.open_web_link(self.index.data(Qt.UserRole + 1).link)

    def op_folder(self, select=False, containing=False):
        """op_folder."""
        if select:
            for x in self.selected:
                text = (
                    'Opening archives...' if self.index.data(Qt.UserRole + 1).is_archive
                    else 'Opening folders...'
                )
                text = 'Opening containing folders...' if containing else text
                self.view.STATUS_BAR_MSG.emit(text)
                gal = x.data(Qt.UserRole + 1)
                path = os.path.split(gal.path)[0] if containing else gal.path
                if containing:
                    utils.open_path(path, gal.path)
                else:
                    utils.open_path(path)
        else:
            text = (
                'Opening archive...' if self.index.data(Qt.UserRole + 1).is_archive
                else 'Opening folder...'
            )
            text = 'Opening containing folder...' if containing else text
            self.view.STATUS_BAR_MSG.emit(text)
            gal = self.index.data(Qt.UserRole + 1)
            path = os.path.split(gal.path)[0] if containing else gal.path
            if containing:
                utils.open_path(path, gal.path)
            else:
                utils.open_path(path)

    def add_chapters(self):
        """add_chapters."""
        def add_chdb(chaps_container):
            """add_chdb."""
            gallery = self.index.data(Qt.UserRole + 1)
            log_i('Adding new chapter for {}'.format(
                gallery.title.encode(errors='ignore')))
            gallerydb.execute(gallerydb.ChapterDB.add_chapters_raw,
                              False, gallery.id, chaps_container)
        ch_widget = ChapterAddWidget(self.index.data(
            Qt.UserRole + 1), self.parent_widget)
        ch_widget.CHAPTERS.connect(add_chdb)
        ch_widget.show()

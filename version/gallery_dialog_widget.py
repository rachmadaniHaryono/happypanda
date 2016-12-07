"""gallery dialog module."""
import os
import threading
import logging
from datetime import datetime

from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDesktopWidget,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from PyQt5.QtCore import (
    QDate,
    QThread,
    QTimer,
    Qt,
)

try:
    from app_constants import ARCHIVE_FILES, FILE_FILTER
    from clicked_label import ClickedLabel
    from completer_text_edit import CompleterTextEdit
    from fetch_obj import FetchObject
    from gcompleter import GCompleter
    from utils import tag_to_string
    import app_constants
    import database
    import gallerydb
    import utils
except ImportError:
    from .app_constants import ARCHIVE_FILES, FILE_FILTER
    from .clicked_label import ClickedLabel
    from .completer_text_edit import CompleterTextEdit
    from .fetch_obj import FetchObject
    from .gcompleter import GCompleter
    from .utils import tag_to_string
    from . import (
        app_constants,
        database,
        gallerydb,
        utils,
    )

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


def _set_gallery_specific_setting(cls, attr, cls_attr, gallery, def_val, constant_attr):
    """set gallery specific_setting."""
    g = gallery[0]
    if all(map(lambda x: getattr(x, attr) == getattr(g, attr), gallery)):
        self_attr = getattr(cls, cls_attr)
        if not cls._find_combobox_match(self_attr, getattr(g, attr), def_val):
            cls._find_combobox_match(
                self_attr, getattr(app_constants, constant_attr), def_val)
        self_attr.g_check.setChecked(True)


def _set_gallery_constant_setting(widget, widget_attr, gallery_attr, constant_attr, def_val):
    """set gallery constant setting."""
    if not widget._find_combobox_match(widget_attr, gallery_attr, def_val):
        widget._find_combobox_match(widget_attr, constant_attr, def_val)


def _check_form_input_condition_match(gallery, attr, editor=None, box=None):
    """function to check _set_form args if it is match certain condition.

    Return True when check is succesful.
    """
    if (editor is not None and box is not None) or (editor is None and box is None):
        raise ValueError('Either only editor or box should be inputted.')
    g = gallery[0]
    g_attr = getattr(g, attr)
    return all(map(lambda x: getattr(x, attr) == g_attr, gallery))


class GalleryDialogWidget(QWidget):
    """A window for adding/modifying gallery.

    Pass a list of QModelIndexes to edit their data
    or pass a path to preset path
    """

    def __init__(self, parent, arg=None):
        """init func."""
        super().__init__(parent, Qt.Dialog)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setAutoFillBackground(True)
        self.parent_widget = parent
        m_l = QVBoxLayout()
        self.main_layout = QVBoxLayout()
        dummy = QWidget(self)
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameStyle(scroll_area.StyledPanel)
        dummy.setLayout(self.main_layout)
        scroll_area.setWidget(dummy)
        m_l.addWidget(scroll_area, 3)

        final_buttons = QHBoxLayout()
        final_buttons.setAlignment(Qt.AlignRight)
        m_l.addLayout(final_buttons)
        self.done = QPushButton("Done")
        self.done.setDefault(True)
        cancel = QPushButton("Cancel")
        final_buttons.addWidget(cancel)
        final_buttons.addWidget(self.done)
        self._multiple_galleries = False
        self._edit_galleries = []

        def new_gallery():
            self.setWindowTitle('Add a new gallery')
            self.newUI()
            self.commonUI()
            self.done.clicked.connect(self.accept)
            cancel.clicked.connect(self.reject)

        if arg:
            if isinstance(arg, (list, gallerydb.Gallery)):
                if isinstance(arg, gallerydb.Gallery):
                    self.setWindowTitle('Edit gallery')
                    self._edit_galleries.append(arg)
                else:
                    self.setWindowTitle('Edit {} galleries'.format(len(arg)))
                    self._multiple_galleries = True
                    self._edit_galleries.extend(arg)
                self.commonUI()
                self.setGallery(arg)
                self.done.clicked.connect(self.accept_edit)
                cancel.clicked.connect(self.reject_edit)
            elif isinstance(arg, str):
                new_gallery()
                self.choose_dir(arg)
        else:
            new_gallery()

        log_d('GalleryDialog: Create UI: successful')
        self.setLayout(m_l)
        if self._multiple_galleries:
            self.resize(500, 400)
        else:
            self.resize(500, 600)
        frect = self.frameGeometry()
        frect.moveCenter(QDesktopWidget().availableGeometry().center())
        self.move(frect.topLeft())
        self._fetch_inst = FetchObject()
        self._fetch_thread = QThread(self)
        self._fetch_thread.setObjectName("GalleryDialog metadata thread")
        self._fetch_inst.moveToThread(self._fetch_thread)
        self._fetch_thread.started.connect(self._fetch_inst.auto_web_metadata)

    def commonUI(self):
        """common ui."""
        if not self._multiple_galleries:
            f_web = QGroupBox("Metadata from the Web")
            f_web.setCheckable(False)
            self.main_layout.addWidget(f_web)
            web_main_layout = QVBoxLayout()
            web_info = ClickedLabel("Which gallery URLs are supported? (hover)", parent=self)
            web_info.setToolTip(app_constants.SUPPORTED_METADATA_URLS)
            web_info.setToolTipDuration(999999999)
            web_main_layout.addWidget(web_info)
            web_layout = QHBoxLayout()
            web_main_layout.addLayout(web_layout)
            f_web.setLayout(web_main_layout)
            #
            url_lbl = QLabel("URL: ")
            self.url_edit = QLineEdit()
            url_btn = QPushButton("Get metadata")
            url_prog = QProgressBar()
            url_btn.clicked.connect(
                lambda: self.web_metadata(self.url_edit.text(), url_btn, url_prog))
            url_prog.setTextVisible(False)
            url_prog.setMinimum(0)
            url_prog.setMaximum(0)
            web_layout.addWidget(url_lbl, 0, Qt.AlignLeft)
            web_layout.addWidget(self.url_edit, 0)
            web_layout.addWidget(url_btn, 0, Qt.AlignRight)
            web_layout.addWidget(url_prog, 0, Qt.AlignRight)
            self.url_edit.setPlaceholderText(
                "Insert supported gallery URLs or just press the button!")
            url_prog.hide()

        f_gallery = QGroupBox("Gallery Info")
        f_gallery.setCheckable(False)
        self.main_layout.addWidget(f_gallery)
        gallery_layout = QFormLayout()
        f_gallery.setLayout(gallery_layout)

        def checkbox_layout(widget):
            if self._multiple_galleries:
                l = QHBoxLayout()
                l.addWidget(widget.g_check)
                widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                l.addWidget(widget)
                return l
            else:
                widget.g_check.setChecked(True)
                widget.g_check.hide()
                return widget

        def add_check(widget):
            widget.g_check = QCheckBox(self)
            return widget

        self.title_edit = add_check(QLineEdit())
        self.author_edit = add_check(QLineEdit())
        author_completer = GCompleter(self, False, True, False)
        author_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.author_edit.setCompleter(author_completer)
        self.descr_edit = add_check(QTextEdit())
        self.descr_edit.setAcceptRichText(True)
        self.lang_box = add_check(QComboBox())
        self.lang_box.addItems(app_constants.G_LANGUAGES)
        self.lang_box.addItems(app_constants.G_CUSTOM_LANGUAGES)
        self.rating_box = add_check(QSpinBox())
        self.rating_box.setMaximum(5)
        self.rating_box.setMinimum(0)
        self._find_combobox_match(self.lang_box, app_constants.G_DEF_LANGUAGE, 0)
        tags_l = QVBoxLayout()
        tag_info = ClickedLabel("How do i write namespace & tags? (hover)", parent=self)
        tag_info.setToolTip(
            "Ways to write tags:\n\nNormal tags:\ntag1, tag2, tag3\n\n"
            "Namespaced tags:\nns1:tag1, ns1:tag2\n\n"
            "Namespaced tags with one or more tags under same namespace:\n"
            "ns1:[tag1, tag2, tag3], ns2:[tag1, tag2]\n\n"
            "Those three ways of writing namespace & tags can be combined freely.\n"
            "Tags are seperated by a comma, NOT whitespace.\n"
            "Namespaces will be capitalized while tags will be lowercased."
        )
        tag_info.setToolTipDuration(99999999)
        tags_l.addWidget(tag_info)
        self.tags_edit = add_check(CompleterTextEdit())
        self.tags_edit.setCompleter(GCompleter(self, False, False))
        if self._multiple_galleries:
            tags_l.addLayout(checkbox_layout(self.tags_edit), 3)
        else:
            tags_l.addWidget(checkbox_layout(self.tags_edit), 3)
        self.tags_edit.setPlaceholderText("Press Tab to autocomplete (Ctrl + E to show popup)")
        self.type_box = add_check(QComboBox())
        self.type_box.addItems(app_constants.G_TYPES)
        self._find_combobox_match(self.type_box, app_constants.G_DEF_TYPE, 0)
        # self.type_box.currentIndexChanged[int].connect(self.doujin_show)
        # self.doujin_parent = QLineEdit()
        # self.doujin_parent.setVisible(False)
        self.status_box = add_check(QComboBox())
        self.status_box.addItems(app_constants.G_STATUS)
        self._find_combobox_match(self.status_box, app_constants.G_DEF_STATUS, 0)
        self.pub_edit = add_check(QDateEdit())
        self.pub_edit.setCalendarPopup(True)
        self.pub_edit.setDate(QDate.currentDate())
        self.path_lbl = ClickedLabel("")
        self.path_lbl.setWordWrap(True)
        self.path_lbl.clicked.connect(lambda a: utils.open_path(a, a) if a else None)

        link_layout = QHBoxLayout()
        self.link_lbl = add_check(QLabel(""))
        self.link_lbl.setWordWrap(True)
        self.link_edit = QLineEdit()
        link_layout.addWidget(self.link_edit)
        if self._multiple_galleries:
            link_layout.addLayout(checkbox_layout(self.link_lbl))
        else:
            link_layout.addWidget(checkbox_layout(self.link_lbl))
        self.link_edit.hide()
        self.link_btn = QPushButton("Modify")
        self.link_btn.setFixedWidth(50)
        self.link_btn2 = QPushButton("Set")
        self.link_btn2.setFixedWidth(40)
        self.link_btn.clicked.connect(self.link_modify)
        self.link_btn2.clicked.connect(self.link_set)
        link_layout.addWidget(self.link_btn)
        link_layout.addWidget(self.link_btn2)
        self.link_btn2.hide()

        rating_ = checkbox_layout(self.rating_box)
        lang_ = checkbox_layout(self.lang_box)
        if self._multiple_galleries:
            rating_.insertWidget(0, QLabel("Rating:"))
            lang_.addLayout(rating_)
            lang_l = lang_
        else:
            lang_l = QHBoxLayout()
            lang_l.addWidget(lang_)
            lang_l.addWidget(QLabel("Rating:"), 0, Qt.AlignRight)
            lang_l.addWidget(rating_)

        gallery_layout.addRow("Title:", checkbox_layout(self.title_edit))
        gallery_layout.addRow("Author:", checkbox_layout(self.author_edit))
        gallery_layout.addRow("Description:", checkbox_layout(self.descr_edit))
        gallery_layout.addRow("Language:", lang_l)
        gallery_layout.addRow("Tags:", tags_l)
        gallery_layout.addRow("Type:", checkbox_layout(self.type_box))
        gallery_layout.addRow("Status:", checkbox_layout(self.status_box))
        gallery_layout.addRow("Publication Date:", checkbox_layout(self.pub_edit))
        gallery_layout.addRow("Path:", self.path_lbl)
        gallery_layout.addRow("Link:", link_layout)

        self.title_edit.setFocus()

    def resizeEvent(self, event):
        """resize event."""
        self.tags_edit.setFixedHeight(event.size().height() // 8)
        self.descr_edit.setFixedHeight(event.size().height() // 12.5)
        return super().resizeEvent(event)

    def _find_combobox_match(self, combobox, key, default):
        f_index = combobox.findText(key, Qt.MatchFixedString)
        if f_index != -1:
            combobox.setCurrentIndex(f_index)
            return True
        else:
            combobox.setCurrentIndex(default)
            return False

    @staticmethod
    def _set_form(gallery, attr, editor=None, box=None):
        """set editor."""
        if not _check_form_input_condition_match(
                gallery=gallery, attr=attr, editor=editor, box=box):
            return
        g = gallery[0]
        g_attr = getattr(g, attr)
        arg = g_attr if attr != 'tags' else tag_to_string(g_attr)
        form = editor if editor is not None else box
        if editor is not None:
            editor.setText(arg)
        else:
            box.setValue(arg)
        form.g_check.setChecked(True)

    @staticmethod
    def _get_gallery_date(g_pub_date):
        """set gallery date."""
        try:
            return datetime.strptime(g_pub_date[1], '%H:%M:%S').time()
        except IndexError:
            pass

    def setGallery(self, gallery):  # NOQA
        """To be used for when editing a gallery."""
        if isinstance(gallery, gallerydb.Gallery):
            self.gallery = gallery

            if not self._multiple_galleries:
                self.url_edit.setText(gallery.link)

            self.title_edit.setText(gallery.title)
            self.author_edit.setText(gallery.artist)
            self.descr_edit.setText(gallery.info)
            self.rating_box.setValue(gallery.rating)
            self.tags_edit.setText(tag_to_string(gallery.tags))

            _set_gallery_constant_setting(
                widget=self, widget_attr=self.lang_box, gallery_attr=gallery.language,
                constant_attr=app_constants.G_DEF_LANGUAGE, def_val=1)
            _set_gallery_constant_setting(
                widget=self, widget_attr=self.type_box, gallery_attr=gallery.type,
                constant_attr=app_constants.G_DEF_TYPE, def_val=0)
            _set_gallery_constant_setting(
                widget=self, widget_attr=self.status_box, gallery_attr=gallery.status,
                constant_attr=app_constants.G_DEF_STATUS, def_val=0)

            gallery_pub_date = "{}".format(gallery.pub_date).split(' ')
            # initiate gallery time when not defined
            self.gallery_time = self._get_gallery_date(g_pub_date=gallery_pub_date)
            qdate_pub_date = QDate.fromString(gallery_pub_date[0], "yyyy-MM-dd")
            self.pub_edit.setDate(qdate_pub_date)

            self.link_lbl.setText(gallery.link)
            self.path_lbl.setText(gallery.path)

        elif isinstance(gallery, list):
            g = gallery[0]
            self._set_form(gallery=gallery, attr='title', editor=self.title_edit)
            self._set_form(gallery=gallery, attr='artist', editor=self.author_edit)
            self._set_form(gallery=gallery, attr='info', editor=self.descr_edit)
            self._set_form(gallery=gallery, attr='tags', editor=self.tags_edit)
            self._set_form(gallery=gallery, attr='rating', box=self.rating_box)
            self._set_form(gallery=gallery, attr='link', editor=self.link_lbl)
            #
            _set_gallery_specific_setting(
                cls=self,
                attr='language', cls_attr='lang_box', gallery=gallery, def_val=1,
                constant_attr='G_DEF_LANGUAGE'
            )
            _set_gallery_specific_setting(
                cls=self,
                attr='type', cls_attr='type_box', gallery=gallery, def_val=0,
                constant_attr='G_DEF_TYPE'
            )
            _set_gallery_specific_setting(
                cls=self,
                attr='status', cls_attr='status_box', gallery=gallery, def_val=0,
                constant_attr='G_DEF_STATUS'
            )
            if all(map(lambda x: x.pub_date == g.pub_date, gallery)):
                gallery_pub_date = "{}".format(g.pub_date).split(' ')
                self.gallery_time = self._get_gallery_date(g_pub_date=gallery_pub_date)
                qdate_pub_date = QDate.fromString(gallery_pub_date[0], "yyyy-MM-dd")
                self.pub_edit.setDate(qdate_pub_date)
                self.pub_edit.g_check.setChecked(True)

    def newUI(self):
        """new ui."""
        f_local = QGroupBox("Directory/Archive")
        f_local.setCheckable(False)
        self.main_layout.addWidget(f_local)
        local_layout = QHBoxLayout()
        f_local.setLayout(local_layout)

        choose_folder = QPushButton("From Directory")
        choose_folder.clicked.connect(lambda: self.choose_dir('f'))
        local_layout.addWidget(choose_folder)

        choose_archive = QPushButton("From Archive")
        choose_archive.clicked.connect(lambda: self.choose_dir('a'))
        local_layout.addWidget(choose_archive)

        self.file_exists_lbl = QLabel()
        local_layout.addWidget(self.file_exists_lbl)
        self.file_exists_lbl.hide()

    def choose_dir(self, mode):  # NOQA
        """choose dir.

        Pass which mode to open the folder explorer in:
        'f': directory
        'a': files
        Or pass a predefined path
        """
        self.done.show()
        self.file_exists_lbl.hide()
        if mode == 'a':
            name = QFileDialog.getOpenFileName(self, 'Choose archive', filter=FILE_FILTER)
            name = name[0]
        elif mode == 'f':
            name = QFileDialog.getExistingDirectory(self, 'Choose folder')
        elif mode:
            if os.path.exists(mode):
                name = mode
            else:
                return None
        if not name:
            return
        head, tail = os.path.split(name)
        name = os.path.join(head, tail)
        parsed = utils.title_parser(tail)
        self.title_edit.setText(parsed['title'])
        self.author_edit.setText(parsed['artist'])
        self.path_lbl.setText(name)
        if not parsed['language']:
            parsed['language'] = app_constants.G_DEF_LANGUAGE
        l_i = self.lang_box.findText(parsed['language'])
        if l_i != -1:
            self.lang_box.setCurrentIndex(l_i)
        if gallerydb.GalleryDB.check_exists(name):
            self.file_exists_lbl.setText('<font color="red">Gallery already exists.</font>')
            self.file_exists_lbl.show()
        # check galleries
        gs = 1
        if name.endswith(ARCHIVE_FILES):
            gs = len(utils.check_archive(name))
        elif os.path.isdir(name):
            g_dirs, g_archs = utils.recursive_gallery_check(name)
            gs = len(g_dirs) + len(g_archs)
        if gs == 0:
            self.file_exists_lbl.setText('<font color="red">Invalid gallery source.</font>')
            self.file_exists_lbl.show()
            self.done.hide()
        if app_constants.SUBFOLDER_AS_GALLERY:
            if gs > 1:
                self.file_exists_lbl.setText(
                    '<font color="red">More than one galleries detected in source! '
                    'Use other methods to add.</font>'
                )
                self.file_exists_lbl.show()
                self.done.hide()

    def check(self):
        """check."""
        if not self._multiple_galleries:
            if len(self.title_edit.text()) is 0:
                self.title_edit.setFocus()
                self.title_edit.setStyleSheet(
                    "border-style:outset;border-width:2px;border-color:red;")
                return False
            elif len(self.author_edit.text()) is 0:
                self.author_edit.setText("Unknown")

            if len(self.path_lbl.text()) == 0 or self.path_lbl.text() == 'No path specified':
                self.path_lbl.setStyleSheet("color:red")
                self.path_lbl.setText('No path specified')
                return False

        return True

    def reject(self):
        """reject."""
        if self.check():
            msgbox = QMessageBox()
            msgbox.setText(
                "<font color='red'><b>Noo oniichan! "
                "You were about to add a new gallery.</b></font>"
            )
            msgbox.setInformativeText("Do you really want to discard?")
            msgbox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msgbox.setDefaultButton(QMessageBox.No)
            if msgbox.exec_() == QMessageBox.Yes:
                self.close()
        else:
            self.close()

    def web_metadata(self, url, btn_widget, pgr_widget):  # NOQA
        """web metadata."""
        if not self.path_lbl.text():
            return
        self.link_lbl.setText(url)
        btn_widget.hide()
        pgr_widget.show()

        def status(stat):
            def do_hide():
                try:
                    pgr_widget.hide()
                    btn_widget.show()
                except RuntimeError:
                    pass

            if stat:
                do_hide()
            else:
                danger_style_sheet = """QProgressBar::chunk {
                    background: QLinearGradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #FF0350,stop: 0.4999 #FF0020,stop: 0.5 #FF0019,stop: 1 #FF0000 );
                    border-bottom-right-radius: 5px;
                    border-bottom-left-radius: 5px;
                    border: .px solid black;}"""
                pgr_widget.setStyleSheet(danger_style_sheet)
                QTimer.singleShot(3000, do_hide)

        def gallery_picker(gallery, title_url_list, q):
            self.parent_widget._web_metadata_picker(gallery, title_url_list, q, self)

        try:
            dummy_gallery = self.make_gallery(self.gallery, False)
        except AttributeError:
            dummy_gallery = self.make_gallery(gallerydb.Gallery(), False, True)
        if not dummy_gallery:
            status(False)
            return None

        dummy_gallery._g_dialog_url = url
        self._fetch_inst.galleries = [dummy_gallery]
        self._disconnect()
        self._fetch_inst.GALLERY_PICKER.connect(gallery_picker)
        self._fetch_inst.GALLERY_EMITTER.connect(self.set_web_metadata)
        self._fetch_inst.FINISHED.connect(status)
        self._fetch_thread.start()

    def set_web_metadata(self, metadata):
        """set web metadata."""
        assert isinstance(metadata, gallerydb.Gallery)
        self.link_lbl.setText(metadata.link)
        self.title_edit.setText(metadata.title)
        self.author_edit.setText(metadata.artist)
        # assigned but never used.
        # tags = ""
        # lang = ['English', 'Japanese']
        self._find_combobox_match(self.lang_box, metadata.language, 2)
        self.tags_edit.setText(tag_to_string(metadata.tags))
        pub_string = "{}".format(metadata.pub_date)
        pub_date = QDate.fromString(pub_string.split()[0], "yyyy-MM-dd")
        self.pub_edit.setDate(pub_date)
        self._find_combobox_match(self.type_box, metadata.type, 0)

    def make_gallery(self, new_gallery, add_to_model=True, new=False):  # NOQA
        """make gallery."""
        def is_checked(widget):
            return widget.g_check.isChecked()
        if self.check():
            if is_checked(self.title_edit):
                new_gallery.title = self.title_edit.text()
                log_d('Adding gallery title')
            if is_checked(self.author_edit):
                new_gallery.artist = self.author_edit.text()
                log_d('Adding gallery artist')
            if not self._multiple_galleries:
                new_gallery.path = self.path_lbl.text()
                log_d('Adding gallery path')
            if is_checked(self.descr_edit):
                new_gallery.info = self.descr_edit.toPlainText()
                log_d('Adding gallery descr')
            if is_checked(self.type_box):
                new_gallery.type = self.type_box.currentText()
                log_d('Adding gallery type')
            if is_checked(self.lang_box):
                new_gallery.language = self.lang_box.currentText()
                log_d('Adding gallery lang')
            if is_checked(self.rating_box):
                new_gallery.rating = self.rating_box.value()
                log_d('Adding gallery rating')
            if is_checked(self.status_box):
                new_gallery.status = self.status_box.currentText()
                log_d('Adding gallery status')
            if is_checked(self.tags_edit):
                new_gallery.tags = utils.tag_to_dict(self.tags_edit.toPlainText())
                log_d('Adding gallery: tagging to dict')
            if is_checked(self.pub_edit):
                qpub_d = self.pub_edit.date().toString("ddMMyyyy")
                dpub_d = datetime.strptime(qpub_d, "%d%m%Y").date()
                try:
                    d_t = self.gallery_time
                except AttributeError:
                    d_t = datetime.now().time().replace(microsecond=0)
                dpub_d = datetime.combine(dpub_d, d_t)
                new_gallery.pub_date = dpub_d
                log_d('Adding gallery pub date')
            if is_checked(self.link_lbl):
                new_gallery.link = self.link_lbl.text()
                log_d('Adding gallery link')

            if new:
                if not new_gallery.chapters:
                    log_d('Starting chapters')
                    thread = threading.Thread(target=utils.make_chapters, args=(new_gallery,))
                    thread.start()
                    thread.join()
                    log_d('Finished chapters')
                    if new and app_constants.MOVE_IMPORTED_GALLERIES:
                        app_constants.OVERRIDE_MONITOR = True
                        new_gallery.move_gallery()
                if add_to_model:
                    self.parent_widget.default_manga_view.add_gallery(new_gallery, True)
                    log_i('Sent gallery to model')
            else:
                if add_to_model:
                    self.parent_widget.default_manga_view.replace_gallery([new_gallery], False)
            return new_gallery

    @staticmethod
    def _change_link(pre_link_item, main_link_item, text, after_link_items):
        """change link.

        This is method helper for link_set and link_modify method.

        Summary of this method.

        - pre_link will be hide.
        - show and set text on main_link_item.
        - hide after_link_item1 and show after_link_item2.
        """
        after_link_item1, after_link_item2 = after_link_items
        pre_link_item.hide()
        main_link_item.show()
        main_link_item.setText(text)
        after_link_item1.hide()
        after_link_item2.show()

    def link_set(self):
        """link set."""
        self._change_link(
            pre_link_item=self.link_edit,
            main_link_item=self.link_lbl, text=self.link_edit.text(),
            after_link_items=[self.link_btn2, self.link_btn]
        )

    def link_modify(self):
        """link modify."""
        self._change_link(
            pre_link_item=self.link_lbl,
            main_link_item=self.link_edit, text=self.link_lbl.text(),
            after_link_items=[self.link_btn, self.link_btn2]
        )

    def _disconnect(self):
        try:
            self._fetch_inst.GALLERY_PICKER.disconnect()
            self._fetch_inst.GALLERY_EMITTER.disconnect()
            self._fetch_inst.FINISHED.disconnect()
        except TypeError:
            pass

    def delayed_close(self):
        """delayed close."""
        if self._fetch_thread.isRunning():
            self._fetch_thread.finished.connect(self.close)
            self.hide()
        else:
            self.close()

    def accept(self):
        """accept."""
        self.make_gallery(gallerydb.Gallery(), new=True)
        self.delayed_close()

    def accept_edit(self):
        """accept edit."""
        gallerydb.execute(database.db.DBBase.begin, True)
        for g in self._edit_galleries:
            self.make_gallery(g)
        self.delayed_close()
        gallerydb.execute(database.db.DBBase.end, True)

    def reject_edit(self):
        """reject edit."""
        self.delayed_close()

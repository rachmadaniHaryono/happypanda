"""gallery list view widget."""
import logging
import os

from PyQt5.QtCore import (
    Qt,
    pyqtSignal,
)
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDesktopWidget,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListView,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

try:
    import utils
    from custom_list_item import CustomListItem
except ImportError:
    from .custom_list_item import CustomListItem
    from . import (
        utils,
    )

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class GalleryListViewWidget(QWidget):
    """GalleryListView."""

    SERIES = pyqtSignal(list)

    def __init__(self, parent=None, modal=False):
        """__init__."""
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog)
        self.setAttribute(Qt.WA_DeleteOnClose)
        layout = QVBoxLayout()
        self.setLayout(layout)

        if modal:
            frame = QFrame()
            frame.setFrameShape(frame.StyledPanel)
            modal_layout = QHBoxLayout()
            frame.setLayout(modal_layout)
            layout.addWidget(frame)
            info = QLabel(
                'This mode let\'s you add galleries from ' + 'different folders.')
            f_folder = QPushButton('Add directories')
            f_folder.clicked.connect(self.from_folder)
            f_files = QPushButton('Add archives')
            f_files.clicked.connect(self.from_files)
            modal_layout.addWidget(info, 3, Qt.AlignLeft)
            modal_layout.addWidget(f_folder, 0, Qt.AlignRight)
            modal_layout.addWidget(f_files, 0, Qt.AlignRight)

        check_layout = QHBoxLayout()
        layout.addLayout(check_layout)
        if modal:
            check_layout.addWidget(
                QLabel(
                    'Please uncheck galleries you do not want to add. '
                    '(Exisiting galleries won\'t be added'
                ),
                3
            )
        else:
            check_layout.addWidget(QLabel(
                'Please uncheck galleries you do not want to add. '
                '(Existing galleries are hidden)'
            ), 3)
        self.check_all = QCheckBox('Check/Uncheck All', self)
        self.check_all.setChecked(True)
        self.check_all.stateChanged.connect(self.all_check_state)

        check_layout.addWidget(self.check_all)
        self.view_list = QListWidget()
        self.view_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.view_list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.view_list.setAlternatingRowColors(True)
        self.view_list.setEditTriggers(self.view_list.NoEditTriggers)
        layout.addWidget(self.view_list)

        add_btn = QPushButton('Add checked')
        add_btn.clicked.connect(self.return_gallery)

        cancel_btn = QPushButton('Cancel')
        cancel_btn.clicked.connect(self.close_window)
        btn_layout = QHBoxLayout()

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        btn_layout.addWidget(spacer)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.resize(500, 550)
        frect = self.frameGeometry()
        frect.moveCenter(QDesktopWidget().availableGeometry().center())
        self.move(frect.topLeft())
        self.setWindowTitle('Gallery List')
        self.count = 0

    def all_check_state(self, new_state):
        """all_check_state."""
        row = 0
        done = False
        while not done:
            item = self.view_list.item(row)
            if item:
                row += 1
                if new_state == Qt.Unchecked:
                    item.setCheckState(Qt.Unchecked)
                else:
                    item.setCheckState(Qt.Checked)
            else:
                done = True

    def add_gallery(self, item, name):
        """Add gallery.

        Constructs an widgetitem to hold the provided item,
        and adds it to the view_list
        """
        assert isinstance(name, str)
        gallery_item = CustomListItem(item)
        gallery_item.setText(name)
        gallery_item.setFlags(gallery_item.flags() | Qt.ItemIsUserCheckable)
        gallery_item.setCheckState(Qt.Checked)
        self.view_list.addItem(gallery_item)
        self.count += 1

    def update_count(self):
        """update_count."""
        self.setWindowTitle('Gallery List ({})'.format(self.count))

    def return_gallery(self):
        """return_gallery."""
        gallery_list = []
        row = 0
        done = False
        while not done:
            item = self.view_list.item(row)
            if not item:
                done = True
            else:
                if item.checkState() == Qt.Checked:
                    gallery_list.append(item.item)
                row += 1

        self.SERIES.emit(gallery_list)
        self.close()

    def from_folder(self):
        """from_folder."""
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.DirectoryOnly)
        file_dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        file_view = file_dialog.findChild(QListView, 'listView')
        if file_view:
            file_view.setSelectionMode(QAbstractItemView.MultiSelection)
        f_tree_view = file_dialog.findChild(QTreeView)
        if f_tree_view:
            f_tree_view.setSelectionMode(QAbstractItemView.MultiSelection)

        if file_dialog.exec_():
            for path in file_dialog.selectedFiles():
                self.add_gallery(path, os.path.split(path)[1])

    def from_files(self):
        """from_files."""
        gallery_list = QFileDialog.getOpenFileNames(
            self, 'Select 1 or more gallery to add',
            filter='Archives ({})'.format(utils.FILE_FILTER)
        )
        for path in gallery_list[0]:
            # Warning: will break when you add more filters
            if len(path) != 0:
                self.add_gallery(path, os.path.split(path)[1])

    def close_window(self):
        """close_window."""
        msgbox = QMessageBox()
        msgbox.setText('Are you sure you want to cancel?')
        msgbox.setStandardButtons(msgbox.Yes | msgbox.No)
        msgbox.setDefaultButton(msgbox.No)
        msgbox.setIcon(msgbox.Question)
        if msgbox.exec_() == QMessageBox.Yes:
            self.close()

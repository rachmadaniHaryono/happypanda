"""gallery list edit."""
import logging

from PyQt5.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QLineEdit,
)
from PyQt5.QtCore import (
    pyqtSignal,
)

try:
    import gallerydb
    import app_constants
    from base_popup import BasePopup
    from clicked_label import ClickedLabel
except ImportError:
    from .base_popup import BasePopup
    from .clicked_label import ClickedLabel
    from . import (
        gallerydb,
        app_constants,
    )

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class GalleryListEdit(BasePopup):
    """gallery list edit."""

    apply = pyqtSignal()

    def __init__(self, parent):
        """init func."""
        super().__init__(parent, blur=False)
        main_layout = QFormLayout(self.main_widget)
        self.name_edit = QLineEdit(self)
        main_layout.addRow("Name:", self.name_edit)
        self.filter_edit = QLineEdit(self)
        what_is_filter = ClickedLabel("What is filter/enforce? (Hover)")
        what_is_filter.setToolTip(app_constants.WHAT_IS_FILTER)
        what_is_filter.setToolTipDuration(9999999999)
        self.enforce = QCheckBox(self)
        self.regex = QCheckBox(self)
        self.case = QCheckBox(self)
        self.strict = QCheckBox(self)
        main_layout.addRow(what_is_filter)
        main_layout.addRow("Filter", self.filter_edit)
        main_layout.addRow("Enforce", self.enforce)
        main_layout.addRow("Regex", self.regex)
        main_layout.addRow("Case sensitive", self.case)
        main_layout.addRow("Match whole terms", self.strict)
        main_layout.addRow(self.buttons_layout)
        self.add_buttons("Close")[0].clicked.connect(self.hide)
        self.add_buttons("Apply")[0].clicked.connect(self.accept)

    def set_list(self, gallery_list, item):
        """set list."""
        self.gallery_list = gallery_list
        self.name_edit.setText(gallery_list.name)
        self.enforce.setChecked(gallery_list.enforce)
        self.regex.setChecked(gallery_list.regex)
        self.case.setChecked(gallery_list.case)
        self.strict.setChecked(gallery_list.strict)
        self.item = item
        if gallery_list.filter:
            self.filter_edit.setText(gallery_list.filter)
        else:
            self.filter_edit.setText('')
        self.adjustSize()
        self.setFixedWidth(self.parent_widget.width())

    def accept(self):
        """accept."""
        name = self.name_edit.text()
        self.item.setText(name)
        self.gallery_list.name = name
        self.gallery_list.filter = self.filter_edit.text()
        self.gallery_list.enforce = self.enforce.isChecked()
        self.gallery_list.regex = self.regex.isChecked()
        self.gallery_list.case = self.case.isChecked()
        self.gallery_list.strict = self.strict.isChecked()
        gallerydb.execute(gallerydb.ListDB.modify_list,
                          True, self.gallery_list)
        self.apply.emit()
        self.hide()

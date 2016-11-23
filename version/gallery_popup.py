"""gallery popup."""
import logging

from PyQt5.QtCore import (
    Qt,
    pyqtSignal,
)
from PyQt5.QtWidgets import (
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

try:
    import gallerydb
    from base_popup import BasePopup
    from flow_layout import FlowLayout
    from gallery_showcase_widget import GalleryShowcaseWidget
except ImportError:
    from .base_popup import BasePopup
    from .flow_layout import FlowLayout
    from .gallery_showcase_widget import GalleryShowcaseWidget
    from . import gallerydb

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


class GalleryPopup(BasePopup):
    """gallery popup.

    Pass a tuple with text and a list of galleries
    gallery profiles won't be scaled if scale is set to false

    Args:
        tup_gallery(tupple):Tupple of gallery data.
        parent:Parent.
        menu:Menu.
        app_instance:Application instance.
    Attributes:
        gallery_doubleclicked(:class:`PyQt5.QtCore.pyqtSignal`):Signal  when gallery double
            clicked.
    """

    gallery_doubleclicked = pyqtSignal(gallerydb.Gallery)

    def __init__(self, tup_gallery, parent=None, menu=None, app_instance=None):
        """init func."""
        if app_instance is None:
            raise NotImplementedError
        super().__init__(parent)
        self.setMaximumWidth(16777215)
        assert isinstance(
            tup_gallery, tuple), "Incorrect type received, expected tuple"
        assert isinstance(tup_gallery[0], str) and isinstance(
            tup_gallery[1], list)
        main_layout = QVBoxLayout()
        # todo make it scroll
        dummy = QWidget()
        self.gallery_layout = FlowLayout(dummy)
        # scroll_area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(400)
        scroll_area.setMidLineWidth(620)
        scroll_area.setBackgroundRole(scroll_area.palette().Shadow)
        scroll_area.setFrameStyle(scroll_area.NoFrame)
        scroll_area.setWidget(dummy)
        main_layout.addWidget(scroll_area, 3)
        #
        text = tup_gallery[0]
        galleries = tup_gallery[1]
        for g in galleries:
            gall_w = GalleryShowcaseWidget(
                parent=self, menu=menu(app_instance=app_instance))
            gall_w.set_gallery(g, (170 // 1.40, 170))
            gall_w.double_clicked.connect(self.gallery_doubleclicked.emit)
            self.gallery_layout.addWidget(gall_w)
        # text_lbl
        text_lbl = QLabel(text)
        text_lbl.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(text_lbl)
        #
        main_layout.addLayout(self.buttons_layout)
        self.main_widget.setLayout(main_layout)
        #
        self.setMaximumHeight(500)
        self.setMaximumWidth(620)
        self.resize(620, 500)
        self.show()

    def get_all_items(self):
        """get all items.

        Returns:
            items(list):List of items.
        """
        n = self.gallery_layout.rowCount()
        items = []
        for x in range(n):
            item = self.gallery_layout.itemAt(x)
            items.append(item.widget())
        return items

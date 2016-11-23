"""modified popup."""
import logging

from PyQt5.QtWidgets import (
    QLabel,
    QVBoxLayout,
)

try:
    from base_popup import BasePopup
except ImportError:
    from .base_popup import BasePopup

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


class ModifiedPopup(BasePopup):
    """popup when modified.

    Args:
        path:Path
        gallery:Gallery.
        parent:Parent.
    """

    def __init__(self, path, gallery_id, parent=None):
        """init func."""
        super().__init__(parent)
        main_layout = QVBoxLayout()
        main_layout.addWidget(
            QLabel("Modified:\npath: {}\nID:{}".format(path, gallery_id)))
        self.main_widget.setLayout(main_layout)
        self.show()

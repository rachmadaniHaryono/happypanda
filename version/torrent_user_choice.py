"""torrent user choice."""
import logging

from PyQt5.QtCore import (
    Qt,
)
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
)

try:
    from base_user_choice import BaseUserChoice
    from custom_list_item import CustomListItem
    from spacer_widget import SpacerWidget
except ImportError:
    from .base_user_choice import BaseUserChoice
    from .custom_list_item import CustomListItem
    from .spacer_widget import SpacerWidget

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class TorrentUserChoice(BaseUserChoice):
    """TorrentUserChoice."""

    def __init__(self, parent, torrentitems=[], **kwargs):
        """__init__."""
        super().__init__(parent, **kwargs)
        title = QLabel('Torrents')
        title.setAlignment(Qt.AlignCenter)
        self.main_layout.addRow(title)
        self._list_w = QListWidget(self)
        self.main_layout.addRow(self._list_w)
        for t in torrentitems:
            self.add_torrent_item(t)

        btn_layout = QHBoxLayout()
        choose_btn = QPushButton('Choose')
        choose_btn.clicked.connect(self.accept)
        btn_layout.addWidget(SpacerWidget('h'))
        btn_layout.addWidget(choose_btn)
        self.main_layout.addRow(btn_layout)

    def add_torrent_item(self, item):
        """add_torrent_item."""
        list_item = CustomListItem(item)
        list_item.setText("{}\nSeeds:{}\tPeers:{}\tSize:{}\tDate:{}\tUploader:{}".format(
            item.name, item.seeds, item.peers, item.size, item.date, item.uploader))
        self._list_w.addItem(list_item)

    def accept(self):
        """accept."""
        items = self._list_w.selectedItems()
        if items:
            item = items[0]
            super().accept(item.item)

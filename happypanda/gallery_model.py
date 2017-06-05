"""gallery model."""
import structlog
from PyQt5.QtCore import (
    QAbstractTableModel,
    QDateTime,
    QModelIndex,
    QVariant,
    Qt,
    pyqtSignal,
)
from PyQt5.QtGui import (
    QColor,
)

try:
    import app_constants
    import utils
    from pretty_delta import PrettyDelta
    from star_rating import StarRating
except ImportError:
    from .pretty_delta import PrettyDelta
    from .star_rating import StarRating
    from . import (
        app_constants,
        utils,
    )


log = structlog.getLogger(__name__)


class GalleryModel(QAbstractTableModel):
    """Model for Model/View/Delegate framework."""

    GALLERY_ROLE = Qt.UserRole + 1
    ARTIST_ROLE = Qt.UserRole + 2
    FAV_ROLE = Qt.UserRole + 3
    DATE_ADDED_ROLE = Qt.UserRole + 4
    PUB_DATE_ROLE = Qt.UserRole + 5
    TIMES_READ_ROLE = Qt.UserRole + 6
    LAST_READ_ROLE = Qt.UserRole + 7
    TIME_ROLE = Qt.UserRole + 8
    RATING_ROLE = Qt.UserRole + 9

    ROWCOUNT_CHANGE = pyqtSignal()
    STATUSBAR_MSG = pyqtSignal(str)
    CUSTOM_STATUS_MSG = pyqtSignal(str)
    ADDED_ROWS = pyqtSignal()
    ADD_MORE = pyqtSignal()

    REMOVING_ROWS = False

    def __init__(self, data, parent=None):
        """init func."""
        super().__init__(parent)
        self.dataChanged.connect(lambda: self.status_b_msg("Edited"))
        self.dataChanged.connect(lambda: self.ROWCOUNT_CHANGE.emit())
        self.layoutChanged.connect(lambda: self.ROWCOUNT_CHANGE.emit())
        self.CUSTOM_STATUS_MSG.connect(self.status_b_msg)
        self._TITLE = app_constants.TITLE
        self._ARTIST = app_constants.ARTIST
        self._TAGS = app_constants.TAGS
        self._TYPE = app_constants.TYPE
        self._FAV = app_constants.FAV
        self._CHAPTERS = app_constants.CHAPTERS
        self._LANGUAGE = app_constants.LANGUAGE
        self._LINK = app_constants.LINK
        self._DESCR = app_constants.DESCR
        self._DATE_ADDED = app_constants.DATE_ADDED
        self._PUB_DATE = app_constants.PUB_DATE

        self._data = data
        self._data_count = 0  # number of items added to model
        self._gallery_to_add = []
        self._gallery_to_remove = []

        self.get_qdatetime = lambda v: QDateTime.fromString("{}".format(v), "yyyy-MM-dd HH:mm:ss")

    def status_b_msg(self, msg):
        """set status b msg."""
        self.STATUSBAR_MSG.emit(msg)

    def column_checker(self, current_column, current_gallery):
        """column check."""
        current_gallery_fav_value = u'\u2605' if current_gallery.fav == 1 else ''
        column_sets = (
            (self._TITLE, current_gallery.title),
            (self._ARTIST, current_gallery.artist),
            (self._TAGS, utils.tag_to_string(current_gallery.tags)),
            (self._TYPE, current_gallery.type),
            (self._FAV, current_gallery_fav_value),
            (self._CHAPTERS, len(current_gallery.chapters)),
            (self._LANGUAGE, current_gallery.language),
            (self._LINK, current_gallery.link),
            (self._DESCR, current_gallery.info),
            (self._DATE_ADDED, self.get_qdatetime(current_gallery.date_added)),
        )
        for column_set in column_sets:
            column, value = column_set
            if current_column == column:
                return value

        if current_column == self._PUB_DATE:
            qdate_g_pdt = self.get_qdatetime(current_gallery.pub_date)
            if qdate_g_pdt.isValid():
                return qdate_g_pdt
            else:
                return 'No date set'
        log.debug('Unknown column', column=current_column)

    @staticmethod
    def get_tooltip_value(current_gallery):
        """get tooltip value."""
        add_bold = []
        add_tips = []
        if not current_gallery.last_read:
            last_read_tips = 'Never!'
        else:
            last_read_tips = \
                '{} ago'.format(PrettyDelta(current_gallery.last_read).format(use_int=True))

        tooltip_sets = (
            (app_constants.TOOLTIP_TITLE, '<b>Title:</b>', current_gallery.title),
            (app_constants.TOOLTIP_AUTHOR, '<b>Author:</b>', current_gallery.artist),
            (app_constants.TOOLTIP_CHAPTERS, '<b>Chapters:</b>', len(current_gallery.chapters)),
            (app_constants.TOOLTIP_STATUS, '<b>Status:</b>', current_gallery.status),
            (app_constants.TOOLTIP_TYPE, '<b>Type:</b>', current_gallery.type),
            (app_constants.TOOLTIP_LANG, '<b>Language:</b>', current_gallery.language),
            (app_constants.TOOLTIP_DESCR, '<b>Description:</b><br />', current_gallery.info),
            (app_constants.TOOLTIP_TAGS, '<b>Tags:</b>',
             utils.tag_to_string(current_gallery.tags)),
            (app_constants.TOOLTIP_LAST_READ, '<b>Last read:</b>', last_read_tips),
            (app_constants.TOOLTIP_TIMES_READ, '<b>Times read:</b>', current_gallery.times_read),
            (app_constants.TOOLTIP_PUB_DATE, '<b>Publication Date:</b>',
             '{}'.format(current_gallery.pub_date).split(' ')[0]),
            (app_constants.TOOLTIP_DATE_ADDED, '<b>Date added:</b>',
             '{}'.format(current_gallery.date_added).split(' ')[0]),
        )
        for tooltip_set in tooltip_sets:
            cond, bold, tips = tooltip_set
            if cond:
                add_bold.append(bold)
                add_tips.append(tips)

        tips = list(zip(add_bold, add_tips))
        tooltip = []
        for tip in tips:
            tooltip.append("{} {}<br />".format(tip[0], tip[1]))
        return ''.join(tooltip)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        if index.row() >= len(self._data) or index.row() < 0:
            return QVariant()

        current_row = index.row()
        current_gallery = self._data[current_row]
        current_column = index.column()

        role_sets = (
            (role == Qt.DisplayRole, self.column_checker(current_column, current_gallery)),
            (role == self.ARTIST_ROLE, current_gallery.artist),
            (role == Qt.DecorationRole, current_gallery.profile),
            (role == Qt.BackgroundRole, QColor(242, 242, 242)),
            (role == Qt.ToolTipRole and app_constants.GRID_TOOLTIP,
             self.get_tooltip_value(current_gallery)),
            (role == self.GALLERY_ROLE, current_gallery),
            (role == self.FAV_ROLE, current_gallery.fav),
            (role == self.DATE_ADDED_ROLE, self.get_qdatetime(current_gallery.date_added)),
            (role == self.PUB_DATE_ROLE and current_gallery.pub_date,
             self.get_qdatetime(current_gallery.pub_date)),
            (role == self.TIMES_READ_ROLE, current_gallery.times_read),
            (role == self.LAST_READ_ROLE and current_gallery.last_read,
             self.get_qdatetime(current_gallery.last_read)),
            (role == self.TIME_ROLE, current_gallery.qtime),
            (role == self.RATING_ROLE, StarRating(current_gallery.rating)),
        )
        for role_set in role_sets:
            cond, value = role_set
            if cond:
                return value

    def rowCount(self, index=QModelIndex()):
        """row count."""
        if index.isValid():
            return 0
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        """column count."""
        return len(app_constants.COLUMNS)

    def headerData(self, section, orientation, role=Qt.DisplayRole):  # NOQA
        if role == Qt.TextAlignmentRole:
            return Qt.AlignLeft
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            if section == self._TITLE:
                return 'Title'
            elif section == self._ARTIST:
                return 'Author'
            elif section == self._TAGS:
                return 'Tags'
            elif section == self._TYPE:
                return 'Type'
            elif section == self._FAV:
                return u'\u2605'
            elif section == self._CHAPTERS:
                return 'Chapters'
            elif section == self._LANGUAGE:
                return 'Language'
            elif section == self._LINK:
                return 'Link'
            elif section == self._DESCR:
                return 'Description'
            elif section == self._DATE_ADDED:
                return 'Date Added'
            elif section == self._PUB_DATE:
                return 'Published'
        return section + 1

    def insertRows(self, position, rows, index=QModelIndex()):
        """insert rows."""
        self._data_count += rows
        if not self._gallery_to_add:
            return False

        self.beginInsertRows(QModelIndex(), position, position + rows - 1)
        for r in range(rows):
            self._data.insert(position, self._gallery_to_add.pop())
        self.endInsertRows()
        return True

    def replaceRows(self, list_of_gallery, position, rows=1, index=QModelIndex()):
        """replace gallery data to the data list WITHOUT adding to DB."""
        for pos, gallery in enumerate(list_of_gallery):
            del self._data[position + pos]
            self._data.insert(position + pos, gallery)
        self.dataChanged.emit(index, index, [Qt.UserRole + 1, Qt.DecorationRole])

    def removeRows(self, position, rows, index=QModelIndex()):
        """remove rows."""
        self._data_count -= rows
        self.beginRemoveRows(QModelIndex(), position, position + rows - 1)
        for r in range(rows):
            try:
                self._data.remove(self._gallery_to_remove.pop())
            except ValueError:
                return False
        self.endRemoveRows()
        return True

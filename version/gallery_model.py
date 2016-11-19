"""gallery model."""

import logging

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
    from star_rating import StarRating
except ImportError:
    from .star_rating import StarRating
    from . import (
        app_constants,
        utils,
    )


log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


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

    def status_b_msg(self, msg):
        """set status b msg."""
        self.STATUSBAR_MSG.emit(msg)

    def data(self, index, role=Qt.DisplayRole):  # NOQA
        if not index.isValid():
            return QVariant()
        if index.row() >= len(self._data) or index.row() < 0:
            return QVariant()

        current_row = index.row()
        current_gallery = self._data[current_row]
        current_column = index.column()

        def column_checker():
            if current_column == self._TITLE:
                title = current_gallery.title
                return title
            elif current_column == self._ARTIST:
                artist = current_gallery.artist
                return artist
            elif current_column == self._TAGS:
                tags = utils.tag_to_string(current_gallery.tags)
                return tags
            elif current_column == self._TYPE:
                type = current_gallery.type
                return type
            elif current_column == self._FAV:
                if current_gallery.fav == 1:
                    return u'\u2605'
                else:
                    return ''
            elif current_column == self._CHAPTERS:
                return len(current_gallery.chapters)
            elif current_column == self._LANGUAGE:
                return current_gallery.language
            elif current_column == self._LINK:
                return current_gallery.link
            elif current_column == self._DESCR:
                return current_gallery.info
            elif current_column == self._DATE_ADDED:
                g_dt = "{}".format(current_gallery.date_added)
                qdate_g_dt = QDateTime.fromString(g_dt, "yyyy-MM-dd HH:mm:ss")
                return qdate_g_dt
            elif current_column == self._PUB_DATE:
                g_pdt = "{}".format(current_gallery.pub_date)
                qdate_g_pdt = QDateTime.fromString(g_pdt, "yyyy-MM-dd HH:mm:ss")
                if qdate_g_pdt.isValid():
                    return qdate_g_pdt
                else:
                    return 'No date set'

        # TODO: name all these roles and put them in app_constants...

        if role == Qt.DisplayRole:
            return column_checker()
        # for artist searching
        if role == self.ARTIST_ROLE:
            artist = current_gallery.artist
            return artist

        if role == Qt.DecorationRole:
            pixmap = current_gallery.profile
            return pixmap

        if role == Qt.BackgroundRole:
            bg_color = QColor(242, 242, 242)
            # assigned but never used.
            # bg_brush = QBrush(bg_color)
            return bg_color

        if app_constants.GRID_TOOLTIP and role == Qt.ToolTipRole:
            add_bold = []
            add_tips = []
            if app_constants.TOOLTIP_TITLE:
                add_bold.append('<b>Title:</b>')
                add_tips.append(current_gallery.title)
            if app_constants.TOOLTIP_AUTHOR:
                add_bold.append('<b>Author:</b>')
                add_tips.append(current_gallery.artist)
            if app_constants.TOOLTIP_CHAPTERS:
                add_bold.append('<b>Chapters:</b>')
                add_tips.append(len(current_gallery.chapters))
            if app_constants.TOOLTIP_STATUS:
                add_bold.append('<b>Status:</b>')
                add_tips.append(current_gallery.status)
            if app_constants.TOOLTIP_TYPE:
                add_bold.append('<b>Type:</b>')
                add_tips.append(current_gallery.type)
            if app_constants.TOOLTIP_LANG:
                add_bold.append('<b>Language:</b>')
                add_tips.append(current_gallery.language)
            if app_constants.TOOLTIP_DESCR:
                add_bold.append('<b>Description:</b><br />')
                add_tips.append(current_gallery.info)
            if app_constants.TOOLTIP_TAGS:
                add_bold.append('<b>Tags:</b>')
                add_tips.append(utils.tag_to_string(current_gallery.tags))
            if app_constants.TOOLTIP_LAST_READ:
                add_bold.append('<b>Last read:</b>')
                add_tips.append(
                    '{} ago'.format(
                        utils.get_date_age(current_gallery.last_read)
                    ) if current_gallery.last_read else "Never!"
                )
            if app_constants.TOOLTIP_TIMES_READ:
                add_bold.append('<b>Times read:</b>')
                add_tips.append(current_gallery.times_read)
            if app_constants.TOOLTIP_PUB_DATE:
                add_bold.append('<b>Publication Date:</b>')
                add_tips.append('{}'.format(current_gallery.pub_date).split(' ')[0])
            if app_constants.TOOLTIP_DATE_ADDED:
                add_bold.append('<b>Date added:</b>')
                add_tips.append('{}'.format(current_gallery.date_added).split(' ')[0])

            tooltip = ""
            tips = list(zip(add_bold, add_tips))
            for tip in tips:
                tooltip += "{} {}<br />".format(tip[0], tip[1])
            return tooltip

        if role == self.GALLERY_ROLE:
            return current_gallery

        # favorite satus
        if role == self.FAV_ROLE:
            return current_gallery.fav

        if role == self.DATE_ADDED_ROLE:
            date_added = "{}".format(current_gallery.date_added)
            qdate_added = QDateTime.fromString(date_added, "yyyy-MM-dd HH:mm:ss")
            return qdate_added

        if role == self.PUB_DATE_ROLE:
            if current_gallery.pub_date:
                pub_date = "{}".format(current_gallery.pub_date)
                qpub_date = QDateTime.fromString(pub_date, "yyyy-MM-dd HH:mm:ss")
                return qpub_date

        if role == self.TIMES_READ_ROLE:
            return current_gallery.times_read

        if role == self.LAST_READ_ROLE:
            if current_gallery.last_read:
                last_read = "{}".format(current_gallery.last_read)
                qlast_read = QDateTime.fromString(last_read, "yyyy-MM-dd HH:mm:ss")
                return qlast_read

        if role == self.TIME_ROLE:
            return current_gallery.qtime

        if role == self.RATING_ROLE:
            return StarRating(current_gallery.rating)

        return None

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

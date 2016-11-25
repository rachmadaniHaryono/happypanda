"""grid delegate."""
import logging

from PyQt5.QtCore import (
    QPoint,
    QPointF,
    QRect,
    QRectF,
    QSize,
    Qt,
    pyqtSignal,
)
from PyQt5.QtGui import (
    QBrush,
    QColor,
    QFont,
    QFontMetrics,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QPixmapCache,
    QPolygonF,
    QTextDocument,
    QTextOption,
)
from PyQt5.QtWidgets import (
    QStyle,
    QStyledItemDelegate,
    QWidget,
)

try:
    import app_constants
    from misc import text_layout
    from gallery_model import GalleryModel
    from file_icon import FileIcon
except ImportError:
    from . import (
        app_constants,
    )
    from .misc import text_layout
    from .gallery_model import GalleryModel
    from .file_icon import FileIcon

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class GridDelegate(QStyledItemDelegate):
    """A custom delegate for the model/view framework."""

    POPUP = pyqtSignal()
    CONTEXT_ON = False

    def __init__(self, app_inst, parent):
        """init func."""
        super().__init__(parent)
        QPixmapCache.setCacheLimit(
            app_constants.THUMBNAIL_CACHE_SIZE[0] * app_constants.THUMBNAIL_CACHE_SIZE[1])
        self._painted_indexes = {}
        self.view = parent
        self.parent_widget = app_inst
        self._paint_level = 0

        # misc.FileIcon.refresh_default_icon()
        self.file_icons = FileIcon()
        if app_constants.USE_EXTERNAL_VIEWER:
            self.external_icon = self.file_icons.get_external_file_icon()
        else:
            self.external_icon = self.file_icons.get_default_file_icon()

        self.font_size = app_constants.GALLERY_FONT[1]
        self.font_name = 0  # app_constants.GALLERY_FONT[0]
        if not self.font_name:
            self.font_name = QWidget().font().family()
        self.title_font = QFont()
        self.title_font.setBold(True)
        self.title_font.setFamily(self.font_name)
        self.artist_font = QFont()
        self.artist_font.setFamily(self.font_name)
        if self.font_size is not 0:
            self.title_font.setPixelSize(self.font_size)
            self.artist_font.setPixelSize(self.font_size)
        self.title_font_m = QFontMetrics(self.title_font)
        self.artist_font_m = QFontMetrics(self.artist_font)
        t_h = self.title_font_m.height()
        a_h = self.artist_font_m.height()
        self.text_label_h = a_h + t_h * 2
        self.W = app_constants.THUMB_W_SIZE
        self.H = app_constants.THUMB_H_SIZE + app_constants.GRIDBOX_LBL_H

    def key(self, key):
        """Assign an unique key to indexes."""
        if key in self._painted_indexes:
            return self._painted_indexes[key]
        else:
            k = str(key)
            self._painted_indexes[key] = k
            return k

    def _increment_paint_level(self):
        self._paint_level += 1
        self.view.update()

    def paint(self, painter, option, index):  # NOQA
        assert isinstance(painter, QPainter)
        rec = option.rect.getRect()
        x = rec[0]
        y = rec[1]
        w = rec[2]
        h = rec[3]
        if self._paint_level:
            # if app_constants.HIGH_QUALITY_THUMBS:
            #   painter.setRenderHint(QPainter.SmoothPixmapTransform)
            painter.setRenderHint(QPainter.Antialiasing)
            gallery = index.data(Qt.UserRole + 1)
            star_rating = index.data(GalleryModel.RATING_ROLE)
            title = gallery.title
            artist = gallery.artist
            title_color = app_constants.GRID_VIEW_TITLE_COLOR
            artist_color = app_constants.GRID_VIEW_ARTIST_COLOR
            label_color = app_constants.GRID_VIEW_LABEL_COLOR
            # Enable this to see the defining box
            # painter.drawRect(option.rect)
            # define font size
            if 20 > len(title) > 15:
                title_size = "font-size:{}px;".format(self.font_size)
            elif 30 > len(title) > 20:
                title_size = "font-size:{}px;".format(self.font_size - 1)
            elif 40 > len(title) >= 30:
                title_size = "font-size:{}px;".format(self.font_size - 2)
            elif 50 > len(title) >= 40:
                title_size = "font-size:{}px;".format(self.font_size - 3)
            elif len(title) >= 50:
                title_size = "font-size:{}px;".format(self.font_size - 4)
            else:
                title_size = "font-size:{}px;".format(self.font_size)

            if 30 > len(artist) > 20:
                artist_size = "font-size:{}px;".format(self.font_size)
            elif 40 > len(artist) >= 30:
                artist_size = "font-size:{}px;".format(self.font_size - 1)
            elif len(artist) >= 40:
                artist_size = "font-size:{}px;".format(self.font_size - 2)
            else:
                artist_size = "font-size:{}px;".format(self.font_size)

            text_area = QTextDocument()
            text_area.setDefaultFont(option.font)
            text_area.setHtml("""
            <head>
            <style>
            #area
            {{
                display:flex;
                width:{6}px;
                height:{7}px
            }}
            #title {{
            position:absolute;
            color: {4};
            font-weight:bold;
            {0}
            }}
            #artist {{
            position:absolute;
            color: {5};
            top:20px;
            right:0;
            {1}
            }}
            </style>
            </head>
            <body>
            <div id="area">
            <center>
            <div id="title">{2}
            </div>
            <div id="artist">{3}
            </div>
            </div>
            </center>
            </body>
            """.format(
                title_size, artist_size, title, artist, title_color, artist_color,
                130 + app_constants.SIZE_FACTOR, 1 + app_constants.SIZE_FACTOR)
            )
            text_area.setTextWidth(w)

            # chapter_area = QTextDocument()
            # chapter_area.setDefaultFont(option.font)
            # chapter_area.setHtml("""
            # <font color="black">{}</font>
            # """.format("chapter"))
            # chapter_area.setTextWidth(w)
            def center_img(width):
                new_x = x
                if width < w:
                    diff = w - width
                    offset = diff // 2
                    new_x += offset
                return new_x

            def img_too_big(start_x):
                txt_layout = text_layout(
                    "Thumbnail regeneration needed!", w, self.title_font, self.title_font_m)

                clipping = QRectF(x, y + h // 4, w, app_constants.GRIDBOX_LBL_H - 10)
                txt_layout.draw(painter, QPointF(x, y + h // 4), clip=clipping)

            loaded_image = gallery.get_profile(app_constants.ProfileType.Default)
            if loaded_image and self._paint_level > 0 and self.view.scroll_speed < 600:
                # if we can't find a cached image
                pix_cache = QPixmapCache.find(self.key(loaded_image.cacheKey()))
                if isinstance(pix_cache, QPixmap):
                    self.image = pix_cache
                    img_x = center_img(self.image.width())
                    if self.image.width() > w or self.image.height() > h:
                        img_too_big(img_x)
                    else:
                        if self.image.height() < self.image.width():  # to keep aspect ratio
                            painter.drawPixmap(QPoint(img_x, y), self.image)
                        else:
                            painter.drawPixmap(QPoint(img_x, y), self.image)
                else:
                    self.image = QPixmap.fromImage(loaded_image)
                    img_x = center_img(self.image.width())
                    QPixmapCache.insert(self.key(loaded_image.cacheKey()), self.image)
                    if self.image.width() > w or self.image.height() > h:
                        img_too_big(img_x)
                    else:
                        if self.image.height() < self.image.width():  # to keep aspect ratio
                            painter.drawPixmap(QPoint(img_x, y), self.image)
                        else:
                            painter.drawPixmap(QPoint(img_x, y), self.image)
            else:

                painter.save()
                painter.setPen(QColor(164, 164, 164, 200))
                if gallery.profile:
                    thumb_text = "Loading..."
                else:
                    thumb_text = "Thumbnail regeneration needed!"
                txt_layout = text_layout(thumb_text, w, self.title_font, self.title_font_m)

                clipping = QRectF(x, y + h // 4, w, app_constants.GRIDBOX_LBL_H - 10)
                txt_layout.draw(painter, QPointF(x, y + h // 4), clip=clipping)
                painter.restore()

            # draw ribbon type
            painter.save()
            painter.setPen(Qt.NoPen)
            if app_constants.DISPLAY_GALLERY_RIBBON:
                type_ribbon_w = type_ribbon_l = w * 0.11
                rib_top_1 = QPointF(x + w - type_ribbon_l - type_ribbon_w, y)
                rib_top_2 = QPointF(x + w - type_ribbon_l, y)
                rib_side_1 = QPointF(x + w, y + type_ribbon_l)
                rib_side_2 = QPointF(x + w, y + type_ribbon_l + type_ribbon_w)
                ribbon_polygon = QPolygonF([rib_top_1, rib_top_2, rib_side_1, rib_side_2])
                ribbon_path = QPainterPath()
                ribbon_path.setFillRule(Qt.WindingFill)
                ribbon_path.addPolygon(ribbon_polygon)
                ribbon_path.closeSubpath()
                painter.setBrush(QBrush(QColor(self._ribbon_color(gallery.type))))
                painter.drawPath(ribbon_path)

            # draw if favourited
            if gallery.fav == 1:
                star_ribbon_w = w * 0.1
                star_ribbon_l = w * 0.08
                rib_top_1 = QPointF(x + star_ribbon_l, y)
                rib_side_1 = QPointF(x, y + star_ribbon_l)
                rib_top_2 = QPointF(x + star_ribbon_l + star_ribbon_w, y)
                rib_side_2 = QPointF(x, y + star_ribbon_l + star_ribbon_w)
                rib_star_mid_1 = QPointF(
                    (rib_top_1.x() + rib_side_1.x()) / 2, (rib_top_1.y() + rib_side_1.y()) / 2)
                rib_star_factor = star_ribbon_l / 4
                rib_star_p1_1 = rib_star_mid_1 + QPointF(rib_star_factor, -rib_star_factor)
                rib_star_p1_2 = rib_star_p1_1 + QPointF(-rib_star_factor, -rib_star_factor)
                rib_star_p1_3 = rib_star_mid_1 + QPointF(-rib_star_factor, rib_star_factor)
                rib_star_p1_4 = rib_star_p1_3 + QPointF(-rib_star_factor, -rib_star_factor)

                crown_1 = QPolygonF(
                    [rib_star_p1_1, rib_star_p1_2, rib_star_mid_1, rib_star_p1_4, rib_star_p1_3])
                painter.setBrush(QBrush(QColor(255, 255, 0, 200)))
                painter.drawPolygon(crown_1)

                ribbon_polygon = QPolygonF([rib_top_1, rib_side_1, rib_side_2, rib_top_2])
                ribbon_path = QPainterPath()
                ribbon_path.setFillRule(Qt.WindingFill)
                ribbon_path.addPolygon(ribbon_polygon)
                ribbon_path.closeSubpath()
                painter.drawPath(ribbon_path)
                painter.setPen(QColor(255, 0, 0, 100))
                painter.drawPolyline(
                    rib_top_1, rib_star_p1_1, rib_star_p1_2, rib_star_mid_1, rib_star_p1_4,
                    rib_star_p1_3, rib_side_1
                )
                painter.drawLine(rib_top_1, rib_top_2)
                painter.drawLine(rib_top_2, rib_side_2)
                painter.drawLine(rib_side_1, rib_side_2)
            painter.restore()

            if self._paint_level > 0:
                if app_constants._REFRESH_EXTERNAL_VIEWER:
                    if app_constants.USE_EXTERNAL_VIEWER:
                        self.external_icon = self.file_icons.get_external_file_icon()
                    else:
                        self.external_icon = self.file_icons.get_default_file_icon()

                type_w = painter.fontMetrics().width(gallery.file_type)
                type_h = painter.fontMetrics().height()
                type_p = QPoint(x + 4, y + app_constants.THUMB_H_SIZE - type_h - 5)
                type_rect = QRect(type_p.x() - 2, type_p.y() - 1, type_w + 4, type_h + 1)
                if app_constants.DISPLAY_GALLERY_TYPE:
                    type_color = QColor(239, 0, 0, 200)
                    if gallery.file_type == "zip":
                        type_color = QColor(241, 0, 83, 200)
                    elif gallery.file_type == "cbz":
                        type_color = QColor(0, 139, 0, 200)
                    elif gallery.file_type == "rar":
                        type_color = QColor(30, 127, 150, 200)
                    elif gallery.file_type == "cbr":
                        type_color = QColor(210, 0, 13, 200)

                    painter.save()
                    painter.setPen(QPen(Qt.white))
                    painter.fillRect(type_rect, type_color)
                    painter.drawText(
                        type_p.x(),
                        type_p.y() + painter.fontMetrics().height() - 4,
                        gallery.file_type
                    )
                    painter.restore()

                star_start_x = (
                    type_rect.x() + type_rect.width() if app_constants.DISPLAY_GALLERY_TYPE else x)
                star_width = star_rating.sizeHint().width()
                star_start_x += ((x + w - star_start_x) - (star_width)) / 2
                star_rating.paint(
                    painter, QRect(star_start_x, type_rect.y(), star_width, type_rect.height()))

                # if app_constants.USE_EXTERNAL_PROG_ICO:
                #   if self.external_icon and not self.external_icon.isNull():
                #       self.external_icon.paint(painter, QRect(x+w-30,
                #       y+app_constants.THUMB_H_SIZE-28, 28, 28))

            if gallery.state == app_constants.GalleryState.New:
                painter.save()
                painter.setPen(Qt.NoPen)
                gradient = QLinearGradient()
                gradient.setStart(x, y + app_constants.THUMB_H_SIZE / 2)
                gradient.setFinalStop(x, y + app_constants.THUMB_H_SIZE)
                gradient.setColorAt(0, QColor(255, 255, 255, 0))
                gradient.setColorAt(1, QColor(0, 255, 0, 150))
                painter.setBrush(QBrush(gradient))
                painter.drawRoundedRect(
                    QRectF(
                        x,
                        y + app_constants.THUMB_H_SIZE / 2,
                        w,
                        app_constants.THUMB_H_SIZE / 2
                    ),
                    2,
                    2
                )
                painter.restore()

            def draw_text_label(lbl_h):
                # draw the label for text
                painter.save()
                painter.translate(x, y + app_constants.THUMB_H_SIZE)
                box_color = QBrush(QColor(label_color))  # QColor(0,0,0,123))
                painter.setBrush(box_color)
                rect = QRect(0, 0, w, lbl_h)  # x, y, width, height
                painter.fillRect(rect, box_color)
                painter.restore()
                return rect

            if option.state & QStyle.State_MouseOver or option.state & QStyle.State_Selected:
                title_layout = text_layout(title, w, self.title_font, self.title_font_m)
                artist_layout = text_layout(artist, w, self.artist_font, self.artist_font_m)
                t_h = title_layout.boundingRect().height()
                a_h = artist_layout.boundingRect().height()

                if app_constants.GALLERY_FONT_ELIDE:
                    lbl_rect = draw_text_label(min(t_h + a_h + 3, app_constants.GRIDBOX_LBL_H))
                else:
                    lbl_rect = draw_text_label(app_constants.GRIDBOX_LBL_H)

                clipping = QRectF(
                    x, y + app_constants.THUMB_H_SIZE, w, app_constants.GRIDBOX_LBL_H - 10)
                painter.setPen(QColor(title_color))
                title_layout.draw(
                    painter, QPointF(x, y + app_constants.THUMB_H_SIZE), clip=clipping)
                painter.setPen(QColor(artist_color))
                artist_layout.draw(
                    painter, QPointF(x, y + app_constants.THUMB_H_SIZE + t_h), clip=clipping)
                # painter.fillRect(option.rect, QColor)
            else:
                if app_constants.GALLERY_FONT_ELIDE:
                    lbl_rect = draw_text_label(self.text_label_h)
                else:
                    lbl_rect = draw_text_label(app_constants.GRIDBOX_LBL_H)
                # draw text
                painter.save()
                alignment = QTextOption(Qt.AlignCenter)
                alignment.setUseDesignMetrics(True)
                title_rect = QRectF(0, 0, w, self.title_font_m.height())
                artist_rect = QRectF(
                    0, self.artist_font_m.height(), w, self.artist_font_m.height())
                painter.translate(x, y + app_constants.THUMB_H_SIZE)
                if app_constants.GALLERY_FONT_ELIDE:
                    painter.setFont(self.title_font)
                    painter.setPen(QColor(title_color))
                    painter.drawText(
                        title_rect,
                        self.title_font_m.elidedText(title, Qt.ElideRight, w - 10),
                        alignment
                    )

                    painter.setPen(QColor(artist_color))
                    painter.setFont(self.artist_font)
                    alignment.setWrapMode(QTextOption.NoWrap)
                    painter.drawText(
                        artist_rect,
                        self.title_font_m.elidedText(artist, Qt.ElideRight, w - 10),
                        alignment
                    )
                else:
                    text_area.setDefaultFont(QFont(self.font_name))
                    text_area.drawContents(painter)
                # #painter.resetTransform()
                painter.restore()

            if option.state & QStyle.State_Selected:
                painter.save()
                selected_rect = QRectF(x, y, w, lbl_rect.height() + app_constants.THUMB_H_SIZE)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(QColor(164, 164, 164, 120)))
                painter.drawRoundedRect(selected_rect, 5, 5)
                # painter.fillRect(selected_rect, QColor(164,164,164,120))
                painter.restore()

            def warning(txt):
                painter.save()
                selected_rect = QRectF(x, y, w, lbl_rect.height() + app_constants.THUMB_H_SIZE)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(QColor(255, 0, 0, 120)))
                p_path = QPainterPath()
                p_path.setFillRule(Qt.WindingFill)
                p_path.addRoundedRect(selected_rect, 5, 5)
                p_path.addRect(x, y, 20, 20)
                p_path.addRect(x + w - 20, y, 20, 20)
                painter.drawPath(p_path.simplified())
                painter.setPen(QColor("white"))
                txt_layout = text_layout(txt, w, self.title_font, self.title_font_m)
                txt_layout.draw(painter, QPointF(x, y + h * 0.3))
                painter.restore()

            if not gallery.id and self.view.view_type != app_constants.ViewType.Addition:
                warning("This gallery does not exist anymore!")
            elif gallery.dead_link:
                warning("Cannot find gallery source!")

            if app_constants.DEBUG or self.view.view_type == app_constants.ViewType.Duplicate:
                painter.save()
                painter.setPen(QPen(Qt.white))
                id_txt = "ID: {}".format(gallery.id)
                type_w = painter.fontMetrics().width(id_txt)
                type_h = painter.fontMetrics().height()
                type_p = QPoint(x + 4, y + 50 - type_h - 5)
                type_rect = QRect(type_p.x() - 2, type_p.y() - 1, type_w + 4, type_h + 1)
                painter.fillRect(type_rect, QColor(239, 0, 0, 200))
                painter.drawText(
                    type_p.x(), type_p.y() + painter.fontMetrics().height() - 4, id_txt)
                painter.restore()

            if option.state & QStyle.State_Selected:
                painter.setPen(QPen(option.palette.highlightedText().color()))
        else:
            painter.fillRect(option.rect, QColor(164, 164, 164, 100))
            painter.setPen(QColor(164, 164, 164, 200))
            txt_layout = text_layout("Fetching...", w, self.title_font, self.title_font_m)

            clipping = QRectF(x, y + h // 4, w, app_constants.GRIDBOX_LBL_H - 10)
            txt_layout.draw(painter, QPointF(x, y + h // 4), clip=clipping)

    def _ribbon_color(self, gallery_type):
        if gallery_type:
            gallery_type = gallery_type.lower()
        if gallery_type == "manga":
            return app_constants.GRID_VIEW_T_MANGA_COLOR
        elif gallery_type == "doujinshi":
            return app_constants.GRID_VIEW_T_DOUJIN_COLOR
        elif "artist cg" in gallery_type:
            return app_constants.GRID_VIEW_T_ARTIST_CG_COLOR
        elif "game cg" in gallery_type:
            return app_constants.GRID_VIEW_T_GAME_CG_COLOR
        elif gallery_type == "western":
            return app_constants.GRID_VIEW_T_WESTERN_COLOR
        elif "image" in gallery_type:
            return app_constants.GRID_VIEW_T_IMAGE_COLOR
        elif gallery_type == "non-h":
            return app_constants.GRID_VIEW_T_NON_H_COLOR
        elif gallery_type == "cosplay":
            return app_constants.GRID_VIEW_T_COSPLAY_COLOR
        else:
            return app_constants.GRID_VIEW_T_OTHER_COLOR

    def sizeHint(self, option, index):
        """size hint."""
        return QSize(self.W, self.H)

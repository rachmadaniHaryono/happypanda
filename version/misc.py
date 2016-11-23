"""misc module."""
# """
# This file is part of Happypanda.
# Happypanda is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# any later version.
# Happypanda is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with Happypanda.  If not, see <http://www.gnu.org/licenses/>.
# """
import logging

from PyQt5.QtCore import (
    QByteArray,
    QPointF,
    QPropertyAnimation,
    Qt,
)
from PyQt5.QtGui import (
    QTextLayout,
    QTextOption,
)
from PyQt5.QtWidgets import (
    QCommonStyle,
    QDesktopWidget,
)

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


def text_layout(text, width, font, font_metrics, alignment=Qt.AlignCenter):
    """Lay out wrapped text."""
    text_option = QTextOption(alignment)
    text_option.setUseDesignMetrics(True)
    text_option.setWrapMode(QTextOption.WordWrap)
    layout = QTextLayout(text, font)
    layout.setTextOption(text_option)
    leading = font_metrics.leading()
    height = 0
    layout.setCacheEnabled(True)
    layout.beginLayout()
    while True:
        line = layout.createLine()
        if not line.isValid():
            break
        line.setLineWidth(width)
        height += leading
        line.setPosition(QPointF(0, height))
        height += line.height()
    layout.endLayout()
    return layout


def centerWidget(widget, parent_widget=None):
    """centerWidget."""
    if parent_widget:
        r = parent_widget.rect()
    else:
        r = QDesktopWidget().availableGeometry()

    widget.setGeometry(QCommonStyle.alignedRect(
        Qt.LeftToRight, Qt.AlignCenter, widget.size(), r))


def clearLayout(layout):  # NOQA
    """clearLayout."""
    if layout is not None:
        while layout.count():
            child = layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()
            elif child.layout() is not None:
                clearLayout(child.layout())


def create_animation(parent, prop):
    """create_animation."""
    p_array = QByteArray().append(prop)
    return QPropertyAnimation(parent, p_array)


# def center_parent(parent, child):
#   "centers child window in parent"
#   centerparent = QPoint(
#   		parent.x() + (parent.frameGeometry().width() -
#   				 child.frameGeometry().width())//2,
#   				parent.y() + (parent.frameGeometry().width() -
#   				   child.frameGeometry().width())//2)
#   desktop = QApplication.desktop()
#   sg_rect = desktop.screenGeometry(desktop.screenNumber(parent))
#   child_frame = child.frameGeometry()
#
#   if centerparent.x() < sg_rect.left():
#   	centerparent.setX(sg_rect.left())
#   elif (centerparent.x() + child_frame.width()) > sg_rect.right():
#   	centerparent.setX(sg_rect.right() - child_frame.width())
#
#   if centerparent.y() < sg_rect.top():
#   	centerparent.setY(sg_rect.top())
#   elif (centerparent.y() + child_frame.height()) > sg_rect.bottom():
#   	centerparent.setY(sg_rect.bottom() - child_frame.height())
#
#   child.move(centerparent)

"""spinner widget."""
import math
import time

from PyQt5.QtCore import (
    pyqtSignal,
    QPoint,
    QPointF,
    QRect,
    QRectF,
    Qt,
    QTimer,
)
from PyQt5.QtGui import (
    QBrush,
    QColor,
    QPainter,
    QPen,
)

try:
    from transparent_widget import TransparentWidget
    from misc import create_animation, text_layout
except ImportError:
    from .transparent_widget import TransparentWidget
    from .misc import (
        create_animation,
        text_layout,
    )


class SpinnerWidget(TransparentWidget):
    """Spinner widget.

    Args:
        parent (QtWidgets.QWidget): Parent widget.
        position (str): Position of the widget. it can be 'center', 'topright' or QPoint.

    Attributes:
        activated (pyqtSignal): Signal when widget activated.
        deactivated (pyqtSignal): Signal when widget deactivated.
        about_to_show (int): State wiget is 'about to show'
        about_to_hide (int): State wiget is 'about to hide'
        _OFFSET_X_TOPRIGHT (int): Default Offset on top right.
        fps (int): Frame per second.
        border (int): Border.
        line_width (int): Line width.
        arc_length (int): Arc Length.
        seconds_per_spin (int): Seconds per spin.
        text_layout: Text layout.
        text: Text.
        _text_margin (int): Text margin.
        _timer (QTimer): Timer.
        _start_angle (int): Start angle.
        _offset_x_topright (int): Offset on top right.
        margin (int): Margin.
        _position: Position.
        _min_size (int): Minimum size.
        state_timer (QTimer): State's timer.
        current_state: Current state.
        fade_animation: Fade animation.
    """

    activated = pyqtSignal()
    deactivated = pyqtSignal()
    about_to_show, about_to_hide = range(2)
    _OFFSET_X_TOPRIGHT = [0]

    def __init__(self, parent, position='topright'):
        """init"""
        super().__init__(parent, flags=Qt.Window | Qt.FramelessWindowHint, move_listener=False)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.fps = 21
        self.border = 2
        self.line_width = 5
        self.arc_length = 100
        self.seconds_per_spin = 1
        self.text_layout = None

        self.text = ''
        self._text_margin = 5

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_timer_timeout)

        # keep track of the current start angle to avoid
        # unnecessary repaints
        self._start_angle = 0

        self._offset_x_topright = self._OFFSET_X_TOPRIGHT[0]
        self.margin = 10
        self._position = position
        self._min_size = 0

        self.state_timer = QTimer()
        self.current_state = self.about_to_show
        self.state_timer.timeout.connect(super().hide)
        self.state_timer.setSingleShot(True)

        # animation
        self.fade_animation = create_animation(self, 'windowOpacity')
        self.fade_animation.setDuration(800)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)

        self.setWindowOpacity(0.0)
        self._update_layout()
        self.set_size(50)
        self._set_position(position)

    def _update_layout(self):
        """Update layout."""
        self.text_layout = text_layout(
            self.text, self.width() - self._text_margin, self.font(), self.fontMetrics())
        self.setFixedHeight(
            self._min_size + self.text_layout.boundingRect().height())

    def set_size(self, w):
        """Set size.

        Args:
            w (int): Width.
        """
        self.setFixedWidth(w)
        self._min_size = w
        self._update_layout()
        self.update()

    def set_text(self, txt):
        """Set text.

        Args:
            txt: Text.
        """
        self.text = txt
        self._update_layout()
        self.update()

    def _set_position(self, new_pos):
        """Set position.

        Args:
            new_pos: New position. It can be'center', 'topright' or QPoint.
        """
        p = self.parent_widget

        # topleft
        if new_pos == "topright":

            def topright():
                return QPoint(
                    p.pos().x() + p.width() - 65 - self._offset_x_topright,
                    p.pos().y() + p.toolbar.height() + 55
                )
            self.move(topright())
            p.move_listener.connect(lambda: self.update_move(topright()))

        elif new_pos == "center":
            p.move_listener.connect(
                lambda: self.update_move(
                    QPoint(p.pos().x() + p.width() // 2,
                           p.pos().y() + p.height() // 2)
                )
            )

        elif isinstance(new_pos, QPoint):
            p.move_listener.connect(lambda: self.update_move(new_pos))

    def paintEvent(self, event):
        """Paint event.

        Args:
            event (QtGui.QPaintEvent): Paint event.
        """
        # call the base paint event:
        super().paintEvent(event)

        painter = QPainter()
        painter.begin(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)

            txt_rect = QRectF(0, 0, 0, 0)
            if not self.text:
                txt_rect.setHeight(self.fontMetrics().height())

            painter.save()
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(88, 88, 88, 180)))
            painter.drawRoundedRect(
                QRect(0, 0, self.width(), self.height() - txt_rect.height()), 5, 5)
            painter.restore()

            pen = QPen(QColor('#F2F2F2'))
            pen.setWidth(self.line_width)
            painter.setPen(pen)

            border = self.border + int(math.ceil(self.line_width / 2.0))
            r = QRectF(
                (txt_rect.height()) / 2, (txt_rect.height() /
                                          2), self.width() - txt_rect.height(),
                self.width() - txt_rect.height()
            )
            r.adjust(border, border, -border, -border)

            # draw the arc:
            painter.drawArc(r, -self._start_angle * 16, self.arc_length * 16)

            # draw text if there is
            if self.text:
                txt_rect = self.text_layout.boundingRect()
                self.text_layout.draw(
                    painter,
                    QPointF(
                        self._text_margin,
                        self.height() - txt_rect.height() - self._text_margin / 2
                    )
                )

            r = None

        finally:
            painter.end()
            painter = None

    def showEvent(self, event):
        """Show event.

        Args:
            event (QtGui.QShowEvent): Show event.
        """
        if self._position == "topright":
            self._OFFSET_X_TOPRIGHT[0] += + self.width() + self.margin
        if not self._timer.isActive():
            self.fade_animation.start()
            self.current_state = self.about_to_show
            self.state_timer.stop()
            self.activated.emit()
            self._timer.start(1000 / max(1, self.fps))
        super().showEvent(event)

    def hideEvent(self, event):
        """Hide event.

        Args:
            event (QtGui.QHideEvent): Hide event.
        """
        self._timer.stop()
        self.deactivated.emit()
        super().hideEvent(event)

    def before_hide(self):
        """function to run before hide."""
        if self.current_state == self.about_to_hide:
            return
        self.current_state = self.about_to_hide
        if self._position == "topright":
            self._OFFSET_X_TOPRIGHT[0] -= self.width() + self.margin
        self.state_timer.start(5000)

    def closeEvent(self, event):
        """Close event.

        Args:
            event (QtGui.QCloseEvent): Close event.
        """
        self._timer.stop()
        super().closeEvent(event)

    def _on_timer_timeout(self):
        """Function when timer is timeout."""
        if not self.isVisible():
            return

        # calculate the spin angle as a function of the current time so that all
        # spinners appear in sync!
        t = time.time()
        whole_seconds = int(t)
        p = (whole_seconds % self.seconds_per_spin) + (t - whole_seconds)
        angle = int((360 * p) / self.seconds_per_spin)

        if angle == self._start_angle:
            return

        self._start_angle = angle
        self.update()

"""completer text edit."""
import logging

from PyQt5.QtCore import (
    Qt,
)
from PyQt5.QtGui import (
    QTextCursor,
)
from PyQt5.QtWidgets import (
    QCompleter,
    QTextEdit,
)

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class CompleterTextEdit(QTextEdit):
    """A textedit with autocomplete."""

    def __init__(self, **kwargs):
        """__init__."""
        super().__init__(**kwargs)
        self._completer = None
        log_d('Instantiate CompleterTextEdit: OK')

    def setCompleter(self, c):
        """setCompleter."""
        if self._completer is not None:
            self._completer.activated.disconnect()

        self._completer = c

        c.setWidget(self)
        c.setCompletionMode(QCompleter.PopupCompletion)
        c.setCaseSensitivity(Qt.CaseInsensitive)
        c.activated.connect(self.insertCompletion)

    def completer(self):
        """completer."""
        return self._completer

    def insertCompletion(self, completion):
        """insertCompletion."""
        if self._completer.widget() is not self:
            return

        tc = self.textCursor()
        extra = len(completion) - len(self._completer.completionPrefix())
        tc.movePosition(QTextCursor.Left)
        tc.movePosition(QTextCursor.EndOfWord)
        tc.insertText(completion[-extra:])
        self.setTextCursor(tc)

    def textUnderCursor(self):
        """textUnderCursor."""
        tc = self.textCursor()
        tc.select(QTextCursor.WordUnderCursor)

        return tc.selectedText()

    def focusInEvent(self, e):
        """focusInEvent."""
        if self._completer is not None:
            self._completer.setWidget(self)

        super().focusInEvent(e)

    def keyPressEvent(self, e):
        """keyPressEvent."""
        if self._completer is not None and self._completer.popup().isVisible():
            # The following keys are forwarded by the completer to the widget.
            if e.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Escape, Qt.Key_Tab, Qt.Key_Backtab):
                e.ignore()
                # Let the completer do default behavior.
                return

        isShortcut = e.modifiers() == Qt.ControlModifier and e.key() == Qt.Key_E
        if self._completer is None or not isShortcut:
            # Do not process the shortcut when we have a completer.
            super().keyPressEvent(e)

        ctrlOrShift = e.modifiers() & (Qt.ControlModifier | Qt.ShiftModifier)
        if self._completer is None or (ctrlOrShift and len(e.text()) == 0):
            return

        eow = "~!@#$%^&*()_+{}|:\"<>?,./;'[]\\-="
        hasModifier = (e.modifiers() != Qt.NoModifier) and not ctrlOrShift
        completionPrefix = self.textUnderCursor()

        hide_completer_popup = not isShortcut and (
            hasModifier or len(e.text()) == 0 or len(
                completionPrefix) < 3 or e.text()[-1] in eow
        )
        if hide_completer_popup:
            self._completer.popup().hide()
            return

        if completionPrefix != self._completer.completionPrefix():
            self._completer.setCompletionPrefix(completionPrefix)
            self._completer.popup().setCurrentIndex(
                self._completer.completionModel().index(0, 0))

        cr = self.cursorRect()
        cr.setWidth(self._completer.popup().sizeHintForColumn(
            0) + self._completer.popup().verticalScrollBar().sizeHint().width())
        if self._completer:
            self._completer.complete(cr)

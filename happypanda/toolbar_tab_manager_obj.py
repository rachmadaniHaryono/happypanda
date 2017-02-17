"""toolbar tab manager.

taken from misc_db.py.
"""
import logging

from PyQt5.QtWidgets import (
    QWidget,
    QButtonGroup,
)
from PyQt5.QtCore import (
    QObject,
)

from .toolbar_button import ToolbarButton
from .manga_views import MangaViews
from . import (
    app_constants,
)

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class ToolbarTabManagerObject(QObject):
    """toolbar tab manager."""

    def __init__(self, toolbar, parent=None):
        """init func."""
        super().__init__(parent)
        self.parent_widget = parent
        self.toolbar = toolbar
        self._actions = []
        self._last_selected = None
        self.idx_widget = self.toolbar.addWidget(QWidget(self.toolbar))
        self.idx_widget.setVisible(False)

        self.agroup = QButtonGroup(self)
        self.agroup.setExclusive(True)

        self.library_btn = None
        self.favorite_btn = self.addTab(
            "Favorites", delegate_paint=False, icon=app_constants.STAR_ICON)
        self.library_btn = self.addTab(
            "Library", delegate_paint=False, icon=app_constants.GRIDL_ICON)
        self.idx_widget = self.toolbar.addWidget(QWidget(self.toolbar))
        self.idx_widget.setVisible(False)
        self.toolbar.addSeparator()

    def _manage_selected(self, b):
        if self._last_selected == b:
            return
        if self._last_selected:
            self._last_selected.selected = False
            self._last_selected.view.list_view.sort_model.rowsInserted.disconnect(
                self.parent_widget.stat_row_info)
            self._last_selected.view.list_view.sort_model.rowsRemoved.disconnect(
                self.parent_widget.stat_row_info)
            self._last_selected.view.hide()
        b.selected = True
        self._last_selected = b
        self.parent_widget.current_manga_view = b.view
        b.view.list_view.sort_model.rowsInserted.connect(
            self.parent_widget.stat_row_info)
        b.view.list_view.sort_model.rowsRemoved.connect(
            self.parent_widget.stat_row_info)
        b.view.show()

    def addTab(  # NOQA
            self,
            name,
            view_type=app_constants.ViewType.Default,
            delegate_paint=True,
            allow_sidebarwidget=False,
            icon=None
    ):
        """add tab."""
        if self.toolbar:
            t = ToolbarButton(self.toolbar, name)
            if icon:
                t.setIcon(icon)
            else:
                t.setIcon(app_constants.CIRCLE_ICON)
            t.setCheckable(True)
            self.agroup.addButton(t)
            t.select.connect(self._manage_selected)
            t.close_tab.connect(self.removeTab)
            if self.library_btn:
                t.view = MangaViews(view_type, self.parent_widget, allow_sidebarwidget)
                t.view.hide()
                t.close_tab.connect(lambda: self.library_btn.click())
                if not allow_sidebarwidget:
                    t.clicked.connect(self.parent_widget.sidebar_list.arrow_handle.click)
            else:
                t.view = self.parent_widget.default_manga_view
            if delegate_paint:
                t.view.list_view.manga_delegate._paint_level = 9000  # over nine thousand!!!
            self._actions.append(self.toolbar.insertWidget(self.idx_widget, t))
            return t

    def removeTab(self, button_or_index):  # NOQA
        """remove tab."""
        if self.toolbar:
            if isinstance(button_or_index, int):
                self.toolbar.removeAction(self._actions.pop(button_or_index))
            else:
                act_to_remove = None
                for act in self._actions:
                    w = self.toolbar.widgetForAction(act)
                    if w == button_or_index:
                        self.toolbar.removeAction(act)
                        act_to_remove = act
                        break
                if act_to_remove:
                    self._actions.remove(act)
